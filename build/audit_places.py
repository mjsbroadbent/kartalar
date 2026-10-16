"""Check every city, town and village against the placement rules (docs/PLACEMENT.md), fix the ones that fail, and
lock the ones that pass.

  python3 build/audit_places.py <fine dem.bin> <extract dir> <network.json> [--fix] [--lock]

--fix   moves each failing place that is not locked or anchored to the best spot that passes: a free real settlement
        in its own jurisdiction (namesakes first), or, where the real map is empty, the best habitable ground; its
        landmarks move with it, and a stated height that disagrees with real ground takes the ground's height.
--lock  places that pass every rule get "locked": true. The build never moves a locked place; one that later fails a
        rule (because a border moved, say) is reported here, not moved.
Writes data/place_audit.md.
"""
import json, math, os, struct, sys, re, unicodedata
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMF, EXT, NETF = sys.argv[1:4]
FIX = "--fix" in sys.argv; LOCK = "--lock" in sys.argv
KY = 110.57; KX = 111.32 * math.cos(math.radians(42.5))
b = open(DEMF, "rb").read()
LON0, LAT0, ST = struct.unpack("<3d", b[8:32]); NX, NY = struct.unpack("<2i", b[32:40])
DEMS = ndimage.gaussian_filter(np.frombuffer(b[64:], dtype="<i2").reshape(NY, NX).astype(np.float32), 1.0)
def z_at(lon, lat): return float(ndimage.map_coordinates(DEMS, [[(lat - LAT0) / ST], [(lon - LON0) / ST]], order=1)[0])
def slope_at(lon, lat):
    h = 0.15     # km: the ground over ~300 m, the size of a village core
    zx = (z_at(lon + h / KX, lat) - z_at(lon - h / KX, lat)) / (2 * h * 1000)
    zy = (z_at(lon, lat + h / KY) - z_at(lon, lat - h / KY)) / (2 * h * 1000)
    return math.hypot(zx, zy)
xy = lambda lon, lat: (lon * KX, lat * KY)

# --- the rules (docs/PLACEMENT.md) ----------------------------------------------------------------------------
KINDS = {"capital", "city", "town", "village"}
ON_REAL = {"capital": 2.5, "city": 2.5, "town": 1.0, "village": 0.6}      # R1: km to the real settlement it takes over
REACH = {"capital": 0, "city": 0, "town": 12.0, "village": 8.0}           # R1: a free real settlement this near must be used
SPACING = {"capital": 4.0, "city": 3.0, "town": 2.0, "village": 1.2}      # R2: km to the next Iradi settlement (the larger's)
MAX_MOVE = {"anchor": 0, "real-place": 0, "stated": 3.0, "placed": 12.0}  # --fix: how far the lore lets a place move
NAMESAKE_KM = {"anchor": 0, "real-place": 25.0, "stated": 5.0, "placed": 25.0}   # a real namesake may be this far
SPARSE = {"Northern Steppe": 20.0, "Karatau": 15.0}                       # habitable ground is searched wider in the steppe
def max_move(p):
    if re.search(r"approximate", p.get("note", ""), re.I): return 12.0
    return MAX_MOVE.get(p["confidence"], 12.0)
REAL_KIND_OK = {                                                          # R3: what a place may sit on
    "capital": {"city"}, "city": {"city", "town"}, "town": {"town", "city", "village", "built-up"},
    "village": {"village", "hamlet", "town", "built-up"}}          # not a 'locality': a tract, a rail junction, a work camp
ELEV_TOL = 120            # R4: m between the stated height and the ground
MAX_SLOPE = 0.15          # R5: ground under the core of an invented place
WATER_KM = {  # a village named for its well (kuduk) has one
   "default": 1.5, "Northern Steppe": 5.0, "Karatau": 3.0}       # R6: invented places; steppe villages live on wells
ROAD_KM = 2.0             # R7: invented places, to a real road or track or an Irad route
LINE_KM = 0.8             # R8: off the Qara-Chik line and the frontier, unless a border or crossing village
SPECIAL = {"boz-korgon": "the government compound: placed by make_bozkorgon.py from the terrain",
           "iyik-janyl": "a city of the lore with no real namesake, on the Naryn flats as the lore places it"}
