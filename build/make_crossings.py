"""Add a crossing point (Gendarmerie checkpoint and El-Choro post) wherever a road or the railway crosses the Qara-Chik line,
unless a checkpoint already sits within 5 km. Run after build/make_line.py."""
import json, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KX = 111.32 * math.cos(math.radians(42.5)); KY = 110.57
km = lambda a, b: math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)
line = json.load(open(os.path.join(ROOT, "data/qarachik.geojson")))["features"]
routes = json.load(open(os.path.join(ROOT, "data/routes.json")))
F = json.load(open(os.path.join(ROOT, "data/features.json")))
S = json.load(open(os.path.join(ROOT, "data/settlements.json")))
F = [f for f in F if not f.get("auto_crossing")]          # rebuild generated ones each run


def inter(p1, p2, p3, p4):
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if d == 0: return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


hits = []
for r in routes:
    if r["kind"] not in ("highway", "road", "railway"): continue
    c = r["coords"]
    for lf in line:
        L = lf["geometry"]["coordinates"]
        for a, b in zip(c, c[1:]):
            for p, q in zip(L, L[1:]):
                x = inter(a, b, p, q)
                if x: hits.append((x, r, lf["properties"]["sector"]))
# a line that ends at the frontier right beside a road (the road running along the frontier) is crossed there too
for lf in line:
    L = lf["geometry"]["coordinates"]
    for end in (L[:], L[::-1]):           # the last ~3 km of the piece at each end
        tail, acc = [end[0]], 0.0
        for a_, b_ in zip(end, end[1:]):
            n_ = max(1, int(km(a_, b_) / 0.1))
            for t_ in range(1, n_ + 1):
                tail.append((a_[0] + (b_[0] - a_[0]) * t_ / n_, a_[1] + (b_[1] - a_[1]) * t_ / n_))
            acc += km(a_, b_)
            if acc > 3: break
        for r in routes:
            if r["kind"] not in ("highway", "road", "railway"): continue
            c = r["coords"]
            best = min(((km(t, q), q) for t in tail for q in c), key=lambda z: z[0])
            if best[0] < 0.5 and not any(km(h[0], best[1]) < 2 for h in hits): hits.append((tuple(best[1]), r, lf["properties"]["sector"]))
existing = [f for f in F if f["kind"] == "checkpoint" or (f["kind"] == "border-crossing" and not f["id"].startswith("xing-"))]   # the line crossings, not the frontier ones
added = []
for x, r, sector in hits:
    if any(km(x, (f["lon"], f["lat"])) < 5 for f in existing + added): continue
    near = min((s for s in S if s["kind"] in ("city", "town", "village", "capital", "suburb")), key=lambda s: km(x, (s["lon"], s["lat"])))
    nm = r.get("crossing_name") or near["name"]
    f = {"id": "qarachik-crossing-" + (r.get("crossing_name", "").lower().replace(" ", "-").replace("-road", "") or near["id"]), "name": f"{nm} crossing", "name_ir": f"{nm} ötkölü", "name_ru": f"КПП «{r.get('crossing_name_ru') or near.get('name_ru') or nm}»",
         "kind": "checkpoint", "city": None, "zone": "ISEZ", "lat": round(x[1], 5), "lon": round(x[0], 5), "elev": None, "confidence": "placed",
         "note": f"Qara-Chik line crossing on the {r['name']} ({sector} sector): Gendarmerie checkpoint on the ISEZ side, El-Choro post on the tribal side.",
         "wiki": "Qara-Chik Demarcation Line", "auto_crossing": True, "status": "line"}
    if any(g["id"] == f["id"] for g in F + added): f["id"] += "-2"
    added.append(f)
F += added
json.dump(F, open(os.path.join(ROOT, "data/features.json"), "w"), ensure_ascii=False, indent=1)
allc = [f for f in F if f["kind"] == "checkpoint"]
print(f"{len(hits)} road/rail crossings of the line, {len(added)} new crossing points; {len(allc)} checkpoints in all")
for f in added: print("  ", f["name"], f["lat"], f["lon"], f["note"][:80])
