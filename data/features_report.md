# Irad gazetteer: landmarks, POIs, natural features, infrastructure

Files: `features.json` (355 point features), `routes.json` (31 lines). Settlements (towns, villages, city quarters) are deliberately excluded; they are in `settlements.json` from the settlements gazetteer.

Coordinates are WGS84 decimal degrees; route coords are `[lon, lat]`. Each route also carries `length_km_drawn` (great-circle length of the drawn polyline, which runs shorter than real winding roads).

## Counts

### Features by kind

| kind | n |
|---|---|
| other | 47 |
| industry | 36 |
| landmark | 35 |
| river-point | 25 |
| heritage | 16 |
| government | 14 |
| lake | 14 |
| pass | 14 |
| ruins | 13 |
| hospital | 10 |
| park | 10 |
| museum | 9 |
| school | 9 |
| church | 8 |
| military | 8 |
| mine | 8 |
| peak | 8 |
| power | 8 |
| spring | 7 |
| stadium | 7 |
| market | 6 |
| checkpoint | 5 |
| university | 5 |
| border-crossing | 4 |
| mazar | 4 |
| oilfield | 4 |
| terminal | 4 |
| dam | 3 |
| station | 3 |
| airport | 2 |
| bus-station | 2 |
| mosque | 2 |
| reservoir | 2 |
| un | 2 |
| hippodrome | 1 |
| **total** | **355** |

### Features by confidence / zone

- confidence: placed 307, real-place 30, stated 15, anchor 3
- zone: ISEZ 246, ATR 109
- with a wiki article title: 338

### Routes by kind

| kind | n | drawn km |
|---|---|---|
| highway | 3 | 476 |
| road | 10 | 667 |
| railway | 8 | 559 |
| pipeline | 4 | 532 |
| canal | 4 | 136 |
| power-line | 2 | 347 |

Routes: `trans-talas-highway` (251.8 km); `fergana-mountain-transit-highway` (153.4 km); `iyik-janyl-branch-road` (9.8 km); `irad-temir-jolu-chu-line` (224.5 km); `irad-temir-jolu-talas-branch` (89.9 km); `irad-temir-jolu-kara-buura-line` (102.6 km); `irad-temir-jolu-north-line` (59.7 km); `irad-temir-jolu-east-line` (38.9 km); `irad-temir-jolu-sary-bulak-spur` (29.3 km); `irad-temir-jolu-chatkal-spur` (12.4 km); `irad-temir-jolu-taez-siding` (1.4 km); `talas-nurzhan-road` (313.7 km); `kok-bel-road` (185.5 km); `chu-highway` (70.6 km); `boz-korgon-branch` (1.7 km); `sary-bulak-road` (10.4 km); `chatkal-smelter-road` (35.4 km); `qara-chik-road` (31.2 km); `kenkol-military-road` (30.1 km); `karakol-road` (21.7 km); `lower-naryn-uzbek-road` (27.7 km); `nurzhan-petroleum-pipeline` (70.6 km); `northern-export-feeder` (85.3 km); `talas-air-base-products-pipeline` (307.8 km); `muyunkum-gas-line` (67.9 km); `chu-irrigation-main-canal` (93.6 km); `eski-aryk` (16.3 km); `jangy-aryk` (22.2 km); `kashkar-aryk-canal` (3.9 km); `toktogul-north-export-line` (273.3 km); `toktogul-south-export-line` (74.0 km)

## Anchors and method

