# Irad settlements gazetteer: build report

Output: `/home/claude/kartalar/data/settlements.json` — 144 entries. Validated: valid JSON, unique ids, every object has all 14 fields, all lat 40.6–46.1 and lon 67.9–75.2.

## 1. Count by kind

| kind | count |
|---|---|
| capital | 1 |
| city | 2 |
| town | 8 |
| village | 104 |
| suburb | 3 |
| quarter | 8 |
| neighbourhood | 7 |
| district | 5 |
| zone-area | 6 |
| **total** | **144** |

By confidence: placed 121, real-place 9, stated 8, anchor 6. By zone: ISEZ 77, ATR 67.

Coverage: all 108 articles in the wiki's *Cities & Settlements* category (the Vol3 *Minor Settlements & Communes* stubs included), plus every settlement named in passing that I found by searching all three wiki volumes, canon/quickref/hiddenlore/SKILL, the Talas Herald archive and stories, IradOne news data and the Tulpar seed chat. The passing mentions are Kara-Oi, Qara-Chik, Besh-Tash, Arsha-Say, Tash-Bulak, Jangy-Kent, Arkyt, Kara-Köl, Kyzyl-Unkur, the Chatkal works settlement and Sary-Bulak's "Rudnik". I also added city quarters, three clan-centre label points (Kara-Suu/Tanıp, Kara-Koyun/Karakoyun, Upper Besh-Tash/Akjele), the 5 districts and the 6 planning zones.

**Deliberately excluded** (not settlements, or outside Irad):
- Archaeological sites and ruins: Shelji, Shahr-i Buzurg, Kand-i Nau, Kand-i Kohna, Diz-i Zard, Diz-i Safid, Shar-i-Kuhna (Old Iyık Janyl), Rabat-i-Safed, Rabat-i Kamal, Rabat-i Sangin. The modern villages beside them are included.
- Facilities: Talas Air Base, Talas North Terminal, the Chu Gate and Kum-Shagyl crossings, the Qara-Chik and Aksay checkpoints, the Kemer and Kyzyl-Jar mines, the Kurpsai/Shamaldy-Sai/Uch-Kurgan power stations, and studs and ranches (Chong-Talas, Ak-Tilek, Kyzyl-Jyldyz, Akyel Breeding Sanctuary).
- Ming-Tepe: the 1898 Andijan rebel's village, outside Irad.
- Kyzyl-Kiya and Kadamjai: these appear only in the raw Kyrgyz news feed (`seen.json`), not in the lore.
- The Boztorgoy clan: it has no named centre (only "Moiynkum winter pastures"), so it gets no point. Clan links are given in the notes instead: Kökjal → Ozgörüsh, Chubar → Bazar-Korgon.

**Conventions:**
- `district` uses the city name for city-governed land. As the spec asks, Talas city and Talas District therefore both read "Talas"; the `kind` field tells them apart.
- `name_ru` follows Russian map practice (ö→о, ü→у, j→дж, ñ/ng→н). Known Russian forms are used where they exist: Таш-Кумыр, Кара-Куль, Чон-Капка, Ийык Джаныл.
- `pop` is filled only where a figure is stated in the lore.
- `elev` is filled only where an elevation is stated for the settlement itself.

## 2. Contradictions and ambiguities, and how I resolved them

