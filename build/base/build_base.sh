#!/bin/sh
# Build Kartalar's own base map (tiles/*.pmtiles) from OpenStreetMap country extracts and the terrain export.
#   build/base/build_base.sh <tools dir> <work dir> [terrain.bin] -- a.osm.pbf b.osm.pbf ...
# <tools dir> holds libosmium/, protozero/ and tippecanoe/ (git clones; tippecanoe built with make).
# Run it after data/city and data/routes.json change (the cities and the Irad routes are baked into the tiles).
set -e
T="$1"; W="$2"; shift 2
DEM=""; if [ "$1" != "--" ]; then DEM="$1"; shift; fi
shift   # --
B=$(dirname "$0"); ROOT=$(cd "$B/../.." && pwd)
mkdir -p "$W/ext" "$W/cur" "$ROOT/tiles"
[ -x "$T/extract" ] || g++ -O2 -std=c++17 -I "$T/libosmium/include" -I "$T/protozero/include" "$B/extract.cpp" -o "$T/extract" -lz -lexpat -lbz2 -pthread
python3 "$B/make_mask.py" "$W/mask.bin"
rm -f "$W"/ext/*.ndjson; "$T/extract" "$W/mask.bin" "$W/ext" "$@"
python3 "$B/curate.py" "$W/ext" "$W/cur"
TC="$T/tippecanoe/tippecanoe -q --force -Z3 --drop-densest-as-needed --simplification=4 --no-feature-limit --maximum-tile-bytes=1000000 --read-parallel -A ©OpenStreetMap"
C="$W/cur"
$TC -z12 --detect-shared-borders -o "$ROOT/tiles/area.pmtiles" -n "Kartalar areas" $C/water.ndjson $C/landcover.ndjson $C/landuse.ndjson $C/park.ndjson $C/aeroway.ndjson
$TC -z14 -o "$ROOT/tiles/lines.pmtiles" -n "Kartalar lines" $C/transportation.ndjson $C/waterway.ndjson
$TC -z14 -o "$ROOT/tiles/detail.pmtiles" -n "Kartalar detail" $C/building.ndjson $C/city.ndjson
if [ -n "$DEM" ]; then python3 "$B/make_dem.py" "$DEM" "$ROOT/tiles"; fi
ls -la "$ROOT/tiles"
