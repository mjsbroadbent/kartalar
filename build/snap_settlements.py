"""Put the Iradi villages and towns where real settlements are.

  python3 build/snap_settlements.py <fine dem.bin> <extract dir>   (extract dir from build/base/extract.cpp)

1. A village that has a real namesake (OpenStreetMap place with the same name, any spelling) within 40 km goes there.
2. Otherwise it goes to the nearest real village or hamlet (or, failing that, built-up land) within 8 km that is not
   already taken, in the same zone and district / planning zone, at a similar height when the lore gives one
   (a valley village does not end up on a ridge, a summer camp at 2,800 m does not drop to the valley floor).
3. Landmarks filed under the village (features with "city" = its name) move with it.
Anchored places only follow a namesake within 5 km. Cities, quarters and districts are left alone.
Writes data/settlement_snap_report.md.
"""
import json, math, os, re, struct, sys, unicodedata
import numpy as np
from scipy import ndimage
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, EXT = sys.argv[1], sys.argv[2]
KY = 110.57
kx = lambda lat: 111.32 * math.cos(math.radians(lat))
b = open(DEMF, "rb").read()
LON0, LAT0, ST = struct.unpack("<3d", b[8:32]); NX, NY = struct.unpack("<2i", b[32:40])
DEM = ndimage.gaussian_filter(np.frombuffer(b[64:], dtype="<i2").reshape(NY, NX).astype(np.float32), 1.0)
elev = lambda lon, lat: float(ndimage.map_coordinates(DEM, [[(lat - LAT0) / ST], [(lon - LON0) / ST]], order=1)[0])

CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяөүңіұқғһәі", ["a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "i", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "h", "ts", "ch", "sh", "sh", "", "i", "", "e", "yu", "ya", "o", "u", "n", "i", "u", "k", "g", "h", "a", "i"]))


def norm(s):
    s = (s or "").lower()
    s = "".join(CYR.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s.replace("ı", "i")); s = "".join(c for c in s if not unicodedata.combining(c))
    for a, b_ in (("dzh", "j"), ("dj", "j"), ("zh", "j"), ("kh", "h"), ("yo", "o"), ("y", "i"), ("q", "k"), ("x", "h")):
        s = s.replace(a, b_)
    s = re.sub(r"[^a-z]", "", s)
    s = re.sub(r"(.)\1+", r"\1", s)
    for suf in ("auili", "aul", "selo", "kishlak", "kishlogi", "kisloq", "posyolok", "poselok"):
        if s.endswith(suf) and len(s) > len(suf) + 3: s = s[: -len(suf)]
    return s


def polys(fn):
    out = []
    for f in json.load(open(os.path.join(ROOT, fn)))["features"]:
        g = f["geometry"]; ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        out.append((f["properties"], [Path(np.array(p[0])) for p in ps]))
    return out


def which(regions, lon, lat, key):
    for pr, paths in regions:
        if any(pa.contains_point((lon, lat)) for pa in paths): return pr.get(key) or pr.get("name")
    return None


ROADS = None


def load_roads():
    global ROADS
    if ROADS is None:
        pts = []
        for line in open(os.path.join(EXT, "transportation.ndjson")):
            f = json.loads(line)
            if f["properties"]["class"] not in ("primary", "secondary", "tertiary", "minor", "track", "trunk"): continue
            g = f["geometry"]
            for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]): pts += c
        ROADS = np.array(pts)
    return ROADS


def road_near(lon, lat, r_km, h=None, reg=None, region=None, h_tol=300):
    R = load_roads(); d = np.hypot((R[:, 0] - lon) * kx(lat), (R[:, 1] - lat) * KY)
    for i in np.argsort(d)[:4000]:
        if d[i] > r_km: return None
        x, y = R[i]
        if h is not None and abs(elev(x, y) - h) > h_tol: continue
        if reg is not None and region(x, y) != reg: continue
        return float(x), float(y)
    return None


