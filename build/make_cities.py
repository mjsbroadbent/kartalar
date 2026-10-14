"""Borrow real street plans for the Iradi cities.

Each Iradi city takes the streets, buildings and land use of a real donor city of about its size (from
tools/city-export.html), moved, turned (or mirrored) and scaled onto the Iradi site, then clipped to the ground the
city can actually occupy there (valley floor, below the foothills, off the airfield, clear of the next town).
Outputs, per city, under data/city/:
  <name>/overview.json   main roads, land use, canals and the real rivers (for zoom 10-13)
  <name>/t_<i>_<j>.json   everything, in 0.02-degree tiles (for zoom 13+)
  index.json             the cities, their tile lists and their footprints (the mask that hides the base map)
Lore routes that cross a city are re-laid along the borrowed main streets inside it (data/routes.json).
Run: python3 build/make_cities.py irad-dem.bin irad-osm-roads.json <dir with city-<donor>.json files>
"""
import json, math, os, struct, sys, heapq
import numpy as np
from scipy import ndimage
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, OSMF, CDIR = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(ROOT, "data/city")

# ---------- the cities ----------
CITIES = [
    {"name": "talas", "donor": "bishkek", "pivot_donor": (74.6037, 42.8765), "pivot": (72.240, 42.519), "rotate": 0, "mirror": False,
     "scale": 1.0, "donor_r_km": 13.5,
     # the Talas valley floor below the foothills, off Talas Air Base
     "ellipse": ((72.225, 42.515), 12.5, 8.5), "max_elev": 1420, "max_slope": 0.09,
     "exclude": [[(72.055, 42.517), (72.13, 42.517), (72.13, 42.548), (72.055, 42.548)]],
     "rivers": ["Талас"]},
    {"name": "nurzhan", "donor": "shymkent", "pivot_donor": (69.5875, 42.3155), "pivot": (73.760, 43.600), "rotate": 45, "mirror": False,
     "scale": 0.92, "donor_r_km": 11.5,
     "ellipse": ((73.77, 43.60), 11.5, 10.5), "max_elev": 900, "max_slope": 0.08,
     "exclude": [], "donor_exclude": [[(69.715, 42.265), (69.77, 42.265), (69.77, 42.325), (69.715, 42.325)]],   # a tile that failed to download
     "rivers": ["Чу"]},
    {"name": "iyik-janyl", "donor": "osh", "pivot_donor": (72.7856, 40.5274), "pivot": (72.2525, 41.3935), "rotate": 0, "mirror": True,
     "scale": 1.0, "donor_r_km": 10.5,
     # the river flats of the Naryn: no higher than ~110 m above the river, north of Tash-Kömür; Cathedral Hill itself
     "ellipse": ((72.23, 41.415), 9.5, 9.0), "above_river": 170, "max_slope": 0.15, "min_lat": 41.372,
     "keep_round": [((72.2525, 41.3935), 0.9)],
     "exclude": [], "rivers": ["Нарын"]},
]
GRID = 0.0005           # ~45 m clipping grid
TILE = 0.02

b = open(DEMF, "rb").read()
d_lon0, d_lat0, d_st = struct.unpack("<3d", b[8:32]); d_nx, d_ny = struct.unpack("<2i", b[32:40])
DEM = ndimage.median_filter(np.frombuffer(b[64:], dtype="<i2").reshape(d_ny, d_nx).astype(float), 3)


def dem(lon, lat):
    return ndimage.map_coordinates(DEM, [(np.asarray(lat) - d_lat0) / d_st, (np.asarray(lon) - d_lon0) / d_st], order=1, mode="nearest")


OSM = json.load(open(OSMF))["ways"]


def kx(lat): return 111.32 * math.cos(math.radians(lat))
KY = 110.57


# ---------- classify donor features ----------
ROAD = {"motorway": "major", "trunk": "major", "primary": "major", "motorway_link": "major", "trunk_link": "major", "primary_link": "major",
        "secondary": "mid", "secondary_link": "mid", "tertiary": "mid", "tertiary_link": "mid",
        "residential": "minor", "unclassified": "minor", "living_street": "minor", "pedestrian": "minor", "road": "minor",
        "service": "service", "footway": "path", "path": "path", "track": "path", "steps": "path", "cycleway": "path"}
