"""Real towns and villages for the map (data/real_places.json), from the extractor's places layer.

  python3 build/real_places.py <extract dir>

Inside Irad every real town, village and hamlet keeps its real name, written the way Irad writes place names (Latin,
Kyrgyz-style: Kök-Jar, Kyzyl-Adyr, Tash-Kömür), unless:
  - a lore place stands there (within 1.5 km, or the same name within 6 km): the lore place is the map's;
  - it lies inside a city plan (Talas, Nurzhan, Iyık Janyl), whose own quarters are in the lore;
  - RENAME gives it another name (the lore's: Taraz is Aulie-Ata in Irad).
Outside Irad only towns and cities are kept (as reference points in the neighbouring countries), with their usual English
names. Each place gets its zone (ISEZ/ATR) and, in the ISEZ, its district.
"""
import json, math, os, re, sys
import numpy as np
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = sys.argv[1]
KY = 110.57

# real place (OSM name) -> how Irad has it
RENAME = {
    "Меркі": dict(name="Merke", name_ru="Мерке", pop=None),        # the lore's spelling (the Merke stream)
    "Манас": dict(name="Jalal-Abad", name_ru="Джалал-Абад", pop=None),   # the 2025 renaming of Jalal-Abad is not used on Irad's maps
    "Тараз": dict(name="Aulie-Ata", name_ru="Аулие-Ата", kind="town", pop=14000,
                  note="Market town on the Talas below the Karatau, on the old Aulie-Ata of the Kokand khanate and the Russian "
                       "uezd town; much of the Soviet city was abandoned after 1992 and 2007 and has been cleared back to the old "
                       "core. Gives its name to the Aulie-Ata cattle of the Talas valley."),
}

from translit import CYR, DROP_WORDS, latin   # noqa: E402


SOVIET = ("Кирова", "Киров", "Фрунзе", "Тельман", "Гагарин", "Панфилов", "Калинин", "Чапаев", "Ленин", "Свердлов", "Жамбыл", "Абай", "Абая")
ROOT1 = ["Ak", "Kara", "Kyzyl", "Kök", "Sary", "Jangy", "Eski", "Orto", "Tash", "Kum", "Boz", "Chong", "Kichi", "Üch", "Besh", "Jyluu", "Tört", "Alma"]
ROOT2 = ["Bulak", "Suu", "Döbö", "Bel", "Jar", "Terek", "Aryk", "Kuduk", "Tal", "Jol", "Kamysh", "Say", "Tübek", "Kystak", "Korgon", "Adyr", "Kyr", "Too", "Uzak", "Talaa"]


