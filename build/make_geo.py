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
# only the hills: the densely settled piedmont plain (Chust-Kasansay-Navkent, the Kara-Suu/Khanabad oases of Andijan)
# stays in Uzbekistan, with the valley's towns ("rural and foothill districts only"); with FINE_DEM the Namangan rim is
# cut at ~950 m, the foot of the Chatkal and Kurama foothills, and the Andijan oases are left out altogether
uz_rim = A["UZ-NG"] & (GY >= 41.13)
_fd = os.environ.get("FINE_DEM")
if _fd and os.path.exists(_fd):
    import struct
    from scipy import ndimage
    _b = open(_fd, "rb").read(); _L0, _A0, _ST = struct.unpack("<3d", _b[8:32]); _NX, _NY = struct.unpack("<2i", _b[32:40])
    _D = ndimage.gaussian_filter(np.frombuffer(_b[64:], dtype="<i2").reshape(_NY, _NX).astype(np.float32), 6)
    E = ndimage.map_coordinates(_D, [(GY - _A0) / _ST, (GX - _L0) / _ST], order=1, mode="nearest")
    hills = ndimage.binary_opening(E >= 950, iterations=2)
    # ... and the Naryn where it leaves Irad: the Uch-Kurgan dam and powerhouse at the gorge mouth stay Iradi
    gorge_mouth = (np.hypot((GX - 72.10) * 84, (GY - 41.168) * 111) < 3.0)
    uz_rim = uz_rim & (hills | gorge_mouth)
else:
    uz_rim = uz_rim | (A["UZ-AN"] & (GX >= 72.78) & (GY >= 40.72))
# Jambyl: everything west of 75 E, minus the Korday corner by Bishkek
jambyl = A["KZ-ZHA"] & (GX <= 75.0) & ~((GX >= 74.55) & (GY <= 43.28))
# the western end of the Suusamyr valley, held by Talas Alatau clans
suusamyr = mask_poly([[(72.95, 42.32), (73.75, 42.30), (73.80, 41.95), (73.20, 41.90), (72.95, 42.05)]])
# Jalal-Abad city stays with Kyrgyzstan, like the big Fergana cities on the Uzbek side
import math as _m
_ring = [(72.998 + 0.075 * _m.cos(t), 40.928 + 0.052 * _m.sin(t)) for t in [k * _m.pi / 18 for k in range(36)]]
jalal_abad = mask_poly([_ring]) | mask_poly([[(73.03, 40.9), (73.12, 40.87), (73.2, 40.78), (73.08, 40.76), (72.99, 40.86)]])
# the Balkhash road notch: the oblast line dips west round a bend of the Almaty–Balkhash highway; Irad's border runs straight
# across it so the road does not leave and re-enter the country
balkhash_notch = mask_poly([[(73.74, 45.30), (74.11, 45.30), (74.11, 45.03), (73.80, 45.03)]])
irad = (A["KG-T"] | A["KG-J"] | jambyl | turkistan_part | uz_rim | suusamyr | balkhash_notch) & (GX >= 68.0) & ~jalal_abad

# west of Uzak the frontier runs north of the Kandiyon - Salaman road (the road and its villages are Uzbek), so the road
# does not weave across it (applied after the road rule below)
_blue = [(71.5288, 41.2754), (71.5542, 41.2854), (71.5847, 41.2862), (71.6051, 41.2958), (71.6255, 41.3112), (71.6560, 41.3246),
         (71.6814, 41.3304), (71.6967, 41.3285), (71.7171, 41.3258), (71.7629, 41.3258)]
kandiyon_strip = mask_poly([_blue + [(71.7629, 41.20), (71.5288, 41.20)]])
# the south-east corner below the Chu: the frontier runs along the foot of the hills north of Kökadyr and Muzbel to the
# motorway crossing at the eastern frontier (the Chu Gate), so the corner's hill villages are left outside
_se = [(74.6802, 43.2857), (74.7034, 43.2987), (74.7266, 43.3127), (74.7537, 43.3212), (74.7653, 43.3325), (74.7847, 43.3381),
       (74.8001, 43.3448), (74.8311, 43.3465), (74.8582, 43.3493), (74.8814, 43.3550), (74.9085, 43.3634), (74.9279, 43.3690),
       (74.9588, 43.3702), (74.9820, 43.3775), (74.9936, 43.3803)]
