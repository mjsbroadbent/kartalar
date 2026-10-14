"""Rebuild the Qara-Chik Demarcation Line, the ISEZ/ATR zones and the ISEZ districts from real terrain.

Rules, following the wiki's description of the line (Qara-Chik Demarcation Line, "Course"):
- Central and western sectors: along the northern foothills of the Talas Alatau, at the upper edge of the
  irrigated fans (land more than H metres above the Talas valley floor is tribal); the line bulges south
  around the Sary-Bulak industrial corridor (the Kara-Suu canyon road).
- Western sector: the Karatau foothills are tribal; the ISEZ keeps the irrigated corridor along the railway
  to the frontier facing Shymkent.
- Northern sector: along the outer edge of the irrigated Talas and Chu plains (canals, the Turksib corridor,
  Nurzhan) facing the Moiynkum and the Betpak-Dala; straight surveyed segments between pillars.
- Southern (Naryn) sector: the crests around the lower Naryn (the catchment of the Naryn below the Toktogul
  dam); the dam itself stays tribal.
Inputs: the elevation grid from tools/dem-export.html and the OSM export from tools/osm-export.html.
Run: python3 build/make_line.py irad-dem.bin irad-osm-roads.json
"""
import json, os, sys, math, struct, heapq
import numpy as np
from matplotlib.path import Path
from scipy import ndimage

sys.setrecursionlimit(100000)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, OSMF = sys.argv[1], sys.argv[2]
STEP = 0.01
LON0, LON1, LAT0, LAT1 = 67.6, 75.8, 40.3, 46.4
lons = np.arange(LON0, LON1 + STEP / 2, STEP); lats = np.arange(LAT0, LAT1 + STEP / 2, STEP)
GX, GY = np.meshgrid(lons, lats)
PTS = np.column_stack([GX.ravel(), GY.ravel()])
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57
CELL_KM = STEP * KX  # ~0.82 km

# ---------- inputs ----------
b = open(DEMF, "rb").read()
d_lon0, d_lat0, d_step = struct.unpack("<3d", b[8:32]); d_nx, d_ny = struct.unpack("<2i", b[32:40])
DEM = np.frombuffer(b[64:], dtype="<i2").reshape(d_ny, d_nx).astype(float)
def dem_at(lon, lat):
    i = np.clip(np.round((np.asarray(lon) - d_lon0) / d_step).astype(int), 0, d_nx - 1)
    j = np.clip(np.round((np.asarray(lat) - d_lat0) / d_step).astype(int), 0, d_ny - 1)
    return DEM[j, i]
E = dem_at(GX, GY)
OSM = json.load(open(OSMF))["ways"]
R = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "data/routes.json")))}
P = {p["id"]: p for p in json.load(open(os.path.join(ROOT, "data/settlements.json"))) + json.load(open(os.path.join(ROOT, "data/features.json")))}


def mask_poly(rings):
    m = np.zeros(PTS.shape[0], bool)
    for ring in rings:
        m ^= Path(np.asarray(ring)).contains_points(PTS)
    return m.reshape(GX.shape)


def cell(lon, lat):
    return int(round((lat - LAT0) / STEP)), int(round((lon - LON0) / STEP))


