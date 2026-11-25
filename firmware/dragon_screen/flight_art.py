#!/usr/bin/env python3
"""Lazy Dragon OLED, right half: the dragon flying, seen from above.

The art for flight_scene.c, drawn on the same 32 px wide upright canvas as art.py
(x right, y down, the dragon flying towards y = 0). Run it to write:

  ../qmk/lazydragon64/flight_art.h   the dragon's parts and the ground and clouds, as
                                     32-bit row masks (row y, bit x = pixel (x, y))
  flight_parts.png                   every part, 8x, for checking the art by eye

The dragon is drawn in three parts so that each can move on its own: the tail (swaying),
the wings (flapping) and the body (head, neck, torso; mouth shut or open). Each part is a
grid of 0 (not part of it), 1 (lit) and 2 (part of it, but dark: eyes, spine plates,
finger bones). For each part the header holds three masks:
  sil  the part's outline, cleared before the part is drawn so it hides what's behind
  ink  the lit pixels
  halo sil grown by one pixel; the screen clears all three halos first, which gives the
       whole dragon a dark border against the ground and clouds
"""
import math, os, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W = 32
CX = 16.0  # the body's centre line, between columns 15 and 16

# ----------------------------------------------------------------- helpers

def grid(h):
    return [[0] * W for _ in range(h)]

def mirror_rows(left_half):
    """16-character left halves -> full 32-wide rows, mirrored about the centre line"""
    code = {".": 0, "#": 1, "x": 2}
    return [[code[c] for c in r] + [code[c] for c in reversed(r)] for r in left_half]

def inside(poly, x, y):
    n, c = len(poly), False
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c

def fill_poly(g, poly, v=1):
    for y in range(len(g)):
        for x in range(W):
            if inside(poly, x + 0.5, y + 0.5):
                g[y][x] = v

def line(g, a, b, v, only_on=None):
    """Bresenham from a to b (pixel coordinates); with only_on, only over those values"""
    (x0, y0), (x1, y1) = (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1])))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    e = dx + dy
    while True:
        if 0 <= y0 < len(g) and 0 <= x0 < W and (only_on is None or g[y0][x0] in only_on):
            g[y0][x0] = v
        if (x0, y0) == (x1, y1):
            return
        e2 = 2 * e
        if e2 >= dy: e += dy; x0 += sx
        if e2 <= dx: e += dx; y0 += sy

def masks(g):
    sil = [sum(1 << x for x in range(W) if g[y][x]) for y in range(len(g))]
    ink = [sum(1 << x for x in range(W) if g[y][x] == 1) for y in range(len(g))]
    halo = []
    for y in range(len(g)):
        m = 0
        for dy in (-1, 0, 1):
            if 0 <= y + dy < len(g):
                r = sil[y + dy]
                m |= r | (r << 1) | (r >> 1)
        halo.append(m & 0xFFFFFFFF)
    return sil, ink, halo

# ----------------------------------------------------------------- the body

# Head pointing up, horns swept back, a row of dark spine plates, hind legs tucked in.
BODY_L = [
    "...............#",  # 0  snout
    "..............##",  # 1
    "..............##",  # 2
    ".............###",  # 3
    ".............#x#",  # 4  eyes
    ".............###",  # 5
    "............#.##",  # 6  horns
    "...........#..##",  # 7
    "...........#..##",  # 8
    "..............##",  # 9  neck
    "..............##",  # 10
    ".............###",  # 11 shoulders
    ".............###",  # 12
    ".............##x",  # 13 spine plate
    ".............###",  # 14
    ".............###",  # 15
    ".............##x",  # 16
    ".............###",  # 17
    ".............###",  # 18
    "............#.##",  # 19 hind legs
    "...........##.##",  # 20
    "...........#..##",  # 21
    "..............##",  # 22 the tail starts here
]
# Mouth open for fire: the jaws part at the front.
BODY_FIRE_L = list(BODY_L)
BODY_FIRE_L[0] = "..............#."
BODY_FIRE_L[1] = "..............#x"
BODY_FIRE_L[2] = "..............##"

