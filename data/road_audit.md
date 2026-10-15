# Road audit (build/audit_roads.py)

Grades are over 500 m windows from the ~90 m terrain grid; GRADE counts only new-built stretches. *Real* = within 40 m of an OpenStreetMap road or track.
Flags: GRADE steeper than the road's ruling grade + 2 points for more than 1 km in all; SIDE new-built over 1 km on side slopes over 30%;
BRIDGE a crossing of a river or canal with no real road crossing within 200 m; BEND a turn over 100 degrees on easy ground;
PARALLEL new road running close beside a real road; END an end more than 1 km from any settlement, feature, other route or real road; EXIT where the road leaves Irad with no real road carrying on.

| road | km | real | steepest | flags |
|---|---|---|---|---|
| trans-talas-highway | 194 | 60% | 15% | 3 |
| fergana-mountain-transit-highway | 355 | 93% | 39% | 7 |
| iyik-janyl-branch-road | 1 | 3% | 31% | 0 |
| talas-nurzhan-road | 339 | 94% | 10% | 4 |
| kok-bel-road | 220 | 68% | 25% | 8 |
| chu-highway | 117 | 85% | 8% | 1 |
| boz-korgon-branch | 42 | 3% | 5% | 2 |
| sary-bulak-road | 29 | 6% | 24% | 2 |
| chatkal-smelter-road | 46 | 43% | 12% | 3 |
| qara-chik-road | 43 | 11% | 26% | 5 |
| kenkol-military-road | 31 | 33% | 26% | 5 |
| karakol-road | 22 | 61% | 9% | 2 |
| lower-naryn-uzbek-road | 39 | 94% | 10% | 1 |
| fergana-rim-road | 97 | 93% | 9% | 1 |
| mailuu-suu-road | 22 | 45% | 23% | 0 |
| arslanbob-road | 49 | 92% | 24% | 0 |

## Trans-Talas Highway (`trans-talas-highway`)

194 km, 60% on real roads, highest 1237 m, steepest 500 m 15.4% (ruling 5%)
- start: Talas North Terminal 1.3 km / route 120.7 km / real road 0.09 km
- end: General Staff complex 0.3 km / route 0.0 km / real road 0.01 km
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**
- **BRIDGE new canal crossing at 72.2020,42.5202**
- **BRIDGE new canal crossing at 72.1696,42.5274**

## Fergana Mountain Transit Highway (State Route 1) (`fergana-mountain-transit-highway`)

355 km, 93% on real roads, highest 3389 m, steepest 500 m 39.1% (ruling 5%)
- start: Talas 0.2 km / route 0.0 km / real road 0.01 km
- end: Tash-Kömür 0.2 km / route 0.0 km / real road 0.00 km
- **GRADE 5.3 km over 7% (max 39%)**
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**
- **BRIDGE new river crossing at 73.1528,42.2816**
- **BRIDGE new river crossing at 72.2692,42.5301**
- **BRIDGE new river crossing at 72.3747,42.5118**
- **BRIDGE new river crossing at 72.3754,42.5116**
- **BEND 119 deg at 73.2517,42.2075**

## Cathedral Hill road (`iyik-janyl-branch-road`)

1 km, 3% on real roads, highest 814 m, steepest 500 m 31.2% (ruling 6%)
- start: Irad Palace of Art 1.1 km / route 0.1 km / real road 0.01 km
- end: Cathedral Hill 0.0 km / route 1.2 km / real road 1.03 km

## Talas-Nurzhan road (lowland route) (`talas-nurzhan-road`)

