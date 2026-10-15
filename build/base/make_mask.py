"""Raster of Irad plus a 6 km fringe (0.01 deg cells over the base-map box) for the OSM extractor: detail
(buildings, minor roads, residential land) is kept only inside it.  python3 build/base/make_mask.py out.bin"""
import json, sys, os, numpy as np
from matplotlib.path import Path
from scipy import ndimage
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, E, S, N, G = 67.5, 75.5, 40.2, 46.5, 0.01
nx, ny = round((E - W) / G), round((N - S) / G)
xs = W + (np.arange(nx) + 0.5) * G; ys = S + (np.arange(ny) + 0.5) * G
X, Y = np.meshgrid(xs, ys); pts = np.column_stack([X.ravel(), Y.ravel()])
m = np.zeros(nx * ny, bool)
for f in json.load(open(os.path.join(ROOT, "data/irad.geojson")))["features"]:
    g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for p in polys:
        inside = Path(np.array(p[0])).contains_points(pts)
        for h in p[1:]: inside &= ~Path(np.array(h)).contains_points(pts)
        m |= inside
m = ndimage.binary_dilation(m.reshape(ny, nx), iterations=6)
open(sys.argv[1], "wb").write(np.packbits(m, axis=None, bitorder="little").tobytes() if False else m.astype(np.uint8).tobytes())
print(nx, ny, m.mean())
