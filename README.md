# Attelkom Kartalar

Maps of Irad, the fictional Central Asian country of the Irad worldbuilding project: a Google-Maps-style site on real terrain, with Irad's own border, zones, districts, cities, villages, landmarks, roads and railways. In the setting it is Attelkom's map service (launched 15 September 2015).

Static site, no build step for the page itself. Deploy on GitHub Pages from the `main` branch root.

## How it works

- **Base map:** [MapLibre GL JS](https://maplibre.org/) (vendored in `vendor/`) with vector tiles from [OpenFreeMap](https://openfreemap.org/) (OpenStreetMap data). The style in `app.js` keeps land cover, water, roads, railways and buildings and hides every real place label and border, so only Iradi names appear. Shaded relief comes from the AWS Terrain Tiles (Mapzen terrarium).
- **Fallback:** `data/physical.geojson` (Natural Earth rivers, lakes and countries) draws under the tiles, so the map still reads if the tile servers are unreachable.
- **Irad's layers** come from the files in `data/`, drawn on top.
- **Labels** use the Noto Sans glyphs in `fonts/` (Latin, Latin Extended for ı ö ü ñ, Cyrillic).

## Data

| File | What it is |
|---|---|
| `data/settlements.json` | Cities, towns, villages, city quarters, districts and ATR planning zones (name in Iradi, English and Russian; kind; zone; district; coordinates; population and elevation where the lore gives them; wiki article) |
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

`build/make_geo.py` rasterises Natural Earth admin regions (Kyrgyzstan's Talas and Jalal-Abad, most of Kazakhstan's Jambyl, the Karatau side of Turkistan region, the Fergana rim) and the hand-drawn lore polygons for the ISEZ, combines them and traces the outlines. `build/check_zones.py` then checks every place against the zones (`--fix` corrects the zone of `placed` items). `build/make_base.py` makes the fallback physical layer.

```
git clone --depth 1 --filter=blob:none --sparse https://github.com/nvkelso/natural-earth-vector ne
(cd ne && git sparse-checkout set --no-cone /geojson/ne_10m_admin_1_states_provinces.geojson /geojson/ne_10m_admin_0_countries.geojson /geojson/ne_10m_rivers_lake_centerlines.geojson /geojson/ne_10m_lakes.geojson)
python3 build/make_geo.py ne/geojson/ne_10m_admin_1_states_provinces.geojson
python3 build/check_zones.py --fix
python3 build/make_base.py ne/geojson
```

## The Qara-Chik line from real terrain

`tools/dem-export.html` saves an elevation grid for Irad's area (Mapzen/AWS Terrain Tiles, every 0.005°). `build/make_line.py <irad-dem.bin> <irad-osm-roads.json>` then rebuilds the ISEZ, the districts and the line itself, following the wiki's description of each sector: the Talas Alatau foothills above the valley floor (bulging around the Sary-Bulak corridor and the lore's own ISEZ villages), the edge of the irrigated Talas and Chu plains (canals, the Turksib corridor, the oil-field and rail corridors), the Karatau foothills, and the crests of the Naryn catchment below the Toktogul dam. `build/make_crossings.py` adds a crossing point wherever a road or the railway crosses the line. Run order: `make_geo.py` (border) → `make_line.py` → `make_crossings.py` → `check_zones.py --fix`.

## Fitting routes to real roads

`tools/osm-export.html` downloads the main roads, railways and rivers for Irad's area from OpenStreetMap (Overpass API) and saves them as one file. `build/snap_routes.py <that file>` redraws every highway, road, railway and canal in `data/routes.json` along the real network, keeping the lore's waypoints in `coords_lore`. Invented railways with no real track follow the valley road; pipelines and power lines stay as drawn. Re-run `build/make_geo.py` and `build/check_zones.py` afterwards.

## Features

- Search across every place in Iradi, English or Russian (accents optional), with keyboard navigation
- Place cards: names in three languages, kind, zone and district, population, elevation, coordinates, link to the Irad Wiki article, share link (`?p=<id>`), nearby places
- Tap anywhere for a dropped pin with zone, district and the nearest settlement
- Category chips (churches, sport and markets, transport, public services, sights, nature)
- Layer toggles, three interface languages, shareable map position in the URL (`#map=zoom/lat/lon`)
- Boz-Korgon shows as a restricted area; the tribal regions carry a "limited map data" notice

## Credits

Map data © OpenStreetMap contributors (ODbL), tiles by OpenFreeMap, terrain from Mapzen/AWS Terrain Tiles, Natural Earth (public domain), MapLibre GL JS (BSD-3-Clause), Noto Sans (OFL) via OpenMapTiles fonts.
