"""Keep the named line checkpoints where their road crosses the Qara-Chik line, just on the ISEZ side.
Run after build/make_line.py and before build/make_crossings.py."""
import json, math, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57
R = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "data/routes.json")))}
L = [f["geometry"]["coordinates"] for f in json.load(open(os.path.join(ROOT, "data/qarachik.geojson")))["features"]]
# checkpoint id -> (road, village that sits beside it, offset of the village along the road towards the ISEZ in km)
ON_ROAD = {"qara-chik-border-checkpoint": ("qara-chik-road", "qara-chik", 0.8)}
# checkpoints on tracks we don't draw: nearest point of the line
ON_LINE = ["aksay-border-patrol-post"]


def inter(p1, p2, p3, p4):
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if d == 0: return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1: return t, u
    return None


def along(c, i, t, back_km):
    """point back_km before parameter (i, t) of polyline c"""
    pts = c[:i + 1] + [[c[i][0] + t * (c[i + 1][0] - c[i][0]), c[i][1] + t * (c[i + 1][1] - c[i][1])]]
    left = back_km
    for a, b in zip(pts[::-1], pts[::-1][1:]):
        d = math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)
        if d >= left:
            f = left / d
            return [a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])]
        left -= d
    return pts[0]


out = {}
for cid, (rid, vid, off) in ON_ROAD.items():
    c = R[rid]["coords"]
    for i, (a, b) in enumerate(zip(c, c[1:])):
        hit = next((h for l in L for p, q in zip(l, l[1:]) for h in [inter(a, b, p, q)] if h), None)
        if hit:
            out[cid] = along(c, i, hit[0], 0.15)
            if vid: out[vid] = along(c, i, hit[0], off)
            break
pts = np.array([p for l in L for p in l])
for cid in ON_LINE:
    out[cid] = None
for fn in ("data/settlements.json", "data/features.json"):
    D = json.load(open(os.path.join(ROOT, fn)))
    for p in D:
        if p["id"] in out:
            q = out[p["id"]]
            if q is None:
                d = np.hypot((pts[:, 0] - p["lon"]) * KX, (pts[:, 1] - p["lat"]) * KY); q = pts[int(d.argmin())]
            p["lon"], p["lat"] = round(float(q[0]), 5), round(float(q[1]), 5)
            print(f"{p['id']:30} -> {p['lat']}, {p['lon']}")
    json.dump(D, open(os.path.join(ROOT, fn), "w"), ensure_ascii=False, indent=1)
