"""Remove hooks, spikes and jogs from the Irad road routes: wherever the line runs out and comes back (the path between
two points is far longer than the straight way between them, over a short stretch), the detour is replaced by the
straight way, unless the straight way crosses a river more often or climbs much steeper ground.
  python3 build/dehook.py              (rewrites data/routes.json; roads and highways only)
"""
import json, math, os, struct, sys
import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KY = 110.57


DEM = None
if len(sys.argv) > 1 and os.path.basename(sys.argv[0]) == "dehook.py":      # a terrain grid: hairpins on a climb are left alone
    b = open(sys.argv[1], "rb").read()
    L0, A0, ST = struct.unpack("<3d", b[8:32]); NX, NY = struct.unpack("<2i", b[32:40])
    DEM = np.frombuffer(b[64:], dtype="<i2").reshape(NY, NX).astype(np.float32)


def z(p):
    return float(ndimage.map_coordinates(DEM, [[(p[1] - A0) / ST], [(p[0] - L0) / ST]], order=1)[0]) if DEM is not None else 0.0


def dehook(c, max_path=0.8, ratio=0.6, min_path=0.08):
    P = np.array(c, float)
    kx = 111.32 * math.cos(math.radians(P[:, 1].mean()))
    changed = True; n_fix = 0
    while changed:
        changed = False
        seg = np.hypot(np.diff(P[:, 0]) * kx, np.diff(P[:, 1]) * KY); cum = np.concatenate([[0], np.cumsum(seg)])
        i = 0
        while i < len(P) - 2:
            best = None
            j = i + 2
            while j < len(P) and cum[j] - cum[i] <= max_path:
                path = cum[j] - cum[i]; straight = math.hypot((P[j, 0] - P[i, 0]) * kx, (P[j, 1] - P[i, 1]) * KY)
                if path > min_path and straight < ratio * path and path - straight > 0.04:
                    climb = abs(z(P[j]) - z(P[i])) / max(straight * 1000, 30)
                    if climb < 0.05: best = j      # not a hairpin up a slope
                j += 1
            if best is not None:
                P = np.vstack([P[:i + 1], P[best:]]); changed = True; n_fix += 1; break
            i += 1
    return [[round(float(x), 5), round(float(y), 5)] for x, y in P], n_fix


# stretches of a route laid onto the real road between two points (the shortest way along real main roads)
FOLLOW = {
    "fergana-mountain-transit-highway": [((72.2385, 41.3960), (72.2330, 41.3685))],    # Iyık Janyl: along the Naryn's east bank to the bridge
}


def follow_real(c, a, b_, net, classes=("road:trunk", "road:primary", "road:secondary", "road:tertiary", "road:unclassified")):
    import heapq
    P = np.array(c, float); kx = 111.32 * math.cos(math.radians(P[:, 1].mean()))
    ia = int(np.argmin(np.hypot((P[:, 0] - a[0]) * kx, (P[:, 1] - a[1]) * KY))); ib = int(np.argmin(np.hypot((P[:, 0] - b_[0]) * kx, (P[:, 1] - b_[1]) * KY)))
    if ia > ib: ia, ib = ib, ia; a, b_ = b_, a
    x0, x1 = min(a[0], b_[0]) - 0.03, max(a[0], b_[0]) + 0.03; y0, y1 = min(a[1], b_[1]) - 0.03, max(a[1], b_[1]) + 0.03
    idx, coords, adj = {}, [], {}
    for w in net:
        if w["k"] not in classes: continue
        prev = None
        for x, y in w["c"]:
            if not (x0 < x < x1 and y0 < y < y1): prev = None; continue
            k = idx.setdefault((x, y), len(coords))
            if k == len(coords): coords.append((x, y)); adj[k] = []
            if prev is not None and prev != k:
                d = math.hypot((coords[prev][0] - x) * kx, (coords[prev][1] - y) * KY); adj[prev].append((k, d)); adj[k].append((prev, d))
            prev = k
    if not coords: return c, False
    C = np.array(coords)
    sa = int(np.argmin(np.hypot((C[:, 0] - P[ia, 0]) * kx, (C[:, 1] - P[ia, 1]) * KY))); sb = int(np.argmin(np.hypot((C[:, 0] - P[ib, 0]) * kx, (C[:, 1] - P[ib, 1]) * KY)))
    dist = {sa: 0}; prev = {}; pq = [(0, sa)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == sb: break
        if d > dist[u]: continue
        for v, w_ in adj[u]:
            if d + w_ < dist.get(v, 1e18): dist[v] = d + w_; prev[v] = u; heapq.heappush(pq, (d + w_, v))
    if sb not in dist: return c, False
    path = [sb]
    while path[-1] != sa: path.append(prev[path[-1]])
    seg = [list(coords[i]) for i in reversed(path)]
    return [list(p) for p in P[:ia]] + seg + [list(p) for p in P[ib + 1:]], True


def load_water():
    fn = os.environ.get("ROUTE_RIVERS")
    out = []
    if fn and os.path.exists(fn):
        for line in open(fn):
            f = json.loads(line)
            if f["properties"]["class"] not in ("river", "canal"): continue
            g = f["geometry"]
            for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]): out.append(np.array(c, float))
    return out