LABEL = re.compile(r"label point", re.I)                                  # a clan homeland's label, not a village
OWN_TRACK = re.compile(r"\btrack\b|trail|pack[- ]horse|migration route", re.I)   # the lore gives it its own way in
CAMP = re.compile(r"\bcamps?\b|yurt|seasonal|summer", re.I)            # summer camps: invented by nature, no road
# placed by hand, with the reason; 'exempt' lists rules the reason answers
MANUAL = {
    "toguz-bulak": ((72.7772, 42.5519), "on the Kök-Bel road just above the Toguz-Bulak crossing (the lore: the road leaves the ISEZ at the crossing below the village)", {"R8"}),
    "kumushtu": ((72.7159, 42.4594), "the real village nearest the Shelji silver-mining site (Kara-Oy), as the lore puts it beside Shelji", set()),
    "arsha-say": ((72.6550, 42.4672), "makes way for Kumushtu: a village on a side stream of the Talas below the Talas Alatau (Sasyk-Bulak)", set()),
}
# rules eased for a place, with the reason
RELAX = {
    "sary-bulak": ({"water": 3.0}, "the mining village in the Sary-Bulak gorge, where the railway spur and the road end at its works; the gorge stream is not on the map"),
    "kara-say": ({"slope": 0.22, "water": 3.0}, "a terrace village: it sits on the slope it farms; its stream is not on the map"),
    "kosh-bel": ({"slope": 0.20, "water": 3.0}, "a hamlet on a high migration route; its spring is not on the map"),
    "shaar-dobo": ({"move": 40.0}, "goes with the Shahr-i Buzurg site to where the Chu plain can water a village"),
    "ak-chiy": ({"move": 40.0}, "the Moiynkum margin is waterless for 30 km around the old guess"),
}
SPECIAL["kara-oi"] = "the research station and UNMI headquarters at the end of the Kara-Oi road, not a village"
RANK = {"anchor": 0, "real-place": 1, "stated": 2, "placed": 3}

CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяөүңіұқғһә", ["a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "i", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "h", "ts", "ch", "sh", "sh", "", "i", "", "e", "yu", "ya", "o", "u", "n", "i", "u", "k", "g", "h", "a"]))
def norm(s):
    s = "".join(CYR.get(c, c) for c in (s or "").lower())
    s = unicodedata.normalize("NFKD", s.replace("ı", "i")); s = "".join(c for c in s if not unicodedata.combining(c))
    for a, b_ in (("dzh", "j"), ("dj", "j"), ("zh", "j"), ("kh", "h"), ("yo", "o"), ("y", "i"), ("q", "k"), ("x", "h"), ("ş", "sh"), ("ç", "ch")):
        s = s.replace(a, b_)
    s = re.sub(r"[^a-z]", "", s); return re.sub(r"(.)\1+", r"\1", s)

# --- data -----------------------------------------------------------------------------------------------------
P = json.load(open(os.path.join(ROOT, "data/settlements.json")))
F = json.load(open(os.path.join(ROOT, "data/features.json")))
real = []; springs = []
for l in open(os.path.join(EXT, "places.ndjson")):
    f = json.loads(l); pr = f["properties"]; k = pr.get("place"); x, y = f["geometry"]["coordinates"]
    if k in ("city", "town", "village", "hamlet", "locality"):
        try: pop = int(float(pr.get("population") or 0))
        except ValueError: pop = 0
        nm = {norm(pr.get(q)) for q in ("name", "name_en", "name_ru", "name_ky", "name_kk", "name_uz") if pr.get(q)} - {""}
        real.append(dict(lon=x, lat=y, kind=k, name=pr.get("name_en") or pr.get("name") or "", pop=pop, names=nm))
    elif k == "spring": springs.append((x, y))
for l in open(os.path.join(EXT, "landuse.ndjson")):     # built-up land without a place node counts too
    f = json.loads(l)
    if f["properties"].get("class") != "residential": continue
    g = f["geometry"]
    for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
        c = np.array(poly[0])
        if len(c) >= 4 and (c[:, 0].max() - c[:, 0].min()) * KX * (c[:, 1].max() - c[:, 1].min()) * KY > 0.04:    # a block, not a house
            real.append(dict(lon=float(c[:, 0].mean()), lat=float(c[:, 1].mean()), kind="built-up", name="", pop=0, names=set()))
