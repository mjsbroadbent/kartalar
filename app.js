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

  /* ---------- icons: stroked 24px SVGs used as CSS masks (class "ic", coloured by currentColor) ---------- */
  const IP = {
    search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>', menu: '<path d="M4 6.5h16M4 12h16M4 17.5h16"/>', close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    pin: '<path d="M12 21s-6.5-6-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 15 12 21 12 21z"/><circle cx="12" cy="9.8" r="2.4"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    phone: '<path d="M6.5 3.5h3l1.5 4-2 1.5a11 11 0 0 0 6 6l1.5-2 4 1.5v3a2 2 0 0 1-2 2A16 16 0 0 1 4.5 5.5a2 2 0 0 1 2-2z"/>',
    globe: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.4 2.4 3.4 5.4 3.4 8.5s-1 6.1-3.4 8.5c-2.4-2.4-3.4-5.4-3.4-8.5s1-6.1 3.4-8.5z"/>',
    book: '<path d="M12 6.5C10 5 7.5 4.5 4 4.8v13.5c3.5-.3 6 .2 8 1.7 2-1.5 4.5-2 8-1.7V4.8c-3.5-.3-6 .2-8 1.7zM12 6.5V20"/>',
    save: '<path d="M7 3.5h10v17l-5-4-5 4z"/>', saved: '<path d="M7 3.5h10v17l-5-4-5 4z" fill="#000"/>',
    share: '<circle cx="17.5" cy="5.5" r="2.5"/><circle cx="6.5" cy="12" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/><path d="M8.7 10.7l6.6-3.9M8.7 13.3l6.6 3.9"/>',
    nearby: '<circle cx="12" cy="12" r="2.5"/><circle cx="12" cy="12" r="7"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    copy: '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5V6a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5"/>',
    info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.4"/>', warn: '<path d="M12 4l9 15.5H3z"/><path d="M12 10v4.5M12 17v.4"/>',
    user: '<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>', elev: '<path d="M2.5 19.5l7-11 4 6 2.5-3.5 5.5 8.5z"/>',
    people: '<circle cx="9" cy="8" r="3.3"/><path d="M2.8 19.5a6.2 6.2 0 0 1 12.4 0"/><circle cx="17" cy="9" r="2.4"/><path d="M16.3 14a4.8 4.8 0 0 1 5 5"/>',
    flag: '<path d="M5.5 21V4M5.5 4.5h11l-2 4 2 4h-11"/>', ruler: '<path d="M3.5 16.5l13-13 4 4-13 13z"/><path d="M7 13l2 2M10 10l2 2M13 7l2 2"/>',
    bike: '<circle cx="6" cy="16.5" r="3.5"/><circle cx="18" cy="16.5" r="3.5"/><path d="M6 16.5l4-7h5l3 7M10 9.5L8.5 6.5H6.5M15 9.5l1-3h2.5"/>',
    edit: '<path d="M4 20h4l10.5-10.5-4-4L4 16z"/><path d="M13 7l4 4"/>', money: '<rect x="3" y="6.5" width="18" height="11" rx="2"/><circle cx="12" cy="12" r="2.6"/>',
    food: '<path d="M7 3v7.5M5 3v5a2 2 0 0 0 4 0V3M7 10.5V21M16.5 3c-2 1.5-2.7 4-2.7 7.5h2.7V21"/>',
    stay: '<path d="M3 18.5V6.5M3 13.5h18v5M21 13.5v-2a2 2 0 0 0-2-2h-8.5v4"/><circle cx="7" cy="10.5" r="1.8"/>',
    shops: '<path d="M5 8.5h14l-1 11.5H6zM9 8.5V7a3 3 0 0 1 6 0v1.5"/>',
    worship: '<path d="M12 2.5v4.5M10.2 4.2h3.6M5.5 21v-9.5L12 7l6.5 4.5V21M3.5 21h17M10 21v-4.5a2 2 0 0 1 4 0V21"/>',
    leisure: '<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3.3 3.5M16 6h3a3 3 0 0 1-3.3 3.5M12 13v4M8.5 20h7"/>',
    transport: '<rect x="5" y="3.5" width="14" height="13.5" rx="3"/><path d="M5 10.5h14M8 20.5V17M16 20.5V17"/><circle cx="8.5" cy="13.8" r=".6"/><circle cx="15.5" cy="13.8" r=".6"/>',
    civic: '<path d="M3 9.5L12 4l9 5.5M5.5 10v8M10 10v8M14 10v8M18.5 10v8M3 20.5h18"/>',
    heritage: '<path d="M4 20.5h16M6 20.5v-9M10.5 20.5v-6M14.5 20.5V12M18 20.5v-9M4.5 9.5l3-2.5h9l3 2.5z"/>',
    nature: '<path d="M2.5 19.5l7-11 4 6 2.5-3.5 5.5 8.5z"/>', crossing: '<path d="M4.5 21V4.5M4.5 8.5h15v4h-15M8.5 8.5l-2 4M13 8.5l-2 4M17.5 8.5l-2 4"/>',
    industry: '<path d="M3 20.5V10l5 3v-3l5 3V5.5h4l1 15z"/>', military: '<path d="M12 3.5l7 2.5v5.5c0 4.5-3 7.5-7 9.5-4-2-7-5-7-9.5V6z"/>',
    place: '<path d="M4 20.5V10l8-6 8 6v10.5h-5.5v-6h-5v6z"/>', other: '<circle cx="12" cy="12" r="3.5"/>', route: '<path d="M6 19.5c0-5 12-3 12-9S6 9 6 4.5"/><circle cx="6" cy="4.5" r="1.6"/><circle cx="6" cy="19.5" r="1.6"/>'
  };
  const icUrl = {};
  Object.entries(IP).forEach(([k, v]) => { icUrl[k] = "url('data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">' + v + '</svg>') + "')"; });
  const ic = (k, cls) => `<span class="ic${cls ? " " + cls : ""}" style="--i:${icUrl[k] || icUrl.other}" aria-hidden="true"></span>`;

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
  const D = { places: [], feats: [], routes: [], irad: null, zones: null, districts: null, reviews: {} };
  const DEMO = new URLSearchParams(location.search).has("demo");    // ?demo: sample businesses and reviews to preview the cards
  const get = u => fetch(u).then(r => r.json());

  const GROUP = {
    food: ["restaurant", "cafe", "chaikhana", "fast-food", "bakery", "bar"], stay: ["hotel", "guesthouse", "hostel"], shops: ["shop", "grocery", "supermarket", "mall", "bank", "pharmacy", "fuel"],
    worship: ["church", "mosque", "mazar"], civic: ["government", "university", "school", "hospital", "museum", "un"],
    leisure: ["stadium", "hippodrome", "market"], transport: ["airport", "station", "bus-station", "terminal"], crossing: ["border-crossing", "checkpoint"],
    industry: ["dam", "power", "mine", "industry", "oilfield"], nature: ["peak", "pass", "lake", "reservoir", "river-point", "spring", "park", "river", "canal", "glacier", "range", "valley", "desert"],
    heritage: ["ruins", "heritage", "landmark"], military: ["military"]
  };
  const GCOL = { food: "#e8710a", stay: "#c2185b", shops: "#3f51b5", worship: "#7b5ea7", civic: "#3f6fb0", leisure: "#e07b39", transport: "#1f8a9a", industry: "#6f6f6f", nature: "#3d8b4f", heritage: "#b0583a", military: "#8b2e2e", crossing: "#9b2c2c", other: "#8a8a8a" };
  const groupOf = k => Object.keys(GROUP).find(g => GROUP[g].includes(k)) || "other";
  const PLACE_RANK = { capital: 1, city: 2, town: 3, village: 5, hamlet: 7, suburb: 6, quarter: 6, neighbourhood: 7, district: 4, "zone-area": 4, "foreign-city": 3, "foreign-town": 5 };

  const BIZ_BIG = ["hotel", "mall", "market", "supermarket", "fuel"];
  const POI_FILTER = ["!", ["in", ["get", "kind"], ["literal", ["river-point", "border-crossing", "checkpoint"]]]];     // crossings have their own layers
  // crossing status (data/features.json "status"): colour and whether it shows from afar
  const XCOL = { main: "#1f5fa8", "line-main": "#9b2c2c", line: "#9b2c2c", local: "#2a9d8f", clan: "#b5651d", minor: "#8a8a8a", closed: "#555555", internal: "#6a6a6a" };
  const XMAJOR = ["main", "line-main", "clan", "line"];
  function fc(features) { return { type: "FeatureCollection", features }; }
  function pointFeat(p, extra) { return { type: "Feature", id: undefined, geometry: { type: "Point", coordinates: [p.lon, p.lat] }, properties: Object.assign({ id: p.id, label: nameOf(p), kind: p.kind }, extra) }; }

  Promise.all([get("data/settlements.json"), get("data/features.json"), get("data/routes.json"), get("data/irad.geojson"), get("data/zones.geojson"), get("data/districts.geojson"), get("data/qarachik.geojson"), get("data/restricted_zone.geojson"), get("data/real_places.json").catch(() => []), get("data/nature.json").catch(() => []),
    DEMO ? get("data/demo/places.json") : Promise.all([get("data/places.json").catch(() => []),
      get("data/biz/index.json").then(ix => Promise.all(ix.map(f => get("data/biz/" + f).catch(() => [])))).catch(() => [])]).then(([a, b]) => a.concat(...b)), get(DEMO ? "data/demo/reviews.json" : "data/reviews.json").catch(() => ({}))])
    .then(([pl, fe, ro, ir, zo, di, qc, rz, rp, na, bz, rv]) => {
      bz.forEach(b => { b.biz = true; });
      fe = fe.concat(bz);      // businesses: restaurants, cafes, hotels, shops (docs/PLACES.md, data/biz)
      D.reviews = rv || {};
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
    // crossing marks: a gate bar across a road, coloured by status (closed ones crossed through)
    Object.entries(XCOL).forEach(([st, col]) => sym("kt-x-" + st, g => {
      const big = XMAJOR.includes(st); const w = big ? 10 : 8, o = (12 - w) / 2;
      g.fillStyle = "#fff"; g.fillRect(o - 1, o - 1, w + 2, w + 2);
      g.fillStyle = col; g.fillRect(o, o, w, w);
      g.fillStyle = "#fff"; g.fillRect(o + 1.5, 5.2, w - 3, 1.6);
      if (st === "closed") { g.strokeStyle = "#fff"; g.lineWidth = 1.4; g.beginPath(); g.moveTo(o + 1, o + 1); g.lineTo(o + w - 1, o + w - 1); g.moveTo(o + w - 1, o + 1); g.lineTo(o + 1, o + w - 1); g.stroke(); }
      if (st === "clan") { g.fillStyle = "#fff"; g.beginPath(); g.arc(6, 6, 1.6, 0, 7); g.fill(); }
    }));
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
    map.addSource("feats", { type: "geojson", data: fc(D.feats.filter(f => !f.biz).map(f => pointFeat(f, { g: groupOf(f.kind), city: f.city || "", st: f.status || "" }))) });
    // businesses: their own source, shown only close in (the big ones a little earlier), like a street map
    map.addSource("biz", { type: "geojson", data: fc(D.feats.filter(f => f.biz).map(f => pointFeat(f, { g: groupOf(f.kind), big: BIZ_BIG.includes(f.kind) || f.lore ? 1 : 0 }))) });
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
      { id: "biz-dot", type: "circle", source: "biz", minzoom: 14, filter: ["any", ["==", ["get", "big"], 1], [">=", ["zoom"], 15]],
        paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 3, 17, 6.5], "circle-color": ["match", ["get", "g"], ...Object.entries(GCOL).flat(), "#8a8a8a"],
          "circle-stroke-color": "#ffffff", "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 14, 1, 17, 1.8] }, _g: "poi" },
      { id: "biz-label", type: "symbol", source: "biz", minzoom: 15.5, filter: ["any", ["==", ["get", "big"], 1], [">=", ["zoom"], 16.5]],
        layout: { "text-field": ["get", "label"], "text-font": textFont("r"), "text-size": 11, "text-offset": [0, 0.85], "text-anchor": "top", "text-max-width": 8, "text-optional": true,
          "symbol-sort-key": ["-", 1, ["get", "big"]] },
        paint: { "text-color": ["match", ["get", "g"], ...Object.entries(GCOL).flat(), "#555"], "text-halo-color": C.halo, "text-halo-width": 1.4 }, _g: "poi" },
      ...[["crossing-major", 6.5, 8, ["in", ["get", "st"], ["literal", XMAJOR]]], ["crossing-minor", 9.5, 11.5, ["!", ["in", ["get", "st"], ["literal", XMAJOR]]]]].map(([id, mz, lz, f]) => (
        { id, type: "symbol", source: "feats", minzoom: mz, filter: ["all", ["in", ["get", "kind"], ["literal", ["border-crossing", "checkpoint"]]], f],
          layout: { "icon-image": ["concat", "kt-x-", ["case", ["==", ["get", "st"], ""], "line", ["get", "st"]]], "icon-allow-overlap": true, "symbol-sort-key": 0,
            "text-field": ["step", ["zoom"], "", lz, ["get", "label"]], "text-font": textFont("r"), "text-size": 11, "text-offset": [0, 0.9], "text-anchor": "top", "text-optional": true, "text-max-width": 9 },
          paint: { "text-color": ["match", ["get", "st"], ...Object.entries(XCOL).flat(), "#9b2c2c"], "text-halo-color": C.halo, "text-halo-width": 1.4 }, _g: "poi" })),
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
    drawChips(); drawSaved();
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
      s += p._t === "place" ? 12 - (PLACE_RANK[p.kind] || 6) * 2 : p.biz ? -4 : 0;
      out.push([s, p]);
    });
    const kinds = Object.values(GROUP).flat().filter(k => q.length >= 3 && norm(t("k_" + k)).startsWith(q));
    if (kinds.length) {
      const c = map.getCenter(), cl = Math.cos(c.lat * Math.PI / 180);
      const near = D.feats.filter(f => f.biz && kinds.includes(f.kind)).map(f => [((f.lon - c.lng) * cl) ** 2 + (f.lat - c.lat) ** 2, f]).sort((a, b) => a[0] - b[0]).slice(0, 8).map(x => x[1]);
      if (near.length) return near.concat(out.sort((a, b) => b[0] - a[0]).map(x => x[1]).filter(x => !near.includes(x))).slice(0, 8);
    }
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

  /* ---------- category chips: only the categories the map has places for ---------- */
  const CHIP_ORDER = ["food", "stay", "shops", "worship", "leisure", "transport", "civic", "heritage", "nature", "crossing"];
  let chipOn = null;
  function drawChips() {
    const have = new Set(D.feats.map(f => groupOf(f.kind)));
    $("#chips").innerHTML = CHIP_ORDER.filter(g => have.has(g)).map(g => `<button type="button" data-chip="${g}" style="--chip:${GCOL[g]}">${ic(g)}${esc(t("grp_" + g))}</button>`).join("");
  }
  $("#chips").addEventListener("click", e => {
    const b = e.target.closest("[data-chip]"); if (!b || !ready) return;
    chipOn = chipOn === b.dataset.chip ? null : b.dataset.chip;
    $$("#chips [data-chip]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.chip === chipOn)));
    const f = chipOn ? ["==", ["get", "g"], chipOn] : null;
    map.setFilter("poi-dot", f ? ["all", POI_FILTER, f] : POI_FILTER); map.setFilter("poi-label", f);
    const BZ = ["any", ["==", ["get", "big"], 1], [">=", ["zoom"], 15]], BZL = ["any", ["==", ["get", "big"], 1], [">=", ["zoom"], 16.5]];
    map.setFilter("biz-dot", f ? f : BZ); map.setFilter("biz-label", f ? ["all", f, ["any", ["==", ["get", "big"], 1], [">=", ["zoom"], 15]]] : BZL);
    map.setLayerZoomRange("biz-dot", f ? 11 : 14, 24); map.setLayerZoomRange("biz-label", f ? 14 : 15.5, 24);
    if (chipOn) {
      const cb = $('[data-layer="poi"]'); if (!cb.checked) { cb.checked = true; setGroup("poi", true); }
      map.setLayerZoomRange("poi-dot", 5, 24); map.setLayerZoomRange("poi-label", 9, 24);
      if (chipOn === "crossing") { map.setLayerZoomRange("crossing-major", 5, 24); map.setLayerZoomRange("crossing-minor", 5, 24); }
      map.setPaintProperty("poi-dot", "circle-opacity", 1);
      const pts = D.feats.filter(x => groupOf(x.kind) === chipOn);
      if (pts.length) {
        const b2 = pts.reduce((a, p) => [Math.min(a[0], p.lon), Math.min(a[1], p.lat), Math.max(a[2], p.lon), Math.max(a[3], p.lat)], [180, 90, -180, -90]);
        map.fitBounds([[b2[0], b2[1]], [b2[2], b2[3]]], { padding: Object.assign({ top: 140, bottom: 60, left: 40, right: 40 }, panelPad(40)), maxZoom: 13 });
      }
      toast(t("chipShown", { n: pts.length, g: t("grp_" + chipOn).toLowerCase() }));
    } else {
      map.setLayerZoomRange("poi-dot", 9, 24); map.setLayerZoomRange("poi-label", 11, 24);
      map.setLayerZoomRange("crossing-major", 6.5, 24); map.setLayerZoomRange("crossing-minor", 9.5, 24);
      map.setPaintProperty("poi-dot", "circle-opacity", ["interpolate", ["linear"], ["zoom"], 9, ["case", ["==", ["get", "g"], "nature"], 1, 0], 11, 1]);
    }
  });

  /* ---------- place panel ---------- */
  const L3 = a => (a ? (LANG === "ru" ? a[2] : LANG === "ir" ? a[1] : a[0]) : "");
  function kindLabel(p) { const x = L3(p.cuisine_label || p.sub_label); return t("k_" + p.kind) + (x ? " · " + x : ""); }
  // district and city names stored in English in the data, shown in the current language
  function locName(n, isCity) {
    if (!n) return "";
    const pl = D.places.find(x => (x.name === n || x.name_en === n) && x.kind !== "district");
    if (isCity && pl) return nameOf(pl);
    if (S[LANG] && S[LANG]["dist_" + n]) return S[LANG]["dist_" + n];
    return pl ? nameOf(pl) : n;
  }
  const iconKey = p => p._t === "place" ? "place" : groupOf(p.kind);
  function dotColor(p) { return p._t === "place" ? "#5c6b60" : GCOL[groupOf(p.kind)]; }
  function kindIcon(p) { return ic(iconKey(p)); }
  const HERO = { place: ["#1f8a2b", "#1aa59a"], food: ["#ff8a00", "#e0531f"], stay: ["#c2185b", "#7b1fa2"], shops: ["#3f51b5", "#1fa3e0"], worship: ["#6a4f9c", "#3f6fb0"],
    leisure: ["#e07b39", "#c9a227"], transport: ["#1f8a9a", "#1fa3e0"], civic: ["#2f5f9e", "#1f8a9a"], heritage: ["#b0583a", "#c9a227"], nature: ["#3d8b4f", "#7aa33a"],
    crossing: ["#9b2c2c", "#5c6b60"], industry: ["#5f6b6a", "#8a978d"], military: ["#8b2e2e", "#5c3a2e"], other: ["#5c6b60", "#8a978d"] };
  const ZOOM = { capital: 11, city: 11.5, town: 12.5, village: 13.5, suburb: 14, quarter: 14, neighbourhood: 14.5, district: 8.5, "zone-area": 7 };
  const wikiUrl = title => "https://irad.wiki/#" + encodeURIComponent(title.replace(/\s+/g, "_"));
  const fmtN = n => Number(n).toLocaleString(LANG === "ru" ? "ru-RU" : "en-GB");
  const fmtKm = d => d < 1 ? Math.round(d * 1000) + " m" : d.toFixed(d < 10 ? 1 : 0) + " km";
  const isWide = () => innerWidth > 760;
  function panelPad(base = 60) {
    if ($("#panel").hidden) return {};
    return isWide() ? { left: parseInt(getComputedStyle(document.documentElement).getPropertyValue("--panel-w")) + base } : { bottom: Math.round(innerHeight * 0.46) + 20, top: 80 };
  }

  // reviews: data/reviews.json {place id: [{author, date, stars, text, lang, guide, reply: {text, date}}]}
  function revOf(p) {
    const list = (D.reviews[p.id] || []).slice();
    const n = p.reviews_count || list.length;
    const avg = p.rating || (list.length ? list.reduce((a, r) => a + r.stars, 0) / list.length : 0);
    return { list, n, avg };
  }
  const stars = (v, cls = "") => `<span class="stars ${cls}" aria-label="${v.toFixed(1)} / 5">${[1, 2, 3, 4, 5].map(i => `<span${i > Math.round(v) ? ' class="off"' : ""}>★</span>`).join("")}</span>`;
  // opening hours: {mo: "09:00-22:00", ..., su: "closed"}, Irad time (UTC+6)
  const DAYS = ["su", "mo", "tu", "we", "th", "fr", "sa"];
  function iradNow() { const d = new Date(Date.now() + 6 * 3600e3); return { day: d.getUTCDay(), min: d.getUTCHours() * 60 + d.getUTCMinutes() }; }
  function openState(h) {
    if (!h) return null;
    const { day, min } = iradNow(), v = h[DAYS[day]];
    if (!v || v === "closed") return { open: false, txt: t("closedToday") };
    if (v === "24h") return { open: true, txt: t("open24") };
    for (const span of v.split(",")) {
      const [a, b] = span.split("-").map(x => { const [hh, mm] = x.trim().split(":").map(Number); return hh * 60 + (mm || 0); });
      const end = b <= a ? b + 1440 : b;
      if (min >= a && min < end) return { open: true, txt: t("openUntil", { t: span.split("-")[1].trim() }) };
    }
    return { open: false, txt: t("closedNow") };
  }
  const saved = () => store("kt_saved") || [];
  const isSaved = id => saved().includes(id);
  function toggleSave(p) {
    const s = saved(), i = s.indexOf(p.id);
    if (i >= 0) s.splice(i, 1); else s.unshift(p.id);
    store("kt_saved", s.slice(0, 200)); drawSaved();
    toast(t(i >= 0 ? "unsavedT" : "savedT", { n: nameOf(p) }));
    return i < 0;
  }

  const panel = $("#panel");
  function showPanel(html) {
    $("#panelBody").innerHTML = html;
    panel.hidden = false; setFull(false); document.body.classList.add("has-panel");
    $("#panelScroll").scrollTop = 0;
    $$("#panelBody .tabs [data-tab]").forEach(b => b.onclick = () => selectTab(b.dataset.tab));
  }
  function selectTab(name) {
    $$("#panelBody .tabs [data-tab]").forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
    $$("#panelBody [data-pane]").forEach(x => (x.hidden = x.dataset.pane !== name));
    const tb = $("#panelBody .tabs"); if (tb && $("#panelScroll").scrollTop > tb.offsetTop) $("#panelScroll").scrollTop = tb.offsetTop;
  }
  function setFull(on) { panel.classList.toggle("full", on); document.body.classList.toggle("sheet-full", on && !isWide()); }
  $("#grip").addEventListener("click", () => setFull(!panel.classList.contains("full")));

  function heroHtml(p, crumbs) {
    const g = iconKey(p), [c1, c2] = HERO[g] || HERO.other;
    if (p.photos && p.photos.length) return `<figure class="hero has-photo"><img src="${esc(p.photos[0])}" alt="${esc(nameOf(p))}" loading="lazy"><span class="hero-count">1 / ${p.photos.length}</span></figure>`;
    return `<figure class="hero" style="--hc1:${c1};--hc2:${c2}">${ic(g, "hero-ic")}<div class="hero-crumb">${crumbs.filter(Boolean).map(c => `<span>${esc(c)}</span>`).join("")}</div></figure>`;
  }
  const row = (icon, html, attrs = "") => `<li ${attrs}>${ic(icon)}<div>${html}</div></li>`;

  function openPlace(p, fly) {
    if (fly && p.bbox) map.fitBounds([[p.bbox[0], p.bbox[1]], [p.bbox[2], p.bbox[3]]], { padding: Object.assign({ top: 60, bottom: 60, left: 60, right: 60 }, panelPad()), maxZoom: 11, speed: 1.6, essential: true });
    const g = iconKey(p);
    const others = [p.name, p.name_en, p.name_ir, p.name_ru].filter((n, i, a) => n && n !== nameOf(p) && a.indexOf(n) === i);
    const zone = p.zone === "ISEZ" ? t("isez") : p.zone === "ATR" ? t("atr") : "";
    const zoneShort = p.zone === "ISEZ" ? "ISEZ" : p.zone === "ATR" ? t("atrShort") : "";
    const qu = p.quarter && D.byId[p.quarter] ? nameOf(D.byId[p.quarter]) : "";
    const city = p._t === "feat" ? [qu, locName(p.city, true)].filter(Boolean).join(", ") : "";
    const dist = p.district && p.district !== p.name && p.kind !== "district" ? (p._t === "place" ? locName(p.district) : "") : "";
    const where = p.address || [city, dist, zone].filter(Boolean).join(" · ");
    const { list, n, avg } = revOf(p), os = openState(p.hours);
    // overview rows
    const rows = [];
    rows.push(row("pin", `${esc(where || t("irad"))}${p.address && (city || zone) ? `<small>${esc([city, zone].filter(Boolean).join(" · "))}</small>` : ""}`));
    if (p.hours) {
      const today = iradNow().day;
      rows.push(row("clock", `<span class="${os.open ? "p-open" : "p-closed"}">${esc(os.txt)}</span><table class="hours">${[1, 2, 3, 4, 5, 6, 0].map(d => `<tr${d === today ? ' class="today"' : ""}><td>${esc(t("day_" + DAYS[d]))}</td><td>${esc(p.hours[DAYS[d]] === "closed" || !p.hours[DAYS[d]] ? t("closed") : p.hours[DAYS[d]] === "24h" ? t("open24") : p.hours[DAYS[d]])}</td></tr>`).join("")}</table>`));
    }
    if (p.price) rows.push(row("money", esc(p.price)));
    if (p.tulpar) rows.push(row("bike", `${esc(t("tulparRow"))}<small>${esc(t("tulparSub"))}</small>`));
    if (p.phone) rows.push(row("phone", `<a href="tel:${esc(p.phone.replace(/\s/g, ""))}">${esc(p.phone)}</a>`));
    if (p.web) rows.push(row("globe", `<a href="${esc(p.web)}" target="_blank" rel="noopener">${esc(p.web.replace(/^https?:\/\//, "").replace(/\/$/, ""))}</a>`));
    if (p.wiki) rows.push(row("book", `<a href="${wikiUrl(p.wiki)}" target="_blank" rel="noopener">${esc(t("readWiki"))}</a>`));
    if (p.pop) rows.push(row("people", `${esc(fmtN(p.pop))}<small>${esc(t("population"))}</small>`));
    if (p.elev) rows.push(row("elev", `${esc(fmtN(p.elev))} m<small>${esc(t("elevation"))}</small>`));
    if (p.length) rows.push(row("ruler", `${esc(fmtN(p.length))} km${p.kind === "river" || p.kind === "canal" ? " " + esc(t("inIrad")) : ""}<small>${esc(t("length"))}</small>`));
    if (p.area) rows.push(row("ruler", `${p.area < 10 ? p.area.toFixed(1) : Math.round(p.area)} km²<small>${esc(t("area"))}</small>`));
    if (p.status) rows.push(row("info", `${esc(t("st_" + p.status))}<small>${esc(t("status"))}</small>`));
    rows.push(row("copy", `${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}<small>${esc(t("coordsCopy"))}</small>`, 'class="click" id="copyLL"'));
    let note = "";
    if (p.id === "boz-korgon") note = `<p class="note warn">${ic("warn")}<span>${esc(t("restrictedText"))}</span></p>`;
    else if (p.zone === "ATR") note = `<p class="note info">${ic("info")}<span>${esc(t("atrText"))}</span></p>`;
    const desc = p.desc || p.note || "";
    // nearby
    const near = D.all.filter(x => x.id !== p.id && !["district", "zone-area"].includes(x.kind)).map(x => [km(p, x), x]).sort((a, b) => a[0] - b[0]).slice(0, 6);
    const nearHtml = `<ul class="row-list">${near.map(([d, x]) => `<li data-id="${esc(x.id)}"><span class="r-ico" style="background:${dotColor(x)}">${kindIcon(x)}</span><span><b>${esc(nameOf(x))}</b><small>${esc(kindLabel(x))}</small></span><em>${fmtKm(d)}</em></li>`).join("")}</ul>`;
    // reviews
    const rvSum = n ? `<div class="rv-sum"><div class="rv-big"><b>${avg.toFixed(1)}</b>${stars(avg)}<small>${esc(t("nReviews", { n: fmtN(n) }))}</small></div>
        <div class="rv-bars">${[5, 4, 3, 2, 1].map(k => { const c = list.filter(r => r.stars === k).length; return `<div><span>${k}</span><i style="--w:${list.length ? Math.round(100 * c / list.length) : 0}%"></i></div>`; }).join("")}</div></div>` : "";
    const rvList = list.sort((a, b) => (b.date || "").localeCompare(a.date || "")).map(r => reviewHtml(r)).join("");
    const rvPane = n ? `${rvSum}<div class="rv-write"><button type="button" class="btn-orange js-write">${esc(t("writeReview"))}</button></div>
        <div class="rv-sort"><button type="button" class="btn-line" aria-pressed="true" data-sort="new">${esc(t("sortNew"))}</button><button type="button" class="btn-line" aria-pressed="false" data-sort="high">${esc(t("sortHigh"))}</button><button type="button" class="btn-line" aria-pressed="false" data-sort="low">${esc(t("sortLow"))}</button></div>
        <div id="rvList">${rvList}</div>`
      : `<div class="rv-empty">${ic("edit")}<b>${esc(t("noReviews"))}</b>${esc(t("noReviewsSub"))}</div><div class="rv-write" style="justify-content:center;border:0"><button type="button" class="btn-orange js-write">${esc(t("writeReview"))}</button></div>`;
    // about
    const facts = [[t("type"), kindLabel(p)]];
    if (zone) facts.push([t("zone"), zone]);
    if (dist) facts.push([t("district"), dist]);
    if (p.real_name) facts.push([t("sovietMaps"), p.real_name]);
    if (others.length) facts.push([t("otherNames"), others.join(" · ")]);

    showPanel(`${heroHtml(p, [dist || city, zoneShort])}
      <div class="p-head">
        <h1>${esc(nameOf(p))}</h1>${others.length ? `<p class="p-alt">${others.map(esc).join(" · ")}</p>` : ""}
        ${n ? `<p class="p-rate"><b>${avg.toFixed(1)}</b>${stars(avg)}<a href="#" class="js-rv">(${fmtN(n)})</a></p>` : ""}
        <p class="p-kind"><b style="--kind:${dotColor(p)}">${esc(kindLabel(p))}</b>${p.price_level ? ` · <span title="${esc(t("priceLevel"))}">${"с".repeat(p.price_level)}</span>` : ""}${os ? ` · <span class="${os.open ? "p-open" : "p-closed"}">${esc(os.txt)}</span>` : ""}</p>
      </div>
      <div class="p-actions">
        ${p.wiki ? `<a class="act primary" href="${wikiUrl(p.wiki)}" target="_blank" rel="noopener"><span class="c">${ic("book")}</span>${esc(t("actWiki"))}</a>` : p.web ? `<a class="act primary" href="${esc(p.web)}" target="_blank" rel="noopener"><span class="c">${ic("globe")}</span>${esc(t("actWeb"))}</a>` : ""}
        <button type="button" class="act${isSaved(p.id) ? " on" : ""}" id="saveBtn"><span class="c">${ic(isSaved(p.id) ? "saved" : "save")}</span><span class="lbl">${esc(t(isSaved(p.id) ? "actSaved" : "actSave"))}</span></button>
        <button type="button" class="act" id="nearBtn"><span class="c">${ic("nearby")}</span>${esc(t("nearby"))}</button>
        <button type="button" class="act" id="shareBtn"><span class="c">${ic("share")}</span>${esc(t("share"))}</button>
        ${p.phone ? `<a class="act" href="tel:${esc(p.phone.replace(/\s/g, ""))}"><span class="c">${ic("phone")}</span>${esc(t("actCall"))}</a>` : ""}
      </div>
      <div class="tabs" role="tablist"><button type="button" role="tab" data-tab="ov" aria-selected="true">${esc(t("tabOverview"))}</button><button type="button" role="tab" data-tab="rv" aria-selected="false">${esc(t("tabReviews"))}${n ? " · " + fmtN(n) : ""}</button><button type="button" role="tab" data-tab="ab" aria-selected="false">${esc(t("tabAbout"))}</button></div>
      <div class="tab" data-pane="ov">${note}<ul class="rows">${rows.join("")}</ul>
        ${desc ? `<div class="sect"><h2>${esc(t("tabAbout"))}</h2><p class="desc">${esc(desc)}</p></div>` : ""}
        ${list.length ? `<div class="sect"><h2>${esc(t("tabReviews"))}</h2></div>${reviewHtml(list[0])}<div class="rv-write" style="padding-top:10px;border:0"><button type="button" class="btn-line js-rv">${esc(t("moreReviews", { n: fmtN(n) }))}</button></div>` : ""}
        <div class="sect" id="nearSect"><h2>${esc(t("nearby"))}</h2>${nearHtml}</div></div>
      <div class="tab" data-pane="rv" hidden>${rvPane}</div>
      <div class="tab" data-pane="ab" hidden><div class="sect" style="border-top:0">${desc ? `<p class="desc">${esc(desc)}</p>` : ""}<dl class="facts">${facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl></div>
        <ul class="rows">${row("flag", `${esc(t("report"))}<small>${esc(t("reportSub"))}</small>`, 'class="click" id="reportBtn"')}</ul></div>`);

    $("#shareBtn").onclick = () => {
      const url = location.origin + location.pathname + "?p=" + encodeURIComponent(p.id) + (DEMO ? "&demo" : "");
      (navigator.share ? navigator.share({ title: nameOf(p), url }) : navigator.clipboard.writeText(url).then(() => toast(t("linkCopied")))).catch(() => {});
    };
    $("#saveBtn").onclick = () => { const on = toggleSave(p); const b = $("#saveBtn"); b.classList.toggle("on", on); b.querySelector(".c").innerHTML = ic(on ? "saved" : "save"); b.querySelector(".lbl").textContent = t(on ? "actSaved" : "actSave"); };
    $("#nearBtn").onclick = () => { selectTab("ov"); setFull(true); $("#panelScroll").scrollTop = $("#nearSect").offsetTop - 50; };
    $("#copyLL").onclick = () => navigator.clipboard.writeText(`${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}`).then(() => toast(t("coordsCopied"))).catch(() => {});
    $("#reportBtn").onclick = () => toast(t("reportT"));
    $$("#panelBody .js-rv").forEach(a => a.onclick = e => { e.preventDefault(); selectTab("rv"); });
    $$("#panelBody .js-write").forEach(b => b.onclick = openLogin);
    $$("#panelBody [data-sort]").forEach(b => b.onclick = () => {
      $$("#panelBody [data-sort]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      const s = b.dataset.sort, l = list.slice().sort((x, y) => s === "high" ? y.stars - x.stars : s === "low" ? x.stars - y.stars : (y.date || "").localeCompare(x.date || ""));
      $("#rvList").innerHTML = l.map(reviewHtml).join("");
    });
    $$("#nearSect [data-id]").forEach(li => li.onclick = () => openPlace(D.byId[li.dataset.id], true));
    if (fly && !p.bbox) map.flyTo({ center: [p.lon, p.lat], zoom: p._t === "place" ? (ZOOM[p.kind] || 13) : (["peak", "pass", "lake", "reservoir", "park", "glacier"].includes(p.kind) ? (p.area > 20 ? 9.5 : 11.5) : 15), padding: panelPad(0), speed: 1.6, essential: true });
    highlight(p);
    history.replaceState(null, "", location.pathname + "?p=" + encodeURIComponent(p.id) + (DEMO ? "&demo" : "") + location.hash);
  }
  const AVA = ["#1f8a2b", "#ff8a00", "#1fa3e0", "#7b5ea7", "#c2185b", "#0d3b1a", "#b0583a", "#2f5f9e"];
  function reviewHtml(r) {
    const h = [...(r.author || "?")].reduce((a, c) => a + c.charCodeAt(0), 0);
    const date = r.date ? new Date(r.date + "T12:00:00Z").toLocaleDateString(LANG === "ru" ? "ru-RU" : "en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";
    return `<div class="rv"><div class="rv-who"><span class="ava" style="background:${AVA[h % AVA.length]}">${esc((r.author || "?").trim()[0].toUpperCase())}</span><div><b>${esc(r.author)}</b><small>${r.guide ? esc(t("localGuide")) + " · " : ""}${r.count ? esc(t("nOwnReviews", { n: r.count })) : ""}</small></div></div>
      <div class="rv-meta">${stars(r.stars)}<span>${esc(date)}</span></div><p>${esc(r.text)}</p>
      ${r.lang && r.lang !== LANG ? `<div class="rv-lang">${esc(t("writtenIn", { l: t("lang_" + r.lang) }))}</div>` : ""}
      ${r.reply ? `<div class="rv-reply"><b>${esc(t("ownerReply"))}</b>${esc(r.reply.text)}</div>` : ""}</div>`;
  }
  function km(a, b) { const dx = (a.lon - b.lon) * 111.32 * Math.cos(a.lat * Math.PI / 180), dy = (a.lat - b.lat) * 110.57; return Math.hypot(dx, dy); }
  let hl = null;
  function highlight(p) {
    if (!hl) hl = new maplibregl.Marker({ color: "#e0531f" });
    hl.setLngLat([p.lon, p.lat]).addTo(map);
  }
  function closeCard() {
    panel.hidden = true; setFull(false); document.body.classList.remove("has-panel"); if (hl) hl.remove();
    history.replaceState(null, "", location.pathname + (DEMO ? "?demo" : "") + location.hash);
  }

  /* dropped pin: what's here */
  function dropPin(ll) {
    const pt = [ll.lng, ll.lat];
    const inIrad = whichIn(D.irad, pt, "name");
    const zone = inIrad ? whichIn(D.zones, pt, "zone") : null;
    const dist = zone === "ISEZ" ? whichIn(D.districts, pt, "district") : null;
    const here = { lat: ll.lat, lon: ll.lng };
    const near = D.places.filter(x => ["capital", "city", "town", "village"].includes(x.kind)).map(x => [km(here, x), x]).sort((a, b) => a[0] - b[0])[0];
    if (!hl) hl = new maplibregl.Marker({ color: "#e0531f" });
    hl.setLngLat(ll).addTo(map);
    const where = !inIrad ? t("outsideIrad") : [dist ? t("districtOf", { d: t("dn_" + dist) }) : "", zone === "ISEZ" ? t("isez") : t("atr")].filter(Boolean).join(" · ");
    showPanel(`<figure class="hero" style="--hc1:#5c6b60;--hc2:#1f8a2b">${ic("pin", "hero-ic")}<div class="hero-crumb"><span>${esc(t("droppedPin"))}</span></div></figure>
      <div class="p-head"><h1>${ll.lat.toFixed(5)}, ${ll.lng.toFixed(5)}</h1><p class="p-kind">${esc(where)}</p></div>
      <div class="p-actions">${inIrad && near ? `<button type="button" class="act primary" id="goNear"><span class="c">${ic("place")}</span>${esc(nameOf(near[1]))}</button>` : ""}
        <button type="button" class="act" id="copyLL"><span class="c">${ic("copy")}</span>${esc(t("actCopy"))}</button></div>
      ${inIrad && zone === "ATR" ? `<p class="note info">${ic("info")}<span>${esc(t("atrText"))}</span></p>` : ""}
      <ul class="rows">${inIrad && near ? row("place", `${esc(t("nearestPlace", { n: nameOf(near[1]), d: near[0].toFixed(near[0] < 10 ? 1 : 0) }))}`) : ""}</ul>`);
    const g = $("#goNear"); if (g) g.onclick = () => openPlace(near[1], true);
    $("#copyLL").onclick = () => navigator.clipboard.writeText(`${ll.lat.toFixed(5)}, ${ll.lng.toFixed(5)}`).then(() => toast(t("coordsCopied"))).catch(() => {});
  }

  /* ---------- map clicks ---------- */
  const CLICKABLE = ["biz-dot", "biz-label", "place-label", "hamlet-label", "foreign-label", "place-dot", "poi-dot", "poi-label", "nature-label", "crossing-major", "crossing-minor", "nature-big", "nature-osm-label", "nature-pass", "nature-small", "landform-label", "quarter-label", "district-label", "zone-area-label"];
  function openLine(f, ll) {
    const p = f.properties;
    if (!hl) hl = new maplibregl.Marker({ color: "#e0531f" });
    hl.setLngLat(ll).addTo(map);
    const total = D.line.features.reduce((a, x) => a + x.properties.km, 0);
    showPanel(`<figure class="hero" style="--hc1:#9b2c2c;--hc2:#5c3a2e">${ic("crossing", "hero-ic")}<div class="hero-crumb"><span>${esc(t("lineKind"))}</span><span>${esc(t("sec_" + p.sector))}</span></div></figure>
      <div class="p-head"><h1>${esc(t("lineName"))}</h1><p class="p-alt">${esc(LANG === "ru" ? "Qara-Chik chek ara sızığı · Qara-Chik Demarcation Line" : LANG === "ir" ? "Qara-Chik Demarcation Line · Демаркационная линия Кара-Чик" : "Qara-Chik chek ara sızığı · Демаркационная линия Кара-Чик")}</p>
        <p class="p-kind"><b style="--kind:#9b2c2c">${esc(t("lineKind"))}</b> · ${esc(t("fol_" + p.follows))}</p></div>
      <div class="p-actions"><a class="act primary" href="${wikiUrl("Qara-Chik Demarcation Line")}" target="_blank" rel="noopener"><span class="c">${ic("book")}</span>${esc(t("actWiki"))}</a></div>
      <p class="note info">${ic("info")}<span>${esc(t("lineText"))}</span></p>
      <ul class="rows">${row("ruler", `${Math.round(total / 10) * 10} km<small>${esc(t("lineLen"))}</small>`)}${row("warn", `12 km<small>${esc(t("lineRwz"))}</small>`)}${row("pin", `${ll.lat.toFixed(4)}°N, ${ll.lng.toFixed(4)}°E<small>${esc(t("coords"))}</small>`)}</ul>`);
  }
  map.on("click", e => {
    if (!ready) return;
    const hit = map.queryRenderedFeatures([[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]], { layers: CLICKABLE.filter(id => map.getLayer(id)) });
    if (hit.length) { const p = D.byId[hit[0].properties.id]; if (p) { openPlace(p, false); return; } }
    const lh = map.getLayer("qarachik-hit") && map.getLayoutProperty("qarachik-hit", "visibility") !== "none" ? map.queryRenderedFeatures(e.point, { layers: ["qarachik-hit"] }) : [];
    if (lh.length) { openLine(lh[0], e.lngLat); return; }
    if (!panel.hidden) { closeCard(); return; }
    dropPin(e.lngLat);
  });
  ["qarachik-hit"].concat(CLICKABLE).forEach(id => {
    map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
  });

  /* ---------- menu, saved places, personal account ---------- */
  function setMenu(open) { $("#menu").hidden = !open; $("#scrim").hidden = !open; $("#menuBtn").setAttribute("aria-expanded", String(open)); }
  $("#menuBtn").addEventListener("click", () => setMenu($("#menu").hidden));
  $("#menuClose").addEventListener("click", () => setMenu(false));
  $("#scrim").addEventListener("click", () => setMenu(false));
  document.addEventListener("keydown", e => { if (e.key === "Escape") { setMenu(false); $("#login").hidden = true; } });
  function drawSaved() {
    const s = saved().map(id => D.byId[id]).filter(Boolean);
    $("#savedList").innerHTML = s.length ? s.map(p => `<li data-id="${esc(p.id)}"><span class="r-ico" style="background:${dotColor(p)}">${kindIcon(p)}</span>${esc(nameOf(p))}</li>`).join("") : `<li class="none">${esc(t("noSaved"))}</li>`;
    $$("#savedList [data-id]").forEach(li => li.onclick = () => { setMenu(false); openPlace(D.byId[li.dataset.id], true); });
  }
  function openLogin() { setMenu(false); $("#loginErr").hidden = true; $("#login").hidden = false; setTimeout(() => $("#loginForm [name=u]").focus(), 50); }
  $("#acctBtn").addEventListener("click", openLogin);
  $("#loginX").addEventListener("click", () => ($("#login").hidden = true));
  $("#login").addEventListener("click", e => { if (e.target.id === "login") $("#login").hidden = true; });
  $("#loginForm").addEventListener("submit", e => {
    e.preventDefault();
    const b = $("#loginForm .btn-orange"); b.disabled = true; b.textContent = t("loginWait");
    setTimeout(() => { b.disabled = false; b.textContent = t("loginGo"); const er = $("#loginErr"); er.textContent = t("loginErr", { c: "BL-" + (4000 + Math.floor(Math.random() * 900)) }); er.hidden = false; }, 1600);
  });
  $("#qClear").innerHTML = ic("close"); $("#qGo").innerHTML = ic("search"); $("#menuBtn").innerHTML = ic("menu"); $("#menuClose").innerHTML = ic("close"); $("#loginX").innerHTML = ic("close");
  $("#acctBtn .i-user").outerHTML = ic("user");
  $("#qGo").addEventListener("click", () => { const r = search(qEl.value); if (r[0]) pick(r[0]); else qEl.focus(); });

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