def seg_hits(a, b_, Rv):
    """crossings of segment a-b with polyline Rv: [(t along a-b, river segment index)]"""
    C, D = Rv[:-1], Rv[1:]
    den = (b_[0] - a[0]) * (D[:, 1] - C[:, 1]) - (b_[1] - a[1]) * (D[:, 0] - C[:, 0])
    with np.errstate(divide="ignore", invalid="ignore"):
        t = ((C[:, 0] - a[0]) * (D[:, 1] - C[:, 1]) - (C[:, 1] - a[1]) * (D[:, 0] - C[:, 0])) / den
        u = ((C[:, 0] - a[0]) * (b_[1] - a[1]) - (C[:, 1] - a[1]) * (b_[0] - a[0])) / den
    k = np.where((t >= 0) & (t <= 1) & (u >= 0) & (u <= 1))[0]
    return [(float(t[i]), int(i)) for i in k]


def along_bank(P, i, t, Rv, kx, span=0.15, tol=0.05):
    """the road runs along this water for `span` km either side of the meeting point (the lines merely touch)"""
    X = P[i] + t * (P[i + 1] - P[i]); d_ = (P[i + 1] - P[i]) * [kx, KY]; d_ /= (np.hypot(*d_) + 1e-12)
    W = Rv * [kx, KY]
    for s_ in (-span, -span / 2, span / 2, span):
        q = X * [kx, KY] + d_ * s_
        if np.hypot(*(W - q).T).min() > tol: return False
    return True


def square_bridges(c, water, real_pts, half=0.07, reach=0.35):
    """every new bridge crosses its river square on and short: the road comes straight at the river for `half` km on
    each side of it; real bridges (on a real road) are left as they are. Returns (coords, number squared)"""
    P = np.array(c, float); kx = 111.32 * math.cos(math.radians(P[:, 1].mean())); n_sq = 0
    x0, x1, y0, y1 = P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()
    water = [Rv for Rv in water if not (Rv[:, 0].max() < x0 or Rv[:, 0].min() > x1 or Rv[:, 1].max() < y0 or Rv[:, 1].min() > y1)]
    from scipy.spatial import cKDTree
    rtree = cKDTree(np.asarray(real_pts) * [kx, KY]) if len(real_pts) else None
    i = 0
    while i < len(P) - 1:
        a, b_ = P[i], P[i + 1]; hit = None
        dv = (b_ - a) * [kx, KY]
        for Rv in water:      # every crossing on this stretch; the first oblique new one is squared
            if Rv[:, 0].max() < min(a[0], b_[0]) or Rv[:, 0].min() > max(a[0], b_[0]) or Rv[:, 1].max() < min(a[1], b_[1]) or Rv[:, 1].min() > max(a[1], b_[1]): continue
            for t, k in seg_hits(a, b_, Rv):
                X_ = a + t * (b_ - a)
                if rtree is not None and rtree.query(X_ * [kx, KY])[0] < 0.04: continue      # a real bridge
                tv_ = (Rv[k + 1] - Rv[k]) * [kx, KY]; tv_ /= (np.hypot(*tv_) + 1e-12)
                sin_ = abs(dv[0] * tv_[1] - dv[1] * tv_[0]) / (np.hypot(*dv) + 1e-12)
                if sin_ > math.sin(math.radians(80)): continue                              # square enough already
                if sin_ < math.sin(math.radians(25)) and along_bank(P, i, t, Rv, kx): continue   # running along the bank, not across
                if hit is None or t < hit[0]: hit = (t, Rv, k, tv_)
        if not hit: i += 1; continue
        t, Rv, k, tv = hit; X = a + t * (b_ - a)
        nv = np.array([-tv[1], tv[0]])
        if np.dot(dv, nv) < 0: nv = -nv                                  # point the normal the way the road goes
        # braided channels and a canal beside the river go under the same bridge: the bridge spans them all
        h_ = half
        L0_ = X - nv * 0.3 / [kx, KY]; L1_ = X + nv * 0.3 / [kx, KY]
        for Rv2 in water:
            for t2, _k2 in seg_hits(L0_, L1_, Rv2):
                d2 = abs(t2 - 0.5) * 0.6
                if d2 < 0.25: h_ = max(h_, d2 + 0.04)
        A = X - nv * h_ / [kx, KY]; B = X + nv * h_ / [kx, KY]
        # the stretch of road within `reach` km either side of the crossing is replaced by: road -> A -> B -> road
        seg = np.hypot(np.diff(P[:, 0]) * kx, np.diff(P[:, 1]) * KY); cum = np.concatenate([[0], np.cumsum(seg)])
        sX = cum[i] + t * seg[i]
        s0, s1 = max(0.0, sX - reach), min(cum[-1], sX + reach)
        at = lambda s_: np.array([np.interp(s_, cum, P[:, 0]), np.interp(s_, cum, P[:, 1])])
        k0 = int(np.searchsorted(cum, s0, side="right")); k1 = int(np.searchsorted(cum, s1, side="left"))
        old_part = np.vstack([at(s0), P[k0:k1], at(s1)]); new_part = np.vstack([at(s0), A, B, at(s1)])
        nx_ = lambda Q: sum(len(seg_hits(a2, b2, Rv2)) for Rv2 in water for a2, b2 in zip(Q[:-1], Q[1:]))
        if nx_(new_part) > nx_(old_part): i += 1; continue        # squaring would cross more water (a gorge): leave it
        P = np.vstack([P[:k0], at(s0), A, B, at(s1), P[k1:]]); n_sq += 1
        i = k0 + 3
    return [[round(float(x), 5), round(float(y), 5)] for x, y in P], n_sq


