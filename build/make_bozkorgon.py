"""Boz-Korgon restricted area, drawn from the terrain instead of a circle.

- the compound (~120 ha): a walled enclosure on the crest of the spur, its long side along the spur;
- the restricted zone: the spur and its slopes above the plain (ground ~60 m above the valley floor around it, within
  ~5 km), widened by a security strip and simplified into straight fence lines between corner posts, plus the guarded
  approach along the road and rail stub from the west.
Writes data/boz_korgon.geojson. Run: python3 build/make_bozkorgon.py irad-dem.bin
"""
import json, math, os, struct, sys
import numpy as np
from scipy import ndimage
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = open(sys.argv[1], "rb").read()
lon0, lat0, st = struct.unpack("<3d", b[8:32]); nx, ny = struct.unpack("<2i", b[32:40])
DEM = np.frombuffer(b[64:], dtype="<i2").reshape(ny, nx).astype(float)
P = {p["id"]: p for p in json.load(open(os.path.join(ROOT, "data/settlements.json")))}
R = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "data/routes.json")))}
cx, cy = P["boz-korgon"]["lon"], P["boz-korgon"]["lat"]
KX = 111.32 * math.cos(math.radians(cy)); KY = 110.57
G = 0.001
lons = np.arange(cx - 0.12, cx + 0.12, G); lats = np.arange(cy - 0.08, cy + 0.08, G)
GX, GY = np.meshgrid(lons, lats)
E = ndimage.map_coordinates(DEM, [(GY - lat0) / st, (GX - lon0) / st], order=1)
E = ndimage.gaussian_filter(E, 3)
D = np.hypot((GX - cx) * KX, (GY - cy) * KY)
ec = E[np.unravel_index(np.argmin(D), D.shape)]
floor = np.percentile(E[D < 7], 10)
# the spur between two ravines: the ravine floors to the north and south (lowest ground in each band) and the crest
# above the compound to the east bound it; the west side stops where the spur meets the plain
def ravine(lo, hi):
    out = []
    for i, x in enumerate(lons):
        js = np.where((lats >= lo) & (lats <= hi))[0]
        out.append(lats[js[np.argmin(E[js, i])]])
    return ndimage.median_filter(np.array(out), 15)[None, :]
north = ravine(cy + 0.012, cy + 0.05); south = ravine(cy - 0.05, cy - 0.012)
east_x = cx + 4.2 / KX
spur = (GY < north) & (GY > south) & (GX < east_x) & (E > floor + 25) & (D < 6)
lab, n = ndimage.label(spur); spur = lab == lab[np.unravel_index(np.argmin(D), D.shape)]
# approach corridor: 1 km either side of the road and rail stub for the last 6 km
corr = np.zeros(GX.shape, bool)
for rid in ("boz-korgon-branch", "irad-temir-jolu-east-line"):
    for x, y in R[rid]["coords"]:
        if math.hypot((x - cx) * KX, (y - cy) * KY) < 6:
            corr |= np.hypot((GX - x) * KX, (GY - y) * KY) < 0.6
zone = ndimage.binary_dilation(spur, iterations=3) | corr          # + ~500 m security strip
zone = ndimage.binary_fill_holes(ndimage.binary_closing(zone, iterations=8))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt


def outline(m, sigma):
    fig = plt.figure(); cs = plt.contour(GX, GY, ndimage.gaussian_filter(m.astype(float), sigma), levels=[0.5]); s = max(cs.allsegs[0], key=len); plt.close(fig)
    return s


