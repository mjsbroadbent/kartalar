"""Lay out Irad Temir Jolu as a railway: real track where it exists, new track over the terrain elsewhere, proper
turnouts at junctions and no curve tighter than the line's minimum radius.

  python3 build/route_rail.py irad-dem.bin irad-osm-roads.json            route every line (before make_cities.py)
  python3 build/route_rail.py irad-dem.bin irad-osm-roads.json --smooth   only smooth (after make_cities.py has laid
                                                                          the lines through the city plans), snap stations

Minimum radii (Soviet 1,520 mm practice, single track): main lines 600 m (400 m in towns and on the approach to
termini), branches 300 m, industrial spurs and sidings 200 m. A branch leaves its parent line at a turnout: it shares
the parent's track up to the switch and curves away, so there are no right-angle junctions.
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, OSMF = sys.argv[1], sys.argv[2]
SMOOTH_ONLY = "--smooth" in sys.argv
sys.path.insert(0, os.path.join(ROOT, "build"))
KY = 110.57

# id: (Rmin km, parent line id or None, via points for new track (None = keep the real-track geometry), grade limit)
LINES = {
    # the old Turksib: real track from Nurzhan station west round the end of the Kyrgyz Range to the lowland junction
    "irad-temir-jolu-chu-line":        dict(R=0.6, R_town=0.35, parent=None, via=[[73.75927, 43.59738], [72.9, 42.95], [71.40724, 42.88695]], net_only=True),
    "irad-temir-jolu-kara-buura-line": dict(R=0.6, R_town=0.35, parent=None, via=[[71.40724, 42.88695], [70.30064, 42.48905]], net_only=True),
    # the Turksib east from Nurzhan to the Kazakh frontier (real track all the way): exchange station at the border
    "irad-temir-jolu-north-line":      dict(R=0.6, R_town=0.35, parent=None, via=[[73.75927, 43.59738], [74.04, 43.8647], [74.60, 43.79], [74.975, 43.623]], net_only=True),
    "irad-temir-jolu-talas-branch":    dict(R=0.4, R_town=0.3, parent="irad-temir-jolu-kara-buura-line",
                                            via=[[71.40724, 42.88695], [71.585, 42.625], [71.816, 42.557], [72.05, 42.526], [72.236, 42.5076]], gmax=0.016),
    "irad-temir-jolu-east-line":       dict(R=0.3, parent="irad-temir-jolu-chu-line", via=[[73.75927, 43.59738], [74.05, 43.585], [74.243, 43.581]], gmax=0.015),
    "irad-temir-jolu-sary-bulak-spur": dict(R=0.2, parent="irad-temir-jolu-talas-branch", via=[[72.135, 42.512], [72.105, 42.425], [72.095, 42.352]], gmax=0.03),
    "irad-temir-jolu-chatkal-spur":    dict(R=0.2, parent="irad-temir-jolu-sary-bulak-spur", via=[[72.106, 42.432], [72.0, 42.44], [71.965, 42.338]], gmax=0.03),
    "irad-temir-jolu-taez-siding":     dict(R=0.15, parent="irad-temir-jolu-talas-branch", via=[[72.11, 42.5205], [72.1235, 42.5105]], gmax=0.02, short=True),
}
STATIONS = {  # station id: (line, where) — 'end', 'start' or 'near'
    "talas-railway-station": ("irad-temir-jolu-talas-branch", "end"),
    "nurzhan-station": ("irad-temir-jolu-chu-line", "near"),
    "nurzhan-rail-freight-depot": ("irad-temir-jolu-north-line", "near"),
    "nurzhan-rail-border-station": ("irad-temir-jolu-north-line", "end"),
    "kara-bulak-station": ("irad-temir-jolu-talas-branch", "near"),
    "talas-cold-chain-hub": ("irad-temir-jolu-taez-siding", "end"),
}


def kx(lat): return 111.32 * math.cos(math.radians(lat))


def to_xy(c, lat0):
    return np.array([(x * kx(lat0), y * KY) for x, y in c])


def to_ll(P, lat0):
    return [[round(x / kx(lat0), 5), round(y / KY, 5)] for x, y in P]


def resample(P, step=0.02):
    seg = np.hypot(*np.diff(P, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
    keep = np.concatenate([[True], seg > 1e-9]); P, s = P[keep], s[keep]
    ss = np.arange(0, s[-1], step)
    if len(ss) == 0 or ss[-1] < s[-1]: ss = np.append(ss, s[-1])
    return np.column_stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])])


def curvature(P, k=5):
    n = len(P); kap = np.zeros(n)
    if n < 2 * k + 1: return kap
    a, b, c = P[:-2 * k], P[k:-k], P[2 * k:]
    ab = np.hypot(*(b - a).T); bc = np.hypot(*(c - b).T); ac = np.hypot(*(c - a).T)
    cr = np.abs((b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0])
    kap[k:-k] = 2 * cr / np.maximum(ab * bc * ac, 1e-12)
    return kap


def railify(P, Rmin, pin_start=1, pin_end=1, R_local=None, iters=600):
    """smooth only where the curve is tighter than Rmin (R_local: per-point minimum radius), keeping pinned ends"""
    P = resample(P)
    n = len(P)
    if n < 12: return P, 1e9
    Rl = np.full(n, Rmin) if R_local is None else R_local(P)
    pinned = np.zeros(n, bool); pinned[:pin_start] = True; pinned[n - pin_end:] = True
    sigma = 2.0
    for it in range(iters):
        kap = curvature(P)
        bad = kap * Rl > 1.0
        if not bad.any(): break
        m = ndimage.binary_dilation(bad, iterations=int(4 * sigma) + 3) & ~pinned
        S = ndimage.gaussian_filter1d(P, sigma, axis=0, mode="nearest")
        P[m] = S[m]
        if it % 40 == 39:
            sigma = min(sigma * 1.4, 25)
            P = resample(P); n = len(P)
            Rl = np.full(n, Rmin) if R_local is None else R_local(P)
            pinned = np.zeros(n, bool); pinned[:pin_start] = True; pinned[n - pin_end:] = True
    kap = curvature(P)
    free = ~pinned
    return P, (1 / kap[free].max() if (kap[free] > 0).any() else 1e9)


def rdp(P, eps):
    if len(P) < 3: return P
    a, b = P[0], P[-1]; v = b - a; n = math.hypot(*v)
    d = np.abs(v[0] * (P[:, 1] - a[1]) - v[1] * (P[:, 0] - a[0])) / n if n else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps: return np.vstack([rdp(P[: i + 1], eps)[:-1], rdp(P[i:], eps)])
    return np.vstack([a, b])


def turnout(parent_xy, start_xy, first_dir, lead=0.45):
    """track shared with the parent from the switch to the branch start: the parent's points within `lead` km of the
    start, on the side the branch heads away to (so the branch leaves at a shallow angle)"""
    d = np.hypot(*(parent_xy - start_xy).T); i = int(np.argmin(d))
    best = None
    for sgn in (1, -1):
        j = i; L = 0.0
        while 0 <= j + sgn < len(parent_xy) and L < lead:
            L += math.hypot(*(parent_xy[j + sgn] - parent_xy[j])); j += sgn
        seg = parent_xy[j:i + 1] if sgn < 0 else parent_xy[i:j + 1][::-1]   # runs from the switch towards the start
        if len(seg) < 2: continue
        tangent = seg[-1] - seg[0]; tangent /= (np.hypot(*tangent) + 1e-12)
        score = tangent @ first_dir
        if best is None or score > best[0]: best = (score, seg)
    return best[1] if best else np.array([start_xy])


def town_radius(Rmain, Rtown, towns):
    def f(P):
        R = np.full(len(P), Rmain)
        for (x, y), r in towns: R[np.hypot(P[:, 0] - x, P[:, 1] - y) < r] = Rtown
        return R
    return f


def main():
    routes = json.load(open(os.path.join(ROOT, "data/routes.json"))); R = {r["id"]: r for r in routes}
    P = {p["id"]: p for p in json.load(open(os.path.join(ROOT, "data/settlements.json")))}
    lat0 = 43.0
    towns = [((P[k]["lon"] * kx(lat0), P[k]["lat"] * KY), r) for k, r in (("talas", 9), ("nurzhan", 9), ("kyzyl-adyr", 3), ("kara-bulak", 2)) if k in P]
    if not SMOOTH_ONLY:
        import route_terrain as rt
        for lid, L in LINES.items():
            if not L["via"] or lid not in R: continue
            spec = {"id": lid, "kind": "rail", "net": "rail", "via": L["via"], "gmax": L.get("gmax", 0.018), "build": 1.0 if not L.get("net_only") else 40.0,
                    "eps": 0.05, "chaikin": 0, "hairpins": False, "margin": 0.08, "snap_km": 2.0, "side_w": 1.5, "snowline": 3000}
            coords, zmax, real_km = rt.route(spec)
            R[lid]["coords"] = [list(p) for p in coords]
            print(f"  routed {lid}: {real_km:.0f} km on real track")
    # smooth, parents first
    order, seen = [], set()
    def visit(l):
        if l in seen or l not in LINES: return
        seen.add(l)
        if LINES[l]["parent"]: visit(LINES[l]["parent"])
        order.append(l)
    for l in LINES: visit(l)
    xy = {}
    for lid in order:
        if lid not in R: continue
        L = LINES[lid]; C = to_xy(R[lid]["coords"], lat0)
        pin_s = 1
        if L["parent"] and L["parent"] in xy and SMOOTH_ONLY:
            pin_s = int((0.3 if L.get("short") else 0.6) / 0.02 * 0.5)    # the turnout laid in the routing pass stays put
        elif L["parent"] and L["parent"] in xy:
            par = xy[L["parent"]]
            Cr = resample(C)
            first_dir = Cr[min(25, len(Cr) - 1)] - Cr[0]; first_dir /= (np.hypot(*first_dir) + 1e-12)
            lead = turnout(par, Cr[0], first_dir, 0.3 if L.get("short") else 1.0)
            C = np.vstack([lead, Cr[1:]]) if len(lead) > 1 else Cr
            pin_s = 2                             # the switch itself stays on the parent's track
        rl = town_radius(L["R"], L.get("R_town", L["R"]), towns) if "R_town" in L else None
        S, rmin = railify(C, L["R"], pin_start=pin_s, pin_end=1, R_local=rl)
        xy[lid] = S
        out = rdp(S, 0.0015)
        R[lid]["coords"] = to_ll(out, lat0)
        km = float(np.hypot(*np.diff(S, axis=0).T).sum())
        R[lid]["length_km"] = round(km)
        R[lid]["min_radius_m"] = int(round(min(rmin, 9.99) * 1000, -1))
        print(f"  {lid:36} {km:6.1f} km, tightest curve {rmin * 1000:5.0f} m (limit {L['R'] * 1000:.0f} m), {len(out)} pts")
    json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
    # stations onto their lines
    F = json.load(open(os.path.join(ROOT, "data/features.json")))
    for f in F:
        if f["id"] in STATIONS and STATIONS[f["id"]][0] in R:
            c = R[STATIONS[f["id"]][0]]["coords"]; how = STATIONS[f["id"]][1]
            q = c[-1] if how == "end" else c[0] if how == "start" else min(c, key=lambda p: (p[0] - f["lon"]) ** 2 + (p[1] - f["lat"]) ** 2)
            f["lon"], f["lat"] = q
    json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
