"""Named nature for the map and its search: data/nature.json

  python3 build/nature.py <extract dir> <curated dir> [fine dem]

Peaks, passes and glaciers come from the OpenStreetMap extract (build/base/extract.cpp), lakes and rivers from the curated
water layers (so a reservoir sits at its redrawn surface), and the ranges, valleys and deserts from the list below, whose
crest lines are pulled onto the high ground of the fine elevation grid. Every OSM name goes through translit.nature_name;
a lore feature of the same kind nearby (data/features.json) wins over the OSM one.
"""
import json, math, os, re, struct, sys
import numpy as np
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translit import nature_name   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT, CUR = sys.argv[1], sys.argv[2]
FINE = sys.argv[3] if len(sys.argv) > 3 else None
KY = 110.57

# ranges and other big landforms: the lore's spelling, a rough crest or axis (lon, lat) and what it is
LANDFORMS = [
    ("range", "Talas Alatau", [(70.95, 42.20), (71.6, 42.25), (72.3, 42.22), (72.9, 42.16), (73.4, 42.12)], "The range walling the Talas valley on the south, highest at Manas Peak (4,482 m) at its western end."),
    ("range", "Kyrgyz Range", [(72.3, 42.72), (73.0, 42.62), (73.7, 42.58), (74.4, 42.55), (74.95, 42.55)], "The long range between the Talas and Chu valleys, crossed by the Kök-Bel road."),
    ("range", "Karatau", [(68.35, 44.05), (68.9, 43.75), (69.5, 43.42), (70.1, 43.1), (70.65, 42.9)], "Low limestone and shale range trending NW from the western end of the Talas Alatau."),
    ("range", "Chatkal Range", [(70.05, 41.05), (70.45, 41.32), (70.9, 41.55), (71.3, 41.72), (71.7, 41.85)], "The range between the Chatkal valley and the Fergana basin."),
    ("range", "Pskem Range", [(70.2, 41.72), (70.55, 41.92), (70.95, 42.1)], "The range between the Pskem and Chatkal valleys on the Uzbek side."),
    ("range", "Ugam Range", [(69.75, 42.05), (70.1, 42.22), (70.45, 42.4)], "The range north of the Pskem along the Kazakh border."),
    ("range", "Fergana Range", [(72.75, 41.62), (73.2, 41.4), (73.6, 41.15), (74.0, 40.9)], "The range closing the Fergana basin on the north-east, with the Babash-Ata spur behind Arslanbob."),
    ("range", "Suusamyr Range", [(73.3, 42.05), (73.8, 42.0), (74.3, 41.98)], "The range on the south side of the Suusamyr valley."),
    ("range", "At-Oinok Range", [(72.95, 41.98), (73.25, 41.9), (73.6, 41.82)], "The range between the Toktogul basin and the upper Naryn gorges."),
    ("desert", "Moiynkum Desert", [(71.0, 44.55), (72.0, 44.35), (73.2, 44.25)], "Sand desert between the lower Talas and the Chu."),
    ("desert", "Betpak-Dala", [(69.8, 45.55), (70.9, 45.45), (72.2, 45.5)], "The clay and stone desert north of the Chu."),
    ("valley", "Talas Valley", [(71.2, 42.55), (71.8, 42.5), (72.4, 42.48), (72.9, 42.42)], "The valley of the Talas between the Kyrgyz Range and the Talas Alatau, the heart of Irad."),
    ("valley", "Chatkal Valley", [(70.95, 41.72), (71.3, 41.85), (71.7, 41.98), (72.0, 42.05)], "The long trough of the Chatkal between the Talas Alatau and the Chatkal Range."),
    ("valley", "Suusamyr Valley", [(73.2, 42.17), (73.7, 42.15), (74.2, 42.15)], "High summer-pasture valley between the Kyrgyz and Suusamyr ranges."),
    ("valley", "Ketmen-Töbö Basin", [(72.55, 41.85), (72.95, 41.78)], "The basin of the Toktogul Reservoir."),
    ("valley", "Chu Valley", [(73.2, 43.75), (73.9, 43.5), (74.6, 43.3)], "The lower valley of the Chu, below the Kazakh-Kyrgyz reach."),
    ("valley", "Fergana Valley", [(71.2, 40.92), (71.9, 40.9), (72.6, 40.88)], "The great irrigated basin to the south, in Uzbekistan and Kyrgyzstan."),
]


def load_dem(fn):
    b = open(fn, "rb").read()
    lon0, lat0, step = struct.unpack("<3d", b[8:32]); nx, ny = struct.unpack("<2i", b[32:40])
    return lon0, lat0, step, np.frombuffer(b[64:], dtype="<i2").reshape(ny, nx)