1. **Iyık Janyl – Tash-Kömür distance.** Vol1, canon and quickref say ~20 km NE. The *Tash-Kömür* article says 18 km, and canon lists 18 km as a retired error. *Resolution:* Used the 20 km anchor.
2. **Iyık Janyl road distance.** Iyık Janyl is 235 km from Talas by road, via a 12-km branch that leaves State Route 1 "above Tash-Kömür". But Tash-Kömür itself, at the end of the same highway, is 236 km. That only works if the branch leaves ~13 km before the highway's end *and* the branch is shorter than stated, or one figure is rounded. *Resolution:* No coordinate effect. Anchors kept.
3. **Iyık Janyl on the "east side of the Naryn gorge".** With the fixed anchor (41.48, 72.38) and the real course of the Naryn between Kurpsai and Tash-Kömür, the anchor sits at or slightly west of the river, not clearly east of it. *Resolution:* Kept the anchor as instructed. Put Cathedral Hill and Shahr-i Khunuk (the "upper side") up-valley to the E/NE, and the Lower Town toward the river. Worth checking against the basemap.
4. **Besh-Tash valley mouth.** Two villages are said to be at the mouth of the Besh-Tash valley: Kök-Oi (~20 km S of Talas, ranger HQ), and the "village of Besh-Tash" where Ayyubov built his studio. *Resolution:* Kept both as adjacent villages ~1 km apart.
5. **Sary-Bulak District geometry.** Sary-Bulak (mine and district seat) is "~28 km south of Talas". The Chatkal smelter is "~30 km SW". Sary-Bulak District must also hold the lower Kara-Suu Canyon (State Route 1 enters the district at the canyon mouth ~20 km S, with a branch to the mine). Yet Kök-Oi/Besh-Tash, also ~20 km S, is in Talas District. Placing Sary-Bulak due south would put it inside the Besh-Tash valley. Canon also says "southern Chatkal and Talas Alatau foothills". A 2-hour bus ride for 28 km suggests a long mountain road. *Resolution:* Made the district a contiguous SW foothill belt. Kara-Suu canyon mouth placed SSW (~72.22 E), Besh-Tash SSE (~72.30 E), Sary-Bulak SSW at ~27 km straight-line (stated 28 km treated as road distance), Chatkal 30 km SW.
6. **Kara-Bulak description.** Canon calls it a "maize station". The wiki calls it a grain (wheat/barley) depot and market town in the "middle"/"central" Talas valley, 35 km W of Talas, with a 35-min bus ride. *Resolution:* Placed by the stated 35 km W, kind `town` (pop. 11,620).
7. **Kenkol fan vs Kara-Bulak.** Ming-Örük (Kara-Buura) is on the Kenkol fan. Kara-Bulak (Talas District) is 35 km W of Talas. So the Kenkol mouth must lie west of Kara-Bulak, although the real Kenkol may be farther east. *Resolution:* Ming-Örük put at 71.725 E, ~7 km W of Kara-Bulak and ~4 km E of Bakyyan (which is 8 km E of Kyzyl-Adyr).
8. **Kara-Buura corridor and Talas North Terminal.** The wiki puts the Talas North Terminal "north-west of Talas, in Kara-Buura District". The brief and canon put it at the end of a corridor west along the Turksib to the Kazakh frontier facing Shymkent. The Trans-Talas Highway is 230 km from the Kazakh border through Kyzyl-Adyr and Talas "toward" the Otmek Pass. A frontier near ~70° E makes that road longer than 230 km. *Resolution:* The terminal is not a settlement and is not included. The district label was moved west into the corridor (42.62, 71.15). No villages are named in the corridor.
9. **Northern Export Feeder length.** 85 km from the Nurzhan tank farm to the KazTransOil network "near Shymkent". Nurzhan (the site of real Shu) is ~370 km from Shymkent. Canon also says the feeder runs north-east. *Resolution:* Not a settlement and not mapped. Flagged for the pipeline layer.
10. **Kök-Jar.** The village is in the "upper Chatkal valley" and, per its school article, the "eastern Chatkal range". But the Kök-Jar Pass above it is "close to Irad's border with Uzbekistan", and the upper valley is far from the Uzbek frontier. *Resolution:* Placed in the upper valley (42.02, 71.90). The pass relation is treated as loose.
11. **Terek-Sai.** The lore says "in the Chatkal valley" (with the Isyk-Bulak springs nearby). The real Terek-Sai lies on the south-west side of the Chatkal range. *Resolution:* Used the approximate real location (`real-place`). Move it onto the Chatkal valley floor if strict lore fit is preferred.
12. **Shahr-i Nav founding.** The village was founded in 1962 "on a newly built branch canal", but the canal that serves it (Jangy-Aryk) was built in 1963–66. *Resolution:* No coordinate effect.
13. **Jon-Aryk "on the lower Chu south-west of Nurzhan".** The Chu passes north/north-west of the city, so south-west is away from the river. *Resolution:* Placed SW of the city on a canal, ~5 km out.
14. **Nurzhan "old quarter".** The admin table says "Urban districts include Dastgoh, the old quarter, and Navbahor". It is ambiguous whether the old quarter is a fourth district. *Resolution:* Treated Dastgoh as the old quarter: its own article and the city history both make it the medieval artisan site.
15. **Kara-Köl.** It lies below the Toktogul dam, where the switchyard and downstream stations are in the ISEZ, yet canon says Kara-Köl is on the tribal side. *Resolution:* Followed canon: ATR, Toktogul–Naryn zone, at its real location.
16. **Semiz: town or district.** The brief calls it a town ~25 min from Talas. The lore calls it a district of the city in the western corridor, ~9 km W of the centre, under the Talas city council. *Resolution:* Kind `suburb`, district "Talas" (city-governed), 9 km W.
17. **Kyzyl-Unkur.** Only the IradOne tremor story (Oct 2026) names it, with the epicentre "in the Kara-Unkur valley, a few km NE of Kyzyl-Unkur". The real village of this name may lie in a neighbouring valley. *Resolution:* Placed in the Kara-Unkur valley between Bazar-Korgon and Arslanbob, marked `placed`.
18. **Ozgörüsh.** The lore puts it on the lower Uzun-Akmat above the reservoir. A real village of that name exists, but I am not certain of its exact coordinates. *Resolution:* Marked `real-place` at an approximate position (41.96, 72.83). Verify.
19. **Qara-Chik checkpoint road.** The checkpoint is on "the road from Talas into the Talas Alatau". That road is distinct from State Route 1 (which has its own canyon-mouth checkpoint) and from the Aksay track. Kara-Oi is a short distance away on the ISEZ side, and Kalba is on the road between. *Resolution:* Put the road SE of Talas: Kalba → Kara-Oi → Qara-Chik (~17–21 km out).
20. **Moiynkum position relative to Nurzhan.** The Nurzhan article says the sands lie to the S and W. Besh-Moinok has farmland meeting the sands to the NW, and Kamyshtuu is on the "northern edge" of the irrigated land at the edge of the sands. *Resolution:* Took the sands as wrapping W–NW. Besh-Moinok and Kamyshtuu placed NW of the city.
21. **Boz-Korgon kind.** It is a fortified compound, not a town. The spec's kind list has no "compound". *Resolution:* Kind `town`, with the note making clear what it is.
22. **Talas Alatau width.** Several places are 20–28 km south of Talas "in the foothills", while the real crest is only ~30–35 km south. The Kara-Suu Canyon is 32 km long through the foothills. *Resolution:* Compressed the foothill belt. Canyon length taken as winding length. Upper Kara-Suu (Tanıp) and Chong-Kapka put at ~42.15–42.19 N.
23. **Kosh-Döbö / Aksay Plateau.** The plateau lies on the divide between the Talas and Uzun-Akmat headwaters in the eastern Talas Alatau. State Route 1 also crosses the range nearby (Otmek tunnel, Fergana Gateway at the Talas Alatau–Chatkal junction). *Resolution:* Plateau camps put at 42.13, 72.72, east of the Gateway corridor.

