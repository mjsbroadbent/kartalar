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

SKIP_KINDS0 = {"park", "peak", "pass", "lake", "river-point", "other", "reservoir", "spring", "district", "zone-area"}
# ---------- northern and western sectors: the settled plains ----------
# The plains ISEZ is a belt along the trunk roads and the railway (the M39 from the Shymkent frontier through Taraz and
# Merke, the road north to Nurzhan, the Turksib), with the irrigated farmland beside them. Secondary roads running
# out into the steppe do not pull the line with them.
road_k = lambda ks: raster_lines(ways(lambda w: w["k"] in ks))
plains = (GX >= 69.9) & (GX <= 75.05) & (GY >= 42.3) & (GY <= 43.85)
trunk = road_k({"road:motorway", "road:trunk"}) & plains & irad
main_roads = road_k({"road:motorway", "road:trunk", "road:primary"})
turksib = rail & plains & ~((GX < 71.3) & (GY > 42.95))  # not the Zhanatas branch into the Karatau
lore_core = raster_lines([R[k]["coords"] for k in ("trans-talas-highway", "talas-nurzhan-road", "chu-highway", "boz-korgon-branch",
                          "irad-temir-jolu-kara-buura-line", "irad-temir-jolu-chu-line", "irad-temir-jolu-talas-branch",
                          "irad-temir-jolu-east-line") if k in R])
core = trunk | turksib | lore_core
d_core = ndimage.distance_transform_edt(~core) * CELL_KM
settled = (d_core <= 7) & (E < 1100)
settled |= within_km(canals, 2.5) & (d_core <= 16) & (E < 1000)
for k in ("nurzhan", "boz-korgon"):
    if k in P:
        settled |= np.hypot((GX - P[k]["lon"]) * KX, (GY - P[k]["lat"]) * KY) < (14 if k == "nurzhan" else 6)
# guarded corridors to the oil fields and the northern rail border station
settled |= within_km(raster_lines([R[k]["coords"] for k in ("nurzhan-petroleum-pipeline", "northern-export-feeder", "irad-temir-jolu-north-line") if k in R]), 2.5)
# smooth the belt the way surveyors would draw it: wide sweeping curves, no fingers along every canal
settled = (ndimage.gaussian_filter(settled.astype(float), 4.0) > 0.5)
# around Nurzhan the oases, the oil fields and the rail yards merge into one district: close the gaps between the arms
chu_n = (GX > 72.95) & (GY > 43.2)
for p in P.values():
    if p["zone"] == "ISEZ" and p.get("confidence") in ("stated", "real-place") and p.get("kind") not in SKIP_KINDS0 and p["lon"] > 72.95 and p["lat"] > 43.2:
        settled |= np.hypot((GX - p["lon"]) * KX, (GY - p["lat"]) * KY) < 5
for k in ("chu-oil-fields", "nurgaz-field-collection-station"):
    if k in P:
        settled |= np.hypot((GX - P[k]["lon"]) * KX, (GY - P[k]["lat"]) * KY) < 5
closed = ~within_km(~within_km(settled & chu_n, 15), 15)
settled |= closed & chu_n
settled = (ndimage.gaussian_filter(settled.astype(float), 5.0) > 0.5)

# ---------- Talas-Chu complex ----------
box = (GX >= 69.9) & (GX <= 75.05) & (GY >= 42.0) & (GY <= 44.7)
# north of the Kirghiz Range (and west of Kyzyl-Adyr) only the settled plains are ISEZ;
# between the ranges everything below the Talas Alatau foothills is ISEZ
region_north = (GY > 42.88) | ((GX > 73.3) & (GY > 42.72)) | ((GX < 71.4) & (GY > AXLAT + 0.05))
tc = irad & box & ((region_north & settled) | (~region_north & ~atr_south & ~atr_karatau))
tc |= irad & sary_bulak & ~region_north
# the lore's own ISEZ places pull the line around them; its tribal villages push it back
SKIP_KINDS = {"park", "peak", "pass", "lake", "river-point", "other", "reservoir", "spring", "district", "zone-area", "checkpoint"}
pin_in = np.zeros(GX.shape, bool); pin_out = np.zeros(GX.shape, bool)
for p in P.values():
    if p.get("kind") in SKIP_KINDS or p["lat"] < 41.95:
        continue
    j, i = cell(p["lon"], p["lat"])
    if p["zone"] == "ISEZ":
        pin_in[j, i] = True
    elif p.get("confidence") != "placed" or p.get("kind") == "village":
        pin_out[j, i] = True
