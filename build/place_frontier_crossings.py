"""Keep the international crossings (features whose id starts with xing-) on the frontier: each one moves to the nearest
point within 4 km where a real road or railway crosses Irad's border (data/irad.geojson), just inside Irad.
Run after build/make_geo.py.   python3 build/place_frontier_crossings.py <make_network.py output>"""
import json, math, os, sys
import numpy as np
from matplotlib.path import Path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KY = 110.57
g = json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"][0]["geometry"]["coordinates"]
P = [(Path(np.array(p[0])), [Path(np.array(h)) for h in p[1:]]) for p in g]
def inside(Q):
    m = np.zeros(len(Q), bool)
    for o, hs in P:
        mm = o.contains_points(Q)
        for h in hs: mm &= ~h.contains_points(Q)
        m |= mm
    return m
F = json.load(open(os.path.join(ROOT, "data/features.json")))
X = [f for f in F if f["id"].startswith("xing-") and not f.get("pinned")]   # pinned: placed by hand (a bridge)
box = (min(f["lon"] for f in X) - 0.1, max(f["lon"] for f in X) + 0.1, min(f["lat"] for f in X) - 0.1, max(f["lat"] for f in X) + 0.1)
cross = []
for w in json.load(open(sys.argv[1]))["ways"]:
    if w["k"] not in ("road:motorway", "road:trunk", "road:primary", "road:secondary", "road:tertiary", "road:unclassified", "rail:rail"): continue
    C = np.array(w["c"])
    if len(C) < 2 or C[:, 0].max() < box[0] or C[:, 0].min() > box[1] or C[:, 1].max() < box[2] or C[:, 1].min() > box[3]: continue
    if not any(abs(C[:, 0] - f["lon"]).min() < 0.06 and abs(C[:, 1] - f["lat"]).min() < 0.05 for f in X): continue
    ins = inside(C)
    for k in np.where(ins[:-1] != ins[1:])[0]:
        a, b = (C[k], C[k + 1]) if ins[k] else (C[k + 1], C[k])
        lo, hi = 0.0, 1.0                                  # find where the segment meets the frontier
        for _ in range(20):
            mid = (lo + hi) / 2
            if inside(np.array([a + mid * (b - a)]))[0]: lo = mid
            else: hi = mid
        L = float(np.hypot(*((b - a) * [111.32 * math.cos(math.radians(a[1])), KY]))) or 1e-6
        cross.append((a + max(0.0, lo - 0.04 / L) * (b - a), w["k"]))     # ~40 m inside Irad
rank = {"road:motorway": 0, "road:trunk": 0, "road:primary": 1, "rail:rail": 1, "road:secondary": 2, "road:tertiary": 3, "road:unclassified": 4}
moved = 0
for f in X:
    kx = 111.32 * math.cos(math.radians(f["lat"]))
    near = [(math.hypot((p[0] - f["lon"]) * kx, (p[1] - f["lat"]) * KY), rank[k], p) for p, k in cross]
    near = [n for n in near if n[0] < 4]
    if not near: print("  no road crossing near", f["id"]); continue
    d, _, p = min(near, key=lambda n: (n[1], n[0]) if n[0] < 1.5 else (9, n[0]))
    if d > 0.05 or not inside(np.array([[f["lon"], f["lat"]]]))[0]: f["lon"], f["lat"] = round(float(p[0]), 5), round(float(p[1]), 5); moved += 1
json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)
print(f"frontier crossings: {len(X)}, {moved} moved onto the frontier")