LAND = {"residential": "residential", "commercial": "commercial", "retail": "commercial", "industrial": "industrial", "railway": "industrial",
        "garages": "industrial", "cemetery": "cemetery", "grass": "grass", "recreation_ground": "park", "village_green": "grass",
        "farmland": "farm", "orchard": "farm", "allotments": "farm", "meadow": "grass", "forest": "wood", "military": "industrial",
        "brownfield": "industrial", "greenfield": "grass", "religious": "institution", "education": "institution", "plant_nursery": "farm"}
LEISURE = {"park": "park", "garden": "park", "pitch": "pitch", "stadium": "pitch", "playground": "park", "sports_centre": "pitch"}
AMENITY = {"school": "institution", "university": "institution", "college": "institution", "hospital": "institution",
           "marketplace": "commercial", "parking": "parking", "grave_yard": "cemetery"}


def classify(f):
    k = f["k"]
    if k == "building": return ("building", None)
    if k.startswith("hw:"):
        c = ROAD.get(k[3:]); return ("road", c) if c else None
    if k.startswith("landuse:"):
        c = LAND.get(k[8:]); return ("land", c) if c else None
    if k.startswith("leisure:"):
        c = LEISURE.get(k[8:]); return ("land", c) if c else None
    if k.startswith("amenity:"):
        c = AMENITY.get(k[8:]); return ("land", c) if c else None
    if k in ("ww:canal", "ww:ditch", "ww:drain", "ww:stream"): return ("canal", "canal" if k == "ww:canal" else "ditch")
    if k == "rail:rail" and not (f.get("t") or {}).get("service"): return ("rail", "rail")
    if k == "rail:rail": return ("rail", "siding")
    return None


def rings_of(f):
    return f["c"] if f.get("multi") else [f["c"]]