chu_corner = mask_poly([_se + [(75.05, 43.3803), (75.05, 43.20), (74.6802, 43.20)]])
# north of Jalal-Abad: the frontier runs up the small river from Dostuk past Suzak and Blagoveshchenka to the Kök-Kamar
# gorge, then round the east side of the valley back down to the old line, so the valley villages east of the river
# (Taygaraev, Leninskoe, Orto-Say, Jygach-Korgon, Oktyabrskoe, Safarovka, Bagysh) are Kyrgyz, with Kümüsh-Aziz, Munduz and Jiyde
_kg = [(72.8544, 40.8631), (72.8628, 40.8638), (72.8717, 40.8665), (72.8836, 40.8672), (72.897, 40.871), (72.906, 40.8762), (72.9134, 40.8874), (72.9209, 40.9032), (72.9253, 40.9144), (72.9313, 40.9211), (72.9387, 40.9301), (72.9581, 40.9526), (72.9789, 40.9706), (72.9938, 40.9841), (73.0087, 40.9998), (73.0206, 41.0133), (73.0281, 41.0246), (73.0311, 41.0403), (73.0385, 41.0504), (73.0445, 41.0549), (73.0564, 41.0565), (73.0683, 41.0628), (73.0802, 41.074), (73.0921, 41.088), (73.0981, 41.083), (73.11, 41.0684), (73.116, 41.065), (73.1279, 41.056), (73.1324, 41.047), (73.1309, 41.0358), (73.1234, 41.0257), (73.1145, 41.0156), (73.1085, 41.0099), (73.0981, 41.0054), (73.0832, 40.9976), (73.0698, 40.9875), (73.0594, 40.9751), (73.0549, 40.965), (73.0564, 40.9571), (73.0653, 40.9492), (73.0713, 40.9459), (73.0728, 40.938)]
kg_valley = mask_poly([_kg + [(73.0638, 40.8998), (73.0653, 40.8897), (72.9789, 40.8694), (72.97, 40.8559), (72.9134, 40.8245), (72.8777, 40.8222)]])
# below the Kyrgyz Range at Kichi-Korgon the frontier follows the Aspara river (OSM course, Granitogorsk to below Kenes)
_aspara = [(73.4555, 42.7051), (73.4556, 42.7065), (73.4568, 42.708), (73.4579, 42.7097), (73.4577, 42.7114), (73.4577, 42.7129), (73.4581, 42.7142), (73.4595, 42.7156), (73.4608, 42.7168), (73.4619, 42.7181), (73.4634, 42.7191), (73.4643, 42.721), (73.4643, 42.7224), (73.4646, 42.7239), (73.4657, 42.7254), (73.4661, 42.7271), (73.4665, 42.7286), (73.4664, 42.7302), (73.4671, 42.7317), (73.4685, 42.7332), (73.4702, 42.7347), (73.4712, 42.736), (73.4721, 42.7373), (73.4732, 42.7387), (73.4752, 42.7392), (73.4766, 42.7403), (73.4767, 42.7419), (73.4778, 42.7429), (73.4791, 42.744), (73.4795, 42.7455), (73.4811, 42.7464), (73.4826, 42.7472), (73.4845, 42.7483), (73.4862, 42.7494), (73.4876, 42.751), (73.4886, 42.7523), (73.49, 42.7538), (73.4914, 42.7548), (73.4923, 42.7562), (73.4937, 42.7578), (73.4947, 42.7594), (73.4967, 42.7616), (73.4983, 42.7626), (73.4994, 42.7643), (73.5006, 42.7658), (73.5014, 42.7678), (73.5015, 42.7693), (73.5018, 42.7713), (73.5016, 42.7728), (73.5014, 42.7744), (73.502, 42.7763), (73.5026, 42.7779), (73.5037, 42.7796), (73.5041, 42.781), (73.5044, 42.7824), (73.5044, 42.7843), (73.5046, 42.7857), (73.5046, 42.787), (73.5047, 42.7888), (73.5057, 42.79), (73.5065, 42.7913), (73.5071, 42.7929), (73.5073, 42.7944), (73.507, 42.7961), (73.5076, 42.7976), (73.508, 42.7995), (73.5078, 42.801), (73.5076, 42.8029), (73.5087, 42.8058), (73.5098, 42.8082), (73.5102, 42.8104), (73.5098, 42.8133), (73.5102, 42.8169), (73.5103, 42.8186), (73.5099, 42.8201), (73.5102, 42.8215), (73.5106, 42.8229), (73.5105, 42.8245), (73.5116, 42.8259), (73.5124, 42.8272), (73.5112, 42.8288), (73.5116, 42.8301), (73.5119, 42.8316), (73.5118, 42.833), (73.5116, 42.8344), (73.5112, 42.8359), (73.511, 42.8374), (73.5103, 42.8387), (73.5095, 42.8403), (73.5102, 42.8415), (73.51, 42.8429), (73.5103, 42.8445), (73.5095, 42.8461), (73.5098, 42.8475), (73.5112, 42.8519), (73.5108, 42.8536), (73.5098, 42.8548), (73.5088, 42.856), (73.5096, 42.8573), (73.5095, 42.8588), (73.5093, 42.8607), (73.5085, 42.8623), (73.5079, 42.8637), (73.5081, 42.8651), (73.5087, 42.8666), (73.5091, 42.8681), (73.5085, 42.8697), (73.5075, 42.8711), (73.5068, 42.8725), (73.5056, 42.8735), (73.5055, 42.8748), (73.5049, 42.8763), (73.5038, 42.8774), (73.5047, 42.8788), (73.5059, 42.88), (73.5037, 42.8812), (73.5056, 42.8814), (73.5028, 42.8815), (73.5055, 42.8816), (73.5026, 42.8817), (73.5039, 42.8828), (73.5045, 42.8842), (73.5051, 42.8855), (73.5036, 42.8865), (73.5029, 42.8879), (73.5011, 42.8884), (73.5002, 42.8897), (73.4991, 42.8908), (73.4978, 42.892), (73.4968, 42.8932), (73.4943, 42.894), (73.4939, 42.8953), (73.4942, 42.8969)]
aspara_w = mask_poly([_aspara + [(73.30, _aspara[-1][1]), (73.30, _aspara[0][1])]])
aspara_e = mask_poly([_aspara + [(73.65, _aspara[-1][1]), (73.65, _aspara[0][1])]])
# above Ak-Kolot the frontier keeps north of the road and river (the road no longer dips out and back)
ak_kolot = mask_poly([[(73.9771, 41.7545), (73.9776, 41.7517), (73.9814, 41.7479), (73.989, 41.7446), (74.0043, 41.7412), (74.031, 41.7412), (74.0539, 41.7403), (74.0666, 41.7384), (74.0768, 41.7361), (74.0844, 41.7327), (74.092, 41.727), (74.1002, 41.72), (74.0704, 41.7327), (74.0005, 41.7355), (73.9865, 41.7403)]])
# on the Kazakh frontier at the Sayramsu crossing the line bends east round the town rather than through it
sayramsu_bump = mask_poly([[(70.0225, 42.27), (70.0275, 42.2687), (70.0373, 42.2643), (70.0472, 42.2606), (70.0546, 42.2568), (70.0595, 42.253), (70.062, 42.248), (70.0608, 42.243), (70.0584, 42.2405), (70.0373, 42.2401), (70.0324, 42.2386), (70.0262, 42.2364), (70.025, 42.253)]])   # drawn a little wide: the smoothed outline rounds it off
# Uch-Kurgan: the frontier keeps south of the road from Sadaf-Jar, then follows the Naryn itself past Kyzyl-Jar up to the
# edge of Kum (Kyzyl-Jar on the right bank in Irad, Uchkurgan across the river; the one bridge is the Kyzyl-Jar crossing)
_uch = [(71.9986, 41.1786), (71.9992, 41.1774), (72.0038, 41.1756), (72.0078, 41.1732), (72.0084, 41.1707), (72.0084, 41.1459), (72.0098, 41.1434), (72.015, 41.141), (72.0256, 41.138), (72.0348, 41.1355), (72.044, 41.1337), (72.0533, 41.1301), (72.0599, 41.1271), (72.0615, 41.115), (72.0635, 41.1099), (72.0652, 41.1115), (72.0687, 41.1143), (72.07, 41.1155), (72.0714, 41.1171), (72.0743, 41.1211), (72.0755, 41.1225), (72.0778, 41.1239), (72.0796, 41.1246), (72.0816, 41.127), (72.0835, 41.1284), (72.0851, 41.1296), (72.0884, 41.1318), (72.0927, 41.1347), (72.0939, 41.1365), (72.0947, 41.1394), (72.095, 41.1409), (72.0971, 41.1443), (72.0992, 41.1464), (72.1018, 41.1482), (72.1052, 41.1514), (72.1065, 41.1525), (72.1082, 41.1535), (72.11, 41.1542), (72.1154, 41.1539), (72.1182, 41.1539), (72.1219, 41.1547), (72.1241, 41.1554), (72.1291, 41.1587), (72.1322, 41.1611), (72.134, 41.1622), (72.1358, 41.1627), (72.1376, 41.1626), (72.1409, 41.1613), (72.1432, 41.1607), (72.1454, 41.1601), (72.1482, 41.1597), (72.1504, 41.1597), (72.1535, 41.1599), (72.1556, 41.1602), (72.1638, 41.1641), (72.1657, 41.1656), (72.166, 41.1652), (72.1692, 41.1632), (72.1719, 41.1588), (72.1732, 41.1538), (72.1745, 41.1494)]
uch_n = mask_poly([_uch + [(72.1745, 41.2232), (71.9986, 41.2232)]])
uch_s = mask_poly([_uch + [(72.1745, 41.1043), (71.9986, 41.1043)]])