def down_river(lon, lat, km_):
    best = None
    for line in open(os.path.join(EXT, "waterway.ndjson")):
        f = json.loads(line)
        if f["properties"]["class"] not in ("river", "stream"): continue
        g = f["geometry"]
        for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
            C = np.array(c); d = np.hypot((C[:, 0] - lon) * kx(lat), (C[:, 1] - lat) * KY); i = int(np.argmin(d))
            if best is None or d[i] < best[0]: best = (d[i], C, i)
    _, C, i = best
    if elev(*C[-1]) > elev(*C[0]): C = C[::-1]; i = len(C) - 1 - i     # run downstream
    walked = 0.0
    while i + 1 < len(C) and walked < km_:
        walked += math.hypot((C[i + 1, 0] - C[i, 0]) * kx(lat), (C[i + 1, 1] - C[i, 1]) * KY); i += 1
    return float(C[i, 0]), float(C[i, 1])


def crest(lon, lat, bearing, max_km=10):
    """the highest point on a straight line from (lon, lat) out to max_km (a ridge crossing for a pass)"""
    t = np.linspace(0.3, max_km, 200); br = math.radians(bearing)
    xs = lon + t * math.sin(br) / kx(lat); ys = lat + t * math.cos(br) / KY
    z = ndimage.map_coordinates(DEM, [(ys - LAT0) / ST, (xs - LON0) / ST], order=1)
    i = int(np.argmax(z)); return float(xs[i]), float(ys[i]), float(z[i])


def resolve(how, real):
    kind, arg = how[0], how[1]
    if kind == "osm":
        for r in real:
            if norm(arg) in r["names"]: return r["lon"], r["lat"]
    if kind == "at": return arg
    if kind == "road_h":     # a real road or track near (lon, lat) at about height h
        lon, lat, r_km, h = arg
        R = load_roads(); d = np.hypot((R[:, 0] - lon) * kx(lat), (R[:, 1] - lat) * KY); sel = np.where(d < r_km)[0]
        if not len(sel): return None
        hz = np.array([elev(*R[i]) for i in sel]); i = sel[int(np.argmin(np.abs(hz - h)))]
        return float(R[i, 0]), float(R[i, 1])
    return None


# placed by hand from the lore's description (the Chatkal valley villages were drawn in the mountains east of the valley)
MANUAL = {
    "archaly": ("osm", "Korgon-Say"),                  # "village in a forested side valley of the Chatkal"
    "kok-jar": ("at", (71.7628, 42.1243)),             # "upper Chatkal valley below the Kök-Jar Pass", ~2,530 m: where the
                                                       # pack track leaves the valley head for the ~3,150 m pass
    "teke-tash": ("road_h", (71.62, 42.10, 5, 2550)),  # "~2,550 m on the southern slopes of the Talas Alatau above the Chatkal valley"
}
# features placed relative to their (moved) village: id -> (village id, how)
FEATURE_MANUAL = {
    "kok-jar-old-mine": ("kok-jar", ("down_valley", 4.0)),
    "kok-jar-primary-school": ("kok-jar", ("down_valley", 5.0)),
    "kok-jar-pass": ("kok-jar", ("at", (71.9501, 42.0765))),   # the crest of the real pack track
    "chatkal-river": ("kanysh-kiya", ("river_near", (71.25, 41.88))),   # on the river, in the middle valley
}
CHATKAL_AXIS = 230   # down-valley bearing of the upper Chatkal


