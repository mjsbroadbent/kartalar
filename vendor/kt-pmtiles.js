/* Minimal PMTiles v3 reader for Kartalar's own tile archives, registered as the MapLibre protocol "kt://".
   Tile URL: kt://<archive>/{z}/{x}/{y}; archives live in tiles/<archive>.pmtiles. An archive name can map to
   several files by zoom (see KT_ARCHIVES). Directories and tiles may be gzip-compressed; HTTP range requests fetch
   only the header, the directories needed and each tile. */
(function () {
  const BASE = (window.KT_TILE_BASE || "tiles/");
  const ARCHIVES = window.KT_ARCHIVES || {};
  const cache = new Map();          // file -> Promise<archive>

  function zxyToId(z, x, y) {
    let acc = 0; for (let i = 0; i < z; i++) acc += 4 ** i;
    const n = 2 ** z; let d = 0;
    for (let s = n / 2; s >= 1; s /= 2) {
      const rx = (x & s) ? 1 : 0, ry = (y & s) ? 1 : 0;
      d += s * s * ((3 * rx) ^ ry);
      if (ry === 0) { if (rx === 1) { x = n - 1 - x; y = n - 1 - y; } const t = x; x = y; y = t; }
    }
    return acc + d;
  }
  async function range(url, off, len, signal) {
    const r = await fetch(url, { headers: { Range: `bytes=${off}-${off + len - 1}` }, signal });
    if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
    const b = await r.arrayBuffer();
    if (r.status === 200 && b.byteLength > len) return b.slice(off, off + len);   // server ignored the range
    return b;
  }
  async function gunzip(buf) {
    const ds = new DecompressionStream("gzip");
    return await new Response(new Blob([buf]).stream().pipeThrough(ds)).arrayBuffer();
  }
  const dec = (buf, c) => c === 2 ? gunzip(buf) : Promise.resolve(buf);
  function u64(dv, o) { return dv.getUint32(o, true) + dv.getUint32(o + 4, true) * 4294967296; }
  function readDir(buf) {
    const b = new Uint8Array(buf); let i = 0;
    const vi = () => { let v = 0, m = 1, c; do { c = b[i++]; v += (c & 0x7f) * m; m *= 128; } while (c & 0x80); return v; };
    const n = vi(), ids = new Array(n), runs = new Array(n), lens = new Array(n), offs = new Array(n);
    let last = 0;
    for (let k = 0; k < n; k++) { last += vi(); ids[k] = last; }
    for (let k = 0; k < n; k++) runs[k] = vi();
    for (let k = 0; k < n; k++) lens[k] = vi();
    for (let k = 0; k < n; k++) { const v = vi(); offs[k] = (v === 0 && k > 0) ? offs[k - 1] + lens[k - 1] : v - 1; }
    return { ids, runs, lens, offs };
  }
  function find(dir, id) {
    let lo = 0, hi = dir.ids.length - 1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (dir.ids[m] < id) lo = m + 1; else if (dir.ids[m] > id) hi = m - 1; else return m; }
    if (hi >= 0) { if (dir.runs[hi] === 0) return hi; if (id - dir.ids[hi] < dir.runs[hi]) return hi; }
    return -1;
  }
  function open(file) {
    if (cache.has(file)) return cache.get(file);
    const p = (async () => {
      const url = BASE + file;
      const head = await range(url, 0, 16384);
      const dv = new DataView(head);
      const h = { rootOff: u64(dv, 8), rootLen: u64(dv, 16), leafOff: u64(dv, 40), dataOff: u64(dv, 56),
                  ic: dv.getUint8(97), tc: dv.getUint8(98), type: dv.getUint8(99), url, leaves: new Map() };
      h.root = readDir(await dec(head.slice(h.rootOff, h.rootOff + h.rootLen), h.ic));
      return h;
    })();
    cache.set(file, p); p.catch(() => cache.delete(file));
    return p;
  }
  async function tile(file, z, x, y, signal) {
    const a = await open(file); const id = zxyToId(z, x, y);
    let dir = a.root;
    for (let depth = 0; depth < 4; depth++) {
      const k = find(dir, id); if (k < 0) return null;
      if (dir.runs[k] > 0) {
        const raw = await range(a.url, a.dataOff + dir.offs[k], dir.lens[k], signal);
        return await dec(raw, a.tc);
      }
      const key = dir.offs[k];
      if (!a.leaves.has(key)) a.leaves.set(key, range(a.url, a.leafOff + dir.offs[k], dir.lens[k]).then(b => dec(b, a.ic)).then(readDir));
      dir = await a.leaves.get(key);
    }
    return null;
  }
  window.ktTile = (file, z, x, y) => tile(file, z, x, y).then(d => d ? d.byteLength : null);   // for debugging
  maplibregl.addProtocol("kt", async (params, abort) => {
    const m = params.url.match(/^kt:\/\/([^/]+)\/(\d+)\/(\d+)\/(\d+)/);
    if (!m) throw new Error("bad kt url " + params.url);
    const name = m[1], z = +m[2], x = +m[3], y = +m[4];
    const pick = ARCHIVES[name]; const file = (typeof pick === "function" ? pick(z) : pick) || name + ".pmtiles";
    const data = await tile(file, z, x, y, abort && abort.signal);
    if (!data && name.startsWith("dem")) throw new Error("no terrain tile " + params.url);
    return { data: data ? new Uint8Array(data) : new Uint8Array(0) };
  });
})();
