#!/usr/bin/env python3
"""Regenerate the key layout and the RGB Matrix LED map in qmk/lazydragon64/info.json
from the KiCad board, so they always match the PCB.

Run with KiCad's Python (it needs the pcbnew module):  python3 gen_layout.py

What it reads from ../lazydragon64.kicad_pcb (left half, as drawn):
  - each switch's centre: the 4 mm centre hole (the footprint origin is a corner)
  - its matrix position: the ROWn net on the switch and the COLn net on its diode
  - the LED chain: DIN (pad 2) / DOUT (pad 4), starting from the KEYLED net
The right half is the same board turned over, so its keys and LEDs are the left
ones mirrored in x, in the same chain order, on matrix rows 5-9.
"""
import json, os, re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "lazydragon64.kicad_pcb")
INFO = os.path.join(HERE, "qmk", "lazydragon64", "info.json")
U = 19.05            # 1u in mm
MIRROR = 15.0        # right key centre (u) = MIRROR - left key centre: leaves a 1u gap

b = pcbnew.LoadBoard(BOARD)
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
def nets(fp): return {pd.GetNumber(): pd.GetNetname() for pd in fp.Pads()}
netrefs = {}
for fp in b.GetFootprints():
    for pd in fp.Pads(): netrefs.setdefault(pd.GetNetname(), set()).add(fp.GetReference())

keys = {}            # SWn -> dict(row, col, cx, cy, w)
for ref, fp in fps.items():
    if not re.fullmatch(r"SW\d+", ref): continue
    hole = [pd for pd in fp.Pads() if abs(pd.GetDrillSize().x / 1e6 - 4.0) < 0.01][0].GetPosition()
    ns = set(nets(fp).values())
    row = int(next(n for n in ns if n.startswith("ROW"))[3:]) - 1
    dnet = next(n for n in ns if n.startswith("Net-(D"))
    diode = next(r for r in netrefs[dnet] if r.startswith("D") and r != ref)
    col = int(next(n for n in nets(fps[diode]).values() if n.startswith("COL"))[3:]) - 1
    w = 1.5 if "1.5U" in fp.GetFPID().GetLibItemName().wx_str() else 1.0
    keys[ref] = dict(row=row, col=col, cx=hole.x / 1e6, cy=hole.y / 1e6, w=w)
assert len(keys) == 32 and len({(k["row"], k["col"]) for k in keys.values()}) == 32

leds = {r: fp for r, fp in fps.items() if "SK6812" in fp.GetFPID().GetLibItemName().wx_str()}
by_din = {nets(fp)["2"]: r for r, fp in leds.items()}
chain, cur = [], by_din["KEYLED"]
while cur and cur not in chain:
    chain.append(cur); cur = by_din.get(nets(leds[cur])["4"])
assert len(chain) == 32, "LED chain broken after %s" % chain[-1]
def key_of(led):
    p = leds[led].GetPosition()
    return min(keys, key=lambda s: (keys[s]["cx"] - p.x / 1e6) ** 2 + (keys[s]["cy"] - p.y / 1e6) ** 2)
led_keys = [key_of(d) for d in chain]
assert len(set(led_keys)) == 32

x0 = min(k["cx"] for k in keys.values()); y0 = min(k["cy"] for k in keys.values())
def centre(k, right):    # key centre in units, right half mirrored
    u = (k["cx"] - x0) / U + 0.5; v = (k["cy"] - y0) / U + 0.5
    return (MIRROR - u if right else u), v

# LAYOUT order: row by row, left half outer -> inner, then right half inner -> outer
layout = []
for r in range(5):
    left = sorted((k for k in keys.values() if k["row"] == r), key=lambda k: k["col"])
    for right, ks in ((False, left), (True, left[::-1])):
        for k in ks:
            u, v = centre(k, right)
            layout.append({"matrix": [r + 5 * right, k["col"]],
                           "x": round(u - k["w"] / 2, 2), "y": round(v - 0.5, 2),
                           **({"w": k["w"]} if k["w"] != 1 else {})})
assert len(layout) == 64

pts = [centre(keys[s], right) for right in (False, True) for s in led_keys]
umin, umax = min(p[0] for p in pts), max(p[0] for p in pts)
vmin, vmax = min(p[1] for p in pts), max(p[1] for p in pts)
rgb = []
for i, s in enumerate(led_keys * 2):
    right = i >= 32; k = keys[s]; u, v = centre(k, right)
    rgb.append({"matrix": [k["row"] + 5 * right, k["col"]],
                "x": round(224 * (u - umin) / (umax - umin)), "y": round(64 * (v - vmin) / (vmax - vmin)), "flags": 4})

info = json.load(open(INFO))
info["layouts"]["LAYOUT"]["layout"] = layout
info["rgb_matrix"]["layout"] = rgb
text = json.dumps(info, indent=4, ensure_ascii=False)
# one key / LED per line, as in QMK's own keyboard files
text = re.sub(r'\[\s*(\d+),\s*(\d+)\s*\]', r'[\1, \2]', text)
text = re.sub(r'\{\s+("matrix": \[\d+, \d+\],)\s*', r'{\1 ', text)
text = re.sub(r'\{("matrix": \[\d+, \d+\], )((?:\s*"[a-z]+": [\d.]+,?)+)\s*\}',
              lambda m: "{" + m.group(1) + re.sub(r",\s*", ", ", m.group(2).strip()) + "}", text)
open(INFO, "w").write(text + "\n")
print("wrote %d keys and %d LEDs to %s" % (len(layout), len(rgb), INFO))
