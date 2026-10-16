# Attelkom Kartalar

Maps of Irad, the fictional Central Asian country of the Irad worldbuilding project: a Google-Maps-style site on real terrain, with Irad's own border, zones, districts, cities, villages, landmarks, roads and railways. In the setting it is Attelkom's map service (launched 15 September 2015).

Static site, no build step for the page itself. Deploy on GitHub Pages from the `main` branch root.

## How it works

- **Base map:** [MapLibre GL JS](https://maplibre.org/) (vendored in `vendor/`) with Kartalar's own tile archives in `tiles/`, served by this site and read by `vendor/kt-pmtiles.js` (a small PMTiles reader, protocol `kt://`). Nothing is loaded from other servers.
  - `tiles/area.pmtiles` (water, land cover, land use, parks, airfields), `tiles/lines.pmtiles` (roads, railways, waterways), `tiles/detail.pmtiles` (buildings and the city plans), `tiles/dem.pmtiles` (terrain for the hill shading).
  - Built by `build/base/build_base.sh` from OpenStreetMap country extracts (Geofabrik: Kazakhstan, Kyrgyzstan, Uzbekistan) and the terrain export (`tools/terrain-export.html`), clipped to 67.5–75.5° E, 40.2–46.5° N. Buildings, minor roads and paths are kept only in Irad and a 6 km fringe. No real names or borders are in the tiles.
  - The base is edited for Irad while it is built (`build/base/curate.py`): the city plans (`data/city`) are baked in over the real towns, real roads and railways that an Irad route follows are cut out (the route layer draws them), other railways inside Irad are drawn as disused, and Taraz is cut back to a small town. Rivers, canals and lakes carry their names in Irad's spelling; the pieces of each named river are joined end to end and a smoothed copy (the `waterlabel` layer) carries the river's name.
  - Rebuild the tiles after the city plans or `data/routes.json` change.
- **Fallback:** `data/physical.geojson` (Natural Earth rivers, lakes and countries) draws under the tiles, outside the tiled box.
- **Irad's layers** come from the files in `data/`, drawn on top.
- **Labels** use the Noto Sans glyphs in `fonts/` (Latin, Latin Extended for ı ö ü ñ, Cyrillic).

## Interface

The map app is Attelkom's: the brand comes from attelkom.net (theme v2.3 by WebStudio Talas): Attelkom green and dark
forest green, orange for the buttons that matter, Montserrat for headings and labels (`vendor/montserrat`, OFL), the 2019
app-icon logo (`img/attelkom-2019.svg`, `img/attelkom-tile.svg`). Places open in a side panel on wide screens and a
bottom sheet on phones, with Overview, Reviews and About tabs, saved places in the menu, and the shared Attelkom personal
account sign-in (which, in-world, always fails with a billing error). Businesses (restaurants, cafés, hotels, shops) and
reviews have a data format ready in `docs/PLACES.md`; add `?demo` to preview sample listings.

## Data

| File | What it is |
|---|---|
| `data/settlements.json` | Cities, towns, villages, city quarters, districts and ATR planning zones (name in Iradi, English and Russian; kind; zone; district; coordinates; population and elevation where the lore gives them; wiki article) |
| `data/nature.json` | Named nature for labels and search (by `build/nature.py`): peaks, passes and glaciers from OpenStreetMap; lakes and reservoirs at their curated outlines; one entry per river and canal (with its length in Irad); and the ranges, valleys and deserts, whose label lines follow the crests of the fine elevation grid. Names go through `build/translit.py` (Irad's Latin spelling; Russian mountaineers' and Soviet names are left off); a lore feature of the same kind nearby wins |
| `build/audit_infra.py` | Lists the real infrastructure the OpenStreetMap base leaves inside Irad (aerodromes and runways, mines, quarries, works, military areas, old border posts) with the nearest lore feature; `SITES` in `build/base/curate.py` removes what is not there in Irad (working pits under the clans' mining moratorium, demolished Aulie-Ata works) and draws Soviet leftovers faint as disused |
| `data/real_places.json` | The real towns and villages (from OpenStreetMap, by `build/real_places.py`): real names in Irad's Latin spelling; places renamed after people in independent Kazakhstan or Kyrgyzstan get Iradi names; Taraz is Aulie-Ata; lore places take precedence; outside Irad, neighbouring towns and cities as reference labels |
| `data/features.json` | Landmarks, churches, markets, stations, checkpoints, dams, mines, peaks, passes, lakes, parks and other features |
| `data/routes.json` | Highways, roads, the Irad Temir Jolu railway, pipelines, canals and power lines as lines |
| `data/irad.geojson` | Irad's border |
| `data/zones.geojson` | The ISEZ and the Autonomous Tribal Regions (the ISEZ outline is drawn as the Qara-Chik line) |
| `data/districts.geojson` | The five ISEZ districts |
| `data/qarachik.geojson` | The Qara-Chik Demarcation Line, in pieces tagged by sector and by what each piece follows (crest, river, canal, foothills, surveyed line) |
| `data/restricted_zone.geojson` | The 12 km restricted-weapons zone either side of the line |
| `data/settlements_report.md`, `data/features_report.md` | How each place was positioned, contradictions found in the lore and how they were resolved |

Each place has a `confidence`: `anchor` (fixed by decision), `real-place` (a real place of the same name), `stated` (derived from distances or directions in the lore) or `placed` (a consistent guess). Move `placed` ones freely.

To add a place, add an object to `settlements.json` or `features.json` with the same fields; it appears on the map and in search.

## Rebuilding the border and zones

`build/make_geo.py` rasterises Natural Earth admin regions (Kyrgyzstan's Talas and Jalal-Abad, most of Kazakhstan's Jambyl, the Karatau side of Turkistan region, the Fergana rim above the foot of the hills, ~950 m, with `FINE_DEM` set; the Andijan oases and the Namangan piedmont towns stay in Uzbekistan) and the hand-drawn lore polygons for the ISEZ, combines them and traces the outlines. `build/check_zones.py` then checks every place against the zones (`--fix` corrects the zone of `placed` items). `build/make_base.py` makes the fallback physical layer.

```
git clone --depth 1 --filter=blob:none --sparse https://github.com/nvkelso/natural-earth-vector ne
(cd ne && git sparse-checkout set --no-cone /geojson/ne_10m_admin_1_states_provinces.geojson /geojson/ne_10m_admin_0_countries.geojson /geojson/ne_10m_rivers_lake_centerlines.geojson /geojson/ne_10m_lakes.geojson)
python3 build/make_geo.py ne/geojson/ne_10m_admin_1_states_provinces.geojson
python3 build/check_zones.py --fix
python3 build/make_base.py ne/geojson
```

## The Qara-Chik line from real terrain

`tools/dem-export.html` saves an elevation grid for Irad's area (Mapzen/AWS Terrain Tiles, every 0.005°). `build/make_line.py <irad-dem.bin> <irad-osm-roads.json>` then rebuilds the ISEZ, the districts and the line itself, following the wiki's description of each sector: the Talas Alatau foothills above the valley floor (bulging around the Sary-Bulak corridor and the lore's own ISEZ villages), the edge of the irrigated Talas and Chu plains (canals, the Turksib corridor, the oil-field and rail corridors), the Karatau foothills, and the crests of the Naryn catchment below the Toktogul dam. `build/make_crossings.py` adds a crossing point wherever a road or the railway crosses the line. Run order: `make_geo.py` (border), then `build/rebuild.sh <irad-dem.bin> <irad-osm-roads.json>`, which runs `route_terrain.py` → `derive_lines.py` → `make_line.py` → `place_checkpoints.py` → `make_crossings.py` → `check_zones.py --fix`.

## Fitting routes to real roads

`tools/osm-export.html` downloads the main roads, railways and rivers for Irad's area from OpenStreetMap (Overpass API) and saves them as one file. `build/snap_routes.py <that file>` redraws every highway, road, railway and canal in `data/routes.json` along the real network, keeping the lore's waypoints in `coords_lore`. Invented railways with no real track follow the valley road; pipelines and power lines stay as drawn. Re-run `build/make_geo.py` and `build/check_zones.py` afterwards.

`build/route_terrain.py` then lays the routes listed in `build/route_specs.json` over the real terrain: each is a cheapest path through the real road (or rail) network plus a fine terrain grid where new road would have to be built, with costs for steep climbs (beyond the route's ruling grade), steep side slopes and altitude. Real main roads are kept as they are; new-built stretches are straightened, rounded and given hairpins where they still climb too fast. `build/derive_lines.py` cuts the Otmek tunnel into State Route 1 and lays the pipelines and power lines along their routes.

`tools/city-export.html` downloads the streets, buildings, land use and parks of the donor cities (Bishkek for Talas, Shymkent for Nurzhan, Osh for Iyık Janyl). `build/make_cities.py` moves each donor plan onto its Iradi site (Shymkent turned 45° so its refinery district lies east; Osh mirrored so its sacred hill becomes Cathedral Hill on the east bank of the Naryn), clips it to the ground the city can occupy (valley floor, off the airfield, clear of Tash-Kömür), drops every real name, and writes `data/city/` (an overview per city and 0.02° detail tiles). It also re-lays the lore routes and railways through each city along the borrowed main streets and tracks, and moves the stations onto them. The map hides the real base map inside each city footprint and draws the borrowed plan instead.

### Editing a road

A road edit (a via point or a `fixed` stretch in `build/route_specs.json`, or a city's `drop_streets` / `add_streets` in
`build/make_cities.py`) does not need the full rebuild:

1. `build/rebuild_roads.sh <dem.bin> <osm.json> <city dir> <route ids>`: re-routes only those roads and the roads that
   start on them, then re-lays the routes along the city streets (about 4 minutes; it starts from
   `build/.cache/routes_raw.json`, the routes before the last city re-lay, which `build/rebuild.sh` saves).
2. `build/preview_routes.py out.png <zoom/lat/lon>`: a screenshot in seconds with the new road lines drawn in colour, the
   committed ones dashed grey and the city plans' streets in dark red. The base tiles may still be the old ones.
3. When it looks right: `build/rebuild_roads.sh --tiles-only <tools dir> <work dir>` refreshes only `tiles/lines.pmtiles`
   and `tiles/detail.pmtiles` (about 2 minutes; `CURATE_LAYERS=transportation` for `curate.py`). Or add
   `--tiles <tools dir> <work dir>` to step 1 to do both in one go.

Run the full `build/rebuild.sh` when a road crosses the Qara-Chik line or the frontier, or a place may have moved.

## Features

- Search across every place in Iradi, English or Russian (accents optional), with keyboard navigation
- Place cards: names in three languages, kind, zone and district, population, elevation, coordinates, link to the Irad Wiki article, share link (`?p=<id>`), nearby places
- Tap anywhere for a dropped pin with zone, district and the nearest settlement
- Category chips (churches, sport and markets, transport, public services, sights, nature)
- Layer toggles, three interface languages, shareable map position in the URL (`#map=zoom/lat/lon`)
- Boz-Korgon shows as a restricted area; the tribal regions carry a "limited map data" notice

## Credits

Map data © OpenStreetMap contributors (ODbL), terrain from Mapzen Terrarium (AWS Terrain Tiles), Natural Earth (public domain), MapLibre GL JS (BSD-3-Clause), Noto Sans (OFL) via OpenMapTiles fonts, Inter (OFL). Tiles built with tippecanoe (BSD-2-Clause) and libosmium (BSL-1.0).
