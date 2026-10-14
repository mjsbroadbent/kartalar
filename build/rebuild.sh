#!/bin/sh
# Rebuild the routes, the Qara-Chik line, the zones and the checkpoints, in order.
# Usage: build/rebuild.sh irad-dem.bin irad-osm-roads.json
set -e
cd "$(dirname "$0")/.."
DEM="$1"; OSM="$2"
python3 build/route_terrain.py "$DEM" "$OSM"     # roads and railways over the terrain (build/route_specs.json)
python3 build/derive_lines.py                   # Otmek tunnel; pipelines and power lines along their routes
python3 build/make_line.py "$DEM" "$OSM"        # ISEZ/ATR, districts, Qara-Chik line, restricted zone
python3 build/place_checkpoints.py              # named checkpoints onto the line
python3 build/make_crossings.py                 # a crossing point wherever a road or railway crosses the line
python3 build/check_zones.py --fix              # placed places take the zone they fall in
python3 build/tag_zones.py                      # tribal places tagged with their UN planning zone
