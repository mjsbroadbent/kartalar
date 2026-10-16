#!/usr/bin/env python3
"""Everyday businesses for an Iradi city: restaurants, cafés, chaikhanas, shops, supermarkets, pharmacies, banks,
fuel and hotels, taken from the real donor city's map and moved with its street plan (build/make_cities.py), so they
sit where businesses really cluster. Real names are never used: every business gets an Iradi name (build/biz_names.py).

    python3 build/make_businesses.py <donor pois.ndjson> [city]

<donor pois.ndjson> comes from build/base/extract_poi.cpp run over the donor country's .osm.pbf and the donor city's
box. Writes data/biz/<city>.json (the format of docs/PLACES.md) and prints counts by kind. Deterministic: the same
input gives the same businesses, names and hours.
"""
import glob, hashlib, json, math, os, re, sys
import numpy as np
from matplotlib.path import Path
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
import biz_names

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KY = 110.57
def kx(lat): return 111.32 * math.cos(math.radians(lat))

# the same move as build/make_cities.py (keep the two in step)
CITIES = {
    "talas": {"donor": "bishkek", "pivot_donor": (74.6037, 42.8765), "pivot": (72.240, 42.519), "rotate": 0, "mirror": False, "scale": 1.0,
              "city": "Talas", "zone": "ISEZ",
              # the Old City is the lore's own mahalla, not the donor's streets: its businesses are made around the bazaar
              "old_town": {"center": (72.2290, 42.5275), "a": 0.60, "b": 0.42, "angle": 12},
              "clusters": [
                  {"at": (72.2338, 42.5262), "r": 0.3, "extra": {"bazaar": True},
                   "mix": [[k, s_] for k, s_ in [("chaikhana", "chaikhana")] * 9 + [("bakery", "bakery")] * 5
                           + [("grocery", x) for x in ["spices", "greengrocer", "butcher", "dairy", "tea"] * 2]
                           + [("shop", x) for x in ["fabric", "carpet", "jewelry", "houseware", "clothes", "shoes", "gift", "hardware"] * 2]
                           + [("restaurant", "restaurant")] * 3 + [("guesthouse", "guest_house")] * 2]},
                  {"at": (72.131, 42.514), "r": 0.5,
                   "mix": [["restaurant", "restaurant", "mexican"]] * 4 + [["bakery", "tortilleria", "mexican"]] * 3 + [["grocery", "convenience"]] * 3
                          + [["bakery", "bakery", "mexican"]] + [["shop", "car_repair"]] * 3},
              ],
              "areas": {"semiz": (72.131, 42.514, 1.4),
                        "base": ([72.152, 72.278, 72.165], [42.508, 42.488, 42.522], 1.6)},     # Cottonwood Estates, Alatau Heights, the strip toward the base
              "named": [   # canon.md: the Tulpar delivery partners, KFC Irad, the International Diplomatic Hotel
                  {"at": "talas-bazar-i-kalan", "kinds": ["chaikhana"], "name": "Chaykhana Bakyt", "name_ir": "Chaykhana Bakyt", "name_en": "Chaikhana Bakyt",
                   "name_ru": "Чайхана «Бакыт»", "tulpar": True},
                  {"at": "semiz", "kinds": ["restaurant", "cafe", "fast-food"], "name": "Taquería Semiz", "name_ir": "Taquería Semiz", "name_en": "Taquería Semiz",
                   "name_ru": "Такерия «Семиз»", "cuisine": "mexican", "kind": "restaurant", "tulpar": True},
                  {"at": "altyn-tower", "kinds": ["restaurant", "cafe", "fast-food"], "name": "Altyn Tower Pizza", "name_ir": "Altyn Tower Pizza",
                   "name_en": "Altyn Tower Pizza", "name_ru": "Altyn Tower Pizza", "cuisine": "pizza", "kind": "restaurant", "tulpar": True},
                  {"at": "talas-central-square", "kinds": ["bakery"], "name": "Nan & Boorsok", "name_ir": "Nan & Boorsok", "name_en": "Nan & Boorsok",
                   "name_ru": "Нан и Боорсок", "tulpar": True},
                  {"at": (72.300, 42.520), "kinds": ["cafe", "restaurant"], "name": "Shashlyk Kara-Suu", "name_ir": "Shashlık Kara-Suu", "name_en": "Shashlyk Kara-Suu",
                   "name_ru": "Шашлык «Кара-Суу»", "cuisine": "shashlyk", "kind": "cafe", "tulpar": True},
                  {"at": "talas-central-square", "kinds": ["hotel"], "name": "International Diplomatic Hotel", "name_ir": "El aralık Diplomatiyalık Meymankana",
                   "name_en": "International Diplomatic Hotel", "name_ru": "Международный дипломатический отель", "price_level": 4,
                   "note": "TCDG's hotel for the diplomatic corps and foreign delegations."},
                  {"at": "talas-bazar-i-kalan", "kinds": ["hotel", "guesthouse"], "name": "Hotel Bazar-i Kalan", "name_ir": "Meymankana Bazar-i Kalan",
                   "name_en": "Hotel Bazar-i Kalan", "name_ru": "Гостиница «Базар-и Калан»", "kind": "hotel", "price_level": 3,
                   "note": "Opened in 2018 on the site of a demolished 1910 merchant house by the covered market."},
              ] + [{"at": at, "kinds": ["fast-food"], "name": "KFC Irad", "name_ir": "KFC Irad", "name_en": "KFC Irad", "name_ru": "KFC Irad",
                    "cuisine": "chicken", "tulpar": True} for at in ["talas-central-square", "silk-road-arena", (72.165, 42.522), (72.278, 42.488)]]},
}

