"""Route Iradi roads, railways and lines over the real terrain.

Each route is a cheapest path through a combined graph:
  - the real OpenStreetMap roads (or railways), used as they are, cheaper the better the road;
  - a fine terrain grid (0.0025 deg, upsampled from the DEM) where new road would have to be built.
Grid steps cost more on steep climbs (beyond the route's ruling grade a road needs hairpins), on steep side
slopes and high up. So the path keeps to real main roads where they serve, runs straight across flat land
where the real roads only wander, and finds valleys and the lowest passes in the mountains.
The new-built stretches are straightened (RDP), rounded (Chaikin) and, where they still climb faster than
the ruling grade, given hairpin bends.

Run after build/snap_routes.py:  python3 build/route_terrain.py irad-dem.bin irad-osm-roads.json
"""
import json, math, os, struct, sys
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, OSMF = sys.argv[1], sys.argv[2]
ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57
RES = float(os.environ.get("ROUTE_RES", "0.0015"))   # ~130 m grid (the terrain grid is ~90 m)

b = open(DEMF, "rb").read()
D_LON0, D_LAT0, D_STEP = struct.unpack("<3d", b[8:32]); D_NX, D_NY = struct.unpack("<2i", b[32:40])
DEM = np.frombuffer(b[64:], dtype="<i2").reshape(D_NY, D_NX).astype(float)
DEM = ndimage.median_filter(DEM, 3) if D_STEP > 0.002 else ndimage.gaussian_filter(DEM, 0.8)   # the terrarium tiles have speckle
OSM = json.load(open(OSMF))["ways"]


def dem_at(lon, lat):
    x = (np.asarray(lon) - D_LON0) / D_STEP; y = (np.asarray(lat) - D_LAT0) / D_STEP
    return ndimage.map_coordinates(DEM, [np.atleast_1d(y), np.atleast_1d(x)], order=1, mode="nearest")


def km(a, b_):
    return math.hypot((a[0] - b_[0]) * KX, (a[1] - b_[1]) * KY)


def km_len(c):
    return sum(km(a, b_) for a, b_ in zip(c, c[1:]))


def rdp(pts, eps):
    if len(pts) < 3:
        return list(pts)
    P = np.asarray(pts); a, b_ = P[0], P[-1]; v = (b_ - a) * [KX, KY]; n = math.hypot(*v)
    rel = (P - a) * [KX, KY]
    d = np.abs(v[0] * rel[:, 1] - v[1] * rel[:, 0]) / n if n else np.hypot(*rel.T)
    i = int(np.argmax(d))
    if d[i] > eps:
        return rdp(pts[: i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


def chaikin(pts, n=2):
    for _ in range(n):
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        for a, b_ in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b_[0], 0.75 * a[1] + 0.25 * b_[1]), (0.25 * a[0] + 0.75 * b_[0], 0.25 * a[1] + 0.75 * b_[1])]
        out.append(pts[-1])
        pts = out
    return pts


ROAD_F = {"road:motorway": 1.0, "road:trunk": 1.0, "road:primary": 1.05, "road:secondary": 1.2, "road:tertiary": 1.5,
          "road:motorway_link": 1.3, "road:trunk_link": 1.3, "road:primary_link": 1.3,
          "road:unclassified": 1.9, "road:track": 2.6}      # an old road or track up a valley is cheaper to upgrade than new road
RIVERS = None   # rasterised real rivers: building across or along one costs a bridge
RAIL_F = {"rail:rail": 1.0, "rail:narrow_gauge": 1.3}
NB = [(0, 1), (1, 0), (1, 1), (1, -1), (1, 2), (2, 1), (1, -2), (2, -1)]   # half of a 16-neighbourhood


