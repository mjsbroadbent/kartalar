# Road audit (build/audit_roads.py)

Grades are over 500 m windows from the ~90 m terrain grid; GRADE counts only new-built stretches. *Real* = within 40 m of an OpenStreetMap road or track.
Flags: GRADE steeper than the road's ruling grade + 2 points for more than 1 km in all; SIDE new-built over 1 km on side slopes over 30%;
BRIDGES new bridges (no real road crossing within 200 m); ZIGZAG the same river or canal crossed twice within 3 km; SKEW a new bridge less than 75 degrees to its river; WATER across a lake; BEND a turn over 100 degrees on easy ground;
PARALLEL new road running close beside a real road; END an end more than 1 km from any settlement, feature, other route or real road; EXIT where the road leaves Irad with no real road carrying on.

| road | km | real | steepest | flags |
|---|---|---|---|---|
| trans-talas-highway | 193 | 64% | 15% | 1 |
| fergana-mountain-transit-highway | 352 | 96% | 32% | 5 |
| iyik-janyl-branch-road | 1 | 3% | 31% | 0 |
| irad-temir-jolu-chu-line | 231 | 97% | 2% | 1 |
| irad-temir-jolu-talas-branch | 101 | 0% | 5% | 11 |
| irad-temir-jolu-kara-buura-line | 146 | 93% | 9% | 2 |
| irad-temir-jolu-north-line | 129 | 97% | 4% | 0 |
| irad-temir-jolu-east-line | 43 | 2% | 3% | 3 |
| irad-temir-jolu-sary-bulak-spur | 39 | 0% | 9% | 7 |
| irad-temir-jolu-chatkal-spur | 6 | 0% | 5% | 2 |
| irad-temir-jolu-taez-siding | 2 | 0% | 7% | 1 |
| talas-nurzhan-road | 336 | 97% | 10% | 2 |
| kok-bel-road | 218 | 70% | 35% | 3 |
| chu-highway | 126 | 95% | 9% | 2 |
| boz-korgon-branch | 42 | 3% | 5% | 2 |
| sary-bulak-road | 28 | 7% | 20% | 2 |
| chatkal-smelter-road | 45 | 60% | 20% | 2 |
| qara-chik-road | 16 | 78% | 7% | 2 |
| kara-oi-road | 29 | 17% | 18% | 2 |
| kenkol-military-road | 32 | 32% | 17% | 3 |
| karakol-road | 22 | 60% | 8% | 0 |
| lower-naryn-uzbek-road | 42 | 93% | 10% | 1 |
| fergana-rim-road | 97 | 93% | 9% | 1 |
| mailuu-suu-road | 23 | 43% | 16% | 0 |
| arslanbob-road | 49 | 92% | 19% | 1 |
| kok-kamar-road | 32 | 52% | 3% | 3 |

## Trans-Talas Highway (`trans-talas-highway`)

193 km, 64% on real roads, highest 1235 m, steepest 500 m 15.4% (ruling 5%)
- start: Talas North Terminal 1.3 km / route 2.3 km / real road 0.09 km
- end: The Hunter's Vigil 0.1 km / route 0.0 km / real road 0.02 km
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Fergana Mountain Transit Highway (State Route 1) (`fergana-mountain-transit-highway`)

352 km, 96% on real roads, highest 3389 m, steepest 500 m 32.4% (ruling 5%)
- start: Talas 0.2 km / route 0.0 km / real road 0.01 km
- end: UNMI Lower Naryn sector HQ 0.2 km / route 0.0 km / real road 0.00 km
- **GRADE 2.5 km over 7% (max 32%)**
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**
- **WATER 0.7 km across a lake or reservoir**
- **BEND 119 deg at 73.2517,42.2075**

## Cathedral Hill road (`iyik-janyl-branch-road`)

1 km, 3% on real roads, highest 811 m, steepest 500 m 31.1% (ruling 6%)
- start: Irad Palace of Art 1.1 km / route 0.0 km / real road 0.01 km
- end: Cathedral Hill 0.0 km / route 1.2 km / real road 1.03 km

## Irad Temir Jolu - Chu line (Turksib) (`irad-temir-jolu-chu-line`)

231 km, 97% on real roads, highest 766 m, steepest 500 m 2.4% (ruling 5%)
- start: Nurzhan railway station 0.0 km / route 0.0 km / real road 0.09 km
- end: Aulie-Ata Airfield (disused) 9.3 km / route 0.0 km / real road 0.00 km
- **PARALLEL 2.1 km new-built 40-250 m beside a real road**

## Irad Temir Jolu - Talas branch (`irad-temir-jolu-talas-branch`)

