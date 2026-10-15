"""Minimal PMTiles v3 writer (uncompressed directories), enough for Kartalar's raster terrain archives."""
import json, struct


def zxy_to_tileid(z, x, y):
    acc = ((1 << (z * 2)) - 1) // 3
    n = 1 << z
    d = 0
    s = n >> 1
    while s > 0:
        rx = 1 if x & s else 0
        ry = 1 if y & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x = n - 1 - x; y = n - 1 - y
            x, y = y, x
        s >>= 1
    return acc + d


def tileid_to_zxy(t):
    acc, z = 0, 0
    while True:
        num = 1 << (2 * z)
        if acc + num > t: break
        acc += num; z += 1
    d = t - acc; n = 1 << z; x = y = 0; s = 1
    while s < n:
        rx = 1 & (d >> 1); ry = 1 & (d ^ rx)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x; y = s - 1 - y
            x, y = y, x
        x += s * rx; y += s * ry
        d >>= 2; s <<= 1
    return z, x, y


def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: out.append(b | 0x80)
        else: out.append(b); return bytes(out)


def read_varint(b, i):
    shift = val = 0
    while True:
        c = b[i]; i += 1
        val |= (c & 0x7F) << shift; shift += 7
        if not c & 0x80: return val, i


def encode_dir(entries):  # entries: (tile_id, offset, length, run_length)
    out = bytearray(varint(len(entries)))
    last = 0
    for e in entries: out += varint(e[0] - last); last = e[0]
    for e in entries: out += varint(e[3])
    for e in entries: out += varint(e[2])
    for i, e in enumerate(entries):
        if i > 0 and e[1] == entries[i - 1][1] + entries[i - 1][2]: out += varint(0)
        else: out += varint(e[1] + 1)
    return bytes(out)


def write(path, tiles, tile_type=2, bounds=(67.5, 40.2, 75.5, 46.5), metadata=None):
    """tiles: dict {(z,x,y): bytes}"""
    items = sorted(((zxy_to_tileid(*k), v) for k, v in tiles.items()), key=lambda t: t[0])
    data = bytearray(); entries = []
    for tid, b in items:
        entries.append((tid, len(data), len(b), 1)); data += b
    root = encode_dir(entries); leaves = b""
    if len(root) > 16384 - 127:
        leaf_size = 4096
        while True:
            leaves = bytearray(); root_entries = []
            for i in range(0, len(entries), leaf_size):
                chunk = entries[i:i + leaf_size]; enc = encode_dir(chunk)
                root_entries.append((chunk[0][0], len(leaves), len(enc), 0)); leaves += enc
            root = encode_dir(root_entries)
            if len(root) <= 16384 - 127: break
            leaf_size *= 2
    meta = json.dumps(metadata or {}).encode()
    zs = [k[0] for k in tiles]
    root_off = 127; meta_off = root_off + len(root); leaf_off = meta_off + len(meta); data_off = leaf_off + len(leaves)
    hdr = b"PMTiles" + bytes([3])
    hdr += struct.pack("<QQQQQQQQQQQ", root_off, len(root), meta_off, len(meta), leaf_off, len(leaves), data_off, len(data),
                       len(entries), len(entries), len(entries))
    hdr += bytes([1, 1, 1, tile_type, min(zs), max(zs)])
    hdr += struct.pack("<iiii", *(round(v * 1e7) for v in bounds))
    hdr += bytes([min(zs)]) + struct.pack("<ii", round((bounds[0] + bounds[2]) / 2 * 1e7), round((bounds[1] + bounds[3]) / 2 * 1e7))
    assert len(hdr) == 127
    with open(path, "wb") as f:
        f.write(hdr); f.write(root); f.write(meta); f.write(leaves); f.write(data)


def read_dir(b):
    n, i = read_varint(b, 0); ids, runs, lens, offs = [], [], [], []
    last = 0
    for _ in range(n): d, i = read_varint(b, i); last += d; ids.append(last)
    for _ in range(n): v, i = read_varint(b, i); runs.append(v)
    for _ in range(n): v, i = read_varint(b, i); lens.append(v)
    for k in range(n):
        v, i = read_varint(b, i)
        offs.append(offs[k - 1] + lens[k - 1] if v == 0 and k > 0 else v - 1)
    return list(zip(ids, offs, lens, runs))
