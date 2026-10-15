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
if len(sys.argv) > 1:      # a terrain grid: hairpins on a climb are left alone
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
    json.dump(R, open(fn, "w"), ensure_ascii=False, indent=1)