RANK = ["fergana-mountain-transit-highway", "trans-talas-highway", "chu-highway", "talas-nurzhan-road", "kok-bel-road", "fergana-rim-road"]


def share(A, B, tol=0.8, start_tol=0.15):
    """where road A begins or ends along road B, A takes B's line for the shared stretch (one road, not two side by side)"""
    A = np.array(A, float); B = np.array(B, float)
    kx = 111.32 * math.cos(math.radians(A[:, 1].mean()))
    def dens(P, step=0.02):
        out = [P[0]]
        for a, b in zip(P, P[1:]):
            n = max(1, int(math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * KY) / step))
            out += [a + (b - a) * t / n for t in range(1, n + 1)]
        return np.array(out)
    Bd = dens(B)
    dB = lambda p: np.hypot((Bd[:, 0] - p[0]) * kx, (Bd[:, 1] - p[1]) * KY)
    changed = False
    for end in (0, -1):
        Ad = dens(A) if end == 0 else dens(A[::-1])
        if dB(Ad[0]).min() > start_tol: continue
        k = 0
        while k < len(Ad) and dB(Ad[k]).min() < tol: k += 1
        if k < 10 or k >= len(Ad): continue
        i0 = int(np.argmin(dB(Ad[0]))); i1 = int(np.argmin(dB(Ad[k - 1])))
        seg = Bd[min(i0, i1):max(i0, i1) + 1]
        if i1 < i0: seg = seg[::-1]
        new = np.vstack([seg, Ad[k:]])
        A = new if end == 0 else new[::-1]; changed = True
    return A, changed


if __name__ == "__main__":
    fn = os.path.join(ROOT, "data/routes.json"); R = json.load(open(fn)); tot = 0
    byid = {r["id"]: r for r in R}
    netf = os.environ.get("ROUTE_NET")
    if netf and os.path.exists(netf):
        net = json.load(open(netf))["ways"]
        for rid, spans in FOLLOW.items():
            for a, b_ in spans:
                c, ok = follow_real(byid[rid]["coords"], a, b_, net)
                if ok: byid[rid]["coords"] = [[round(float(x), 5), round(float(y), 5)] for x, y in c]; print(f"  {rid}: laid on the real road {a} - {b_}")
    for ia, a in enumerate(RANK):
        for b_ in RANK[:ia]:
            if a in byid and b_ in byid:
                c, ch = share(byid[a]["coords"], byid[b_]["coords"])
                if ch:
                    byid[a]["coords"] = [[round(float(x), 5), round(float(y), 5)] for x, y in c]
                    print(f"  {a}: shares {b_}'s line where they run together")
    for r in R:
        if r.get("kind") in ("road", "highway") and r.get("coords") and len(r["coords"]) > 3:
            r["coords"], n = dehook(r["coords"]); tot += n
            if n: print(f"  {r['id']}: {n} hooks straightened")
    water = load_water()
    if water and netf and os.path.exists(netf):
        real_pts = []
        for w in net:
            if w["k"].startswith("road:"):
                for a, b_ in zip(w["c"], w["c"][1:]):
                    n_ = max(1, int(math.hypot((b_[0] - a[0]) * 82, (b_[1] - a[1]) * KY) / 0.02))
                    real_pts += [[a[0] + (b_[0] - a[0]) * t / n_, a[1] + (b_[1] - a[1]) * t / n_] for t in range(n_)]
        real_pts = np.array(real_pts)
        for r in R:
            if r.get("kind") in ("road", "highway") and r.get("coords") and len(r["coords"]) > 1:
                tot_n = 0; c_ = r["coords"]
                for _ in range(3):           # squaring one bridge can move the road onto the next bend: repeat
                    c_, n = square_bridges(c_, water, real_pts); tot_n += n
                    if not n: break
                if tot_n: r["coords"] = c_; print(f"  {r['id']}: {tot_n} bridges squared to their river")
    json.dump(R, open(fn, "w"), ensure_ascii=False, indent=1)
