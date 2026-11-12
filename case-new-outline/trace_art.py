# Trace a black-on-white line drawing into closed outline loops (mm) for build_case.py.
#   python3 trace_art.py IMAGE OUT.json WIDTH_MM [DILATE_PX] [X0:X1:OVERLAP]
# The ink is thresholded at 50 % (transparent pixels count as white), optionally
# thickened by DILATE_PX pixels (so thin strokes survive an FDM first layer), traced
# with marching squares and simplified.
# Without a crop: loops are in mm, centred on the ink bounding box, u right, v up.
# With X0:X1:OVERLAP: one repeat of a tiling border. Image columns X0..X1 are the
# period, OVERLAP extra columns past X1 let neighbouring copies overlap. Loops are then
# in pixels with u from X0 and v about the ink's vertical centre (WIDTH_MM is ignored),
# plus the ink count of every period column so a build can place cuts in sparse spots.
# make_ivy_tile.py imports load_ink/dilate/trace from here.
import sys, json
import numpy as np
from PIL import Image

def load_ink(img):
    src = Image.open(img).convert("RGBA")
    white = Image.new("RGBA", src.size, (255, 255, 255, 255)); white.alpha_composite(src)
    return np.array(white.convert("L")) < 128

def dilate(ink, n):
    for _ in range(n):                    # 3x3 dilation
        p = np.pad(ink, 1)
        ink = np.zeros_like(ink)
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                ink |= p[dy:dy + ink.shape[0], dx:dx + ink.shape[1]]
    return ink

def rdp(pts, eps):
    pts = np.asarray(pts, float)
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1: continue
        a, b = pts[i], pts[j]; ab = b - a; n = np.hypot(*ab)
        seg = pts[i + 1:j]
        d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / n if n else np.hypot(*(seg - a).T)
        k = int(np.argmax(d))
        if d[k] > eps: keep[i + 1 + k] = True; stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return pts[keep]

def trace(ink, eps=0.45):
    """Closed outline loops of a boolean image, as arrays of (x, y) pixel coordinates."""
    g = np.pad(ink, 1).astype(np.uint8)   # border of white so every loop closes
    # marching squares: corner bits a=TL b=TR c=BR d=BL; midpoints keyed in half-pixels
    idx = (g[:-1, :-1] << 3) | (g[:-1, 1:] << 2) | (g[1:, 1:] << 1) | g[1:, :-1]
    T = lambda x, y: (2 * x + 1, 2 * y); R = lambda x, y: (2 * x + 2, 2 * y + 1)
    B = lambda x, y: (2 * x + 1, 2 * y + 2); L = lambda x, y: (2 * x, 2 * y + 1)
    CASES = {1: ((L, B),), 2: ((B, R),), 3: ((L, R),), 4: ((T, R),), 5: ((T, R), (L, B)),
             6: ((T, B),), 7: ((T, L),), 8: ((T, L),), 9: ((T, B),), 10: ((T, L), (R, B)),
             11: ((T, R),), 12: ((L, R),), 13: ((R, B),), 14: ((L, B),)}
    nb = {}
    for y, x in zip(*np.nonzero((idx > 0) & (idx < 15))):
        for e0, e1 in CASES[int(idx[y, x])]:
            p, q = e0(x, y), e1(x, y)
            nb.setdefault(p, []).append(q); nb.setdefault(q, []).append(p)
    loops, seen = [], set()
    for start in nb:
        if start in seen: continue
        loop = [start]; seen.add(start); prev, cur = None, start
        while True:
            nxt = [q for q in nb[cur] if q != prev]
            nxt = nxt[0] if nxt else nb[cur][0]
            if nxt == start: break
            if nxt in seen: break
            loop.append(nxt); seen.add(nxt); prev, cur = cur, nxt
        if len(loop) >= 4: loops.append(loop)
    out = []
    for lp in loops:
        pts = np.array(lp, float) / 2.0 - 0.5     # half-pixel keys -> pixel coords (padding removed)
        k = int(np.argmax(pts[:, 0] + 1e-3 * pts[:, 1]))   # start on an extreme point so RDP keeps the shape
        pts = np.vstack([pts[k:], pts[:k], pts[k:k + 1]])
        q = rdp(pts, eps)[:-1]
        if len(q) >= 3: out.append(q)
    return out

if __name__ == "__main__":
    img, out, width = sys.argv[1], sys.argv[2], float(sys.argv[3])
    dil = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    crop = [int(v) for v in sys.argv[5].split(":")] if len(sys.argv) > 5 else None
    ink = load_ink(img)
    if crop:
        x0, x1, ov = crop
        ink = ink[:, x0:x1 + ov]
        ys = np.nonzero(ink.any(axis=1))[0]
        ink = ink[ys.min():ys.max() + 1]
    else:
        ys, xs = np.nonzero(ink)
        ink = ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ink = dilate(ink, dil)
    H, W = ink.shape
    s = width / W if not crop else 1.0       # mm per pixel (pixels when tiling)
    res = []
    for q in trace(ink):
        u = (q[:, 0] - ((W - 1) / 2 if not crop else 0)) * s; v = -(q[:, 1] - (H - 1) / 2) * s
        res.append([[round(a, 4), round(b, 4)] for a, b in zip(u, v)])
    meta = {"image": img, "dilate_px": dil, "loops": res}
    if crop:
        meta.update(units="px", period_px=crop[1] - crop[0], overlap_px=crop[2], height_px=H,
                    column_ink=ink[:, :crop[1] - crop[0]].sum(axis=0).tolist())
        print(f"{len(res)} loops, {sum(map(len, res))} points, period {crop[1] - crop[0]} px, height {H} px")
    else:
        meta.update(width_mm=width, height_mm=H * s, mm_per_px=s)
        print(f"{len(res)} loops, {sum(map(len, res))} points, art {width:.1f} x {H * s:.1f} mm, {s:.4f} mm/px")
    json.dump(meta, open(out, "w"))
