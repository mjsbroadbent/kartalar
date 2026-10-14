"""Borrow real street plans for the Iradi cities.

Each Iradi city takes the streets, buildings and land use of a real donor city of about its size (from
tools/city-export.html), moved, turned (or mirrored) and scaled onto the Iradi site, then clipped to the ground the
city can actually occupy there (valley floor, below the foothills, off the airfield, clear of the next town).
Outputs, per city, under data/city/:
  <name>/overview.json   main roads, land use, canals and the real rivers (for zoom 10-13)
  <name>/t_<i>_<j>.json   everything, in 0.02-degree tiles (for zoom 13+)
  index.json             the cities, their tile lists and their footprints (the mask that hides the base map)
Lore routes that cross a city are re-laid along the borrowed main streets inside it (data/routes.json).
Run: python3 build/make_cities.py irad-dem.bin irad-osm-roads.json <dir with city-<donor>.json files>
"""
import json, math, os, struct, sys, heapq
import numpy as np
from scipy import ndimage
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, OSMF, CDIR = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(ROOT, "data/city")

# ---------- the cities ----------
CITIES = [
    {"name": "talas", "donor": "bishkek", "pivot_donor": (74.6037, 42.8765), "pivot": (72.240, 42.519), "rotate": 0, "mirror": False,
     "scale": 1.0, "donor_r_km": 13.5,
     # the Talas valley floor below the foothills, off Talas Air Base
     "ellipse": ((72.225, 42.515), 12.5, 8.5), "max_elev": 1420, "max_slope": 0.09,
     "exclude": [[(72.055, 42.517), (72.13, 42.517), (72.13, 42.548), (72.055, 42.548)]],
     "rivers": ["Талас"]},
    {"name": "nurzhan", "donor": "shymkent", "pivot_donor": (69.5875, 42.3155), "pivot": (73.760, 43.600), "rotate": 45, "mirror": False,
     "scale": 0.92, "donor_r_km": 11.5,
     "ellipse": ((73.77, 43.60), 11.5, 10.5), "max_elev": 900, "max_slope": 0.08,
     "exclude": [], "donor_exclude": [[(69.715, 42.265), (69.77, 42.265), (69.77, 42.325), (69.715, 42.325)]],   # a tile that failed to download
     "rivers": ["Чу"]},
    {"name": "iyik-janyl", "donor": "osh", "pivot_donor": (72.7856, 40.5274), "pivot": (72.222, 41.418), "rotate": 0, "mirror": False,
     # bend the plan along the river: the donor's river (upstream to downstream) is laid onto the Naryn, so the streets
     # along its banks follow the Naryn; the sacred hill on its left bank becomes Cathedral Hill on the Naryn's left (east) bank
     "warp": {"donor_river": "ww:river", "donor_river_min_pts": 100, "target_river": "Нарын", "target_flow": ((72.34, 41.486), (72.21, 41.336)),
              # mirrored across the river: the donor's dense old centre goes to the wide western flats (the Lower Town, where
              # most people live), its quieter far bank to the east bank below Cathedral Hill
              "mirror": True},
     "no_rail": True, "fill_houses": True, "trim_empty": True, "demote_major": True, "bridges": 4, "relay_only": [],
     "scale": 1.0, "donor_r_km": 15.0, "connect_real_roads": True, "tight_footprint": True,
     # archaeological sites kept open: the walled medieval town (~45 ha) and the citadel knoll
     # Shar-i-Kuhna, the walled medieval town (~45 ha) on its terrace; Diz-i Safid's knoll, kept as a park
     "keep_clear": [{"rect": (72.214, 41.394), "w": 0.78, "h": 0.58, "angle": 22, "k": "heritage"},
                    {"knoll": (72.218, 41.4225), "r": 0.45, "above": 45, "k": "park"}],
     "fill_gaps": True, "relay_minor_w": 10, "smooth_routes": ["fergana-mountain-transit-highway", "iyik-janyl-branch-road"],
     # the river flats of the Naryn: no higher than ~110 m above the river, north of Tash-Kömür; Cathedral Hill itself
     "ellipse": ((72.23, 41.415), 9.5, 9.0), "above_river": 170, "max_slope": 0.15, "min_lat": 41.372,
     "keep_round": [((72.2525, 41.3935), 0.9)],
     "exclude": [], "rivers": ["Нарын"]},
]
GRID = 0.0005           # ~45 m clipping grid
TILE = 0.02

b = open(DEMF, "rb").read()
d_lon0, d_lat0, d_st = struct.unpack("<3d", b[8:32]); d_nx, d_ny = struct.unpack("<2i", b[32:40])
DEM = ndimage.median_filter(np.frombuffer(b[64:], dtype="<i2").reshape(d_ny, d_nx).astype(float), 3)


def dem(lon, lat):
    return ndimage.map_coordinates(DEM, [(np.asarray(lat) - d_lat0) / d_st, (np.asarray(lon) - d_lon0) / d_st], order=1, mode="nearest")


OSM = json.load(open(OSMF))["ways"]


def kx(lat): return 111.32 * math.cos(math.radians(lat))
KY = 110.57


# ---------- classify donor features ----------
ROAD = {"motorway": "major", "trunk": "major", "primary": "major", "motorway_link": "major", "trunk_link": "major", "primary_link": "major",
        "secondary": "mid", "secondary_link": "mid", "tertiary": "mid", "tertiary_link": "mid",
        "residential": "minor", "unclassified": "minor", "living_street": "minor", "pedestrian": "minor", "road": "minor",
        "service": "service", "footway": "path", "path": "path", "track": "path", "steps": "path", "cycleway": "path"}
LAND = {"residential": "residential", "commercial": "commercial", "retail": "commercial", "industrial": "industrial", "railway": "industrial",
        "garages": "industrial", "cemetery": "cemetery", "grass": "grass", "recreation_ground": "park", "village_green": "grass",
        "farmland": "farm", "orchard": "farm", "allotments": "farm", "meadow": "grass", "forest": "wood", "military": "industrial",
        "brownfield": "industrial", "greenfield": "grass", "religious": "institution", "education": "institution", "plant_nursery": "farm"}