def iradi_name(seed, taken):
    """a Kyrgyz-style descriptive village name (Ak-Bulak, Kara-Döbö ...) not yet used nearby"""
    import hashlib
    h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16)
    for k in range(len(ROOT1) * len(ROOT2)):
        a = ROOT1[(h + k * 7) % len(ROOT1)]; b = ROOT2[(h // 31 + k * 3) % len(ROOT2)]
        nm = f"{a}-{b}"
        if norm(nm) not in taken: return nm
    return f"{ROOT1[h % len(ROOT1)]}-{ROOT2[h % len(ROOT2)]}"


def commemorative(pr, native):
    """a village renamed after a person in independent Kazakhstan or Kyrgyzstan (after Irad went its own way)"""
    ru = pr.get("name_ru") or ""
    if any(w in ru or w in native for w in SOVIET): return False
    if re.search(r"\bата\b|\bбаба\b|биби|bibi", native.lower()): return False                  # saints' shrines keep their names
    if re.search(r"ауылы$", native.strip()) and len(native.split()) >= 3: return True        # "Firstname Surname ауылы"
    if re.search(r"ауылы$", native.strip()) and re.search(r"(ов|ев|ова|ева|ұлы|улы|баев)\s+ауылы$", native.strip()): return True
    if re.search(r"имени|^Аул |атындагы|батыр", native + " " + ru): return True
    w = native.split()
    return len(w) >= 2 and bool(re.search(r"(ов|ев|ова|ева|ұлы|улы|ин|баев)$", w[-1]))   # Firstname Surname


def norm(s):
    s = latin(s).lower()
    for a, b in (("ö", "o"), ("ü", "u"), ("ı", "i"), ("kh", "h"), ("zh", "j"), ("dj", "j"), ("y", "i")): s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


def polys(fn, key):
    out = []
    for f in json.load(open(os.path.join(ROOT, fn)))["features"]:
        g = f["geometry"]; ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        out.append((f["properties"].get(key), [Path(np.array(p[0])) for p in ps]))
    return out


def which(regions, x, y):
    for v, paths in regions:
        if any(p.contains_point((x, y)) for p in paths): return v
    return None


def main():
    irad = polys("data/irad.geojson", "name"); zones = polys("data/zones.geojson", "zone"); dists = polys("data/districts.geojson", "district")
    feet = [Path(np.array(p[0])) for c in json.load(open(os.path.join(ROOT, "data/city/index.json")))["cities"]
            for p in ([c["footprint"]["coordinates"]] if c["footprint"]["type"] == "Polygon" else c["footprint"]["coordinates"])]
    lore = [p for p in json.load(open(os.path.join(ROOT, "data/settlements.json"))) if p["kind"] not in ("district", "zone-area")]
    LX = np.array([[p["lon"], p["lat"]] for p in lore]); lore_n = [norm(p.get("name")) for p in lore]
    out, seen, dropped = [], [], {"lore place": 0, "city plan": 0, "duplicate": 0, "no name": 0}
    for line in open(os.path.join(EXT, "places.ndjson")):
        f = json.loads(line); pr = f["properties"]; x, y = f["geometry"]["coordinates"]
        if pr["place"] not in ("city", "town", "village", "hamlet"): continue      # peaks, passes and localities are build/nature.py's
        native = pr.get("name") or pr.get("name_ky") or pr.get("name_kk") or pr.get("name_uz") or pr.get("name_ru")
        if not native: dropped["no name"] += 1; continue
        if re.search(r"\d|разъезд|айрығы|станция|пионерлагер|демалыс|зона отдыха|санатори|шипажай|кордон|подхоз|ПМК|лагерь", native + " " + (pr.get("name_ru") or ""), re.I):
            dropped["no name"] += 1; continue      # rail sidings, stations, camps and sanatoria, numbered blocks
        if not re.search(r"[\u0400-\u04FF]", native) and pr.get("name_ru"): native_l = pr["name_ru"]       # Uzbek Latin: read from Russian
        else: native_l = native
        inside = which(irad, x, y) is not None
        if not inside and pr["place"] not in ("city", "town"): continue
        if not inside:
            try: popv = int(re.sub(r"\D", "", pr.get("population") or "0") or 0)
            except ValueError: popv = 0
            if pr["place"] == "town" and popv < 20000: continue
        if any(p.contains_point((x, y)) for p in feet): dropped["city plan"] += 1; continue
        kx = 111.32 * math.cos(math.radians(y))
        d = np.hypot((LX[:, 0] - x) * kx, (LX[:, 1] - y) * KY)
        rn = RENAME.get(native)
        en = pr.get("name_en") or ""
        nm = rn["name"] if rn else (latin(native_l) if inside else (en if re.fullmatch(r"[A-Za-z \-()]+", en) else latin(pr.get("name_ru") or native)))
        renamed = False
        clash = any(lore_n[i] == norm(nm) and (lore[i]["kind"] in ("capital", "city") or (lore[i]["kind"] == "town" and d[i] < 30))
                    for i in range(len(lore)))                     # nor a second Talas or Nurzhan, nor a namesake next to a lore town
        if any(s_[2] == "orig:" + norm(native) and math.hypot((s_[0] - x) * kx, (s_[1] - y) * KY) < 3 for s_ in seen): dropped["duplicate"] += 1; continue
        seen.append((x, y, "orig:" + norm(native)))
        if inside and not rn and (commemorative(pr, native) or clash):
            nm = iradi_name(pr["id"], {s_[2] for s_ in seen} | set(lore_n)); renamed = True
        if not rn and (d.min() < 1.5 or any(d[i] < 6 and lore_n[i] == norm(native) for i in range(len(lore)))):
            dropped["lore place"] += 1; continue
        if not renamed and any(s[2] == norm(nm) and math.hypot((s[0] - x) * kx, (s[1] - y) * KY) < 3 for s in seen): dropped["duplicate"] += 1; continue
        seen.append((x, y, norm(nm)))
        try: pop = int(re.sub(r"\D", "", pr.get("population") or "") or 0) or None
        except ValueError: pop = None
        kind = {"city": "town", "town": "town", "village": "village", "hamlet": "hamlet"}[pr["place"]]
        if pr["place"] == "city" and pop and pop > 100000: kind = "city"
        p = {"id": "osm-" + str(pr["id"]), "name": nm, "name_ru": pr.get("name_ru") or (native if re.search(r"[Ѐ-ӿ]", native) else None),
             "kind": kind, "lon": round(x, 5), "lat": round(y, 5), "pop": pop, "confidence": "osm",
             "zone": which(zones, x, y) if inside else "abroad", "district": which(dists, x, y) if inside else None}
        if not inside: p["kind"] = "foreign-" + ("city" if pr["place"] == "city" else "town"); p["name"] = re.sub(r"\s*\(.*?\)", "", p["name"])
        if inside and not rn: p["pop"] = None      # Irad's populations are the lore's to give, not today's real figures
        if rn: p.update({k: v for k, v in rn.items()}); p["confidence"] = "renamed"
        if renamed:
            p["confidence"] = "irad-name"; p["real_name"] = latin(native); p["name_ru"] = None
            p["name"] = re.sub(r"\s*\(.*?\)", "", p["name"])
            p["note"] = ("Iradi name; the village was not renamed after a person as on the Kazakh or Kyrgyz side." if commemorative(pr, native)
                         else "Iradi name, to tell it from the city of the same name.")
        out.append(p)
    json.dump(out, open(os.path.join(ROOT, "data/real_places.json"), "w"), ensure_ascii=False, indent=0)
    import collections
    print(len(out), "places;", dict(collections.Counter(p["kind"] for p in out)), "; dropped", dropped)
    for p in out:
        if p["kind"] in ("town", "city") and p["zone"] != "abroad": print(f"  {p['name']:24} {p.get('name_ru') or '':24} {p['zone']} {p.get('district') or ''} {p.get('pop') or ''}")


if __name__ == "__main__":
    main()
