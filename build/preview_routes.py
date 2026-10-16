#!/usr/bin/env python3
"""Screenshot the map with the current road data drawn over it, before the tiles are rebuilt.

    python3 build/preview_routes.py <out.png> <zoom/lat/lon> [more views...] [--size 1400x1000] [--ids a,b] [--no-before]

Per view, <out.png> gets a suffix (-1, -2 ...) when there is more than one. Drawn on top of the (possibly stale) base map:
  - every Irad road and railway from data/routes.json in a bright colour per route, labelled with its id
    (--ids: only those routes);
  - the same routes as committed (git HEAD) as dashed grey lines, so a change shows as grey vs colour (--no-before: off);
  - the city plans' main streets (major and mid) from data/city in thin dark red, so streets
    dropped or added by hand show before detail.pmtiles is rebuilt.
The page is served from the repo by a small local server (with HTTP range support for the pmtiles).
"""
import functools, glob, http.server, io, json, os, re, subprocess, sys, threading

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_head(self):
        rng = self.headers.get("Range"); path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path): return super().send_head()
        m = re.match(r"bytes=(\d+)-(\d*)", rng); size = os.path.getsize(path)
        a = int(m.group(1)); b = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
        with open(path, "rb") as f: f.seek(a); data = f.read(b - a + 1)
        self.send_response(206); self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Range", f"bytes {a}-{b}/{size}"); self.send_header("Content-Length", str(len(data))); self.end_headers()
        return io.BytesIO(data)


def city_streets(bbox):
    x0, y0, x1, y1 = bbox; out = []
    for fn in glob.glob(os.path.join(ROOT, "data/city/*/overview.json")) + glob.glob(os.path.join(ROOT, "data/city/*/t_*.json")):
        for f in json.load(open(fn))["features"]:
            p = f["properties"]; g = f["geometry"]
            if p.get("t") != "road" or p.get("k") not in ("major", "mid") or g["type"] != "LineString": continue
            if any(x0 <= x <= x1 and y0 <= y <= y1 for x, y, *_ in g["coordinates"]):
                out.append({"type": "Feature", "properties": {"k": p["k"]}, "geometry": g})
    return out


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: (a.pop(a.index(k) + 1), a.remove(k))[0] if k in a else d
    size = opt("--size", "1400x1000"); W, H = map(int, size.split("x"))
    ids = set(opt("--ids", "").split(",")) - {""}
    before = "--no-before" not in a
    if not before: a.remove("--no-before")
    out, views = a[0], a[1:]
    if not views: sys.exit(__doc__)

    routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
    keep = lambda r: r.get("coords") and r.get("kind") in ("highway", "road", "railway") and (not ids or r["id"] in ids)
    pal = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#00a6a6", "#f032e6", "#9a6324", "#808000", "#000075"]
    now = [{"type": "Feature", "properties": {"id": r["id"], "c": pal[i % len(pal)]},
            "geometry": {"type": "LineString", "coordinates": [c[:2] for c in r["coords"]]}} for i, r in enumerate(x for x in routes if keep(x))]
    old = []
    if before:
        try:
            head = json.loads(subprocess.check_output(["git", "-C", ROOT, "show", "HEAD:data/routes.json"], stderr=subprocess.DEVNULL))
            cur = {r["id"]: r.get("coords") for r in routes}
            old = [{"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": [c[:2] for c in r["coords"]]}}
                   for r in head if keep(r) and r.get("coords") != cur.get(r["id"])]
        except Exception:
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n, v in enumerate(views):
            z, lat, lon = map(float, v.split("/"))
            span = 360 / (512 * 2 ** z)     # degrees per pixel
            bbox = (lon - W * span, lat - H * span, lon + W * span, lat + H * span)
            pg = b.new_page(viewport={"width": W, "height": H}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(f"http://127.0.0.1:{port}/#map={z}/{lat}/{lon}")
            pg.wait_for_function("window.KT && window.KT.map && window.KT.map.getSource('routes')", timeout=60000)
            pg.wait_for_timeout(5000)
            pg.evaluate("""([now, old, streets]) => { const m = window.KT.map, fc = f => ({type: "FeatureCollection", features: f});
              m.addSource("pv-st", {type: "geojson", data: fc(streets)});
              m.addLayer({id: "pv-st", type: "line", source: "pv-st", paint: {"line-color": "#8b1a1a", "line-width": ["match", ["get", "k"], "major", 1.4, 0.8], "line-opacity": 0.7}});
              m.addSource("pv-old", {type: "geojson", data: fc(old)});
              m.addLayer({id: "pv-old", type: "line", source: "pv-old", paint: {"line-color": "#555", "line-width": 3, "line-dasharray": [2, 2], "line-opacity": 0.8}});
              m.addSource("pv-now", {type: "geojson", data: fc(now)});
              m.addLayer({id: "pv-now", type: "line", source: "pv-now", layout: {"line-cap": "round", "line-join": "round"}, paint: {"line-color": ["get", "c"], "line-width": 3.5, "line-opacity": 0.85}});
              m.addLayer({id: "pv-lab", type: "symbol", source: "pv-now", layout: {"symbol-placement": "line", "text-field": ["get", "id"], "text-size": 12, "symbol-spacing": 300, "text-font": ["Noto Sans Bold"]},
                          paint: {"text-color": ["get", "c"], "text-halo-color": "#fff", "text-halo-width": 2}}); }""",
                        [now, old, city_streets(bbox)])
            pg.wait_for_timeout(2500)
            fn = out if len(views) == 1 else re.sub(r"(\.png)?$", f"-{n + 1}.png", out, count=1)
            pg.screenshot(path=fn); print(fn, *errs[:3]); pg.close()
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
