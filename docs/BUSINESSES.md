# Businesses on the map, and the Iradi companies invented for them

`build/make_businesses.py` fills a city with everyday businesses (restaurants, cafés, chaikhanas, groceries,
supermarkets, pharmacies, banks, fuel, hotels, shops). They come from the real donor city's OpenStreetMap data,
moved with its street plan (`build/make_cities.py`), so they sit where businesses really cluster. **No donor-city
business name is kept** (they are real shops in a real city). Every business gets an Iradi name from `build/biz_names.py`.
International brands may appear where the lore puts them (KFC Irad), never in a bad light (`RULES.md` 3 in the desk repo). Output: `data/biz/<city>.json`, listed in
`data/biz/index.json` (format: `docs/PLACES.md`).

    build/base/extract_poi.cpp   # g++ ... -o extract_poi; extract_poi kyrgyzstan.osm.pbf 74.40 42.74 74.80 43.00 > bishkek_poi.ndjson
    python3 build/make_businesses.py bishkek_poi.ndjson talas

The same input always gives the same businesses, names and hours.

Done so far: **Talas** (from Bishkek), about 3,100 businesses; **Nurzhan** (from Shymkent), 2,300; **Iyık Janyl** (from Osh), 800.
Shymkent and Osh are thinly mapped, so those two are topped up along their main streets with Talas's mix of kinds
(`fill_to`). Their plans are moved by `make_cities.py` itself: `MOVE_POIS=<city>:<in.ndjson>:<out.ndjson> python3 build/make_cities.py ...`.

## Companies and brands invented for the map

Some of these are now in the lore (Bereke, Jıldız Market, Shıpa Dariykana, Ak Bata Bank, Chuy Commercial Bank: see quickref);
the rest are still to adopt into canon, rename or drop.

| Name (Iradi / English / Russian) | What | In Talas (and the others) |
|---|---|---|
| **Bereke** / Bereke Supermarket / Береке | Supermarket chain, the biggest (*bereke*: plenty) | 76 stores (Nurzhan 53, Iyık Janyl 15) |
| **Jıldız Market** / Jıldız Market / Жылдыз Маркет | Second supermarket chain (*jıldız*: star) | 40 stores (Nurzhan 36, Iyık Janyl 6) |
| **Shıpa Dariykana** / Shıpa Pharmacy / Аптека «Шыпа» | Pharmacy chain (*shıpa*: cure) | 34 pharmacies (Nurzhan 23, Iyık Janyl 14) |
| **Chüy Kommertsiyalık Banky** / Chuy Commercial Bank / Чуй Коммерческий банк | Commercial bank, one of the "other banks" the Bank of Irad Clearing House implies | 12 branches (Nurzhan 16, Iyık Janyl 5) |
| **Ak Bata Bank** / Ak Bata Bank / Ак Бата Банк | Commercial bank (*ak bata*: blessing) | 24 branches (Nurzhan 15, Iyık Janyl 4) |
| **Hotel Bazar-i Kalan** / Meymankana Bazar-i Kalan | A name for the lore's unnamed 2018 hotel on the site of the demolished 1910 merchant house by the covered market | 1 |

Numbered state pharmacies ("Pharmacy No. 22", *22-Dariykana*, Аптека № 22) are a type, not a company: Soviet-style
numbering kept on, numbers 1–60.

## Lore companies used, and how far the map takes them

| Lore | On the map | Beyond the lore |
|---|---|---|
| Talasbank (28 branches) | 20 in Talas, 6 in Nurzhan, 2 in Iyık Janyl | Where the branches are |
| Transoxiana Microfinance Fund | 5 offices | The number of offices |
| NurGaz (makes the petrol and diesel; refuses Tulpar Pay) | Brand of about 60% of filling stations (65 in Talas, 43 in Nurzhan, 11 in Iyık Janyl) | NurGaz as a fuel-station brand |
| KFC Irad (the only foreign chain named) | 4 restaurants in Talas (by Central Square, by the Silk Road Arena, on the strip toward the air base, in Alatau Heights); 2 in Nurzhan (by Central Square, in Navbahor) | The locations; KFC Irad in Nurzhan |
| Tulpar delivery partners | Chaikhana Bakyt (Bazar-i Kalan), Taquería Semiz (Semiz), Altyn Tower Pizza (by Altyn Tower), Nan & Boorsok (near Central Square), Shashlyk Kara-Suu (east edge, on the Kök-Bel road side) | Their exact spots |
| International Diplomatic Hotel (TCDG) | Off Central Square, on the central avenue | Its location |
| Tulpar delivery generally | About 40% of eateries show "Delivery with Tulpar" | |

