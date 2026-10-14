"""Put the lore's sites in Talas onto the city plan.

Each site goes to the building or grounds in the plan that suits it: anchors are features of the donor plan picked by
their (donor) name and carried through the same transform as the plan (so the Talas sports palace stands on the
plan's sports palace, the philharmonic on its round concert hall); sites without an anchor go to the nearest piece of
ground of the right kind (a pitch for a stadium, institutional grounds for a hospital or school, industrial land for
a works, a building for an office). The Old City sites sit on the generated old town.
Run after build/make_cities.py:  python3 build/place_sites.py <dir with city-<donor>.json>
"""
import json, math, os, re, sys, glob
import numpy as np
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDIR = sys.argv[1]
sys.argv = [sys.argv[0], "-", "-", CDIR]
import importlib.util
spec = importlib.util.spec_from_file_location("mc_cfg", os.path.join(ROOT, "build/make_cities.py"))
src = open(os.path.join(ROOT, "build/make_cities.py")).read()
CITIES = None
_ns = {}
exec(src.split("GRID = 0.0005")[0].split("# ---------- the cities ----------")[1], {"math": math, "np": np}, _ns)
CITIES = {c["name"]: c for c in _ns["CITIES"]}
KY = 110.57
kx = lambda lat: 111.32 * math.cos(math.radians(lat))

# Talas: site id -> donor-name regex (first match, largest feature wins) or ("at", lon, lat) or ("kind", kind)
TALAS = {
    "national-historical-museum": r"Улуттук тарыхый музей",
    "talas-city-hall": r"Мэрия г\. Бишкек",
    "bank-of-irad-head-office": r"^Национальный Банк КР",
    "talas-central-post-office": r"^Кыргызпочта$",
    "talas-fire-brigade-hq": r"Пожарная часть Свердловского",
    "talas-municipal-theater": r"Театр юного зрителя",
    "talas-philharmonic-hall": r"^Филармония$",
    "talas-opera-ballet": r"театр оперы и балета",
    "talas-drama-theatre": r"Русский Драматический Театр",
    "talas-central-park": r"Панфилов атындагы сейилбак",
    "irad-central-sports-complex": r"Кожомкул атындагы спорт сарайы",
    "silk-road-arena": r"Дөлөн Өмүрзаков атындагы стадион",
    "talas-regional-hospital": r"^Национальный госпиталь",
    "talas-blood-services-center": r"^Республиканская больница",
    "talas-municipal-hospital-1": r"Чуйская областная объединенная больница",
    "st-luka-hospital-talas": r"Республикалык жугуштуу оорулар",
    "talas-state-university": r"Кыргыз улуттук аграрды",
    "talas-pedagogical-institute": r"Кыргызский Национальный Университет имени Жус",
    "national-conservatory-folk-music": r"Кыргызская национальная консерватория",
    "talas-municipal-bus-depot": r"^Автобусный парк",
    "irad-state-hippodrome": r"^Ипподром$",
    "general-staff-complex": r"Генеральный штаб Вооруженных Сил",
    "talas-gymnasium-4": r"Компьютерная гимназия №5",
    "church-st-tomas-talas": r"^Католическая церковь",
    "alikhan-media-center": r"^БЦ Россия",
    "iradi-leatherworks-factory": r"^Кожзавод",
    "talas-municipal-cold-storage": r"^Холодильные камеры",
    "attelkom-park": r"стадион Сельмашевец",
    "tsu-stadium": r"Кыргызская Государственная Академия Физическо",
    "talas-pre-trial-detention": r"^СИЗО ГКНБ",
}
NEAR = {   # site -> (other site, max metres): placed on the nearest suitable spot next to it
    "hunters-vigil": ("talas-central-park", 0), "talas-government-house": ("talas-central-square", 160), "talas-legislative-hall": ("talas-central-square", 260),
    "talas-hall-of-justice": ("talas-central-square", 420), "talas-district-court": ("talas-hall-of-justice", 250),
    "state-archives-of-irad": ("talas-state-university", 250), "st-luka-clinic-talas": ("st-luka-hospital-talas", 600),
    "st-maryam-catholic-academy": ("church-st-tomas-talas", 300), "miners-hall-talas": ("talas-central-square", 380),
    "talasfilm-archives": ("cinema-boulevard", 120),
}
OLD = {"talas-citadel": "citadel", "kalan-darwaza": "gate1", "temir-kapka-gate": "gate0", "bazar-i-kalan": "bazaar", "talas-bazar-i-kalan": "bazaar"}
GROUND = {"stadium": {"pitch"}, "hippodrome": {"pitch", "grass"}, "hospital": {"institution"}, "school": {"institution"}, "university": {"institution"},
          "market": {"commercial"}, "industry": {"industrial"}, "terminal": {"industrial"}, "park": {"park", "grass"}, "military": {"industrial", "institution"},
          "bus-station": {"commercial", "parking", "industrial"}}


