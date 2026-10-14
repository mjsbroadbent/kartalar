"""Fallback physical layer from Natural Earth (rivers, lakes) and neighbouring countries, clipped to the region.
Run: python3 build/make_base.py <natural-earth-vector/geojson folder>"""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NE = sys.argv[1]
BX = (65.5, 39.0, 78.5, 48.0)
def inbox(c): return BX[0] <= c[0] <= BX[2] and BX[1] <= c[1] <= BX[3]
def rnd(c): return [round(c[0], 3), round(c[1], 3)]
out = []
riv = json.load(open(os.path.join(NE, "ne_10m_rivers_lake_centerlines.geojson")))
for f in riv["features"]:
    g = f["geometry"]
    lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    keep = [[rnd(c) for c in l] for l in lines if any(inbox(c) for c in l)]
    if keep:
        out.append({"type": "Feature", "properties": {"k": "river", "rank": f["properties"].get("scalerank", 9)},
                    "geometry": {"type": "MultiLineString", "coordinates": keep}})
lak = json.load(open(os.path.join(NE, "ne_10m_lakes.geojson")))
for f in lak["features"]:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    keep = [[[rnd(c) for c in r] for r in p] for p in polys if any(inbox(c) for c in p[0])]
    if keep:
        out.append({"type": "Feature", "properties": {"k": "lake"}, "geometry": {"type": "MultiPolygon", "coordinates": keep}})
cty = json.load(open(os.path.join(NE, "ne_10m_admin_0_countries.geojson")))
names = {"KAZ": ("Kazakhstan", "Kazakstan", "Казахстан"), "KGZ": ("Kyrgyzstan", "Kırgızstan", "Киргизия"),
         "UZB": ("Uzbekistan", "Özbekstan", "Узбекистан"), "TJK": ("Tajikistan", "Tajikstan", "Таджикистан"), "CHN": ("China", "Kıtay", "Китай")}
for f in cty["features"]:
    a3 = f["properties"]["ADM0_A3"]
    if a3 not in names: continue
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    keep = [[[rnd(c) for c in r[::2] + [r[0]]] for r in p] for p in polys if any(inbox(c) for c in p[0])]
    if keep:
        n = names[a3]
        out.append({"type": "Feature", "properties": {"k": "country", "a3": a3, "name": n[0], "name_ir": n[1], "name_ru": n[2]},
                    "geometry": {"type": "MultiPolygon", "coordinates": keep}})
json.dump({"type": "FeatureCollection", "features": out}, open(os.path.join(ROOT, "data/physical.geojson"), "w"), separators=(",", ":"))
print(len(out), os.path.getsize(os.path.join(ROOT, "data/physical.geojson")) // 1024, "KB")
