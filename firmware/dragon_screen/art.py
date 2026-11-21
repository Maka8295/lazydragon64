"""Lazy Dragon OLED pixel art: the sleeping dragon on its hoard from the case bottom,
redrawn as a 32 x 32 scene (x right, y down) in layers. Each layer is a list of
(x, y, on) edits applied in order, so a layer can also cut dark detail into the
ones under it. make_art.py turns every combination into firmware data."""

def rows(spec, x0=0, y0=0):
    """spec: {y: [(x_from, x_to), ...]} -> lit pixels"""
    return [(x, y + y0, 1) for y, spans in spec.items() for a, b in spans for x in range(a + x0, b + x0 + 1)]
def px(points, on=1):
    return [(x, y, on) for x, y in points]
def line(a, b, on=1):
    (x0, y0), (x1, y1) = a, b; out = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1; e = dx + dy
    while True:
        out.append((x0, y0, on))
        if (x0, y0) == (x1, y1): return out
        e2 = 2 * e
        if e2 >= dy: e += dy; x0 += sx
        if e2 <= dx: e += dx; y0 += sy
def poly(pts, on=1):
    out = []
    for a, b in zip(pts, pts[1:]): out += line(a, b, on)
    return out
def sprite(art, x0, y0):
    """'#' lit, 'x' dark, '.' leaves the pixel alone"""
    out = []
    for j, r in enumerate(art.split("/")):
        for i, c in enumerate(r):
            if c == "#": out.append((x0 + i, y0 + j, 1))
            elif c == "x": out.append((x0 + i, y0 + j, 0))
    return out
COIN_A = "x##x/#xx#/x##x"            # 4 x 3
COIN_B = "x###x/#xxx#/x###x"         # 5 x 3
COIN_C = "x#x/#x#/x#x"               # 3 x 3
CROWN = "#x#x#/#####/#xxx#/#####"
SWORD = "x#x/x#x/#####/x#x/x#x/x#x/x#x/x#x/xxx"
GEM = "x###x/#x#x#/x#x#x/xx#xx"
# the hoard: hand-placed, mounded under the dragon, densest in the middle
HOARD = (sprite(CROWN, 0, 21) + sprite(COIN_B, 6, 21) + sprite(COIN_A, 12, 22) + sprite(SWORD, 17, 20) + sprite(COIN_C, 23, 21) +
         sprite(COIN_A, 1, 26) + sprite(GEM, 6, 25) + sprite(COIN_B, 11, 26) + sprite(COIN_C, 22, 26) + sprite(COIN_A, 26, 27) +
         sprite(COIN_B, 2, 29) + sprite(COIN_C, 8, 29) + sprite(COIN_A, 13, 30) + sprite(COIN_B, 19, 29) + sprite(COIN_C, 25, 30) + sprite(COIN_A, 28, 30))
HORNS = rows({8: [(6, 7), (10, 11), (13, 13)], 7: [(6, 7), (10, 11), (14, 14)], 6: [(7, 8), (11, 12)], 5: [(7, 8), (11, 12)],
              4: [(8, 8), (12, 12)], 3: [(8, 8), (12, 13)], 2: [(9, 9), (13, 13)], 1: [(9, 9), (13, 13)], 0: [(14, 14)]})
HEAD = rows({9: [(5, 12)], 10: [(4, 13)], 11: [(3, 14)], 12: [(2, 14)], 13: [(2, 14)], 14: [(2, 14)], 15: [(2, 14)], 16: [(3, 13)]})
FRILL = px([(15, 11), (16, 10), (15, 13), (16, 13), (17, 12)])
BODY = rows({12: [(15, 24)], 13: [(15, 26)], 14: [(15, 27)], 15: [(14, 28)], 16: [(14, 29)], 17: [(13, 29)], 18: [(12, 30)], 19: [(11, 30)]})
SPIKES = px([(26, 12), (28, 13), (29, 14), (30, 15)])
TAIL = rows({20: [(29, 31)], 21: [(29, 31)], 22: [(28, 31)], 23: [(27, 30)], 24: [(25, 29)], 25: [(24, 26)]})
TAIL_FLICK = [(x, y, 0) for x in range(23, 32) for y in range(22, 27)] + \
    rows({20: [(29, 31)], 21: [(29, 31)], 22: [(28, 31)], 23: [(28, 30)], 24: [(27, 29)]}) + px([(26, 23), (25, 22), (27, 24)])
