# Road audit (build/audit_roads.py)

Grades are over 500 m windows from the ~90 m terrain grid; GRADE counts only new-built stretches. *Real* = within 40 m of an OpenStreetMap road or track.
Flags: GRADE steeper than the road's ruling grade + 2 points for more than 1 km in all; SIDE new-built over 1 km on side slopes over 30%;
BRIDGES new bridges (no real road crossing within 200 m); ZIGZAG the same river or canal crossed twice within 3 km; SKEW a new bridge less than 75 degrees to its river (45 for a railway, where skew bridges are the usual way across); WATER across a lake; BEND a turn over 100 degrees on easy ground;
PARALLEL new road running close beside a real road; END an end more than 1 km from any settlement, feature, other route or real road; EXIT where the road leaves Irad with no real road carrying on.

| road | km | real | steepest | flags |
|---|---|---|---|---|
| trans-talas-highway | 193 | 64% | 15% | 1 |
| fergana-mountain-transit-highway | 352 | 96% | 32% | 5 |
| iyik-janyl-branch-road | 1 | 3% | 31% | 0 |
| irad-temir-jolu-chu-line | 230 | 100% | 2% | 0 |
| irad-temir-jolu-talas-branch | 101 | 0% | 5% | 1 |
| irad-temir-jolu-kara-buura-line | 146 | 93% | 9% | 2 |
| irad-temir-jolu-north-line | 130 | 97% | 4% | 1 |
| irad-temir-jolu-east-line | 44 | 2% | 3% | 1 |
| irad-temir-jolu-sary-bulak-spur | 39 | 0% | 10% | 3 |
| irad-temir-jolu-chatkal-spur | 6 | 0% | 24% | 3 |
| irad-temir-jolu-taez-siding | 2 | 0% | 8% | 1 |
| talas-nurzhan-road | 336 | 97% | 10% | 2 |
| kok-bel-road | 231 | 67% | 12% | 2 |
| chu-highway | 126 | 95% | 9% | 2 |
| boz-korgon-branch | 42 | 3% | 5% | 2 |
| sary-bulak-road | 32 | 6% | 8% | 1 |
| chatkal-smelter-road | 45 | 60% | 20% | 2 |
| qara-chik-road | 16 | 75% | 7% | 2 |
| kara-oi-road | 29 | 17% | 12% | 2 |
| kenkol-military-road | 33 | 30% | 9% | 4 |
| karakol-road | 22 | 60% | 8% | 0 |
| lower-naryn-uzbek-road | 42 | 93% | 10% | 1 |
| fergana-rim-road | 97 | 93% | 9% | 1 |
| mailuu-suu-road | 25 | 41% | 16% | 0 |
| arslanbob-road | 49 | 92% | 19% | 1 |
| kok-kamar-road | 32 | 53% | 3% | 3 |

## Trans-Talas Highway (`trans-talas-highway`)

193 km, 64% on real roads, highest 1235 m, steepest 500 m 15.4% (ruling 5%)
- start: Talas North Terminal 1.3 km / route 2.3 km / real road 0.09 km
- end: Central City Park 0.1 km / route 0.0 km / real road 0.02 km
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Fergana Mountain Transit Highway (State Route 1) (`fergana-mountain-transit-highway`)

352 km, 96% on real roads, highest 3389 m, steepest 500 m 32.4% (ruling 5%)
- start: Central Square (Government Square) 0.2 km / route 0.0 km / real road 0.01 km
- end: UNMI Lower Naryn sector HQ 0.2 km / route 0.0 km / real road 0.00 km
- **GRADE 2.5 km over 7% (max 32%)**
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**
- **WATER 0.8 km across a lake or reservoir**
- **BEND 119 deg at 73.2517,42.2075**

## Cathedral Hill road (`iyik-janyl-branch-road`)

1 km, 3% on real roads, highest 811 m, steepest 500 m 31.1% (ruling 6%)
- start: Irad Palace of Art 1.1 km / route 0.0 km / real road 0.01 km
- end: Cathedral Hill 0.0 km / route 1.2 km / real road 1.03 km

## Irad Temir Jolu - Chu line (Turksib) (`irad-temir-jolu-chu-line`)

230 km, 100% on real roads, highest 766 m, steepest 500 m 2.5% (ruling 5%)
- start: Nurzhan railway station 0.0 km / route 0.0 km / real road 0.09 km
- end: Aulie-Ata Airfield (disused) 9.3 km / route 0.0 km / real road 0.00 km

## Irad Temir Jolu - Talas branch (`irad-temir-jolu-talas-branch`)

