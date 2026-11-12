# Make one repeat of a vine border for the alternating ivy wrap in build_case.py.
#   python3 make_ivy_tile.py IMAGE OUT.json [CUT_WINDOW_PX] [MAX_DY_PX]
# - Keeps only the largest connected piece of ink, so nothing in the pattern floats.
# - Finds "stem-only" columns: one run of ink, roughly stem thickness, and the same
#   within CUT_WINDOW_PX either side. Only these may be cut, so no leaf is ever sliced:
#   anything crossing such a column would add a second run.
# - Picks the longest repeat whose two ends are both stem-only, at full stem thickness,
#   with stem heights within MAX_DY_PX. A slight vertical shear then levels the ends.
#   Copies alternate normal / rotated 180 deg about the stem axis. Each joint pairs an
#   end with the rotated copy of the same end, so the stem runs straight through it.
# - Writes the outline (pixels, u from the start of the repeat, v up from the stem axis)
#   plus the per-column "cut_ok" flags so the build can end the vine only at bare stem.
import sys, os, json, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_art import load_ink, trace

img, out = sys.argv[1], sys.argv[2]
WIN = int(sys.argv[3]) if len(sys.argv) > 3 else 8
MAX_DY = float(sys.argv[4]) if len(sys.argv) > 4 else 40
OV = 4
ink = load_ink(img); H, W = ink.shape
# largest 8-connected component
lab = np.zeros(ink.shape, np.int32); sizes = {}; n = 0
for y0, x0 in zip(*np.nonzero(ink)):
    if lab[y0, x0]: continue
    n += 1; q = collections.deque([(y0, x0)]); lab[y0, x0] = n; c = 0
    while q:
        y, x = q.popleft(); c += 1
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and ink[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; q.append((yy, xx))
    sizes[n] = c
big = max(sizes, key=sizes.get); ink = lab == big
dropped = sorted((s for k, s in sizes.items() if k != big), reverse=True)
# per-column runs
def runs(col):
    d = np.diff(np.concatenate(([0], col.astype(np.int8), [0])))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))
cols = [runs(ink[:, x]) for x in range(W)]
single = [r[0][1] - r[0][0] for r in cols if len(r) == 1]
med = float(np.median(single))
stem = np.array([len(r) == 1 and 0.6 * med <= r[0][1] - r[0][0] <= 1.6 * med for r in cols])
ok = np.array([stem[max(0, x - WIN):x + WIN + 1].all() for x in range(W)])
cy = {x: (cols[x][0][0] + cols[x][0][1] - 1) / 2 for x in range(W) if stem[x]}
th = {x: cols[x][0][1] - cols[x][0][0] for x in range(W) if stem[x]}
cand = [x for x in range(W) if ok[x] and th[x] >= 0.75 * med and OV <= x < W - OV]   # not the tapered tips
best = None
for xa in cand:
    for xb in cand:
        if xb - xa < W / 2: continue
        dy = cy[xb] - cy[xa]
        if abs(dy) > MAX_DY: continue
        key = (xb - xa, -abs(dy))
        if best is None or key > best[0]: best = (key, xa, xb, dy)
if best is None: raise SystemExit("no pair of stem-only columns at matching heights")
_, xa, xb, dy = best
period = xb - xa; axis = cy[xa]
crop = ink[:, xa - OV:xb + OV + 1]
loops = []
for q in trace(crop):
    x = q[:, 0] + (xa - OV)                              # image columns
    y = q[:, 1] - (x - xa) * dy / period                # shear: both ends at the axis
    u = x - xa; v = -(y - axis)
    loops.append([[round(a, 3), round(b, 3)] for a, b in zip(u, v)])
half = max(abs(v) for lp in loops for _, v in lp)
json.dump({"image": img, "units": "px", "alternate": True, "period_px": period, "overlap_px": OV,
           "half_height_px": half, "stem_px": med, "crop": [xa, xb], "shear_dy_px": dy,
           "dropped_components_px": dropped, "cut_ok": ok[xa:xb + 1].astype(int).tolist(),
           "loops": loops}, open(out, "w"))
print(f"kept 1 component, dropped {len(dropped)} {dropped[:5]}; stem {med:.0f} px; repeat x {xa}..{xb} "
      f"({period} px), ends at y {cy[xa]:.1f}/{cy[xb]:.1f} (shear {dy:+.1f} px), half-height {half:.0f} px, "
      f"{len(loops)} loop(s), {int(ok[xa:xb + 1].sum())} cuttable columns")
