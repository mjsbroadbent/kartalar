# Road audit (build/audit_roads.py)

Grades are over 500 m windows from the ~90 m terrain grid; GRADE counts only new-built stretches. *Real* = within 40 m of an OpenStreetMap road or track.
Flags: GRADE steeper than the road's ruling grade + 2 points for more than 1 km in all; SIDE new-built over 1 km on side slopes over 30%;
BRIDGES new bridges (no real road crossing within 200 m); ZIGZAG the same river or canal crossed twice within 3 km; SKEW a new bridge less than 75 degrees to its river; WATER across a lake; BEND a turn over 100 degrees on easy ground;
PARALLEL new road running close beside a real road; END an end more than 1 km from any settlement, feature, other route or real road; EXIT where the road leaves Irad with no real road carrying on.

| road | km | real | steepest | flags |
|---|---|---|---|---|
| trans-talas-highway | 193 | 64% | 15% | 1 |
| fergana-mountain-transit-highway | 353 | 95% | 39% | 5 |
| iyik-janyl-branch-road | 1 | 3% | 31% | 0 |
| irad-temir-jolu-chu-line | 231 | 97% | 2% | 1 |
| irad-temir-jolu-talas-branch | 101 | 0% | 5% | 11 |
| irad-temir-jolu-kara-buura-line | 146 | 93% | 9% | 2 |
| irad-temir-jolu-north-line | 129 | 97% | 4% | 0 |
| irad-temir-jolu-east-line | 43 | 2% | 3% | 3 |
| irad-temir-jolu-sary-bulak-spur | 23 | 0% | 18% | 2 |
| irad-temir-jolu-chatkal-spur | 23 | 0% | 39% | 5 |
| irad-temir-jolu-taez-siding | 2 | 0% | 7% | 1 |
| talas-nurzhan-road | 336 | 97% | 10% | 2 |
| kok-bel-road | 214 | 72% | 25% | 3 |
| chu-highway | 117 | 85% | 8% | 1 |
| boz-korgon-branch | 42 | 3% | 5% | 2 |
| sary-bulak-road | 25 | 8% | 25% | 1 |
| chatkal-smelter-road | 45 | 58% | 12% | 4 |
| qara-chik-road | 40 | 14% | 26% | 4 |
| kenkol-military-road | 32 | 32% | 25% | 2 |
| karakol-road | 22 | 60% | 8% | 0 |
| lower-naryn-uzbek-road | 39 | 94% | 10% | 1 |
| fergana-rim-road | 97 | 93% | 9% | 1 |
| mailuu-suu-road | 22 | 45% | 23% | 0 |
| arslanbob-road | 49 | 92% | 25% | 1 |

## Trans-Talas Highway (`trans-talas-highway`)

193 km, 64% on real roads, highest 1235 m, steepest 500 m 15.4% (ruling 5%)
- start: Talas North Terminal 1.3 km / route 2.3 km / real road 0.09 km
- end: Central City Park 0.1 km / route 0.0 km / real road 0.02 km
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Fergana Mountain Transit Highway (State Route 1) (`fergana-mountain-transit-highway`)

353 km, 95% on real roads, highest 3389 m, steepest 500 m 39.0% (ruling 5%)
- start: Talas 0.2 km / route 0.0 km / real road 0.01 km
- end: UNMI Lower Naryn sector HQ 0.2 km / route 0.0 km / real road 0.00 km
- **GRADE 5.0 km over 7% (max 39%)**
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**
- **WATER 0.4 km across a lake or reservoir**
- **BEND 119 deg at 73.2517,42.2075**

## Cathedral Hill road (`iyik-janyl-branch-road`)

1 km, 3% on real roads, highest 813 m, steepest 500 m 31.2% (ruling 6%)
- start: Irad Palace of Art 1.1 km / route 0.0 km / real road 0.01 km
- end: Cathedral Hill 0.0 km / route 1.2 km / real road 1.03 km

## Irad Temir Jolu - Chu line (Turksib) (`irad-temir-jolu-chu-line`)

231 km, 97% on real roads, highest 766 m, steepest 500 m 2.4% (ruling 5%)
- start: Nurzhan railway station 0.0 km / route 0.0 km / real road 0.09 km
- end: Talas border gauge 15.3 km / route 0.0 km / real road 0.00 km
- **PARALLEL 2.1 km new-built 40-250 m beside a real road**

## Irad Temir Jolu - Talas branch (`irad-temir-jolu-talas-branch`)