101 km, 0% on real roads, highest 1254 m, steepest 500 m 4.7% (ruling 5%)
- start: Aulie-Ata Airfield (disused) 8.4 km / route 0.0 km / real road 0.01 km
- end: Talas railway station 0.0 km / route 0.6 km / real road 52.55 km
- **BRIDGES 8 new river/canal bridges**

## Irad Temir Jolu - Kara-Buura corridor line (to Talas North Terminal) (`irad-temir-jolu-kara-buura-line`)

146 km, 93% on real roads, highest 1138 m, steepest 500 m 9.1% (ruling 5%)
- start: Aulie-Ata Airfield (disused) 9.3 km / route 0.0 km / real road 0.00 km
- end: Talas North Terminal 1.7 km / route 2.6 km / real road 0.03 km
- **SKEW new bridge crosses the river at 14 deg at 71.1346,42.6648**
- **ZIGZAG crosses the same river twice within 0.4 km at 71.1395,42.6660**

## Irad Temir Jolu - Nurzhan north line (`irad-temir-jolu-north-line`)

130 km, 97% on real roads, highest 1022 m, steepest 500 m 3.7% (ruling 5%)
- start: Nurzhan railway station 0.0 km / route 0.0 km / real road 0.09 km
- end: Nurzhan rail border station 0.0 km / route 21.2 km / real road 0.22 km
- **PARALLEL 1.2 km new-built 40-250 m beside a real road**

## Irad Temir Jolu - eastern corridor to Boz-Korgon (`irad-temir-jolu-east-line`)

44 km, 2% on real roads, highest 879 m, steepest 500 m 3.4% (ruling 5%)
- start: Nurzhan madrasa 0.6 km / route 0.0 km / real road 0.01 km
- end: Boz-Korgon 0.7 km / route 0.1 km / real road 27.65 km
- **BRIDGES 4 new river/canal bridges**

## Irad Temir Jolu - Sary-Bulak and Chatkal spur (`irad-temir-jolu-sary-bulak-spur`)

39 km, 0% on real roads, highest 1670 m, steepest 500 m 10.0% (ruling 5%)
- start: Semiz cemetery 0.7 km / route 0.0 km / real road 51.10 km
- end: Sary-Bulak Antimony Works (SBAW) 0.2 km / route 0.1 km / real road 70.32 km
- **GRADE 1.2 km over 7% (max 10%)**
- **SIDE 1.4 km new-built on >30% slopes**
- **BRIDGES 4 new river/canal bridges**

## Irad Temir Jolu - Chatkal smelter siding (`irad-temir-jolu-chatkal-spur`)

6 km, 0% on real roads, highest 1483 m, steepest 500 m 24.5% (ruling 5%)
- start: Chatkal Antimony Processing Mill 5.9 km / route 0.0 km / real road 67.25 km
- end: Chatkal Antimony Processing Mill 0.1 km / route 0.1 km / real road 70.93 km
- **SIDE 1.4 km new-built on >30% slopes**
- **SKEW new bridge crosses the river at 45 deg at 71.9793,42.3780**
- **BRIDGES 1 new river/canal bridges**

## Irad Temir Jolu - TAEZ sidings (`irad-temir-jolu-taez-siding`)

2 km, 0% on real roads, highest 1196 m, steepest 500 m 7.6% (ruling 5%)
- start: Talas Airport Logistics Hub (Iradiya terminal) 0.6 km / route 0.0 km / real road 51.34 km
- end: Talas Cold Chain Logistics Hub 0.0 km / route 0.4 km / real road 52.68 km
- **BRIDGES 1 new river/canal bridges**

## Talas-Nurzhan road (lowland route) (`talas-nurzhan-road`)

336 km, 97% on real roads, highest 1235 m, steepest 500 m 10.2% (ruling 6%)
- start: Central City Park 0.1 km / route 0.0 km / real road 0.02 km
- end: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- **BRIDGES 1 new river/canal bridges**
- **WATER 0.3 km across a lake or reservoir**

## Kök-Bel road (`kok-bel-road`)

231 km, 67% on real roads, highest 2739 m, steepest 500 m 11.7% (ruling 6%)
- start: Central Square (Government Square) 0.2 km / route 0.0 km / real road 0.01 km
- end: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- **GRADE 1.1 km over 8% (max 12%)**
- **SIDE 8.9 km new-built on >30% slopes**

## Chu highway (Nurzhan - Chu Gate) (`chu-highway`)

