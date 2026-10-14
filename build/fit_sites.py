"""Move invented ('placed') sites off ridges and steep slopes onto plausible ground nearby.

Villages, towns and buildings go to the nearest gentle valley floor (near a river or road where there is one) within a
few km, staying in the same zone (ISEZ/ATR), the same district or planning zone; lakes go to the nearest flat basin
(cirque floor); peaks to the local summit. Things placed together (a village and its school, a works and its mill) move
together. Elevations are reset from the terrain. Prints every move; writes a report to data/site_fit_report.md.
Run: python3 build/fit_sites.py irad-dem.bin irad-osm-roads.json [--write]
"""
import json, math, os, struct, sys
import numpy as np
from scipy import ndimage
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, OSMF = sys.argv[1], sys.argv[2]; WRITE = "--write" in sys.argv
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57
b = open(DEMF, "rb").read()
lon0, lat0, st = struct.unpack("<3d", b[8:32]); nx, ny = struct.unpack("<2i", b[32:40])
Z = ndimage.median_filter(np.frombuffer(b[64:], dtype="<i2").reshape(ny, nx).astype(float), 3)
CKM = st * KY
gy, gx = np.gradient(Z, st * KY * 1000, st * KX * 1000)
SLOPE = np.hypot(gx, gy)
VREL = Z - ndimage.minimum_filter(Z, size=7)          # height above the lowest ground within ~1.5 km
PEAK = ndimage.maximum_filter(Z, size=9)
LONS = lon0 + np.arange(nx) * st; LATS = lat0 + np.arange(ny) * st


def rc(x, y):
    return int(round((y - lat0) / st)), int(round((x - lon0) / st))