- I used the fixed anchors exactly: Talas 42.520, 72.240 (Central Square); Nurzhan 43.600, 73.760 (central square); Boz-Korgon 43.580, 74.250. Iyık Janyl 41.480, 72.380, Tash-Kömür 41.350, 72.220 and Kyzyl-Adyr 42.620, 71.580 served as reference points for nearby features. They are not entered as features themselves, because they are settlements.
- Features that exist in reality carry `real-place` and use my best knowledge of the real location: Toktogul dam and reservoir, the Kurpsai, Tash-Kömür, Shamaldy-Sai and Uch-Kurgan stations, Manas Peak, Otmek and Kara-Buura passes, Kyzyl-Adyr (Kirov) Reservoir, Sary-Chelek, Arslanbob, Aksu-Zhabagly, Mailuu-Suu tailings, Suusamyr, Karatau, Moiynkum, Betpak-Dala and Akzhaykyn. The lore gives its own names for some of them, and those names are used.
- `stated` means the lore gives a distance and direction from an anchor that fixes the point, for example "12 km W of Talas" or "3 km S of Iyık Janyl". `placed` means my judgement from looser clues.
- Talas city layout used: the Kokand citadel (Köhne Diz) and Old City lie about 2.5 km W of the centre on the terrace above the river. Bazar-i Kalan is on the Old City's eastern edge. The Russian grid town and Soviet centre lie east of the citadel. Alatau Heights and TSU are to the SE. The western corridor runs out to Semiz (about 9 km W), the TAEZ (west of Semiz) and the air base (12 km W). The Talas River runs along the north edge of the city.
- Nurzhan layout used: Dastgoh is west on a Chu branch, Navbahor south and the eastern industrial zone east (refinery, data centre, NAI, Zhetysu). The gas compressor and the NurGaz housing are north, and the railway station and freight depot NE.

## Contradictions and ambiguities, and how I resolved them

1. **Nurzhan Petroleum Pipeline length.** The canon and the Transport article give about 90 km. The Northern Export Feeder article gives 118 km. The canon "common errors" list says "not 118", so I drew about 90 km from a collection station WNW of Nurzhan. The drawn line is 71 km because straight segments shorten the route; the real line would wind through the field gathering network. I kept the station at 43.73, 73.02, south of the Chu: the settlements file puts the ATR villages of Kamyshtuu and Kaiyrma just to the north, and the station must stay inside the ISEZ Chu District.
2. **Iyık Janyl to Tash-Kömür.** The Tash-Kömür article says 18 km NE, while the canon says about 20 km ("not 18"). I used 20 km, which matches the anchors.
3. **Sary-Bulak and Chatkal, "southern" or "northern" foothills.** The SBAW, Chatkal and 1971-directive articles say the southern foothills of the Talas Alatau. The Talas Alatau article says the northern foothills south of Talas. All of them give 28 km S (Sary-Bulak) and 30 km SW (Chatkal) of Talas. I followed the distances, which put both sites on the north-facing foothills S and SW of Talas. The real Chatkal valley lies beyond the crest.
4. **Rabat-i-Safed.** Its article and the Oct 2026 Herald and IradOne stories put it 25 km E of Talas on the road toward the Chu. The Transport article implies desert stages to the west. I used 25 km E.
5. **Talas North Terminal.** The canon puts it on the Kazakh frontier facing Shymkent, at the end of the Kara-Buura corridor; the Herald's customs story is datelined Kyzyl-Adyr, which fits. A Tulpar chat post links a lane closure "near the North Terminal" to a late Talas–Semiz bus, which would put it much closer to Talas. I kept the canon position (42.47, 70.30, the real Tulkubas area) and treated the chat post as hearsay.
6. **Trans-Talas Highway length.** The lore gives about 230 km from the frontier through Kyzyl-Adyr and Talas "toward the Otmek Pass". With the terminal at 70.30 E, the paved road to the Qara-Chik line comes to about 205 km drawn. The gravel track on to the Otmek Pass brings the total to 252 km drawn.
7. **Fergana Mountain Transit Highway.** The lore gives 236 km in total and 142 km for the mountain section. The drawn line is 155 km because straight segments cut the switchbacks. Waypoints follow the stated sequence: about 20 km of farmland, then the Kara-Suu Canyon, the Otmek Tunnel, the Gateway at 2,480 m, the Naryn below the dam, the switchyard, Kurpsai and Tash-Kömür. The 12 km Iyık Janyl branch leaves about 13 km above Tash-Kömür.
8. **Fergana Gateway.** The lore places a 2,480 m pass at the junction of the Talas Alatau and Chatkal ranges. No real road pass that low exists there; the real Ala-Bel is 3,184 m and further east. I placed it at the range junction between the Kara-Suu Canyon and the Toktogul dam (41.97, 72.42).
9. **Irad Temir Jolu (~580 km).** The lore describes several parts:
   - a Chu line through Nurzhan;
   - a Nurzhan–Talas line that takes the lowland route around the western end of the Kyrgyz Range;
   - a "Talas line north" to the Kazakh network through the Talas North Terminal;
   - a branch that made Talas a railway terminus;
   - spurs to Sary-Bulak, Chatkal, Kara-Bulak and the TAEZ;
   - a rail-only border station north of Nurzhan.

   I modelled this as the real Turksib from Nurzhan west to a junction at the western end of the Kyrgyz Range (the real Taraz area). From the junction, a Kara-Buura corridor line runs west to the terminal and a Talas branch runs up the valley via Kyzyl-Adyr and Kara-Bulak. A north line runs from Nurzhan to the border station, plus the industrial spurs. I also drew a stub east to Boz-Korgon, inferred from "the road and rail corridor east from Nurzhan". The drawn total is 559 km, which fits "about 580" once track curvature is allowed for.