# OSM tag -> (our kind, sub-type). None: not brought across (civic places are the lore's; parking, benches ...)
FOOD = {"restaurant": "restaurant", "cafe": "cafe", "fast_food": "fast-food", "bar": "bar", "pub": "bar", "food_court": "fast-food",
        "ice_cream": "cafe", "biergarten": "bar"}
SHOP = {"supermarket": "supermarket", "convenience": "grocery", "kiosk": "grocery", "greengrocer": "grocery", "butcher": "grocery",
        "general": "grocery", "outpost": None, "bakery": "bakery", "confectionery": "bakery", "pastry": "bakery", "alcohol": "grocery",
        "beverages": "grocery", "dairy": "grocery", "seafood": "grocery", "deli": "grocery", "spices": "grocery", "tea": "grocery",
        "clothes": "shop", "shoes": "shop", "mobile_phone": "shop", "electronics": "shop", "computer": "shop", "hardware": "shop",
        "doityourself": "shop", "furniture": "shop", "florist": "shop", "books": "shop", "stationery": "shop", "cosmetics": "shop",
        "jewelry": "shop", "gift": "shop", "toys": "shop", "sports": "shop", "fabric": "shop", "car_parts": "shop", "tyres": "shop",
        "optician": "shop", "chemist": "shop", "houseware": "shop", "mall": "mall", "department_store": "mall", "hairdresser": "shop",
        "beauty": "shop", "car_repair": "shop", "variety_store": "shop", "bag": "shop", "boutique": "shop", "baby_goods": "shop",
        "pet": "shop", "hifi": "shop", "appliance": "shop", "paint": "shop", "kitchen": "shop", "watches": "shop", "carpet": "shop"}
AMEN = {"pharmacy": "pharmacy", "bank": "bank", "fuel": "fuel", "marketplace": "market", "bureau_de_change": "bank"}
TOUR = {"hotel": "hotel", "hostel": "hostel", "guest_house": "guesthouse", "motel": "hotel", "apartment": "guesthouse"}
# what share of each kind to keep: the donor is mapped very unevenly, and a map with five kiosks per block reads as noise
KEEP = {"grocery": 0.55, "shop": 0.45, "bank": 0.3, "pharmacy": 0.6, "cafe": 0.85, "fast-food": 0.8, "mall": 0.6, "market": 0.7}
KEEP_SUB = {"kiosk": 0.25, "car_repair": 0.3, "hairdresser": 0.35, "beauty": 0.3, "bureau_de_change": 0.3, "alcohol": 0.5}


def classify(p):
    a, s, t = p.get("amenity"), p.get("shop"), p.get("tourism")
    if a in FOOD: return FOOD[a], a
    if a in AMEN: return AMEN[a], a
    if s in SHOP: return (SHOP[s], s) if SHOP[s] else None
    if t in TOUR: return TOUR[t], t
    return None


def h01(*xs):
    """a stable number in [0, 1) from the inputs"""
    return int(hashlib.md5("|".join(map(str, xs)).encode()).hexdigest()[:12], 16) / 16 ** 12


