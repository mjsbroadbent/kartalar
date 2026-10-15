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
    side_r = np.zeros(Z.shape, np.int8); tan_x = np.zeros(Z.shape, np.float32); tan_y = np.zeros(Z.shape, np.float32)
    rp, rt, rw = [], [], []
    wcell = np.zeros(Z.shape, np.float32)
    for c, wgt in [(c_, 1.0) for c_ in (RIVERS or [])] + [(c_, 0.3) for c_ in (CANALS or [])]:   # a canal bridge is a small one
        if c[:, 0].max() < x0 or c[:, 0].min() > x1 or c[:, 1].max() < y0 or c[:, 1].min() > y1: continue
        P = c * [KX, KY]
        for a_, b2 in zip(P[:-1], P[1:]):
            L_ = math.hypot(*(b2 - a_)); n_ = max(1, int(L_ / 0.03)); t_ = (b2 - a_) / (L_ + 1e-12)
            for k in range(n_): rp.append(a_ + (b2 - a_) * k / n_); rt.append(t_); rw.append(wgt)
    if rp:
        rp = np.array(rp); rt = np.array(rt); tree_r = cKDTree(rp)
        G2 = np.column_stack([GX.ravel() * KX, GY.ravel() * KY])
        d_, k_ = tree_r.query(G2, distance_upper_bound=0.3)
        near = np.isfinite(d_); kk = k_[near]
        rel = G2[near] - rp[kk]
        cr = rt[kk, 0] * rel[:, 1] - rt[kk, 1] * rel[:, 0]
        sv = np.zeros(len(G2), np.int8); sv[near] = np.sign(cr).astype(np.int8)
        side_r = sv.reshape(Z.shape)
        tx_ = np.zeros(len(G2), np.float32); ty_ = np.zeros(len(G2), np.float32)
        tx_[near] = rt[kk, 0]; ty_[near] = rt[kk, 1]
        tan_x = tx_.reshape(Z.shape); tan_y = ty_.reshape(Z.shape)
        wv = np.zeros(len(G2), np.float32); wv[near] = np.array(rw)[kk]; wcell = wv.reshape(Z.shape)
    # lakes and reservoirs: no new road across open water (real roads over dams and causeways stay usable)
    from matplotlib.path import Path as _P
    wet = np.zeros(Z.shape, bool)
    GP = None
    for R_ in (LAKES or []):
        if R_[:, 0].max() < x0 or R_[:, 0].min() > x1 or R_[:, 1].max() < y0 or R_[:, 1].min() > y1: continue
        if GP is None: GP = np.column_stack([GX.ravel(), GY.ravel()])
        sel = (GP[:, 0] >= R_[:, 0].min()) & (GP[:, 0] <= R_[:, 0].max()) & (GP[:, 1] >= R_[:, 1].min()) & (GP[:, 1] <= R_[:, 1].max())
        if sel.any():
            w_ = wet.ravel(); w_[sel] |= _P(R_).contains_points(GP[sel]); wet = w_.reshape(Z.shape)
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
            av = 1 + 50 * (avoid[j0:j1, i0:i1] | avoid[j0 + dj:j1 + dj, i0 + di:i1 + di]) + 40 * (wet[j0:j1, i0:i1] | wet[j0 + dj:j1 + dj, i0 + di:i1 + di])
            # a bridge: costs more the more obliquely the step crosses the river (bridges go straight across, short)
            crossing = (side_r[j0:j1, i0:i1].astype(np.int16) * side_r[j0 + dj:j1 + dj, i0 + di:i1 + di]) < 0
            sx, sy = di * RES * KX / L, dj * RES * KY / L
            tx2 = tan_x[j0:j1, i0:i1] + tan_x[j0 + dj:j1 + dj, i0 + di:i1 + di]; ty2 = tan_y[j0:j1, i0:i1] + tan_y[j0 + dj:j1 + dj, i0 + di:i1 + di]
            tn = np.hypot(tx2, ty2) + 1e-9
            sin_ = np.abs(sx * ty2 - sy * tx2) / tn
            wq = np.maximum(wcell[j0:j1, i0:i1], wcell[j0 + dj:j1 + dj, i0 + di:i1 + di])
            rv = spec.get("bridge_km", 0.8) * wq * crossing / np.maximum(sin_, 0.2) ** 2
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
            raw = pts
            n_raw = river_crossings(raw)
            for e_, ch_ in ((eps, spec.get("chaikin", 2 if kind == "road" else 3)), (0.02, 1), (0.008, 0)):
                pts = chaikin(rdp(raw, e_), ch_)
                if river_crossings(pts) <= n_raw: break      # smoothing must not add river crossings
            else:
                pts = list(raw)
            if kind == "road" and spec.get("hairpins", True):
                pts = hairpins(pts, gmax * spec.get("hairpin_grade", 1.25))
        out += pts if not out else pts[1:]
    out = [(round(x, 5), round(y, 5)) for x, y in out]
    clean = []
    for p in out:
        if clean and clean[-1] == p:
            continue
        clean.append(p)
    # no out-and-back spikes (a via point reached and left the way it came)
    ch = True
    while ch and len(clean) > 3:
        ch = False
        for k in range(1, len(clean) - 1):
            p0, p1, p2 = clean[k - 1], clean[k], clean[k + 1]
            ax_, ay_ = (p1[0] - p0[0]) * KX, (p1[1] - p0[1]) * KY; bx_, by_ = (p2[0] - p1[0]) * KX, (p2[1] - p1[1]) * KY
            la, lb = math.hypot(ax_, ay_), math.hypot(bx_, by_)
            if la * lb > 0 and (ax_ * bx_ + ay_ * by_) < -0.985 * la * lb:
                del clean[k]; ch = True; break
    zs = dem_at([p[0] for p in clean], [p[1] for p in clean])
    real_km = sum(km(a, b_) for real, pts in runs if real for a, b_ in zip(pts, pts[1:]))
    return clean, float(zs.max()), real_km