# ---------- per city ----------
def build(C):
    donor = json.load(open(os.path.join(CDIR, f"city-{C['donor']}.json")))
    pdx, pdy = C["pivot_donor"]; tx, ty = C["pivot"]
    kd, kt = kx(pdy), kx(ty)
    a = math.radians(C["rotate"]); ca, sa = math.cos(a), math.sin(a); sc = C["scale"]; mir = -1 if C["mirror"] else 1
    dex = [Path(np.array(p)) for p in C.get("donor_exclude", [])]

    def tf(pts):
        P = np.asarray(pts, float)
        x = (P[:, 0] - pdx) * kd * mir; y = (P[:, 1] - pdy) * KY
        xr, yr = (x * ca - y * sa) * sc, (x * sa + y * ca) * sc
        return np.column_stack([tx + xr / kt, ty + yr / KY])

    # allowed ground at the target
    (ex, ey), ea, eb = C["ellipse"]
    lons = np.arange(ex - ea / kt - 0.01, ex + ea / kt + 0.01, GRID); lats = np.arange(ey - eb / KY - 0.01, ey + eb / KY + 0.01, GRID)
    GX, GY = np.meshgrid(lons, lats)
    E = dem(GX.ravel(), GY.ravel()).reshape(GX.shape)
    gy_, gx_ = np.gradient(ndimage.gaussian_filter(E, 2), GRID * KY * 1000, GRID * kt * 1000)
    slope = np.hypot(gx_, gy_)
    ok = (((GX - ex) * kt / ea) ** 2 + ((GY - ey) * KY / eb) ** 2 <= 1) & (slope <= C["max_slope"])
    if "max_elev" in C: ok &= E <= C["max_elev"]
    riv_pts = np.array([p for w in OSM if w["k"] == "water:river" and (w.get("n") or "") in C["rivers"] for p in w["c"]
                        if lons[0] - 0.05 < p[0] < lons[-1] + 0.05 and lats[0] - 0.05 < p[1] < lats[-1] + 0.05])
    riv = np.zeros(GX.shape, bool)
    for w in OSM:
        if w["k"] == "water:river" and (w.get("n") or "") in C["rivers"]:
            c = w["c"]
            for (x1, y1), (x2, y2) in zip(c, c[1:]):
                n = int(max(abs(x2 - x1), abs(y2 - y1)) / (GRID / 2)) + 1
                for t in np.linspace(0, 1, n + 1):
                    i = int(round((x1 + (x2 - x1) * t - lons[0]) / GRID)); j = int(round((y1 + (y2 - y1) * t - lats[0]) / GRID))
                    if 0 <= j < GX.shape[0] and 0 <= i < GX.shape[1]: riv[j, i] = True
    dr, (rj, ri) = ndimage.distance_transform_edt(~riv, return_indices=True)
    if "above_river" in C:
        ok &= E <= E[rj, ri] + C["above_river"]
    if "min_lat" in C: ok &= GY >= C["min_lat"]
    for poly in C["exclude"]:
        ok &= ~Path(np.array(poly)).contains_points(np.column_stack([GX.ravel(), GY.ravel()])).reshape(GX.shape)
    for (cx, cy), r in C.get("keep_round", []):
        ok |= np.hypot((GX - cx) * kt, (GY - cy) * KY) <= r
    ok = ndimage.binary_opening(ok, iterations=2)
    ok = ndimage.binary_fill_holes(ndimage.binary_closing(ok, iterations=3))
    lab, n = ndimage.label(ok)
    j0, i0 = int(round((ty - lats[0]) / GRID)), int(round((tx - lons[0]) / GRID))
    sizes = ndimage.sum(ok, lab, range(1, n + 1))
    main = lab[j0, i0] or (1 + int(np.argmax(sizes)))
    ok = lab == main
    near_river = dr * GRID * KY * 1000 < 60      # no buildings or side streets in the river

    def cell_ok(x, y, arr=ok):
        i = np.round((np.asarray(x) - lons[0]) / GRID).astype(int); j = np.round((np.asarray(y) - lats[0]) / GRID).astype(int)
        inb = (i >= 0) & (i < GX.shape[1]) & (j >= 0) & (j < GX.shape[0])
        out = np.zeros(len(np.atleast_1d(x)), bool)
        out[inb] = arr[j[inb], i[inb]]
        return out

    feats = []
    rd = C["donor_r_km"]
    for f in donor["features"]:
        cl = classify(f)
        if not cl: continue
        kind, sub = cl
        rr = rings_of(f)
        p0 = rr[0][0]
        if math.hypot((p0[0] - pdx) * kd, (p0[1] - pdy) * KY) > rd: continue
        if dex and any(pth.contains_point(p0) for pth in dex): continue
        if kind == "building":
            r = rr[0]
            if len(r) < 4: continue
            T = tf(r)
            if not cell_ok(T[:, 0], T[:, 1]).all(): continue
            if cell_ok(T[:, 0], T[:, 1], near_river).any(): continue
            lv = (f.get("t") or {}).get("building:levels")
            props = {"k": "building"}
            try:
                if lv and float(lv) >= 5: props["tall"] = 1
            except ValueError: pass
            feats.append(("building", props, [T]))
        elif kind == "land":
            parts = []
            for r in rr:
                if len(r) < 4: continue
                T = tf(r); okv = cell_ok(T[:, 0], T[:, 1])
                if okv.mean() >= 0.75: parts.append(T)
            if parts: feats.append(("land", {"k": sub}, parts))
        else:   # lines: roads and canals, cut where they leave the allowed ground
            for r in rr:
                if len(r) < 2: continue
                # densify long segments so the clip follows the ground
                pts = [r[0]]
                for (x1, y1), (x2, y2) in zip(r, r[1:]):
                    L = math.hypot((x2 - x1) * kd, (y2 - y1) * KY); n = max(1, int(L / 0.06))
                    for t in range(1, n + 1): pts.append([x1 + (x2 - x1) * t / n, y1 + (y2 - y1) * t / n])
                T = tf(pts); okv = cell_ok(T[:, 0], T[:, 1])
                if not (kind == "road" and sub in ("major", "mid")):
                    okv &= ~cell_ok(T[:, 0], T[:, 1], near_river)   # only the main streets bridge the river
                run = []
                for p, o in zip(T, okv):
                    if o: run.append(p)
                    else:
                        if len(run) >= 2: feats.append((kind, {"k": sub}, [np.array(run)]))
                        run = []
                if len(run) >= 2: feats.append((kind, {"k": sub}, [np.array(run)]))
    # footprint: built-up ground (buildings and streets), smoothed, inside the allowed ground
    fp = np.zeros(GX.shape, bool)
    for kind, props, parts in feats:
        if kind in ("building", "road") and props.get("k") not in ("path",):  # (railways do not make a town)
            for T in parts:
                i = np.round((T[:, 0] - lons[0]) / GRID).astype(int); j = np.round((T[:, 1] - lats[0]) / GRID).astype(int)
                m = (i >= 0) & (i < GX.shape[1]) & (j >= 0) & (j < GX.shape[0]); fp[j[m], i[m]] = True
    fp = ndimage.binary_closing(ndimage.binary_dilation(fp, iterations=3), iterations=6)
    fp = ndimage.binary_fill_holes(fp) & ndimage.binary_dilation(ok, iterations=3)
    lab, n = ndimage.label(fp)
    sizes = ndimage.sum(fp, lab, range(1, n + 1))
    fp = np.isin(lab, 1 + np.where(sizes >= 40)[0])
    fp = ndimage.binary_fill_holes(fp)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig = plt.figure(); cs = plt.contour(GX, GY, ndimage.gaussian_filter(fp.astype(float), 1.2), levels=[0.5]); segs = cs.allsegs[0]; plt.close(fig)
    rings = [s for s in segs if len(s) > 8]
    rings.sort(key=lambda s: -abs(np.sum(s[:-1, 0] * s[1:, 1] - s[1:, 0] * s[:-1, 1])))
    polys = []
    for s in rings:
        r = [[round(float(x), 5), round(float(y), 5)] for x, y in s]
        if r[0] != r[-1]: r.append(r[0])
        host = next((P for P in polys if Path(np.array(P[0])).contains_point(r[0])), None)
        if host is not None: host.append(r)
        else: polys.append([r])
    footprint = {"type": "MultiPolygon", "coordinates": polys}
    fpath = [[Path(np.array(r)) for r in P] for P in polys]
    in_fp = lambda x, y: any(P[0].contains_point((x, y)) and not any(h.contains_point((x, y)) for h in P[1:]) for P in fpath)
    # the real river inside the city (the base map is hidden there)
    rivers = []
    for w in OSM:
        if w["k"] == "water:river" and (w.get("n") or "") in C["rivers"]:
            run = []
            for p in w["c"]:
                if in_fp(*p) or (run and in_fp(*run[-1])): run.append(p)
                else:
                    if len(run) >= 2: rivers.append(run)
                    run = []
            if len(run) >= 2: rivers.append(run)
    return feats, footprint, rivers, (lons, lats, ok)


