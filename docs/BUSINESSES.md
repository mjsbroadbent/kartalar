# Businesses on the map, and the Iradi companies invented for them

`build/make_businesses.py` fills a city with everyday businesses (restaurants, cafés, chaikhanas, groceries,
supermarkets, pharmacies, banks, fuel, hotels, shops). They come from the real donor city's OpenStreetMap data,
moved with its street plan (`build/make_cities.py`), so they sit where businesses really cluster. **No real business
name is kept.** Every business gets an Iradi name from `build/biz_names.py`. Output: `data/biz/<city>.json`, listed in
`data/biz/index.json` (format: `docs/PLACES.md`).

    build/base/extract_poi.cpp   # g++ ... -o extract_poi; extract_poi kyrgyzstan.osm.pbf 74.40 42.74 74.80 43.00 > bishkek_poi.ndjson
    python3 build/make_businesses.py bishkek_poi.ndjson talas

The same input always gives the same businesses, names and hours.

Done so far: **Talas** (from Bishkek), about 3,100 businesses.

## Companies and brands invented for the map

None of these are in the lore yet. They are the ones to adopt into canon, rename or drop.

| Name (Iradi / English / Russian) | What | In Talas |
|---|---|---|
| **Bereke** / Bereke Supermarket / Береке | Supermarket chain, the biggest (*bereke*: plenty) | 76 stores |
| **Jıldız Market** / Jıldız Market / Жылдыз Маркет | Second supermarket chain (*jıldız*: star) | 40 stores |
| **Shıpa Dariykana** / Shıpa Pharmacy / Аптека «Шыпа» | Pharmacy chain (*shıpa*: cure) | 34 pharmacies |
| **Chüy Kommertsiyalık Banky** / Chuy Commercial Bank / Чуй Коммерческий банк | Commercial bank, one of the "other banks" the Bank of Irad Clearing House implies | 10 branches |
| **Ak Bata Bank** / Ak Bata Bank / Ак Бата Банк | Commercial bank (*ak bata*: blessing) | 18 branches |
| **Hotel Bazar-i Kalan** / Meymankana Bazar-i Kalan | A name for the lore's unnamed 2018 hotel on the site of the demolished 1910 merchant house by the covered market | 1 |

Numbered state pharmacies ("Pharmacy No. 22", *22-Dariykana*, Аптека № 22) are a type, not a company: Soviet-style
numbering kept on, numbers 1–60.

## Lore companies used, and how far the map takes them

| Lore | On the map | Beyond the lore |
|---|---|---|
| Talasbank (28 branches) | Exactly 28 branches across the city | Where the branches are |
| Transoxiana Microfinance Fund | 5 offices | The number of offices |
| NurGaz (makes the petrol and diesel; refuses Tulpar Pay) | Brand of about 60% of filling stations (65 in Talas) | NurGaz as a fuel-station brand |
| KFC Irad (the only foreign chain named) | 4 restaurants: by Central Square, by the Silk Road Arena, on the strip toward the air base, in Alatau Heights | The locations |
| Tulpar delivery partners | Chaikhana Bakyt (Bazar-i Kalan), Taquería Semiz (Semiz), Altyn Tower Pizza (by Altyn Tower), Nan & Boorsok (near Central Square), Shashlyk Kara-Suu (east edge, on the Kök-Bel road side) | Their exact spots |
| International Diplomatic Hotel (TCDG) | Off Central Square, on the central avenue | Its location |
| Tulpar delivery generally | About 40% of eateries show "Delivery with Tulpar" | |

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
