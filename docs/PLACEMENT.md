# Where Irad's cities, towns and villages go

Kartalar is authoritative for geography: the lore follows the map. These rules decide where a settlement may stand.
`build/audit_places.py` checks every city, town and village against them, writes `data/place_audit.md`, and can fix
and lock places:

    python3 build/audit_places.py <fine dem.bin> <extract dir> <network.json> [--fix] [--lock]

Kinds covered: capital, city, town, village. Quarters, neighbourhoods and suburbs follow their city's street plan
(`place_sites.py`); districts and planning-zone labels follow their polygons.

## The rules

**R1 – Real ground first.** Irad sits on real land, so a settlement takes over a real one: a capital or city a real
city, a town a real town or village, a village a real village, hamlet or block of built-up land (not a bare
'locality', which is usually a tract, a rail junction or a work camp). The real place's name is kept as `real_name`.
A free real settlement within reach must be used (8 km for a village, 12 for a town) if it suits the place: same
zone and district, a height within 300 m of the lore's, clear of the line. Only where the real map is empty may a
place be invented, and then only a village. Summer camps and yurt encampments are invented by nature and never take
over a village. A real namesake within 25 km wins over a nearer stranger for a loosely placed village, and within
5 km for a place the lore pins.

**R2 – One place per spot.** No two Iradi places share a real settlement. Spacing to the next place: 4 km from the
capital, 3 from a city, 2 from a town, 1.2 between villages. No village or town inside a city's street plan.

**R3 – Size.** What a place sits on fits its size: no city on a village, no town on a hamlet.

**R4 – Height.** The lore's height is within 120 m of the ground. On real ground the ground wins and the lore's figure
changes; an invented place is put where the ground matches the lore's height.

**R5–R7 – Habitable, for invented places.** Ground under the village core no steeper than 15%; water (river, stream,
canal, spring or lake) within 1.5 km (3 km in the Karatau, 5 km in the Northern Steppe, and none needed for a village
named for its well, *kuduk*); a road or track within 2 km (5 km in the ATR, 6 km in the steppe; not needed for a summer
camp or a place the lore gives its own track or pack trail). A real settlement already proves all three.

**R8 – Jurisdiction.** Inside its zone, its ISEZ district or its ATR planning zone, and at least 0.8 km from the
Qara-Chik line and the frontier unless the lore makes it a border or crossing place.

## Exceptions, each with its reason (in the script)

- **Special places** placed by their own logic: the Boz-Korgon compound (`make_bozkorgon.py`), Iyık Janyl (a lore
  city with no real namesake, on the Naryn flats), and the Kara-Oi research station and UNMI headquarters at the end of
  the Kara-Oi road.
- **Label points**: a clan homeland the lore names by its valley, not a village (Kara-Suu, Upper Besh-Tash).
- **Placed by hand** (`MANUAL`): Toguz-Bulak on the Kök-Bel road just above its crossing; Kümüshtü on the real
  village nearest the Shelji site; Arsha-Say making way for it.
- **Rules eased** (`RELAX`): Sary-Bulak (the road and the railway spur end at its works; the gorge stream is not
  mapped), Kara-Say (a terrace village on the slope it farms), Kosh-Bel (a hamlet on a high migration route; its spring
  is not mapped), Shaar-Döbö (moved with the Shahr-i Buzurg site to watered ground), Ak-Chiy (the Moiynkum margin is
  waterless around the old guess).

## Locking

A place that passes every rule is marked `"locked": true`. Nothing in the build moves a locked place:
`snap_settlements.py`, `fit_sites.py`, `place_sites.py`, `check_zones.py --fix` and `tag_zones.py` all leave it alone.
If a later change (a border, a new route) makes a locked place fail, the audit reports it and does not move it. To
move one on purpose, change its position by hand (or remove `locked`, run `--fix`, then `--lock`) and let the lore follow.

How far `--fix` may move a place depends on how firmly the lore pins it: anchors and real places not at all (only a
wrong height is corrected), places the lore states up to 3 km, loosely placed ones up to 12 km, further in the empty
steppe. Landmarks filed under a village (`"city"` = its name) move with it.