def river_crossings(pts):
    """how many times a line crosses the real rivers (and lake shores do not count)"""
    if not RIVERS or len(pts) < 2: return 0
    P = np.asarray(pts, float); n = 0
    x0, x1, y0, y1 = P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()
    for Rv in RIVERS + CANALS:
        if Rv[:, 0].max() < x0 or Rv[:, 0].min() > x1 or Rv[:, 1].max() < y0 or Rv[:, 1].min() > y1: continue
        A, B = P[:-1, None, :], P[1:, None, :]; C, D = Rv[None, :-1, :], Rv[None, 1:, :]
        den = (B[..., 0] - A[..., 0]) * (D[..., 1] - C[..., 1]) - (B[..., 1] - A[..., 1]) * (D[..., 0] - C[..., 0])
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((C[..., 0] - A[..., 0]) * (D[..., 1] - C[..., 1]) - (C[..., 1] - A[..., 1]) * (D[..., 0] - C[..., 0])) / den
            u = ((C[..., 0] - A[..., 0]) * (B[..., 1] - A[..., 1]) - (C[..., 1] - A[..., 1]) * (B[..., 0] - A[..., 0])) / den
        n += int(((t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)).sum())
    return n


def hairpins(pts, gmax, step=0.1, hyst=40.0, max_chord=4.0):
    """replace climbs steeper than gmax with roads laid over the terrain at the ruling grade (serpentine). The line is
    split at the high and low points of its profile (ignoring wiggles under ~40 m), and each climb or descent with a
    steep 400 m stretch in it is laid out again as a whole, end to end."""
    n_pts = len(pts)
    if n_pts < 2: return list(pts)
    cuts = [0]; L = 0.0
    for k in range(n_pts - 1):
        L += km(pts[k], pts[k + 1])
        if L >= step or k == n_pts - 2: cuts.append(k + 1); L = 0.0
    zc = dem_at([pts[c][0] for c in cuts], [pts[c][1] for c in cuts]).astype(float)
    zs = ndimage.gaussian_filter1d(zc, 2.0, mode="nearest") if len(zc) > 4 else zc
    # turning points of the profile, with hysteresis
    turn = [0]; ext = 0; d = 0
    for q in range(1, len(zs)):
        if d >= 0 and zs[q] >= zs[ext]: ext = q; d = 1 if zs[q] > zs[turn[-1]] + 1e-9 else d
        elif d <= 0 and zs[q] <= zs[ext]: ext = q; d = -1 if zs[q] < zs[turn[-1]] - 1e-9 else d
        if d == 1 and zs[ext] - zs[q] > hyst: turn.append(ext); ext = q; d = -1
        elif d == -1 and zs[q] - zs[ext] > hyst: turn.append(ext); ext = q; d = 1
    if turn[-1] != len(zs) - 1: turn.append(len(zs) - 1)
    # split long climbs so each fits a local grid
    segs = []
    for u, v in zip(turn, turn[1:]):
        while km(pts[cuts[u]], pts[cuts[v]]) > max_chord and v - u > 2:
            m = u + 1
            while m < v - 1 and km(pts[cuts[u]], pts[cuts[m + 1]]) <= max_chord * 0.75: m += 1
            segs.append((u, m)); u = m
        segs.append((u, v))
    out = [pts[0]]
    w = max(1, int(round(0.4 / step)))
    for u, v in segs:
        ia, ib = cuts[u], cuts[v]
        ww = min(w, v - u)                 # a climb shorter than the window is judged whole
        steep = ww > 0 and any(abs(zc[q + ww] - zc[q]) / 1000 > gmax * max(sum(km(pts[k], pts[k + 1]) for k in range(cuts[q], cuts[q + ww])), 1e-6)
                               and abs(zc[q + ww] - zc[q]) > 20 for q in range(u, v - ww + 1))
        rz = serpentine(pts[ia], pts[ib], 0.92 * gmax) if steep and km(pts[ia], pts[ib]) >= 0.15 else None
        out += (rz[1:] if rz else list(pts[ia + 1:ib + 1]))
    return out

