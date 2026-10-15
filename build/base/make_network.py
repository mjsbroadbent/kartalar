"""The real road and railway network for the routers (format of the old Overpass export: {"ways": [{"k", "c"}]}), from
the extractor's transportation layer (before curation), including unclassified roads and tracks.
  python3 build/base/make_network.py <extract dir>/transportation.ndjson out.json"""
import json, sys
K = {"motorway": "road:motorway", "trunk": "road:trunk", "primary": "road:primary", "secondary": "road:secondary",
     "tertiary": "road:tertiary", "minor": "road:unclassified", "track": "road:track", "rail": "rail:rail"}
ways = []
for line in open(sys.argv[1]):
    f = json.loads(line); p = f["properties"]; k = K.get(p["class"])
    if not k or (k == "rail:rail" and f["tippecanoe"]["minzoom"] > 8): continue      # no sidings
    g = f["geometry"]; parts = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    for c in parts:
        ways.append({"k": k, "c": [[round(x, 5), round(y, 5)] for x, y in c]})
json.dump({"source": "OpenStreetMap contributors (ODbL), Geofabrik extracts", "ways": ways}, open(sys.argv[2], "w"))
print(len(ways))
