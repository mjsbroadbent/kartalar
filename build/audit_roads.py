"""Audit the Irad roads against the terrain and the real network.

  python3 build/audit_roads.py <fine dem.bin> <extract dir> [plot dir]

For every road and highway in data/routes.json: length, share on real roads, steepest sustained grades, new-built
stretches on steep side slopes, river crossings without a real bridge, sharp bends on easy ground, where each end
lands (settlement, another route, a real road) and, where the road leaves Irad, whether a real road carries on.
Writes data/road_audit.md; with a plot dir, one picture per road (shaded relief, real roads, the route).
"""
import json, math, os, struct, sys
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, EXT = sys.argv[1], sys.argv[2]
PLOT = sys.argv[3] if len(sys.argv) > 3 else None
KY = 110.57; KX = 111.32 * math.cos(math.radians(42.5))

b = open(DEMF, "rb").read()
LON0, LAT0, ST = struct.unpack("<3d", b[8:32]); NX, NY = struct.unpack("<2i", b[32:40])
DEM = np.frombuffer(b[64:], dtype="<i2").reshape(NY, NX).astype(np.float32)
DEMS = ndimage.gaussian_filter(DEM, 1.0)
gy_, gx_ = np.gradient(DEMS, ST * KY * 1000, ST * KX * 1000); SLOPE = np.hypot(gx_, gy_)


def sample(A, lon, lat):
    return ndimage.map_coordinates(A, [(np.asarray(lat) - LAT0) / ST, (np.asarray(lon) - LON0) / ST], order=1, mode="nearest")


def resample(c, step=0.05):
    P = np.array(c, float) * [KX, KY]; seg = np.hypot(*np.diff(P, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
    ss = np.arange(0, s[-1], step); ss = np.append(ss, s[-1]) if ss[-1] < s[-1] else ss
    Q = np.column_stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])]) / [KX, KY]
    return Q, ss


def load(layer):
    return [json.loads(l) for l in open(os.path.join(EXT, layer + ".ndjson"))]


def parts(g):
    return [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]