def route(spec):
    wps = spec["via"]
    kind = spec.get("kind", "road")
    gmax = spec.get("gmax", 0.06 if kind == "road" else 0.018)
    build = spec.get("build", 1.15)
    netf = {"road": ROAD_F, "rail": RAIL_F, "none": {}}[spec.get("net", kind)]
    netf = {k: v * spec.get("net_scale", {}).get(k, 1.0) for k, v in netf.items()}
    xs = [p[0] for p in wps]; ys = [p[1] for p in wps]
    m = spec.get("margin", 0.12)
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    lons = np.arange(x0, x1 + RES / 2, RES); lats = np.arange(y0, y1 + RES / 2, RES)
    GX, GY = np.meshgrid(lons, lats); ny, nx = GX.shape
    Z = dem_at(GX.ravel(), GY.ravel()).reshape(ny, nx)
    Z = ndimage.gaussian_filter(Z, 0.7)
    gy, gx = np.gradient(Z, RES * KY * 1000, RES * KX * 1000)
    side = np.hypot(gx, gy)
    from matplotlib.path import Path
    avoid_paths = [Path(np.asarray(poly)) for poly in spec.get("avoid", [])]
    avoid = np.zeros_like(Z, bool)
    for poly in spec.get("avoid", []):
        avoid |= Path(np.asarray(poly)).contains_points(np.column_stack([GX.ravel(), GY.ravel()])).reshape(ny, nx)
    # the side of the nearest river each cell lies on (+1 / -1 within ~300 m of a river, 0 elsewhere): a step from one
    # side to the other is a river crossing and costs a bridge; running along the valley floor beside the river does not
    side_r = np.zeros(Z.shape, np.int8)
    rp, rt = [], []
    for c in (RIVERS or []):
        if c[:, 0].max() < x0 or c[:, 0].min() > x1 or c[:, 1].max() < y0 or c[:, 1].min() > y1: continue
        P = c * [KX, KY]
        for a_, b2 in zip(P[:-1], P[1:]):
            L_ = math.hypot(*(b2 - a_)); n_ = max(1, int(L_ / 0.03)); t_ = (b2 - a_) / (L_ + 1e-12)
            for k in range(n_): rp.append(a_ + (b2 - a_) * k / n_); rt.append(t_)
    if rp:
        rp = np.array(rp); rt = np.array(rt); tree_r = cKDTree(rp)
        G2 = np.column_stack([GX.ravel() * KX, GY.ravel() * KY])
        d_, k_ = tree_r.query(G2, distance_upper_bound=0.3)
        near = np.isfinite(d_); kk = k_[near]
        rel = G2[near] - rp[kk]
        cr = rt[kk, 0] * rel[:, 1] - rt[kk, 1] * rel[:, 0]
        sv = np.zeros(len(G2), np.int8); sv[near] = np.sign(cr).astype(np.int8)
        side_r = sv.reshape(Z.shape)
    N = ny * nx
    idx = np.arange(N).reshape(ny, nx)
    rows, cols, wts = [], [], []
    for dj, di in NB:
        for sgn in (1,):
            j0, j1 = max(0, -dj), ny - max(0, dj); i0, i1 = max(0, -di), nx - max(0, di)
            A = idx[j0:j1, i0:i1]; B = idx[j0 + dj:j1 + dj, i0 + di:i1 + di]
            L = math.hypot(di * RES * KX, dj * RES * KY)
            za = Z[j0:j1, i0:i1]; zb = Z[j0 + dj:j1 + dj, i0 + di:i1 + di]
            g = np.abs(zb - za) / (L * 1000)
            fg = np.where(g <= gmax, 1 + 0.5 * (g / gmax) ** 2, 1.5 * g / gmax)
            fg = fg * np.where(g > 4 * gmax, 6.0, 1.0)
            s = 0.5 * (side[j0:j1, i0:i1] + side[j0 + dj:j1 + dj, i0 + di:i1 + di])
            fs = 1 + spec.get("side_w", 3.0) * np.maximum(0, s - 0.18)
            zm = 0.5 * (za + zb)
            fe = 1 + np.maximum(0, (zm - spec.get("snowline", 2600)) / 400.0)
            av = 1 + 50 * (avoid[j0:j1, i0:i1] | avoid[j0 + dj:j1 + dj, i0 + di:i1 + di])
            rv = spec.get("bridge_km", 0.8) * ((side_r[j0:j1, i0:i1].astype(np.int16) * side_r[j0 + dj:j1 + dj, i0 + di:i1 + di]) < 0)
            w = L * build * fg * fs * fe * av + rv
            rows.append(A.ravel()); cols.append(B.ravel()); wts.append(w.ravel())
    rows = np.concatenate(rows); cols = np.concatenate(cols); wts = np.concatenate(wts)
    # real network nodes, numbered after the grid
    net_coords, net_idx, er, ec, ew = [], {}, [], [], []
    for way in OSM:
        f = netf.get(way["k"])
        if f is None:
            continue
        c = way["c"]
        if max(p[0] for p in c) < x0 or min(p[0] for p in c) > x1 or max(p[1] for p in c) < y0 or min(p[1] for p in c) > y1:
            continue
        prev = None
        for p in c:
            if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1) or any(ap.contains_point(p) for ap in avoid_paths):
                prev = None; continue
            key = (p[0], p[1]); k = net_idx.get(key)
            if k is None:
                k = net_idx[key] = len(net_coords); net_coords.append(key)
            if prev is not None and prev != k:
                d = km(net_coords[prev], key) * f + 1e-6
                er += [prev, k]; ec += [k, prev]; ew += [d, d]
            prev = k
    M = len(net_coords)
    if M:
        nc = np.array(net_coords)
        gi = np.clip(np.round((nc[:, 0] - x0) / RES).astype(int), 0, nx - 1); gj = np.clip(np.round((nc[:, 1] - y0) / RES).astype(int), 0, ny - 1)
        link = np.hypot((nc[:, 0] - lons[gi]) * KX, (nc[:, 1] - lats[gj]) * KY) * build + 0.03
        er = np.concatenate([np.array(er, int) + N, np.arange(M) + N, idx[gj, gi]])
        ec = np.concatenate([np.array(ec, int) + N, idx[gj, gi], np.arange(M) + N])
        ew = np.concatenate([np.array(ew), link, link])
    rows = np.concatenate([rows, cols, er if M else []]).astype(int)
    cols2 = np.concatenate([cols, rows[:len(cols)], ec if M else []]).astype(int)
    wts = np.concatenate([wts, wts, ew if M else []])
    G = coo_matrix((wts, (rows, cols2)), shape=(N + M, N + M)).tocsr()

    ntree = cKDTree(np.column_stack([np.array(net_coords)[:, 0] * KX, np.array(net_coords)[:, 1] * KY])) if M else None

    def node_of(p, snap=False):
        if snap and ntree is not None:
            d, k = ntree.query([p[0] * KX, p[1] * KY])
            if d <= spec.get("snap_km", 1.5):
                return N + int(k)
        i = int(round((p[0] - x0) / RES)); j = int(round((p[1] - y0) / RES))
        return idx[min(max(j, 0), ny - 1), min(max(i, 0), nx - 1)]

    def coord(n):
        if n >= N:
            return net_coords[n - N], True
        j, i = divmod(n, nx)
        return (float(lons[i]), float(lats[j])), False

    seq = []   # list of (lon, lat, on_real_network)
    for k_, (a, b_) in enumerate(zip(wps, wps[1:])):
        s, t = node_of(a, k_ > 0), node_of(b_, k_ + 1 < len(wps) - 1)
        dist, pred = dijkstra(G, indices=s, return_predecessors=True)
        if not np.isfinite(dist[t]):
            raise SystemExit(f"{spec['id']}: no path {a} -> {b_}")
        path, n = [], t
        while n != s and n >= 0:
            path.append(n); n = pred[n]
        path.append(s); path.reverse()
        pts = [coord(n) for n in path]
        if seq:
            pts = pts[1:]
        seq += [(p[0], p[1], real) for p, real in pts]
    # the exact waypoints at the ends
    seq[0] = (wps[0][0], wps[0][1], False); seq[-1] = (wps[-1][0], wps[-1][1], False)
    # split into runs: real network vs new-built
    runs, cur, cur_real = [], [], seq[0][2]
    for x, y, real in seq:
        if real != cur_real and cur:
            runs.append((cur_real, cur)); cur = [cur[-1]] if not real else [cur[-1]]
            cur_real = real
        cur.append((x, y))
    runs.append((cur_real, cur))
    # very short new-built links between two real stretches are just junctions
    out = []
    eps = spec.get("eps", 0.06 if kind == "road" else 0.12)
    for real, pts in runs:
        if real:
            pts = rdp(pts, 0.012)
        else:
            pts = rdp(pts, eps)
            pts = chaikin(pts, spec.get("chaikin", 2 if kind == "road" else 3))
            if kind == "road" and spec.get("hairpins", True):
                pts = hairpins(pts, gmax * spec.get("hairpin_grade", 1.25))
        out += pts if not out else pts[1:]
    out = [(round(x, 5), round(y, 5)) for x, y in out]
    clean = []
    for p in out:
        if clean and clean[-1] == p:
            continue
        clean.append(p)
    zs = dem_at([p[0] for p in clean], [p[1] for p in clean])
    real_km = sum(km(a, b_) for real, pts in runs if real for a, b_ in zip(pts, pts[1:]))
    return clean, float(zs.max()), real_km