101 km, 0% on real roads, highest 1254 m, steepest 500 m 4.7% (ruling 5%)
- start: Talas border gauge 15.6 km / route 0.0 km / real road 0.01 km
- end: Talas railway station 0.0 km / route 0.6 km / real road 52.55 km
- **SKEW new bridge crosses the canal at 33 deg at 71.8755,42.5416**
- **SKEW new bridge crosses the canal at 67 deg at 72.1831,42.5120**
- **SKEW new bridge crosses the river at 74 deg at 71.9396,42.5441**
- **SKEW new bridge crosses the canal at 53 deg at 72.1602,42.5231**
- **SKEW new bridge crosses the river at 48 deg at 72.1033,42.5276**
- **SKEW new bridge crosses the river at 56 deg at 72.0276,42.5334**
- **SKEW new bridge crosses the river at 52 deg at 72.0486,42.5274**
- **ZIGZAG crosses the same river twice within 1.9 km at 72.0276,42.5334**
- **ZIGZAG crosses the same river twice within 0.1 km at 72.0486,42.5274**
- **SKEW new bridge crosses the canal at 55 deg at 71.4123,42.8004**
- **BRIDGES 12 new river/canal bridges**

## Irad Temir Jolu - Kara-Buura corridor line (to Talas North Terminal) (`irad-temir-jolu-kara-buura-line`)

146 km, 93% on real roads, highest 1138 m, steepest 500 m 9.1% (ruling 5%)
- start: Talas border gauge 15.3 km / route 0.0 km / real road 0.00 km
- end: Talas North Terminal 1.7 km / route 2.6 km / real road 0.03 km
- **SKEW new bridge crosses the river at 14 deg at 71.1346,42.6648**
- **ZIGZAG crosses the same river twice within 0.4 km at 71.1395,42.6660**

## Irad Temir Jolu - Nurzhan north line (`irad-temir-jolu-north-line`)

129 km, 97% on real roads, highest 1022 m, steepest 500 m 3.7% (ruling 5%)
- start: Nurzhan railway station 0.0 km / route 0.0 km / real road 0.09 km
- end: Nurzhan rail border station 0.0 km / route 34.4 km / real road 0.22 km

## Irad Temir Jolu - eastern corridor to Boz-Korgon (`irad-temir-jolu-east-line`)

43 km, 2% on real roads, highest 879 m, steepest 500 m 3.4% (ruling 5%)
- start: Nurzhan madrasa 0.6 km / route 0.0 km / real road 0.00 km
- end: Boz-Korgon compound 0.6 km / route 0.1 km / real road 27.65 km
- **SKEW new bridge crosses the canal at 75 deg at 73.7753,43.6045**
- **SKEW new bridge crosses the canal at 45 deg at 73.8617,43.5991**
- **BRIDGES 4 new river/canal bridges**

## Irad Temir Jolu - Sary-Bulak and Chatkal spur (`irad-temir-jolu-sary-bulak-spur`)

23 km, 0% on real roads, highest 1968 m, steepest 500 m 18.3% (ruling 5%)
- start: Semiz 1.4 km / route 0.0 km / real road 51.07 km
- end: Sary-Bulak Antimony Works (SBAW) 0.2 km / route 0.2 km / real road 70.32 km
- **GRADE 5.7 km over 7% (max 18%)**
- **BRIDGES 2 new river/canal bridges**

## Irad Temir Jolu - Chatkal smelter siding (`irad-temir-jolu-chatkal-spur`)

23 km, 0% on real roads, highest 1631 m, steepest 500 m 39.4% (ruling 5%)
- start: Kara-Suu Canyon checkpoint (State Route 1 northern post) 1.7 km / route 0.0 km / real road 60.60 km
- end: Chatkal Antimony Processing Mill 0.5 km / route 0.4 km / real road 71.05 km
- **SKEW new bridge crosses the river at 58 deg at 71.9796,42.3749**
- **SKEW new bridge crosses the river at 66 deg at 71.9605,42.3383**
- **SKEW new bridge crosses the canal at 24 deg at 72.0608,42.4363**
- **SKEW new bridge crosses the canal at 63 deg at 71.9911,42.4260**
- **BRIDGES 4 new river/canal bridges**

## Irad Temir Jolu - TAEZ sidings (`irad-temir-jolu-taez-siding`)

2 km, 0% on real roads, highest 1196 m, steepest 500 m 7.2% (ruling 5%)
- start: Talas Airport Logistics Hub (Iradiya terminal) 0.6 km / route 0.0 km / real road 51.08 km
- end: Talas Cold Chain Logistics Hub 0.0 km / route 1.0 km / real road 52.68 km
- **BRIDGES 1 new river/canal bridges**

## Talas-Nurzhan road (lowland route) (`talas-nurzhan-road`)

336 km, 97% on real roads, highest 1235 m, steepest 500 m 10.2% (ruling 6%)
- start: Central City Park 0.1 km / route 0.0 km / real road 0.02 km
- end: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- **BRIDGES 1 new river/canal bridges**
- **WATER 0.3 km across a lake or reservoir**

## Kök-Bel road (`kok-bel-road`)