## 3. Places placed by guess (`confidence: placed`)

All 121 `placed` entries are consistent with their stated district or zone and terrain, but have no explicit distance. They fall into two groups:

**Weakly constrained.** The lore gives only a zone or district plus a terrain type, or a vague direction. These positions are essentially free choices and should be the first to move if the basemap or later lore disagrees:

- Soviet Centre (Talas): 42.521, 72.247
- Western Corridor (Talas): 42.522, 72.175
- Cottonwood Estates (Talas): 42.508, 72.152
- Northern Industrial District (Talas): 42.546, 72.252
- Mikrorayon Estates (Nurzhan): 43.613, 73.785
- Cathedral Hill (Iyık Janyl): 41.483, 72.386
- Lower Town (Iyık Janyl): 41.474, 72.368
- Kara-Oi (Talas): 42.405, 72.49
- Qara-Chik (Talas): 42.375, 72.525
- Kalba (Talas): 42.445, 72.44
- Ak-Terek (Talas): 42.432, 72.3
- Cholpon-Bulak (Talas): 42.622, 72.33
- Sabz-Kand (Talas): 42.478, 72.372
- Jangy-Kent (Talas): 42.478, 72.62
- Almaluu (Talas): 42.462, 72.56
- Arsha-Say (Talas): 42.415, 72.68
- Tash-Bulak (Talas): 42.42, 72.01
- Shagyldy (Talas): 42.602, 72.15
- Ak-Tash (Kara-Buura): 42.52, 71.47
- Taldy-Suu (Kara-Buura): 42.695, 71.615
- Ak-Döbö (Kara-Buura): 42.665, 71.52
- Sary-Döbö (Chu): 43.78, 73.42
- Kara-Suu (Talas Alatau): 42.15, 72.26
- Upper Besh-Tash (Talas Alatau): 42.23, 72.32
- Kyrk-Choro (Talas Alatau): 42.25, 71.2
- Kara-Kungey (Talas Alatau): 42.355, 72.6
- Karakol-Ashuu (Talas Alatau): 42.235, 73.11
- Ak-Kyya (Talas Alatau): 42.16, 73.55
- Kosh-Döbö (Talas Alatau): 42.13, 72.72
- Kök-Jar (Chatkal Highlands): 42.02, 71.9
- Kyzyl-Bel (Chatkal Highlands): 42.07, 72.05
- Teke-Tash (Chatkal Highlands): 42.06, 71.74
- Archaly (Chatkal Highlands): 41.79, 71.4
- Bel-Aldy (Chatkal Highlands): 41.64, 71.56
- Muz-Tör (Chatkal Highlands): 41.72, 71.7
- Jashyl-Köl (Chatkal Highlands): 41.795, 71.845
- Besh-Köl (Chatkal Highlands): 41.95, 71.72
- Jele-Döbö (Toktogul–Naryn): 41.855, 72.84
- Kara-Jylga (Toktogul–Naryn): 42.03, 73.05
- Tash-Köröö (Toktogul–Naryn): 41.96, 73.12
- Kara-Say (Toktogul–Naryn): 41.745, 73.15
- Kosh-Bel (Toktogul–Naryn): 41.67, 73.21
- Dary-Bulak (Toktogul–Naryn): 41.57, 73.3
- Kyzyl-Unkur (Fergana Rim): 41.22, 72.83
- Korgoncho (Fergana Rim): 41.105, 72.46
- Örüktü (Fergana Rim): 41.195, 72.615
- Boz-Adyr (Fergana Rim): 41.225, 71.95
- Kara-Jygach (Fergana Rim): 41.36, 71.98
- Bazar-Terek (Karatau): 42.96, 70.45
- Hauzdy (Karatau): 42.985, 70.9
- Tar-Say (Karatau): 43.12, 70.7
- Kyzyl-Döbö (Karatau): 43.06, 70.25
- Bitik-Tash (Karatau): 43.33, 70.05
- Kök-Say (Karatau): 43.54, 69.7
- Tuzduu (Karatau): 43.22, 69.32
- Sasyk-Bulak (Karatau): 43.65, 68.88
- Ak-Jar (Karatau): 43.9, 68.72
- Tört-Kuduk (Northern Steppe): 44.35, 73.35
- Ak-Jal (Northern Steppe): 44.4, 73.85
- Kaiyrma (Northern Steppe): 44.05, 72.95
- Kamyshtuu (Northern Steppe): 43.81, 73.56
- Tash-Kuduk (Northern Steppe): 43.6, 72.15
- Ak-Chiy (Northern Steppe): 43.45, 72.75
- Zhalgyz-Terek (Northern Steppe): 43.95, 71.8
- Töö-Kuduk (Northern Steppe): 44.2, 70.8