def hairpins(pts, gmax):
    """replace stretches that climb faster than gmax with hairpin zigzags (legs up to ~350 m off the line)"""
    out = [pts[0]]
    for a, b_ in zip(pts, pts[1:]):
        L = km(a, b_)
        za, zb = dem_at([a[0], b_[0]], [a[1], b_[1]])
        dz = abs(zb - za) / 1000
        if L < 0.05 or dz < 0.08 or dz / L <= gmax:
            out.append(b_); continue
        need = dz / gmax
        vx, vy = (b_[0] - a[0]) * KX / L, (b_[1] - a[1]) * KY / L
        px, py = -vy, vx
        best = None
        for w in (0.12, 0.2, 0.28, 0.35):
            for n in range(2, 40):
                adv = L / n
                if adv < 0.06:
                    break
                tot = 2 * math.hypot(adv / 2, w) + (n - 2) * math.hypot(adv, 2 * w) if n > 1 else L
                if tot >= need:
                    best = (w, n); break
            if best:
                break
        if not best:
            w, n = 0.35, max(2, int(L / 0.06))
        else:
            w, n = best
        for k in range(1, n):
            t = k / n; sgn = 1 if k % 2 else -1
            out.append((a[0] + (b_[0] - a[0]) * t + sgn * w * px / KX, a[1] + (b_[1] - a[1]) * t + sgn * w * py / KY))
        out.append(b_)
    return out