def crest(line, dem, radius_km, high):
    """pull each point of a range's line onto the highest ground within radius (valleys: the lowest)"""
    lon0, lat0, step, Z = dem if dem is not None else (0, 0, 1, np.zeros((1, 1)))
    out = []
    for x, y in line:
        if dem is None: out.append((x, y)); continue
        kx = 111.32 * math.cos(math.radians(y))
        rx, ry = int(radius_km / kx / step), int(radius_km / KY / step)
        i, j = int((x - lon0) / step), int((y - lat0) / step)
        if not (rx <= i < Z.shape[1] - rx and ry <= j < Z.shape[0] - ry): out.append((x, y)); continue
        W = Z[j - ry:j + ry + 1, i - rx:i + rx + 1].astype(float)
        W = W if high else -W
        jj, ii = np.unravel_index(np.argmax(W), W.shape)
        out.append((round(lon0 + (i - rx + ii) * step, 4), round(lat0 + (j - ry + jj) * step, 4)))
    # a smoothing pass so the label line does not zigzag between summits
    sm = out
    for _ in range(3):
        sm = [sm[0]] + [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4) for a, b, c in zip(sm, sm[1:], sm[2:])] + [sm[-1]]
    # densify with a Catmull-Rom curve so the label bends gently along the range
    P = np.array(sm); dense = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for t in np.linspace(0, 1, 8, endpoint=False):
            dense.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(P[-1])
    return [(round(float(x), 4), round(float(y), 4)) for x, y in dense]


def polys(fn):
    out = []
    for f in json.load(open(os.path.join(ROOT, fn)))["features"]:
        g = f["geometry"]; ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        out += [Path(np.array(p[0])) for p in ps]
    return out


def ring_area_km2(r):
    r = np.array(r); y0 = r[:, 1].mean(); kx = 111.32 * math.cos(math.radians(y0))
    x, y = r[:, 0] * kx, r[:, 1] * KY
    return abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) / 2