BODY_H = len(BODY_L)
TAIL_TOP = 22          # body row where the tail joins
TAIL_H = 22            # tail rows, from TAIL_TOP

def body(fire=False):
    return mirror_rows(BODY_FIRE_L if fire else BODY_L)

# ----------------------------------------------------------------- the tail

TAIL_PHASES = 8

def tail(phase):
    """The tail as a run of discs along a swaying curve, ending in a spade."""
    g = grid(TAIL_H)
    L = TAIL_H - 5
    a = 2 * math.pi * phase / TAIL_PHASES
    pts = []
    for i in range(0, 4 * L + 1):
        s = i / 4                                  # 0 at the body, L at the spade
        u = s / L
        x = CX + 3.0 * u ** 1.4 * math.sin(a - 2.6 * u)
        r = 1.45 - 0.9 * u
        pts.append((x, s + 0.5, r))
    for y in range(TAIL_H):
        for x in range(W):
            for px_, py, r in pts:
                if (x + 0.5 - px_) ** 2 + (y + 0.5 - py) ** 2 <= r * r:
                    g[y][x] = 1
                    break
    # the spade, pointing back along the tail's last direction
    (xa, ya, _), (xb, yb, _) = pts[-6], pts[-1]
    dx, dy = xb - xa, yb - ya
    n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
    tip = (xb + dx * 4.6, yb + dy * 4.6)
    wl = (xb + dx * 1.3 - dy * 2.9, yb + dy * 1.3 + dx * 2.9)
    wr = (xb + dx * 1.3 + dy * 2.9, yb + dy * 1.3 - dx * 2.9)
    notch = (xb + dx * 0.4, yb + dy * 0.4)
    fill_poly(g, [notch, wl, tip, wr])
    return g

# ----------------------------------------------------------------- the wings

WING_TOP = 2           # body row of the first wing row
WING_H = 24

# The right wing, in body rows and canvas columns (the left wing is its mirror image).
# A bat's wing: the arm runs from the shoulder forward and out to the wrist, which has a
# claw, and three fingers fan back from the wrist. The bones are lit; the membrane between
# them is a 50% dither, so it reads as thin skin, and sags into scallops between the
# finger tips. Each flap phase gives the outward reach (1 = level; less = raised or
# lowered, so foreshortened from above), a forward sweep in rows at the tip, and how far
# the fingers are folded in.
#   phase:    0 level (also the glide)   1-2 downstroke   3-4 upstroke, folding   5 opening
FLAP = [
    dict(reach=1.00, sweep=0.0, fold=0.00),
    dict(reach=0.88, sweep=1.0, fold=0.00),
    dict(reach=0.66, sweep=1.8, fold=0.10),
    dict(reach=0.50, sweep=0.6, fold=0.40),
    dict(reach=0.40, sweep=-0.8, fold=0.60),
    dict(reach=0.72, sweep=-0.6, fold=0.25),
]
ROOT_X = 18.5          # where the wing meets the body (under the body's edge)
SS = 4                 # supersampling for the membrane outline

def wing_points(p):
    def at(dx, y):     # dx: columns out from the root at full reach; y: body row
        return (ROOT_X + dx * p["reach"], y - p["sweep"] * dx / 13.0 - WING_TOP)
    f = p["fold"]
    wrist = at(8.0, 7.6 + 1.5 * f)
    claw = at(8.6, 6.0 + 1.5 * f)
    tips = [at(13.0, 12.6 - 2.0 * f), at(11.6, 18.6 - 4.5 * f), at(7.2, 22.0 - 6.0 * f)]
    shoulder, hip = at(0, 11.0), at(0, 20.0)
    return shoulder, wrist, claw, tips, hip

def stroke(g, a, b, r, v=1):
    """a thick line: every pixel whose centre is within r of the segment a-b"""
    (ax, ay), (bx, by) = a, b
    L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1e-9
    for y in range(len(g)):
        for x in range(16, W):
            cx, cy = x + 0.5, y + 0.5
            t = max(0, min(1, ((cx - ax) * (bx - ax) + (cy - ay) * (by - ay)) / L2))
            if (cx - ax - t * (bx - ax)) ** 2 + (cy - ay - t * (by - ay)) ** 2 <= r * r:
                g[y][x] = v