def main():
    S = json.load(open(os.path.join(ROOT, "data/settlements.json")))
    F = json.load(open(os.path.join(ROOT, "data/features.json")))
    zones = polys("data/zones.geojson"); districts = polys("data/districts.geojson"); pz = polys("data/planning_zones.geojson")
    city_foot = [Path(np.array(p[0])) for c in json.load(open(os.path.join(ROOT, "data/city/index.json")))["cities"]
                 for p in ([c["footprint"]["coordinates"]] if c["footprint"]["type"] == "Polygon" else c["footprint"]["coordinates"])]
    region = lambda lon, lat: (which(zones, lon, lat, "zone"), which(districts, lon, lat, "district"), which(pz, lon, lat, "zone"))
    # real places and built-up land
    real = []
    for line in open(os.path.join(EXT, "places.ndjson")):
        f = json.loads(line); p = f["properties"]
        if p["place"] not in ("village", "hamlet", "town"): continue
        x, y = f["geometry"]["coordinates"]
        names = {norm(p.get(k)) for k in ("name", "name_en", "name_ru", "name_ky", "name_kk", "name_uz") if p.get(k)}
        real.append(dict(lon=x, lat=y, names=names - {""}, label=p.get("name_en") or p.get("name"), kind=p["place"]))
    for line in open(os.path.join(EXT, "landuse.ndjson")):
        f = json.loads(line)
        if f["properties"]["class"] != "residential": continue
        g = f["geometry"]; ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
        c = np.array(ring).mean(0); real.append(dict(lon=float(c[0]), lat=float(c[1]), names=set(), label="built-up land", kind="landuse"))
    RX = np.array([[r["lon"], r["lat"]] for r in real])
    for r in real: r["region"] = None
    taken = set()
    # settled places that stay put still occupy their real village
    movable = []
    for p in S:
        if p["kind"] not in ("village", "town") or p["id"] in ("boz-korgon",) or p.get("locked"): continue   # locked: docs/PLACEMENT.md
        if any(pa.contains_point((p["lon"], p["lat"])) for pa in city_foot): continue
        movable.append(p)
    lore_h = {}
    for p in movable:
        m = re.search(r"~?([1-4],?\d{3}) m\b", p.get("note") or "")
        if p.get("elev"): lore_h[p["id"]] = float(p["elev"])
        elif m: lore_h[p["id"]] = float(m.group(1).replace(",", ""))
    plan = []
    for p in movable:
        d = np.hypot((RX[:, 0] - p["lon"]) * kx(p["lat"]), (RX[:, 1] - p["lat"]) * KY)
        nm = {norm(p.get("name")), norm(p.get("name_ru")), norm(p.get("name_en"))} - {""}
        lim = {"anchor": 5, "real-place": 60}.get(p.get("confidence"), 6)   # Kyrgyz place names repeat a lot
        hits = [i for i in np.argsort(d) if d[i] < lim and real[i]["names"] & nm]
        if p.get("confidence") != "real-place":
            reg = region(p["lon"], p["lat"]); hits = [i for i in hits if region(real[i]["lon"], real[i]["lat"]) == reg]
        if hits: plan.append((0, d[hits[0]], p, hits[0], "namesake")); continue
        if p.get("confidence") == "anchor" or p["id"] in MANUAL: continue
        plan.append((1, 0, p, None, None))
    out_rows = []; moved = {}
    # namesakes first, then the rest by how close their best candidate is
    for pri, dd, p, i, why in sorted([x for x in plan if x[0] == 0], key=lambda x: x[1]):
        if i in taken: continue
        taken.add(i); moved[p["id"]] = (i, why)
    rest = [x[2] for x in plan if x[0] == 1]
    cands = {}
    for p in rest:
        reg = region(p["lon"], p["lat"]); h0 = lore_h.get(p["id"])
        d = np.hypot((RX[:, 0] - p["lon"]) * kx(p["lat"]), (RX[:, 1] - p["lat"]) * KY)
        lst = []
        for i in np.argsort(d):
            if d[i] > 8: break
            r = real[i]
            if r["region"] is None: r["region"] = region(r["lon"], r["lat"])
            if r["region"] != reg: continue
            if any(pa.contains_point((r["lon"], r["lat"])) for pa in city_foot): continue
            hz = elev(r["lon"], r["lat"])
            if h0 is not None and abs(hz - h0) > 300: continue
            cost = d[i] + (1.5 if r["kind"] == "landuse" else 0) + (0.5 if r["kind"] == "hamlet" else 0)
            lst.append((cost, i))
        cands[p["id"]] = sorted(lst)
    order = sorted(rest, key=lambda p: cands[p["id"]][0][0] if cands[p["id"]] else 99)
    for p in order:
        for cost, i in cands[p["id"]]:
            if i not in taken:
                taken.add(i); moved[p["id"]] = (i, "nearest " + real[i]["kind"]); break
    # no settlement in reach: onto the nearest real road within 3 km (not summer camps, which have none)
    for p in rest:
        if p["id"] in moved or re.search(r"camp|summer|yurt", p.get("note") or "", re.I): continue
        q = road_near(p["lon"], p["lat"], 3.0, lore_h.get(p["id"]), region(p["lon"], p["lat"]), region)
        if q:
            real.append(dict(lon=q[0], lat=q[1], names=set(), label="road", kind="road")); moved[p["id"]] = (len(real) - 1, "nearest road")
    # hand placements (see MANUAL)
    for pid, how in MANUAL.items():
        q = resolve(how, real)
        if q: real.append(dict(lon=q[0], lat=q[1], names=set(), label=how[0] + " " + str(how[1])[:30], kind="manual")); moved[pid] = (len(real) - 1, "by hand")
    byid = {p["id"]: p for p in S}
    for pid, (i, why) in moved.items():
        p = byid[pid]; r = real[i]
        d = math.hypot((r["lon"] - p["lon"]) * kx(p["lat"]), (r["lat"] - p["lat"]) * KY)
        if d < 0.15: continue
        dx, dy = r["lon"] - p["lon"], r["lat"] - p["lat"]
        h_old, h_new = elev(p["lon"], p["lat"]), elev(r["lon"], r["lat"])
        nf = 0
        for f in F:     # its landmarks come along
            if f.get("city") and norm(f["city"]) == norm(p["name"]) and math.hypot((f["lon"] - p["lon"]) * kx(p["lat"]), (f["lat"] - p["lat"]) * KY) < 4:
                f["lon"] = round(f["lon"] + dx, 5); f["lat"] = round(f["lat"] + dy, 5); nf += 1
        out_rows.append((p["id"], p["name"], d, why, r["label"], h_old, h_new, nf))
        p["lon"], p["lat"] = round(r["lon"], 5), round(r["lat"], 5)
        if p.get("confidence") == "placed": p["confidence"] = "real-place" if why == "namesake" else "placed"
    fb = {f["id"]: f for f in F}
    for fid, (vid, (how, arg)) in FEATURE_MANUAL.items():
        if fid not in fb or vid not in byid: continue
        v = byid[vid]; f = fb[fid]
        if how == "down_valley":   # arg km down the nearest river from the village
            q = down_river(v["lon"], v["lat"], arg)
            f["lon"], f["lat"] = round(q[0], 5), round(q[1], 5); f["elev"] = int(round(elev(*q), -1))
        elif how == "river_near":
            q = down_river(arg[0], arg[1], 0.0); f["lon"], f["lat"] = round(q[0], 5), round(q[1], 5); f["elev"] = int(round(elev(*q), -1))
        elif how == "at":
            f["lon"], f["lat"] = arg; f["elev"] = int(round(elev(*arg), -1))
        elif how == "crest":    # a ridge crossing in a fan of bearings round arg, at about the pass height the lore gives
            hv = elev(v["lon"], v["lat"]); want = float(f.get("elev") or hv + 600)
            cands_ = [crest(v["lon"], v["lat"], arg + db, 8) for db in range(-60, 61, 5)]
            cands_ = [c for c in cands_ if c[2] > hv + 150] or cands_
            x, y, z = min(cands_, key=lambda c: abs(c[2] - want))
            f["lon"], f["lat"] = round(x, 5), round(y, 5); f["elev"] = int(round(z, -1))
        out_rows.append((fid, f["name"], 0.0, "by hand (feature)", how, 0, f.get("elev") or 0, 0))
    json.dump(S, open(os.path.join(ROOT, "data/settlements.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)
    unmoved = [p["name"] for p in movable if p["id"] not in moved]
    with open(os.path.join(ROOT, "data/settlement_snap_report.md"), "w") as f:
        f.write("# Villages and towns moved onto real settlements (build/snap_settlements.py)\n\n| place | moved | why | onto | height then -> now | landmarks moved |\n|---|---|---|---|---|---|\n")
        for r in sorted(out_rows, key=lambda r: -r[2]):
            f.write(f"| {r[1]} | {r[2]:.1f} km | {r[3]} | {r[4]} | {r[5]:.0f} -> {r[6]:.0f} m | {r[7]} |\n")
        f.write(f"\nNo real settlement within reach (left where they were): {', '.join(unmoved) or 'none'}\n")
    for r in sorted(out_rows, key=lambda r: -r[2]): print(f"  {r[1]:22} {r[2]:5.1f} km  {r[3]:16} {r[4][:24]:24} {r[5]:5.0f} -> {r[6]:5.0f} m  +{r[7]}")
    print("  left:", ", ".join(unmoved))


if __name__ == "__main__":
    main()
