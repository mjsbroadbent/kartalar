# Businesses and reviews

Kartalar is meant to work like a full maps app for Irad, run by Attelkom: besides towns, landmarks and roads it can list
restaurants, cafés, hotels and shops, with opening hours and user reviews. The place panel already shows all of this
whenever the data has it. Nothing is listed yet: `data/places.json` is `[]` and `data/reviews.json` is `{}`.

To preview the panel, add `?demo` to the address (for example `?p=demo-jibek-ashkana&demo`). The map then loads
`data/demo/places.json` and `data/demo/reviews.json` instead: four sample listings in central Talas with reviews. They
are demo data only, not lore.

## data/places.json

A list of places in the same format as `data/features.json`. They are appended to the features, so search, the map dots,
the category chips and "nearby" all pick them up. A chip only appears when the map has places of its kind.

| field | | |
|---|---|---|
| `id` | required | unique, e.g. `ashkana-jibek-talas` |
| `name`, `name_en`, `name_ru`, `name_ir` | `name` required | shown by the interface language |
| `kind` | required | `restaurant`, `cafe`, `chaikhana`, `bakery`, `bar` (Food & drink); `hotel`, `guesthouse`, `hostel` (Hotels); `shop`, `supermarket`, `bank`, `pharmacy`, `fuel` (Shops & services) |
| `lat`, `lon` | required | |
| `city`, `zone` | | `city` is the English name of its city or village; `zone` is `ISEZ` or `ATR` |
| `address` | | street address, shown first under Overview |
| `hours` | | `{"mo": "09:00-22:00", ..., "su": "closed"}`. A day can be `"closed"`, `"24h"` or several spans, e.g. `"09:00-13:00,14:00-18:00"`. A span past midnight works (`"18:00-02:00"`). Open or closed is worked out in Irad time (UTC+6). |
| `phone` | | `+996 39 312 44 07`; shows a Call button |
| `web` | | website; shows a Website button when there is no wiki article |
| `price` | | free text, e.g. `"250–600 som per person"` |
| `price_level` | | 1–4, shown as с … сссс |
| `photos` | | image paths, the first is the panel's header picture (e.g. `img/places/<id>-1.jpg`) |
| `rating`, `reviews_count` | | totals, when a place has more reviews than `data/reviews.json` carries |
| `note` | | description, shown under About |
| `wiki` | | Irad Wiki article title |

## data/reviews.json

An object keyed by place id (any place on the map can have reviews, not only businesses):

```json
{
  "ashkana-jibek-talas": [
    {"author": "Aibek T.", "guide": true, "count": 87, "date": "2026-09-30", "stars": 5, "lang": "en",
     "text": "Best lagman near the market.", "reply": {"text": "Thank you!", "date": "2026-10-01"}}
  ]
}
```

- `stars` is 1–5. `date` is ISO.
- `lang` is `en`, `ru` or `ir`. A review in another language than the interface says so.
- `guide` marks a "Kartalar expert". `count` is how many reviews the author has written.
- `reply` is the owner's response.

The rating, the count and the 5-to-1 bars are worked out from the list unless the place gives `rating` and `reviews_count`.

## Writing reviews

"Write a review" opens the Attelkom personal account sign-in, which is shared with attelkom.net. In-world it fails with
a billing system error, like every sign-in on the Attelkom site.
