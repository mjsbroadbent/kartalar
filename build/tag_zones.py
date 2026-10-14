"""Tag tribal places with the UN planning zone they fall in and put the zone label points inside their zones.
Run after build/make_line.py (reads data/planning_zones.geojson)."""
import json, os
import numpy as np
from matplotlib.path import Path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FC = json.load(open(os.path.join(ROOT, "data/planning_zones.geojson")))["features"]
Z = [(f["properties"]["zone"], [[Path(np.array(r)) for r in poly] for poly in f["geometry"]["coordinates"]], f["properties"]["area_km2"]) for f in FC]
def inside(polys, x, y):
    return any(rs[0].contains_point((x, y)) and not any(r.contains_point((x, y)) for r in rs[1:]) for rs in polys)
def zone_at(x, y):
    for n, polys, _ in Z:
        if inside(polys, x, y): return n
    best, bd = None, 1e9          # on a boundary: nearest vertex
    for n, polys, _ in Z:
        for rs in polys:
            v = rs[0].vertices; d = ((v[:, 0] - x) ** 2 + (v[:, 1] - y) ** 2).min()
            if d < bd: bd, best = d, n
    return best
NOTES = {
 "Northern Steppe": "the southern Betpak-Dala north of the Chu, the Moiynkum sands between the Chu and the Talas and the piedmont plain north of the ISEZ belt; Boztorgoy winter pastures.",
 "Karatau": "the Karatau range and its foothills toward the Kyzylkum Fringe, north and west of the ISEZ belt along the Shymkent road; Kulan-Talaa plain.",
 "Talas Alatau": "the north slope and crest of the Talas Alatau above the Talas valley, from Aksu-Zhabagly on the Kazakh frontier east to the State Route 1 corridor: Aksay Plateau, Kara-Koyun, upper Besh-Tash and Kara-Suu, Manas Peak.",
 "Chatkal Highlands": "everything south of the Talas Alatau crest and west of the State Route 1 corridor and the Naryn gorge: the Chatkal valley and range, Sary-Chelek, the walnut forests, the Uzun-Akmat valley above the reservoir and the hills west of the Naryn down to the Fergana rim (Boz-Adyr, Kara-Jygach).",
 "Kyrgyz Range–Suusamyr": "the high Kyrgyz Range pastures east of the Kök-Bel road (since 2009) and the Suusamyr side east of the State Route 1 corridor: Toguz-Bulak, Otmek, the Western Karakol valley, Ak-Kyya.",
 "Toktogul–Naryn": "the mountains east of the State Route 1 corridor round the Toktogul basin and east of the Naryn gorge, up to the Fergana Range crest (the basin floor and gorge corridor are ISEZ); Kökjal clan.",
 "Fergana Rim": "the Fergana side of the Fergana Range above the ISEZ farm belt: Mailuu-Suu, the Kara-Unkur valley, Arslanbob and its walnut forest, Oruktu, Jangak-Bulak; highland Chubar.",
}
NAME_RU = {"Kyrgyz Range–Suusamyr": "Киргизский хребет – Суусамыр"}
for fn in ("data/settlements.json", "data/features.json"):
    D = json.load(open(os.path.join(ROOT, fn)))
    have = {p["id"] for p in D}
    if fn.endswith("settlements.json"):
        for n, _, _ in Z:
            zid = "zone-" + n.lower().replace("–", "-").replace(" ", "-")
            if zid not in have:
                D.append({"id": zid, "name": n, "name_ru": NAME_RU.get(n, n), "name_en": n, "kind": "zone-area", "zone": "ATR", "district": n,
                          "lat": 0, "lon": 0, "pop": None, "elev": None, "confidence": "placed", "note": "", "wiki": None})
    for p in D:
        if p.get("kind") == "zone-area" and p.get("district") in NOTES:
            n = p["district"]; polys = next(pp for nn, pp, _ in Z if nn == n); a = next(aa for nn, _, aa in Z if nn == n)
            # label point: the vertex-average of the largest ring, nudged to the interior if needed
            big = max((rs[0] for rs in polys), key=lambda r: len(r.vertices)); c = big.vertices.mean(0)
            if not inside(polys, *c):
                xs = np.linspace(big.vertices[:, 0].min(), big.vertices[:, 0].max(), 40); ys = np.linspace(big.vertices[:, 1].min(), big.vertices[:, 1].max(), 40)
                cand = [(x, y) for x in xs for y in ys if inside(polys, x, y)]
                c = min(cand, key=lambda q: (q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2)
            p["lon"], p["lat"] = round(float(c[0]), 3), round(float(c[1]), 3)
            p["note"] = f"UN planning zone ~{a:,} km²: " + NOTES[n]
        elif p.get("zone") == "ATR" and (p.get("district") or fn.endswith("settlements.json")):
            z = zone_at(p["lon"], p["lat"])
            if p.get("district") != z:
                print(f"  {p['id']:34} {p.get('district')} -> {z}"); p["district"] = z
    json.dump(D, open(os.path.join(ROOT, fn), "w"), ensure_ascii=False, indent=1)