RT = cKDTree([xy(r["lon"], r["lat"]) for r in real])
def dense(c, step=0.1):
    out = []
    for a, b_ in zip(c, c[1:]):
        n = max(1, int(math.hypot((b_[0] - a[0]) * KX, (b_[1] - a[1]) * KY) / step))
        out += [xy(a[0] + (b_[0] - a[0]) * t / n, a[1] + (b_[1] - a[1]) * t / n) for t in range(n)]
    out.append(xy(*c[-1])); return out
wat = [xy(*s) for s in springs]
for l in open(os.path.join(EXT, "waterway.ndjson")):
    f = json.loads(l); g = f["geometry"]
    if f["properties"].get("class") not in ("river", "stream", "canal", "ditch", "drain"): continue
    for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
        if 67.5 < c[0][0] < 76 and 40.5 < c[0][1] < 46: wat += dense(c, 0.2)
for l in open(os.path.join(EXT, "water.ndjson")):
    g = json.loads(l)["geometry"]
    for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
        if 67.5 < poly[0][0][0] < 76 and 40.5 < poly[0][0][1] < 46: wat += dense(poly[0], 0.3)
WT = cKDTree(wat)
roads = []
for w in json.load(open(NETF))["ways"]:
    if w["k"].startswith("road:"): roads += dense(w["c"], 0.1)
for r in json.load(open(os.path.join(ROOT, "data/routes.json"))):
    if r.get("kind") in ("road", "highway") and r.get("coords"): roads += dense(r["coords"], 0.1)
RDT = cKDTree(roads)
lines = []
for g in [f["geometry"] for f in json.load(open(os.path.join(ROOT, "data/qarachik.geojson")))["features"]]:
    for c in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]): lines += dense(c, 0.1)
for f in json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"]:
    g = f["geometry"]
    for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
        for ring in poly: lines += dense(ring, 0.1)
LT = cKDTree(lines)
def polys(fn, key):
    out = []
    for f in json.load(open(os.path.join(ROOT, fn)))["features"]:
        g = f["geometry"]
        for p in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            out.append((f["properties"][key], [Path(np.array(r)) for r in p]))
    return out
def where(lon, lat, PL):
    for k, rings in PL:
        if rings[0].contains_point((lon, lat)) and not any(r.contains_point((lon, lat)) for r in rings[1:]): return k
Z = polys("data/zones.geojson", "zone"); D = polys("data/districts.geojson", "district"); PZ = polys("data/planning_zones.geojson", "zone")
DISTRICT_CITIES = {"Talas", "Nurzhan", "Iyık Janyl"}
CITY_FOOT = []          # the borrowed street plans of the cities: no village or town inside one
for c in json.load(open(os.path.join(ROOT, "data/city/index.json")))["cities"]:
    g = c["footprint"]
    for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
        CITY_FOOT.append((c["name"], Path(np.array(poly[0]))))
def in_city(lon, lat):
    return next((n for n, pa in CITY_FOOT if pa.contains_point((lon, lat))), None)
places = [p for p in P if p["kind"] in KINDS]
BORDER_WORDS = re.compile(r"border|frontier|crossing|checkpoint|on the line", re.I)

def jurisdiction_ok(p, lon, lat):
    z = where(lon, lat, Z)
    if z != p["zone"]: return False, f"R8 said {p['zone']}, map {z}"
    if z == "ISEZ" and p["district"] not in DISTRICT_CITIES:
        d = where(lon, lat, D)
        if d != p["district"]: return False, f"R8 said district {p['district']}, map {d}"
    if z == "ATR":
        pz = where(lon, lat, PZ)
        if pz and p["district"] != pz: return False, f"R8 said planning zone {p['district']}, map {pz}"
    return True, ""