339 km, 94% on real roads, highest 1239 m, steepest 500 m 10.3% (ruling 6%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Nurzhan central square 0.1 km / route 0.0 km / real road 0.03 km
- **BRIDGE new canal crossing at 72.2020,42.5202**
- **BRIDGE new canal crossing at 72.1696,42.5274**
- **BRIDGE new river crossing at 71.5988,42.6504**
- **BRIDGE new canal crossing at 73.7568,43.5702**

## Kök-Bel road (`kok-bel-road`)

220 km, 68% on real roads, highest 2741 m, steepest 500 m 25.4% (ruling 6%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Nurzhan central square 0.1 km / route 0.0 km / real road 0.03 km
- **GRADE 11.0 km over 8% (max 25%)**
- **SIDE 3.1 km new-built on >30% slopes**
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**
- **BRIDGE new river crossing at 72.2692,42.5301**
- **BRIDGE new river crossing at 72.3747,42.5118**
- **BRIDGE new river crossing at 72.3754,42.5116**
- **BRIDGE new canal crossing at 73.7568,43.5702**
- **BEND 100 deg at 72.5823,42.4839**

## Chu highway (Nurzhan - Chu Gate) (`chu-highway`)

117 km, 85% on real roads, highest 1029 m, steepest 500 m 7.5% (ruling 5%)
- start: Nurzhan central square 0.1 km / route 0.0 km / real road 0.03 km
- end: Chu Gate crossing 0.0 km / route 59.7 km / real road 0.39 km
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**

## Boz-Korgon branch road (`boz-korgon-branch`)

42 km, 3% on real roads, highest 883 m, steepest 500 m 4.7% (ruling 5%)
- start: Nurzhan Refinery No. 1 0.6 km / route 5.0 km / real road 1.01 km
- end: Boz-Korgon 0.5 km / route 26.4 km / real road 2.76 km
- **PARALLEL 1.5 km new-built 40-250 m beside a real road**
- **BRIDGE new canal crossing at 73.9263,43.6000**

## Sary-Bulak branch road (`sary-bulak-road`)

29 km, 6% on real roads, highest 1968 m, steepest 500 m 24.4% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Sary-Bulak Antimony Works (SBAW) 0.0 km / route 9.8 km / real road 7.33 km
- **GRADE 4.5 km over 9% (max 24%)**
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Chatkal smelter road (`chatkal-smelter-road`)

46 km, 43% on real roads, highest 1630 m, steepest 500 m 11.8% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Kemer Antimony Mine 0.0 km / route 12.7 km / real road 0.05 km
- **PARALLEL 1.9 km new-built 40-250 m beside a real road**
- **BRIDGE new canal crossing at 72.2020,42.5202**
- **BRIDGE new canal crossing at 72.1696,42.5274**

## Talas - Qara-Chik checkpoint road (`qara-chik-road`)

43 km, 11% on real roads, highest 2538 m, steepest 500 m 26.2% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Köl-Sai glacial lake 1.7 km / route 18.8 km / real road 8.33 km
- **GRADE 7.0 km over 9% (max 26%)**
- **SIDE 4.8 km new-built on >30% slopes**
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**
- **BRIDGE new river crossing at 72.2692,42.5301**
- **END at 72.5100,42.3150 is 1.7 km from anything**

## Kenkol Pass road (`kenkol-military-road`)

31 km, 33% on real roads, highest 2117 m, steepest 500 m 26.4% (ruling 9%)
- start: Kara-Bulak kurgans 4.6 km / route 0.0 km / real road 0.00 km
- end: Kenkol Pass 0.0 km / route 17.8 km / real road 4.16 km
- **BRIDGE new canal crossing at 71.8669,42.5432**
- **BRIDGE new river crossing at 71.8190,42.4007**
- **BRIDGE new river crossing at 71.8177,42.3963**
- **BRIDGE new river crossing at 71.8000,42.3764**
- **BRIDGE new river crossing at 71.8001,42.3765**

## Western Karakol valley road (`karakol-road`)

22 km, 61% on real roads, highest 2638 m, steepest 500 m 8.6% (ruling 8%)
- start: Suusamyr crossing 1.1 km / route 0.0 km / real road 0.00 km
- end: Karakol 0.0 km / route 18.9 km / real road 2.49 km
- **BRIDGE new river crossing at 73.4256,42.1371**
- **BRIDGE new river crossing at 73.4270,42.1351**

## Tash-Kömür - Uzbek border road (`lower-naryn-uzbek-road`)

39 km, 94% on real roads, highest 664 m, steepest 500 m 9.9% (ruling 6%)
- start: Tash-Kömür 0.2 km / route 0.0 km / real road 0.00 km
- end: Naryn River (leaving Irad) 2.7 km / route 8.9 km / real road 0.01 km
- **BEND 101 deg at 72.1892,41.1952**

## Fergana rim road (Tash-Kömür – Bazar-Korgon) (`fergana-rim-road`)

97 km, 93% on real roads, highest 821 m, steepest 500 m 8.9% (ruling 6%)
- start: Tash-Kömür 0.0 km / route 0.2 km / real road 0.12 km
- end: Bazar-Korgon 0.0 km / route 0.0 km / real road 0.01 km
- **PARALLEL 1.9 km new-built 40-250 m beside a real road**

## Mailuu-Suu road (`mailuu-suu-road`)

22 km, 45% on real roads, highest 1215 m, steepest 500 m 22.6% (ruling 7%)
- start: Korgoncho 0.4 km / route 0.0 km / real road 0.00 km
- end: Mailuu-Suu 0.0 km / route 17.9 km / real road 0.40 km

## Arslanbob road (`arslanbob-road`)

49 km, 92% on real roads, highest 1854 m, steepest 500 m 24.5% (ruling 7%)
- start: Bazar-Korgon 0.0 km / route 0.0 km / real road 0.01 km
- end: Arslanbob 0.0 km / route 34.0 km / real road 0.02 km

