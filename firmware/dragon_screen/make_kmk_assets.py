#!/usr/bin/env python3
"""Pack the Lazy Dragon screen art for the KMK (CircuitPython) port on the Lucca-58HE.

Writes ~/PCBs/Lucca-58HE/dragon_screen/dragon_assets.bin: the art laid out as portrait
strips 32 px wide (offsets printed below must match dragon_screen.py), then stored turned
on its side as a 1376 x 32, 1-bit image, leftmost pixel in the top bit of each byte (what
bitmaptools.readinto expects by default).
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
art = json.load(open(os.path.join(HERE, "dragon_art.json")))
glyph = dict(zip(art["chars"], [bytes.fromhex(g) for g in art["font"]]))

rows = []
def block(n):
    start = len(rows); rows.extend([0] * n); return start
def px(base, x, y, on=True):
    if 0 <= x < 32:
        rows[base + y] = (rows[base + y] | (1 << x)) if on else (rows[base + y] & ~(1 << x))
def text(base, s, x, y, scale=1, adv=6, ink=True):
    for c in s:
        g = glyph[c]
        for col in range(5):
            for r in range(7):
                if g[col] >> r & 1:
                    for sx in range(scale):
                        for sy in range(scale): px(base, x + col * scale + sx, y + r * scale + sy, ink)
        x += adv
def pill(label, filled):
    base = block(11); w = len(label) * 6 + 3; x0 = (32 - w) // 2
    for y in range(11):
        for x in range(x0, x0 + w):
            side, cap = x in (x0, x0 + w - 1), y in (0, 10)
            px(base, x, y, not (side and cap) and (filled or side or cap))
    text(base, label, x0 + 2, 2, ink=not filled)
    return base

offsets = {}
offsets["POSES"] = block(0)
for pose in art["poses"]:
    rows.extend(int(h, 16) for h in pose)
offsets["PILL_BASE"] = pill("BASE", False)
offsets["PILL_FN"] = pill("FN", True)
offsets["PILL_CAPS_OFF"] = pill("CAPS", False)
offsets["PILL_CAPS_ON"] = pill("CAPS", True)
offsets["WPM_LABEL"] = b = block(7); text(b, "WPM", 7, 0)
offsets["DIGITS"] = block(0)
for d in "0123456789":
    b = block(14); text(b, d, 0, 0, scale=2)
offsets["Z_SMALL"] = b = block(3)
for i in range(3): px(b, i, 0); px(b, i, 2)
px(b, 1, 1)
offsets["Z_BIG"] = b = block(4)
for i in range(4): px(b, i, 0); px(b, i, 3)
px(b, 2, 1); px(b, 1, 2)
offsets["SPARK"] = b = block(3)
for x, y in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)): px(b, x, y)

# Stored on its side (landscape, 1376 x 32), since the screen is driven in its native
# landscape orientation with no rotation (rotating in the driver garbles it).
#   dragon_assets.bin          upright on the Lucca: portrait (x, y) -> atlas (W-1-y, x)
#   dragon_assets_flipped.bin  the other way up:     portrait (x, y) -> atlas (y, 31-x)
W = 1376
assert len(rows) <= W
def bit(r, c): return r < len(rows) and rows[r] >> c & 1
outdir = os.path.expanduser("~/PCBs/Lucca-58HE/dragon_screen")
out = os.path.join(outdir, "dragon_assets.bin")
for name, pixel in (("dragon_assets.bin", lambda X, Y: bit(W - 1 - X, Y)),
                    ("dragon_assets_flipped.bin", lambda X, Y: bit(X, 31 - Y))):
    with open(os.path.join(outdir, name), "wb") as f:
        for Y in range(32):
            bits = "".join("1" if pixel(X, Y) else "0" for X in range(W))
            f.write(bytes(int(bits[i:i + 8], 2) for i in range(0, W, 8)))
print("rows", len(rows), "bytes", os.path.getsize(out), "(%d x 32)" % W)
for k, v in offsets.items(): print("_%s = const(%d)" % (k, v))