def zigzag(a, b_, za, dz, chord, gmax):
    """the old straight-legged flight of hairpins between a and b_ (fallback when the terrain walk fails)"""
    need = dz / gmax
    vx, vy = (b_[0] - a[0]) * KX / chord, (b_[1] - a[1]) * KY / chord
    px, py = -vy, vx
    best = None
    for w in (0.3, 0.22, 0.15):                   # long legs first: few turns
        for n in range(2, 60):
            adv = chord / n
            if adv < 0.04: break
            if 2 * math.hypot(adv / 2, w) + (n - 2) * math.hypot(adv, 2 * w) >= need: best = (w, n); break
        if best: break
    w, n = best if best else (0.3, max(2, int(chord / 0.04)))
    zl, zr = dem_at([a[0] + 0.15 * px / KX, a[0] - 0.15 * px / KX], [a[1] + 0.15 * py / KY, a[1] - 0.15 * py / KY])
    side = -1 if abs(zr - za) < abs(zl - za) else 1        # first leg onto the gentler side
    zz = [a]
    for k in range(1, n):
        t = k / n; sgn = side if k % 2 else -side
        zz.append((a[0] + (b_[0] - a[0]) * t + sgn * w * px / KX, a[1] + (b_[1] - a[1]) * t + sgn * w * py / KY))
    zz.append(b_)
    # round the turns a little (one corner-cutting pass keeps them tight)
    rz = [zz[0]]
    for p0, p1 in zip(zz, zz[1:]):
        rz.append((0.85 * p0[0] + 0.15 * p1[0], 0.85 * p0[1] + 0.15 * p1[1])); rz.append((0.15 * p0[0] + 0.85 * p1[0], 0.15 * p0[1] + 0.85 * p1[1]))
    rz.append(zz[-1])
    return rz