def check(p, lon, lat, others):
    """the rules a place at (lon, lat) breaks, with notes. others: [(id, lon, lat, kind)] of the other places"""
    q = xy(lon, lat); fails = []; notes = []; invented = False; k_real = None
    exempt = MANUAL.get(p["id"], (None, None, set()))[2]
    if p["id"] in SPECIAL: notes.append(SPECIAL[p["id"]])
    elif LABEL.search(p.get("note", "")): notes.append("a clan label point, not a village")
    elif p["id"] in MANUAL and (lon, lat) == MANUAL[p["id"]][0]: notes.append("by hand: " + MANUAL[p["id"]][1])
    else:
        d, k = RT.query(q)
        if d <= ON_REAL[p["kind"]]:
            k_real = k; r = real[k]
            notes.append(f"on {r['name'] or '(unnamed)'} ({r['kind']}{', ' + format(r['pop'], ',') if r['pop'] else ''})")
            if r["kind"] not in REAL_KIND_OK[p["kind"]]: fails.append(f"R3 a {p['kind']} on a real {r['kind']}")
        else:
            invented = True
            free = [i for i in RT.query_ball_point(q, REACH[p["kind"]]) if real[i]["kind"] in REAL_KIND_OK[p["kind"]]
                    and not in_city(real[i]["lon"], real[i]["lat"])
                    and jurisdiction_ok(p, real[i]["lon"], real[i]["lat"])[0]
                    and not (p.get("elev") and abs(z_at(real[i]["lon"], real[i]["lat"]) - p["elev"]) > 300)
                    and LT.query(xy(real[i]["lon"], real[i]["lat"]))[0] >= LINE_KM and not any(
                        math.hypot((o[1] - real[i]["lon"]) * KX, (o[2] - real[i]["lat"]) * KY) < ON_REAL[o[3]] for o in others)]
            if free and not CAMP.search(p.get("note", "")): fails.append(f"R1 a free real settlement {math.hypot(*(np.array(xy(real[free[0]]['lon'], real[free[0]]['lat'])) - q)):.1f} km away")
            elif p["kind"] in ("capital", "city", "town"): fails.append(f"R1 a {p['kind']} not on a real settlement")
            else: notes.append(f"invented (nearest real {d:.1f} km)")
    for o in others:
        dd = math.hypot((o[1] - lon) * KX, (o[2] - lat) * KY)
        if dd < max(SPACING[p["kind"]], SPACING[o[3]]) and p["id"] not in SPECIAL and o[0] not in SPECIAL:
            fails.append(f"R2 {dd:.1f} km from {o[0]}")
    if p["kind"] in ("town", "village") and p["id"] not in SPECIAL:
        c = in_city(lon, lat)
        if c: fails.append(f"R2 inside the street plan of {c}")
    zg = z_at(lon, lat)
    if p.get("elev") and abs(p["elev"] - zg) > ELEV_TOL: fails.append(f"R4 stated {p['elev']} m, ground {zg:.0f} m")
    sl = slope_at(lon, lat); dw = WT.query(q)[0]; dr = RDT.query(q)[0]
    pz = where(lon, lat, PZ)
    if invented and not LABEL.search(p.get("note", "")):
        rx = RELAX.get(p["id"], ({}, ""))[0]
        if sl > rx.get("slope", MAX_SLOPE): fails.append(f"R5 on a {100 * sl:.0f}% slope")
        if dw > rx.get("water", WATER_KM.get(pz or "", WATER_KM["default"])) and not re.search(r"kuduk|quduq|құдық", p["id"] + p.get("note", ""), re.I): fails.append(f"R6 {dw:.1f} km from water")
        if dr > ROAD_KM * (3 if pz == "Northern Steppe" else 2.5 if p["zone"] == "ATR" else 1) and not CAMP.search(p.get("note", "")) and not OWN_TRACK.search(p.get("note", "")): fails.append(f"R7 {dr:.1f} km from a road")
    dl = LT.query(q)[0]
    if dl < LINE_KM and not BORDER_WORDS.search(p.get("note", "")) and "R8" not in exempt: fails.append(f"R8 {dl:.2f} km from the line or frontier")
    ok_j, why = jurisdiction_ok(p, lon, lat)
    if not ok_j: fails.append(why)
    return fails, notes, dict(z=zg, slope=sl, water=dw, road=dr, invented=invented, real=k_real)

def others_of(p, pos):
    return [(o["id"], pos[o["id"]][0], pos[o["id"]][1], o["kind"]) for o in places if o["id"] != p["id"]]