LEISURE = {"park": "park", "garden": "park", "pitch": "pitch", "stadium": "pitch", "playground": "park", "sports_centre": "pitch"}
AMENITY = {"school": "institution", "university": "institution", "college": "institution", "hospital": "institution",
           "marketplace": "commercial", "parking": "parking", "grave_yard": "cemetery"}


def classify(f):
    k = f["k"]
    if k == "building": return ("building", None)
    if k.startswith("hw:"):
        c = ROAD.get(k[3:]); return ("road", c) if c else None
    if k.startswith("landuse:"):
        c = LAND.get(k[8:]); return ("land", c) if c else None
    if k.startswith("leisure:"):
        c = LEISURE.get(k[8:]); return ("land", c) if c else None
    if k.startswith("amenity:"):
        c = AMENITY.get(k[8:]); return ("land", c) if c else None
    if k in ("ww:canal", "ww:ditch", "ww:drain", "ww:stream"): return ("canal", "canal" if k == "ww:canal" else "ditch")
    if k == "rail:rail" and not (f.get("t") or {}).get("service"): return ("rail", "rail")
    if k == "rail:rail": return ("rail", "siding")
    return None


def rings_of(f):
    return f["c"] if f.get("multi") else [f["c"]]


# ---------- per city ----------
def build(C):
    donor = json.load(open(os.path.join(CDIR, f"city-{C['donor']}.json")))
    pdx, pdy = C["pivot_donor"]; tx, ty = C["pivot"]
    kd, kt = kx(pdy), kx(ty)
    a = math.radians(C["rotate"]); ca, sa = math.cos(a), math.sin(a); sc = C["scale"]; mir = -1 if C["mirror"] else 1
    dex = [Path(np.array(p)) for p in C.get("donor_exclude", [])]

    W = C.get("warp")
    if W:
        def centerline(pts, flow_from, flow_dir):
            # order the river points from upstream, resample every 50 m, smooth over ~1.5 km
            P = np.asarray(pts, float); k_ = kx(P[0, 1])
            XY = np.column_stack([P[:, 0] * k_, P[:, 1] * KY])
            # order along the general flow (the reaches used here run without loops); bins of 100 m, averaged
            fdir = np.array(flow_dir, float); fdir /= np.hypot(*fdir)
            proj = XY @ fdir
            bins = np.floor((proj - proj.min()) / 0.1).astype(int)
            L = np.array([XY[bins == k].mean(0) for k in np.unique(bins)])
            order = None
            seg = np.hypot(*np.diff(L, axis=0).T); sarr = np.concatenate([[0], np.cumsum(seg)])
            ss = np.arange(0, sarr[-1], 0.05)
            R_ = np.column_stack([np.interp(ss, sarr, L[:, 0]), np.interp(ss, sarr, L[:, 1])])
            R_ = ndimage.gaussian_filter1d(R_, 35, axis=0, mode="nearest")
            tan = np.gradient(R_, axis=0); tan /= np.hypot(*tan.T)[:, None]
            return R_, tan, ss, k_
        dpts = [p for f in donor["features"] if f["k"] == W["donor_river"] and len(f["c"]) >= W["donor_river_min_pts"] for p in f["c"]]
        Dr, Dt, Ds, Dk = centerline(dpts, (72.858, 40.434), (-0.75, 0.66))
        tpts = [p for w in OSM if w["k"] == "water:river" and (w.get("n") or "") == W["target_river"] for p in w["c"]
                if abs(p[0] - tx) < 0.25 and abs(p[1] - ty) < 0.25]
        (fx0, fy0), (fx1, fy1) = W["target_flow"]
        tpts = [p for p in tpts if fy1 - 0.05 <= p[1] <= fy0 + 0.05]
        Tr, Tt, Ts, Tk = centerline(tpts, W["target_flow"][0], ((fx1 - fx0) * kx(fy0), (fy1 - fy0) * KY))
        # curvature of the target river line: on the inside of a bend, anything farther from the river than the bend radius
        # would fold over itself, so it is dropped (and the gap filled later)
        dT = np.gradient(Tt, axis=0) / 0.05
        KAP = Tt[:, 0] * dT[:, 1] - Tt[:, 1] * dT[:, 0]
        # normals from nearby stretches cross too: use the sharpest bend within ~3 km on each side
        KAPMAX = ndimage.maximum_filter1d(KAP, 121, mode="nearest"); KAPMIN = ndimage.minimum_filter1d(KAP, 121, mode="nearest")
        dD = np.gradient(Dt, axis=0) / 0.05
        KAPD = Dt[:, 0] * dD[:, 1] - Dt[:, 1] * dD[:, 0]
        FOLD = [None]
        from scipy.spatial import cKDTree
        DT = cKDTree(Dr)
        def frame(Rr, Tn, S_, q):
            i = int(np.argmin(np.hypot(*(Rr - q).T))); off = q - Rr[i]
            return S_[i] + off @ Tn[i], Tn[i, 0] * off[1] - Tn[i, 1] * off[0]
        s0d, _ = frame(Dr, Dt, Ds, np.array([pdx * Dk, pdy * KY]))
        s0t, _ = frame(Tr, Tt, Ts, np.array([tx * Tk, ty * KY]))

        def tf(pts):
            P = np.asarray(pts, float)
            q = np.column_stack([P[:, 0] * Dk, P[:, 1] * KY])
            _, i = DT.query(q)
            off = q - Dr[i]; t_ = Dt[i]
            s_ = Ds[i] + np.einsum("ij,ij->i", off, t_) - s0d + s0t
            d_ = t_[:, 0] * off[:, 1] - t_[:, 1] * off[:, 0]          # left of the flow is positive
            fold_d = d_ * KAPD[i] > 0.45                               # inside a donor bend: collapses onto a ray
            if W.get("mirror"): d_ = -d_
            j = np.clip(np.searchsorted(Ts, s_), 0, len(Ts) - 1)
            base = Tr[j] + Tt[j] * (s_ - Ts[j])[:, None]
            nrm = np.column_stack([-Tt[j, 1], Tt[j, 0]])
            out = base + nrm * d_[:, None]
            FOLD[0] = (np.where(d_ > 0, d_ * KAPMAX[j], d_ * KAPMIN[j]) > 0.5) | fold_d
            return np.column_stack([out[:, 0] / Tk, out[:, 1] / KY])
    else:
      FOLD = [None]
      def tf(pts):
        P = np.asarray(pts, float)
        x = (P[:, 0] - pdx) * kd * mir; y = (P[:, 1] - pdy) * KY
        xr, yr = (x * ca - y * sa) * sc, (x * sa + y * ca) * sc
        FOLD[0] = np.zeros(len(P), bool)
        return np.column_stack([tx + xr / kt, ty + yr / KY])

    # allowed ground at the target
    (ex, ey), ea, eb = C["ellipse"]
    lons = np.arange(ex - ea / kt - 0.01, ex + ea / kt + 0.01, GRID); lats = np.arange(ey - eb / KY - 0.01, ey + eb / KY + 0.01, GRID)
    GX, GY = np.meshgrid(lons, lats)
    E = dem(GX.ravel(), GY.ravel()).reshape(GX.shape)
    gy_, gx_ = np.gradient(ndimage.gaussian_filter(E, 2), GRID * KY * 1000, GRID * kt * 1000)
    slope = np.hypot(gx_, gy_)
    ok = (((GX - ex) * kt / ea) ** 2 + ((GY - ey) * KY / eb) ** 2 <= 1) & (slope <= C["max_slope"])
    if "max_elev" in C: ok &= E <= C["max_elev"]
    riv_pts = np.array([p for w in OSM if w["k"] == "water:river" and (w.get("n") or "") in C["rivers"] for p in w["c"]
                        if lons[0] - 0.05 < p[0] < lons[-1] + 0.05 and lats[0] - 0.05 < p[1] < lats[-1] + 0.05])
    riv = np.zeros(GX.shape, bool)
    for w in OSM:
        if w["k"] == "water:river" and (w.get("n") or "") in C["rivers"]:
            c = w["c"]
            for (x1, y1), (x2, y2) in zip(c, c[1:]):
                n = int(max(abs(x2 - x1), abs(y2 - y1)) / (GRID / 2)) + 1
                for t in np.linspace(0, 1, n + 1):
                    i = int(round((x1 + (x2 - x1) * t - lons[0]) / GRID)); j = int(round((y1 + (y2 - y1) * t - lats[0]) / GRID))
                    if 0 <= j < GX.shape[0] and 0 <= i < GX.shape[1]: riv[j, i] = True
    dr, (rj, ri) = ndimage.distance_transform_edt(~riv, return_indices=True)
    if "above_river" in C:
        ok &= E <= E[rj, ri] + C["above_river"]
    if "min_lat" in C: ok &= GY >= C["min_lat"]
    for poly in C["exclude"]:
        ok &= ~Path(np.array(poly)).contains_points(np.column_stack([GX.ravel(), GY.ravel()])).reshape(GX.shape)
    for (cx, cy), r in C.get("keep_round", []):
        ok |= np.hypot((GX - cx) * kt, (GY - cy) * KY) <= r
    ok = ndimage.binary_opening(ok, iterations=2)
    ok = ndimage.binary_fill_holes(ndimage.binary_closing(ok, iterations=3))
    lab, n = ndimage.label(ok)
    j0, i0 = int(round((ty - lats[0]) / GRID)), int(round((tx - lons[0]) / GRID))
    sizes = ndimage.sum(ok, lab, range(1, n + 1))
    main = lab[j0, i0] or (1 + int(np.argmax(sizes)))
    ok = lab == main
    near_river = dr * GRID * KY * 1000 < 60      # no buildings or side streets in the river
    CLEAR = []        # (kind, ring lon/lat array, raster mask)
    for kc in C.get("keep_clear", []):
        if "rect" in kc:
            cx, cy = kc["rect"]; a_ = math.radians(kc["angle"]); w2, h2 = kc["w"] / 2, kc["h"] / 2
            ring = np.array([(cx + (x * math.cos(a_) - y * math.sin(a_)) / kt, cy + (x * math.sin(a_) + y * math.cos(a_)) / KY)
                             for x, y in ((-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2), (-w2, -h2))])
            m_ = Path(ring).contains_points(np.column_stack([GX.ravel(), GY.ravel()])).reshape(GX.shape)
        else:
            cx, cy = kc["knoll"]; near_ = np.hypot((GX - cx) * kt, (GY - cy) * KY) < kc["r"]
            base_ = np.percentile(E[near_], 5)
            m_ = near_ & (ndimage.gaussian_filter(E, 1.5) > base_ + kc["above"])
            lab_, n_ = ndimage.label(m_); m_ = lab_ == lab_[int(round((cy - lats[0]) / GRID)), int(round((cx - lons[0]) / GRID))]
            m_ = ndimage.binary_closing(m_, iterations=2)
            import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
            fig_ = plt.figure(); cs_ = plt.contour(GX, GY, ndimage.gaussian_filter(m_.astype(float), 1), levels=[0.5]); sg = cs_.allsegs[0]; plt.close(fig_)
            ring = max(sg, key=len)
        CLEAR.append((kc["k"], ring, m_))

    def cell_ok(x, y, arr=ok):
        i = np.round((np.asarray(x) - lons[0]) / GRID).astype(int); j = np.round((np.asarray(y) - lats[0]) / GRID).astype(int)
        inb = (i >= 0) & (i < GX.shape[1]) & (j >= 0) & (j < GX.shape[0])
        out = np.zeros(len(np.atleast_1d(x)), bool)
        out[inb] = arr[j[inb], i[inb]]
        return out

    feats = []
    rd = C["donor_r_km"]
    for f in donor["features"]:
        cl = classify(f)
        if not cl: continue
        kind, sub = cl
        if kind == "rail" and C.get("no_rail"): continue
        rr = rings_of(f)
        p0 = rr[0][0]
        if math.hypot((p0[0] - pdx) * kd, (p0[1] - pdy) * KY) > rd: continue
        if dex and any(pth.contains_point(p0) for pth in dex): continue
        if kind == "building":
            r = rr[0]
            if len(r) < 4: continue
            T = tf(r)
            if FOLD[0].any() or not cell_ok(T[:, 0], T[:, 1]).all(): continue
            if cell_ok(T[:, 0], T[:, 1], near_river).any(): continue
            lv = (f.get("t") or {}).get("building:levels")
            props = {"k": "building"}
            try:
                if lv and float(lv) >= 5: props["tall"] = 1
            except ValueError: pass
            feats.append(("building", props, [T]))
        elif kind == "land":
            parts = []
            for r in rr:
                if len(r) < 4: continue
                T = tf(r); okv = cell_ok(T[:, 0], T[:, 1]) & ~FOLD[0]
                if okv.mean() >= 0.75: parts.append(T)
            if parts: feats.append(("land", {"k": sub}, parts))
        else:   # lines: roads and canals, cut where they leave the allowed ground
            for r in rr:
                if len(r) < 2: continue
                # densify long segments so the clip follows the ground
                pts = [r[0]]
                for (x1, y1), (x2, y2) in zip(r, r[1:]):
                    L = math.hypot((x2 - x1) * kd, (y2 - y1) * KY); n = max(1, int(L / 0.06))
                    for t in range(1, n + 1): pts.append([x1 + (x2 - x1) * t / n, y1 + (y2 - y1) * t / n])
                T = tf(pts); okv = cell_ok(T[:, 0], T[:, 1]) & ~FOLD[0]
                if not (kind == "road" and sub in ("major", "mid")):
                    okv &= ~cell_ok(T[:, 0], T[:, 1], near_river)   # only the main streets bridge the river
                run = []
                for p, o in zip(T, okv):
                    if o: run.append(p)
                    else:
                        if len(run) >= 2: feats.append((kind, {"k": sub}, [np.array(run)]))
                        run = []
                if len(run) >= 2: feats.append((kind, {"k": sub}, [np.array(run)]))
    if C.get("demote_major"):
        # the donor's arterials are not the Iradi highways here: draw them as ordinary town streets
        feats = [(k, ({"k": "mid"} if k == "road" and p_["k"] == "major" else p_), parts) for k, p_, parts in feats]
    if C.get("bridges"):
        # only a few streets bridge the river: pick the longest crossing streets, at least 1.2 km apart; cut the rest at the bank
        bank, _ = ndimage.label(~riv)
        def bank_at(x, y):
            i = int(round((x - lons[0]) / GRID)); j = int(round((y - lats[0]) / GRID))
            return bank[j, i] if 0 <= j < bank.shape[0] and 0 <= i < bank.shape[1] else 0
        def crossings(T):
            """runs of points near the river where the street really goes to the other bank: [(start, end)]"""
            inr = cell_ok(T[:, 0], T[:, 1], near_river); out = []; m = 0
            while m < len(T):
                if not inr[m]: m += 1; continue
                e = m
                while e < len(T) and inr[e]: e += 1
                if m > 0 and e < len(T):
                    b0, b1 = bank_at(*T[m - 1]), bank_at(*T[e])
                    if b0 and b1 and b0 != b1: out.append((m, e))
                m = e
            return out
        cross = []
        for n_, (k, p_, parts) in enumerate(feats):
            if k != "road" or p_["k"] not in ("mid", "major"): continue
            T = parts[0]
            L = float(np.hypot(np.diff(T[:, 0]) * kt, np.diff(T[:, 1]) * KY).sum())
            for m, e in crossings(T): cross.append((L, n_, T[(m + e - 1) // 2]))
        cross.sort(key=lambda c_: -c_[0])
        sites = []
        for L, n_, q in cross:
            if len(sites) >= C["bridges"]: break
            if all(math.hypot((q[0] - s_[0]) * kt, (q[1] - s_[1]) * KY) > 1.2 for s_ in sites): sites.append(q)
        new = []
        for k, p_, parts in feats:
            if k == "road" and p_["k"] in ("mid", "major"):
                T = parts[0]; cr = crossings(T)
                if cr:
                    cut = np.zeros(len(T), bool)
                    for m, e in cr:
                        mid_ = T[(m + e - 1) // 2]
                        if min((math.hypot((mid_[0] - s_[0]) * kt, (mid_[1] - s_[1]) * KY) for s_ in sites), default=9) > 0.15: cut[m:e] = True
                    run = []
                    for pt, c_ in zip(T, cut):
                        if not c_: run.append(pt)
                        else:
                            if len(run) >= 2: new.append((k, p_, [np.array(run)]))
                            run = []
                    if len(run) >= 2: new.append((k, p_, [np.array(run)]))
                    continue
            new.append((k, p_, parts))
        feats = new
        print(f"  {C['name']}: {len(sites)} bridges kept of {len(cross)} crossings")

    if C.get("fill_gaps"):
        # open ground inside the town that the donor left empty (its parks and hills) gets ordinary blocks: a street grid
        # aligned with the streets around it, joined to them, then houses along it like the rest
        road_m = np.zeros(GX.shape, bool); segs = []
        for k, p_, parts in feats:
            if k == "road" and p_["k"] in ("mid", "major", "minor"):
                T = parts[0]
                i = np.round((T[:, 0] - lons[0]) / GRID).astype(int); j = np.round((T[:, 1] - lats[0]) / GRID).astype(int)
                m = (i >= 0) & (i < GX.shape[1]) & (j >= 0) & (j < GX.shape[0]); road_m[j[m], i[m]] = True
                for a_, b_ in zip(T, T[1:]): segs.append(((a_ + b_) / 2, b_ - a_))
        clear_m = np.zeros(GX.shape, bool)
        for _, _, m_ in CLEAR: clear_m |= ndimage.binary_dilation(m_, iterations=1)
        dist_r = ndimage.distance_transform_edt(~road_m) * GRID * KY
        town = ndimage.binary_fill_holes(ndimage.binary_closing(ndimage.binary_dilation(road_m, iterations=6), iterations=8))
        gap = town & ok & (dist_r > 0.11) & ~clear_m & ~near_river
        lab, n = ndimage.label(gap)
        sizes = ndimage.sum(gap, lab, range(1, n + 1))
        mids = np.array([m_ for m_, _ in segs]); dirs = np.array([d_ for _, d_ in segs])
        from scipy.spatial import cKDTree
        mt = cKDTree(np.column_stack([mids[:, 0] * kt, mids[:, 1] * KY]))
        made = 0
        for c in range(1, n + 1):
            if sizes[c - 1] < 60: continue            # under ~0.12 km2
            comp = lab == c
            grow = ndimage.binary_dilation(comp, iterations=3) & ok & ~clear_m      # reach the surrounding streets
            jj, ii = np.where(comp); cx, cy = lons[ii].mean(), lats[jj].mean()
            near = mt.query_ball_point([cx * kt, cy * KY], 0.6)
            v = dirs[near] * [kt, KY]; L = np.hypot(*v.T) + 1e-9; ang = np.arctan2(v[:, 1], v[:, 0])
            th = 0.5 * math.atan2((L * np.sin(2 * ang)).sum(), (L * np.cos(2 * ang)).sum())
            u = np.array([math.cos(th), math.sin(th)]); w = np.array([-u[1], u[0]])
            gj_, gi_ = np.where(grow)
            P = np.column_stack([(lons[gi_] - cx) * kt, (lats[gj_] - cy) * KY])
            a0, a1 = (P @ u).min() - 0.1, (P @ u).max() + 0.1; b0, b1 = (P @ w).min() - 0.1, (P @ w).max() + 0.1
            def add_line(o, along, frm, to, step=0.02):
                ts = np.arange(frm, to, step); pts = o[None, :] + ts[:, None] * along[None, :]
                X = cx + pts[:, 0] / kt; Y = cy + pts[:, 1] / KY
                okp = cell_ok(X, Y, grow); run = []
                out = 0
                for x, y, o_ in zip(X, Y, okp):
                    if o_: run.append((x, y))
                    else:
                        if len(run) >= 4: feats.append(("road", {"k": "minor"}, [np.array(run)])); out += 1
                        run = []
                if len(run) >= 4: feats.append(("road", {"k": "minor"}, [np.array(run)])); out += 1
                return out
            for b in np.arange(b0, b1, 0.11): made += add_line(b * w, u, a0, a1)        # streets every ~110 m
            for a in np.arange(a0, a1, 0.24): made += add_line(a * u, w, b0, b1)        # cross streets every ~240 m
        print(f"  {C['name']}: {made} streets laid out in empty ground")

    if C.get("fill_houses"):
        # the donor's buildings are only partly mapped: line its side streets with courtyard houses where none are mapped
        H = 0.0001   # ~10 m
        hx0, hy0 = lons[0], lats[0]; hnx = int((lons[-1] - lons[0]) / H) + 2; hny = int((lats[-1] - lats[0]) / H) + 2
        occ = np.zeros((hny, hnx), bool)
        def mark(T, r=1):
            i = np.round((T[:, 0] - hx0) / H).astype(int); j = np.round((T[:, 1] - hy0) / H).astype(int)
            m = (i >= r) & (i < hnx - r) & (j >= r) & (j < hny - r)
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1): occ[j[m] + dj, i[m] + di] = True
        for kind, props, parts in feats:
            if kind == "building": mark(parts[0], 1)
            elif kind == "road":
                T = parts[0]
                dense = [T[0]]
                for a_, b_ in zip(T, T[1:]):
                    n_ = max(1, int(math.hypot((b_[0] - a_[0]) * kt, (b_[1] - a_[1]) * KY) / 0.008))
                    for t_ in range(1, n_ + 1): dense.append(a_ + (b_ - a_) * t_ / n_)
                mark(np.array(dense), 0 if props["k"] in ("minor", "service", "path") else 1)
        rng = np.random.default_rng(7)
        added = 0
        for kind, props, parts in list(feats):
            if kind != "road" or props["k"] != "minor": continue
            T = parts[0]
            for a_, b_ in zip(T, T[1:]):
                dx, dy = (b_[0] - a_[0]) * kt * 1000, (b_[1] - a_[1]) * KY * 1000; L = math.hypot(dx, dy)
                if L < 15: continue
                ux, uy = dx / L, dy / L; nxv, nyv = -uy, ux
                pos = 6.0
                while pos < L - 6:
                    w_, dpt = rng.uniform(9, 14), rng.uniform(10, 16)
                    for side in (1, -1):
                        cxm = pos * ux + side * (8 + dpt / 2) * nxv; cym = pos * uy + side * (8 + dpt / 2) * nyv
                        corners = [(-w_ / 2, -dpt / 2), (w_ / 2, -dpt / 2), (w_ / 2, dpt / 2), (-w_ / 2, dpt / 2)]
                        ring = [(a_[0] + (cxm + cx_ * ux + cy_ * nxv * side) / 1000 / kt, a_[1] + (cym + cx_ * uy + cy_ * nyv * side) / 1000 / KY) for cx_, cy_ in corners]
                        R_ = np.array(ring + [ring[0]])
                        i = np.round((R_[:, 0] - hx0) / H).astype(int); j = np.round((R_[:, 1] - hy0) / H).astype(int)
                        if (i < 1).any() or (j < 1).any() or (i >= hnx - 1).any() or (j >= hny - 1).any(): continue
                        if occ[j, i].any() or not cell_ok(R_[:, 0], R_[:, 1]).all() or cell_ok(R_[:, 0], R_[:, 1], near_river).any(): continue
                        if rng.random() < 0.12: continue        # gardens and empty plots
                        feats.append(("building", {"k": "building"}, [R_])); mark(R_, 1); added += 1
                    pos += w_ + rng.uniform(4, 9)
        print(f"  {C['name']}: {added} houses added along side streets")

    for kk, ring, m_ in CLEAR:
        P_ = Path(ring); new = []
        for k, p_, parts in feats:
            T = parts[0]; inn = P_.contains_points(T[:, :2])
            if not inn.any(): new.append((k, p_, parts)); continue
            if k in ("road", "canal", "rail"):
                if k == "canal": new.append((k, p_, parts)); continue
                run = []
                for pt, i_ in zip(T, inn):
                    if not i_: run.append(pt)
                    else:
                        if len(run) >= 2: new.append((k, p_, [np.array(run)]))
                        run = []
                if len(run) >= 2: new.append((k, p_, [np.array(run)]))
            elif k == "land" and inn.mean() < 0.3:
                new.append((k, p_, parts))
        feats = new + [("land", {"k": kk}, [np.asarray(ring)])]

    if C.get("trim_empty"):
        # streets that run out across empty ground (the donor's suburbs fell outside the site): cut them back to the houses
        bpts = np.vstack([parts[0][:, :2] for k, _, parts in feats if k == "building"])
        from scipy.spatial import cKDTree
        bt = cKDTree(np.column_stack([bpts[:, 0] * kt, bpts[:, 1] * KY]))
        new = []
        for k, p_, parts in feats:
            if k != "road":
                new.append((k, p_, parts)); continue
            T = parts[0]
            d_, _ = bt.query(np.column_stack([T[:, 0] * kt, T[:, 1] * KY]))
            keep = d_ < 0.18
            run = []
            for pt, kp in zip(T, keep):
                if kp: run.append(pt)
                else:
                    if len(run) >= 2: new.append((k, p_, [np.array(run)]))
                    run = []
            if len(run) >= 2: new.append((k, p_, [np.array(run)]))
        feats = new

    # footprint: built-up ground (buildings and streets), smoothed, inside the allowed ground
    fp = np.zeros(GX.shape, bool)
    for kind, props, parts in feats:
        if kind in ("building", "road") and props.get("k") not in ("path",):  # (railways do not make a town)
            for T in parts:
                i = np.round((T[:, 0] - lons[0]) / GRID).astype(int); j = np.round((T[:, 1] - lats[0]) / GRID).astype(int)
                m = (i >= 0) & (i < GX.shape[1]) & (j >= 0) & (j < GX.shape[0]); fp[j[m], i[m]] = True
    if C.get("tight_footprint"):
        fp = ndimage.binary_closing(ndimage.binary_dilation(fp, iterations=2), iterations=4)
        fp = ndimage.binary_fill_holes(fp) & ndimage.binary_dilation(ok, iterations=2)
        lab, n = ndimage.label(fp)
        sizes = ndimage.sum(fp, lab, range(1, n + 1))
        fp = lab == (1 + int(np.argmax(sizes)))            # one town: outlying scraps are dropped with their streets
        fp = ndimage.binary_fill_holes(fp)
        inside = lambda T: fp[np.clip(np.round((T[:, 1] - lats[0]) / GRID).astype(int), 0, fp.shape[0] - 1),
                              np.clip(np.round((T[:, 0] - lons[0]) / GRID).astype(int), 0, fp.shape[1] - 1)]
        new = []
        for k, p_, parts in feats:
            T = parts[0]
            if k in ("road", "canal", "rail"):
                m = inside(T); run = []
                for pt, kp in zip(T, m):
                    if kp: run.append(pt)
                    else:
                        if len(run) >= 2: new.append((k, p_, [np.array(run)]))
                        run = []
                if len(run) >= 2: new.append((k, p_, [np.array(run)]))
            elif inside(T).mean() > 0.5:
                new.append((k, p_, parts))
        feats = new
        # stray street fragments (cut off by the river or the edge) that join nothing are removed
        roads = [(n_, f) for n_, f in enumerate(feats) if f[0] == "road"]
        key = lambda q: (round(float(q[0]), 4), round(float(q[1]), 4))
        par = {}
        def find(a):
            while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
            return a
        node_of = {}
        for n_, (k, p_, parts) in roads:
            T = parts[0]
            for q in T: node_of.setdefault(key(q), []).append(n_)
            a = find(("r", n_))
            for q in T: par[find(("p",) + key(q))] = a
        comp_len = {}
        for n_, (k, p_, parts) in roads:
            T = parts[0]; L = float(np.hypot(np.diff(T[:, 0]) * kt, np.diff(T[:, 1]) * KY).sum())
            r_ = find(("r", n_)); comp_len[r_] = comp_len.get(r_, 0) + L
        drop = {n_ for n_, f in roads if comp_len[find(("r", n_))] < 0.6}
        feats = [f for n_, f in enumerate(feats) if n_ not in drop]
    else:
        fp = ndimage.binary_closing(ndimage.binary_dilation(fp, iterations=3), iterations=6)
        fp = ndimage.binary_fill_holes(fp) & ndimage.binary_dilation(ok, iterations=3)
        lab, n = ndimage.label(fp)
        sizes = ndimage.sum(fp, lab, range(1, n + 1))
        fp = np.isin(lab, 1 + np.where(sizes >= 40)[0])
        fp = ndimage.binary_fill_holes(fp)
    if C.get("connect_real_roads"):
        # real roads that run up to the town edge carry on into it until they meet its streets (instead of stopping at the mask)
        from scipy.spatial import cKDTree
        sp = np.vstack([parts[0] for k, p_, parts in feats if k == "road" and p_["k"] in ("mid", "major", "minor")])
        st_ = cKDTree(np.column_stack([sp[:, 0] * kt, sp[:, 1] * KY]))
        infp = lambda x, y: fp[min(max(int(round((y - lats[0]) / GRID)), 0), fp.shape[0] - 1), min(max(int(round((x - lons[0]) / GRID)), 0), fp.shape[1] - 1)]
        added = 0
        for w in OSM:
            if w["k"] not in ("road:trunk", "road:primary", "road:secondary", "road:tertiary"): continue
            c = w["c"]
            if not any(lons[0] < x < lons[-1] and lats[0] < y < lats[-1] for x, y in c): continue
            dense = [c[0]]
            for (x1, y1), (x2, y2) in zip(c, c[1:]):
                n_ = max(1, int(math.hypot((x2 - x1) * kt, (y2 - y1) * KY) / 0.03))
                for t_ in range(1, n_ + 1): dense.append([x1 + (x2 - x1) * t_ / n_, y1 + (y2 - y1) * t_ / n_])
            flags = [infp(x, y) for x, y in dense]
            for direction in (1, -1):
                seq = list(range(len(dense)))[::direction]
                for a_, b_ in zip(seq, seq[1:]):
                    if not flags[a_] and flags[b_]:        # enters the town here
                        run = [dense[a_]]; m = b_
                        idxs = seq[seq.index(b_):]
                        for m in idxs:
                            run.append(dense[m])
                            d_, _ = st_.query([dense[m][0] * kt, dense[m][1] * KY])
                            if d_ < 0.04 or not flags[m]: break
                        if len(run) >= 2:
                            feats.append(("road", {"k": "mid"}, [np.array(run)])); added += 1
        print(f"  {C['name']}: {added} real roads joined to the town streets")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig = plt.figure(); cs = plt.contour(GX, GY, ndimage.gaussian_filter(fp.astype(float), 1.2), levels=[0.5]); segs = cs.allsegs[0]; plt.close(fig)
    rings = [s for s in segs if len(s) > 8]
    rings.sort(key=lambda s: -abs(np.sum(s[:-1, 0] * s[1:, 1] - s[1:, 0] * s[:-1, 1])))
    polys = []
    for s in rings:
        r = [[round(float(x), 5), round(float(y), 5)] for x, y in s]
        if r[0] != r[-1]: r.append(r[0])
        host = next((P for P in polys if Path(np.array(P[0])).contains_point(r[0])), None)
        if host is not None: host.append(r)
        else: polys.append([r])
    footprint = {"type": "MultiPolygon", "coordinates": polys}
    fpath = [[Path(np.array(r)) for r in P] for P in polys]
    in_fp = lambda x, y: any(P[0].contains_point((x, y)) and not any(h.contains_point((x, y)) for h in P[1:]) for P in fpath)
    # the real river inside the city (the base map is hidden there)
    rivers = []
    for w in OSM:
        if w["k"] == "water:river" and (w.get("n") or "") in C["rivers"]:
            run = []
            for p in w["c"]:
                if in_fp(*p) or (run and in_fp(*run[-1])): run.append(p)
                else:
                    if len(run) >= 2: rivers.append(run)
                    run = []
            if len(run) >= 2: rivers.append(run)
    if C.get("smooth_routes"):
        # lore highways that keep their own course through the town: smoothed inside it, and nothing built on them
        routes_all = json.load(open(os.path.join(ROOT, "data/routes.json")))
        for r in routes_all:
            if r["id"] not in C["smooth_routes"]: continue
            c = np.array(r["coords"]); inn = np.array([in_fp(x, y) for x, y in c])
            if not inn.any(): continue
            i0_, i1_ = int(np.argmax(inn)), len(inn) - 1 - int(np.argmax(inn[::-1]))
            mid_ = c[max(i0_ - 1, 0): i1_ + 2]
            sm = thin_line(mid_, 40)
            for _ in range(3):
                sm = np.vstack([sm[:1]] + [np.array([0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]) for a, b in zip(sm, sm[1:])] + [sm[-1:]])
            r["coords"] = [[round(x, 5), round(y, 5)] for x, y in np.vstack([c[:max(i0_ - 1, 0)], sm, c[i1_ + 2:]])]
            dense = []
            for a, b in zip(sm, sm[1:]):
                n_ = max(1, int(math.hypot((b[0] - a[0]) * kt, (b[1] - a[1]) * KY) / 0.01))
                for t_ in range(n_): dense.append(a + (b - a) * t_ / n_)
            from scipy.spatial import cKDTree
            rt = cKDTree(np.array([(x * kt, y * KY) for x, y in dense]))
            before = len(feats)
            feats = [f for f in feats if not (f[0] == "building" and rt.query(np.column_stack([f[2][0][:, 0] * kt, f[2][0][:, 1] * KY]))[0].min() < 0.022)]
            print(f"  {C['name']}: {r['id']} smoothed through the town, {before - len(feats)} buildings cleared from its line")
        json.dump(routes_all, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
    return feats, footprint, rivers, (lons, lats, ok)


def gj(kind, props, parts):
    if kind == "building" or kind == "land":
        rings = [[[round(float(x), 5), round(float(y), 5)] for x, y in T] for T in parts]
        rings = [r if r[0] == r[-1] else r + [r[0]] for r in rings]
        geom = {"type": "Polygon", "coordinates": [rings[0]]} if len(rings) == 1 else {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
    else:
        geom = {"type": "LineString", "coordinates": [[round(float(x), 5), round(float(y), 5)] for x, y in parts[0]]}
    p = dict(props); p["t"] = kind
    return {"type": "Feature", "properties": p, "geometry": geom}


def thin_line(c, eps_m=4):
    """drop near-collinear points (RDP in metres) so the densified clip points don't bloat the files"""
    if len(c) < 3: return c
    P = np.asarray(c); a, b_ = P[0], P[-1]; k = kx(P[0, 1])
    v = (b_ - a) * [k * 1000, KY * 1000]; rel = (P - a) * [k * 1000, KY * 1000]; n_ = math.hypot(*v)
    d = np.abs(v[0] * rel[:, 1] - v[1] * rel[:, 0]) / n_ if n_ else np.hypot(*rel.T)
    i = int(np.argmax(d))
    if d[i] > eps_m: return np.vstack([thin_line(P[: i + 1], eps_m)[:-1], thin_line(P[i:], eps_m)])
    return np.vstack([a, b_])


# ---------- re-lay the lore routes inside each city along its borrowed main streets ----------
def relay_routes(cities_out):
    routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
    for name, feats, footprint, relay_only, minor_w in cities_out:
        fpath = [[Path(np.array(r)) for r in P] for P in footprint["coordinates"]]
        in_fp = lambda x, y: any(P[0].contains_point((x, y)) and not any(h.contains_point((x, y)) for h in P[1:]) for P in fpath)
        from scipy.spatial import cKDTree

        def graph(want):
            idx, coords, adj = {}, [], {}
            for kind, props, parts in feats:
                if (kind, props["k"]) not in want: continue
                T = parts[0]; w = want[(kind, props["k"])]; prev = None
                for x, y in T:
                    key = (round(float(x), 4), round(float(y), 4))
                    if key not in idx: idx[key] = len(coords); coords.append(key); adj[idx[key]] = []
                    cur = idx[key]
                    if prev is not None and prev != cur:
                        L = math.hypot((coords[prev][0] - key[0]) * kx(key[1]), (coords[prev][1] - key[1]) * KY) * w
                        adj[prev].append((cur, L)); adj[cur].append((prev, L))
                    prev = cur
            if not coords: return None
            # snap only to the main connected network (clipping leaves stray bits)
            comp = [-1] * len(coords); best = (0, -1); cid = 0
            for s0 in range(len(coords)):
                if comp[s0] >= 0: continue
                stack = [s0]; comp[s0] = cid; size = 0
                while stack:
                    u = stack.pop(); size += 1
                    for v, _ in adj[u]:
                        if comp[v] < 0: comp[v] = cid; stack.append(v)
                if size > best[0]: best = (size, cid)
                cid += 1
            keep = [i for i in range(len(coords)) if comp[i] == best[1]]
            C = np.array([coords[i] for i in keep])
            class Tree:
                def __init__(s_): s_.t = cKDTree(np.column_stack([C[:, 0] * kx(C[0, 1]), C[:, 1] * KY]))
                def query(s_, q): d, i = s_.t.query(q); return d, keep[i]
            return coords, adj, Tree(), kx(C[0, 1])

        G_road = graph({("road", "major"): 1.0, ("road", "mid"): 1.3, ("road", "minor"): minor_w})
        G_rail = graph({("rail", "rail"): 1.0, ("rail", "siding"): 1.6})

        def path(G, a_pt, b_pt):
            coords, adj, tree, k_ = G
            da, a = tree.query([a_pt[0] * k_, a_pt[1] * KY]); db, b_ = tree.query([b_pt[0] * k_, b_pt[1] * KY])
            lim = 3.0 if G is G_rail else 1.5
            if da > lim or db > lim or a == b_: return None
            dist = {a: 0.0}; prev = {}; pq = [(0.0, a)]
            while pq:
                d, u = heapq.heappop(pq)
                if u == b_: break
                if d > dist.get(u, 1e18): continue
                for v, w in adj[u]:
                    nd = d + w
                    if nd < dist.get(v, 1e18): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
            if b_ not in dist: return None
            out = [b_]
            while out[-1] != a: out.append(prev[out[-1]])
            return [list(coords[i]) for i in reversed(out)]

        def densify(c, step=0.1):
            out = [c[0]]
            for (x1, y1), (x2, y2) in zip(c, c[1:]):
                L = math.hypot((x2 - x1) * kx(y1), (y2 - y1) * KY); n = max(1, int(L / step))
                for t in range(1, n + 1): out.append([x1 + (x2 - x1) * t / n, y1 + (y2 - y1) * t / n])
            return out

        for r in routes:
            if r["kind"] not in ("highway", "road", "railway"): continue
            if relay_only is not None and r["id"] not in relay_only: continue
            G = G_rail if r["kind"] == "railway" else G_road
            if G is None: continue
            c = densify(r["coords"]); inside = [in_fp(*p) for p in c]
            if not any(inside): continue
            out, i, did = [], 0, False
            while i < len(c):
                if not inside[i]: out.append(c[i]); i += 1; continue
                j = i
                while j < len(c) and inside[j]: j += 1
                pth = path(G, c[i], c[j - 1])
                if pth and len(pth) >= 2:
                    out += pth; did = True
                else:
                    out += c[i:j]
                i = j
            r["coords"] = [[round(x, 5), round(y, 5)] for x, y in thin_line(np.array(out), 3)]
            if did:
                r.setdefault("in_city", [])
                if name not in r["in_city"]: r["in_city"].append(name)
    json.dump(routes, open(os.path.join(ROOT, "data/routes.json"), "w"), ensure_ascii=False, indent=1)
    # stations follow their line: the terminus to the end of the re-laid branch, junction stations onto the nearest track
    R = {r["id"]: r for r in routes}
    F = json.load(open(os.path.join(ROOT, "data/features.json")))
    SNAP = {"talas-railway-station": ("irad-temir-jolu-talas-branch", "end"), "nurzhan-station": ("irad-temir-jolu-chu-line", "near"),
            "nurzhan-rail-freight-depot": ("irad-temir-jolu-north-line", "near")}
    for f in F:
        if f["id"] in SNAP and SNAP[f["id"]][0] in R:
            c = R[SNAP[f["id"]][0]]["coords"]
            q = c[-1] if SNAP[f["id"]][1] == "end" else min(c, key=lambda p: (p[0] - f["lon"]) ** 2 + (p[1] - f["lat"]) ** 2)
            print(f"  {f['id']}: {f['lat']},{f['lon']} -> {q[1]},{q[0]}")
            f["lon"], f["lat"] = q
    json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    index = {"tile": TILE, "cities": []}
    outs = []
    for C in CITIES:
        feats, footprint, rivers, _ = build(C)
        d = os.path.join(OUT, C["name"]); os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d): os.remove(os.path.join(d, fn))
        tiles = {}
        overview = []
        for kind, props, parts in feats:
            if kind in ("road", "canal", "rail"): parts = [thin_line(parts[0])]
            f = gj(kind, props, parts)
            x, y = parts[0][0]
            key = (int(math.floor(x / TILE)), int(math.floor(y / TILE)))
            if (kind == "road" and props["k"] in ("major", "mid")) or (kind == "canal" and props["k"] == "canal") or kind in ("land", "rail"):
                overview.append(f)          # drawn from the overview at every zoom
            else:
                tiles.setdefault(key, []).append(f)
        for r in rivers:
            overview.append({"type": "Feature", "properties": {"t": "river"}, "geometry": {"type": "LineString", "coordinates": r}})
        tl = []
        for (i, j), fs in tiles.items():
            fn = f"t_{i}_{j}.json"
            json.dump({"type": "FeatureCollection", "features": fs}, open(os.path.join(d, fn), "w"), separators=(",", ":"))
            tl.append([i, j])
        json.dump({"type": "FeatureCollection", "features": overview}, open(os.path.join(d, "overview.json"), "w"), separators=(",", ":"))
        xs = [p[0] for P in footprint["coordinates"] for p in P[0]]; ys = [p[1] for P in footprint["coordinates"] for p in P[0]]
        index["cities"].append({"name": C["name"], "donor": C["donor"], "bbox": [min(xs), min(ys), max(xs), max(ys)], "tiles": sorted(tl), "footprint": footprint})
        nb = sum(1 for k, _, _ in feats if k == "building")
        size = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
        area = 0.0
        for P in footprint["coordinates"]:
            for h, r in enumerate(P):
                x = np.array([q[0] for q in r]) * kx(C["pivot"][1]); y = np.array([q[1] for q in r]) * KY
                a_ = 0.5 * abs(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1])); area += a_ if h == 0 else -a_
        print(f"{C['name']:11} from {C['donor']:9} {len(feats):6} features, {nb:6} buildings, {len(tl):3} tiles, {size/1e6:5.1f} MB, built-up {area:5.0f} km2")
        outs.append((C["name"], feats, footprint, C.get("relay_only"), C.get("relay_minor_w", 3.5)))
    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
    relay_routes(outs)