101 km, 0% on real roads, highest 1254 m, steepest 500 m 4.7% (ruling 5%)
- start: Aulie-Ata Airfield (disused) 8.4 km / route 0.0 km / real road 0.01 km
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
- start: Aulie-Ata Airfield (disused) 9.3 km / route 0.0 km / real road 0.00 km
- end: Talas North Terminal 1.7 km / route 2.6 km / real road 0.03 km
- **SKEW new bridge crosses the river at 14 deg at 71.1346,42.6648**
- **ZIGZAG crosses the same river twice within 0.4 km at 71.1395,42.6660**

## Irad Temir Jolu - Nurzhan north line (`irad-temir-jolu-north-line`)

129 km, 97% on real roads, highest 1022 m, steepest 500 m 3.7% (ruling 5%)
- start: Nurzhan railway station 0.0 km / route 0.0 km / real road 0.09 km
- end: Nurzhan rail border station 0.0 km / route 21.2 km / real road 0.22 km

## Irad Temir Jolu - eastern corridor to Boz-Korgon (`irad-temir-jolu-east-line`)

43 km, 2% on real roads, highest 879 m, steepest 500 m 3.4% (ruling 5%)
- start: Nurzhan madrasa 0.6 km / route 0.0 km / real road 0.00 km
- end: Boz-Korgon 0.7 km / route 0.1 km / real road 27.65 km
- **SKEW new bridge crosses the canal at 75 deg at 73.7753,43.6045**
- **SKEW new bridge crosses the canal at 45 deg at 73.8617,43.5991**
- **BRIDGES 4 new river/canal bridges**

## Irad Temir Jolu - Sary-Bulak and Chatkal spur (`irad-temir-jolu-sary-bulak-spur`)

39 km, 0% on real roads, highest 1670 m, steepest 500 m 8.5% (ruling 5%)
- start: Semiz 1.4 km / route 0.0 km / real road 51.07 km
- end: Sary-Bulak Antimony Works (SBAW) 0.2 km / route 0.2 km / real road 70.32 km
- **GRADE 1.1 km over 7% (max 9%)**
- **SIDE 1.2 km new-built on >30% slopes**
- **SKEW new bridge crosses the canal at 74 deg at 72.1350,42.5108**
- **SKEW new bridge crosses the river at 74 deg at 72.1349,42.5211**
- **SKEW new bridge crosses the canal at 62 deg at 72.0695,42.4381**
- **SKEW new bridge crosses the canal at 54 deg at 71.9930,42.4265**
- **BRIDGES 4 new river/canal bridges**

## Irad Temir Jolu - Chatkal smelter siding (`irad-temir-jolu-chatkal-spur`)

6 km, 0% on real roads, highest 1454 m, steepest 500 m 5.2% (ruling 5%)
- start: Chatkal Antimony Processing Mill 5.4 km / route 0.0 km / real road 67.75 km
- end: Chatkal Antimony Processing Mill 0.1 km / route 0.0 km / real road 70.93 km
- **SKEW new bridge crosses the river at 45 deg at 71.9712,42.3662**
- **BRIDGES 2 new river/canal bridges**

## Irad Temir Jolu - TAEZ sidings (`irad-temir-jolu-taez-siding`)

2 km, 0% on real roads, highest 1196 m, steepest 500 m 7.2% (ruling 5%)
- start: Talas Airport Logistics Hub (Iradiya terminal) 0.6 km / route 0.0 km / real road 51.08 km
- end: Talas Cold Chain Logistics Hub 0.0 km / route 0.9 km / real road 52.68 km
- **BRIDGES 1 new river/canal bridges**

## Talas-Nurzhan road (lowland route) (`talas-nurzhan-road`)

336 km, 97% on real roads, highest 1235 m, steepest 500 m 10.2% (ruling 6%)
- start: The Hunter's Vigil 0.1 km / route 0.0 km / real road 0.02 km
- end: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- **BRIDGES 1 new river/canal bridges**
- **WATER 0.3 km across a lake or reservoir**

## Kök-Bel road (`kok-bel-road`)

218 km, 70% on real roads, highest 2778 m, steepest 500 m 34.6% (ruling 6%)
- start: Talas 0.2 km / route 0.0 km / real road 0.01 km
- end: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- **GRADE 10.8 km over 8% (max 35%)**
- **SIDE 8.5 km new-built on >30% slopes**
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Chu highway (Nurzhan - Chu Gate) (`chu-highway`)

126 km, 95% on real roads, highest 1272 m, steepest 500 m 9.0% (ruling 5%)
- start: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- end: Chu Gate crossing 0.0 km / route 23.2 km / real road 0.01 km
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**

## Boz-Korgon branch road (`boz-korgon-branch`)

42 km, 3% on real roads, highest 883 m, steepest 500 m 4.7% (ruling 5%)
- start: Nurzhan Refinery No. 1 0.6 km / route 0.4 km / real road 1.01 km
- end: Boz-Korgon 0.5 km / route 0.2 km / real road 2.76 km
- **PARALLEL 1.5 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**

## Sary-Bulak branch road (`sary-bulak-road`)