tc |= within_km(pin_in, 2.6) & irad & box
# the upper Talas valley above the mouth of the Otmek valley is tribal (State Route 1 is added back below)
kcrest = np.full(lons.shape, 43.0)
for i, x in enumerate(lons):
    js = np.where((lats >= 42.5) & (lats <= 43.0))[0]
    kcrest[i] = lats[js[np.argmax(E[js, i])]]
kcrest = ndimage.median_filter(kcrest, 11)
tc &= ~((GX > 72.975) & (GY < kcrest[None, :]))
# the high Kirghiz Range east of the Talas-Nurzhan road is tribal summer pasture, joined to the tribal mountains in the east
hi = irad & (E > 2300) & (GY > AXLAT) & (GY < 42.95) & (GX > 72.3)
hi = ndimage.binary_opening(hi, iterations=2)
lab, n = ndimage.label(hi | (irad & (GX > 72.975) & (GY < kcrest[None, :]) & (E > 2300)))
east_ids = set(np.unique(lab[(GX > 73.3) & (lab > 0)])) - {0}
hi = np.isin(lab, list(east_ids))
hi = ndimage.gaussian_filter(within_km(hi, 1.5).astype(float), 3) > 0.5
tc &= ~hi
lab, n = ndimage.label(tc)
keep = {lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("talas", "nurzhan", "kyzyl-adyr") if k in P} - {0}
# the Kara-Oi road is ISEZ up to UNMI Kara-Oi at its end; the Qara-Chik road is ISEZ through Qara-Chik to the valley mouth
for rid, upto in (("kara-oi-road", (72.47, 42.385)), ("qara-chik-road", (71.556, 42.522))):
    if rid in R:
        C_ = np.array(R[rid]["coords"]); k_ = int(np.argmin(np.hypot((C_[:, 0] - upto[0]) * KX, (C_[:, 1] - upto[1]) * KY)))
        tc |= within_km(raster_lines([C_[:k_ + 1].tolist()]), 1.2) & irad
lab, n = ndimage.label(tc)
# an ISEZ village's pocket cut off from the main body (a side valley) is joined to it by a corridor up the valley,
# rather than dropped (which would hand the lore's ISEZ places to the clans)
mainm = np.isin(lab, list(keep))
_, (mj, mi) = ndimage.distance_transform_edt(~mainm, return_indices=True)
for lb in set(np.unique(lab[pin_in])) - keep - {0}:
    comp = lab == lb; js, is_ = np.where(comp & pin_in)
    j0_, i0_ = js[0], is_[0]; j1_, i1_ = mj[j0_, i0_], mi[j0_, i0_]
    if math.hypot(j1_ - j0_, i1_ - i0_) * CELL_KM > 12: continue
    line_ = np.zeros(tc.shape, bool)
    for t in np.linspace(0, 1, 200): line_[int(round(j0_ + (j1_ - j0_) * t)), int(round(i0_ + (i1_ - i0_) * t))] = True
    tc |= within_km(line_, 1.0) & irad
lab, n = ndimage.label(tc)
keep = {lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("talas", "nurzhan", "kyzyl-adyr") if k in P} - {0}
tc = np.isin(lab, list(keep))

# the trunk roads and the lore's ISEZ routes stay inside the zone end to end, so the line crosses them only where
# they leave Irad or enter the mountains
protect = (core | (main_roads & within_km(tc, 6) & (E < 1100))) & irad
tc |= within_km(protect, 2.5) & irad & (box | within_km(lore_core, 3))
tc &= ~within_km(pin_out, 1.4) | within_km(protect, 3.0)
lab, n = ndimage.label(tc)
tc = np.isin(lab, list({lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("talas", "nurzhan") if k in P} - {0}))
tc = ndimage.binary_fill_holes(tc) & irad

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
# The Naryn below the dam: the river flats and the gorge floor only (the mountains either side of the gorge are tribal),
# widening over the flats at Iyık Janyl and Tash-Kömür.
reach_g = np.zeros(GX.shape, bool)
for c in naryn_river:
    for x, y in c:
        if 41.1 <= y <= 41.66 and x <= 72.7:
            j, i = cell(x, y); reach_g[j, i] = True