pos = {p["id"]: (p["lon"], p["lat"]) for p in places}
moves = []
if FIX:
    # who gives way: the locked and anchored stay; then the better-attested and bigger keep their spot
    order = sorted(places, key=lambda p: (not p.get("locked"), RANK.get(p["confidence"], 9), -(p.get("pop") or 0)))
    moved_ids = set()
    for p in places:
        if p["id"] in MANUAL and not p.get("locked"):
            q = MANUAL[p["id"]][0]; moves.append((p, pos[p["id"]], q, "by hand")); pos[p["id"]] = q; moved_ids.add(p["id"])
    for rnd in range(3):
        for p in order:
            if p.get("locked") or p["id"] in SPECIAL or p["id"] in moved_ids or LABEL.search(p.get("note", "")): continue
            fails, notes, m = check(p, *pos[p["id"]], others_of(p, pos))
            if p["confidence"] == "anchor":
                if fails and all(f.startswith("R4") for f in fails):
                    moves.append((p, pos[p["id"]], pos[p["id"]], f"height {p['elev']} -> {int(round(m['z'], -1))}")); p["elev"] = int(round(m["z"], -1))
                continue
            # a stated height wrong for a place on real ground is the lore's slip: the ground wins
            if [f for f in fails if not f.startswith("R4")] == [] and fails and not m["invented"]:
                moves.append((p, pos[p["id"]], pos[p["id"]], "height " + str(p["elev"]) + " -> " + str(int(round(m["z"], -1))))); p["elev"] = int(round(m["z"], -1)); continue
            if not fails: continue
            lon0, lat0 = pos[p["id"]]; h0 = p.get("elev")
            oth = others_of(p, pos)
            nm = {norm(p.get("name")), norm(p.get("name_en")), norm(p.get("name_ru"))} - {""}
            best = None
            # 1. a free real settlement: namesake within 25 km, otherwise the nearest that passes, within 12 km
            for i in ([] if CAMP.search(p.get("note", "")) else RT.query_ball_point(xy(lon0, lat0), 25.0)):
                r = real[i]; dd = math.hypot((r["lon"] - lon0) * KX, (r["lat"] - lat0) * KY)
                namesake = bool(r["names"] & nm) and dd <= NAMESAKE_KM.get(p["confidence"], 25)
                if not namesake and dd > max_move(p): continue
                if r["kind"] not in REAL_KIND_OK[p["kind"]]: continue
                if h0 and abs(z_at(r["lon"], r["lat"]) - h0) > 300 and not namesake: continue
                f2, _, m2 = check(p, r["lon"], r["lat"], oth)
                f2 = [f for f in f2 if not f.startswith("R4")]
                if f2: continue
                cost = dd + (0 if namesake else 3) + (1.5 if r["kind"] == "built-up" else 0) + (0.5 if r["kind"] == "hamlet" else 0) \
                    + (abs(m2["z"] - h0) / 150 if h0 else 0)
                if best is None or cost < best[0]: best = (cost, r["lon"], r["lat"], ("namesake " if namesake else "") + (r["name"] or r["kind"]))
            # 2. no real settlement to take over: the best habitable ground within 8 km (villages only)
            if best is None and p["kind"] == "village":
                pz0 = where(lon0, lat0, PZ); far = h0 and abs(z_at(lon0, lat0) - h0) > ELEV_TOL
                R_ = SPARSE.get(pz0, 12.0 if far else 8.0)
                if not far and not SPARSE.get(pz0): R_ = min(R_, max_move(p))
                cap = RELAX.get(p["id"], ({}, ""))[0].get("move", 40 if pz0 in SPARSE else 20)
                widen = far or pz0 in SPARSE or "move" in RELAX.get(p["id"], ({}, ""))[0]
                while best is None and R_ <= cap:
                    stp = 0.4 if R_ <= 8 else 0.8 if R_ <= 20 else 1.6
                    for dx in np.arange(-R_, R_ + 0.01, stp):
                        for dy in np.arange(-R_, R_ + 0.01, stp):
                            dd = math.hypot(dx, dy)
                            if dd > R_: continue
                            lon, lat = lon0 + dx / KX, lat0 + dy / KY
                            if h0 and abs(z_at(lon, lat) - h0) > 250: continue
                            if RT.query(xy(lon, lat))[0] <= ON_REAL["village"]: continue
                            f2, _, m2 = check(p, lon, lat, oth)
                            f2 = [f for f in f2 if not f.startswith("R4")]
                            if f2: continue
                            cost = dd + 8 * m2["slope"] + m2["water"] + 0.5 * m2["road"] + (abs(m2["z"] - h0) / 100 if h0 else 0)
                            if best is None or cost < best[0]: best = (cost, round(lon, 5), round(lat, 5), "habitable ground")
                    if best is None and widen and R_ < cap: R_ = min(cap, R_ * 1.6)
                    else: break
            if best and p["id"] == "shaar-dobo":     # its site goes with it
                for f in F:
                    if f["id"] == "shahr-i-buzurg": f["lon"] = round(f["lon"] + best[1] - lon0, 5); f["lat"] = round(f["lat"] + best[2] - lat0, 5)
            if best:
                pos[p["id"]] = (best[1], best[2]); moves.append((p, (lon0, lat0), (best[1], best[2]), best[3])); moved_ids.add(p["id"])
    # apply: the place, its landmarks, its height and the real place it takes over
    for p, a, b_, why in moves:
        if a == b_: continue
        dlon, dlat = b_[0] - p["lon"], b_[1] - p["lat"]
        for f in F:
            if f.get("city") == p["name"] and not f.get("locked"):
                f["lon"] = round(f["lon"] + dlon, 5); f["lat"] = round(f["lat"] + dlat, 5)
        p["lon"], p["lat"] = round(b_[0], 5), round(b_[1], 5)
        zg = int(round(z_at(p["lon"], p["lat"]), -1))
        if p.get("elev") and abs(p["elev"] - zg) > ELEV_TOL: p["elev"] = zg