10. **Taraz.** The real city of Taraz lies inside the Jambyl footprint but has no counterpart in the lore. Iradi historiography identifies medieval Taraz with Talas. The rail and road junction sits at the Taraz location with no feature, and the settlements helper should know about this gap.
11. **Northern frontier near Nurzhan.** The Qara-Chik northern sector "rejoins the Kazakh border east of the city". The rail border station lies "north of the city", and the Export Feeder runs 85 km NE to the "eastern Kazakh frontier". I placed the border station NNE (44.05, 74.19) and the Feeder metering station NE (44.18, 74.56). That leaves an ISEZ wedge NE of Nurzhan, with the frontier running roughly N–S along 74.5–74.6 E down to the Chu Gate (43.53, 74.63).
12. **Northern Export Feeder.** It runs NE to the eastern frontier, yet feeds KazTransOil "near Shymkent", which lies far west. I drew it NE as stated and took the Shymkent connection to be on the Kazakh side.
13. **Kyzylkum Fringe and the 2018 clashes "with Uzbek border guards".** In real geography the Syr Darya side NW of Turkistan city is Kazakh, and Uzbekistan's Kyzylkum frontier lies SW of Shymkent, which is outside Irad. I placed the Fringe on the SW Karatau foothills facing the Syr Darya (43.60, 68.75, beside the settlements file's Ak-Jar and Sasyk-Bulak) and flag that the Uzbek frontier there exists only in the lore.
14. **Talas River share.** A 50/50 split with Kazakhstan and a border gauge sit oddly with a river that dies in the Moiynkum inside Irad. I put the "Talas border gauge" where the river leaves the irrigated lower valley (43.00, 71.30). The terminus is a separate river-point in the western Moiynkum.
15. **Toktogul capacity.** The canon gives 1,200 MW. The IradOne and Herald stories of 13 Oct 2026 report 1,440 MW after a refit. The note gives both.
16. **Kara-Köl and the switchyard.** The tribal workers' town of Kara-Köl lies just below the dam, while State Route 1 and the ISEZ switchyard are also "below the dam". I put the Naryn bridge checkpoint at the crossing and the switchyard and dispatch centre on the west bank downstream (41.64, 72.615).
17. **Sary-Bulak works status.** It is described as the district's largest employer, but the Oct 2026 Herald and IradOne stories describe idle lines and a phased restart in 2026–27. This is noted on the feature.
18. **Ayyubov house-museum.** The canon gives "Besh-Tash (upper valley; Ayyubov museum)", but the upper Besh-Tash valley is on the tribal side. At first I placed it mid-valley on the ATR side. I then moved it to the settlements file's Besh-Tash village at the valley mouth beside Kök-Oi (ISEZ), so the two files agree.
19. **Kara-Suu Canyon and Besh-Tash.** Both lie about 20 km S of Talas, and the upper Kara-Suu is partly inside the Besh-Tash conservation area. I put the canyon immediately west of Besh-Tash, with the Sary-Bulak gorge to its west. The settlements file puts Chong-Kapka (the rock gateway) at 42.19 and Kara-Suu village at 42.15 on the tribal side, so State Route 1 follows only the lower, ISEZ part of the canyon (to about 42.24). It then climbs east through avalanche galleries to the Otmek Tunnel (42.11, 72.32), keeping the ISEZ corridor clear of the tribal villages.
20. **Two Otmeks.** The Otmek Tunnel on State Route 1 and the Otmek Pass on the old Talas–Suusamyr road are kept apart, as the lore insists.
21. **Qara-Chik checkpoint and Kara-Oi.** The checkpoint is "on the road from Talas into the Talas Alatau", with UNMI's Kara-Oi "a short distance away on the ISEZ side". The direction is not given, so I aligned both with the settlements file's Qara-Chik, Kara-Oi and Kalba villages, SE of Talas: checkpoint at 42.373, 72.522 and UNMI at 42.404, 72.488. The road runs Talas–Kalba–Kara-Oi–Qara-Chik.
22. **Muyunkum gas field.** It lies "beneath the NE Moiynkum near the lower Chu". The Moiynkum is S and W of Nurzhan and the Chu runs NW from the city, so I placed the field NW of Nurzhan near the river (43.88, 72.80).
23. **Nurzhan Botanical Gardens.** Its "eastern edge" location clashes with the eastern industrial zone, so I shifted it SE.
24. **Church of St. Janyl dome.** One article gives a 22 m dome and the other about 28 m to the top of the cross. This does not affect position.
25. **Suusamyr.** The Iradi part of the valley is in the ATR, but the real Suusamyr village is Kyrgyz. Features are placed in the western (Iradi) part of the valley.
26. **Left out.** I did not include the following:
    - the five unnamed US installations ("logistics depots, a testing facility and training areas");
    - the 2007 "UN compound outside the city";
    - Bektur's homestead in the Kara-Suu Canyon (a private residence);
    - embassies and trade offices: the ISEZ "maintains no embassies", no foreign mission in Irad is described, and Mexico has only a mobile consular team;
    - the Orto-Sai Reservoir, which is outside Irad and outside the coordinate box;
    - the proposed Trans-Irad Gas Pipeline, which is unbuilt;
    - Toktogul town, Kara-Köl, Mailuu-Suu, Arkyt, Alatau Heights, Cottonwood Estates and other settlements or quarters, which belong to the settlements file.