def main():
    routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
    roads = [r for r in routes if r.get("kind") in ("road", "highway", "railway") and r.get("coords")]
    specs = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "build/route_specs.json")))}
    # real network
    net, bridges, railn = [], [], []
    for f in load("transportation"):
        cl = f["properties"]["class"]
        if cl == "rail" and f["tippecanoe"]["minzoom"] <= 8:
            for c in parts(f["geometry"]): railn.append(resample(c, 0.03)[0])
        if cl in ("path", "rail", "transit"): continue
        for c in parts(f["geometry"]):
            Q, _ = resample(c, 0.03); net.append(Q)
            if f["properties"].get("brunnel") == "bridge": bridges.append(Q)
    NET = np.vstack(net); road_tree = cKDTree(NET * [KX, KY]); rail_tree = cKDTree(np.vstack(railn) * [KX, KY])
    btree = cKDTree(np.vstack(bridges) * [KX, KY]) if bridges else None
    global LAKES
    LAKES = []
    for f in load("water"):
        if f["properties"]["class"] != "lake": continue
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            R_ = np.array(poly[0])
            if len(R_) > 8: LAKES.append((Path(R_), (R_[:, 0].min(), R_[:, 0].max(), R_[:, 1].min(), R_[:, 1].max())))
    rivers = []
    for f in load("waterway"):
        if f["properties"]["class"] in ("river", "canal"):
            for c in parts(f["geometry"]): rivers.append((f["properties"]["class"], np.array(c)))
    g = json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"][0]["geometry"]
    irad = [Path(np.array(p[0])) for p in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])]
    inside = lambda P: np.any([pa.contains_points(P) for pa in irad], axis=0)
    places = json.load(open(os.path.join(ROOT, "data/settlements.json"))) + json.load(open(os.path.join(ROOT, "data/features.json")))
    places = [p for p in places if p.get("kind") not in ("district", "zone-area")]
    ptree = cKDTree(np.array([(p["lon"] * KX, p["lat"] * KY) for p in places]))
    # every other route's points, for junctions
    rp = {r["id"]: resample(r["coords"], 0.05)[0] for r in roads}

    out = ["# Road audit (build/audit_roads.py)", "",
           "Grades are over 500 m windows from the ~90 m terrain grid; GRADE counts only new-built stretches. *Real* = within 40 m of an OpenStreetMap road or track.",
           "Flags: GRADE steeper than the road's ruling grade + 2 points for more than 1 km in all; SIDE new-built over 1 km on side slopes over 30%;",
           "BRIDGES new bridges (no real road crossing within 200 m); ZIGZAG the same river or canal crossed twice within 3 km; SKEW a new bridge less than 75 degrees to its river; WATER across a lake; BEND a turn over 100 degrees on easy ground;",
           "PARALLEL new road running close beside a real road; END an end more than 1 km from any settlement, feature, other route or real road; EXIT where the road leaves Irad with no real road carrying on.", ""]
    summary = []
    for r in roads:
        Q, ss = resample(r["coords"], 0.05); L = ss[-1]
        z = sample(DEMS, Q[:, 0], Q[:, 1])
        w = 10   # 10 x 50 m = 500 m
        gr = np.abs(z[w:] - z[:-w]) / (ss[w:] - ss[:-w]) / 1000 if len(z) > w else np.zeros(1)
        gmax = specs.get(r["id"], {}).get("gmax", 0.06 if r["kind"] == "road" else 0.05)
        ntree = rail_tree if r["kind"] == "railway" else road_tree     # a railway's real line is real track
        d_real, _ = ntree.query(Q * [KX, KY]); real = d_real < 0.04
        # only new-built stretches count (a real road is where it is; in narrow gorges the grid misreads its grade)
        newb = np.convolve((~real).astype(float), np.ones(w) / w, "valid")[:len(gr)] > 0.5 if len(z) > w else np.zeros(1, bool)
        steep_km = float(((gr > gmax + 0.02) & newb).sum() * 0.05)
        sl = sample(SLOPE, Q[:, 0], Q[:, 1])
        side_km = float(((~real) & (sl > 0.30)).sum() * 0.05)
        flags = []
        if steep_km > 1: flags.append(f"GRADE {steep_km:.1f} km over {100 * (gmax + 0.02):.0f}% (max {100 * gr.max():.0f}%)")
        if side_km > 1: flags.append(f"SIDE {side_km:.1f} km new-built on >30% slopes")
        # new road shadowing a real road a little way off (it should follow the real road, or keep well clear)
        par = (~real) & (d_real < 0.25); run = best = 0
        for v in par:
            run = run + 1 if v else 0; best = max(best, run)
        if best * 0.05 > 1.0: flags.append(f"PARALLEL {best * 0.05:.1f} km new-built 40-250 m beside a real road")
        # river crossings
        P = np.array(r["coords"]); nbridge = [0]
        seglen = np.hypot(*np.diff(P * [KX, KY], axis=0).T); cum = np.concatenate([[0], np.cumsum(seglen)])
        for cls, Rv in rivers:
            if Rv[:, 0].max() < P[:, 0].min() or Rv[:, 0].min() > P[:, 0].max() or Rv[:, 1].max() < P[:, 1].min() or Rv[:, 1].min() > P[:, 1].max(): continue
            A, B = P[:-1, None, :], P[1:, None, :]; C, D = Rv[None, :-1, :], Rv[None, 1:, :]
            den = (B[..., 0] - A[..., 0]) * (D[..., 1] - C[..., 1]) - (B[..., 1] - A[..., 1]) * (D[..., 0] - C[..., 0])
            with np.errstate(divide="ignore", invalid="ignore"):
                t = ((C[..., 0] - A[..., 0]) * (D[..., 1] - C[..., 1]) - (C[..., 1] - A[..., 1]) * (D[..., 0] - C[..., 0])) / den
                u = ((C[..., 0] - A[..., 0]) * (B[..., 1] - A[..., 1]) - (C[..., 1] - A[..., 1]) * (B[..., 0] - A[..., 0])) / den
            hits = []
            for i, j in zip(*np.where((t >= 0) & (t <= 1) & (u >= 0) & (u <= 1))):
                x = P[i] + t[i, j] * (P[i + 1] - P[i])
                hits.append((cum[i] + t[i, j] * seglen[i], x))
                if not ntree.query_ball_point(x * [KX, KY], 0.2): nbridge[0] += 1
                if ntree.query(x * [KX, KY])[0] > 0.04:     # a new bridge: how square it crosses
                    dv = (P[i + 1] - P[i]) * [KX, KY]; tv = (Rv[j + 1] - Rv[j]) * [KX, KY]
                    ang = math.degrees(math.asin(min(1, abs(dv[0] * tv[1] - dv[1] * tv[0]) / (np.hypot(*dv) * np.hypot(*tv) + 1e-12))))
                    Wk = Rv * [KX, KY]; dd = dv / (np.hypot(*dv) + 1e-12)
                    along = ang < 25 and all(np.hypot(*(Wk - (x * [KX, KY] + dd * s_)).T).min() < 0.05 for s_ in (-0.15, -0.075, 0.075, 0.15))
                    if ang < 75 and not along: flags.append(f"SKEW new bridge crosses the {cls} at {ang:.0f} deg at {x[0]:.4f},{x[1]:.4f}")
            hits.sort(key=lambda h: h[0])
            newx = lambda x: ntree.query(x * [KX, KY])[0] > 0.04    # on a real road the crossings are the real road's
            for (s0, x0), (s1, x1) in zip(hits, hits[1:]):    # the same river crossed twice in a short way: a zigzag
                if s1 - s0 < 3.0 and (newx(x0) or newx(x1)): flags.append(f"ZIGZAG crosses the same {cls} twice within {s1 - s0:.1f} km at {x0[0]:.4f},{x0[1]:.4f}")
        if nbridge[0]: flags.append(f"BRIDGES {nbridge[0]} new river/canal bridges")
        # over open water (a lake or reservoir) away from a real road
        wet = np.zeros(len(Q), bool)
        for pa, ex in LAKES:
            sel = (Q[:, 0] >= ex[0]) & (Q[:, 0] <= ex[1]) & (Q[:, 1] >= ex[2]) & (Q[:, 1] <= ex[3])
            if sel.any(): wet[sel] |= pa.contains_points(Q[sel])
        wet &= ~real
        if wet.sum() * 0.05 > 0.2: flags.append(f"WATER {wet.sum() * 0.05:.1f} km across a lake or reservoir")
        # bends on easy ground
        V = np.array(r["coords"], float) * [KX, KY]
        for i in range(1, len(V) - 1):
            u1, u2 = V[i] - V[i - 1], V[i + 1] - V[i]; n1, n2 = np.hypot(*u1), np.hypot(*u2)
            if n1 < 0.15 or n2 < 0.15: continue
            ang = math.degrees(math.acos(max(-1, min(1, (u1 @ u2) / (n1 * n2)))))
            p = V[i] / [KX, KY]
            if ang > 100 and sample(SLOPE, [p[0]], [p[1]])[0] < 0.08: flags.append(f"BEND {ang:.0f} deg at {p[0]:.4f},{p[1]:.4f}")
        # ends
        ends = []
        for e in (Q[0], Q[-1]):
            dp, ip = ptree.query(e * [KX, KY]); dr = min((np.hypot(*((rp[o] - e) * [KX, KY]).T).min() for o in rp if o != r["id"]), default=9e9)
            dn, _ = ntree.query(e * [KX, KY])
            ends.append(f"{places[ip]['name']} {dp:.1f} km / route {dr:.1f} km / real road {dn:.2f} km")
            if min(dp, dr, dn) > 1.0: flags.append(f"END at {e[0]:.4f},{e[1]:.4f} is {min(dp, dr, dn):.1f} km from anything")
        # exits
        ins = inside(Q)
        for i in np.where(ins[:-1] != ins[1:])[0]:
            x = Q[i]; out_pts = NET[np.hypot(*((NET - x) * [KX, KY]).T) < 0.5]
            if not len(out_pts) or inside(out_pts).all(): flags.append(f"EXIT at {x[0]:.4f},{x[1]:.4f}: no real road outside Irad")
        summary.append((r["id"], L, real.mean(), gr.max(), len(flags)))
        out += [f"## {r.get('name', r['id'])} (`{r['id']}`)", "",
                f"{L:.0f} km, {100 * real.mean():.0f}% on real roads, highest {z.max():.0f} m, steepest 500 m {100 * gr.max():.1f}% (ruling {100 * gmax:.0f}%)",
                f"- start: {ends[0]}", f"- end: {ends[1]}"] + [f"- **{fl}**" for fl in flags] + [""]
        if PLOT: plot(r, Q, real, rivers)
    out[7:7] = ["| road | km | real | steepest | flags |", "|---|---|---|---|---|"] + [f"| {i} | {L:.0f} | {100 * re:.0f}% | {100 * g:.0f}% | {n} |" for i, L, re, g, n in summary] + [""]
    open(os.path.join(ROOT, "data/road_audit.md"), "w").write("\n".join(out) + "\n")
    for s in summary: print(f"  {s[0]:36} {s[1]:5.0f} km  real {100 * s[2]:3.0f}%  steepest {100 * s[3]:4.1f}%  flags {s[4]}")


