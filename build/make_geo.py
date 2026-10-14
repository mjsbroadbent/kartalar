"""Build Irad's border, ISEZ/ATR zones and ISEZ districts as GeoJSON.

Method: rasterise real admin-1 regions (Natural Earth 10m) and hand-drawn lore polygons on a
0.01-degree grid, combine them with boolean masks, then trace the outlines back to polygons.
Run:  python3 build/make_geo.py <path to ne_10m_admin_1_states_provinces.geojson>
"""
import json, sys, os
sys.setrecursionlimit(100000)
import numpy as np
from matplotlib.path import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NE = sys.argv[1]
STEP = 0.01
LON0, LON1, LAT0, LAT1 = 67.6, 75.8, 40.3, 46.4
lons = np.arange(LON0, LON1 + STEP / 2, STEP)
lats = np.arange(LAT0, LAT1 + STEP / 2, STEP)
GX, GY = np.meshgrid(lons, lats)
PTS = np.column_stack([GX.ravel(), GY.ravel()])


def mask_poly(rings):
    m = np.zeros(PTS.shape[0], bool)
    for ring in rings:
        m ^= Path(np.asarray(ring)).contains_points(PTS)
    return m.reshape(GX.shape)


def mask_geom(g):
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    m = np.zeros(GX.shape, bool)
    for p in polys:
        m |= mask_poly(p)
    return m


def near_line(coords, km):
    """cells within km of a polyline"""
    m = np.zeros(GX.shape, bool)
    c = np.asarray(coords)
    kx = 111.32 * np.cos(np.radians(42.5))
    for (x1, y1), (x2, y2) in zip(c[:-1], c[1:]):
        lo_x, hi_x = min(x1, x2) - km / kx, max(x1, x2) + km / kx
        lo_y, hi_y = min(y1, y2) - km / 111, max(y1, y2) + km / 111
        sel = (GX >= lo_x) & (GX <= hi_x) & (GY >= lo_y) & (GY <= hi_y)
        px, py = (GX[sel] - x1) * kx, (GY[sel] - y1) * 111
        dx, dy = (x2 - x1) * kx, (y2 - y1) * 111
        L = dx * dx + dy * dy or 1e-9
        t = np.clip((px * dx + py * dy) / L, 0, 1)
        d = np.hypot(px - t * dx, py - t * dy)
        idx = np.where(sel)
        m[idx[0][d <= km], idx[1][d <= km]] = True
    return m


ne = json.load(open(NE))
A = {}
for f in ne["features"]:
    p = f["properties"]
    if p.get("iso_3166_2") in ("KG-T", "KG-J", "KZ-ZHA", "KZ-YUZ", "UZ-NG", "UZ-AN"):
        A[p["iso_3166_2"]] = mask_geom(f["geometry"])

# ---------- Irad ----------
# NE side of the Karatau crest (Turkistan region): Turkistan city and Shymkent stay outside
# the Karatau and its foothills toward the Kyzylkum, north of a line that leaves Turkistan city, Kentau and Shymkent outside
city_line = [(67.6, 43.9), (68.65, 43.62), (69.0, 43.1), (69.4, 42.75), (70.0, 42.55), (70.05, 41.9)]
ne_of_line = mask_poly([city_line + [(75.8, 41.9), (75.8, 46.4), (67.6, 46.4)]])
turkistan_part = A["KZ-YUZ"] & ne_of_line & (GY <= 45.1)
# Uzbek rim: foothills north of Namangan, eastern rim of Andijan; the big cities stay outside
uz_rim = (A["UZ-NG"] & (GY >= 41.13)) | (A["UZ-AN"] & (GX >= 72.78) & (GY >= 40.72))
# Jambyl: everything west of 75 E, minus the Korday corner by Bishkek
jambyl = A["KZ-ZHA"] & (GX <= 75.0) & ~((GX >= 74.55) & (GY <= 43.28))
# the western end of the Suusamyr valley, held by Talas Alatau clans
suusamyr = mask_poly([[(72.95, 42.32), (73.75, 42.30), (73.80, 41.95), (73.20, 41.90), (72.95, 42.05)]])
# Jalal-Abad city stays with Kyrgyzstan, like the big Fergana cities on the Uzbek side
import math as _m
_ring = [(72.998 + 0.075 * _m.cos(t), 40.928 + 0.052 * _m.sin(t)) for t in [k * _m.pi / 18 for k in range(36)]]
jalal_abad = mask_poly([_ring]) | mask_poly([[(73.03, 40.9), (73.12, 40.87), (73.2, 40.78), (73.08, 40.76), (72.99, 40.86)]])
irad = (A["KG-T"] | A["KG-J"] | jambyl | turkistan_part | uz_rim | suusamyr) & (GX >= 68.0) & ~jalal_abad

