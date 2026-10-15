"""A fine elevation grid (KTDEM1, 0.001 deg, ~90 m) from the terrain export, for the road and railway routers and the
road audit.  python3 build/base/make_fine_dem.py kartalar-terrain.bin out.bin"""
import io, math, struct, sys
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, OUT = sys.argv[1], sys.argv[2]
LON0, LAT0, STEP, NX, NY = 67.6, 40.25, 0.001, 7801, 6151      # 67.6-75.4 E, 40.25-46.4 N
f = open(SRC, "rb"); assert f.read(8) == b"KTTILES1"
tiles = {}
while True:
    h = f.read(9)
    if len(h) < 9: break
    z, x, y, L = struct.unpack("<BHHI", h)
    a = np.asarray(Image.open(io.BytesIO(f.read(L))).convert("RGB")).astype(np.int32)
    tiles[(x, y)] = (a[..., 0] * 256 + a[..., 1] - 32768).astype(np.int16); Z = z
xs = [k[0] for k in tiles]; ys = [k[1] for k in tiles]; X0, Y0 = min(xs), min(ys)
M = np.zeros(((max(ys) - Y0 + 1) * 256, (max(xs) - X0 + 1) * 256), np.int16)
for (x, y), t in tiles.items(): M[(y - Y0) * 256:(y - Y0 + 1) * 256, (x - X0) * 256:(x - X0 + 1) * 256] = t
n = 2 ** Z * 256
lons = LON0 + np.arange(NX) * STEP; lats = LAT0 + np.arange(NY) * STEP
px = (lons + 180) / 360 * n - X0 * 256
py = (1 - np.log(np.tan(np.radians(lats)) + 1 / np.cos(np.radians(lats))) / math.pi) / 2 * n - Y0 * 256
out = np.zeros((NY, NX), np.int16)
for j in range(NY):
    out[j] = ndimage.map_coordinates(M, [np.full(NX, py[j]), px], order=1, mode="nearest")
hdr = b"KTDEM1\0\0" + struct.pack("<3d", LON0, LAT0, STEP) + struct.pack("<2i", NX, NY)
open(OUT, "wb").write(hdr + b"\0" * (64 - len(hdr)) + out.astype("<i2").tobytes())
print(NX, NY, out.min(), out.max())