# ---------- opening hours: the donor's own where mapped, otherwise by kind ----------
DAYS = ["mo", "tu", "we", "th", "fr", "sa", "su"]
def parse_hours(s):
    """the common forms of OSM opening_hours -> {"mo": "09:00-21:00", ...}; None when not understood"""
    s = s.strip()
    if s == "24/7": return {d: "24h" for d in DAYS}
    out = {}
    for rule in [r.strip() for r in s.split(";") if r.strip()]:
        m = re.fullmatch(r"(?:([A-Z][a-z](?:-[A-Z][a-z])?(?:,[A-Z][a-z](?:-[A-Z][a-z])?)*)\s+)?(off|closed|\d\d:\d\d-\d\d:\d\d(?:,\s*\d\d:\d\d-\d\d:\d\d)*)", rule)
        if not m: return None
        days = []
        for part in (m.group(1) or "Mo-Su").split(","):
            ab = [x.lower() for x in part.split("-")]
            if any(x not in DAYS for x in ab): return None
            i, j = DAYS.index(ab[0]), DAYS.index(ab[-1])
            days += [DAYS[(i + k) % 7] for k in range((j - i) % 7 + 1)]
        v = "closed" if m.group(2) in ("off", "closed") else re.sub(r"\s", "", m.group(2)).replace("24:00", "00:00")
        if v == "00:00-00:00": v = "24h"
        for d in days: out[d] = v
    for d in DAYS: out.setdefault(d, "closed")
    return out

DEFAULT_HOURS = {   # (weekdays, saturday, sunday) choices
    "restaurant": [("11:00-23:00",) * 3, ("12:00-00:00",) * 3, ("10:00-22:00",) * 3],
    "cafe": [("08:00-22:00",) * 3, ("09:00-23:00",) * 3, ("10:00-22:00",) * 3],
    "chaikhana": [("07:00-21:00",) * 3, ("06:00-20:00",) * 3, ("08:00-22:00",) * 3],
    "fast-food": [("10:00-23:00",) * 3, ("09:00-02:00",) * 3, ("24h",) * 3],
    "bar": [("17:00-02:00",) * 3, ("18:00-03:00",) * 3],
    "bakery": [("07:00-20:00",) * 3, ("06:00-19:00",) * 3],
    "grocery": [("08:00-23:00",) * 3, ("24h",) * 3, ("07:00-22:00",) * 3],
    "supermarket": [("08:00-23:00",) * 3, ("09:00-22:00",) * 3, ("24h",) * 3],
    "shop": [("10:00-20:00", "10:00-19:00", "10:00-18:00"), ("09:00-19:00", "09:00-17:00", "closed"), ("10:00-21:00",) * 3],
    "mall": [("10:00-22:00",) * 3],
    "market": [("06:00-18:00", "06:00-18:00", "06:00-16:00"), ("07:00-17:00", "07:00-17:00", "closed")],
    "pharmacy": [("08:00-22:00",) * 3, ("24h",) * 3, ("09:00-20:00", "09:00-18:00", "10:00-16:00")],
    "bank": [("09:00-17:00", "09:00-13:00", "closed"), ("09:00-18:00", "10:00-15:00", "closed")],
    "fuel": [("24h",) * 3, ("06:00-23:00",) * 3],
    "hotel": [("24h",) * 3], "hostel": [("24h",) * 3], "guesthouse": [("24h",) * 3, ("08:00-22:00",) * 3],
}
def default_hours(kind, key):
    ch = DEFAULT_HOURS[kind]; wd, sa, su = ch[int(h01(key, "h") * len(ch))]
    return {**{d: wd for d in DAYS[:5]}, "sa": sa, "su": su}


def load_city_buildings(city):
    pts = []
    for fn in glob.glob(os.path.join(ROOT, "data/city", city, "t_*.json")):
        for f in json.load(open(fn))["features"]:
            if f["properties"].get("t") != "building": continue
            g = f["geometry"]; ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
            R = np.array(ring)[:, :2]; pts.append(R.mean(axis=0))
    return np.array(pts)