def raster(lines):
    m = np.zeros(Z.shape, bool)
    for c in lines:
        for (x1, y1), (x2, y2) in zip(c, c[1:]):
            n = int(max(abs(x2 - x1), abs(y2 - y1)) / (st / 2)) + 1
            for t in np.linspace(0, 1, n + 1):
                j, i = rc(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
                if 0 <= j < ny and 0 <= i < nx: m[j, i] = True
    return m


OSM = json.load(open(OSMF))["ways"]
RIVER_D = ndimage.distance_transform_edt(~raster([w["c"] for w in OSM if w["k"] in ("water:river", "water:canal")])) * CKM
ROAD_D = ndimage.distance_transform_edt(~raster([w["c"] for w in OSM if w["k"].startswith("road:")] +
                                              [r["coords"] for r in json.load(open(os.path.join(ROOT, "data/routes.json"))) if r["kind"] in ("road", "highway")])) * CKM


def polys_of(fc, key):
    out = []
    for f in json.load(open(os.path.join(ROOT, fc)))["features"]:
        for poly in f["geometry"]["coordinates"]:
            out.append((f["properties"][key], [Path(np.array(r)) for r in poly]))
    return out


def label_grid(polys):
    pts = np.column_stack([np.repeat(LONS[None, :], ny, 0).ravel(), np.repeat(LATS[:, None], nx, 1).ravel()])
    lab = np.full(ny * nx, "", dtype=object)
    for name, rings in polys:
        x0, y0 = rings[0].vertices.min(0); x1, y1 = rings[0].vertices.max(0)
        sel = np.where((pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1))[0]
        m = rings[0].contains_points(pts[sel])
        for r in rings[1:]: m &= ~r.contains_points(pts[sel])
        lab[sel[m]] = name
    return lab.reshape(ny, nx)


ZONE = label_grid(polys_of("data/zones.geojson", "zone"))
AREA = label_grid(polys_of("data/districts.geojson", "district") + polys_of("data/planning_zones.geojson", "zone"))

SETTLE = {"village", "town", "suburb", "industry", "military", "terminal", "station", "airport", "market", "school", "hospital",
          "government", "un", "stadium", "power", "oilfield", "bus-station", "hippodrome", "university", "museum", "mosque",
          "church", "other", "heritage", "mazar", "ruins", "park", "checkpoint", "mine"}
NEVER = {"checkpoint", "border-crossing", "dam", "reservoir", "district", "zone-area", "pass", "river-point", "spring", "landmark"}
REGION_WORDS = ("range", "plateau", "valley", "fan", "fringe", "steppe", "forest", "reserve", "national-park", "glacier", "cirque",
                "depression", "sands", "kyr", "epicentre", "badlands", "gorge", "canyon", "headwaters", "terraces", "wellfields", "concession", "area",
                "cave", "hps", "observatory")   # canyon floors and summit sites are finer than the elevation grid
SKIP_LAKES = True   # cirque tarns are finer than the 450 m grid; leave them where the lore put them


def at(a, x, y):
    j, i = rc(x, y)
    return a[min(max(j, 0), ny - 1), min(max(i, 0), nx - 1)]


def best_site(p, kind, R_km):
    j0, i0 = rc(p["lon"], p["lat"])
    r = int(R_km / CKM) + 1
    js, is_ = slice(max(j0 - r, 0), min(j0 + r + 1, ny)), slice(max(i0 - r, 0), min(i0 + r + 1, nx))
    JJ, II = np.mgrid[js, is_]
    d = np.hypot((II - i0) * st * KX, (JJ - j0) * st * KY)
    ok = (d <= R_km) & (ZONE[js, is_] == ZONE[j0, i0]) & (AREA[js, is_] == AREA[j0, i0])
    E_ = Z[js, is_]
    want = p.get("elev")
    if kind == "lake":
        # cirque and valley lakes: the flattest hollow near the height the lore gives
        cost = SLOPE[js, is_] / 0.05 + VREL[js, is_] / 60 + d / 2 + (np.abs(E_ - want) / 150 if want else 0)
    elif kind == "peak":
        cost = -(Z[js, is_]) / 100 + d / 3
    else:
        cost = (VREL[js, is_] / 80 + SLOPE[js, is_] / 0.06 + d / 2.0 + (RIVER_D[js, is_] > 0.8) * 0.5 + (ROAD_D[js, is_] > 1.2) * 0.4
                + np.maximum(0, E_ - 2700) / 80 + (np.maximum(0, E_ - want) / 250 if want else 0))
        if p.get("zone") == "ISEZ":
            cost = cost + (Z[js, is_] > 2400) * 3
        ok &= SLOPE[js, is_] < 0.22
    cost = np.where(ok, cost, np.inf)
    k = np.unravel_index(np.argmin(cost), cost.shape)
    if not np.isfinite(cost[k]):
        return None
    return float(LONS[II[k]]), float(LATS[JJ[k]])


def bad(p):
    k = p["kind"]
    e, s, v = at(Z, p["lon"], p["lat"]), at(SLOPE, p["lon"], p["lat"]), at(VREL, p["lon"], p["lat"])
    if k == "lake": return (not SKIP_LAKES) and (s > 0.2 or v > 120)
    if k == "peak": return at(PEAK, p["lon"], p["lat"]) - e > 150
    if k in SETTLE: return s > 0.2 or v > 220
    return False


P = {fn: json.load(open(os.path.join(ROOT, fn))) for fn in ("data/settlements.json", "data/features.json")}
allp = [p for D in P.values() for p in D]
moves = []
movable = lambda p: (p.get("confidence") == "placed" and not p.get("city") and p["kind"] not in NEVER
                     and not any(w in p["id"] for w in REGION_WORDS) and not p.get("auto_crossing"))
done = set()
# villages and towns first; things within 1.5 km of a village follow it
order = sorted([p for p in allp if movable(p) and bad(p)], key=lambda p: (p["kind"] not in ("village", "town"), p["id"]))
for p in order:
    if p["id"] in done: continue
    R = 6.0 if p["kind"] in ("village", "town", "lake", "peak") else 4.0
    if p["kind"] in ("village", "town") and at(Z, p["lon"], p["lat"]) > 2900: R = 10.0
    q = best_site(p, p["kind"], R)
    if not q: print("  no site for", p["id"]); continue
    dx, dy = q[0] - p["lon"], q[1] - p["lat"]
    group = [p]
    if p["kind"] in ("village", "town"):
        group += [o for o in allp if o is not p and movable(o) and o["id"] not in done and o["kind"] not in ("village", "town", "lake", "peak")
                  and math.hypot((o["lon"] - p["lon"]) * KX, (o["lat"] - p["lat"]) * KY) < 1.5]
    for o in group:
        nxp, nyp = (q if o is p else (o["lon"] + dx, o["lat"] + dy))
        before = (o["lat"], o["lon"], o.get("elev"))
        o["lon"], o["lat"] = round(nxp, 4), round(nyp, 4)
        ne = int(round(at(Z, o["lon"], o["lat"]) / 10) * 10)
        if o["kind"] == "peak": ne = int(round(at(PEAK, o["lon"], o["lat"]) / 10) * 10)
        if o.get("elev") is not None or o["kind"] in ("village", "town", "lake", "peak"): o["elev"] = ne
        km = math.hypot((o["lon"] - before[1]) * KX, (o["lat"] - before[0]) * KY)
        moves.append((o["id"], o["kind"], o["zone"], before, (o["lat"], o["lon"], o.get("elev")), km, "with " + p["id"] if o is not p else ""))
        done.add(o["id"])
for m in moves:
    print(f"{m[0]:36} {m[1]:10} {m[2]:4} {m[3][0]:.3f},{m[3][1]:.3f} {str(m[3][2]):>5} -> {m[4][0]:.3f},{m[4][1]:.3f} {m[4][2]!s:>5}  {m[5]:4.1f} km {m[6]}")
print(len(moves), "moves")
if WRITE:
    for fn, D in P.items():
        json.dump(D, open(os.path.join(ROOT, fn), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data/site_fit_report.md"), "w") as f:
        f.write("# Sites moved onto the terrain (build/fit_sites.py)\n\n| id | kind | zone | from (lat, lon, elev) | to (lat, lon, elev) | km | note |\n|---|---|---|---|---|---|---|\n")
        for m in moves:
            f.write(f"| {m[0]} | {m[1]} | {m[2]} | {m[3][0]:.3f}, {m[3][1]:.3f}, {m[3][2]} | {m[4][0]:.3f}, {m[4][1]:.3f}, {m[4][2]} | {m[5]:.1f} | {m[6]} |\n")