def wing(phase):
    shoulder, wrist, claw, tips, hip = wing_points(FLAP[phase])
    poly = [shoulder, wrist, tips[0]]
    prev = tips[0]
    for t in tips[1:] + [hip]:
        mx, my = (prev[0] + t[0]) / 2, (prev[1] + t[1]) / 2
        poly.append((mx + (wrist[0] - mx) * 0.30, my + (wrist[1] - my) * 0.30))  # scallop
        poly.append(t)
        prev = t
    g = grid(WING_H)
    for y in range(WING_H):
        for x in range(16, W):
            n = sum(inside(poly, x + (i + 0.5) / SS, y + (j + 0.5) / SS) for i in range(SS) for j in range(SS))
            if n * 2 >= SS * SS:
                g[y][x] = 1 if (x + y) & 1 else 2
    stroke(g, shoulder, wrist, 0.75)
    stroke(g, wrist, claw, 0.5)
    for t in tips:
        stroke(g, wrist, t, 0.5)
    for y in range(WING_H):        # the left wing: mirror image
        for x in range(16):
            g[y][x] = g[y][W - 1 - x]
    return g

# ----------------------------------------------------------------- the ground

GROUND_H = 768         # rows; the map loops, so its last row joins its first

def build_ground():
    """The land below, as one long picture that scrolls down the screen. Kept sparse and
    mostly outlines so it stays behind the dragon: sea, a coast, fields along a road, a
    village and a castle, a forest with a river through it, a lake, and back to the sea."""
    rnd = random.Random(64)
    g = [[0] * W for _ in range(GROUND_H)]
    def put(x, y, v=1):
        if 0 <= x < W:
            g[y % GROUND_H][x] = v
    def sprite(art, x0, y0):
        for j, r in enumerate(art.split("/")):
            for i, c in enumerate(r):
                if c == "#": put(x0 + i, y0 + j)
                elif c == "x": put(x0 + i, y0 + j, 0)
    def blank(x0, y0, w, h):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w): put(x, y, 0)
    def free(x0, y0, w, h):
        return all(not g[(y) % GROUND_H][x] for y in range(y0 - 1, y0 + h + 1) for x in range(max(0, x0 - 1), min(W, x0 + w + 1)))
    WAVE = ".##../#..##"        # a small wave crest, seen from above
    def sea(y0, y1, step=7):
        for y in range(y0, y1, step):
            off = rnd.randrange(8)
            for x in range(-off, W, 9 + rnd.randrange(3)):
                if rnd.random() < 0.75:
                    sprite(WAVE, x + rnd.randrange(3), y + rnd.randrange(3))
    def shore(y_of_x, land_below, y0, y1):
        """a coastline: a solid curve, foam dashes on the sea side"""
        for x in range(W):
            yc = y_of_x(x)
            put(x, yc); put(x, yc + 1)
            for y in range(y0, y1):
                if (y < yc) == land_below and abs(y - yc) <= 1:
                    pass
            fy = yc - 3 if land_below else yc + 3
            if (x + yc) % 3 == 0: put(x, fy)
    def grass(y0, y1, density=0.025):
        for y in range(y0, y1):
            for x in range(W):
                if rnd.random() < density: put(x, y)
    def field(x0, y0, w, h, kind):
        blank(x0, y0, w, h)
        for x in range(x0, x0 + w):     # hedges: dotted outline
            if x % 2 == 0: put(x, y0); put(x, y0 + h - 1)
        for y in range(y0, y0 + h):
            if y % 2 == 0: put(x0, y); put(x0 + w - 1, y)
        for y in range(y0 + 2, y0 + h - 2):
            for x in range(x0 + 2, x0 + w - 2):
                if kind == 0 and y % 3 == 0: put(x, y)                 # crop rows
                elif kind == 1 and x % 3 == 0 and y % 2 == 0: put(x, y)  # vines
                elif kind == 2 and (x + 2 * y) % 7 == 0: put(x, y)      # scattered
    def road(x_of_y, y0, y1):
        for y in range(y0, y1):
            x = x_of_y(y)
            put(x, y)
            if y % 2: put(x + 1, y)
            blank(x - 1, y, 1, 1); blank(x + 2, y, 1, 1)
    TREE = ".##./#..#/#..#/.##."
    BUSH = ".#./#.#/.#."
    def forest(y0, y1, avoid=lambda x, y: False, n=60):
        for _ in range(n * 4):
            x, y = rnd.randrange(-1, W - 2), rnd.randrange(y0, y1 - 4)
            art, w = (TREE, 4) if rnd.random() < 0.7 else (BUSH, 3)
            if free(x, y, w, w) and not any(avoid(x + i, y + j) for i in range(w) for j in range(w)):
                sprite(art, x, y)
    HOUSE = "###/#x#/###"
    def castle(x0, y0):
        s = 16
        blank(x0 - 2, y0 - 2, s + 4, s + 4)
        for i in range(s):           # walls, with crenellations outside
            for (x, y) in ((x0 + i, y0), (x0 + i, y0 + s - 1), (x0, y0 + i), (x0 + s - 1, y0 + i)):
                put(x, y)
            if i % 2 == 0:
                put(x0 + i, y0 - 1); put(x0 + i, y0 + s); put(x0 - 1, y0 + i); put(x0 + s, y0 + i)
        for (tx, ty) in ((x0 - 1, y0 - 1), (x0 + s - 3, y0 - 1), (x0 - 1, y0 + s - 3), (x0 + s - 3, y0 + s - 3)):
            sprite(".##./####/####/.##.", tx, ty)    # corner towers
        sprite("######/#xxxx#/#x##x#/#x##x#/#xxxx#/######", x0 + 5, y0 + 5)   # the keep
        put(x0 + 7, y0 + 3); put(x0 + 8, y0 + 3); put(x0 + 8, y0 + 4)     # its flag
        blank(x0 + 6, y0 + s - 1, 4, 2)            # the gate
    # A 0-150: open sea, with a small island
    sea(0, 150)
    blank(17, 62, 12, 10)
    sprite("..####../.#....#./#..##..#/#.#..#.#/.#....#./..####..", 19, 63)
    # B 150-200: the coast, sea above, a beach and grass below
    yc = lambda x: 170 + int(round(5 * math.sin(x / 5.0) + x * 0.4))
    blank(0, 150, W, 50)
    sea(150, 170, 7)
    for x in range(W):
        for y in range(yc(x) - 2, 200): put(x, y, 0)
    shore(yc, True, 150, 200)
    for x in range(W):                          # sand: fine dots just inland
        for y in range(yc(x) + 3, yc(x) + 7):
            if (x * 3 + y * 5) % 11 == 0: put(x, y)
    grass(185, 200, 0.02)
    # C 200-330: fields either side of a road
    rx = lambda y: 15 + int(round(3 * math.sin(y / 23.0)))
    grass(200, 330, 0.015)
    field(1, 204, 12, 20, 0); field(19, 202, 12, 14, 1); field(19, 218, 12, 22, 0)
    field(0, 228, 13, 16, 2); field(2, 248, 11, 24, 1); field(19, 244, 13, 18, 2)
    field(18, 266, 12, 22, 0); field(1, 276, 12, 14, 0); field(2, 294, 11, 20, 2); field(19, 292, 12, 26, 1)
    road(rx, 200, 330)
    # D 330-450: a village on the road, and a castle
    grass(330, 450, 0.015)
    road(rx, 330, 360)
    for (hx, hy) in ((9, 334), (19, 336), (10, 341), (20, 343), (8, 348), (19, 351), (11, 355)):
        sprite(HOUSE, hx, hy)
    road(lambda y: 15, 360, 386)
    castle(8, 388)
    forest(410, 450, n=14)
    # E 450-580: forest with a river winding through
    rc = lambda y: 16 + 9 * math.sin((y - 450) / 26.0)
    river = lambda x, y: abs(x + 0.5 - rc(y)) < 5
    forest(450, 580, avoid=river, n=70)
    for y in range(450, 580):
        c = rc(y)
        put(int(round(c - 4)), y); put(int(round(c + 4)), y)
        for x in range(int(round(c - 3)), int(round(c + 4))): put(x, y, 0)
        if y % 5 == 0: put(int(round(c - 1 + (y // 5) % 3)), y)   # current
    # F 580-700: two lakes among the trees, with ragged shores
    def lake_at(cx, cy, rx, ry, seed):
        lr = random.Random(seed)
        bumps = [(lr.uniform(0.6, 1.4), lr.uniform(0, 6.3), lr.uniform(0.04, 0.10)) for _ in range(3)]
        def f(x, y):
            ang = math.atan2((y - cy) / ry, (x - cx) / rx)
            k = 1 + sum(b * a * math.sin(n * ang + ph) for (n, ph, a), b in zip([(2, p, a) for a, p, _ in bumps], [1, 1, 1]))
            return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < k
        return f
    lakes = [lake_at(13.5, 612, 11, 13, 7), lake_at(19, 664, 13, 17, 8)]
    in_lake = lambda x, y: any(l(x + 0.5, y + 0.5) for l in lakes)
    near_lake = lambda x, y: any(in_lake(x + dx, y + dy) for dx in (-2, 0, 2) for dy in (-2, 0, 2))
    forest(580, 700, avoid=near_lake, n=55)
    for y in range(590, 690):
        for x in range(W):
            if in_lake(x, y):
                put(x, y, 0)
                if not all(in_lake(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): put(x, y)
    for (wx, wy) in ((9, 607), (14, 616), (13, 655), (20, 662), (16, 672)):
        sprite(WAVE, wx, wy)
    # G 700-768: grass to sea (land above, sea below), joining A at the top again
    yc2 = lambda x: 730 + int(round(4 * math.sin(x / 4.0 + 1) - x * 0.3))
    grass(700, 730, 0.02)
    forest(700, 718, n=10)
    sea(736, 768, 7)
    for x in range(W):
        for y in range(yc2(x) - 1, yc2(x) + 4): put(x, y, 0)
    shore(yc2, False, 700, 768)
    return g

# ----------------------------------------------------------------- clouds

def cloud(w, h, blobs, seed):
    """A cumulus from above: a solid rim, a sparse speckle inside, darker gaps between puffs."""
    rnd = random.Random(seed)
    g = [[0] * w for _ in range(h)]
    inside_ = lambda x, y: any((x - bx) ** 2 + (y - by) ** 2 <= r * r for bx, by, r in blobs)
    for y in range(h):
        for x in range(w):
            if inside_(x + 0.5, y + 0.5):
                edge = not all(inside_(x + 0.5 + dx, y + 0.5 + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                g[y][x] = 1 if edge or ((x + y * 2) % 5 == 0 and (x * 7 + y) % 3 != 0) else 2
    return g

CLOUDS = [
    cloud(20, 11, [(5, 6, 4), (10, 4.5, 4.5), (15, 6, 4), (10, 7.5, 3.5)], 1),
    cloud(14, 9, [(4, 5, 3.5), (9, 4.5, 4), (7, 6, 3)], 2),
    cloud(26, 13, [(5, 7, 4), (11, 5, 5), (17, 5.5, 4.5), (21, 8, 3.5), (13, 9, 4)], 3),
]

# ----------------------------------------------------------------- output

def row_masks(g, w=W):
    sil = [sum(1 << x for x in range(w) if g[y][x]) for y in range(len(g))]
    ink = [sum(1 << x for x in range(w) if g[y][x] == 1) for y in range(len(g))]
    return sil, ink

def c_rows(rows):
    return "{" + ", ".join("0x%08x" % r for r in rows) + "}"

def write_header(path):
    o = []
    o.append("// Generated by firmware/dragon_screen/flight_art.py. Do not edit by hand.")
    o.append("// The dragon flying, seen from above: parts, ground and clouds for flight_scene.c.")
    o.append("// Row y, bit x = pixel (x, y) on the 32 px wide upright canvas.\n#pragma once\n#include <stdint.h>\n")
    o.append("#define FL_BODY_H %d\n#define FL_TAIL_TOP %d\n#define FL_TAIL_H %d\n#define FL_WING_TOP %d\n#define FL_WING_H %d" % (BODY_H, TAIL_TOP, TAIL_H, WING_TOP, WING_H))
    o.append("#define FL_FLAPS %d\n#define FL_TAIL_PHASES %d\n#define FL_GROUND_H %d\n#define FL_CLOUDS %d\n" % (len(FLAP), TAIL_PHASES, GROUND_H, len(CLOUDS)))
    o.append("// [part][0 sil, 1 ink, 2 halo][row]; body 0 mouth shut, 1 open")
    def block(name, grids, h):
        o.append("static const uint32_t %s[%d][3][%d] = {" % (name, len(grids), h))
        for g in grids:
            sil, ink, halo = masks(g)
            o.append("    {%s,\n     %s,\n     %s}," % (c_rows(sil), c_rows(ink), c_rows(halo)))
        o.append("};\n")
    block("fl_body", [body(False), body(True)], BODY_H)
    block("fl_wing", [wing(i) for i in range(len(FLAP))], WING_H)
    block("fl_tail", [tail(i) for i in range(TAIL_PHASES)], TAIL_H)
    gr = build_ground()
    o.append("static const uint32_t fl_ground[%d] = {" % GROUND_H)
    rows = [sum(1 << x for x in range(W) if gr[y][x]) for y in range(GROUND_H)]
    for i in range(0, GROUND_H, 8):
        o.append("    " + ", ".join("0x%08x" % r for r in rows[i:i + 8]) + ",")
    o.append("};\n")
    o.append("// clouds: width, height, then sil and ink rows (bit x = column x of the cloud)")
    o.append("typedef struct { uint8_t w, h; uint32_t sil[16], ink[16]; } fl_cloud_t;")
    o.append("static const fl_cloud_t fl_clouds[%d] = {" % len(CLOUDS))
    for c in CLOUDS:
        sil, ink = row_masks(c, len(c[0]))
        o.append("    {%d, %d, %s, %s}," % (len(c[0]), len(c), c_rows(sil), c_rows(ink)))
    o.append("};")
    open(path, "w").write("\n".join(o) + "\n")
    return gr

def to_img(g, scale=8, bg=40):
    h, w = len(g), len(g[0])
    im = Image.new("L", (w, h), bg)
    for y in range(h):
        for x in range(w):
            if g[y][x] == 1: im.putpixel((x, y), 255)
            elif g[y][x] == 2: im.putpixel((x, y), 0)
    return im.resize((w * scale, h * scale), Image.NEAREST)

def compose(wing_phase, tail_phase, fire=False):
    """The whole dragon as one grid, layered the way flight_scene.c draws it."""
    h = max(WING_TOP + WING_H, TAIL_TOP + TAIL_H)
    out = grid(h)
    for part, top in ((tail(tail_phase), TAIL_TOP), (wing(wing_phase), WING_TOP), (body(fire), 0)):
        for y, row in enumerate(part):
            for x, v in enumerate(row):
                if v: out[top + y][x] = v
    return out

if __name__ == "__main__":
    gr = write_header(os.path.join(HERE, "..", "qmk", "lazydragon64", "flight_art.h"))
    tiles = [compose(w, 0) for w in range(len(FLAP))] + [compose(0, t) for t in range(0, TAIL_PHASES, 2)] + [compose(0, 0, True)]
    ims = [to_img(t, 6) for t in tiles]
    sheet = Image.new("L", (sum(i.width + 12 for i in ims), max(i.height for i in ims) + 12), 90)
    x = 6
    for im in ims:
        sheet.paste(im, (x, 6)); x += im.width + 12
    sheet.save(os.path.join(HERE, "flight_parts.png"))
    # the ground in six strips side by side, and the clouds
    strips = [to_img(gr[i:i + 128], 3, 0) for i in range(0, GROUND_H, 128)] + [to_img(c, 3) for c in CLOUDS]
    gs = Image.new("L", (sum(i.width + 9 for i in strips), 128 * 3), 90)
    x = 0
    for im in strips:
        gs.paste(im, (x, 0)); x += im.width + 9
    gs.save(os.path.join(HERE, "flight_ground.png"))
    print("wrote flight_art.h")