# ---------- ISEZ ----------
R = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "data/routes.json")))}
# Talas valley floor, the Taraz plain and the Kara-Buura corridor west to the frontier facing Shymkent
valley = mask_poly([[(70.05, 42.38), (70.6, 42.46), (71.1, 42.58), (71.6, 42.46), (72.0, 42.36), (72.5, 42.32), (72.95, 42.38), (73.1, 42.55),
                     (73.2, 42.80), (72.6, 42.95), (72.0, 43.15), (71.4, 43.25), (71.1, 43.0), (70.6, 42.88), (70.1, 42.7)]])
# the belt along the Kirghiz Range foothills linking the Talas plain with the Chu (Kulan, Merke)
belt = mask_poly([[(71.9, 42.85), (72.6, 42.72), (73.3, 42.78), (73.4, 43.30), (72.6, 43.40), (71.9, 43.35)]])
# Talas-Nurzhan corridor along the Turksib and the Chu lowlands
corridor = near_line(R["irad-temir-jolu-chu-line"]["coords"], 9) | near_line(R["talas-nurzhan-road"]["coords"], 7)
# the lower Chu lowlands from Merke past Nurzhan and Boz-Korgon, down the Chu toward the Moiynkum
chu = mask_poly([[(73.2, 42.80), (73.8, 42.90), (74.55, 43.22), (75.0, 43.45), (75.0, 44.25), (74.1, 44.12), (73.75, 43.88), (73.5, 43.86), (73.0, 43.85), (72.9, 43.6), (72.85, 43.35)]])
# southern industrial corridor and foothills south of Talas (antimony works, Chatkal smelter)
sary_bulak = mask_poly([[(71.86, 42.42), (72.0, 42.37), (72.4, 42.34), (72.5, 42.30), (72.42, 42.285), (72.25, 42.282), (72.15, 42.245), (72.06, 42.275), (71.95, 42.28), (71.86, 42.30)]])
naryn = mask_poly([[(71.95, 41.10), (72.20, 40.98), (72.38, 41.18), (72.47, 41.40), (72.56, 41.50), (72.64, 41.60), (72.635, 41.650), (72.59, 41.655), (72.50, 41.59), (72.40, 41.55), (72.10, 41.45)]])
# the Fergana Mountain Transit Highway crosses tribal land (Suusamyr, Toktogul basin) as a guarded road, not ISEZ territory;
# only the short branch to Iyık Janyl is added to the Lower Naryn salient
fmth = near_line(R["iyik-janyl-branch-road"]["coords"], 2)
toktogul_dam = near_line([(72.62, 41.672), (72.66, 41.682)], 2.5)   # the dam itself stays with the ATR
isez = irad & (valley | belt | corridor | chu | sary_bulak | naryn | fmth) & ~toktogul_dam

