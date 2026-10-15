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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translit import nature_name   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
KY = 110.57
KX = 111.32 * math.cos(math.radians(43.0))

# real towns with no (or a much smaller) Iradi town in the lore: the town's own built-up area (its contiguous
# residential land and buildings, not the villages round it) is cleared except a core of about core_km2, grown out from
# the centre through the street fabric and rounded off to whole neighbourhoods, so the small town keeps a real shape
SHRINK = [
    dict(name="Taraz", center=(71.3769, 42.9016), core_km2=4.5, search_km=12.0),
]
SG = 0.0005   # ~45 m grid for the town masks
DETAIL_LAYERS = {"building", "landuse", "park"}

# real infrastructure inside Irad, against the lore (build/audit_infra.py lists it): (lon, lat, radius km, action)
#   remove  - not there in Irad (a working open pit under the clans' mining moratorium, a Kazakh-Kyrgyz post, a cleared plant)
#   disused - there, but closed since the Soviet years: drawn faint (runways, works, pits)
SITES = [
    (72.734, 42.293, 3.5, "remove"),    # Jerooy gold pit: tribal Talas Alatau, moratorium
    (71.528, 42.184, 3.5, "remove"),    # "Vertex Gold" pit below Kök-Suu Peak
    (71.764, 42.379, 2.0, "remove"),    # Shiraljin gold: the Karakoyun clan's own valley
    (74.260, 43.619, 1.8, "remove"),    # Shatyrkul copper pit beside Boz-Korgon
    (71.277, 42.933, 1.8, "remove"),    # Aulie-Ata machine works: demolished with the old city
    (71.098, 42.948, 2.5, "remove"),    # phosphorus plant west of Aulie-Ata: demolished, back to fields
    (71.499, 41.396, 0.5, "remove"), (71.678, 41.422, 0.5, "remove"), (73.183, 41.038, 0.5, "remove"),   # Kyrgyz army posts in tribal land
    (71.301, 42.858, 3.0, "disused"),   # Aulie-Ata airfield, closed 1994
    (72.726, 42.967, 3.0, "disused"),   # Kulan (Lugovoy) bomber dispersal field, closed 1992, in the restricted-weapons zone
    (72.947, 44.272, 2.5, "disused"),   # Moiynkum reserve airfield
    (71.710, 42.716, 1.5, "disused"), (70.506, 43.206, 1.5, "disused"),   # Semetey and Karatau strips
    (71.069, 41.262, 2.0, "disused"), (71.054, 41.258, 1.0, "disused"),   # Bozymchak adits
    (71.450, 42.025, 4.5, "disused"),   # Kuru-Tegerek copper prospect and its pads
    (70.949, 41.481, 1.5, "disused"), (73.981, 41.177, 2.0, "disused"),   # Fullgold, Makmal
    (71.150, 41.510, 3.5, "disused"),   # Terek-Sai mines
    (71.139, 41.967, 1.8, "disused"), (71.174, 42.030, 2.5, "disused"),   # Chatkal highland workings
    (72.705, 45.116, 4.0, "disused"),   # Akbakay pits
    (69.615, 43.585, 14.0, "disused"), (70.140, 43.374, 4.0, "disused"), (70.468, 43.148, 1.8, "disused"), (70.527, 43.194, 1.5, "disused"),   # Karatau phosphorite
    (71.081, 44.335, 5.0, "disused"), (71.264, 44.298, 2.0, "disused"), (71.552, 44.435, 2.5, "disused"),   # Amangeldy gas wells, capped
    (73.959, 45.203, 2.0, "disused"),   # Ülken power-plant site, abandoned 1991
    (72.652, 42.982, 1.0, "disused"),   # Kulan gas compressor station, dry since 1991
    (72.705, 42.426, 1.2, "disused"),   # Kümüshtü tailings, capped
]
SITE_LAYERS = {"landuse": ("industrial", "quarry", "military"), "aeroway": None}