d_r, (rj_, ri_) = ndimage.distance_transform_edt(~reach_g, return_indices=True)
river_floor = E[rj_, ri_]
naryn = irad & (d_r * CELL_KM <= 7) & (E < river_floor + 180) & (GY < 41.66)
# the farm belt of the northern Fergana rim from Tash-Kömür east past Bazar-Korgon: the lowland below the foot of the hills,
# along the main road; Mailuu-Suu, Arslanbob and the upper valleys stay with the clans
rim_roads = raster_lines(ways(lambda w: w["k"] in ("road:trunk", "road:primary", "road:secondary")))
rim = irad & (GY < 41.3) & (GX >= 72.05) & (GX <= 73.1) & (E < 950) & within_km(rim_roads & (GY < 41.3), 10)
naryn |= rim
naryn = ndimage.gaussian_filter(naryn.astype(float), 2.0) > 0.5
naryn &= irad
lab, n = ndimage.label(naryn)
seed = [lab[cell(P[k]["lon"], P[k]["lat"])] for k in ("tash-komur", "iyik-janyl") if k in P]
naryn = np.isin(lab, [s for s in seed if s])
naryn = ndimage.binary_fill_holes(naryn)
# Iyık Janyl fills the river flats above Tash-Kömür; its quarters and the lore's other ISEZ places in the salient stay inside
for p in P.values():
    if p["zone"] == "ISEZ" and p["lat"] < 41.95 and p.get("kind") not in SKIP_KINDS:
        r_km = 6.0 if p["id"] == "iyik-janyl" else 1.5
        naryn |= irad & (np.hypot((GX - p["lon"]) * KX, (GY - p["lat"]) * KY) < r_km)
naryn = ndimage.binary_fill_holes(ndimage.binary_closing(naryn, iterations=2)) & irad
# the last power station of the cascade, where the river leaves the hills
uk = P.get("uch-kurgan-hps")
if uk:
    naryn |= irad & (np.hypot((GX - uk["lon"]) * KX, (GY - uk["lat"]) * KY) < 2.2)
# State Route 1: the valley floors along the road from the Talas valley over the Otmek and Ala-Bel, down the Chychkan
# valley and around the Toktogul basin to the Naryn gorge (a corridor up to the valley sides, narrow over the passes)
sr1 = R["fergana-mountain-transit-highway"]["coords"]
sr1_cells = raster_lines([sr1])
road_elev = np.where(sr1_cells, E, np.nan)
dist_sr1, (rj, ri) = ndimage.distance_transform_edt(~sr1_cells, return_indices=True)
floor_sr1 = E[rj, ri]
corridor = irad & ((dist_sr1 * CELL_KM <= 1.6) | ((dist_sr1 * CELL_KM <= 8) & (E < floor_sr1 + 250) & (floor_sr1 < 1900)))
lab, n = ndimage.label(corridor)
corridor = np.isin(lab, list(set(np.unique(lab[sr1_cells & corridor])) - {0}))
corridor = ndimage.binary_fill_holes(ndimage.binary_closing(corridor, iterations=4)) & irad
naryn |= corridor
# the Toktogul switchyard: a small ISEZ pocket below the dam, joined to the salient along the road
sw = P.get("toktogul-switchyard")
if sw:
    naryn |= irad & (np.hypot((GX - sw["lon"]) * KX, (GY - sw["lat"]) * KY) < 1.6)