def gj(kind, props, parts):
    if kind == "building" or kind == "land":
        rings = [[[round(float(x), 5), round(float(y), 5)] for x, y in T] for T in parts]
        rings = [r if r[0] == r[-1] else r + [r[0]] for r in rings]
        geom = {"type": "Polygon", "coordinates": [rings[0]]} if len(rings) == 1 else {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
    else:
        geom = {"type": "LineString", "coordinates": [[round(float(x), 5), round(float(y), 5)] for x, y in parts[0]]}
    p = dict(props); p["t"] = kind
    return {"type": "Feature", "properties": p, "geometry": geom}


def thin_line(c, eps_m=4):
    """drop near-collinear points (RDP in metres) so the densified clip points don't bloat the files"""
    if len(c) < 3: return c
    P = np.asarray(c); a, b_ = P[0], P[-1]; k = kx(P[0, 1])
    v = (b_ - a) * [k * 1000, KY * 1000]; rel = (P - a) * [k * 1000, KY * 1000]; n_ = math.hypot(*v)
    d = np.abs(v[0] * rel[:, 1] - v[1] * rel[:, 0]) / n_ if n_ else np.hypot(*rel.T)
    i = int(np.argmax(d))
    if d[i] > eps_m: return np.vstack([thin_line(P[: i + 1], eps_m)[:-1], thin_line(P[i:], eps_m)])
    return np.vstack([a, b_])


# ---------- re-lay the lore routes inside each city along its borrowed main streets ----------
def relay_routes(cities_out):
    routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
    for name, feats, footprint in cities_out:
        fpath = [[Path(np.array(r)) for r in P] for P in footprint["coordinates"]]
        in_fp = lambda x, y: any(P[0].contains_point((x, y)) and not any(h.contains_point((x, y)) for h in P[1:]) for P in fpath)
        from scipy.spatial import cKDTree

        def graph(want):
            idx, coords, adj = {}, [], {}
            for kind, props, parts in feats:
                if (kind, props["k"]) not in want: continue
                T = parts[0]; w = want[(kind, props["k"])]; prev = None
                for x, y in T:
                    key = (round(float(x), 4), round(float(y), 4))
                    if key not in idx: idx[key] = len(coords); coords.append(key); adj[idx[key]] = []
                    cur = idx[key]
                    if prev is not None and prev != cur:
                        L = math.hypot((coords[prev][0] - key[0]) * kx(key[1]), (coords[prev][1] - key[1]) * KY) * w
                        adj[prev].append((cur, L)); adj[cur].append((prev, L))
                    prev = cur
            if not coords: return None
            # snap only to the main connected network (clipping leaves stray bits)
            comp = [-1] * len(coords); best = (0, -1); cid = 0
            for s0 in range(len(coords)):
                if comp[s0] >= 0: continue
                stack = [s0]; comp[s0] = cid; size = 0
                while stack:
                    u = stack.pop(); size += 1
                    for v, _ in adj[u]:
                        if comp[v] < 0: comp[v] = cid; stack.append(v)
                if size > best[0]: best = (size, cid)
                cid += 1
            keep = [i for i in range(len(coords)) if comp[i] == best[1]]
            C = np.array([coords[i] for i in keep])
            class Tree:
                def __init__(s_): s_.t = cKDTree(np.column_stack([C[:, 0] * kx(C[0, 1]), C[:, 1] * KY]))
                def query(s_, q): d, i = s_.t.query(q); return d, keep[i]
            return coords, adj, Tree(), kx(C[0, 1])

        G_road = graph({("road", "major"): 1.0, ("road", "mid"): 1.3, ("road", "minor"): 3.5})
        G_rail = graph({("rail", "rail"): 1.0, ("rail", "siding"): 1.6})

        def path(G, a_pt, b_pt):
            coords, adj, tree, k_ = G
            da, a = tree.query([a_pt[0] * k_, a_pt[1] * KY]); db, b_ = tree.query([b_pt[0] * k_, b_pt[1] * KY])
            lim = 3.0 if G is G_rail else 1.5
            if da > lim or db > lim or a == b_: return None
            dist = {a: 0.0}; prev = {}; pq = [(0.0, a)]
            while pq:
                d, u = heapq.heappop(pq)
                if u == b_: break
                if d > dist.get(u, 1e18): continue
                for v, w in adj[u]:
                    nd = d + w
                    if nd < dist.get(v, 1e18): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
            if b_ not in dist: return None
            out = [b_]
            while out[-1] != a: out.append(prev[out[-1]])
            return [list(coords[i]) for i in reversed(out)]

        def densify(c, step=0.1):
            out = [c[0]]
            for (x1, y1), (x2, y2) in zip(c, c[1:]):
                L = math.hypot((x2 - x1) * kx(y1), (y2 - y1) * KY); n = max(1, int(L / step))
                for t in range(1, n + 1): out.append([x1 + (x2 - x1) * t / n, y1 + (y2 - y1) * t / n])
            return out

        for r in routes:
            if r["kind"] not in ("highway", "road", "railway"): continue
            G = G_rail if r["kind"] == "railway" else G_road
            if G is None: continue
            c = densify(r["coords"]); inside = [in_fp(*p) for p in c]
            if not any(inside): continue
            out, i, did = [], 0, False
            while i < len(c):
                if not inside[i]: out.append(c[i]); i += 1; continue
                j = i
                while j < len(c) and inside[j]: j += 1
                pth = path(G, c[i], c[j - 1])
                if pth and len(pth) >= 2:
                    out += pth; did = True
                else:
                    out += c[i:j]
                i = j
            r["coords"] = [[round(x, 5), round(y, 5)] for x, y in thin_line(np.array(out), 3)]
            if did:
                r.setdefault("in_city", [])
                if name not in r["in_city"]: r["in_city"].append(name)
    json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
    # stations follow their line: the terminus to the end of the re-laid branch, junction stations onto the nearest track
    R = {r["id"]: r for r in routes}
    F = json.load(open(os.path.join(ROOT, "data/features.json")))
    SNAP = {"talas-railway-station": ("irad-temir-jolu-talas-branch", "end"), "nurzhan-station": ("irad-temir-jolu-chu-line", "near"),
            "nurzhan-rail-freight-depot": ("irad-temir-jolu-north-line", "near")}
    for f in F:
        if f["id"] in SNAP and SNAP[f["id"]][0] in R:
            c = R[SNAP[f["id"]][0]]["coords"]
            q = c[-1] if SNAP[f["id"]][1] == "end" else min(c, key=lambda p: (p[0] - f["lon"]) ** 2 + (p[1] - f["lat"]) ** 2)
            print(f"  {f['id']}: {f['lat']},{f['lon']} -> {q[1]},{q[0]}")
            f["lon"], f["lat"] = q
    json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    index = {"tile": TILE, "cities": []}
    outs = []
    for C in CITIES:
        feats, footprint, rivers, _ = build(C)
        d = os.path.join(OUT, C["name"]); os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d): os.remove(os.path.join(d, fn))
        tiles = {}
        overview = []
        for kind, props, parts in feats:
            if kind in ("road", "canal", "rail"): parts = [thin_line(parts[0])]
            f = gj(kind, props, parts)
            x, y = parts[0][0]
            key = (int(math.floor(x / TILE)), int(math.floor(y / TILE)))
            if (kind == "road" and props["k"] in ("major", "mid")) or (kind == "canal" and props["k"] == "canal") or kind in ("land", "rail"):
                overview.append(f)          # drawn from the overview at every zoom
            else:
                tiles.setdefault(key, []).append(f)
        for r in rivers:
            overview.append({"type": "Feature", "properties": {"t": "river"}, "geometry": {"type": "LineString", "coordinates": r}})
        tl = []
        for (i, j), fs in tiles.items():
            fn = f"t_{i}_{j}.json"
            json.dump({"type": "FeatureCollection", "features": fs}, open(os.path.join(d, fn), "w"), separators=(",", ":"))
            tl.append([i, j])
        json.dump({"type": "FeatureCollection", "features": overview}, open(os.path.join(d, "overview.json"), "w"), separators=(",", ":"))
        xs = [p[0] for P in footprint["coordinates"] for p in P[0]]; ys = [p[1] for P in footprint["coordinates"] for p in P[0]]
        index["cities"].append({"name": C["name"], "donor": C["donor"], "bbox": [min(xs), min(ys), max(xs), max(ys)], "tiles": sorted(tl), "footprint": footprint})
        nb = sum(1 for k, _, _ in feats if k == "building")
        size = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
        area = 0.0
        for P in footprint["coordinates"]:
            for h, r in enumerate(P):
                x = np.array([q[0] for q in r]) * kx(C["pivot"][1]); y = np.array([q[1] for q in r]) * KY
                a_ = 0.5 * abs(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1])); area += a_ if h == 0 else -a_
        print(f"{C['name']:11} from {C['donor']:9} {len(feats):6} features, {nb:6} buildings, {len(tl):3} tiles, {size/1e6:5.1f} MB, built-up {area:5.0f} km2")
        outs.append((C["name"], feats, footprint))
    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
    relay_routes(outs)