28 km, 7% on real roads, highest 1967 m, steepest 500 m 19.6% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Sary-Bulak Antimony Works (SBAW) 0.0 km / route 0.2 km / real road 7.33 km
- **GRADE 1.1 km over 9% (max 20%)**
- **SIDE 1.1 km new-built on >30% slopes**

## Chatkal smelter road (`chatkal-smelter-road`)

45 km, 60% on real roads, highest 1630 m, steepest 500 m 19.9% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: Kemer Antimony Mine 0.0 km / route 5.0 km / real road 0.05 km
- **PARALLEL 2.0 km new-built 40-250 m beside a real road**
- **SKEW new bridge crosses the river at 43 deg at 71.9794,42.3720**

## Qara-Chik road (Kyzyl-Adyr - Qara-Chik checkpoint) (`qara-chik-road`)

16 km, 78% on real roads, highest 1236 m, steepest 500 m 6.6% (ruling 7%)
- start: Kyzyl-Adyr district hospital 0.4 km / route 0.0 km / real road 0.02 km
- end: Qara-Chik Border Checkpoint 1.4 km / route 12.4 km / real road 0.00 km
- **SKEW new bridge crosses the canal at 16 deg at 71.5575,42.5151**
- **ZIGZAG crosses the same canal twice within 0.4 km at 71.5568,42.5185**

## Talas - Kara-Oi road (`kara-oi-road`)

29 km, 17% on real roads, highest 2004 m, steepest 500 m 17.7% (ruling 7%)
- start: Talas 0.1 km / route 0.0 km / real road 0.02 km
- end: UNMI Headquarters, Kara-Oi 0.0 km / route 11.2 km / real road 5.23 km
- **SIDE 1.7 km new-built on >30% slopes**
- **PARALLEL 1.6 km new-built 40-250 m beside a real road**

## Kenkol Pass road (`kenkol-military-road`)

32 km, 32% on real roads, highest 2117 m, steepest 500 m 16.6% (ruling 9%)
- start: Kara-Bulak kurgans 4.6 km / route 0.0 km / real road 0.00 km
- end: Kenkol Pass 0.0 km / route 17.8 km / real road 4.16 km
- **ZIGZAG crosses the same river twice within 0.5 km at 71.8183,42.4009**
- **ZIGZAG crosses the same river twice within 0.5 km at 71.7575,42.3369**
- **BRIDGES 5 new river/canal bridges**

## Western Karakol valley road (`karakol-road`)

22 km, 60% on real roads, highest 2638 m, steepest 500 m 8.3% (ruling 8%)
- start: Suusamyr crossing 0.7 km / route 0.0 km / real road 0.00 km
- end: Karakol 0.0 km / route 18.9 km / real road 2.49 km

## Tash-Kömür - Uzbek border road (`lower-naryn-uzbek-road`)

42 km, 93% on real roads, highest 665 m, steepest 500 m 10.0% (ruling 6%)
- start: UNMI Lower Naryn sector HQ 0.2 km / route 0.0 km / real road 0.00 km
- end: Kyzyl-Jar crossing 0.2 km / route 9.9 km / real road 0.00 km
- **BEND 101 deg at 72.1892,41.1952**

## Fergana rim road (Tash-Kömür – Bazar-Korgon) (`fergana-rim-road`)

97 km, 93% on real roads, highest 812 m, steepest 500 m 8.9% (ruling 6%)
- start: UNMI Lower Naryn sector HQ 0.3 km / route 0.2 km / real road 0.12 km
- end: Bazar-Korgon bazaar 0.1 km / route 0.0 km / real road 0.01 km
- **PARALLEL 2.2 km new-built 40-250 m beside a real road**

## Mailuu-Suu road (`mailuu-suu-road`)

23 km, 43% on real roads, highest 1214 m, steepest 500 m 16.3% (ruling 7%)
- start: Korgoncho 1.4 km / route 0.2 km / real road 0.00 km
- end: Mailuu-Suu 2.4 km / route 18.0 km / real road 0.40 km

## Arslanbob road (`arslanbob-road`)

49 km, 92% on real roads, highest 1854 m, steepest 500 m 19.3% (ruling 7%)
- start: Bazar-Korgon bazaar 0.1 km / route 0.0 km / real road 0.01 km
- end: Arslanbob 0.6 km / route 29.8 km / real road 0.02 km
- **SKEW new bridge crosses the river at 56 deg at 72.9144,41.3363**

## Kök-Kamar road (`kok-kamar-road`)

32 km, 52% on real roads, highest 1102 m, steepest 500 m 3.3% (ruling 7%)
- start: Suzak crossing 1.0 km / route 19.2 km / real road 0.06 km
- end: Kök-Jangak crossing 5.3 km / route 25.1 km / real road 0.01 km
- **PARALLEL 2.0 km new-built 40-250 m beside a real road**
- **SKEW new bridge crosses the river at 50 deg at 73.0799,41.0796**
- **BRIDGES 1 new river/canal bridges**

