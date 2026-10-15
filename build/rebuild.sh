#!/bin/sh
# Rebuild the routes, the Qara-Chik line, the zones and the checkpoints, in order.
# Usage: build/rebuild.sh irad-dem.bin irad-osm-roads.json [dir with city-<donor>.json from tools/city-export.html]
# The routers use a finer terrain grid and the full road network when given (build/base/make_fine_dem.py and
# make_network.py): ROUTE_DEM=fine-dem.bin ROUTE_NET=network.json ROUTE_RIVERS=<extract>/waterway.ndjson
set -e
cd "$(dirname "$0")/.."
DEM="$1"; OSM="$2"
RDEM="${ROUTE_DEM:-$DEM}"; RNET="${ROUTE_NET:-$OSM}"
python3 build/route_terrain.py "$RDEM" "$RNET"   # roads over the terrain (build/route_specs.json)
python3 build/route_rail.py "$RDEM" "$RNET"     # railways: real track, new track over the terrain, turnouts, minimum radii
python3 build/derive_lines.py                   # Otmek tunnel; pipelines and power lines along their routes
if [ -n "$3" ]; then python3 build/make_cities.py "$RDEM" "$OSM" "$3"; fi   # borrowed city plans; routes re-laid along their streets
python3 build/dehook.py "$RDEM"                 # no hooks or jogs left by the city re-lay
python3 build/route_rail.py "$RDEM" "$RNET" --smooth
if [ -n "$3" ]; then python3 build/place_sites.py "$3"; fi   # railways smoothed again after the city re-lay; stations onto the track
python3 build/make_line.py "$DEM" "$OSM"        # ISEZ/ATR, districts, Qara-Chik line, restricted zone
python3 build/place_checkpoints.py              # named checkpoints onto the line
python3 build/make_crossings.py                 # a crossing point wherever a road or railway crosses the line
python3 build/check_zones.py --fix              # placed places take the zone they fall in
python3 build/tag_zones.py                      # tribal places tagged with their UN planning zone
python3 build/make_bozkorgon.py "$DEM"                    # Boz-Korgon restricted area from the terrain
# The base map tiles (tiles/*.pmtiles) bake in the city plans and the Irad routes: rebuild them afterwards with
#   build/base/build_base.sh <tools dir> <work dir> [kartalar-terrain.bin] -- <country>.osm.pbf ...