214 km, 72% on real roads, highest 2743 m, steepest 500 m 25.0% (ruling 6%)
- start: Talas 0.2 km / route 0.0 km / real road 0.01 km
- end: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- **GRADE 10.9 km over 8% (max 25%)**
- **SIDE 5.1 km new-built on >30% slopes**
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Chu highway (Nurzhan - Chu Gate) (`chu-highway`)

117 km, 85% on real roads, highest 1029 m, steepest 500 m 7.5% (ruling 5%)
- start: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- end: Chu Gate crossing 0.0 km / route 38.7 km / real road 0.39 km
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**

## Boz-Korgon branch road (`boz-korgon-branch`)

42 km, 3% on real roads, highest 883 m, steepest 500 m 4.7% (ruling 5%)
- start: Nurzhan Refinery No. 1 0.6 km / route 0.4 km / real road 1.01 km
- end: Boz-Korgon compound 0.4 km / route 0.2 km / real road 2.76 km
- **PARALLEL 1.5 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**

## Sary-Bulak branch road (`sary-bulak-road`)

25 km, 8% on real roads, highest 1967 m, steepest 500 m 24.6% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Sary-Bulak Antimony Works (SBAW) 0.0 km / route 0.2 km / real road 7.33 km
- **GRADE 4.7 km over 9% (max 25%)**

## Chatkal smelter road (`chatkal-smelter-road`)

45 km, 58% on real roads, highest 1630 m, steepest 500 m 11.7% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Kemer Antimony Mine 0.0 km / route 5.3 km / real road 0.05 km
- **PARALLEL 2.0 km new-built 40-250 m beside a real road**
- **SKEW new bridge crosses the river at 12 deg at 71.9583,42.3196**
- **ZIGZAG crosses the same river twice within 0.1 km at 71.9577,42.3199**
- **SKEW new bridge crosses the river at 43 deg at 71.9794,42.3720**

## Talas - Qara-Chik checkpoint road (`qara-chik-road`)

40 km, 14% on real roads, highest 2538 m, steepest 500 m 26.1% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Köl-Sai glacial lake 1.7 km / route 18.8 km / real road 8.33 km
- **GRADE 7.0 km over 9% (max 26%)**
- **SIDE 4.8 km new-built on >30% slopes**
- **PARALLEL 1.6 km new-built 40-250 m beside a real road**
- **END at 72.5100,42.3150 is 1.7 km from anything**

## Kenkol Pass road (`kenkol-military-road`)

32 km, 32% on real roads, highest 2117 m, steepest 500 m 25.1% (ruling 9%)
- start: Kara-Bulak kurgans 4.6 km / route 0.0 km / real road 0.00 km
- end: Kenkol Pass 0.0 km / route 17.8 km / real road 4.16 km
- **ZIGZAG crosses the same river twice within 0.5 km at 71.8183,42.4009**
- **BRIDGES 3 new river/canal bridges**

## Western Karakol valley road (`karakol-road`)

22 km, 60% on real roads, highest 2638 m, steepest 500 m 8.3% (ruling 8%)
- start: Suusamyr crossing 1.1 km / route 0.0 km / real road 0.00 km
- end: Karakol 0.0 km / route 18.9 km / real road 2.49 km

## Tash-Kömür - Uzbek border road (`lower-naryn-uzbek-road`)

39 km, 94% on real roads, highest 665 m, steepest 500 m 10.0% (ruling 6%)
- start: UNMI Lower Naryn sector HQ 0.2 km / route 0.0 km / real road 0.00 km
- end: Naryn River (leaving Irad) 2.7 km / route 8.9 km / real road 0.01 km
- **BEND 101 deg at 72.1892,41.1952**

## Fergana rim road (Tash-Kömür – Bazar-Korgon) (`fergana-rim-road`)

97 km, 93% on real roads, highest 812 m, steepest 500 m 8.9% (ruling 6%)
- start: UNMI Lower Naryn sector HQ 0.3 km / route 0.2 km / real road 0.12 km
- end: Bazar-Korgon bazaar 0.1 km / route 0.0 km / real road 0.01 km
- **PARALLEL 2.2 km new-built 40-250 m beside a real road**

## Mailuu-Suu road (`mailuu-suu-road`)

22 km, 45% on real roads, highest 1215 m, steepest 500 m 22.6% (ruling 7%)
- start: Korgoncho 1.4 km / route 0.2 km / real road 0.00 km
- end: Mailuu-Suu 2.4 km / route 18.0 km / real road 0.40 km

## Arslanbob road (`arslanbob-road`)

49 km, 92% on real roads, highest 1854 m, steepest 500 m 24.9% (ruling 7%)
- start: Bazar-Korgon bazaar 0.1 km / route 0.0 km / real road 0.01 km
- end: Arslanbob 0.6 km / route 34.0 km / real road 0.02 km
- **SKEW new bridge crosses the river at 56 deg at 72.9144,41.3363**

