"""Edit the extracted OSM base layers into the Irad base map before tiling.

  python3 build/base/curate.py <extract dir> <out dir>

- the city plans (data/city) go into the base map as layer "city", with a "mask" polygon under them (the real town
  there is drawn over); real features wholly inside a city footprint are dropped, lines are cut at the footprint
- real roads that an Irad route (data/routes.json) follows are cut where they run along it (the route layer draws
  that road), and the same for railways; other real railways inside Irad are marked disused (only Irad Temir Jolu runs)
- real towns that the lore makes smaller are cut back to a core (SHRINK): their outer streets, buildings and
  built-up land go, leaving the farmland
"""
import json, math, os, sys, glob
import numpy as np
from matplotlib.path import Path
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
KY = 110.57
KX = 111.32 * math.cos(math.radians(43.0))

# real towns with no (or a much smaller) Iradi town in the lore: keep a core of r_core km, clear the rest out to r_out km
SHRINK = [
    dict(name="Taraz", center=(71.3769, 42.9016), r_core=1.4, r_out=10.0, r_tert=6.0),
]
DETAIL_LAYERS = {"building", "landuse", "park"}
DETAIL_ROADS = {"minor", "service", "track", "path", "transit"}


def xy(c): return np.array([(x * KX, y * KY) for x, y in c])


def load(layer):
    fn = os.path.join(SRC, layer + ".ndjson")
    return [json.loads(l) for l in open(fn)] if os.path.exists(fn) else []


def lines_of(g):
    return [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]


def first_ring_pts(g):
    if g["type"] == "Polygon": return g["coordinates"][0]
    if g["type"] == "MultiPolygon": return [p for poly in g["coordinates"] for p in poly[0]]
    return [p for l in lines_of(g) for p in l]


def densify(c, step_km=0.025):
    P = np.array(c, float); out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        d = math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY); n = max(1, int(d / step_km))
        for i in range(1, n + 1): out.append(a + (b - a) * i / n)
    return np.array(out)


def cut_line(c, drop):
    """split a line, removing the stretches where drop(points) is true; returns the kept pieces"""
    P = densify(c); m = drop(P)
    if not m.any(): return [c]
    if m.all(): return []
    pieces, cur = [], []
    for p, d in zip(P, m):
        if d:
            if len(cur) >= 2: pieces.append(cur)
            cur = []
        else: cur.append([round(float(p[0]), 6), round(float(p[1]), 6)])
    if len(cur) >= 2: pieces.append(cur)
    # thin the densified pieces back down
    out = []
    for q in pieces:
        Q = np.array(q); keep = [0]
        for i in range(1, len(Q) - 1):
            a, b, c2 = Q[keep[-1]], Q[i], Q[i + 1]
            v = c2 - a; w = b - a; n = math.hypot(v[0] * KX, v[1] * KY)
            dev = abs(v[0] * KX * w[1] * KY - v[1] * KY * w[0] * KX) / n if n else 0
            if dev > 0.002: keep.append(i)
        keep.append(len(Q) - 1)
        out.append([q[i] for i in keep])
    return out