def site_action(layer, cls, x, y):
    if layer not in SITE_LAYERS or (SITE_LAYERS[layer] and cls not in SITE_LAYERS[layer]): return None
    for sx, sy, r, act in SITES:
        if math.hypot((x - sx) * 111.32 * math.cos(math.radians(sy)), (y - sy) * KY) < r: return act
    return None
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


def prune_orphans(feats, route_d, count):
    """main-road pieces the cuts left hanging: an isolated piece, or a spur from an Irad route that ends in the fields
    (a main road does not just stop), are dropped"""
    MAJOR = ("motorway", "trunk", "primary", "secondary")
    split = []
    for f in feats:     # one feature per piece, so each piece of a cut road is judged on its own
        if f["geometry"]["type"] == "MultiLineString" and f["properties"].get("class") in MAJOR:
            for c in f["geometry"]["coordinates"]: split.append({**f, "geometry": {"type": "LineString", "coordinates": c}})
        else: split.append(f)
    feats = split
    verts, owner = [], []
    for n, f in enumerate(feats):
        for c in lines_of(f["geometry"]):
            for p in c: verts.append(p); owner.append(n)
    V = np.array(verts) * [KX, KY]; owner = np.array(owner); tree = cKDTree(V)
    cls_of = [f["properties"].get("class") for f in feats]
    def connected(p, n):      # joined to another real main road (a track or field lane does not count)
        for i in tree.query_ball_point(np.array(p) * [KX, KY], 0.025):
            if owner[i] != n and cls_of[owner[i]] in MAJOR + ("tertiary",): return True
        return False
    keep = []
    for n, f in enumerate(feats):
        if f["properties"].get("class") not in MAJOR or f["geometry"]["type"] != "LineString": keep.append(f); continue
        C = np.array(f["geometry"]["coordinates"]); L = float(np.hypot(*np.diff(C * [KX, KY], axis=0).T).sum())
        ends = [C[0], C[-1]]
        con = [connected(e, n) for e in ends]; onr = [route_d(np.array([e]))[0] < 0.08 for e in ends]
        near_route = np.median(route_d(C)) < 1.5
        if not any(con) and not any(onr) and L < 2: count("transportation orphan"); continue
        if near_route and L < 3 and not any(con) and not all(onr): count("transportation orphan"); continue
        if near_route and L < 5 and ((onr[0] and not con[1] and not onr[1]) or (onr[1] and not con[0] and not onr[0])): count("transportation spur"); continue
        keep.append(f)
    return keep