LEGS = px([(10, 20), (12, 20), (14, 20), (24, 20), (26, 20), (28, 20)]) + px([(11, 20), (13, 20), (25, 20), (27, 20)], 0) + \
    px([(23, 18), (23, 19), (24, 17), (14, 18), (13, 19)], 0)
FACE = px([(3, 13), (3, 15), (4, 15), (5, 15), (6, 15), (14, 13), (14, 14)], 0)
EYE = {
    "closed": px([(6, 12), (7, 13), (8, 13), (9, 12), (10, 11)], 0),
    "half":   px([(6, 12), (7, 12), (8, 12), (9, 12), (7, 13), (8, 13)], 0),
    "open":   px([(7, 12), (8, 12), (7, 13), (8, 13), (9, 13), (9, 12)], 0) + px([(8, 12)]),
}
def wing_fold():
    clear = [(x, y, 0) for x in range(16, 28) for y in range(0, 12)]
    lit = rows({1: [(18, 18)], 2: [(18, 19)], 3: [(17, 20)], 4: [(17, 21)], 5: [(17, 22), (26, 26)], 6: [(17, 23), (25, 26)],
                7: [(16, 26)], 8: [(16, 26)], 9: [(16, 25)], 10: [(16, 24)], 11: [(16, 23)]})
    ribs = line((18, 4), (20, 10), 0) + line((19, 4), (24, 7), 0) + px([(25, 9), (24, 10)], 0)
    return clear + lit + ribs + [(x, 12, 0) for x in range(17, 24)]
def wing_up():
    clear = [(x, y, 0) for x in range(15, 29) for y in range(0, 12)]
    lit = rows({0: [(16, 17)], 1: [(16, 19)], 2: [(16, 21), (27, 27)], 3: [(16, 22), (26, 27)], 4: [(16, 27)], 5: [(16, 27)],
                6: [(16, 26)], 7: [(16, 25)], 8: [(16, 24)], 9: [(16, 23)], 10: [(16, 22)], 11: [(16, 21)]})
    ribs = line((17, 2), (19, 10), 0) + line((18, 1), (25, 5), 0) + px([(26, 6), (24, 8)], 0)
    return clear + lit + ribs + [(x, 12, 0) for x in range(17, 22)]
WING = {"fold": wing_fold(), "up": wing_up()}
MOUTH_OPEN = px([(2, 14), (2, 15), (3, 15), (4, 15), (5, 15), (6, 15), (7, 15), (3, 16), (4, 16), (5, 16)], 0)
FIRE = [
    [(x, y, 0) for x in range(0, 6) for y in range(14, 25)] +
    rows({14: [(0, 0)], 15: [(0, 1)], 16: [(0, 2)], 17: [(1, 3)], 18: [(0, 0), (2, 3)], 19: [(0, 1), (3, 3)], 20: [(1, 2)], 21: [(2, 2)], 22: [(1, 1)]}),
    [(x, y, 0) for x in range(0, 6) for y in range(14, 25)] +
    rows({15: [(0, 0)], 16: [(0, 1)], 17: [(0, 3)], 18: [(1, 2)], 19: [(0, 0), (2, 3)], 20: [(0, 2)], 21: [(1, 1), (3, 3)], 22: [(2, 2)], 23: [(1, 1)]}),
]
def scene(eye="closed", wing="fold", tail="rest", fire=None):
    g = [[0] * 32 for _ in range(32)]
    def apply(edits):
        for x, y, on in edits:
            x, y = int(x), int(y)
            if 0 <= x < 32 and 0 <= y < 32: g[y][x] = on
    for layer in (HOARD, TAIL if tail == "rest" else TAIL_FLICK, BODY, SPIKES, WING[wing], HORNS, HEAD, FRILL, LEGS, FACE, EYE[eye]):
        apply(layer)
    if fire is not None:
        apply(MOUTH_OPEN); apply(FIRE[fire])
    return g