# districts
dist = {
    "Lower Naryn": isez & (naryn | (fmth & (GY < 42.15))),
    "Sary-Bulak": isez & sary_bulak,
}
rest = isez & ~dist["Lower Naryn"] & ~dist["Sary-Bulak"]
dist["Chu"] = rest & (GX >= 72.95) & (GY >= 42.75)
dist["Kara-Buura"] = rest & ~dist["Chu"] & (GX < 71.92)
dist["Talas"] = rest & ~dist["Chu"] & ~dist["Kara-Buura"]

cell_km2 = (STEP * 111.32 * np.cos(np.radians(GY))) * (STEP * 110.57)
area = lambda m: float(cell_km2[m].sum())
for k in ("KG-T","KG-J"): print(k, round(area(A[k])))
print("jambyl", round(area(jambyl)), "turkistan part", round(area(turkistan_part)), "uz rim", round(area(uz_rim)))
print("Irad %.0f km2, ISEZ %.0f, ATR %.0f" % (area(irad), area(isez), area(irad & ~isez)))
for k, v in dist.items():
    print("  %-12s %.0f km2" % (k, area(v)))


# ---------- trace outlines ----------
def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = np.asarray(pts[0]), np.asarray(pts[-1])
    v = b - a
    n = np.hypot(*v)
    P = np.asarray(pts)
    d = np.abs(v[0] * (P[:, 1] - a[1]) - v[1] * (P[:, 0] - a[0])) / n if n else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps:
        return rdp(pts[: i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


def trace(m, eps=0.004, min_km2=4):
    fig = plt.figure()
    cs = plt.contour(GX, GY, m.astype(float), levels=[0.5])
    rings = []
    for path in cs.allsegs[0]:
        if len(path) < 4:
            continue
        r = [tuple(map(float, p)) for p in path]
        if r[0] != r[-1]:
            r.append(r[0])
        r = rdp(r[:-1], eps) + [r[0]]
        if len(r) < 4:
            continue
        x, y = np.array(r).T
        a = 0.5 * (np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1]))
        if abs(a) * 111 * 82 < min_km2:
            continue
        rings.append((abs(a), [[round(px, 4), round(py, 4)] for px, py in r]))
    plt.close(fig)
    # nest holes: a ring inside a bigger ring is a hole
    rings.sort(key=lambda t: -t[0])
    polys = []
    for a, r in rings:
        host = None
        for P in polys:
            if Path(np.array(P[0])).contains_point(r[0]):
                host = P
        if host is not None and len(host) == 1 and Path(np.array(host[0])).contains_points(np.array(r[:-1])).all():
            host.append(r)
        else:
            polys.append([r])
    return {"type": "MultiPolygon", "coordinates": polys}


def feat(geom, **props):
    return {"type": "Feature", "properties": props, "geometry": geom}


out = os.path.join(ROOT, "data")
json.dump({"type": "FeatureCollection", "features": [feat(trace(irad, 0.003), name="Irad", name_ir="Irad", name_ru="Ирад", area_km2=round(area(irad)))]},
          open(os.path.join(out, "irad.geojson"), "w"))
json.dump({"type": "FeatureCollection", "features": [
    feat(trace(isez, 0.003), zone="ISEZ", name="Irad Special Economic Zone", name_ir="Irad Atayın Ekonomikalık Zonası", name_ru="Особая экономическая зона Ирада", area_km2=round(area(isez))),
    feat(trace(irad & ~isez, 0.003), zone="ATR", name="Autonomous Tribal Regions", name_ir="Avtonomduu Uruu Aymaktarı", name_ru="Автономные племенные районы", area_km2=round(area(irad & ~isez)))]},
    open(os.path.join(out, "zones.geojson"), "w"))
json.dump({"type": "FeatureCollection", "features": [feat(trace(m, 0.003, 1), district=k, area_km2=round(area(m))) for k, m in dist.items()]},
          open(os.path.join(out, "districts.geojson"), "w"))
for f in ("irad", "zones", "districts"):
    print(f, os.path.getsize(os.path.join(out, f + ".geojson")) // 1024, "KB")