isez = tc | naryn
isez = ndimage.binary_fill_holes(isez) & irad
atr_holes, n = ndimage.label(irad & ~isez)
small = [k + 1 for k, v in enumerate(ndimage.sum(np.ones_like(atr_holes), atr_holes, range(1, n + 1))) if v < 60]
isez |= np.isin(atr_holes, small)
cell_km2 = (STEP * 111.32 * np.cos(np.radians(GY))) * (STEP * 110.57)
area = lambda m: float(cell_km2[m].sum())
print("ISEZ %.0f km2 (Talas-Chu %.0f, Naryn %.0f), ATR %.0f" % (area(isez), area(tc), area(naryn), area(irad & ~isez)))

# ---------- districts ----------
south_of_axis = GY < AXLAT
# State Route 1 corridor from the Otmek tunnel south and the Toktogul basin down to the dam: Toktogul District;
# the Naryn below the dam (gorge, Iyık Janyl and Tash-Kömür flats, Fergana farm belt): Lower Naryn District
south_corr = naryn & ~tc & (GY < 42.28)
dam_ = P.get("toktogul-dam", {"lat": 41.677})
tokt = south_corr & (GY >= dam_["lat"] - 0.012)
ln = south_corr & ~tokt
dist = {"Toktogul": tokt, "Lower Naryn": ln, "Sary-Bulak": tc & (GY < 42.452) & ((sary_bulak & south_of_axis & (GY < AXLAT - 0.06)) | ((GY < 42.43) & (GX >= 71.95) & (GX <= 72.25)))}  # the industrial corridor and the limestone foothills south of Talas
rest = isez & ~south_corr & ~dist["Sary-Bulak"]
# Talas District is the Talas valley up to the crest of the Kyrgyz Range; west of it, Kara-Buura, the border following
# the low ground where the Kenkol and Kara-Buura fans meet; north of the range, Kara-Buura near Taraz and Chu further east,
# split at the stream that comes off the range at about 72.85 E
fan_lat = np.arange(42.3, 42.92, STEP)
fan_lon = []
for y in fan_lat:
    # low ground between the fans on the valley floor; the crest of the spur at the range's western end above it and
    # in the mountains below
    lo, hi = (71.6, 71.95) if y > 42.62 else (71.62, 71.78)
    i0, i1 = int(round((lo - LON0) / STEP)), int(round((hi - LON0) / STEP)); j = int(round((y - LAT0) / STEP))
    row = ndimage.uniform_filter1d(E[j, i0:i1 + 1], 5)
    fan_lon.append(lons[i0 + (int(np.argmin(row)) if 42.45 < y <= 42.62 else int(np.argmax(row)))])
fan_lon = ndimage.uniform_filter1d(np.array(fan_lon), 9)
fan_x = np.interp(GY, fan_lat, fan_lon)
north_of_range = (GY > kcrest[None, :]) & (GX > 71.6)
# the Chu/Kara-Buura border north of the range: the valley of the stream that comes off the range at about 72.85 E,
# then the stream itself across the plain
st_lat = np.arange(42.7, 43.25, STEP); st_lon = []
riv = [p for w in OSM if w["k"].startswith("water:river") and not w.get("n") for p in w["c"] if 72.75 < p[0] < 72.97 and 42.95 < p[1] < 43.12]
riv = np.array(riv) if riv else np.zeros((0, 2))
for y in st_lat:
    near_ = riv[np.abs(riv[:, 1] - y) < 0.01] if len(riv) else []
    if len(near_):
        st_lon.append(float(np.median(near_[:, 0])))
    elif y < 42.97:
        i0, i1 = int(round((72.75 - LON0) / STEP)), int(round((72.95 - LON0) / STEP)); j = int(round((y - LAT0) / STEP))
        st_lon.append(lons[i0 + int(np.argmin(ndimage.uniform_filter1d(E[j, i0:i1 + 1], 3)))])
    else:
        st_lon.append(st_lon[-1] if st_lon else 72.85)