def rdp(pts, eps):
    if len(pts) < 3: return list(pts)
    a, b_ = pts[0], pts[-1]; v = ((b_[0] - a[0]) * KX, (b_[1] - a[1]) * KY); nn = math.hypot(*v)
    dd = [abs(v[0] * (p[1] - a[1]) * KY - v[1] * (p[0] - a[0]) * KX) / nn if nn else math.hypot((p[0] - a[0]) * KX, (p[1] - a[1]) * KY) for p in pts]
    i = int(np.argmax(dd))
    if dd[i] > eps: return rdp(pts[: i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


ring = [tuple(p) for p in outline(zone, 2)]
fence = rdp(ring[:-1], 0.22) + [ring[0]]          # straight fence lines, posts where the line turns by more than ~220 m
# compound: the 120 ha around the crest point, its long axis along the spur (principal axis of the spur near the centre)
near = spur & (D < 1.5)
pts = np.column_stack([(GX[near] - cx) * KX, (GY[near] - cy) * KY])
gy_, gx_ = np.gradient(E, G * KY, G * KX)
m_ = D < 1.5
ang = math.atan2(gy_[m_].mean(), gx_[m_].mean())     # the spur rises along the fall line: long axis up the spur
L, W_ = 1.45, 0.83         # km, ~120 ha
corners = [(-L / 2, -W_ / 2), (L / 2, -W_ / 2), (L / 2, W_ / 2), (-L / 2, W_ / 2)]
# chamfer two corners so it is not a perfect rectangle (the wall follows the crest)
corners = [(-L / 2, -W_ / 2), (L / 2 - 0.25, -W_ / 2), (L / 2, -W_ / 2 + 0.2), (L / 2, W_ / 2), (-L / 2 + 0.3, W_ / 2), (-L / 2, W_ / 2 - 0.15)]
comp = [(cx + (x * math.cos(ang) - y * math.sin(ang)) / KX, cy + (x * math.sin(ang) + y * math.cos(ang)) / KY) for x, y in corners]
comp.append(comp[0])
area = lambda r: 0.5 * abs(sum((a[0] * b_[1] - b_[0] * a[1]) * KX * KY for a, b_ in zip(r, r[1:])))
r5 = lambda r: [[round(x, 5), round(y, 5)] for x, y in r]
def label_pt():
    from matplotlib.path import Path as _P
    F_ = _P(np.array(fence)); Cc = np.array(comp).mean(0); best = None
    xs = np.linspace(min(p[0] for p in fence), max(p[0] for p in fence), 60); ys = np.linspace(min(p[1] for p in fence), max(p[1] for p in fence), 60)
    for x in xs:
        for y in ys:
            if not F_.contains_point((x, y)): continue
            dc = math.hypot((x - Cc[0]) * KX, (y - Cc[1]) * KY)
            de = min(math.hypot((x - a) * KX, (y - b_) * KY) for a, b_ in fence)
            sc = min(de, 1.2) + 0.3 * min(dc, 2.0)
            if dc > 1.0 and (best is None or sc > best[0]): best = (sc, x, y)
    return [round(best[1], 5), round(best[2], 5)] if best else r5([Cc])[0]
out = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"kind": "zone", "name": "Boz-Korgon restricted area", "area_km2": round(area(fence), 1)}, "geometry": {"type": "Polygon", "coordinates": [r5(fence)]}},
    {"type": "Feature", "properties": {"kind": "compound", "name": "Boz-Korgon compound", "area_ha": round(area(comp) * 100)}, "geometry": {"type": "Polygon", "coordinates": [r5(comp)]}},
    # one label point inside the fence, clear of the compound (a polygon label repeats on every tile)
    {"type": "Feature", "properties": {"kind": "label"}, "geometry": {"type": "Point", "coordinates": label_pt()}}]}
json.dump(out, open(os.path.join(ROOT, "data/boz_korgon.geojson"), "w"))
print(f"restricted area {area(fence):.1f} km2, {len(fence) - 1} fence posts; compound {area(comp) * 100:.0f} ha at {ec:.0f} m (plain ~{floor:.0f} m)")

# the compound's point in the gazetteer sits in the compound
cc = np.array(comp[:-1]).mean(0)
for fn in ("data/features.json", "data/settlements.json"):
    pts = json.load(open(os.path.join(ROOT, fn)))
    for p in pts:
        if p["id"] == "boz-korgon":
            p["lon"], p["lat"] = round(float(cc[0]), 5), round(float(cc[1]), 5)
            if fn.endswith("features.json"): p["elev"] = 890
    json.dump(pts, open(os.path.join(ROOT, fn), "w"), ensure_ascii=False, indent=1)
