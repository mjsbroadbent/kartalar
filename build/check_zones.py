"""Report places whose stated zone or district disagrees with the drawn zones (and fix 'placed' ones with --fix)."""
import json, sys
import numpy as np
from matplotlib.path import Path
fix = "--fix" in sys.argv
def polys(fc, key):
    out = []
    for f in json.load(open(fc))["features"]:
        for p in f["geometry"]["coordinates"]:
            out.append((f["properties"][key], [Path(np.array(r)) for r in p]))
    return out
Z = polys("data/zones.geojson", "zone"); D = polys("data/districts.geojson", "district"); I = polys("data/irad.geojson", "name")
def where(lon, lat, P):
    for k, rings in P:
        if rings[0].contains_point((lon, lat)) and not any(r.contains_point((lon, lat)) for r in rings[1:]):
            return k
    return None
for fn in ("data/settlements.json", "data/features.json"):
    data = json.load(open(fn)); n = 0
    for p in data:
        z = where(p["lon"], p["lat"], Z); d = where(p["lon"], p["lat"], D)
        if where(p["lon"], p["lat"], I) is None:
            print("OUTSIDE IRAD", fn, p["id"], p["lat"], p["lon"], p["confidence"]); continue
        z = z or "?"
        if z != p["zone"] and p["kind"] != "checkpoint":   # line checkpoints straddle the line
            n += 1
            print(f'{fn.split("/")[1][:4]} {p["id"]:38} said {p["zone"]:4} map {z:4} {p["confidence"]:10} {p["lat"]:.3f},{p["lon"]:.3f}')
            if fix and p["confidence"] == "placed": p["zone"] = z
        if fix and p["confidence"] == "placed" and z == "ISEZ" and "district" in p and d and p["kind"] not in ("district",) and p["district"] not in ("Talas", "Nurzhan", "Iyık Janyl") and p["district"] != d:
            p["district"] = d
    print(fn, "mismatches:", n)
    if fix: json.dump(data, open(fn, "w"), ensure_ascii=False, indent=1)