def main():
    C = CITIES["talas"]
    donor = json.load(open(os.path.join(CDIR, f"city-{C['donor']}.json")))
    pdx, pdy = C["pivot_donor"]; tx, ty = C["pivot"]; kd, kt = kx(pdy), kx(ty)
    tf = lambda x, y: (tx + (x - pdx) * kd / kt, ty + (y - pdy))
    anchors = {}
    for sid, rx in TALAS.items():
        best = None
        for f in donor["features"]:
            n = (f.get("t") or {}).get("name") or ""
            if not n or f["k"].startswith("hw:") or not re.search(rx, n): continue
            r = f["c"][0] if f.get("multi") else f["c"]
            A = 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:]))) if len(r) > 3 else 0
            if best is None or A > best[0]:
                best = (A, np.mean(np.array(r), axis=0))
        if best is not None: anchors[sid] = tf(*best[1])
        else: print("  no donor anchor for", sid)
    # the plan: land polygons (overview) and buildings (tiles)
    land, bld = [], []
    for f in json.load(open(os.path.join(ROOT, "data/city/talas/overview.json")))["features"]:
        if f["properties"]["t"] == "land":
            g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            for p in polys:
                R = np.array(p[0]); A = 0.5 * abs(np.dot(R[:-1, 0], R[1:, 1]) - np.dot(R[1:, 0], R[:-1, 1])) * kt * KY * 1e6
                land.append((f["properties"]["k"], R, R.mean(0), A))
    for fn in glob.glob(os.path.join(ROOT, "data/city/talas/t_*.json")):
        for f in json.load(open(fn))["features"]:
            if f["properties"]["t"] == "building":
                R = np.array(f["geometry"]["coordinates"][0]); bld.append(R[:-1].mean(0))
    bld = np.array(bld)
    O = C["old_town"]
    old = {"citadel": O["citadel"], "bazaar": O["bazaar"], "gate0": O["gates"][0], "gate1": O["gates"][1]}
    feats = json.load(open(os.path.join(ROOT, "data/features.json")))
    sett = json.load(open(os.path.join(ROOT, "data/settlements.json")))
    allp = {p["id"]: p for p in feats + sett}
    dist = lambda a, b: math.hypot((a[0] - b[0]) * kt, (a[1] - b[1]) * KY) * 1000
    moved = []

    def put(p, q, why):
        before = (p["lon"], p["lat"]); p["lon"], p["lat"] = round(float(q[0]), 5), round(float(q[1]), 5)
        moved.append((p["id"], dist(before, q), why))

    used_land = set()
    for sid in list(anchors):   # an anchor that falls off the clipped plan: snap by kind instead
        q = anchors[sid]
        if np.hypot((bld[:, 0] - q[0]) * kt, (bld[:, 1] - q[1]) * KY).min() * 1000 > 250:
            print("  anchor off the plan, snapping by kind:", sid); del anchors[sid]
    for sid, q in anchors.items():
        if sid in allp: put(allp[sid], q, "donor anchor")
    for sid, key in OLD.items():
        if sid in allp: put(allp[sid], old[key], "old town")
    for sid, (other, r) in NEAR.items():
        if sid not in allp or other not in allp: continue
        o = allp[other]; ref = (o["lon"], o["lat"])
        if r == 0: put(allp[sid], ref, "at " + other); continue
        d = np.hypot((bld[:, 0] - ref[0]) * kt, (bld[:, 1] - ref[1]) * KY) * 1000
        cand = np.where((d > 40) & (d < r))[0]
        if len(cand):
            # the building closest to the site's lore position among those near the reference
            p = allp[sid]; dd = np.hypot((bld[cand, 0] - p["lon"]) * kt, (bld[cand, 1] - p["lat"]) * KY)
            put(p, bld[cand[int(np.argmin(dd))]], "near " + other)
    done = set(anchors) | set(OLD) | set(NEAR) | {"talas-central-square", "talas-railway-station", "talas-cold-chain-hub"}
    for p in feats:
        if (p.get("city") or "").lower() != "talas" or p["id"] in done: continue
        q0 = (p["lon"], p["lat"])
        kinds = GROUND.get(p["kind"])
        if kinds:
            c = [(dist(q0, L[2]), i) for i, L in enumerate(land) if L[0] in kinds and i not in used_land and L[3] > 3000]
            c = [x for x in c if x[0] < 1500]
            if c:
                d_, i = min(c); used_land.add(i); put(p, land[i][2], f"{land[i][0]} grounds"); continue
        if p["kind"] in ("river-point", "spring", "airport", "station"): continue
        d = np.hypot((bld[:, 0] - q0[0]) * kt, (bld[:, 1] - q0[1]) * KY) * 1000
        i = int(np.argmin(d))
        if d[i] < 400: put(p, bld[i], "building")
    json.dump(feats, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(sett, open(os.path.join(ROOT, "data/settlements.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data/talas_sites_report.md"), "w") as f:
        f.write("# Talas sites placed on the city plan (build/place_sites.py)\n\n| site | moved | placed on |\n|---|---|---|\n")
        for sid, d_, why in sorted(moved, key=lambda m: -m[1]):
            f.write(f"| {sid} | {d_:.0f} m | {why} |\n")
    for sid, d_, why in sorted(moved, key=lambda m: -m[1]):
        print(f"  {sid:38} {d_:6.0f} m  {why}")


if __name__ == "__main__":
    main()