27. **Reconciled with `settlements.json`.** The settlements gazetteer appeared in the same folder during this work. I moved about 100 features to match its village and quarter coordinates:
    - Old City cluster: citadel, gates, Juma Mosque, St. Yuhanna and Sarchashma moved to sit around its Köhne Diz/Bazar-i Kalan quarter (42.527, 72.228);
    - Qara-Chik, Kara-Oi and Kalba;
    - Kara-Suu, Chong-Kapka and Besh-Tash;
    - Tash-Bulak (so the Muz-Suu and Muz-Köl moved west to about 72.02 E), Tegirmen, Tunuk-Bulak, Arsha-Say, Jangy-Kent and Kümüshtü;
    - Ming-Örük and Kara-Koyun (so the Kenkol and Kara-Koyun valleys were re-sorted, Kenkol at about 71.74 and Kara-Koyun at about 71.64);
    - Kyrk-Choro (so Manas Peak moved to 42.135, 71.22 under the north face);
    - Kök-Jar, Kyzyl-Bel, Besh-Köl, Jashyl-Köl, Muz-Tör and Terek-Sai;
    - Besh-Terek, Sary-Döbö, Shaar-Döbö, Shahr-i Nav and Kök-Döbö;
    - Hauzdy, Bitik-Tash, Tar-Say, Tuzduu (so Kulan-Talaa moved to about 69.2 E), Sasyk-Bulak and Ak-Jar;
    - Ak-Jal (so Keng-Talaa moved to 44.45, 73.6), Ozgörüsh, Karakol, Karakol-Ashuu, Kosh-Döbö, Jyluu-Bulak and Altyn-Bulak.

    The two files may still differ in small ways. The settlements file has its own entries for some landmark-like names (Bazar-i Kalan, Cathedral Hill, Köhne Diz, Boz-Korgon) as quarters or compounds; my point features for those sit within a few hundred metres of its points.
