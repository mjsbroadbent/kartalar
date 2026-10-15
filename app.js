/* Attelkom Kartalar: maps of Irad.
   Base map: our own tile archives in tiles/ (built by build/base from OpenStreetMap extracts, with the city plans baked
   in and no real labels or borders) and our own terrain; everything Iradi comes from data/*.json and data/*.geojson.
   Nothing is loaded from other servers. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const store = (k, v) => { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || "null"); localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return null; } };
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------- language ---------- */
  const nav = (navigator.language || "en").toLowerCase();
  const LANG = store("kt_lang") || (nav.startsWith("ru") ? "ru" : nav.startsWith("ky") ? "ir" : "en");
  document.documentElement.lang = LANG === "ir" ? "ky" : LANG;
  const S = window.KT_STR || { en: {} };
  const t = (k, v) => { let s = (S[LANG] && S[LANG][k]) || S.en[k] || k; if (v) s = s.replace(/\{(\w+)\}/g, (m, x) => (x in v ? v[x] : m)); return s; };
  const nameOf = p => (LANG === "ru" ? p.name_ru : LANG === "ir" ? (p.name_ir || p.name) : (p.name_en || p.name)) || p.name;

  /* ---------- base style ---------- */
  const BASE = new URL(".", location.href).href;
  const C = {
    land: "#f2efe7", water: "#aad3e8", waterLine: "#8cc2de", wood: "#d6e6c6", grass: "#e4ecd3", sand: "#efe5c9", ice: "#f7fbfd",
    farm: "#eceee0", res: "#e8e2d8", park: "#d4e8c2", building: "#ddd5ca", motorway: "#f4b860", motorwayCase: "#d6923a",
    primary: "#fbd98f", primaryCase: "#d9b56a", road: "#ffffff", roadCase: "#d8d2c6", rail: "#9a958c",
    border: "#5a3d79", borderHalo: "#c9b6e3", qarachik: "#b23a2a", outside: "#e6e3dc", text: "#2c2a26", halo: "#ffffff"
  };
  // all base-map data is our own: tiles/*.pmtiles, read through vendor/kt-pmtiles.js (protocol kt://)
  const style = {
    version: 8,
    glyphs: BASE + "fonts/{fontstack}/{range}.pbf",
    sources: {
      area: { type: "vector", tiles: ["kt://area/{z}/{x}/{y}"], minzoom: 3, maxzoom: 12 },
      lines: { type: "vector", tiles: ["kt://lines/{z}/{x}/{y}"], minzoom: 3, maxzoom: 14 },
      detail: { type: "vector", tiles: ["kt://detail/{z}/{x}/{y}"], minzoom: 3, maxzoom: 14 },
      dem: { type: "raster-dem", tiles: ["kt://dem/{z}/{x}/{y}"], encoding: "terrarium", tileSize: 256, minzoom: 5, maxzoom: 11, bounds: [67.5, 40.2, 75.5, 46.5] },
      phys: { type: "geojson", data: "data/physical.geojson" }
    },
    layers: [
      { id: "bg", type: "background", paint: { "background-color": C.land } },
      // fallback physical layer (always present; vector tiles draw over it)
      { id: "phys-lake", type: "fill", source: "phys", filter: ["==", ["get", "k"], "lake"], paint: { "fill-color": C.water } },
      { id: "phys-river", type: "line", source: "phys", maxzoom: 9, filter: ["==", ["get", "k"], "river"], paint: { "line-color": C.waterLine, "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.6, 8, 1.6] } },
      // base layers from tiles/area, tiles/lines and tiles/detail (an OpenMapTiles-like schema), no labels, no boundaries
      { id: "landcover-farm", type: "fill", source: "area", "source-layer": "landcover", filter: ["==", ["get", "class"], "farmland"], paint: { "fill-color": C.farm } },
      { id: "landcover-wood", type: "fill", source: "area", "source-layer": "landcover", filter: ["in", ["get", "class"], ["literal", ["wood", "forest"]]], paint: { "fill-color": C.wood, "fill-opacity": 0.8 } },
      { id: "landcover-grass", type: "fill", source: "area", "source-layer": "landcover", filter: ["in", ["get", "class"], ["literal", ["grass", "scrub"]]], paint: { "fill-color": C.grass, "fill-opacity": 0.6 } },
      { id: "landcover-sand", type: "fill", source: "area", "source-layer": "landcover", filter: ["==", ["get", "class"], "sand"], paint: { "fill-color": C.sand } },
      { id: "landcover-ice", type: "fill", source: "area", "source-layer": "landcover", filter: ["==", ["get", "class"], "ice"], paint: { "fill-color": C.ice } },
      { id: "landuse-res", type: "fill", source: "area", "source-layer": "landuse", minzoom: 9, filter: ["in", ["get", "class"], ["literal", ["residential", "suburb", "neighbourhood", "commercial", "industrial", "retail"]]], paint: { "fill-color": C.res, "fill-opacity": ["case", ["has", "disused"], 0.3, 0.8] } },
      { id: "park", type: "fill", source: "area", "source-layer": "park", paint: { "fill-color": C.park, "fill-opacity": 0.5 } },
      { id: "water", type: "fill", source: "area", "source-layer": "water", paint: { "fill-color": C.water } },
      { id: "waterway", type: "line", source: "lines", "source-layer": "waterway", filter: ["!=", ["get", "brunnel"], "tunnel"], paint: { "line-color": C.waterLine, "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 13, 2, 16, 5] } },
      { id: "aeroway", type: "line", source: "area", "source-layer": "aeroway", minzoom: 11, filter: ["==", ["geometry-type"], "LineString"], paint: { "line-color": ["case", ["has", "disused"], "#e2ddd3", "#d4d0dc"], "line-width": ["interpolate", ["linear"], ["zoom"], 11, 2, 15, 20] } },
      { id: "building", type: "fill", source: "detail", "source-layer": "building", minzoom: 13, paint: { "fill-color": C.building, "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0, 14.5, 0.9] } },
      { id: "road-minor-case", type: "line", source: "lines", "source-layer": "transportation", minzoom: 12, filter: ["in", ["get", "class"], ["literal", ["minor", "service"]]], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.roadCase, "line-width": ["interpolate", ["linear"], ["zoom"], 12, 1, 16, 10] } },
      { id: "road-minor", type: "line", source: "lines", "source-layer": "transportation", minzoom: 12, filter: ["in", ["get", "class"], ["literal", ["minor", "service"]]], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.road, "line-width": ["interpolate", ["linear"], ["zoom"], 12, 0.5, 16, 8] } },
      { id: "road-track", type: "line", source: "lines", "source-layer": "transportation", minzoom: 12, filter: ["in", ["get", "class"], ["literal", ["track", "path"]]], paint: { "line-color": "#c9bfa9", "line-dasharray": [2, 2], "line-width": 1 } },
      { id: "road-mid-case", type: "line", source: "lines", "source-layer": "transportation", minzoom: 9, filter: ["in", ["get", "class"], ["literal", ["secondary", "tertiary"]]], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.roadCase, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 1, 16, 14] } },
      { id: "road-mid", type: "line", source: "lines", "source-layer": "transportation", minzoom: 8, filter: ["in", ["get", "class"], ["literal", ["secondary", "tertiary"]]], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.road, "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.5, 16, 12] } },
      { id: "road-primary-case", type: "line", source: "lines", "source-layer": "transportation", minzoom: 7, filter: ["in", ["get", "class"], ["literal", ["primary", "trunk"]]], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.primaryCase, "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.2, 16, 18] } },
      { id: "road-primary", type: "line", source: "lines", "source-layer": "transportation", minzoom: 6, filter: ["in", ["get", "class"], ["literal", ["primary", "trunk"]]], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.primary, "line-width": ["interpolate", ["linear"], ["zoom"], 6, 0.6, 16, 15] } },
      { id: "road-motorway", type: "line", source: "lines", "source-layer": "transportation", minzoom: 5, filter: ["==", ["get", "class"], "motorway"], layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": C.motorway, "line-width": ["interpolate", ["linear"], ["zoom"], 5, 0.8, 16, 18] } },
      { id: "rail-disused", type: "line", source: "lines", "source-layer": "transportation", minzoom: 10, filter: ["all", ["==", ["get", "class"], "rail"], ["has", "disused"]], paint: { "line-color": "#b9b2a6", "line-dasharray": [4, 3], "line-width": ["interpolate", ["linear"], ["zoom"], 10, 0.6, 16, 2] } },
      { id: "rail", type: "line", source: "lines", "source-layer": "transportation", minzoom: 9, filter: ["all", ["==", ["get", "class"], "rail"], ["!", ["has", "disused"]]], paint: { "line-color": C.rail, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.8, 16, 3] } },
      { id: "rail-dash", type: "line", source: "lines", "source-layer": "transportation", minzoom: 11, filter: ["all", ["==", ["get", "class"], "rail"], ["!", ["has", "disused"]]], paint: { "line-color": "#ffffff", "line-dasharray": [3, 3], "line-width": ["interpolate", ["linear"], ["zoom"], 11, 0.6, 16, 2] } },
      // Iradi city plans (data/city): a mask hides the real base map inside each city, then its own streets are drawn
      { id: "city-mask", type: "fill", source: "detail", "source-layer": "city", filter: ["==", ["get", "t"], "mask"], paint: { "fill-color": C.land } },
      // relief over the base map and the city masks alike (so the hills inside a city footprint still show)
      { id: "hillshade", type: "hillshade", source: "dem", paint: { "hillshade-exaggeration": 0.42, "hillshade-shadow-color": "#4d4535", "hillshade-highlight-color": "rgba(255,255,255,0.35)", "hillshade-accent-color": "#6b6250" } },
      { id: "city-land", type: "fill", source: "detail", "source-layer": "city", filter: ["==", ["get", "t"], "land"],
        paint: { "fill-color": ["match", ["get", "k"], "residential", C.res, "commercial", "#efdcd6", "industrial", "#e3dbe6", "park", C.park, "grass", C.grass,
          "farm", C.farm, "cemetery", "#d3dfca", "institution", "#efe6c8", "pitch", "#cfe5c0", "wood", C.wood, "heritage", "#e6dcc3", "parking", "#e7e3dc", C.res], "fill-opacity": 0.9 } },
      { id: "city-river", type: "line", source: "detail", "source-layer": "city", filter: ["==", ["get", "t"], "river"], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.water, "line-width": ["interpolate", ["exponential", 1.6], ["zoom"], 9, 1.5, 13, 6, 16, 30] } },
      { id: "city-canal", type: "line", source: "detail", "source-layer": "city", filter: ["all", ["==", ["get", "t"], "canal"], ["!=", ["get", "k"], "ditch"]], minzoom: 11, paint: { "line-color": C.waterLine, "line-width": ["interpolate", ["linear"], ["zoom"], 11, 0.6, 16, 3] } },
      { id: "city-ditch", type: "line", source: "detail", "source-layer": "city", filter: ["all", ["==", ["get", "t"], "canal"], ["==", ["get", "k"], "ditch"]], minzoom: 14, paint: { "line-color": C.waterLine, "line-width": 1 } },
      { id: "city-building", type: "fill", source: "detail", "source-layer": "city", minzoom: 13, filter: ["==", ["get", "t"], "building"],
        paint: { "fill-color": ["case", ["has", "tall"], "#d3c9bc", C.building], "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0, 14.5, 0.9] } },
      { id: "city-path", type: "line", source: "detail", "source-layer": "city", minzoom: 15, filter: ["==", ["get", "k"], "path"], paint: { "line-color": "#c9bfa9", "line-dasharray": [2, 2], "line-width": 1 } },
      { id: "city-minor-case", type: "line", source: "detail", "source-layer": "city", minzoom: 12.5, filter: ["in", ["get", "k"], ["literal", ["minor", "service"]]], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.roadCase, "line-width": ["interpolate", ["linear"], ["zoom"], 12.5, 1, 16, ["match", ["get", "k"], "service", 6, 10]] } },
      { id: "city-minor", type: "line", source: "detail", "source-layer": "city", minzoom: 12.5, filter: ["in", ["get", "k"], ["literal", ["minor", "service"]]], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.road, "line-width": ["interpolate", ["linear"], ["zoom"], 12.5, 0.5, 16, ["match", ["get", "k"], "service", 4.5, 8]] } },
      { id: "city-rail", type: "line", source: "detail", "source-layer": "city", minzoom: 9, filter: ["==", ["get", "t"], "rail"], paint: { "line-color": C.rail, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.8, 16, 3] } },
      { id: "city-rail-dash", type: "line", source: "detail", "source-layer": "city", minzoom: 11, filter: ["all", ["==", ["get", "t"], "rail"], ["==", ["get", "k"], "rail"]], paint: { "line-color": "#ffffff", "line-dasharray": [3, 3], "line-width": ["interpolate", ["linear"], ["zoom"], 11, 0.6, 16, 2] } },
      { id: "city-mid-case", type: "line", source: "detail", "source-layer": "city", minzoom: 9.5, filter: ["==", ["get", "k"], "mid"], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.roadCase, "line-width": ["interpolate", ["linear"], ["zoom"], 9.5, 1, 16, 14] } },
      { id: "city-mid", type: "line", source: "detail", "source-layer": "city", minzoom: 9.5, filter: ["==", ["get", "k"], "mid"], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.road, "line-width": ["interpolate", ["linear"], ["zoom"], 9.5, 0.5, 16, 12] } },
      { id: "city-major-case", type: "line", source: "detail", "source-layer": "city", minzoom: 8.5, filter: ["==", ["get", "k"], "major"], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.primaryCase, "line-width": ["interpolate", ["linear"], ["zoom"], 8.5, 1.2, 16, 18] } },
      { id: "city-major", type: "line", source: "detail", "source-layer": "city", minzoom: 8.5, filter: ["==", ["get", "k"], "major"], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": C.primary, "line-width": ["interpolate", ["linear"], ["zoom"], 8.5, 0.6, 16, 15] } }
    ]
  };

  /* ---------- map ---------- */
  const map = new maplibregl.Map({
    container: "map", style, center: [71.6, 43.2], zoom: 5.6, minZoom: 4, maxZoom: 17, hash: "map",
    attributionControl: false, dragRotate: false, pitchWithRotate: false,
    maxBounds: [[62, 37], [82, 50]]
  });
  map.touchZoomRotate.disableRotation();
  window.kartalarMap = map;   // handy for debugging from the console
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "Map data © Attelkom · <a href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\">© OpenStreetMap contributors</a> · Terrain: Mapzen Terrarium · Natural Earth" }), "bottom-right");
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
  map.addControl(new maplibregl.GeolocateControl({ positionOptions: { enableHighAccuracy: false } }), "bottom-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

  /* ---------- data ---------- */
  const D = { places: [], feats: [], routes: [], irad: null, zones: null, districts: null };
  const get = u => fetch(u).then(r => r.json());

  const GROUP = {
    worship: ["church", "mosque", "mazar"], civic: ["government", "university", "school", "hospital", "museum", "un"],
    leisure: ["stadium", "hippodrome", "market"], transport: ["airport", "station", "bus-station", "border-crossing", "checkpoint", "terminal"],
    industry: ["dam", "power", "mine", "industry", "oilfield"], nature: ["peak", "pass", "lake", "reservoir", "river-point", "spring", "park", "river", "canal", "glacier", "range", "valley", "desert"],
    heritage: ["ruins", "heritage", "landmark"], military: ["military"]
  };
  const GCOL = { worship: "#7b5ea7", civic: "#3f6fb0", leisure: "#e07b39", transport: "#1f8a9a", industry: "#6f6f6f", nature: "#3d8b4f", heritage: "#b0583a", military: "#8b2e2e", other: "#8a8a8a" };
  const groupOf = k => Object.keys(GROUP).find(g => GROUP[g].includes(k)) || "other";
  const PLACE_RANK = { capital: 1, city: 2, town: 3, village: 5, hamlet: 7, suburb: 6, quarter: 6, neighbourhood: 7, district: 4, "zone-area": 4, "foreign-city": 3, "foreign-town": 5 };

  const POI_FILTER = ["!=", ["get", "kind"], "river-point"];
  function fc(features) { return { type: "FeatureCollection", features }; }
  function pointFeat(p, extra) { return { type: "Feature", id: undefined, geometry: { type: "Point", coordinates: [p.lon, p.lat] }, properties: Object.assign({ id: p.id, label: nameOf(p), kind: p.kind }, extra) }; }

  Promise.all([get("data/settlements.json"), get("data/features.json"), get("data/routes.json"), get("data/irad.geojson"), get("data/zones.geojson"), get("data/districts.geojson"), get("data/qarachik.geojson"), get("data/restricted_zone.geojson"), get("data/real_places.json").catch(() => []), get("data/nature.json").catch(() => [])])
    .then(([pl, fe, ro, ir, zo, di, qc, rz, rp, na]) => {
      D.line = qc; D.rwz = rz;
      pl = pl.concat(rp);      // the real towns and villages (build/real_places.py) after the lore's own places
      D.places = pl; D.feats = fe; D.routes = ro; D.irad = ir; D.zones = zo; D.districts = di;
      D.nature = na;       // named peaks, passes, lakes, rivers and ranges (build/nature.py)
      D.all = pl.map(p => Object.assign({ _t: "place" }, p)).concat(fe.map(f => Object.assign({ _t: "feat" }, f)), na.map(f => Object.assign({ _t: "feat" }, f)));
      D.byId = Object.fromEntries(D.all.map(p => [p.id, p]));
      dataReady = true; maybeAdd();
    });
  let dataReady = false, styleReady = false, added = false;
  map.on("style.load", () => { styleReady = true; maybeAdd(); });
  function maybeAdd() { if (dataReady && styleReady && !added) { added = true; addOverlay(); } }

  function addOverlay() {
    // little map symbols drawn here, so no icon font or sprite sheet is needed: a peak triangle and a pass mark
    const sym = (name, draw) => {
      if (map.hasImage(name)) return;
      const r = window.devicePixelRatio > 1 ? 2 : 1, n = 12 * r, cv = document.createElement("canvas"); cv.width = cv.height = n;
      const g = cv.getContext("2d"); g.scale(r, r); draw(g); map.addImage(name, g.getImageData(0, 0, n, n), { pixelRatio: r });
    };
    sym("kt-peak", g => { g.beginPath(); g.moveTo(6, 1.5); g.lineTo(11, 10.5); g.lineTo(1, 10.5); g.closePath(); g.fillStyle = "#7a6248"; g.fill(); g.strokeStyle = "#fff"; g.lineWidth = 1; g.stroke(); });
    sym("kt-pass", g => { g.strokeStyle = "#fff"; g.lineWidth = 3; g.beginPath(); g.moveTo(2, 3); g.quadraticCurveTo(6, 7, 2, 11); g.moveTo(10, 3); g.quadraticCurveTo(6, 7, 10, 11); g.stroke();
      g.strokeStyle = "#7a6248"; g.lineWidth = 1.6; g.stroke(); });
    // grey wash over the neighbours: a world box with Irad cut out
    const holes = [];
    D.irad.features[0].geometry.coordinates.forEach(poly => holes.push(poly[0]));
    map.addSource("outside", { type: "geojson", data: fc([{ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[[40, 20], [100, 20], [100, 60], [40, 60], [40, 20]]].concat(holes) } }]) });
    map.addSource("irad", { type: "geojson", data: D.irad });
    map.addSource("zones", { type: "geojson", data: D.zones });
    map.addSource("districts", { type: "geojson", data: D.districts });
    map.addSource("qarachik", { type: "geojson", data: D.line });
    map.addSource("rwz", { type: "geojson", data: D.rwz });
    map.addSource("routes", { type: "geojson", data: fc(D.routes.map(r => ({ type: "Feature", properties: { id: r.id, kind: r.kind, label: nameOf(r) }, geometry: { type: "LineString", coordinates: r.coords } })).concat(D.routes.flatMap(r => (r.tunnels || []).map(t => ({ type: "Feature", properties: { id: r.id, kind: "tunnel", label: "" }, geometry: { type: "LineString", coordinates: t } }))))) });
    const bk = D.byId["boz-korgon"];
    map.addSource("restricted", { type: "geojson", data: "data/boz_korgon.geojson" });
    map.addSource("places", { type: "geojson", data: fc(D.places.map(p => pointFeat(p, { rank: (PLACE_RANK[p.kind] || 6) + (p.confidence === "osm" ? 0.5 : 0), pop: p.pop || 0 }))) });
    map.addSource("nature", { type: "geojson", data: fc(D.nature.filter(f => !f.line && !["river", "canal"].includes(f.kind)).map(f => pointFeat(f, { elev: f.elev ? f.elev.toLocaleString("en-GB") + " m" : "", area: f.area || 0, big: (f.area || 0) >= 3 ? 1 : 0 }))) });
    map.addSource("landforms", { type: "geojson", data: fc(D.nature.filter(f => f.line).map(f => ({ type: "Feature", properties: { id: f.id, kind: f.kind, label: nameOf(f) }, geometry: { type: "LineString", coordinates: f.line } }))) });
    map.addSource("feats", { type: "geojson", data: fc(D.feats.map(f => pointFeat(f, { g: groupOf(f.kind), city: f.city || "" }))) });
    map.addSource("neighbours", { type: "geojson", data: fc([
      ["Kazakhstan", "Kazakstan", "Казахстан", 75.9, 44.9], ["Kazakhstan", "Kazakstan", "Казахстан", 67.2, 45.6], ["Kyrgyzstan", "Kırgızstan", "Киргизия", 75.4, 41.95],
      ["Uzbekistan", "Özbekstan", "Узбекистан", 69.6, 41.25], ["Tajikistan", "Tajikstan", "Таджикистан", 70.2, 39.6]
    ].map(([en, ir, ru, x, y]) => ({ type: "Feature", properties: { label: LANG === "ru" ? ru : LANG === "ir" ? ir : en }, geometry: { type: "Point", coordinates: [x, y] } }))) });

    const textFont = w => [w === "b" ? "Noto Sans Bold" : w === "i" ? "Noto Sans Italic" : "Noto Sans Regular"];
    const halo = { "text-color": C.text, "text-halo-color": C.halo, "text-halo-width": 1.6 };
    const isV = ["==", ["get", "kind"], "village"];
    const DOT_OP = ["interpolate", ["linear"], ["zoom"], 8.5, ["case", isV, 0, 1], 9, 1, 11, 1, 12, ["case", isV, 1, 0], 13, ["case", isV, 1, 0], 14, 0];
    const L = [
      { id: "outside", type: "fill", source: "outside", paint: { "fill-color": C.outside, "fill-opacity": 0.72 } },
      { id: "atr-tint", type: "fill", source: "zones", filter: ["==", ["get", "zone"], "ATR"], paint: { "fill-color": "#b58a4c", "fill-opacity": ["interpolate", ["linear"], ["zoom"], 5, 0.07, 10, 0.03] }, _g: "zones" },
      { id: "district-line", type: "line", source: "districts", minzoom: 6.5, paint: { "line-color": "#8c8577", "line-width": 0.8, "line-dasharray": [3, 2] }, _g: "zones" },
      { id: "rwz", type: "fill", source: "rwz", minzoom: 6, paint: { "fill-color": C.qarachik, "fill-opacity": ["interpolate", ["linear"], ["zoom"], 6, 0.035, 11, 0.02] }, _g: "zones" },
      { id: "qarachik-halo", type: "line", source: "qarachik", paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["linear"], ["zoom"], 5, 3, 12, 7], "line-opacity": 0.6 }, _g: "zones" },
      { id: "qarachik", type: "line", source: "qarachik", layout: { "line-join": "round" },
        paint: { "line-color": C.qarachik, "line-width": ["interpolate", ["linear"], ["zoom"], 5, 1.2, 12, 3], "line-dasharray": [4, 2], "line-opacity": 0.9 }, _g: "zones" },
      { id: "qarachik-hit", type: "line", source: "qarachik", paint: { "line-color": "#000", "line-width": 14, "line-opacity": 0 }, _g: "zones" },
      { id: "restricted-fill", type: "fill", source: "restricted", minzoom: 8, paint: { "fill-color": "#9b2c2c", "fill-opacity": ["match", ["get", "kind"], "compound", 0.32, 0.13] } },
      { id: "restricted-line", type: "line", source: "restricted", minzoom: 8, paint: { "line-color": "#9b2c2c", "line-width": 1.4, "line-dasharray": [2, 2] } },
      { id: "border-halo", type: "line", source: "irad", paint: { "line-color": C.borderHalo, "line-width": ["interpolate", ["linear"], ["zoom"], 4, 4, 10, 9], "line-opacity": 0.6 } },
      { id: "border", type: "line", source: "irad", paint: { "line-color": C.border, "line-width": ["interpolate", ["linear"], ["zoom"], 4, 1.2, 10, 2.4] } },
      // our routes: shown at regional zooms, fading out once real streets take over
      { id: "infra", type: "line", source: "routes", minzoom: 6, filter: ["in", ["get", "kind"], ["literal", ["pipeline", "canal", "power-line"]]], layout: { visibility: "none" },
        paint: { "line-color": ["match", ["get", "kind"], "pipeline", "#3f8a3f", "canal", "#3f9fd8", "#9c79b4"], "line-width": 1.4, "line-dasharray": [2, 1.5] }, _g: "infra" },
      { id: "route-road", type: "line", source: "routes", filter: ["in", ["get", "kind"], ["literal", ["highway", "road"]]], layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": ["match", ["get", "kind"], "highway", "#e39a32", "#efbe63"], "line-width": ["interpolate", ["linear"], ["zoom"], 5, ["match", ["get", "kind"], "highway", 1.8, 1], 9, ["match", ["get", "kind"], "highway", 3.2, 2], 14, ["match", ["get", "kind"], "highway", 7, 5]],
          "line-opacity": ["interpolate", ["linear"], ["zoom"], 10, 0.95, 13, 0.6] }, _g: "routes" },
      { id: "route-rail", type: "line", source: "routes", filter: ["==", ["get", "kind"], "railway"], paint: { "line-color": "#5a5650", "line-width": ["interpolate", ["linear"], ["zoom"], 5, 1, 9, 2, 14, 3] }, _g: "routes" },
      { id: "route-rail-dash", type: "line", source: "routes", minzoom: 6.5, filter: ["==", ["get", "kind"], "railway"], paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["linear"], ["zoom"], 6, 0.5, 9, 1, 14, 1.6], "line-dasharray": [3, 3] }, _g: "routes" },
      { id: "route-tunnel", type: "line", source: "routes", minzoom: 7, filter: ["==", ["get", "kind"], "tunnel"], paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.5, 12, 3.5], "line-dasharray": [1.2, 1.2] }, _g: "routes" },
      { id: "route-label", type: "symbol", source: "routes", minzoom: 7.5, filter: ["in", ["get", "kind"], ["literal", ["highway", "railway", "road"]]],
        layout: { "symbol-placement": "line", "text-field": ["get", "label"], "text-font": textFont("r"), "text-size": ["interpolate", ["linear"], ["zoom"], 8, 10.5, 14, 13], "symbol-spacing": 400, "symbol-sort-key": ["match", ["get", "kind"], "highway", 0, "railway", 1, 2] }, paint: { "text-color": "#6d5a3a", "text-opacity": ["interpolate", ["linear"], ["zoom"], 9.5, ["match", ["get", "kind"], "road", 0, 1], 10, 1], "text-halo-color": C.halo, "text-halo-width": 1.4 }, _g: "routes" },
      // labels: neighbours, planning zones, districts
      { id: "neighbour-label", type: "symbol", source: "neighbours", maxzoom: 8, layout: { "text-field": ["upcase", ["get", "label"]], "text-font": textFont("r"), "text-size": 13, "text-letter-spacing": 0.25 }, paint: { "text-color": "#9a968c", "text-halo-color": C.outside, "text-halo-width": 1 } },
      { id: "zone-area-label", type: "symbol", source: "places", minzoom: 5, maxzoom: 8.5, filter: ["==", ["get", "kind"], "zone-area"],
        layout: { "text-field": ["upcase", ["get", "label"]], "text-font": textFont("i"), "text-size": ["interpolate", ["linear"], ["zoom"], 5, 10, 8, 13], "text-letter-spacing": 0.18, "text-max-width": 8 },
        paint: { "text-color": "#9a7a4a", "text-halo-color": C.halo, "text-halo-width": 1.2 }, _g: "zones" },
      { id: "district-label", type: "symbol", source: "places", minzoom: 7, maxzoom: 10.5, filter: ["==", ["get", "kind"], "district"],
        layout: { "text-field": ["upcase", ["get", "label"]], "text-font": textFont("i"), "text-size": 12, "text-letter-spacing": 0.15, "text-max-width": 8 },
        paint: { "text-color": "#8a7f6c", "text-halo-color": C.halo, "text-halo-width": 1.2 }, _g: "zones" },
      // nature: ranges, valleys and deserts along their axes, river names along the rivers, then peaks, passes and lakes
      { id: "landform-label", type: "symbol", source: "landforms", minzoom: 6, maxzoom: 11,
        layout: { "symbol-placement": "line-center", "text-field": ["upcase", ["get", "label"]], "text-font": textFont("i"), "text-size": ["interpolate", ["linear"], ["zoom"], 6, 10, 9, 13],
          "text-letter-spacing": ["match", ["get", "kind"], "range", 0.45, 0.3], "text-max-angle": 45, "text-keep-upright": true, "text-allow-overlap": false, "text-padding": 0 },
        paint: { "text-color": ["match", ["get", "kind"], "range", "#8a6a48", "desert", "#a08350", "#5f8a5a"], "text-halo-color": C.halo, "text-halo-width": 1.2,
          "text-opacity": ["interpolate", ["linear"], ["zoom"], 9.5, 1, 11, 0] }, _g: "poi" },
      ...[["river-label", 9, ["river", "canal"]], ["stream-label", 12.5, ["stream"]]].map(([id, mz, cls]) => (
        { id, type: "symbol", source: "lines", "source-layer": "waterlabel", minzoom: mz, filter: ["all", ["has", "name"], ["in", ["get", "class"], ["literal", cls]]],
          layout: { "symbol-placement": "line", "text-field": ["get", "name"], "text-font": textFont("i"), "text-size": ["interpolate", ["linear"], ["zoom"], 9, 10.5, 14, 13], "symbol-spacing": 450, "text-max-angle": 35, "text-letter-spacing": 0.05 },
          paint: { "text-color": "#3f78a8", "text-halo-color": C.halo, "text-halo-width": 1.3 }, _g: "poi" })),
      ...[["nature-big", 7.5, ["==", ["get", "big"], 1]], ["nature-osm-label", 10.5, ["==", ["get", "kind"], "peak"]], ["nature-pass", 11.5, ["==", ["get", "kind"], "pass"]],
          ["nature-small", 11, ["all", ["==", ["get", "big"], 0], ["!", ["in", ["get", "kind"], ["literal", ["peak", "pass"]]]]]]].map(([id, mz, filter]) => (
        { id, type: "symbol", source: "nature", minzoom: mz, filter,
          layout: { "icon-image": ["match", ["get", "kind"], "peak", "kt-peak", "pass", "kt-pass", ""],
            "text-field": ["step", ["zoom"], ["get", "label"], 11.5, ["format", ["get", "label"], {}, ["case", ["!=", ["get", "elev"], ""], "\n", ""], {}, ["get", "elev"], { "font-scale": 0.85 }]],
            "text-font": textFont("i"), "text-size": ["case", ["==", ["get", "big"], 1], 12, 10.5], "text-max-width": 8,
            "text-anchor": ["match", ["get", "kind"], "peak", "top", "pass", "top", "center"], "text-offset": ["match", ["get", "kind"], "peak", ["literal", [0, 0.6]], "pass", ["literal", [0, 0.6]], ["literal", [0, 0]]],
            "symbol-sort-key": ["-", 0, ["get", "area"]] },
          paint: { "text-color": ["match", ["get", "kind"], "lake", "#3f78a8", "reservoir", "#3f78a8", "glacier", "#5a8fb0", "#6b5a44"], "text-halo-color": C.halo, "text-halo-width": 1.3 }, _g: "poi" })),
      // places of interest
      { id: "poi-dot", type: "circle", source: "feats", minzoom: 9,
        filter: POI_FILTER,
        paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 3, 14, 6], "circle-color": ["match", ["get", "g"], ...Object.entries(GCOL).flat(), "#8a8a8a"],
          "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5, "circle-opacity": ["interpolate", ["linear"], ["zoom"], 9, ["case", ["==", ["get", "g"], "nature"], 1, 0], 11, 1] }, _g: "poi" },
      { id: "poi-label", type: "symbol", source: "feats", minzoom: 11,
        layout: { "text-field": ["get", "label"], "text-font": textFont("r"), "text-size": 11.5, "text-offset": [0, 0.9], "text-anchor": "top", "text-max-width": 9, "text-optional": true,
          "symbol-sort-key": ["match", ["get", "kind"], ["peak", "pass", "lake", "reservoir"], 0, 1] },
        paint: { "text-color": ["match", ["get", "g"], ...Object.entries(GCOL).flat(), "#555"], "text-halo-color": C.halo, "text-halo-width": 1.5 }, _g: "poi" },
      { id: "nature-label", type: "symbol", source: "feats", minzoom: 8, maxzoom: 11, filter: ["in", ["get", "kind"], ["literal", ["peak", "pass", "lake", "reservoir", "park"]]],
        layout: { "text-field": ["get", "label"], "text-font": textFont("i"), "text-size": 11, "text-max-width": 8,
          "icon-image": ["match", ["get", "kind"], "peak", "kt-peak", "pass", "kt-pass", ""], "text-anchor": ["match", ["get", "kind"], "peak", "top", "pass", "top", "center"],
          "text-offset": ["match", ["get", "kind"], "peak", ["literal", [0, 0.6]], "pass", ["literal", [0, 0.6]], ["literal", [0, 0]]] },
        paint: { "text-color": "#4b7a55", "text-halo-color": C.halo, "text-halo-width": 1.4 }, _g: "poi" },
      { id: "restricted-label", type: "symbol", source: "restricted", minzoom: 9, filter: ["==", ["get", "kind"], "label"], layout: { "text-field": t("restricted"), "text-font": textFont("b"), "text-size": 11 }, paint: { "text-color": "#9b2c2c", "text-halo-color": C.halo, "text-halo-width": 1.5 } },
      // settlements
      { id: "place-dot", type: "circle", source: "places", filter: ["in", ["get", "kind"], ["literal", ["capital", "city", "town", "village"]]],
        minzoom: 5,
        paint: { "circle-radius": ["match", ["get", "kind"], "capital", 5, "city", 4.5, "town", 3.5, 2.5], "circle-color": "#ffffff", "circle-stroke-color": "#3a3a3a", "circle-stroke-width": ["match", ["get", "kind"], "capital", 2, 1.2],
          "circle-opacity": DOT_OP, "circle-stroke-opacity": DOT_OP } },
      // real places outside Irad: grey reference labels
      { id: "foreign-label", type: "symbol", source: "places", minzoom: 6, filter: ["in", ["get", "kind"], ["literal", ["foreign-city", "foreign-town"]]],
        layout: { "text-field": ["get", "label"], "text-font": textFont("r"), "text-size": ["match", ["get", "kind"], "foreign-city", 12, 10.5], "symbol-sort-key": ["get", "rank"] },
        paint: { "text-color": "#8d877d", "text-halo-color": C.halo, "text-halo-width": 1.4, "text-opacity": ["interpolate", ["linear"], ["zoom"], 6, ["match", ["get", "kind"], "foreign-city", 1, 0], 8, 1] } },
      { id: "hamlet-label", type: "symbol", source: "places", minzoom: 11.5, filter: ["==", ["get", "kind"], "hamlet"],
        layout: { "text-field": ["get", "label"], "text-font": textFont("r"), "text-size": 11, "symbol-sort-key": ["get", "rank"] },
        paint: { "text-color": "#5d584f", "text-halo-color": C.halo, "text-halo-width": 1.4 } },
      { id: "quarter-label", type: "symbol", source: "places", minzoom: 11, filter: ["in", ["get", "kind"], ["literal", ["suburb", "quarter", "neighbourhood"]]],
        layout: { "text-field": ["upcase", ["get", "label"]], "text-font": textFont("b"), "text-size": 11, "text-letter-spacing": 0.08, "text-max-width": 7 },
        paint: { "text-color": "#7b7468", "text-halo-color": C.halo, "text-halo-width": 1.5 } },
      { id: "place-label", type: "symbol", source: "places", filter: ["in", ["get", "kind"], ["literal", ["capital", "city", "town", "village"]]],
        layout: {
          // hidden labels get no text at all, so they do not keep other labels (ranges, rivers) off the map
          "text-field": ["step", ["zoom"], ["match", ["get", "kind"], ["village", "town"], "", ["get", "label"]], 6.75, ["match", ["get", "kind"], "village", "", ["get", "label"]], 8.6, ["get", "label"]],
          "text-font": ["case", ["in", ["get", "kind"], ["literal", ["capital", "city"]]], ["literal", textFont("b")], ["literal", textFont("r")]],
          "text-size": ["interpolate", ["linear"], ["zoom"], 5, ["match", ["get", "kind"], "capital", 15, "city", 13, "town", 11, 10], 12, ["match", ["get", "kind"], "capital", 22, "city", 20, "town", 15, 13]],
          "text-variable-anchor": ["left", "right", "top", "bottom"], "text-radial-offset": 0.6, "text-justify": "auto", "text-max-width": 9,
          "symbol-sort-key": ["get", "rank"]
        },
        paint: Object.assign({}, halo, { "text-halo-width": 2,
          "text-opacity": ["interpolate", ["linear"], ["zoom"], 6.5, ["match", ["get", "kind"], ["village", "town"], 0, 1], 7, ["match", ["get", "kind"], "village", 0, 1], 8.5, ["match", ["get", "kind"], "village", 0, 1], 9, 1] }),
        minzoom: 5 }
    ];
    L.forEach(l => { const g = l._g; delete l._g; if (g) l.metadata = { g }; map.addLayer(l); });
    applyLayerPrefs();
    ready = true;
    const q = new URLSearchParams(location.search).get("p");
    if (q && D.byId[q]) openPlace(D.byId[q], true);
    else if (!location.hash.includes("map=")) map.fitBounds(bbox(D.irad), { padding: 30, duration: 0 });
    updateNotice();
  }
  let ready = false;

  function circle([lon, lat], km, n = 48) {
    const pts = [];
    for (let i = 0; i <= n; i++) {
      const a = (i / n) * 2 * Math.PI;
      pts.push([lon + (km / (111.32 * Math.cos(lat * Math.PI / 180))) * Math.cos(a), lat + (km / 110.57) * Math.sin(a)]);
    }
    return { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [pts] } };
  }
  function bbox(gj) {
    let a = [180, 90, -180, -90];
    gj.features.forEach(f => f.geometry.coordinates.flat(2).forEach(([x, y]) => { a = [Math.min(a[0], x), Math.min(a[1], y), Math.max(a[2], x), Math.max(a[3], y)]; }));
    return [[a[0], a[1]], [a[2], a[3]]];
  }
  function inRings(pt, rings) {
    let inside = false;
    rings.forEach(r => { for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [xi, yi] = r[i], [xj, yj] = r[j]; if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) inside = !inside; } });
    return inside;
  }
  function whichIn(gj, pt, key) {
    for (const f of gj.features) for (const poly of f.geometry.coordinates) if (inRings(pt, poly)) return f.properties[key];
    return null;
  }

  /* ---------- layers menu ---------- */
  function applyLayerPrefs() {
    const prefs = store("kt_layers") || {};
    $$("[data-layer]").forEach(cb => {
      const g = cb.dataset.layer; if (g in prefs) cb.checked = prefs[g];
      setGroup(g, cb.checked);
    });
  }
  function setGroup(g, on) {
    if (g === "terrain") { if (map.getLayer("hillshade")) map.setLayoutProperty("hillshade", "visibility", on ? "visible" : "none"); return; }
    map.getStyle().layers.forEach(l => { if (l.metadata && l.metadata.g === g) map.setLayoutProperty(l.id, "visibility", on ? "visible" : "none"); });
  }
  $$("[data-layer]").forEach(cb => cb.addEventListener("change", () => {
    const p = store("kt_layers") || {}; p[cb.dataset.layer] = cb.checked; store("kt_layers", p); setGroup(cb.dataset.layer, cb.checked);
  }));
  $("#menuBtn").addEventListener("click", () => { const m = $("#menu"); m.hidden = !m.hidden; $("#menuBtn").setAttribute("aria-expanded", String(!m.hidden)); });
  document.addEventListener("click", e => { if (!$("#menu").hidden && !e.target.closest("#menu, #menuBtn")) { $("#menu").hidden = true; $("#menuBtn").setAttribute("aria-expanded", "false"); } });
  $$("#langSeg [data-lang]").forEach(b => {
    b.setAttribute("aria-pressed", String(b.dataset.lang === LANG));
    b.addEventListener("click", () => { store("kt_lang", b.dataset.lang); location.reload(); });
  });

  /* ---------- search ---------- */
  const norm = s => String(s || "").toLowerCase().replace(/ı/g, "i").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ё/g, "е").replace(/[^a-z0-9а-я ]+/g, " ").trim();
  function search(qs) {
    const q = norm(qs); if (!q) return [];
    const out = [];
    D.all.forEach(p => {
      const names = [p.name, p.name_en, p.name_ir, p.name_ru].filter(Boolean).map(norm);
      let s = 0;
      names.forEach(n => { if (n === q) s = Math.max(s, 100); else if (n.startsWith(q)) s = Math.max(s, 70); else if (n.split(" ").some(w => w.startsWith(q))) s = Math.max(s, 50); else if (n.includes(q)) s = Math.max(s, 30); });
      if (!s) return;
      s += p._t === "place" ? 12 - (PLACE_RANK[p.kind] || 6) * 2 : 0;
      out.push([s, p]);
    });
    return out.sort((a, b) => b[0] - a[0]).slice(0, 8).map(x => x[1]);
  }
  let results = [], sel = -1;
  const qEl = $("#q");
  function showResults() {
    const ul = $("#results");
    results = search(qEl.value); sel = -1;
    $("#qClear").hidden = !qEl.value;
    if (!qEl.value.trim()) { ul.hidden = true; return; }
    ul.innerHTML = results.length ? results.map((p, i) => `<li role="option" data-i="${i}"><span class="r-ico" style="background:${dotColor(p)}">${kindIcon(p)}</span><span><b>${esc(nameOf(p))}</b><small>${esc(kindLabel(p))}${p._t === "feat" && p.city ? " · " + esc(locName(p.city, true)) : p.district && p.kind !== "district" ? " · " + esc(locName(p.district)) : ""}</small></span></li>`).join("")
      : `<li class="none">${esc(t("noResults"))}</li>`;
    ul.hidden = false;
  }
  qEl.addEventListener("input", showResults);
  qEl.addEventListener("focus", () => { if (qEl.value) showResults(); });
  qEl.addEventListener("keydown", e => {
    const items = $$("#results li[data-i]");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(0, Math.min(items.length - 1, sel + (e.key === "ArrowDown" ? 1 : -1))); items.forEach((li, i) => li.classList.toggle("on", i === sel)); }
    else if (e.key === "Enter") { const p = results[sel >= 0 ? sel : 0]; if (p) pick(p); }
    else if (e.key === "Escape") { $("#results").hidden = true; }
  });
  $("#results").addEventListener("click", e => { const li = e.target.closest("[data-i]"); if (li) pick(results[+li.dataset.i]); });
  $("#qClear").addEventListener("click", () => { qEl.value = ""; showResults(); closeCard(); qEl.focus(); });
  document.addEventListener("click", e => { if (!e.target.closest(".top")) $("#results").hidden = true; });
  function pick(p) { $("#results").hidden = true; qEl.value = nameOf(p); $("#qClear").hidden = false; openPlace(p, true); qEl.blur(); }

  /* ---------- category chips ---------- */
  const CHIPS = [["worship", "⛪"], ["leisure", "🏟️"], ["transport", "🚉"], ["civic", "🏛️"], ["heritage", "🏺"], ["nature", "⛰️"]];
  $("#chips").innerHTML = CHIPS.map(([g, e]) => `<button type="button" data-chip="${g}"><span>${e}</span>${esc(t("grp_" + g))}</button>`).join("");
  let chipOn = null;
  $("#chips").addEventListener("click", e => {
    const b = e.target.closest("[data-chip]"); if (!b || !ready) return;
    chipOn = chipOn === b.dataset.chip ? null : b.dataset.chip;
    $$("#chips [data-chip]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.chip === chipOn)));
    const f = chipOn ? ["==", ["get", "g"], chipOn] : null;
    map.setFilter("poi-dot", f ? ["all", POI_FILTER, f] : POI_FILTER); map.setFilter("poi-label", f);
    if (chipOn) {
      const cb = $('[data-layer="poi"]'); if (!cb.checked) { cb.checked = true; setGroup("poi", true); }
      map.setLayerZoomRange("poi-dot", 5, 24); map.setLayerZoomRange("poi-label", 9, 24);
      map.setPaintProperty("poi-dot", "circle-opacity", 1);
      const pts = D.feats.filter(x => groupOf(x.kind) === chipOn);
      if (pts.length) {
        const b2 = pts.reduce((a, p) => [Math.min(a[0], p.lon), Math.min(a[1], p.lat), Math.max(a[2], p.lon), Math.max(a[3], p.lat)], [180, 90, -180, -90]);
        map.fitBounds([[b2[0], b2[1]], [b2[2], b2[3]]], { padding: { top: 140, bottom: 60, left: 40, right: 40 }, maxZoom: 12 });
      }
      toast(t("chipShown", { n: pts.length, g: t("grp_" + chipOn).toLowerCase() }));
    } else {
      map.setLayerZoomRange("poi-dot", 9, 24); map.setLayerZoomRange("poi-label", 11, 24);
      map.setPaintProperty("poi-dot", "circle-opacity", ["interpolate", ["linear"], ["zoom"], 9, ["case", ["==", ["get", "g"], "nature"], 1, 0], 11, 1]);
    }
  });

  /* ---------- place card ---------- */
  function kindLabel(p) { return t("k_" + p.kind); }
  // district and city names stored in English in the data, shown in the current language
  function locName(n, isCity) {
    if (!n) return "";
    const pl = D.places.find(x => (x.name === n || x.name_en === n) && x.kind !== "district");
    if (isCity && pl) return nameOf(pl);
    if (S[LANG] && S[LANG]["dist_" + n]) return S[LANG]["dist_" + n];
    return pl ? nameOf(pl) : n;
  }
  function dotColor(p) { return p._t === "place" ? "#5f6b7a" : GCOL[groupOf(p.kind)]; }
  function kindIcon(p) {
    if (p._t === "place") return { capital: "★", city: "●", town: "●", village: "•", district: "▦", "zone-area": "▦" }[p.kind] || "•";
    return { worship: "✝", civic: "▣", leisure: "◆", transport: "⇄", industry: "⚙", nature: "▲", heritage: "◈", military: "✚" }[groupOf(p.kind)] || "•";
  }
  const ZOOM = { capital: 11, city: 11.5, town: 12.5, village: 13.5, suburb: 14, quarter: 14, neighbourhood: 14.5, district: 8.5, "zone-area": 7 };
  const wikiUrl = title => "https://irad.wiki/#" + encodeURIComponent(title.replace(/\s+/g, "_"));
  function openPlace(p, fly) {
    if (fly && p.bbox) map.fitBounds([[p.bbox[0], p.bbox[1]], [p.bbox[2], p.bbox[3]]], { padding: 60, maxZoom: 11, speed: 1.6, essential: true });
    else if (fly) map.flyTo({ center: [p.lon, p.lat], zoom: p._t === "place" ? (ZOOM[p.kind] || 13) : (["peak", "pass", "lake", "reservoir", "park", "glacier"].includes(p.kind) ? (p.area > 20 ? 9.5 : 11.5) : 15), speed: 1.6, essential: true });
    const others = [p.name, p.name_en, p.name_ir, p.name_ru].filter((n, i, a) => n && n !== nameOf(p) && a.indexOf(n) === i);
    const zone = p.zone === "ISEZ" ? t("isez") : p.zone === "ATR" ? t("atr") : "";
    const where = p._t === "place" ? (p.kind === "district" ? zone : [p.district && p.district !== p.name ? locName(p.district) : "", zone].filter(Boolean).join(" · "))
      : [locName(p.city, true), zone].filter(Boolean).join(" · ");
    const facts = [];
    if (p.pop) facts.push([t("population"), Number(p.pop).toLocaleString(LANG === "ru" ? "ru-RU" : "en-GB")]);
    if (p.elev) facts.push([t("elevation"), Number(p.elev).toLocaleString("en-GB") + " m"]);
    if (p.length) facts.push([t("length"), p.length.toLocaleString("en-GB") + " km" + (p.kind === "river" || p.kind === "canal" ? " " + t("inIrad") : "")]);
    if (p.area) facts.push([t("area"), (p.area < 10 ? p.area.toFixed(1) : Math.round(p.area)) + " km²"]);
    facts.push([t("coords"), `${p.lat.toFixed(4)}°N, ${p.lon.toFixed(4)}°E`]);
    let extra = "";
    if (p.id === "boz-korgon") extra = `<p class="warn">⚠ ${esc(t("restrictedText"))}</p>`;
    else if (p.desc) extra = `<p class="info">${esc(p.desc)}</p>`;
    else if (p.zone === "ATR") extra = `<p class="info">${esc(t("atrText"))}</p>`;
    $("#cardBody").innerHTML = `<div class="c-kind" style="color:${dotColor(p)}">${kindIcon(p)} ${esc(kindLabel(p))}</div>
      <h2>${esc(nameOf(p))}</h2>${others.length ? `<p class="c-alt">${others.map(esc).join(" · ")}</p>` : ""}
      ${where ? `<p class="c-where">${esc(where)}</p>` : ""}
      <div class="c-actions">
        ${p.wiki ? `<a class="c-btn primary" href="${wikiUrl(p.wiki)}" target="_blank" rel="noopener">📖 ${esc(t("readWiki"))}</a>` : ""}
        <button type="button" class="c-btn" id="shareBtn">🔗 ${esc(t("share"))}</button>
        <button type="button" class="c-btn" id="nearBtn">📍 ${esc(t("nearby"))}</button>
      </div>
      ${extra}
      <dl class="c-facts">${facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
      <div id="nearList"></div>`;
    $("#shareBtn").onclick = () => {
      const url = location.origin + location.pathname + "?p=" + encodeURIComponent(p.id);
      (navigator.share ? navigator.share({ title: nameOf(p), url }) : navigator.clipboard.writeText(url).then(() => toast(t("linkCopied")))).catch(() => {});
    };
    $("#nearBtn").onclick = () => showNearby(p);
    $("#card").hidden = false;
    highlight(p);
    history.replaceState(null, "", location.pathname + "?p=" + encodeURIComponent(p.id) + location.hash);
  }
  function km(a, b) { const dx = (a.lon - b.lon) * 111.32 * Math.cos(a.lat * Math.PI / 180), dy = (a.lat - b.lat) * 110.57; return Math.hypot(dx, dy); }
  function showNearby(p) {
    const list = D.all.filter(x => x.id !== p.id && !["district", "zone-area"].includes(x.kind)).map(x => [km(p, x), x]).sort((a, b) => a[0] - b[0]).slice(0, 8);
    $("#nearList").innerHTML = `<h3>${esc(t("nearby"))}</h3><ul class="near">` + list.map(([d, x]) => `<li data-id="${esc(x.id)}"><span class="r-ico" style="background:${dotColor(x)}">${kindIcon(x)}</span><span><b>${esc(nameOf(x))}</b><small>${esc(kindLabel(x))}</small></span><em>${d < 1 ? Math.round(d * 1000) + " m" : d.toFixed(d < 10 ? 1 : 0) + " km"}</em></li>`).join("") + `</ul>`;
    $$("#nearList [data-id]").forEach(li => li.onclick = () => openPlace(D.byId[li.dataset.id], true));
  }
  let hl = null;
  function highlight(p) {
    if (!hl) hl = new maplibregl.Marker({ color: "#d93025" });
    hl.setLngLat([p.lon, p.lat]).addTo(map);
  }
  function closeCard() { $("#card").hidden = true; if (hl) hl.remove(); history.replaceState(null, "", location.pathname + location.hash); }
  $("#cardClose").addEventListener("click", closeCard);

  /* dropped pin: what's here */
  function dropPin(ll) {
    const pt = [ll.lng, ll.lat];
    const inIrad = whichIn(D.irad, pt, "name");
    const zone = inIrad ? whichIn(D.zones, pt, "zone") : null;
    const dist = zone === "ISEZ" ? whichIn(D.districts, pt, "district") : null;
    const here = { lat: ll.lat, lon: ll.lng };
    const near = D.places.filter(x => ["capital", "city", "town", "village"].includes(x.kind)).map(x => [km(here, x), x]).sort((a, b) => a[0] - b[0])[0];
    if (!hl) hl = new maplibregl.Marker({ color: "#d93025" });
    hl.setLngLat(ll).addTo(map);
    const where = !inIrad ? t("outsideIrad") : [dist ? t("districtOf", { d: t("dn_" + dist) }) : "", zone === "ISEZ" ? t("isez") : t("atr")].filter(Boolean).join(" · ");
    $("#cardBody").innerHTML = `<div class="c-kind">📍 ${esc(t("droppedPin"))}</div><h2>${ll.lat.toFixed(5)}, ${ll.lng.toFixed(5)}</h2><p class="c-where">${esc(where)}</p>
      ${inIrad && near ? `<p class="c-alt">${esc(t("nearestPlace", { n: nameOf(near[1]), d: near[0].toFixed(near[0] < 10 ? 1 : 0) }))}</p>` : ""}
      ${inIrad && zone === "ATR" ? `<p class="info">${esc(t("atrText"))}</p>` : ""}
      <div class="c-actions">${inIrad && near ? `<button type="button" class="c-btn" id="goNear">${esc(nameOf(near[1]))}</button>` : ""}</div>`;
    const g = $("#goNear"); if (g) g.onclick = () => openPlace(near[1], true);
    $("#card").hidden = false;
  }

  /* ---------- map clicks ---------- */
  const CLICKABLE = ["place-label", "hamlet-label", "foreign-label", "place-dot", "poi-dot", "poi-label", "nature-label", "nature-big", "nature-osm-label", "nature-pass", "nature-small", "landform-label", "quarter-label", "district-label", "zone-area-label"];
  function openLine(f, ll) {
    const p = f.properties;
    if (!hl) hl = new maplibregl.Marker({ color: "#d93025" });
    hl.setLngLat(ll).addTo(map);
    const total = D.line.features.reduce((a, x) => a + x.properties.km, 0);
    $("#cardBody").innerHTML = `<div class="c-kind" style="color:${C.qarachik}">┅ ${esc(t("lineKind"))}</div>
      <h2>${esc(t("lineName"))}</h2><p class="c-alt">${esc(LANG === "ru" ? "Qara-Chik chek ara sızığı · Qara-Chik Demarcation Line" : LANG === "ir" ? "Qara-Chik Demarcation Line · Демаркационная линия Кара-Чик" : "Qara-Chik chek ara sızığı · Демаркационная линия Кара-Чик")}</p>
      <p class="c-where">${esc(t("sec_" + p.sector))} · ${esc(t("fol_" + p.follows))}</p>
      <div class="c-actions"><a class="c-btn primary" href="${wikiUrl("Qara-Chik Demarcation Line")}" target="_blank" rel="noopener">📖 ${esc(t("readWiki"))}</a></div>
      <p class="info">${esc(t("lineText"))}</p>
      <dl class="c-facts"><dt>${esc(t("lineLen"))}</dt><dd>${Math.round(total / 10) * 10} km</dd><dt>${esc(t("lineRwz"))}</dt><dd>12 km</dd><dt>${esc(t("coords"))}</dt><dd>${ll.lat.toFixed(4)}°N, ${ll.lng.toFixed(4)}°E</dd></dl>`;
    $("#card").hidden = false;
  }
  map.on("click", e => {
    if (!ready) return;
    const hit = map.queryRenderedFeatures([[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]], { layers: CLICKABLE.filter(id => map.getLayer(id)) });
    if (hit.length) { const p = D.byId[hit[0].properties.id]; if (p) { openPlace(p, false); return; } }
    const lh = map.getLayer("qarachik-hit") && map.getLayoutProperty("qarachik-hit", "visibility") !== "none" ? map.queryRenderedFeatures(e.point, { layers: ["qarachik-hit"] }) : [];
    if (lh.length) { openLine(lh[0], e.lngLat); return; }
    if (!$("#card").hidden) { closeCard(); return; }
    dropPin(e.lngLat);
  });
  ["qarachik-hit"].concat(CLICKABLE).forEach(id => {
    map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
  });

  /* ---------- notices ---------- */
  function updateNotice() {
    if (!ready) return;
    const c = map.getCenter(), z = map.getZoom(), n = $("#notice");
    const bk = D.byId["boz-korgon"];
    let msg = "";
    if (bk && z >= 10 && km({ lat: c.lat, lon: c.lng }, bk) < 12) msg = "⚠ " + t("restrictedNotice");
    else if (z >= 9.5 && whichIn(D.zones, [c.lng, c.lat], "zone") === "ATR") msg = t("atrNotice");
    n.textContent = msg; n.hidden = !msg;
  }
  map.on("moveend", updateNotice);

  let toastT;
  function toast(s) { const el = $("#toast"); el.textContent = s; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => (el.hidden = true), 2600); }

  /* static text */
  $$("[data-t]").forEach(el => (el.textContent = t(el.dataset.t)));
  $$("[data-tp]").forEach(el => el.setAttribute("placeholder", t(el.dataset.tp)));
  window.KT = { map, D };
})();