stream_x = np.interp(GY, st_lat, ndimage.uniform_filter1d(np.array(st_lon), 7))
dist["Kara-Buura"] = rest & ((GX < fan_x) | (north_of_range & (GX < stream_x)))
dist["Chu"] = rest & ~dist["Kara-Buura"] & (north_of_range | (GX > 73.3))
dist["Talas"] = rest & ~dist["Kara-Buura"] & ~dist["Chu"]
# stray bits (filled holes, slivers) join the district they touch most; each district keeps one piece
for _ in range(2):
    for k in list(dist):
        lab_, n_ = ndimage.label(dist[k])
        if n_ <= 1: continue
        sizes = ndimage.sum(dist[k], lab_, range(1, n_ + 1)); main = 1 + int(np.argmax(sizes))
        for c in range(1, n_ + 1):
            if c == main: continue
            piece = lab_ == c; ring_ = ndimage.binary_dilation(piece, iterations=2) & ~piece
            best = max((o for o in dist if o != k), key=lambda o: (dist[o] & ring_).sum())
            if (dist[best] & ring_).sum():
                dist[k] &= ~piece; dist[best] |= piece
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
    # contour a slightly blurred mask, so diagonal edges come out straight instead of in 0.01-degree steps (as make_geo does)
    fig = plt.figure(); cs = plt.contour(GX, GY, ndimage.gaussian_filter(m.astype(float), 1.0), levels=[0.5]); segs = cs.allsegs[0]; plt.close(fig)
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
border_d = ndimage.distance_transform_edt(~border_cells) * CELL_KM
pieces = []
for r in rings_of(isez):
    # the line runs right up to the frontier where it meets it: a piece is carried on through the near-border band
    # until it is within ~0.4 km of the frontier; stretches running along the frontier itself are dropped
    def bd(q):
        j, i = cell(*q); return border_d[min(max(j, 0), GX.shape[0] - 1), min(max(i, 0), GX.shape[1] - 1)]
    near = [bd(q) <= 2.0 for q in r]
    cur, k = [], 0
    while k < len(r):
        if not near[k]:
            if not cur and k > 0:         # coming off the frontier: start where the outline leaves it
                b_ = k - 1
                while b_ > 0 and near[b_] and bd(r[b_]) > 0.4: b_ -= 1
                cur = [tuple(q) for q in r[b_:k]] if bd(r[b_]) <= 0.4 else []
            cur.append(tuple(r[k])); k += 1; continue
        if cur:                           # heading for the frontier: carry on until it is reached
            e_ = k
            while e_ < len(r) and near[e_] and bd(r[e_]) > 0.4: e_ += 1
            if e_ < len(r) and bd(r[e_]) <= 0.4: cur += [tuple(q) for q in r[k:e_ + 1]]
            if len(cur) > 3: pieces.append(cur)
            cur = []
        k += 1
    if len(cur) > 3: pieces.append(cur)


def sector(x, y):
    """the wiki's sectors: southern = the Naryn, the Fergana rim and the State Route 1 corridor through the Suusamyr;
    northern = the plains belt north of the Kyrgyz Range to Nurzhan; western = the frontier to the Kara-Buura valley
    and the Kenkol Pass; central = the Talas Alatau foothills south of Talas and the Kyrgyz Range tongue"""
    if y < 41.9 or (x > 72.95 and y < 42.35): return "southern"
    if y > 42.75: return "northern"
    if x < 71.9: return "western"
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
        eps = {"survey": 0.02, "canal": 0.012, "river": 0.003, "foothills": 0.005, "crest": 0.004}[fol]
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

# ---------- UN planning zones of the ATR ----------
# The ISEZ splits the tribal land into three separate blocks (north of the plains belt; the mountains west of the
# State Route 1 corridor and the Naryn gorge; the mountains east of them). Each zone lies inside one block, split
# along the main crests, so no zone reaches across ISEZ land.
atr = irad & ~isez
blab, nb = ndimage.label(atr)
bsz = ndimage.sum(atr, blab, range(1, nb + 1))
blocks = list(1 + np.argsort(-bsz)[:3])
def block_at(lon, lat):
    return blab[cell(lon, lat)]
B_N, B_W, B_E = block_at(71.0, 44.0), block_at(71.6, 42.3), block_at(73.1, 41.7)
def ridge(lo, hi, x0, x1, smooth=9):
    """latitude of the highest ground between lo and hi for each longitude (a crest line), smoothed"""
    out = np.full(lons.shape, np.nan)
    js = np.where((lats >= lo) & (lats <= hi))[0]
    for i, x in enumerate(lons):
        if x0 <= x <= x1:
            out[i] = lats[js[np.argmax(ndimage.uniform_filter1d(E[js, i], 3))]]
    ok = ~np.isnan(out)
    out[ok] = ndimage.median_filter(out[ok], smooth)
    out[~ok] = np.interp(lons[~ok], lons[ok], out[ok])
    return out[None, :]