def serpentine(a, b_, gmax, res=0.04, pad=0.7, turn_km=0.6):
    """a climb laid out over the terrain on a fine local grid of position and heading: steps steeper than gmax cost
    dearly, each change of heading costs a little and a hairpin about turn_km, so the road takes long legs across the
    slope at the ruling grade with as few turns as the climb needs. None if no path is found."""
    from scipy.sparse import csr_matrix
    x0 = min(a[0], b_[0]) - pad / KX; x1 = max(a[0], b_[0]) + pad / KX
    y0 = min(a[1], b_[1]) - pad / KY; y1 = max(a[1], b_[1]) + pad / KY
    nx = int((x1 - x0) * KX / res) + 1; ny = int((y1 - y0) * KY / res) + 1
    if nx * ny > 40000: res *= math.sqrt(nx * ny / 40000); nx = int((x1 - x0) * KX / res) + 1; ny = int((y1 - y0) * KY / res) + 1
    gxs = x0 + np.arange(nx) * res / KX; gys = y0 + np.arange(ny) * res / KY
    GX_, GY_ = np.meshgrid(gxs, gys)
    Z = ndimage.gaussian_filter(dem_at(GX_.ravel(), GY_.ravel()).reshape(ny, nx).astype(float), 1.2)
    DIRS = [(1, 0), (2, 1), (1, 1), (1, 2), (0, 1), (-1, 2), (-1, 1), (-2, 1), (-1, 0), (-2, -1), (-1, -1), (-1, -2), (0, -1), (1, -2), (1, -1), (2, -1)]
    H = len(DIRS); NC = ny * nx
    cell = np.arange(NC).reshape(ny, nx)
    rows, cols, wts = [], [], []
    for h2, (di, dj) in enumerate(DIRS):
        j0, j1 = max(0, -dj), ny - max(0, dj); i0, i1 = max(0, -di), nx - max(0, di)
        A = cell[j0:j1, i0:i1].ravel(); B = cell[j0 + dj:j1 + dj, i0 + di:i1 + di].ravel()
        L = math.hypot(di, dj) * res
        g = np.abs(Z[j0 + dj:j1 + dj, i0 + di:i1 + di] - Z[j0:j1, i0:i1]).ravel() / (L * 1000)
        c = L * (1 + np.maximum(0, g - gmax) * 400)
        for h in range(H):
            dh = min((h2 - h) % H, (h - h2) % H)
            tc = 0.0 if dh == 0 else (0.02 * dh if dh <= 2 else turn_km)
            rows.append(A * H + h); cols.append(B * H + h2); wts.append(c + tc)
    S0 = NC * H; T0 = S0 + 1
    ia = int(round((a[0] - x0) * KX / res)); ja = int(round((a[1] - y0) * KY / res))
    ib = int(round((b_[0] - x0) * KX / res)); jb = int(round((b_[1] - y0) * KY / res))
    ca, cb = cell[ja, ia], cell[jb, ib]
    rows.append(np.full(H, S0)); cols.append(ca * H + np.arange(H)); wts.append(np.full(H, 1e-6))
    rows.append(cb * H + np.arange(H)); cols.append(np.full(H, T0)); wts.append(np.full(H, 1e-6))
    G = csr_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(S0 + 2, S0 + 2))
    dist, pred = dijkstra(G, indices=S0, return_predecessors=True)
    if not np.isfinite(dist[T0]): return None
    n = pred[T0]; seq = []
    while n != S0 and n >= 0:
        seq.append(n // H); n = pred[n]
    seq.reverse()
    path = [tuple(a)] + [(float(gxs[q % nx]), float(gys[q // nx])) for q in seq[1:-1]] + [tuple(b_)]
    path = rdp(path, 0.012)
    # no spikes: drop a vertex where the road doubles straight back on itself over a short leg
    ch = True
    while ch and len(path) > 3:
        ch = False
        for k in range(1, len(path) - 1):
            p0, p1, p2 = path[k - 1], path[k], path[k + 1]
            ax_, ay_ = (p1[0] - p0[0]) * KX, (p1[1] - p0[1]) * KY; bx_, by_ = (p2[0] - p1[0]) * KX, (p2[1] - p1[1]) * KY
            la, lb = math.hypot(ax_, ay_), math.hypot(bx_, by_)
            if min(la, lb) < 0.05 and (ax_ * bx_ + ay_ * by_) < -0.97 * la * lb:      # a stray spike, not a hairpin
                del path[k]; ch = True; break
    path = chaikin(path, 2)
    path[0] = tuple(a); path[-1] = tuple(b_)
    return path

def load_rivers(classes=("river",)):
    fn = os.environ.get("ROUTE_RIVERS")
    if not fn or not os.path.exists(fn): return []
    out = []
    for line in open(fn):
        f = json.loads(line)
        if f["properties"]["class"] not in classes: continue
        g = f["geometry"]
        for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]): out.append(np.array(c))
    return out


RIVERS = load_rivers()
CANALS = load_rivers(("canal",))


def load_lakes():
    fn = os.environ.get("ROUTE_RIVERS")
    fn = fn and os.path.join(os.path.dirname(fn), "water.ndjson")
    if not fn or not os.path.exists(fn): return []
    out = []
    for line in open(fn):
        f = json.loads(line)
        if f["properties"]["class"] != "lake": continue
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            R_ = np.array(poly[0])
            if len(R_) > 8: out.append(R_)
    return out


LAKES = load_lakes()

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
                best = (1e9, None)                          # the nearest point on it, not just its nearest vertex
                for q in range(len(C) - 1):
                    d_ = (C[q + 1] - C[q]) * [KX, KY]; t_ = float(np.clip(np.dot((np.array(p) - C[q]) * [KX, KY], d_) / max(np.dot(d_, d_), 1e-12), 0, 1))
                    pp = C[q] + (C[q + 1] - C[q]) * t_; e_ = float(np.hypot(*((pp - p) * [KX, KY])))
                    if e_ < best[0]: best = (e_, pp)
                spec["via"][k] = [round(float(best[1][0]), 5), round(float(best[1][1]), 5)]
        coords, zmax, real_km = route(spec)
        if spec.get("prefix") and R.get(spec["prefix"]["route"], {}).get("coords"):
            # the road begins along another (one road, one line): that road's stretch is put in front
            B = np.array(R[spec["prefix"]["route"]]["coords"])
            nr = lambda q: int(np.argmin(np.hypot((B[:, 0] - q[0]) * KX, (B[:, 1] - q[1]) * KY)))
            i0 = nr(spec["prefix"]["from"])
            # the segment of that road nearest this road's start: its stretch is taken up to there, no further
            P_ = np.array(coords[0]); best = (1e9, 0, 0.0)
            for k in range(len(B) - 1):
                d_ = (B[k + 1] - B[k]) * [KX, KY]; t_ = float(np.clip(np.dot((P_ - B[k]) * [KX, KY], d_) / max(np.dot(d_, d_), 1e-12), 0, 1))
                e_ = float(np.hypot(*((B[k] + (B[k + 1] - B[k]) * t_ - P_) * [KX, KY])))
                if e_ < best[0]: best = (e_, k, t_)
            k = best[1]
            seg = B[i0:k + 1] if i0 <= k else B[k + 1:i0 + 1][::-1]
            coords = [tuple(p) for p in seg] + list(coords)
        r["coords"] = [list(p) for p in coords]
        r["snapped"] = "terrain"
        L = km_len(coords)
        r["length_km"] = round(L)
        r["max_elev_m"] = int(round(zmax / 10) * 10)
        rep.append(f"{spec['id']:36} {before:6.0f} -> {L:6.0f} km  (real roads/track {real_km:5.0f} km)  highest {zmax:5.0f} m  {len(coords)} pts")
        print(rep[-1], flush=True)
    json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