def label_point(rings):
    """a point well inside the polygon (outer ring, holes): the grid point farthest from its edges"""
    outer = np.array(rings[0]); P = [Path(np.array(r)) for r in rings]
    x0, y0 = outer.min(0); x1, y1 = outer.max(0)
    gx, gy = np.meshgrid(np.linspace(x0, x1, 24), np.linspace(y0, y1, 24)); G = np.c_[gx.ravel(), gy.ravel()]
    inside = P[0].contains_points(G)
    for h in P[1:]: inside &= ~h.contains_points(G)
    if not inside.any(): return outer.mean(0)
    G = G[inside]; kx = 111.32 * math.cos(math.radians(outer[:, 1].mean()))
    E = np.vstack([np.array(r) for r in rings])[::max(1, sum(len(r) for r in rings) // 400)]
    d = np.min(np.hypot((G[:, None, 0] - E[None, :, 0]) * kx, (G[:, None, 1] - E[None, :, 1]) * KY), axis=1)
    return G[np.argmax(d)]


def norm(s):
    s = (s or "").lower()
    for a, b in (("ö", "o"), ("ü", "u"), ("kh", "h"), ("dj", "j"), ("y", "i"), ("lake ", ""), (" lake", ""), (" pass", ""), (" peak", ""),
                 (" reservoir", ""), (" river", "")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s).replace("h", "")


def main():
    irad = polys("data/irad.geojson")
    def inside(x, y, pad=0.0):
        return any(p.contains_point((x, y), radius=pad) or p.contains_point((x, y), radius=-pad) for p in irad)
    lore = [f for f in json.load(open(os.path.join(ROOT, "data/features.json")))]
    LORE_KIND = {"peak": ("peak",), "pass": ("pass",), "glacier": ("glacier",), "lake": ("lake", "reservoir"), "reservoir": ("lake", "reservoir"),
                 "river": ("river-point",), "canal": ("river-point",)}
    def lore_has(kind, nm, x, y, near_km):
        kx = 111.32 * math.cos(math.radians(y))
        for f in lore:
            if f["kind"] not in LORE_KIND.get(kind, ()): continue
            d = math.hypot((f["lon"] - x) * kx, (f["lat"] - y) * KY)
            fn = norm(re.sub(r"\s*\(.*", "", f["name"]))
            if d < near_km or (fn and fn == norm(nm) and (d < 25 or kind in ("river", "canal"))): return True
            if kind in ("lake", "reservoir") and f.get("name") and nm and re.search(r"\b" + re.escape(nm.split()[0]) + r"\b", f.get("desc", "") + f.get("name", "")) and d < 10:
                return True       # "Kyzyl-Adyr Reservoir: former Kirov Reservoir"
        return False
    out, seen = [], {}
    def add(p):
        k = (p["kind"], norm(p["name"]))
        kx = 111.32 * math.cos(math.radians(p["lat"]))
        for q in seen.get(k, []):
            if math.hypot((q["lon"] - p["lon"]) * kx, (q["lat"] - p["lat"]) * KY) < (40 if p["kind"] in ("river", "canal") else 4): return
        if p["kind"] in ("peak", "pass") and any(q["kind"] == p["kind"] and math.hypot((q["lon"] - p["lon"]) * kx, (q["lat"] - p["lat"]) * KY) < 0.8 for q in out): return
        seen.setdefault(k, []).append(p); out.append(p)
    dropped = {"lore": 0, "no name": 0, "outside": 0, "small": 0}

    # peaks, passes, glaciers
    for line in open(os.path.join(EXT, "places.ndjson")):
        f = json.loads(line); pr = f["properties"]
        if pr["place"] not in ("peak", "pass", "glacier"): continue
        x, y = f["geometry"]["coordinates"]
        if not inside(x, y, 0.15): dropped["outside"] += 1; continue
        nm = nature_name(pr)
        if not nm: dropped["no name"] += 1; continue
        if lore_has(pr["place"], nm, x, y, 2.5 if pr["place"] == "pass" else 1.5): dropped["lore"] += 1; continue
        try: ele = round(float(re.sub(r"[^\d.]", "", pr.get("ele") or "") or "nan"))
        except ValueError: ele = None
        if ele is not None and (ele != ele or ele < 200 or ele > 7500): ele = None
        if pr["place"] == "pass" and not re.search(r"(Pass|Bel|Ashuu|Ashu|Davan)$", nm): nm += " Pass"
        add({"id": "osm-" + str(pr["id"]), "name": nm, "name_ru": pr.get("name_ru"), "kind": pr["place"], "lon": round(x, 5), "lat": round(y, 5),
             "elev": ele, "confidence": "osm", "abroad": not inside(x, y)})

    # lakes and reservoirs at their curated outlines, grouped by name
    lakes = {}
    for line in open(os.path.join(CUR, "water.ndjson")):
        f = json.loads(line); pr = f["properties"]
        if pr.get("class") != "lake" or not pr.get("name"): continue
        g = f["geometry"]; ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for rings in ps:
            a = ring_area_km2(rings[0]); c = np.array(rings[0]).mean(0)
            key = pr["name"]
            grp = next((G for G in lakes.setdefault(key, []) if math.hypot((G["c"][0] - c[0]) * 80, (G["c"][1] - c[1]) * KY) < 8), None)
            if grp is None: grp = {"c": c, "area": 0, "big": None, "bigA": 0}; lakes[key].append(grp)
            grp["area"] += a
            if a > grp["bigA"]: grp["bigA"] = a; grp["big"] = rings
    for nm, groups in lakes.items():
        for G in groups:
            x, y = label_point(G["big"])
            if G["area"] < 0.03: dropped["small"] += 1; continue
            if not inside(x, y, 0.1): dropped["outside"] += 1; continue
            kind = "reservoir" if "Reservoir" in nm else "lake"
            if lore_has(kind, nm, x, y, 1.0): dropped["lore"] += 1; continue
            add({"id": f"osm-lake-{norm(nm)}-{round(x, 2)}-{round(y, 2)}", "name": nm, "kind": kind, "lon": round(float(x), 5), "lat": round(float(y), 5),
                 "area": round(G["area"], 2), "confidence": "osm", "abroad": not inside(x, y)})

    # rivers and canals: one search entry per name and stretch inside Irad, at the middle of its longest piece
    rivers = {}
    for line in open(os.path.join(CUR, "waterway.ndjson")):
        f = json.loads(line); pr = f["properties"]
        if pr.get("class") not in ("river", "canal") or not pr.get("name"): continue
        g = f["geometry"]; cs = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for c in cs:
            C = np.array(c); kx = 111.32 * math.cos(math.radians(C[:, 1].mean()))
            L = float(np.hypot(np.diff(C[:, 0]) * kx, np.diff(C[:, 1]) * KY).sum())
            rivers.setdefault((pr["class"], pr["name"]), []).append((L, C))
    for (cls, nm), pieces in rivers.items():
        mids = [(L, C, C[len(C) // 2]) for L, C in pieces if inside(*C[len(C) // 2])]
        total = sum(L for L, C, m in mids)
        if total < (6 if cls == "river" else 10): dropped["small"] += 1; continue
        L, C, m = max(mids, key=lambda t: t[0])
        if lore_has(cls, nm, float(m[0]), float(m[1]), 0): dropped["lore"] += 1; continue
        allp = np.vstack([C for _, C, _ in mids])
        add({"id": f"osm-{cls}-{norm(nm)}", "name": nm + ("" if cls == "canal" or nm.endswith("Darya") else " River"), "kind": cls,
             "lon": round(float(m[0]), 5), "lat": round(float(m[1]), 5), "length": round(total),
             "bbox": [round(float(v), 3) for v in (*allp.min(0), *allp.max(0))], "confidence": "osm"})

    # ranges, deserts, valleys
    dem = load_dem(FINE) if FINE and os.path.exists(FINE) else None
    for kind, nm, line, desc in LANDFORMS:
        ln = crest(line, dem if kind in ("range", "valley") else None, 4 if kind == "range" else 3, kind == "range")
        mid = ln[len(ln) // 2]
        A = np.array(ln)
        add({"id": "land-" + norm(nm), "name": nm, "kind": kind, "lon": mid[0], "lat": mid[1], "line": ln, "desc": desc,
             "bbox": [round(float(v), 3) for v in (*A.min(0), *A.max(0))], "confidence": "lore"})

    json.dump(out, open(os.path.join(ROOT, "data/nature.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    import collections
    print(len(out), "features;", dict(collections.Counter(p["kind"] for p in out)), "; dropped", dropped)


if __name__ == "__main__":
    main()