fergana_crest = ridge(41.3, 41.75, 72.2, 74.0)      # Fergana Range / Babash-Ata: Naryn side vs Fergana side
suusamyr_crest = ridge(41.92, 42.2, 72.9, 74.0)     # Suusamyr range: Suusamyr and Kyrgyz Range vs the Toktogul basin
# Talas Alatau main crest (Talas side vs Chatkal side), through the passes the lore names
_tc = np.array([(69.9, 42.3), (70.6, 42.2), (71.22, 42.12), (71.45, 42.19), (71.6, 42.29), (71.74, 42.31), (71.9, 42.22),
                (72.05, 42.14), (72.26, 42.1), (72.5, 42.12), (72.72, 42.08), (73.0, 42.05)])
talas_crest = np.interp(lons, _tc[:, 0], _tc[:, 1])[None, :]
# Karatau: the range and its foothills (the upland above the Moiynkum and Chu–Sarysu lowland), west of the lower Talas
E_s = ndimage.gaussian_filter(E, 8)
karatau_axis = raster_lines([[(70.45, 42.75), (69.9, 43.25), (69.2, 43.7), (68.4, 44.15), (67.9, 44.4)]])
karatau_ring = (E_s >= 380) & within_km(karatau_axis, 80)
_l, _n = ndimage.label(karatau_ring & (blab == B_N))
karatau_ring = _l == _l[cell(69.5, 43.4)]
PZ = {
    "Northern Steppe": (blab == B_N) & ~karatau_ring,
    "Karatau": (blab == B_N) & karatau_ring,
    "Talas Alatau": (blab == B_W) & (GY >= talas_crest),
    "Chatkal Highlands": (blab == B_W) & (GY < talas_crest),
    "Kyrgyz Range–Suusamyr": (blab == B_E) & (GY >= suusamyr_crest),
    "Toktogul–Naryn": (blab == B_E) & (GY < suusamyr_crest) & (GY >= fergana_crest),
    "Fergana Rim": (blab == B_E) & (GY < fergana_crest),
}
# stray tribal crumbs (tiny blocks) join the zone next to them; detached bits of a zone join the neighbour they touch most
rest = atr & ~np.any(list(PZ.values()), axis=0)
for _ in range(3):
    names = list(PZ)
    for k in names:
        lab_, n_ = ndimage.label(PZ[k])
        if n_ <= 1: continue
        sizes = ndimage.sum(PZ[k], lab_, range(1, n_ + 1)); main = 1 + int(np.argmax(sizes))
        for c in range(1, n_ + 1):
            if c == main: continue
            piece = lab_ == c; ring_ = ndimage.binary_dilation(piece, iterations=2) & ~piece
            best = max((o for o in names if o != k), key=lambda o: (PZ[o] & ring_).sum())
            if (PZ[best] & ring_).sum():
                PZ[k] &= ~piece; PZ[best] |= piece
    lab_, n_ = ndimage.label(rest)
    for c in range(1, n_ + 1):
        piece = lab_ == c; ring_ = ndimage.binary_dilation(piece, iterations=2) & ~piece
        best = max(PZ, key=lambda o: (PZ[o] & ring_).sum())
        PZ[best] |= piece
    rest = atr & ~np.any(list(PZ.values()), axis=0)
for k, v in PZ.items():
    print("  zone %-22s %6.0f km2" % (k, area(v)))
json.dump({"type": "FeatureCollection", "features": [feat(trace(v, 0.003, 1), zone=k, area_km2=int(round(area(v), -2))) for k, v in PZ.items()]},
          open(os.path.join(out, "planning_zones.geojson"), "w"))
np.save(os.path.join(os.path.dirname(DEMF), "planning_zones.npy"), np.stack([PZ[k] for k in PZ]))
np.save(os.path.join(os.path.dirname(DEMF), "isez_mask.npy"), isez)