for p in places:
    pos[p["id"]] = (p["lon"], p["lat"])
    if FIX:
        d, k = RT.query(xy(p["lon"], p["lat"]))
        if d <= ON_REAL[p["kind"]] and real[k]["name"] and norm(real[k]["name"]) != norm(p["name"]) and p["id"] not in SPECIAL:
            p["real_name"] = real[k]["name"]
        elif "real_name" in p and (d > ON_REAL[p["kind"]] or not real[k]["name"]): del p["real_name"]

rows = []; nlock = 0
for p in places:
    fails, notes, m = check(p, p["lon"], p["lat"], others_of(p, pos))
    if LOCK and not fails and p["id"] not in SPECIAL and not LABEL.search(p.get("note", "")): p["locked"] = True   # special places and labels stay with their own scripts
    nlock += bool(p.get("locked"))
    rows.append((p, not fails, fails, notes, m))
korder = {"capital": 0, "city": 1, "town": 2, "village": 3}
rows.sort(key=lambda r: (r[1], korder[r[0]["kind"]], r[0]["zone"], r[0]["district"] or "", r[0]["name"]))
out = ["# Place audit (build/audit_places.py)", "",
       "Rules in docs/PLACEMENT.md: R1 on a real settlement where one is free nearby, R2 one place per settlement and spacing, R3 size, "
       "R4 height, R5–R7 slope, water and road for invented places, R8 jurisdiction. Locked places are never moved by the build.", "",
       f"**{sum(r[1] for r in rows)} of {len(rows)} pass; {nlock} locked.**", ""]
if moves:
    out += ["## Moved by --fix", "", "| place | moved | onto |", "|---|---|---|"]
    for p, a, b_, why in moves:
        out.append(f"| {p['name']} | {math.hypot((b_[0] - a[0]) * KX, (b_[1] - a[1]) * KY):.1f} km | {why} |")
    out.append("")
out += ["## Places", "", "| place | kind | zone / district | status | problems | notes |", "|---|---|---|---|---|---|"]
for p, ok, fails, notes, m in rows:
    st = ("🔒 locked" if p.get("locked") else "pass") if ok else ("🔒 locked, fails" if p.get("locked") else "fails")
    out.append(f"| {p['name']} (`{p['id']}`) | {p['kind']} | {p['zone']} / {p['district'] or '–'} | {st} | {'; '.join(fails) or '–'} | "
               f"{'; '.join(notes)}; {m['z']:.0f} m, slope {100 * m['slope']:.0f}%, water {m['water']:.1f} km, road {m['road']:.1f} km |")
open(os.path.join(ROOT, "data/place_audit.md"), "w").write("\n".join(out) + "\n")
print(f"{sum(r[1] for r in rows)} of {len(rows)} pass; {nlock} locked; {sum(1 for m in moves if m[1] != m[2])} moved")
for p, a, b_, why in moves:
    print(f"  moved {p['id']:22} {math.hypot((b_[0] - a[0]) * KX, (b_[1] - a[1]) * KY):5.1f} km  {why}")
for p, ok, fails, *_ in rows:
    if not ok: print(f"  FAIL {p['id']:22} {p['kind']:8} " + "; ".join(fails))
if FIX or LOCK:
    json.dump(P, open(os.path.join(ROOT, "data/settlements.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)