# ---------- ISEZ ----------
R = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "data/routes.json")))}
# where an Irad road or railway runs along the frontier, the frontier keeps to the far side of it (the oblast lines
# cross and recross the real roads): the land within ~1.5 km of the stretches of road inside Irad is Irad's
_inside = lambda x, y: irad[min(max(int(round((y - LAT0) / STEP)), 0), irad.shape[0] - 1), min(max(int(round((x - LON0) / STEP)), 0), irad.shape[1] - 1)]
hug = np.zeros(GX.shape, bool)
for r in R.values():
    if r.get("kind") not in ("highway", "road", "railway") or not r.get("coords"): continue
    C = [tuple(q) for q in r["coords"]]
    ins = [bool(_inside(x, y)) for x, y in C]
    # an excursion out of Irad that comes back in (the road weaving across the oblast line) counts as inside;
    # a road leaving Irad for good keeps its real exit
    k = 0
    while k < len(C):
        if ins[k]: k += 1; continue
        e = k
        while e < len(C) and not ins[e]: e += 1
        if k > 0 and e < len(C):
            L = sum(np.hypot((C[q + 1][0] - C[q][0]) * 82, (C[q + 1][1] - C[q][1]) * 111) for q in range(k - 1, e))
            if L < 25:
                for q in range(k, e): ins[q] = True
        k = e
    run = []
    for q, (x, y) in enumerate(C):
        if ins[q]: run.append((x, y))
        else:
            if len(run) > 1: hug |= near_line(run, 1.5)
            run = []
    if len(run) > 1: hug |= near_line(run, 1.5)
