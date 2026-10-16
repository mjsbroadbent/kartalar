#!/bin/sh
# Fast rebuild after a road edit (build/route_specs.json or a city's drop_streets/add_streets): only the steps a road
# change reaches. The full build/rebuild.sh is still the check before a commit when a road crosses the Qara-Chik line
# or the frontier (crossings, zones) or a place may have moved.
#   build/rebuild_roads.sh <dem.bin> <osm.json> <city dir> [route ids, comma-separated] [--tiles <tools dir> <work dir>]
#   build/rebuild_roads.sh --tiles-only <tools dir> <work dir>
# Same ROUTE_DEM / ROUTE_NET / ROUTE_RIVERS as rebuild.sh. With route ids, only those roads (and the roads that start
# on them or borrow their line) are re-routed; without, every road. --tiles then refreshes tiles/lines.pmtiles and
# tiles/detail.pmtiles (the work dir is build_base.sh's: <work>/ext and <work>/cur from the last full base build).
# Check a road before the tiles with build/preview_routes.py: the app draws the routes from data/routes.json.
set -e
cd "$(dirname "$0")/.."
t0=$(date +%s); step() { echo "== $1 ($(( $(date +%s) - t0 ))s)"; }
tiles() {   # <tools dir> <work dir>
  T="$1"; W="$2"
  [ -d "$W/ext" ] && [ -d "$W/cur" ] || { echo "no $W/ext or $W/cur: run build/base/build_base.sh once first"; exit 1; }
  CURATE_LAYERS=transportation python3 build/base/curate.py "$W/ext" "$W/cur" > /dev/null
  TC="$T/tippecanoe/tippecanoe -q --force -Z3 --drop-densest-as-needed --simplification=4 --no-feature-limit --maximum-tile-bytes=1000000 --read-parallel -A ©OpenStreetMap"
  C="$W/cur"
  $TC -z14 -o tiles/lines.pmtiles -n "Kartalar lines" $C/transportation.ndjson $C/waterway.ndjson $C/waterlabel.ndjson
  step "lines tiles"
  $TC -z14 -o tiles/detail.pmtiles -n "Kartalar detail" $C/building.ndjson $C/city.ndjson
  step "detail tiles"
}
# only the tiles, after a preview looked right: build/rebuild_roads.sh --tiles-only <tools dir> <work dir>
if [ "$1" = "--tiles-only" ]; then tiles "$2" "$3"; exit 0; fi

DEM="$1"; OSM="$2"; CDIR="$3"; shift 3
IDS=""; if [ -n "$1" ] && [ "$1" != "--tiles" ]; then IDS="$1"; shift; fi
RDEM="${ROUTE_DEM:-$DEM}"; RNET="${ROUTE_NET:-$OSM}"

if [ -n "$IDS" ]; then
  # add every road that depends on a changed one (prefix / start_on / end_on), until nothing more is added
  IDS=$(python3 - "$IDS" <<'EOF'
import json, sys
ids = set(sys.argv[1].split(","))
specs = json.load(open("build/route_specs.json"))
known = {s["id"] for s in specs}
bad = ids - known
if bad: sys.exit(f"unknown route id(s): {', '.join(sorted(bad))}")
while True:
    more = {s["id"] for s in specs if s["id"] not in ids and
            ({s.get("start_on"), s.get("end_on"), (s.get("prefix") or {}).get("route")} & ids)}
    if not more: break
    ids |= more
print(",".join(sorted(ids)))
EOF
)
  echo "routes: $IDS"
fi
# The city re-lay and the smoothing passes are not meant to run twice over the same line (a road drifts), so start
# from the routes as they were before the last city re-lay, saved by rebuild.sh (and by this script).
RAW=build/.cache/routes_raw.json
[ -f "$RAW" ] || { echo "no $RAW: run build/rebuild.sh once first"; exit 1; }
cp "$RAW" data/routes.json
step "roads over the terrain"
if [ -n "$IDS" ]; then python3 build/route_terrain.py "$RDEM" "$RNET" "$IDS"; else python3 build/route_terrain.py "$RDEM" "$RNET"; fi
cp data/routes.json "$RAW"
step "lines along the routes";python3 build/derive_lines.py
step "city plans, routes re-laid along streets"; python3 build/make_cities.py "$RDEM" "$OSM" "$CDIR"
step "dehook"; python3 build/dehook.py "$RDEM"
step "railways smoothed"; python3 build/route_rail.py "$RDEM" "$RNET" --smooth
step "stations"; python3 build/place_sites.py "$CDIR"
step "routes done"

if [ "$1" = "--tiles" ]; then tiles "$2" "$3"; fi