def raster_lines(lines):
    m = np.zeros(GX.shape, bool)
    for c in lines:
        c = np.asarray(c)
        for (x1, y1), (x2, y2) in zip(c[:-1], c[1:]):
            n = int(max(abs(x2 - x1), abs(y2 - y1)) / (STEP / 2)) + 1
            for t in np.linspace(0, 1, n + 1):
                j, i = cell(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
                if 0 <= j < m.shape[0] and 0 <= i < m.shape[1]:
                    m[j, i] = True
    return m


def within_km(m, km):
    return ndimage.distance_transform_edt(~m) * CELL_KM <= km


irad_fc = json.load(open(os.path.join(ROOT, "data/irad.geojson")))
irad = np.zeros(GX.shape, bool)
for poly in irad_fc["features"][0]["geometry"]["coordinates"]:
    irad |= mask_poly(poly)

ways = lambda pred: [w["c"] for w in OSM if pred(w)]
canals = raster_lines(ways(lambda w: w["k"] == "water:canal"))
rail = raster_lines(ways(lambda w: w["k"].startswith("rail")))
talas_river = [c for c in ways(lambda w: w["k"] == "water:river" and (w.get("n") or "") in ("Талас", "Talas"))]
naryn_river = [c for c in ways(lambda w: w["k"] == "water:river" and (w.get("n") or "") in ("Нарын", "Naryn"))]

# ---------- central/western sectors: Talas Alatau foothills ----------
# valley axis: the Talas river east of 71.6 E, then the Kara-Buura railway west to the frontier
axis_pts = [p for c in talas_river for p in c if p[0] >= 71.6 and 42.3 < p[1] < 42.8]
axis_pts += [p for p in R["irad-temir-jolu-kara-buura-line"]["coords"] if p[0] < 71.45]
axis_pts = np.array(axis_pts)
bins = np.arange(69.9, 73.6, 0.02)
ax_lat, ax_floor = [], []
for x in bins:
    sel = axis_pts[np.abs(axis_pts[:, 0] - x) <= 0.04]
    if len(sel):
        ax_lat.append(np.median(sel[:, 1])); ax_floor.append(np.percentile(dem_at(sel[:, 0], sel[:, 1]), 20))
    else:
        ax_lat.append(np.nan); ax_floor.append(np.nan)
ax_lat, ax_floor = np.array(ax_lat), np.array(ax_floor)
ok = ~np.isnan(ax_lat)
ax_lat = np.interp(bins, bins[ok], ax_lat[ok]); ax_floor = np.interp(bins, bins[ok], ax_floor[ok])
ax_floor = ndimage.uniform_filter1d(ax_floor, 9); ax_lat = ndimage.uniform_filter1d(ax_lat, 5)
AXLAT = np.interp(GX, bins, ax_lat); FLOOR = np.interp(GX, bins, ax_floor)
H_SOUTH = 330  # metres above the valley floor where the irrigated fans end
south_high = (GY < AXLAT) & (E > FLOOR + H_SOUTH) & (GX >= 69.9) & (GX <= 73.6)
# keep only the mass joined to the high mountains (no tribal islands on valley-floor hillocks)
lab, n = ndimage.label(south_high)
sizes = ndimage.sum(south_high, lab, range(1, n + 1))
atr_south = np.isin(lab, 1 + np.where(sizes > 400)[0])
# everything beyond the crest of the Talas Alatau (the Chatkal side, the Toktogul basin, the Suusamyr) is tribal
crest_lat = np.full(lons.shape, np.nan)
for i, x in enumerate(lons):
    if not (69.9 <= x <= 73.6):
        continue
    a_ = np.interp(x, bins, ax_lat)
    js = np.where((lats >= a_ - 0.45) & (lats <= a_ - 0.04))[0]
    col = E[js, i]
    crest_lat[i] = lats[js[np.argmax(col)]]
ok_ = ~np.isnan(crest_lat)
crest_lat[ok_] = ndimage.median_filter(crest_lat[ok_], 15)
CREST = np.where(np.isnan(crest_lat), -90, crest_lat)[None, :].repeat(GX.shape[0], 0)
atr_south |= (GY < CREST) & (GX >= 69.9) & (GX <= 73.6)

# Sary-Bulak industrial corridor: the Kara-Suu canyon road to the works and the smelter stays ISEZ
sb_roads = raster_lines([R["sary-bulak-road"]["coords"], R["chatkal-smelter-road"]["coords"], R["irad-temir-jolu-sary-bulak-spur"]["coords"]] +
                        [[[P[k]["lon"], P[k]["lat"]], [P[k]["lon"] + 0.001, P[k]["lat"]]] for k in ("sary-bulak-antimony-works", "chatkal-smelting-complex", "sary-bulak", "chatkal") if k in P])
sary_bulak = within_km(sb_roads, 3.2) & (E < FLOOR + 1700) & (GY >= 42.245)

# ---------- western sector: Karatau foothills ----------
atr_karatau = (GX < 71.35) & (GY > AXLAT + 0.04) & (E > FLOOR + 160)

# ---------- northern sector: edge of the irrigated plains ----------
nur = P["nurzhan"]; bk = P["boz-korgon"]
city = np.zeros(GX.shape, bool)
for k, r in (("talas", 0), ("nurzhan", 0), ("boz-korgon", 0), ("kyzyl-adyr", 0)):
    if k in P:
        j, i = cell(P[k]["lon"], P[k]["lat"]); city[j, i] = True
turksib = rail & (GX >= 70.2) & (GX <= 75.0) & (GY >= 42.4) & (GY <= 44.2)
irrigated = within_km(canals & (E < 1100), 4.0) | within_km(turksib, 6.0) | within_km(city & (GY > 43), 16)
irrigated = ndimage.binary_closing(irrigated, iterations=14)
irrigated = ndimage.binary_opening(irrigated, iterations=5)
irrigated = ndimage.binary_closing(irrigated, iterations=6)
irrigated = ndimage.binary_fill_holes(irrigated)
# guarded corridors to the oil fields and the northern rail border station
irrigated |= within_km(raster_lines([R[k]["coords"] for k in ("nurzhan-petroleum-pipeline", "northern-export-feeder", "irad-temir-jolu-north-line") if k in R]), 3.0)
atr_north = (E < 1000) & (GY > 42.78) & ~irrigated

# ---------- Talas-Chu complex ----------
box = (GX >= 69.9) & (GX <= 75.05) & (GY >= 42.0) & (GY <= 44.7)
# north of the Kirghiz Range (and west of Kyzyl-Adyr) only the irrigated plains are ISEZ; between the ranges
# everything below the Talas Alatau foothills is ISEZ
region_north = (GY > 42.88) | ((GX > 73.3) & (GY > 42.72)) | ((GX < 71.4) & (GY > AXLAT + 0.05))
tc = irad & box & ((region_north & irrigated) | (~region_north & ~atr_south & ~atr_karatau))
tc |= irad & sary_bulak & ~region_north
# the Trans-Talas Highway and the railway along the Kara-Buura corridor stay inside the ISEZ
tc |= irad & within_km(raster_lines([R["trans-talas-highway"]["coords"], R["irad-temir-jolu-kara-buura-line"]["coords"]]), 2.5)
# the lore's own ISEZ places pull the line around them (villages, works, checkpoints, oil fields);
# its tribal places push it back
SKIP_KINDS = {"park", "peak", "pass", "lake", "river-point", "other", "reservoir", "spring", "district", "zone-area"}
pin_in = np.zeros(GX.shape, bool); pin_out = np.zeros(GX.shape, bool)
for p in P.values():
    if p.get("kind") in SKIP_KINDS or p["lat"] < 41.95:
        continue
    j, i = cell(p["lon"], p["lat"])
    if p["zone"] == "ISEZ":
        pin_in[j, i] = True
    elif p.get("confidence") != "placed":
        pin_out[j, i] = True
pins = within_km(pin_in, 2.6) & irad & box
tc |= pins
# join any island to the main body along the shortest line (a valley corridor)
lab, n = ndimage.label(tc)
main = {lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("talas", "nurzhan", "kyzyl-adyr") if k in P} - {0}
main_mask = np.isin(lab, list(main))
dist_main, (nj, ni) = ndimage.distance_transform_edt(~main_mask, return_indices=True)
links = np.zeros(GX.shape, bool)
for k in range(1, n + 1):
    if k in main:
        continue
    comp = lab == k
    if comp.sum() > 20000:
        continue
    cj, ci = np.unravel_index(np.argmin(np.where(comp, dist_main, np.inf)), comp.shape)
    if dist_main[cj, ci] * CELL_KM > 25:
        continue
    tj, ti = nj[cj, ci], ni[cj, ci]
    for t in np.linspace(0, 1, int(max(abs(tj - cj), abs(ti - ci))) + 2):
        links[int(round(cj + (tj - cj) * t)), int(round(ci + (ti - ci) * t))] = True
tc |= within_km(links, 1.3) & irad
tc &= ~within_km(pin_out, 1.6)
# the upper Talas valley above the mouth of the Otmek valley is tribal
kcrest = np.full(lons.shape, 43.0)
for i, x in enumerate(lons):
    js = np.where((lats >= 42.5) & (lats <= 43.0))[0]
    kcrest[i] = lats[js[np.argmax(E[js, i])]]
kcrest = ndimage.median_filter(kcrest, 11)
tc &= ~((GX > 72.975) & (GY < kcrest[None, :]))
lab, n = ndimage.label(tc)
keep = {lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("talas", "nurzhan", "kyzyl-adyr") if k in P} - {0}
tc = np.isin(lab, list(keep))
tc = ndimage.binary_fill_holes(tc) & irad
# drop slivers: open/close a little so the line doesn't zigzag cell by cell
tc = ndimage.binary_closing(tc, iterations=3) & irad
tc = ndimage.binary_opening(tc, iterations=2)
lab, n = ndimage.label(tc)
tc = np.isin(lab, list({lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("talas", "nurzhan") if k in P} - {0}))

# ---------- southern (Naryn) sector: catchment of the Naryn below the Toktogul dam ----------
W = (71.2, 73.3, 40.95, 42.25)
wi0, wi1 = int((W[0] - d_lon0) / d_step), int((W[1] - d_lon0) / d_step)
wj0, wj1 = int((W[2] - d_lat0) / d_step), int((W[3] - d_lat0) / d_step)
Z = DEM[wj0:wj1, wi0:wi1].copy()
ny_, nx_ = Z.shape
# priority-flood: fill pits and record flow direction toward the outlet
filled = np.full(Z.shape, np.inf); visited = np.zeros(Z.shape, bool); down = np.full(Z.shape + (2,), -1)
pq = []
for j in range(ny_):
    for i in range(nx_):
        if j in (0, ny_ - 1) or i in (0, nx_ - 1):
            heapq.heappush(pq, (Z[j, i], j, i)); visited[j, i] = True; filled[j, i] = Z[j, i]
nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
while pq:
    z, j, i = heapq.heappop(pq)
    for dj, di in nb:
        jj, ii = j + dj, i + di
        if 0 <= jj < ny_ and 0 <= ii < nx_ and not visited[jj, ii]:
            visited[jj, ii] = True
            filled[jj, ii] = max(Z[jj, ii], z)
            down[jj, ii] = (j, i)
            heapq.heappush(pq, (filled[jj, ii], jj, ii))
# the reach: Naryn river cells between the dam and where the river leaves the hills
dam = P.get("toktogul-dam", {"lat": 41.677, "lon": 72.644})
reach = np.zeros(Z.shape, bool)
for c in naryn_river:
    for x, y in c:
        if 41.16 <= y <= 41.585 and W[0] < x < W[1]:   # from below Kara-Köl down to where the river leaves the hills
            j, i = int(round((y - d_lat0) / d_step)) - wj0, int(round((x - d_lon0) / d_step)) - wi0
            if 0 <= j < ny_ and 0 <= i < nx_:
                reach[j, i] = True
reach = ndimage.binary_dilation(reach, iterations=1)
# walk every cell downstream; it belongs to the salient if it reaches the reach before leaving
basin = np.zeros(Z.shape, bool); state = np.zeros(Z.shape, np.int8)  # 0 unknown, 1 in, 2 out
for j0 in range(ny_):
    for i0 in range(nx_):
        if state[j0, i0]:
            continue
        path, j, i = [], j0, i0
        while True:
            if state[j, i]:
                res = state[j, i]; break
            if reach[j, i]:
                res = 1; break
            path.append((j, i))
            dj = down[j, i]
            if dj[0] < 0:
                res = 2; break
            j, i = int(dj[0]), int(dj[1])
        for (a, c) in path:
            state[a, c] = res
basin = (state == 1) | reach
naryn_dem = np.zeros(DEM.shape, bool); naryn_dem[wj0:wj1, wi0:wi1] = basin
naryn = dem_at(GX, GY) * 0 > 1  # placeholder same shape
ii = np.clip(np.round((GX - d_lon0) / d_step).astype(int), 0, d_nx - 1); jj = np.clip(np.round((GY - d_lat0) / d_step).astype(int), 0, d_ny - 1)
# the salient keeps to the crests nearest the river: the catchment, but no further than 20 km from the reach
reach_g = np.zeros(GX.shape, bool)
for c in naryn_river:
    for x, y in c:
        if 41.16 <= y <= 41.585:
            j, i = cell(x, y); reach_g[j, i] = True
naryn = naryn_dem[jj, ii] & irad & within_km(reach_g, 20)
# the dam and the reservoir shore stay tribal; the switchyard stays ISEZ
naryn &= ~((np.hypot((GX - dam["lon"]) * KX, (GY - dam["lat"]) * KY) < 2.2))
lab, n = ndimage.label(naryn)
seed = [lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("tash-komur", "iyik-janyl") if k in P]
naryn = np.isin(lab, [s for s in seed if s])
naryn = ndimage.binary_fill_holes(ndimage.binary_opening(naryn, iterations=1))
# the last power station of the cascade, where the river leaves the hills
uk = P.get("uch-kurgan-hps")
if uk:
    naryn |= irad & (np.hypot((GX - uk["lon"]) * KX, (GY - uk["lat"]) * KY) < 2.2)
# Kara-Köl and the slopes around the dam stay tribal (canon)
naryn &= ~((GY > 41.595) & (GX > 72.55))
lab, n = ndimage.label(naryn)
naryn = np.isin(lab, [s_ for s_ in [lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("tash-komur", "iyik-janyl")] if s_])
# the Toktogul switchyard: a small ISEZ pocket below the dam, joined to the salient along the road
sw = P.get("toktogul-switchyard")
if sw:
    naryn |= irad & (np.hypot((GX - sw["lon"]) * KX, (GY - sw["lat"]) * KY) < 1.6)

isez = tc | naryn
atr_holes, n = ndimage.label(irad & ~isez)
small = [k + 1 for k, v in enumerate(ndimage.sum(np.ones_like(atr_holes), atr_holes, range(1, n + 1))) if v < 60]
isez |= np.isin(atr_holes, small)
cell_km2 = (STEP * 111.32 * np.cos(np.radians(GY))) * (STEP * 110.57)
area = lambda m: float(cell_km2[m].sum())
print("ISEZ %.0f km2 (Talas-Chu %.0f, Naryn %.0f), ATR %.0f" % (area(isez), area(tc), area(naryn), area(irad & ~isez)))

# ---------- districts ----------
south_of_axis = GY < AXLAT
dist = {"Lower Naryn": naryn, "Sary-Bulak": tc & sary_bulak & south_of_axis & (GY < AXLAT - 0.06)}
rest = tc & ~dist["Sary-Bulak"]
dist["Chu"] = rest & (GX >= 72.95) & (GY >= 42.72)
dist["Kara-Buura"] = rest & ~dist["Chu"] & (GX < 71.92)
dist["Talas"] = rest & ~dist["Chu"] & ~dist["Kara-Buura"]
for k, v in dist.items():
    print("  %-12s %.0f km2" % (k, area(v)))


# ---------- tracing ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    P_ = np.asarray(pts); a, b_ = P_[0], P_[-1]; v = b_ - a; nn = math.hypot(*v)
    dd = np.abs(v[0] * (P_[:, 1] - a[1]) - v[1] * (P_[:, 0] - a[0])) / nn if nn else np.hypot(*(P_ - a).T)
    i = int(np.argmax(dd))
    if dd[i] > eps:
        return rdp(pts[: i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


def rings_of(m):
    fig = plt.figure(); cs = plt.contour(GX, GY, m.astype(float), levels=[0.5]); segs = cs.allsegs[0]; plt.close(fig)
    return [[tuple(map(float, p)) for p in s] for s in segs if len(s) > 3]


def trace(m, eps=0.003, min_km2=2):
    rings = []
    for r in rings_of(m):
        if r[0] != r[-1]:
            r.append(r[0])
        r = rdp(r[:-1], eps) + [r[0]]
        if len(r) < 4:
            continue
        x, y = np.array(r).T
        a = 0.5 * abs(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1]))
        if a * 111 * 82 < min_km2:
            continue
        rings.append((a, [[round(px, 4), round(py, 4)] for px, py in r]))
    rings.sort(key=lambda t: -t[0]); polys = []
    for a, r in rings:
        host = None
        for Pp in polys:
            if Path(np.array(Pp[0])).contains_point(r[0]):
                host = Pp
        if host is not None and len(host) == 1:
            host.append(r)
        else:
            polys.append([r])
    return {"type": "MultiPolygon", "coordinates": polys}


def feat(geom, **props):
    return {"type": "Feature", "properties": props, "geometry": geom}


out = os.path.join(ROOT, "data")
json.dump({"type": "FeatureCollection", "features": [
    feat(trace(isez), zone="ISEZ", name="Irad Special Economic Zone", name_ir="Irad Atayın Ekonomikalık Zonası", name_ru="Особая экономическая зона Ирада", area_km2=round(area(isez))),
    feat(trace(irad & ~isez), zone="ATR", name="Autonomous Tribal Regions", name_ir="Avtonomduu Uruu Aymaktarı", name_ru="Автономные племенные районы", area_km2=round(area(irad & ~isez)))]},
    open(os.path.join(out, "zones.geojson"), "w"))
json.dump({"type": "FeatureCollection", "features": [feat(trace(m, 0.003, 1), district=k, area_km2=round(area(m))) for k, m in dist.items()]},
          open(os.path.join(out, "districts.geojson"), "w"))

# ---------- the line itself: ISEZ outline minus the stretches on Irad's international border ----------
border_cells = irad & ~ndimage.binary_erosion(irad, iterations=1)
near_border = within_km(border_cells, 2.0)
rivers_all = raster_lines(ways(lambda w: w["k"] == "water:river"))
near_river = within_km(rivers_all, 0.9)
near_canal = within_km(canals, 0.9)
pieces = []
for r in rings_of(isez):
    cur = []
    for x, y in r:
        j, i = cell(x, y)
        on_border = near_border[min(max(j, 0), GX.shape[0] - 1), min(max(i, 0), GX.shape[1] - 1)]
        if on_border:
            if len(cur) > 3: pieces.append(cur)
            cur = []
        else:
            cur.append((x, y))
    if len(cur) > 3: pieces.append(cur)


def sector(x, y):
    if y < 41.9: return "southern"
    if y > 42.75 or x > 72.95: return "northern"
    if x < 71.6: return "western"
    return "central"


def follows(x, y):
    j, i = cell(x, y)
    e = E[j, i]
    if near_river[j, i]: return "river"
    if near_canal[j, i]: return "canal"
    if y < 41.9: return "crest"
    if e > 1500: return "foothills"
    return "survey"


feats, total = [], 0.0
for pc in pieces:
    # split each piece into runs of the same sector and character; plains get straight pillar-to-pillar segments
    runs, cur, key = [], [pc[0]], (sector(*pc[0]), follows(*pc[0]))
    for p in pc[1:]:
        k = (sector(*p), follows(*p))
        if k != key and len(cur) > 6:
            runs.append((key, cur)); cur = [cur[-1]]; key = k
        cur.append(p)
    runs.append((key, cur))
    for (sec, fol), c in runs:
        eps = {"survey": 0.045, "canal": 0.012, "river": 0.003, "foothills": 0.005, "crest": 0.004}[fol]
        c = rdp(c, eps)
        if len(c) < 2: continue
        km = sum(math.hypot((a[0] - b_[0]) * KX, (a[1] - b_[1]) * KY) for a, b_ in zip(c, c[1:]))
        total += km
        feats.append(feat({"type": "LineString", "coordinates": [[round(x, 4), round(y, 4)] for x, y in c]}, sector=sec, follows=fol, km=round(km, 1)))
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(out, "qarachik.geojson"), "w"))
print("Qara-Chik line: %.0f km in %d pieces" % (total, len(feats)))
by = {}
for f in feats:
    by[(f["properties"]["sector"], f["properties"]["follows"])] = by.get((f["properties"]["sector"], f["properties"]["follows"]), 0) + f["properties"]["km"]
for k, v in sorted(by.items()):
    print("  %-9s %-9s %4.0f km" % (k[0], k[1], v))
line_cells = raster_lines([f["geometry"]["coordinates"] for f in feats])
rwz = within_km(line_cells, 12) & irad
json.dump({"type": "FeatureCollection", "features": [feat(trace(rwz, 0.004, 5), name="Restricted-weapons zone")]}, open(os.path.join(out, "restricted_zone.geojson"), "w"))
np.save(os.path.join(os.path.dirname(DEMF), "isez_mask.npy"), isez)