29. **Manas Peak position.** My first placement used about 42.12, 71.72. The lore puts the peak at the junction with the Pskem and Ugam ranges, and the settlements file puts Kyrk-Choro below its north face at 71.20 E, so I used 42.135, 71.22. The real summit position should be checked against a map before publication.
28. **Russian names.** These are mechanical transliterations of the Iradi Latin (о/у used for ö/ü). Standard Russian forms are used where a real place has one, for example Токтогульская ГЭС, Таш-Кумыр, Сары-Челек and Аксу-Жабаглы. Iradi forms come from the lore where it gives them; the rest are Kyrgyz-based renderings, marked by generic terms such as *ashuusu*, *kölü*, *kapchygayı* and *GESi*.


## Features placed by guess (`confidence: "placed"`)

The lore names these features and usually gives a relation such as "X km S of Talas", "in the eastern industrial zone" or "near the cathedral", but no coordinates. I placed them using those clues, the real terrain, the anchor points and the settlements file. Treat the positions as plausible, not surveyed.

- **Talas** (82): Government House; Legislative Hall; Hall of Justice (Supreme Court of Irad); Talas District Court; Talas City Hall; Bank of Irad head office; Silk Road Financial Tower (Talasbank HQ); Altyn Tower; Miners' Hall; General Staff complex; Central City Park; The Hunter's Vigil; Widow's Horse Memorial; Talas Central Post Office; National Historical Museum of Irad; Talas Philharmonic Hall ("Tündük"); Talas Opera and Ballet Theater; Talas State Academic Drama Theatre; Talas municipal theater (Town Hall Meeting site); National Conservatory of Folk Music; Cinema Boulevard; Talasfilm Archives and Film Preservation Institute; Talasfilm Studios; Alikhan Media Center (IradOne HQ); IradOne Transmitter Mast (Television Hill); Communications Square (Attelkom HQ); Köhne Diz (Talas citadel); Kalan Darwaza; Temir-Kapka Gate; Coppersmiths' Row (Misgaron); Bazar-i Kalan; Juma Mosque (Talas); Church of St. Yuhanna (Talas); Sarchashma Springs and bathhouse; Iradi Telegraph Office; Kara-Khanid minaret foundations; Jibek Jolu clothing market; Talas Central Bus Station; Talas Municipal Bus Depot; Talas railway station; Silk Road Arena; Irad State Hippodrome; Irad Central Sports Complex; Attelkom Park; TSU Stadium; Talas State University; State Archives of Irad; Talas Pedagogical Institute; Talas Gendarmerie Academy; Talas Veterinary Research Center; Talas Regional Hospital Medical Complex; Talas Municipal Hospital No. 1; Talas Blood Services Center; St. Luka Clinic; St. Luka Hospital; St. Maryam Catholic Academy; Talas Municipal Gymnasium No. 4; Talas American School; Talas Youth Soccer Academy; Church of St. Tomas (Talas); Talas Pre-Trial Detention Center; Talas women's colony; Talas Municipal Fire Brigade HQ; Talas Fire Station No. 2; Talas Municipal Water Treatment Works; Talas city landfill; Talas Municipal Cold Storage; Talas Free Economic Trade Zone; Talas Customs Clearance Terminal; Iradi Leatherworks Factory; Talas Dairy Processing Combine; Talas Agribusiness Export Zone (TAEZ); Sukarne Irad Complex; Sukarne Feedlot Complex; Sukarne Quality Control Labs; Conagra Talas Beef Facility; Talas Cold Chain Logistics Hub; Talas Central Cattle Mart; Talas Airport Logistics Hub (Iradiya terminal); Barysh Rapid Reaction Strike Group base; Kashkar-Aryk; Talas River (at Talas)
- **Semiz** (5): Church of St. Yusup the Worker; Semiz market (el mercado); Semiz water tower; Lienzo Charro de Semiz; Semiz cemetery
- **Nurzhan** (35): House of Soviets (Nurzhan city administration); Azatlık Prospect; Palace of Metallurgists; Nurzhan Municipal Library; Nurzhan Polytechnic Institute; NurGaz headquarters; NurGaz Stadium; Lokomotiv Stadium; Nurzhan railway station; Nurzhan Rail Freight Depot; Nurzhan Oil Refinery; Nurzhan Asphalt and Bitumen Plant; Nurzhan ammonia works; NurGaz tank farm (Feeder head station); Attelkom Data Center; Nurzhan Central Grain Terminal (NAI); Zhetysu Industrial Textiles; Nurzhan Heavy Machine Plant; NurGaz Pipeline Maintenance Depot; Dastgoh Creek; Nurzhan Gas Compressor Station; Nurzhan central heat and power plant; Navbahor Pond; Navbahor solar-powered school; Nurzhan Botanical Gardens; Nurzhan Municipal Botanical Institute; Nurzhan Children's Polyclinic; Nurzhan Emergency Dispatch Center; Nurzhan Technical Lyceum; St. Teresa Community Kitchen; Nurzhan synagogue and Jewish community center; Nurzhan madrasa; IradOdin regional studio; 2nd Motor Rifle Brigade base; Chu Basin Hydrological Station
- **Iyık Janyl** (10): Church of St. Janyl; Cathedral Hill; Iyık Janyl Monastic Cloister; St. Ephrem Major Seminary (Cathedral Seminary); Cathedral Seminary Library of Iyık Janyl; Iyık Janyl Diocesan Archives Vault; Iyık Janyl Pilgrimage Hostel; Irad Palace of Art; Motherhouse of the Order of St. Janyl the Hermit; Khunuk Creek
- **Tash-Kömür** (5): Tash-Kömür airstrip; Tash-Kömür coal mines; UNMI Lower Naryn sector HQ; Lower Naryn Mountain Rifle Battalion; Lower Naryn district hospital
- **rural ISEZ** (86): Talas Air Base foothill radar stations; 1st Mechanized Infantry Brigade base; Kok-Tash Kariz System; Kand-i Nau; Shelji; Taldy-Bulak petroglyphs; Jety-Kaiyng; Akyel Breeding Sanctuary; Kyzyl-Jyldyz stud; Arstanov stud farm; Talas Solar Park (Boz-Tektir); Boz-Tektir; Kara-Bulak Grain Logistics Depot; Kara-Bulak station; Kara-Bulak maize station; Kara-Bulak kurgans; Urmaral River (Tegirmen confluence); Kashka-Suu River (lower course); Muz-Suu River (canal intakes); Qara-Chik Border Checkpoint; UNMI Headquarters, Kara-Oi; Besh-Tash National Park; Besh-Tash Timber Concession; Yusup Ayyubov house-museum; Kemel Ishakov house-museum; Kara-Suu Canyon; Kara-Suu Canyon petroglyphs; Kara-Suu Hydroelectric Station; Kara-Suu Canyon checkpoint (State Route 1 northern post); Sary-Bulak Gorge; Chatkal Tailings Repository; Chatkal Mountain Rescue Base; Chatkal Primary Health Post; Kyzyl-Jar Antimony Shafts; Maryam-Bulak; Ak-Kyr; Kyrk-Kazyk Caves; Chatkal Wildlife Protection Post; Sary-Bulak Mountain Rifle Battalion; Otmek Tunnel; Fergana Gateway; Fergana Gateway summit checkpoint; Toktogul switchyard and national dispatch centre; Naryn bridge checkpoint (below Toktogul dam); Jyluu-Bulak sanatorium; Altyn-Bulak mineral water plant; Diz-i Safid; Talas North Terminal; Ak-Tash Training Center; Ak-Tash sanatorium; Ak-Tilek Ranch; Kyzyl-Adyr district hospital; Kyzyl-Adyr Hills; Ambar-Döbö; Karool-Döbö; Kenkol burial ground; Kuru-Say; Ichke-Suu Gorge; Kapka-Bel; Eski-Korgon fort; Ak-Döbö settlement mound; Kara-Buura River; Kenkol Mountain Meteorological Post; Talas border gauge; Xinjiang Lihua spinning complex; Chu Correctional Colony; Chu Gate crossing; Nurzhan rail border station; Kum-Shagyl crossing; Northern Export Feeder metering station; Chu oil fields; Uzun-Kyr; NurGaz main field collection station; Diz-i Zard; Shahr-i Nav ruins; Chui Sugar Refining Corporation factory (Besh-Terek); Chui Cotton Inspection Directorate laboratories; Xinjiang Lihua No. 3 Gin; Kök-Döbö weather radar; Sary-Kyr; Boz-Suu diversion weir; Kyzyl-Suu (Chu tributary); Chu Irrigation Canal System headworks; Chu River (entry into Irad); Naryn River (leaving Irad); Kök-Bel Pass
- **ATR** (84): Besh-Tash Lower Tarn; Besh-Tash Upper Lake (Lake Besh-Tash); Kara-Suu cave chapel; Manas Glacier; Manas Peak Glaciological Observatory; Kök-Suu Peak; Rabat-i Sangin; Kenkol Pass; Chong-Kenkol; Kara-Koyun Valley; Karakoyun Pass; Grave of Muratbek Biy; Urmaral Tarns; Kyzyl-Köl; Kara-Suu Rapids; Kara-Suu Gold Prospecting Area; Kara-Suu Rural Health Center; Kara-Suu Tribal Elders Council Hall; Tegerek-Köl; Köl-Sai glacial lake; Kashka-Suu Glaciers; Tuyuk-Suu Pass; Aksay Plateau; Kurultai ground (Aksay Plateau); Achuu-Köl; Aksay Emergency Shelter; Talas River headwaters (Karakol and Uch-Koshoi); Karakol-Ashuu; Karakol Glacier; Karakol Mountain Logistics Depot; Suusamyr Wool Washing Mill; Ak-Suu Mineral Springs; Kyzylkum Fringe; Kulan-Talaa; Kulan-Sor; Karakyr Range; Kyzyl-Jar badlands; Kök-Moinok; Teshik-Talaa; Bürküt-Uya; Rabat-i Kamal; Bitik-Tash petroglyphs; Keng-Talaa; Mazar-Too; Kaz-Köl; Kalmak-Kuduk; Kumdy-Bulak; Muyunkum Natural Gas Field; Talas River terminus; Uch-Terek Rapids; Naryn River (entry into Irad); Uzun-Akmat River (mouth); Uzun-Akmat Terraces; Tar-Kapchygai; Ak-Muz; Koi-Bel; Kök-Art Pass; Shrine of Arslanbob-Ata; Kara-Unkur Cave; Kök-Kamar Gorge; Kum-Say Fan; Tuura-Say; Chopo-Jar; Sadaf-Jar; Kichi-Bel; Jangak-Bulak sacred walnut grove; Chatkal River (middle valley); Chatkal Gorge; Chatkal Snow Leopard Sanctuary; Kök-Jar Pass; Kök-Jar antimony exploration mine (disused); Kök-Jar Primary School; Terek-Sai mines; Isyk-Bulak; Ak-Bash; Kylych-Kyr; Kara-Kazan Cirque; Besh-Köl Glaciers; Kyzyl-Bel Pass; Altyn-Say; Ak-Balyk Creek; Chakmak-Say; Kum-Bel gold prospect; Jashyl-Köl

The drawn courses of all routes are also my placement: they follow real valleys, the real Turksib, real roads and the lore descriptions. The two Toktogul export power lines, the Chu main canal and the products pipeline are schematic, because the lore names these lines without tracing them.