def main():
    # ---------- cities ----------
    ix = json.load(open(os.path.join(ROOT, "data/city/index.json")))
    foot = []
    city_out = []
    for c in ix["cities"]:
        g = c["footprint"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for p in polys: foot.append(Path(np.array(p[0])))
        city_out.append({"type": "Feature", "tippecanoe": {"layer": "city", "minzoom": 0}, "properties": {"t": "mask"}, "geometry": g})
        d = os.path.join(ROOT, "data/city", c["name"])
        MZ = {"land": 8, "river": 7, "canal": 10, "rail": 8, "road": 8}
        for f in json.load(open(os.path.join(d, "overview.json")))["features"]:
            pr = f["properties"]; mz = MZ.get(pr["t"], 9)
            if pr["t"] == "road" and pr.get("k") == "mid": mz = 9
            city_out.append({"type": "Feature", "tippecanoe": {"layer": "city", "minzoom": mz}, "properties": {k: v for k, v in pr.items()}, "geometry": f["geometry"]})
        for fn in sorted(glob.glob(os.path.join(d, "t_*.json"))):
            for f in json.load(open(fn))["features"]:
                pr = dict(f["properties"]); pr["det"] = 1
                mz = 13 if pr["t"] == "building" else 14 if pr.get("k") == "path" else 12
                city_out.append({"type": "Feature", "tippecanoe": {"layer": "city", "minzoom": mz}, "properties": pr, "geometry": f["geometry"]})
    fb = [(P, P.get_extents()) for P in foot]

    def in_city(pts):
        pts = np.asarray(pts, float); m = np.zeros(len(pts), bool)
        for P, e in fb:
            sel = (pts[:, 0] >= e.x0) & (pts[:, 0] <= e.x1) & (pts[:, 1] >= e.y0) & (pts[:, 1] <= e.y1)
            if sel.any(): m[sel] |= P.contains_points(pts[sel])
        return m

    # ---------- Irad routes ----------
    routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
    rd, rl = [], []
    for r in routes:
        if not r.get("coords") or len(r["coords"]) < 2: continue
        P = densify(r["coords"], 0.02) * [KX, KY]
        (rl if r.get("kind") in ("railway", "rail") else rd).append(P)
    road_tree = cKDTree(np.vstack(rd)); rail_tree = cKDTree(np.vstack(rl))
    near_road = lambda P: road_tree.query(np.asarray(P) * [KX, KY], distance_upper_bound=0.045)[0] < 0.045
    near_rail = lambda P: rail_tree.query(np.asarray(P) * [KX, KY], distance_upper_bound=0.06)[0] < 0.06

    g = json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"][0]["geometry"]
    irad = [Path(np.array(p[0])) for p in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])]
    in_irad = lambda pts: np.any([P.contains_points(np.asarray(pts)) for P in irad], axis=0)

    def shrunk(pts, key="r_out"):
        pts = np.asarray(pts, float); m = np.zeros(len(pts), bool)
        for s in SHRINK:
            d = np.hypot((pts[:, 0] - s["center"][0]) * KX, (pts[:, 1] - s["center"][1]) * KY)
            m |= (d > s["r_core"]) & (d < s.get(key, 0))
        return m

    stats = {}
    def count(k): stats[k] = stats.get(k, 0) + 1

    for layer in ["transportation", "waterway", "water", "landcover", "landuse", "park", "building", "aeroway"]:
        out = []
        for f in load(layer):
            g = f["geometry"]; cls = f["properties"].get("class")
            if g["type"] in ("Polygon", "MultiPolygon"):
                pts = np.array(first_ring_pts(g)); c0 = pts.mean(0)[None]
                if layer != "water" and layer != "landcover" and in_city(c0)[0]: count(layer + " in city"); continue
                if layer in ("water",) and in_city(pts).all(): continue
                if (layer in DETAIL_LAYERS) and shrunk(c0)[0]: count(layer + " shrunk"); continue
                out.append(f); continue
            # lines
            drops = [in_city]
            if layer == "transportation" and cls in DETAIL_ROADS: drops.append(shrunk)
            if layer == "transportation" and cls == "tertiary": drops.append(lambda P: shrunk(P, "r_tert"))   # the old city's own streets
            if layer == "transportation" and cls in ("motorway", "trunk", "primary", "secondary", "tertiary", "minor"): drops.append(near_road)
            if layer == "transportation" and cls == "rail": drops.append(near_rail)
            drop = lambda P: np.any([d(P) for d in drops], axis=0)
            pieces = []
            for c in lines_of(g): pieces += cut_line(c, drop)
            if not pieces: count(layer + " dropped"); continue
            if len(pieces) > 1 or len(pieces[0]) != len(lines_of(g)[0]): count(layer + " cut")
            props = dict(f["properties"])
            if layer == "transportation" and cls == "rail":
                allp = np.array([p for q in pieces for p in q])
                if in_irad(allp[::max(1, len(allp) // 20)]).mean() > 0.5: props["disused"] = 1; count("rail disused")
            f["geometry"] = {"type": "LineString", "coordinates": pieces[0]} if len(pieces) == 1 else {"type": "MultiLineString", "coordinates": pieces}
            f["properties"] = props
            out.append(f)
        with open(os.path.join(OUT, layer + ".ndjson"), "w") as fo:
            for f in out: fo.write(json.dumps(f, separators=(",", ":")) + "\n")
        print(f"  {layer}: {len(out)}")
    with open(os.path.join(OUT, "city.ndjson"), "w") as fo:
        for f in city_out: fo.write(json.dumps(f, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"  city: {len(city_out)}")
    for k, v in sorted(stats.items()): print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