126 km, 95% on real roads, highest 1272 m, steepest 500 m 9.0% (ruling 5%)
- start: Nurzhan 0.1 km / route 0.0 km / real road 0.03 km
- end: Chu Gate crossing 0.0 km / route 23.2 km / real road 0.01 km
- **PARALLEL 1.1 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**

## Boz-Korgon branch road (`boz-korgon-branch`)

42 km, 3% on real roads, highest 883 m, steepest 500 m 4.7% (ruling 5%)
- start: Nurzhan Oil Refinery 0.6 km / route 0.1 km / real road 1.01 km
- end: Boz-Korgon 0.5 km / route 0.2 km / real road 2.76 km
- **PARALLEL 1.5 km new-built 40-250 m beside a real road**
- **BRIDGES 1 new river/canal bridges**

## Sary-Bulak branch road (`sary-bulak-road`)

32 km, 6% on real roads, highest 1968 m, steepest 500 m 8.3% (ruling 7%)
- start: Central Square (Government Square) 0.1 km / route 0.0 km / real road 0.02 km
- end: Sary-Bulak Antimony Works (SBAW) 0.0 km / route 0.2 km / real road 7.33 km
- **SIDE 1.6 km new-built on >30% slopes**

## Chatkal smelter road (`chatkal-smelter-road`)

45 km, 60% on real roads, highest 1630 m, steepest 500 m 19.8% (ruling 7%)
- start: Central Square (Government Square) 0.1 km / route 0.0 km / real road 0.02 km
- end: Kemer Antimony Mine 0.0 km / route 5.0 km / real road 0.05 km
- **PARALLEL 1.9 km new-built 40-250 m beside a real road**
- **SKEW new bridge crosses the river at 43 deg at 71.9794,42.3720**

## Qara-Chik road (Kyzyl-Adyr - Qara-Chik checkpoint) (`qara-chik-road`)

16 km, 75% on real roads, highest 1236 m, steepest 500 m 6.6% (ruling 7%)
- start: Kyzyl-Adyr district hospital 0.4 km / route 0.0 km / real road 0.02 km
- end: Qara-Chik Border Checkpoint 1.4 km / route 12.4 km / real road 0.00 km
- **SKEW new bridge crosses the canal at 16 deg at 71.5575,42.5151**
- **ZIGZAG crosses the same canal twice within 0.4 km at 71.5568,42.5185**

## Talas - Kara-Oi road (`kara-oi-road`)

29 km, 17% on real roads, highest 2006 m, steepest 500 m 12.0% (ruling 7%)
- start: Central Square (Government Square) 0.1 km / route 0.0 km / real road 0.02 km
- end: UNMI Headquarters, Kara-Oi 0.0 km / route 11.2 km / real road 5.23 km
- **SIDE 1.4 km new-built on >30% slopes**
- **PARALLEL 1.6 km new-built 40-250 m beside a real road**

## Kenkol Pass road (`kenkol-military-road`)

33 km, 30% on real roads, highest 2117 m, steepest 500 m 8.9% (ruling 9%)
- start: Kara-Bulak kurgans 4.2 km / route 0.0 km / real road 0.01 km
- end: Kenkol Pass 0.0 km / route 17.8 km / real road 4.16 km
- **SIDE 4.8 km new-built on >30% slopes**
- **ZIGZAG crosses the same river twice within 0.5 km at 71.8183,42.4009**
- **ZIGZAG crosses the same river twice within 0.7 km at 71.7524,42.3357**
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

25 km, 41% on real roads, highest 1221 m, steepest 500 m 16.3% (ruling 7%)
- start: Korgoncho 1.2 km / route 0.0 km / real road 0.01 km
- end: Mailuu-Suu 2.4 km / route 18.0 km / real road 0.40 km

## Arslanbob road (`arslanbob-road`)

49 km, 92% on real roads, highest 1854 m, steepest 500 m 19.3% (ruling 7%)
- start: Bazar-Korgon bazaar 0.1 km / route 0.0 km / real road 0.01 km
- end: Arslanbob 0.6 km / route 29.8 km / real road 0.02 km
- **SKEW new bridge crosses the river at 56 deg at 72.9144,41.3363**

## Kök-Kamar road (`kok-kamar-road`)

32 km, 53% on real roads, highest 1102 m, steepest 500 m 3.3% (ruling 7%)
- start: Suzak crossing 1.0 km / route 19.2 km / real road 0.06 km
- end: Kök-Jangak crossing 5.3 km / route 25.1 km / real road 0.01 km
- **PARALLEL 2.0 km new-built 40-250 m beside a real road**
- **SKEW new bridge crosses the river at 50 deg at 73.0799,41.0796**
- **BRIDGES 1 new river/canal bridges**