def plot(r, Q, real, rivers):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    x0, x1 = Q[:, 0].min() - 0.03, Q[:, 0].max() + 0.03; y0, y1 = Q[:, 1].min() - 0.03, Q[:, 1].max() + 0.03
    i0, i1 = int((x0 - LON0) / ST), int((x1 - LON0) / ST); j0, j1 = int((y0 - LAT0) / ST), int((y1 - LAT0) / ST)
    Z = DEMS[j0:j1, i0:i1]; gy, gx = np.gradient(Z, ST * KY * 1000, ST * KX * 1000)
    hs = np.clip(0.55 + 0.45 * (-gx - gy) / np.sqrt(1 + gx ** 2 + gy ** 2), 0, 1)
    asp = (y1 - y0) * KY / ((x1 - x0) * KX); W = 12
    fig, ax = plt.subplots(figsize=(W, max(4, min(W * asp, 16))), dpi=110)
    ax.imshow(hs, extent=(LON0 + i0 * ST, LON0 + i1 * ST, LAT0 + j0 * ST, LAT0 + j1 * ST), origin="lower", cmap="gray", vmin=0, vmax=1, aspect=1 / math.cos(math.radians(42.5)))
    for f in NETF:
        c = f
        if c[:, 0].max() < x0 or c[:, 0].min() > x1 or c[:, 1].max() < y0 or c[:, 1].min() > y1: continue
        ax.plot(c[:, 0], c[:, 1], color="#e0a020", lw=0.6, alpha=0.8)
    for cls, Rv in rivers:
        if Rv[:, 0].max() < x0 or Rv[:, 0].min() > x1 or Rv[:, 1].max() < y0 or Rv[:, 1].min() > y1: continue
        ax.plot(Rv[:, 0], Rv[:, 1], color="#3b7dd8", lw=0.9 if cls == "river" else 0.5)
    ax.plot(Q[:, 0], Q[:, 1], color="#d01010", lw=1.6)
    ax.scatter(Q[~real, 0][::4], Q[~real, 1][::4], s=2, color="#ff00ff", zorder=5)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_title(f"{r['id']}  (magenta = new-built)")
    fig.tight_layout(); fig.savefig(os.path.join(PLOT, r["id"] + ".png")); plt.close(fig)


NETF = []
if __name__ == "__main__":
    if PLOT:
        os.makedirs(PLOT, exist_ok=True)
        for line in open(os.path.join(EXT, "transportation.ndjson")):
            f = json.loads(line)
            if f["properties"]["class"] in ("motorway", "trunk", "primary", "secondary", "tertiary", "minor", "track"):
                for c in parts(f["geometry"]): NETF.append(np.array(c))
    main()