## Nurzhan and Iyık Janyl

Places the lore mentions without a name or a spot, given one on the map (to adopt or correct):

| Map | Lore | Beyond the lore |
|---|---|---|
| **Radiobazar** / Nurzhan Radio Bazaar / Радиобазар, a block west of Azatlık Prospect's south end, with radio, phone and computer stalls round it | "the Nurzhan radio bazaar … the last row" | Its location |
| **Dastgoh bazarı** / Dastgoh Market, in the Dastgoh District | "Dastgoh market" (forum): forge goods, plastic-tunnel vegetables | Its location |
| **Kotelnaya** / Котельная ("the boiler room"), café in Dastgoh | "Former boiler room under a block in Dastgoh is now a café with mor-wave on vinyl" (forum) | The name |
| Talasbank's **Azatlık branch** | "on the 10th of every month the Talasbank on Azatlık has a queue" | Its spot on the prospect |
| **Iyık Janyl bazarı** / Iyık Janyl Bazaar / Ийык-Джанылский базар, the Lower Town | "old bazaar centre"; livestock and wool markets where ATR herders trade | The name and spot |

What each city's mix follows:

- **Nurzhan** (the Russo heartland): about 40% of names Russian and the shop sign is *Magazin* (canon: Nurzhan says
  *magazin*, not *dükön*); canteens (*stolovaya*, 52, some numbered "Canteen No. 7" the Soviet way); banquet halls for
  weddings (10); Russian and Koryo-saram cuisine as common as Iradi (kuksi, Koryoin laghman); fewer chaikhanas; Navbahor
  (oil staff, shopping centres) gets European, American, pizza, sushi and coffee places. Shymkent is thinly mapped, so
  about 1,400 of the 2,300 are filled in along the main streets.
- **Iyık Janyl** (the spiritual capital): almost no Russian names, saints' names (Ephrem, Janyl, Toma, Mattai) and local
  words (*ziyarat*, *jangak*, *örük*); below Cathedral Hill twelve guesthouses, icon-and-candle shops, souvenir, felt
  (*shyrdak*), saddle (*eerchi*) and leather shops; teahouses along Khunuk Creek in Shahr-i Khunuk; the Lower Town bazaar
  with fruit, butcher, dairy and craft stalls; Iradi and Uzbek food (*özbek paloo*); few bars (conservative clergy),
  more cash (few Tulpar partners), no KFC.

New words: *toikana* (banquet hall, for weddings: *toi* + *-kana*), *stolovaya* (canteen, attested), *shamdal jana
ikona* (icons and candles), *eerchi* (saddler; canon has *eerchilik*, saddlery).

## Other lore followed

- **No horsemeat** anywhere (sale banned in the ISEZ). Bars and pubs exist; pork is not avoided.
- **Semiz** (the Mexican community): taquerías, tortillerías, abarrotes, a panadería and *talleres* (car workshops) on
  its high street, and most eateries nearby Mexican.
- **The air base side and the contractors' estates** (Cottonwood Estates, Alatau Heights, the strip toward the base):
  diners, grills, steakhouses, barbecue and burgers.
- **The Old City**: none of the donor's businesses (its streets are the lore's own mahalla). Instead a bazaar cluster
  round Bazar-i Kalan: chaikhanas, bakeries, spice, tea, dairy and butcher stalls, cloth, carpet and copper shops, two
  guesthouses.
- **Koryo-saram** cafés (kuksi, morkovcha), Uzbek, Russian, Turkish, Georgian and Chinese (including Dungan) places in
  the mix; about 30% of the donor's cafés are chaikhanas here.
- **Prices in som** at the canon's level (plov 25–30 som): chaikhana 40–90 som a head, cafés 60–250, restaurants
  150–700, upmarket up to 1,500.

## Iradi words used that the lore does not attest

From the map's interface strings, Kyrgyz-based like the rest of Iradi. To adopt or correct:

*dariykana* (pharmacy), *meymankana* (hotel), *konok üy* (guest house), *azık-tülük* (groceries), *sooda borboru*
(shopping centre), *valyuta almashuu* (currency exchange), *et dükönü* (butcher), *jemish-jashılcha* (fruit and veg),
*tez tamak* (fast food), *avtoservis*, *avtobölüktör* (car parts), *lagman-üy* (lagman house).

The one-off businesses (for example "Kafe Navat", "Dükön Aigül", "Restoran Dunhuang") are generated from first names,
words and place names and are not tracked here. Only chains and brands are.