# real main roads along the frontier that the border should keep to the near side of (ROUTE_NET = make_network.py output)
ROAD_HUG_BOXES = [(73.45, 42.98, 74.0, 43.2)]      # the Kum-Jol stretch of the Bishkek road below the Kyrgyz Range
_net = os.environ.get("ROUTE_NET")
if _net and os.path.exists(_net):
    for w in json.load(open(_net))["ways"]:
        if w["k"] not in ("road:motorway", "road:trunk", "road:primary"): continue
        for x0_, y0_, x1_, y1_ in ROAD_HUG_BOXES:
            pts = [(x, y) for x, y in w["c"] if x0_ <= x <= x1_ and y0_ <= y <= y1_]
            if len(pts) > 1: hug |= near_line(pts, 1.5)
# real main roads that clip the frontier: a stretch of under ~2.5 km that dips into Irad and straight out again (or out and
# back in) is put wholly on the side the road runs on, so the road does not cross the frontier twice for nothing
clip_in = np.zeros(GX.shape, bool); clip_out = np.zeros(GX.shape, bool)
if _net and os.path.exists(_net):
    for w in json.load(open(_net))["ways"]:
        if w["k"] not in ("road:motorway", "road:trunk", "road:primary", "road:secondary", "road:tertiary"): continue
        C = w["c"]
        if len(C) < 3: continue
        xs = [q[0] for q in C]; ys = [q[1] for q in C]
        if max(xs) < LON0 or min(xs) > LON1 or max(ys) < LAT0 or min(ys) > LAT1: continue
        ins = [bool(_inside(x, y)) for x, y in C]
        k = 1
        while k < len(C):
            if ins[k] == ins[k - 1]: k += 1; continue
            e = k
            while e < len(C) and ins[e] == ins[k]: e += 1
            if e < len(C):           # a run k..e-1 bounded by the other side on both ends
                L = sum(np.hypot((C[q + 1][0] - C[q][0]) * 82, (C[q + 1][1] - C[q][1]) * 111) for q in range(k - 1, e))
                if L < 2.5:
                    seg = C[k - 1:e + 1]
                    if ins[k]: clip_out |= near_line(seg, 0.7)      # dips in: give the strip back
                    else: clip_in |= near_line(seg, 0.7)            # dips out: keep it
            k = e