**Moderately constrained.** The lore gives a direction from a city, a named river or confluence, or a neighbouring feature:

Köhne Diz (42.527, 72.228), Bazar-i Kalan (42.526, 72.234), Shahr-i Kabud (42.536, 72.226), Alatau Heights (42.488, 72.278), Dastgoh District (43.603, 73.715), Navbahor District (43.572, 73.762), Central District (43.601, 73.761), Eastern Industrial Zone (43.597, 73.815), NurGaz Worker Housing Complex (43.628, 73.752), Shahr-i Khunuk (41.488, 72.398), Talas District (42.47, 72.52), Kara-Buura District (42.62, 71.15), Chu District (43.5, 73.95), Sary-Bulak District (42.32, 72.1), Lower Naryn District (41.4, 72.3), Northern Steppe (44.55, 71.8), Karatau (43.35, 69.9), Talas Alatau (42.18, 72.55), Chatkal Highlands (41.8, 71.6), Toktogul–Naryn (41.82, 73.0), Fergana Rim (41.15, 72.55), Tegirmen (42.553, 71.965), Sarymsakty (42.522, 72.395), Kümüshtü (42.445, 72.8), Besh-Tash (42.35, 72.292), Uuk-Bulak (42.448, 72.12), Jangy-Jol (42.488, 72.05), Köpürö-Bazar (42.54, 72.168), Teskey-Jar (42.43, 72.9), Toguz-Bulak (42.58, 72.745), Ming-Örük (42.575, 71.725), Eski-Korgon (42.705, 71.42), Chet-Bulak (42.725, 71.56), Ak-Bulak (42.372, 72.085), Tunuk-Bulak (42.335, 72.17), Besh-Terek (43.618, 73.555), Shahr-i Nav (43.695, 73.815), Besh-Moinok (43.755, 73.5), Jon-Aryk (43.555, 73.6), Kum-Aryk (43.592, 73.85), Kök-Döbö (43.485, 73.905), Aral (43.665, 73.625), Uch-Emchek (43.585, 73.635), Kapka-Tash (41.28, 72.17), Jyluu-Bulak (41.405, 72.27), Bulak-Bashy (41.44, 72.345), Altyn-Bulak (41.405, 72.195), Chong-Kapka (42.188, 72.24), Kara-Koyun (42.385, 71.65), Kashka-Jol (42.385, 71.535), Kyrk-Bulak (42.43, 71.4), Orto-Ayyl (42.4, 73.02), Otmek (42.3, 73.22), Karakol (42.1, 73.3), Sopol-Tepa (41.075, 72.69), Jangak-Bulak (41.335, 72.835).

**Stated and anchor entries** are fixed by explicit distances or by the brief's anchors:

Talas, Nurzhan, Iyık Janyl, Boz-Korgon, Semiz, Kara-Bulak, Kök-Oi, Kyzyl-Adyr, Bakyyan, Sary-Bulak, Chatkal, Shaar-Döbö, Temirchi, Tash-Kömür.

**Real-place entries** use approximate real-world coordinates:

Kanysh-Kiya, Terek-Sai, Arkyt, Toktogul, Kara-Köl, Ozgörüsh, Bazar-Korgon, Arslanbob, Mailuu-Suu.
