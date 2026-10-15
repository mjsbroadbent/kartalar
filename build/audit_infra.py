"""Real infrastructure left inside Irad by the OpenStreetMap base, against the lore's own features

  python3 build/audit_infra.py <extract dir>

Lists the aerodromes (with their runways), military areas, big quarries and industrial sites, mines and border posts
inside Irad, each with the nearest lore feature and place, so each one can be given a lore role, renamed or dropped.
Border posts are listed only away from Irad's frontier: a real Kazakh-Kyrgyz or Uzbek-Kyrgyz post inside Irad is a relic.
"""
import json, math, os, sys
import numpy as np
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translit import latin   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = sys.argv[1]
KY = 110.57


def rings(g):
    return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []


def area_km2(r):
    r = np.array(r); kx = 111.32 * math.cos(math.radians(r[:, 1].mean()))
    x, y = r[:, 0] * kx, r[:, 1] * KY
    return abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) / 2


def main():
    irad = [Path(np.array(p[0])) for f in json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"] for p in rings(f["geometry"])]
    edge = np.vstack([p.vertices for p in irad])
    inside = lambda x, y: any(p.contains_point((x, y)) for p in irad)
    def edge_km(x, y): return float(np.min(np.hypot((edge[:, 0] - x) * 111.32 * math.cos(math.radians(y)), (edge[:, 1] - y) * KY)))
    feats = json.load(open(os.path.join(ROOT, "data/features.json")))
    places = json.load(open(os.path.join(ROOT, "data/settlements.json"))) + json.load(open(os.path.join(ROOT, "data/real_places.json")))
    def nearest(lst, x, y, kinds=None):
        best = None
        for f in lst:
            if kinds and f["kind"] not in kinds: continue
            d = math.hypot((f["lon"] - x) * 111.32 * math.cos(math.radians(y)), (f["lat"] - y) * KY)
            if best is None or d < best[0]: best = (d, f["name"], f["kind"])
        return f"{best[1]} ({best[2]}, {best[0]:.1f} km)" if best else ""
    def nm(pr): return " / ".join(dict.fromkeys(v for v in (pr.get("name"), pr.get("name_en"), latin(pr.get("name_ru") or "")) if v)) or "(unnamed)"

    runways = []
    for line in open(os.path.join(EXT, "aeroway.ndjson")):
        f = json.loads(line)
        if f["properties"].get("class") != "runway" or f["geometry"]["type"] != "LineString": continue
        C = np.array(f["geometry"]["coordinates"]); kx = 111.32 * math.cos(math.radians(C[:, 1].mean()))
        runways.append((C.mean(0), float(np.hypot(np.diff(C[:, 0]) * kx, np.diff(C[:, 1]) * KY).sum())))
    rows = []
    def add(kind, x, y, pr, extra=""):
        if not inside(x, y): return
        rows.append((kind, round(x, 4), round(y, 4), nm(pr), extra, nearest(feats, x, y), nearest(places, x, y)))
    for line in open(os.path.join(EXT, "aeroway.ndjson")):
        f = json.loads(line); pr = f["properties"]
        if pr.get("class") != "aerodrome": continue
        rs = rings(f["geometry"]);
        if not rs: continue
        R = np.array(rs[0][0]); x, y = R.mean(0); P = Path(R)
        rw = [L for c, L in runways if P.contains_point(c)]
        tags = ", ".join(f"{k}={pr[k]}" for k in ("icao", "iata", "aerodrome_type", "military", "disused", "abandoned") if pr.get(k))
        add("aerodrome", x, y, pr, f"runways {', '.join(f'{L:.1f}' for L in sorted(rw, reverse=True)) or '-'} km; {area_km2(R):.2f} km² {tags}")
    lone = [(c, L) for c, L in runways if not any(r[0] == "aerodrome" and abs(r[1] - c[0]) < 0.03 and abs(r[2] - c[1]) < 0.03 for r in rows)]
    for c, L in lone:
        if L > 0.6: add("runway", c[0], c[1], {}, f"{L:.1f} km, no aerodrome outline")
    for line in open(os.path.join(EXT, "landuse.ndjson")):
        f = json.loads(line); pr = f["properties"]; cls = pr.get("class")
        if cls not in ("military", "quarry", "industrial"): continue
        rs = rings(f["geometry"]);
        if not rs: continue
        a = sum(area_km2(r[0]) for r in rs)
        if a < {"military": 0.05, "quarry": 0.3, "industrial": 0.8}[cls]: continue
        x, y = np.array(rs[0][0]).mean(0)
        add(cls, x, y, pr, f"{a:.2f} km²")
    for line in open(os.path.join(EXT, "places.ndjson")):
        f = json.loads(line); pr = f["properties"]; x, y = f["geometry"]["coordinates"]
        if pr["place"] == "border":
            if inside(x, y) and edge_km(x, y) > 4: add("border post", x, y, pr, f"{edge_km(x, y):.0f} km inside Irad's frontier")
        elif pr["place"] in ("mine", "aerodrome"): add(pr["place"] + " (point)", x, y, pr)
    rows.sort()
    for r in rows: print(" | ".join(str(v) for v in r))
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