def main():
    src = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else "talas"
    C = CITIES[name]
    pdx, pdy = C["pivot_donor"]; tx, ty = C["pivot"]; kd, kt = kx(pdy), kx(ty)
    a = math.radians(C["rotate"]); ca, sa = math.cos(a), math.sin(a); sc = C["scale"]; mir = -1 if C["mirror"] else 1
    def tf(lon, lat):
        x = (lon - pdx) * kd * mir; y = (lat - pdy) * KY
        return tx + (x * ca - y * sa) * sc / kt, ty + (x * sa + y * ca) * sc / KY

    ix = json.load(open(os.path.join(ROOT, "data/city/index.json")))
    fp = [c for c in ix["cities"] if c["name"] == name][0]["footprint"]
    foot = [Path(np.array(p[0])) for p in (fp["coordinates"] if fp["type"] == "MultiPolygon" else [fp["coordinates"]])]
    in_foot = lambda x, y: any(P.contains_point((x, y)) for P in foot)
    O = C.get("old_town")
    def in_old(x, y):
        if not O: return False
        (cx, cy), A, B = O["center"], O["a"], O["b"]; th = math.radians(O["angle"])
        X, Y = (x - cx) * kt, (y - cy) * KY
        u, v = (X * math.cos(th) + Y * math.sin(th)) / A, (-X * math.sin(th) + Y * math.cos(th)) / B
        return u * u + v * v <= 1
    B = load_city_buildings(name); bt = cKDTree(B * [kt, KY])
    print(f"  {len(B)} buildings in the {name} plan")

    # the lore's own places in the city: no business on top of one
    feats = [f for f in json.load(open(os.path.join(ROOT, "data/features.json"))) if f.get("city") == C["city"]]
    lore_t = cKDTree(np.array([[f["lon"] * kt, f["lat"] * KY] for f in feats])) if feats else None
    places = json.load(open(os.path.join(ROOT, "data/settlements.json")))
    quarters = [p for p in places if p["kind"] in ("quarter", "neighbourhood", "suburb") and in_foot(p["lon"], p["lat"])]

    out, stats, seen = [], {}, set()
    def add(kind, sub, x, y, key, hours, extra):
        if (round(x, 5), round(y, 5)) in seen: return
        seen.add((round(x, 5), round(y, 5)))
        q = min(quarters, key=lambda p: (p["lon"] - x) ** 2 * kt * kt + (p["lat"] - y) ** 2 * KY * KY) if quarters else None
        dq = math.hypot((q["lon"] - x) * kt, (q["lat"] - y) * KY) if q else 99
        b = {"id": f"biz-{name}-{len(out) + 1:04d}", "kind": kind, "sub": sub, "lat": round(y, 6), "lon": round(x, 6),
             "city": C["city"], "zone": C["zone"], "quarter": q["id"] if q and dq < 2.5 else None, "hours": hours}
        b.update(extra); b["_key"] = key
        out.append(b); stats[kind] = stats.get(kind, 0) + 1

    n_in = 0
    for line in open(src):
        p = json.loads(line); c = classify(p)
        if not c: continue
        kind, sub = c
        x, y = tf(p["lon"], p["lat"])
        if not in_foot(x, y) or in_old(x, y): continue
        n_in += 1
        if h01(p["osm"], "keep") >= KEEP_SUB.get(sub, KEEP.get(kind, 1.0)): continue
        d, _ = bt.query([x * kt, y * KY])
        if d > (0.12 if kind in ("fuel", "market", "mall") else 0.04): continue      # on a building (fuel and markets: by one)
        if lore_t is not None and lore_t.query([x * kt, y * KY])[0] < 0.03: continue
        hours = parse_hours(p["opening_hours"]) if p.get("opening_hours") else None
        extra = {}
        if p.get("cuisine"): extra["cuisine"] = p["cuisine"].split(";")[0]
        if p.get("stars"): extra["stars"] = p["stars"]
        add(kind, sub, x, y, p["osm"], hours, extra)
    print(f"  {n_in} donor businesses fall on the site; {len(out)} kept")

    # clusters the donor cannot give: the Old City's bazaar lanes, Semiz's Mexican high street (canon: a dozen
    # tortillerías, taquerías, groceries, a bakery and car workshops). Each: [kind, sub, cuisine] cycled over buildings near the centre
    for ci, cl in enumerate(C.get("clusters", [])):
        bx, by = cl["at"]
        near = bt.query_ball_point([bx * kt, by * KY], cl["r"])
        near = sorted(near, key=lambda i: h01(name, "cl", ci, i))[:len(cl["mix"])]
        for j, i in enumerate(near):
            kind, sub, cu = (cl["mix"][j] + [None, None])[:3]
            x, y = B[i]
            add(kind, sub, float(x), float(y), f"cl{ci}-{j}", None, dict({"cuisine": cu} if cu else {}, **cl.get("extra", {})))

    # a share of the donor's cafés are teahouses here
    for b in out:
        if b["kind"] == "cafe" and b.get("cuisine") not in ("coffee_shop", "dessert", "pizza", "burger") and h01(b["_key"], "chai") < 0.3:
            b["kind"] = "chaikhana"; stats["cafe"] -= 1; stats["chaikhana"] = stats.get("chaikhana", 0) + 1

    # the lore's character by area: the Mexican community's Semiz, the American contractors' strip toward the air base
    # and the gated estates (canon: taquerías and tortillerías in Semiz; steakhouses and fast food near the base)
    def area_of(b):
        for a_, (lon, lat, r) in C.get("areas", {}).items():
            for (lo, la) in ([(lon, lat)] if isinstance(lon, float) else zip(lon, lat)):
                if math.hypot((b["lon"] - lo) * kt, (b["lat"] - la) * KY) < r: return a_
        return None
    for b in out:
        if not b["hours"]: b["hours"] = default_hours(b["kind"], b["_key"])
        biz_names.dress(b, name, area_of(b))

    # banks: the lore's Talasbank has 28 branches; the Transoxiana Microfinance Fund a few; the rest two smaller banks
    banks = sorted([b for b in out if b["kind"] == "bank" and b["sub"] != "bureau_de_change"], key=lambda b: h01(b["_key"], "bank"))
    for i, b in enumerate(banks):
        if i < C.get("talasbank", 28): continue
        elif i < C.get("talasbank", 28) + 5: biz_names.set_names(b, "Transoxiana Mikrokarjı Fondu", "Transoxiana Microfinance Fund", "Трансоксиана Микрофинансовый фонд")
        elif h01(b["_key"], "bk2") < 0.55: biz_names.set_names(b, "Chüy Kommertsiyalık Banky", "Chuy Commercial Bank", "Чуй Коммерческий банк")
        else: biz_names.set_names(b, "Ak Bata Bank", "Ak Bata Bank", "Ак Бата Банк")

    # the lore's own businesses, onto the nearest fitting one
    taken = set()
    def nearest(kinds, lon, lat, cond=lambda b: True):
        c_ = [b for b in out if b["kind"] in kinds and b["id"] not in taken and cond(b)]
        b = min(c_, key=lambda b: (b["lon"] - lon) ** 2 * kt * kt + (b["lat"] - lat) ** 2 * KY * KY); taken.add(b["id"]); return b
    feat = {f["id"]: f for f in feats + places}
    for spec in C.get("named", []):
        at = spec["at"]; lon, lat = (feat[at]["lon"], feat[at]["lat"]) if isinstance(at, str) else at
        b = nearest(spec["kinds"], lon, lat, spec.get("cond", lambda b: True))
        b["kind"] = spec.get("kind", b["kind"])
        for k_, v in spec.items():
            if k_ in ("name", "name_en", "name_ru", "name_ir", "cuisine", "note", "price_level", "price", "tulpar"): b[k_] = v
        if "cuisine" in spec: b["cuisine_label"] = biz_names.CUISINE_LABEL[spec["cuisine"]]
        b["lore"] = True

    # Tulpar delivery: the five lore partners and a share of the city's eateries
    for b in out:
        if b["kind"] in ("restaurant", "cafe", "fast-food", "chaikhana", "bakery") and h01(b["_key"], "tulpar") < 0.4: b["tulpar"] = True
        del b["_key"]
        if b["quarter"] is None: del b["quarter"]
        if b.get("sub") == b["kind"]: del b["sub"]
        if b.get("name_ir") == b["name"]: del b["name_ir"]                # nameOf() falls back to name
        b["lat"], b["lon"] = round(b["lat"], 5), round(b["lon"], 5)

    os.makedirs(os.path.join(ROOT, "data/biz"), exist_ok=True)
    fn = os.path.join(ROOT, "data/biz", f"{name}.json")
    json.dump(out, open(fn, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote {fn}: {len(out)} businesses")
    for k, v in sorted(stats.items(), key=lambda kv: -kv[1]): print(f"    {k:12} {v}")


if __name__ == "__main__":
    main()