print("road clips: %d cells kept in, %d given back" % (int((clip_in & ~irad).sum()), int((clip_out & irad).sum())))
added = hug & ~irad & (GX >= 68.0)
print("frontier kept off the roads: %.0f km2 added" % float(((STEP * 111.32 * np.cos(np.radians(GY))) * (STEP * 110.57))[added].sum()))
irad = ((irad | (clip_in & (GX >= 68.0))) & ~(clip_out & ~hug)) | added
irad = (irad | aspara_w | ak_kolot | uch_n) & ~uch_s & ~sayramsu_bump & ~kandiyon_strip & ~chu_corner & ~kg_valley & ~aspara_e
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


def trace(m, eps=0.004, min_km2=4, smooth=0):
    fig = plt.figure()
    f_ = m.astype(float)
    if smooth:      # contour a slightly blurred mask: diagonal edges come out straight instead of in 0.01-degree steps
        from scipy import ndimage
        f_ = ndimage.gaussian_filter(f_, smooth)
    cs = plt.contour(GX, GY, f_, levels=[0.5])
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


def snap_to_lines(geom, lines, tol_km=1.0):
    """frontier stretches that follow a river exactly: ring vertices within tol of one of these polylines move onto it,
    and the polyline's own vertices are put in between, so the border follows the river and not the 0.01-degree grid"""
    kx = 111.32 * np.cos(np.radians(41.5)); out = []
    def proj(L, p):
        best = None
        for i in range(len(L) - 1):
            a, b = np.array(L[i]), np.array(L[i + 1]); v = (b - a) * [kx, 110.57]; w = (np.array(p) - a) * [kx, 110.57]
            t = float(np.clip(np.dot(w, v) / (np.dot(v, v) or 1e-12), 0, 1)); d = float(np.hypot(*(w - t * v)))
            if best is None or d < best[0]: best = (d, i + t, a + t * (b - a))
        return best
    for poly in geom["coordinates"]:
        newp = []
        for ring in poly:
            nr = []; prev = None
            for p in ring:
                hit = None
                for li, L in enumerate(lines):
                    d, par, q = proj(L, p)
                    if d < tol_km and (hit is None or d < hit[0]): hit = (d, li, par, q)
                if hit:
                    _, li, par, q = hit
                    if prev and prev[0] == li:          # fill in the river's own bends between two snapped vertices
                        lo, hi = sorted((prev[1], par)); mids = [k for k in range(int(np.floor(lo)) + 1, int(np.ceil(hi))) if lo < k < hi]
                        if par < prev[1]: mids = mids[::-1]
                        nr += [[round(lines[li][k][0], 5), round(lines[li][k][1], 5)] for k in mids]
                    nr.append([round(float(q[0]), 5), round(float(q[1]), 5)]); prev = (li, par)
                else:
                    nr.append(p); prev = None
            newp.append(nr)
        out.append(newp)
    return {"type": "MultiPolygon", "coordinates": out}


# rivers the frontier follows exactly (OSM courses): the Naryn past Kyzyl-Jar, the Aspara at Kichi-Korgon
FRONTIER_RIVERS = [_uch[_uch.index(min(_uch, key=lambda q: abs(q[0] - 72.0635) + abs(q[1] - 41.1099))):
                        _uch.index(min(_uch, key=lambda q: abs(q[0] - 72.1638) + abs(q[1] - 41.1641))) + 1], _aspara]


