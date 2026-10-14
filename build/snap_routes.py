"""Redraw data/routes.json along real OpenStreetMap roads, railways and waterways.

Input: an export made with tools/osm-export.html (irad-osm-roads.json).
Each Iradi route keeps its waypoints from the lore; consecutive waypoints are joined by the
cheapest path through the matching real network (roads for highways and roads, rail for the
railway, canals and rivers for canals). Pipelines and power lines are left as drawn.
Run: python3 build/snap_routes.py irad-osm-roads.json
"""
import json, os, sys, math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OSM = json.load(open(sys.argv[1]))
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57


def xy(c):
    return np.column_stack([np.asarray(c)[:, 0] * KX, np.asarray(c)[:, 1] * KY])


ROAD_COST = {"motorway": 1.0, "trunk": 1.0, "primary": 1.08, "secondary": 1.25, "tertiary": 1.5,
             "motorway_link": 1.3, "trunk_link": 1.3, "primary_link": 1.3, "path": 4}
NETS = {
    "road": lambda k: ROAD_COST.get(k[5:]) if k.startswith("road:") else None,
    "rail": lambda k: 1.0 if k.startswith("rail:") else None,
    "water": lambda k: (1.0 if k == "water:canal" else 1.4) if k.startswith("water:") else None,
}


class Net:
    def __init__(self, costf):
        idx, coords, rows, cols, w = {}, [], [], [], []
        for way in OSM["ways"]:
            f = costf(way["k"])
            if f is None:
                continue
            prev = None
            for c in way["c"]:
                key = (c[0], c[1])
                i = idx.get(key)
                if i is None:
                    i = idx[key] = len(coords); coords.append(key)
                if prev is not None and prev != i:
                    a, b = coords[prev], coords[i]
                    d = math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY) * f + 1e-6
                    rows += [prev, i]; cols += [i, prev]; w += [d, d]
                prev = i
        self.coords = np.array(coords)
        n = len(coords)
        self.G = coo_matrix((w, (rows, cols)), shape=(n, n)).tocsr()
        self.tree = cKDTree(xy(self.coords))
        print(f"  network: {n:,} nodes, {len(w)//2:,} edges")

    def nearest(self, pt):
        d, i = self.tree.query(xy([pt])[0])
        return float(d), int(i)

    def path(self, a, b, limit):
        dist, pred = dijkstra(self.G, indices=a, return_predecessors=True, limit=limit)
        if not np.isfinite(dist[b]):
            return None, None
        out, i = [], b
        while i != a and i >= 0:
            out.append(i); i = pred[i]
        out.append(a)
        return [tuple(self.coords[j]) for j in reversed(out)], float(dist[b])


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    P = np.asarray(pts); a, b = P[0], P[-1]; v = b - a; n = math.hypot(*v)
    d = np.abs(v[0] * (P[:, 1] - a[1]) - v[1] * (P[:, 0] - a[0])) / n if n else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps:
        return rdp(pts[: i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


def km_len(c):
    c = np.asarray(c)
    return float(np.hypot(np.diff(c[:, 0]) * KX, np.diff(c[:, 1]) * KY).sum()) if len(c) > 1 else 0.0


sys.setrecursionlimit(100000)
routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
# routes whose lore waypoints don't follow any real road: route between these points instead
VIA = {
    # Talas -> Otmok pass -> Suusamyr -> Ala-Bel (the Fergana Gateway) -> Chychkan valley -> Toktogul basin -> Kara-Kol -> Naryn gorge -> Tash-Komur
    "fergana-mountain-transit-highway": [[72.24, 42.52], [72.22, 41.35]],
}
nets = {}
report = []
SNAP_KM = {"road": 4.0, "rail": 6.0, "water": 3.0}
for r in routes:
    net_name = {"highway": "road", "road": "road", "railway": "rail", "canal": "water"}.get(r["kind"])
    if not net_name:
        report.append(f"{r['id']}: {r['kind']}, kept as drawn ({km_len(r['coords']):.0f} km)")
        continue
    if net_name not in nets:
        print("building", net_name); nets[net_name] = Net(NETS[net_name])
    src = r.get("coords_lore") or r["coords"]
    if r["id"] in VIA:
        src = VIA[r["id"]]
    # an invented railway with no real track nearby follows the valley road instead
    if net_name == "rail":
        if "rail" not in nets:
            print("building rail"); nets["rail"] = Net(NETS["rail"])
        near = sum(nets["rail"].nearest(p)[0] <= SNAP_KM["rail"] for p in src)
        if near < len(src) / 2:
            net_name = "road"
            if "road" not in nets:
                print("building road"); nets["road"] = Net(NETS["road"])
    N = nets[net_name]
    snapped = []
    for pt in src:
        d, i = N.nearest(pt)
        snapped.append((pt, d, i))
    keep = [s for s in snapped if s[1] <= SNAP_KM[net_name]]
    dropped = len(snapped) - len(keep)
    out, straight_bits = [], 0
    if not keep:
        report.append(f"{r['id']}: no real {net_name} near any waypoint, kept as drawn")
        continue
    # lead-in from the original first point if it is off the network
    if snapped[0][1] > SNAP_KM[net_name]:
        out.append(tuple(src[0]))
    for (p1, d1, i1), (p2, d2, i2) in zip(keep[:-1], keep[1:]):
        if i1 == i2:
            continue
        straight = math.hypot((N.coords[i1][0] - N.coords[i2][0]) * KX, (N.coords[i1][1] - N.coords[i2][1]) * KY)
        seg, cost = N.path(i1, i2, limit=max(straight * 4, 30) if r["id"] not in VIA else 2000)
        if seg is None or (r["id"] not in VIA and km_len(seg) > max(straight * 2.6, straight + 25)):
            out += [tuple(N.coords[i1]), tuple(N.coords[i2])]; straight_bits += 1
        else:
            out += seg if not out or out[-1] != seg[0] else seg[1:]
    if snapped[-1][1] > SNAP_KM[net_name]:
        out.append(tuple(src[-1]))
    # tidy: drop immediate back-and-forth duplicates, simplify to ~25 m
    clean = []
    for p in out:
        if clean and clean[-1] == p:
            continue
        if len(clean) >= 2 and clean[-2] == p:
            clean.pop(); continue
        clean.append(p)
    clean = rdp(clean, 0.00025)
    if len(clean) < 2 or km_len(clean) < 0.5:
        report.append(f"{r['id']}: snapping collapsed the line, kept as drawn"); continue
    before, after = km_len(src), km_len(clean)
    r.setdefault("coords_lore", src)
    r["coords"] = [[round(x, 5), round(y, 5)] for x, y in clean]
    r["snapped"] = net_name
    report.append(f"{r['id']}: {net_name}, {len(src)} waypoints ({dropped} too far from the network, skipped), "
                  f"{straight_bits} gaps bridged straight, {before:.0f} km as drawn -> {after:.0f} km along real {net_name}s, {len(clean)} points")

json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
print("\n".join(report))