def load_rivers():
    fn = os.environ.get("ROUTE_RIVERS")
    if not fn or not os.path.exists(fn): return []
    out = []
    for line in open(fn):
        f = json.loads(line)
        if f["properties"]["class"] != "river": continue
        g = f["geometry"]
        for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]): out.append(np.array(c))
    return out


RIVERS = load_rivers()

if __name__ == "__main__":
    SPECS = json.load(open(os.path.join(ROOT, "build/route_specs.json")))
    routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
    R = {r["id"]: r for r in routes}
    rep = []
    for spec in SPECS:
        if spec.get("skip") or (ONLY and spec["id"] not in ONLY):
            continue
        r = R[spec["id"]]
        before = km_len(r["coords"])
        for key, k in (("start_on", 0), ("end_on", -1)):    # begin or end at a junction on another route
            if spec.get(key) and R.get(spec[key], {}).get("coords"):
                C = np.array(R[spec[key]]["coords"]); p = spec["via"][k]
                d = np.hypot((C[:, 0] - p[0]) * KX, (C[:, 1] - p[1]) * KY); i = int(np.argmin(d))
                spec["via"][k] = [float(C[i, 0]), float(C[i, 1])]
        coords, zmax, real_km = route(spec)
        r["coords"] = [list(p) for p in coords]
        r["snapped"] = "terrain"
        L = km_len(coords)
        r["length_km"] = round(L)
        r["max_elev_m"] = int(round(zmax / 10) * 10)
        rep.append(f"{spec['id']:36} {before:6.0f} -> {L:6.0f} km  (real roads/track {real_km:5.0f} km)  highest {zmax:5.0f} m  {len(coords)} pts")
        print(rep[-1], flush=True)
    json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