def splice(geom, path, tol_km=0.6):
    """replace the stretch of the outline between the two ends of path (each within tol of the outline) by path itself,
    for small hand-drawn changes that the 0.01-degree grid cannot hold (taking the shorter way round the ring)"""
    kx = 111.32 * np.cos(np.radians(path[0][1]))
    for poly in geom["coordinates"]:
        for ri, ring in enumerate(poly):
            # put the two ends onto the outline as vertices of their own (projected onto the nearest edge)
            for end in (path[0], path[-1]):
                R = np.array(ring); A_, B_ = R[:-1], R[1:]; v = (B_ - A_) * [kx, 110.57]; w = (np.array(end) - A_) * [kx, 110.57]
                t = np.clip((v * w).sum(1) / np.maximum((v * v).sum(1), 1e-12), 0, 1); dd = np.hypot(*(w - t[:, None] * v).T); e_ = int(dd.argmin())
                if dd[e_] <= tol_km and 0 < t[e_] < 1:
                    q = A_[e_] + t[e_] * (B_[e_] - A_[e_]); ring.insert(e_ + 1, [round(float(q[0]), 5), round(float(q[1]), 5)])
            R = np.array(ring)
            d0 = np.hypot((R[:, 0] - path[0][0]) * kx, (R[:, 1] - path[0][1]) * 110.57); d1 = np.hypot((R[:, 0] - path[-1][0]) * kx, (R[:, 1] - path[-1][1]) * 110.57)
            i, j = int(d0[:-1].argmin()), int(d1[:-1].argmin())
            if d0[i] > tol_km or d1[j] > tol_km or i == j: continue
            n = len(ring) - 1; core = ring[:-1]
            fwd = (j - i) % n; bwd = (i - j) % n
            P = [[round(x, 5), round(y, 5)] for x, y in path]
            if fwd <= bwd:      # replace i..j going forward
                new = [core[(i + k) % n] for k in range(0)] + P + [core[(j + k) % n] for k in range(1, bwd)]
            else:               # replace going backward: the ring runs j..i, so put the path in reversed
                new = P[::-1] + [core[(i + k) % n] for k in range(1, fwd)]
            new.append(new[0]); poly[ri] = new
            return geom
    print("  splice: no fit for", path[0], path[-1])
    return geom


# hand-drawn stretches spliced into the traced frontier
SPLICES = [
    # Kyzyl-Jar: the frontier stays on the Naryn down past the bridge, then turns up to the Sadaf-Jar road's line
    [(72.0743, 41.1211), (72.0714, 41.1171), (72.07, 41.1155), (72.0687, 41.1143), (72.0652, 41.1115), (72.0635, 41.1099), (72.0615, 41.115), (72.0605, 41.1265)],
    # Tash-Akyr: the Jalal-Abad–Osh boundary kept north of the trunk road it clipped
    [(73.1375, 40.8502), (73.1445, 40.8503), (73.1495, 40.8525), (73.1535, 40.8543), (73.1585, 40.8553)],
    # Makmal: the frontier below the road's last bend, so the road crosses it once
    [(74.0790, 41.1580), (74.0815, 41.1585), (74.0850, 41.1600), (74.0880, 41.1612)],
]


def feat(geom, **props):
    return {"type": "Feature", "properties": props, "geometry": geom}


out = os.path.join(ROOT, "data")
_spliced = snap_to_lines(trace(irad, 0.003, smooth=1.0), FRONTIER_RIVERS, 0.9)
for _p in SPLICES: _spliced = splice(_spliced, _p)
json.dump({"type": "FeatureCollection", "features": [feat(_spliced, name="Irad", name_ir="Irad", name_ru="Ирад", area_km2=round(area(irad)))]},
          open(os.path.join(out, "irad.geojson"), "w"))
json.dump({"type": "FeatureCollection", "features": [
    feat(trace(isez, 0.003), zone="ISEZ", name="Irad Special Economic Zone", name_ir="Irad Atayın Ekonomikalık Zonası", name_ru="Особая экономическая зона Ирада", area_km2=round(area(isez))),
    feat(trace(irad & ~isez, 0.003), zone="ATR", name="Autonomous Tribal Regions", name_ir="Avtonomduu Uruu Aymaktarı", name_ru="Автономные племенные районы", area_km2=round(area(irad & ~isez)))]},
    open(os.path.join(out, "zones.geojson"), "w"))
json.dump({"type": "FeatureCollection", "features": [feat(trace(m, 0.003, 1), district=k, area_km2=round(area(m))) for k, m in dist.items()]},
          open(os.path.join(out, "districts.geojson"), "w"))
for f in ("irad", "zones", "districts"):
    print(f, os.path.getsize(os.path.join(out, f + ".geojson")) // 1024, "KB")
