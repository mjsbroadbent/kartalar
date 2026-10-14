"""Lay the pipelines and power lines that the lore puts 'along' a road or railway onto that route's final course.
Run after build/route_terrain.py."""
import json, math, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57
km = lambda a, b: math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)
routes = json.load(open(os.path.join(ROOT, "data/routes.json"))); R = {r["id"]: r for r in routes}


def rdp(pts, eps):
    if len(pts) < 3: return list(pts)
    a, b = pts[0], pts[-1]; vx, vy = (b[0] - a[0]) * KX, (b[1] - a[1]) * KY; n = math.hypot(vx, vy)
    best, bi = -1, 0
    for i, p in enumerate(pts):
        rx, ry = (p[0] - a[0]) * KX, (p[1] - a[1]) * KY
        d = abs(vx * ry - vy * rx) / n if n else math.hypot(rx, ry)
        if d > best: best, bi = d, i
    if best > eps: return rdp(pts[:bi + 1], eps)[:-1] + rdp(pts[bi:], eps)
    return [pts[0], pts[-1]]


def part(rid, frm=None, to=None, reverse=False):
    c = [tuple(p) for p in R[rid]["coords"]]
    if reverse: c = c[::-1]
    i = min(range(len(c)), key=lambda k: km(c[k], frm)) if frm else 0
    j = min(range(len(c)), key=lambda k: km(c[k], to)) if to else len(c) - 1
    return c[i:j + 1]


def chain(*parts):
    out = []
    for p in parts:
        out += p if not out else p[1:] if km(out[-1], p[0]) < 0.5 else p
    return out


def put(rid, pts, eps, note=None):
    pts = rdp(pts, eps)
    R[rid]["coords"] = [[round(x, 5), round(y, 5)] for x, y in pts]
    R[rid]["length_km"] = round(sum(km(a, b) for a, b in zip(pts, pts[1:])))
    if note: R[rid]["note"] = note
    print(f"{rid:36} {R[rid]['length_km']:4d} km, {len(pts)} pts")


# the Otmek tunnel (2003): ~5 km under the crest below the Ötmök pass, portals ~3,150-3,200 m; the old pass road stays
sr = [tuple(p) for p in R["fergana-mountain-transit-highway"]["coords"]]
T = [(73.14296, 42.28578), (73.19532, 42.26326)]
if not R["fergana-mountain-transit-highway"].get("tunnels"):
    i = min(range(len(sr)), key=lambda k: km(sr[k], T[0])); j = min(range(len(sr)), key=lambda k: km(sr[k], T[1]))
    sr = sr[:i + 1] + sr[j:]
    R["fergana-mountain-transit-highway"]["coords"] = [list(p) for p in sr]
    R["fergana-mountain-transit-highway"]["tunnels"] = [[list(sr[i]), list(sr[i + 1])]]
R["fergana-mountain-transit-highway"]["length_km"] = round(sum(km(a, b) for a, b in zip(sr, sr[1:])))
print("State Route 1", R["fergana-mountain-transit-highway"]["length_km"], "km")

sw, ab = (72.615, 41.64), (72.093, 42.533)
# jet-fuel line: beside the Turksib from the Nurzhan refinery to the junction below Taraz, then the Talas branch to the air base
put("talas-air-base-products-pipeline",
    chain([(73.822, 43.598)], part("irad-temir-jolu-chu-line"), part("irad-temir-jolu-talas-branch", to=ab), [ab]), 0.3)
# export power lines: straight spans between angle towers, following the State Route 1 corridor
put("toktogul-north-export-line",
    chain([sw], part("fergana-mountain-transit-highway", frm=sw, reverse=True), part("trans-talas-highway", reverse=True)), 1.2)
put("toktogul-south-export-line",
    chain([sw], part("fergana-mountain-transit-highway", frm=sw), part("lower-naryn-uzbek-road")), 0.8)
json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