def label_line(c, tol_km=0.12):
    """a river's course with the meanders taken out (Douglas-Peucker, then Chaikin corner cutting), for its name to follow"""
    P = np.array(c, float)
    if len(P) < 2: return None
    kx = 111.32 * math.cos(math.radians(P[:, 1].mean()))
    Q = P * [kx, KY]
    keep = np.zeros(len(Q), bool); keep[[0, -1]] = True; stack = [(0, len(Q) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1: continue
        a, b = Q[i], Q[j]; ab = b - a; L = np.hypot(*ab)
        seg = Q[i + 1:j]
        d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L if L > 0 else np.hypot(*(seg - a).T)
        k = int(np.argmax(d))
        if d[k] > tol_km: keep[i + 1 + k] = True; stack += [(i, i + 1 + k), (i + 1 + k, j)]
    R = P[keep]
    for _ in range(2):
        if len(R) < 3: break
        R = np.vstack([R[:1]] + [np.array([0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]) for a, b in zip(R, R[1:])] + [R[-1:]])
    if np.hypot(*((R[-1] - R[0]) * [kx, KY])) < 0.5 and len(R) < 4: return None
    return [[round(x, 5), round(y, 5)] for x, y in R]


def merge_named(feats, count):
    """join the OSM pieces of a named river end to end, so its name has room to be drawn along it"""
    keep, groups = [], {}
    for f in feats:
        pr = f["properties"]
        if pr.get("name") and pr.get("class") in ("river", "canal", "stream") and not pr.get("brunnel"): groups.setdefault((pr["class"], pr["name"]), []).append(f)
        else: keep.append(f)
    for (cls, nm), fs in groups.items():
        lines = [list(map(tuple, c)) for f in fs for c in lines_of(f["geometry"])]
        mz = min(f["tippecanoe"]["minzoom"] for f in fs)
        k = lambda p: (round(p[0], 6), round(p[1], 6))
        ends = {}
        for i, c in enumerate(lines):
            ends.setdefault(k(c[0]), []).append(i); ends.setdefault(k(c[-1]), []).append(i)
        used = [False] * len(lines)
        def take(i, at):          # line i, oriented to start at point key `at`
            c = lines[i]; used[i] = True
            return c if k(c[0]) == at else c[::-1]
        out = []
        for i in range(len(lines)):
            if used[i]: continue
            chain = take(i, k(lines[i][0]))
            for direction in (1, 0):
                while True:
                    e = k(chain[-1])
                    nxt = [j for j in ends.get(e, []) if not used[j]]
                    if len(ends.get(e, [])) != 2 or not nxt: break     # stop at forks and confluences
                    chain = chain + take(nxt[0], e)[1:]
                chain = chain[::-1]
            out.append(chain)
        count("waterway named pieces merged", len(lines) - len(out))
        for c in out:
            keep.append({"type": "Feature", "tippecanoe": {"layer": "waterway", "minzoom": mz}, "properties": {"class": cls, "name": nm},
                         "geometry": {"type": "LineString", "coordinates": [list(p) for p in c]}})
    return keep


def lake_levels():
    """a lake or reservoir outline drawn above its own water (a reservoir mapped at full supply level, with dry shore
    inside it) is redrawn at the water surface the terrain shows; a smaller outline of the same water inside a bigger one
    is dropped. Needs FINE_DEM (build/base/make_fine_dem.py)."""
    import struct
    from scipy import ndimage
    fn = os.environ.get("FINE_DEM")
    if not fn or not os.path.exists(fn): return None
    b = open(fn, "rb").read()
    L0, A0, ST = struct.unpack("<3d", b[8:32]); NX, NY = struct.unpack("<2i", b[32:40])
    D = np.frombuffer(b[64:], dtype="<i2").reshape(NY, NX)
    big = []
    for f in load("water"):
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            R = np.array(poly[0])
            if len(R) > 200: big.append(R)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

    def fix(g):
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        R = np.array(polys[0][0])
        if len(polys) == 1 and len(R) < 400:     # a small outline lying inside a bigger outline of the same water
            for B in big:
                if B is not R and len(B) > len(R) and Path(B).contains_points(R[::max(1, len(R) // 20)]).all(): return None
        x0, x1, y0, y1 = R[:, 0].min(), R[:, 0].max(), R[:, 1].min(), R[:, 1].max()
        if (x1 - x0) * (y1 - y0) * 9000 < 20.0 or x0 < L0 or y0 < A0 or x1 > L0 + NX * ST or y1 > A0 + NY * ST: return g
        i0, i1, j0, j1 = int((x0 - L0) / ST) - 2, int((x1 - L0) / ST) + 3, int((y0 - A0) / ST) - 2, int((y1 - A0) / ST) + 3
        X, Y = np.meshgrid(L0 + np.arange(i0, i1) * ST, A0 + np.arange(j0, j1) * ST)
        Q = np.column_stack([X.ravel(), Y.ravel()]); inside = np.zeros(len(Q), bool)
        for poly in polys:
            m = Path(np.array(poly[0])).contains_points(Q)
            for h in poly[1:]: m &= ~Path(np.array(h)).contains_points(Q)
            inside |= m
        inside = inside.reshape(X.shape); Z = D[j0:j1, i0:i1].astype(float)
        if inside.sum() < 200: return g
        z = Z[inside]; level = np.median(z)
        if np.percentile(z, 95) - level < 10 or inside.sum() * (ST * 111) ** 2 * 0.75 < 20: return g     # at its surface already, or small
        wet = inside & (Z <= level + 2)
        wet = ndimage.binary_opening(wet, iterations=1)
        lab, n = ndimage.label(wet)
        if not n: return g
        sizes = ndimage.sum(wet, lab, range(1, n + 1)); wet = np.isin(lab, 1 + np.where(sizes > 0.05 * sizes.max())[0])
        fig = plt.figure(); cs = plt.contour(X, Y, ndimage.gaussian_filter(wet.astype(float), 0.8), levels=[0.5]); segs = cs.allsegs[0]; plt.close(fig)
        rings = sorted([s_ for s_ in segs if len(s_) > 6], key=lambda s_: -abs(np.sum(s_[:-1, 0] * s_[1:, 1] - s_[1:, 0] * s_[:-1, 1])))
        out = []
        for s_ in rings:
            r = [[round(float(x), 6), round(float(y), 6)] for x, y in s_]
            if r[0] != r[-1]: r.append(r[0])
            host = next((P_ for P_ in out if Path(np.array(P_[0])).contains_point(r[0])), None)
            if host is not None: host.append(r)
            else: out.append([r])
        print(f"  lake at {np.mean(R[:, 0]):.3f},{np.mean(R[:, 1]):.3f}: outline at up to {np.percentile(z, 95):.0f} m, water at {level:.0f} m; redrawn")
        return {"type": "MultiPolygon", "coordinates": out} if out else g
    return fix


def raster_polys(rings_list, x0, y0, nx, ny):
    M = np.zeros((ny, nx), bool)
    xs = x0 + np.arange(nx) * SG; ys = y0 + np.arange(ny) * SG
    for R in rings_list:
        R = np.asarray(R)
        i0, i1 = max(0, int((R[:, 0].min() - x0) / SG)), min(nx, int((R[:, 0].max() - x0) / SG) + 2)
        j0, j1 = max(0, int((R[:, 1].min() - y0) / SG)), min(ny, int((R[:, 1].max() - y0) / SG) + 2)
        if i1 <= i0 or j1 <= j0: continue
        GX, GY = np.meshgrid(xs[i0:i1], ys[j0:j1])
        M[j0:j1, i0:i1] |= Path(R).contains_points(np.column_stack([GX.ravel(), GY.ravel()])).reshape(GX.shape)
    return M


def town_mask(s_):
    """cells of the town's built-up area to clear: (x0, y0, mask)"""
    from scipy import ndimage
    cx, cy = s_["center"]; r = s_["search_km"]
    x0, y0 = cx - r / KX, cy - r / KY; nx, ny = int(2 * r / KX / SG) + 1, int(2 * r / KY / SG) + 1
    inbox = lambda R: x0 < R[:, 0].mean() < x0 + nx * SG and y0 < R[:, 1].mean() < y0 + ny * SG
    land = []
    for f in load("landuse"):
        if f["properties"]["class"] not in ("residential", "commercial", "industrial", "retail"): continue
        R = np.array(first_ring_pts(f["geometry"]))
        if inbox(R): land.append(R)
    LM = raster_polys(land, x0, y0, nx, ny)
    B = np.zeros((ny, nx), bool)
    for f in load("building"):
        R = np.array(first_ring_pts(f["geometry"])); c = R.mean(0)
        i, j = int((c[0] - x0) / SG), int((c[1] - y0) / SG)
        if 0 <= i < nx and 0 <= j < ny: B[j, i] = True
    urban = ndimage.binary_closing(LM | ndimage.binary_dilation(B, iterations=1), iterations=3)
    lab, n = ndimage.label(urban)
    jc, ic = int((cy - y0) / SG), int((cx - x0) / SG)
    if not lab[jc, ic]:
        d, (jj, ii) = ndimage.distance_transform_edt(lab == 0, return_indices=True); jc, ic = jj[jc, ic], ii[jc, ic]
    town = lab == lab[jc, ic]
    # grow the core through the built-up cells from the centre (geodesic, so it follows the town's own shape)
    from collections import deque
    want = s_["core_km2"] / (SG * KX * SG * KY); core = np.zeros_like(town); q = deque([(jc, ic)]); core[jc, ic] = True; got = 1
    while q and got < want:
        j, i = q.popleft()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b_ = j + dj, i + di
            if 0 <= a < ny and 0 <= b_ < nx and town[a, b_] and not core[a, b_]:
                core[a, b_] = True; got += 1; q.append((a, b_))
    # whole neighbourhoods: a land-use block mostly inside the core joins it, one mostly outside leaves it
    for R in land:
        m = raster_polys([R], x0, y0, nx, ny)
        if m.sum() == 0: continue
        frac = (m & core).sum() / m.sum()
        if frac >= 0.5: core |= m
        else: core &= ~m
    core = ndimage.binary_opening(ndimage.binary_closing(core, iterations=2), iterations=1)
    lab2, n2 = ndimage.label(core)
    if n2: core = lab2 == (1 + int(np.argmax(ndimage.sum(core, lab2, range(1, n2 + 1)))))
    clear = town & ~ndimage.binary_dilation(core, iterations=1)
    print(f"  {s_['name']}: built-up area {town.sum() * SG * KX * SG * KY:.0f} km2, kept core {core.sum() * SG * KX * SG * KY:.1f} km2")
    return x0, y0, clear


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
    near_road_wide = lambda P: road_tree.query(np.asarray(P) * [KX, KY], distance_upper_bound=0.09)[0] < 0.09   # main roads: a route smoothed off their line
    route_d = lambda P: road_tree.query(np.asarray(P) * [KX, KY])[0]
    near_rail = lambda P: rail_tree.query(np.asarray(P) * [KX, KY], distance_upper_bound=0.06)[0] < 0.06

    g = json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"][0]["geometry"]
    irad = [Path(np.array(p[0])) for p in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])]
    in_irad = lambda pts: np.any([P.contains_points(np.asarray(pts)) for P in irad], axis=0)

    masks = [town_mask(s_) for s_ in SHRINK]

    def shrunk(pts, key=None):
        pts = np.asarray(pts, float); m = np.zeros(len(pts), bool)
        for (x0, y0, M) in masks:
            i = np.round((pts[:, 0] - x0) / SG).astype(int); j = np.round((pts[:, 1] - y0) / SG).astype(int)
            ok = (i >= 0) & (i < M.shape[1]) & (j >= 0) & (j < M.shape[0])
            m[ok] |= M[j[ok], i[ok]]
        return m

    stats = {}
    def count(k, n=1): stats[k] = stats.get(k, 0) + n

    lake_fix = lake_levels()
    for layer in ["transportation", "waterway", "water", "landcover", "landuse", "park", "building", "aeroway"]:
        out = []
        for f in load(layer):
            g = f["geometry"]; cls = f["properties"].get("class")
            if layer == "water" and cls == "lake" and lake_fix:
                g2 = lake_fix(g)
                if g2 is None: count("water duplicate dropped"); continue
                if g2 is not g: f["geometry"] = g = g2; count("water redrawn at its surface")
            if layer in SITE_LAYERS:
                cc = np.array(first_ring_pts(g) if g["type"] in ("Polygon", "MultiPolygon") else lines_of(g)[0]).mean(0)
                act = site_action(layer, cls, cc[0], cc[1])
                if act == "remove": count(f"{layer} site removed"); continue
                if act == "disused": f["properties"]["disused"] = 1; count(f"{layer} site disused")
            if layer in ("landuse", "aeroway"):      # names and refs are kept in the extract for the lore check only
                f["properties"] = {k: v for k, v in f["properties"].items() if k in ("class", "brunnel", "disused")}
            if layer in ("waterway", "water") or (layer == "landcover" and cls == "ice"):
                nm = nature_name(f["properties"])
                f["properties"] = {k: v for k, v in f["properties"].items() if not k.startswith("name")}
                if nm: f["properties"]["name"] = nm
            if g["type"] in ("Polygon", "MultiPolygon"):
                pts = np.array(first_ring_pts(g)); c0 = pts.mean(0)[None]
                if layer != "water" and layer != "landcover" and in_city(c0)[0]: count(layer + " in city"); continue
                if layer in ("water",) and in_city(pts).all(): continue
                if (layer in DETAIL_LAYERS) and shrunk(c0)[0]: count(layer + " shrunk"); continue
                out.append(f); continue
            # lines
            drops = [in_city]
            if layer == "transportation" and (cls in DETAIL_ROADS or (cls == "rail" and f["tippecanoe"]["minzoom"] > 8)): drops.append(shrunk)   # yards too
            if layer == "transportation" and cls == "tertiary": drops.append(shrunk)   # the old city's own streets
            if layer == "transportation" and cls in ("motorway", "trunk", "primary"): drops.append(near_road_wide)
            elif layer == "transportation" and cls in ("secondary", "tertiary", "minor"): drops.append(near_road)
            if layer == "transportation" and cls == "rail": drops.append(near_rail)
            drop = lambda P: np.any([d(P) for d in drops], axis=0)
            pieces = []
            for c in lines_of(g): pieces += cut_line(c, drop)
            whole = len(pieces) == 1 and len(pieces[0]) == len(lines_of(g)[0])
            if not whole and layer == "transportation":    # stubs left over by the cuts (hooks beside a route) go
                pieces = [q for q in pieces if sum(math.hypot((a[0] - b_[0]) * KX, (a[1] - b_[1]) * KY) for a, b_ in zip(q, q[1:])) > 0.3]
            if layer == "transportation" and cls in ("motorway", "trunk", "primary", "secondary"):
                # slip roads and loops of an interchange the route has taken over: short pieces with both ends on the route
                def ramp(q):
                    Q = np.array(q); L = float(np.hypot(*np.diff(Q * [KX, KY], axis=0).T).sum())
                    return L < 1.5 and route_d(Q[[0, -1]]).min() < 0.25 and np.median(route_d(Q)) < 0.4
                pieces = [q for q in pieces if not ramp(q)]
            if not pieces: count(layer + " dropped"); continue
            if len(pieces) > 1 or len(pieces[0]) != len(lines_of(g)[0]): count(layer + " cut")
            props = dict(f["properties"])
            if layer == "transportation" and cls == "rail":
                allp = np.array([p for q in pieces for p in q])
                if in_irad(allp[::max(1, len(allp) // 20)]).mean() > 0.5: props["disused"] = 1; count("rail disused")
            f["geometry"] = {"type": "LineString", "coordinates": pieces[0]} if len(pieces) == 1 else {"type": "MultiLineString", "coordinates": pieces}
            f["properties"] = props
            out.append(f)
        if layer == "transportation": out = prune_orphans(out, route_d, count)
        if layer == "waterway":
            out = merge_named(out, count)
            with open(os.path.join(OUT, "waterlabel.ndjson"), "w") as fo:      # smoothed copies of the named rivers to hang their names on
                for f in out:
                    if f["properties"].get("name") and f["geometry"]["type"] == "LineString" and len(f["geometry"]["coordinates"]) > 3:
                        c = label_line(f["geometry"]["coordinates"])
                        if c: fo.write(json.dumps({"type": "Feature", "tippecanoe": {"layer": "waterlabel", "minzoom": max(8, f["tippecanoe"]["minzoom"])},
                                                   "properties": f["properties"], "geometry": {"type": "LineString", "coordinates": c}}, separators=(",", ":"), ensure_ascii=False) + "\n")
        with open(os.path.join(OUT, layer + ".ndjson"), "w") as fo:
            for f in out: fo.write(json.dumps(f, separators=(",", ":")) + "\n")
        print(f"  {layer}: {len(out)}")
    with open(os.path.join(OUT, "city.ndjson"), "w") as fo:
        for f in city_out: fo.write(json.dumps(f, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"  city: {len(city_out)}")
    for k, v in sorted(stats.items()): print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
