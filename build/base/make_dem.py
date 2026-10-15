"""Terrain archives for the hill shading, from the terrain export (tools/terrain-export.html).

  python3 build/base/make_dem.py kartalar-terrain.bin tiles/

Elevations are rounded to whole metres (Terrarium blue channel fixed), which makes the PNGs compress far better, and a
pyramid down to zoom 5 is built by averaging (edges padded from the nearest data, so no false cliffs where the export
ends). Tiles are lossless WebP. One archive, dem.pmtiles, if it stays under GitHub's file limit; otherwise the top
zoom goes to dem<z>.pmtiles and the page picks the archive by zoom.
"""
import io, os, struct, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmtiles_write as P

SRC, OUT = sys.argv[1], sys.argv[2]


def decode(png):
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def encode(e):
    v = np.clip(np.round(e) + 32768, 0, 65535).astype(np.int64)
    rgb = np.stack([v >> 8, v & 255, np.full_like(v, 0)], -1).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(rgb, "RGB").save(buf, "WEBP", lossless=True, quality=100, method=4); return buf.getvalue()


def main():
    f = open(SRC, "rb"); assert f.read(8) == b"KTTILES1"
    elev = {}
    while True:
        h = f.read(9)
        if len(h) < 9: break
        z, x, y, L = struct.unpack("<BHHI", h); elev[(z, x, y)] = decode(f.read(L))
    zmax = max(k[0] for k in elev)
    levels = {zmax: elev}
    for z in range(zmax - 1, 4, -1):
        up = levels[z + 1]; cur = {}
        parents = {(x >> 1, y >> 1) for (_, x, y) in up}
        for (px, py) in parents:
            big = np.full((512, 512), np.nan, np.float32)
            for dx in (0, 1):
                for dy in (0, 1):
                    t = up.get((z + 1, px * 2 + dx, py * 2 + dy))
                    if t is not None: big[dy * 256:(dy + 1) * 256, dx * 256:(dx + 1) * 256] = t
            small = np.nanmean(big.reshape(256, 2, 256, 2), axis=(1, 3))
            bad = np.isnan(small)
            if bad.any():   # smooth extrapolation (normalised convolution), so no streaks or cliffs past the data
                ok = (~bad).astype(np.float32); v = np.where(bad, 0, small)
                for sg in (8, 32, 96):
                    num = ndimage.gaussian_filter(v * ok, sg, mode="nearest"); den = ndimage.gaussian_filter(ok, sg, mode="nearest")
                    fill = np.where(den > 1e-6, num / np.maximum(den, 1e-6), np.nan)
                    upd = bad & ~np.isnan(fill); small = np.where(upd, fill, small); v = np.where(upd, fill, v); ok = np.where(upd, 1.0, ok).astype(np.float32); bad = bad & ~upd
                    if not bad.any(): break
                if bad.any(): small = np.where(bad, np.nanmean(small), small)
            cur[(z, px, py)] = small
        levels[z] = cur
        print(f"  z{z}: {len(cur)} tiles")
    os.makedirs(OUT, exist_ok=True)
    top = {k: encode(v) for k, v in levels[zmax].items()}
    low = {k: encode(v) for z in levels if z < zmax for k, v in levels[z].items()}
    meta = {"name": "Kartalar terrain", "encoding": "terrarium", "attribution": "Mapzen Terrarium (AWS)"}
    for fn in os.listdir(OUT):
        if fn.startswith("dem") and fn.endswith(".pmtiles"): os.remove(os.path.join(OUT, fn))
    if sum(map(len, top.values())) + sum(map(len, low.values())) < 95e6:
        P.write(os.path.join(OUT, "dem.pmtiles"), {**low, **top}, tile_type=4, metadata=meta)
    else:
        P.write(os.path.join(OUT, f"dem{zmax}.pmtiles"), top, tile_type=4, metadata=meta)
        P.write(os.path.join(OUT, "dem.pmtiles"), low, tile_type=4, metadata=meta)
    for fn in sorted(os.listdir(OUT)):
        if fn.startswith("dem"): print(f"  {fn}: {os.path.getsize(os.path.join(OUT, fn)) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
