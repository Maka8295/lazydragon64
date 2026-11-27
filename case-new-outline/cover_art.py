# 2D art for the Lazy Dragon top covers (build_cover.py): the window tile, the dragon and
# its fit on the lid, as shapely geometry in mm. Needs shapely and numpy (FreeCAD's Python
# has both).
import json, os, math
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
WINDOW_JSON = os.path.join(HERE, "window_art.json")    # ~/Downloads/window.png, traced
DRAGON_JSON = os.path.join(HERE, "dragon_art.json")    # the same trace the case underside used

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]

def even_odd(loops):
    """Closed loops -> region, filled by the even-odd rule (holes, islands in holes, ...)."""
    P = [Polygon(l).buffer(0) for l in loops if len(l) >= 3]
    P = [p for p in P if p.area > 1e-9]
    if not P: return Polygon()
    pts = [p.representative_point() for p in P]
    depth = [sum(1 for j, q in enumerate(P) if j != i and q.area > P[i].area and q.contains(pts[i]))
             for i in range(len(P))]
    g = Polygon()
    for d in range(max(depth) + 1):
        U = unary_union([P[i] for i in range(len(P)) if depth[i] == d])
        g = g.union(U) if d % 2 == 0 else g.difference(U)
    return g.buffer(0)

def drop_small(g, amin):
    return unary_union([p for p in polys(g) if p.area >= amin])

# ---------------------------------------------------------------- window
def window(height_mm, stroke_min=0.38, gap_min=0.28, hole_min=0.04):
    """The tracery window, height_mm tall, with the middle of its sill at (0, 0), x right, y up.
    At the cover's size the drawing's thinnest strokes would be ~0.16 mm, too thin for a
    0.4 mm nozzle. Every stroke is grown so the thinnest reach stroke_min (Arachne prints
    walls down to ~0.34 mm), then any opening narrower than gap_min, or smaller than
    hole_min mm2, is closed. The frame, the four lancets, the rosette and the two side
    lights stay; the finest tracery in the arch closes up."""
    d = json.load(open(WINDOW_JSON))
    k = height_mm / d["height_px"]
    g = even_odd([[(x * k, y * k) for x, y in lp] for lp in d["loops"]])
    g = affinity.translate(g, -d["width_px"] * k / 2, 0)
    g = g.buffer(max(0.0, (stroke_min - d["thinnest_stroke_px"] * k) / 2), join_style=1)
    env = unary_union([Polygon(p.exterior) for p in polys(g)])
    bg = env.difference(g).buffer(-gap_min / 2, join_style=1).buffer(gap_min / 2, join_style=1)
    bg = drop_small(bg.intersection(env), hole_min)
    g = env.difference(bg).buffer(0).simplify(0.01)
    assert len(polys(g)) == 1, "window came out in %d pieces" % len(polys(g))
    return polys(g)[0], d["width_px"] * k

# ---------------------------------------------------------------- dragon
def dragon_raw():
    """The traced drawing in mm at its traced size (112.5 mm wide), centred, v up."""
    return even_odd(json.load(open(DRAGON_JSON))["loops"])

def fit_dragon(outline, raw, margin=3.0):
    """Largest scale at which the drawing (its own outline, not its box) fits inside the lid
    outline inset by margin, and the centre of the room it has at that scale."""
    hull = raw.buffer(0.3).simplify(0.1)
    room = prep(outline.buffer(-margin, join_style=1))
    x0, y0, x1, y1 = outline.bounds
    lo, hi, best = 0.8, 2.0, None
    for _ in range(18):                    # bisect on scale, grid search on position
        s = (lo + hi) / 2; h = affinity.scale(hull, s, s, origin=(0, 0)); ok = None
        bx0, by0, bx1, by1 = h.bounds
        for cx in np.arange(x0 - bx0, x1 - bx1 + 1e-9, 0.5):
            for cy in np.arange(y0 - by0, y1 - by1 + 1e-9, 0.5):
                if room.contains(affinity.translate(h, cx, cy)): ok = (cx, cy); break
            if ok: break
        if ok: lo, best = s, (s, ok)
        else: hi = s
    s, (cx, cy) = best
    h = affinity.scale(hull, s, s, origin=(0, 0))
    xs = [c for c in np.arange(cx - 40, cx + 40, 0.25) if room.contains(affinity.translate(h, c, cy))]
    cx = (min(xs) + max(xs)) / 2
    ys = [c for c in np.arange(cy - 40, cy + 40, 0.25) if room.contains(affinity.translate(h, cx, c))]
    cy = (min(ys) + max(ys)) / 2
    return s, cx, cy

def dragon_simplified(raw, s, speck=(0.65, 5.0), pile=(25.0, -1.7), hole_fill=0.5, land_min=0.45, piece_min=0.4):
    """The drawing at scale s (still centred on 0), with the hoard simplified for printing.
    The lid prints upside down, so the engraving is on the first layer: every bit of
    un-engraved land is a separate island there, and thin ones print badly.
    - Loose marks in the coin pile (separate ink pieces of speck mm2 at the final size,
      below v = pile[1] and left of u = pile[0] in the traced drawing, so not the chest's
      lock or the crown's dots) are dropped: each coin is a plain ring.
    - Enclosed land under hole_fill mm2 (the specks between touching coins) is engraved.
    - Any enclosed land narrower than land_min is engraved, and leftover bits under
      piece_min mm2 go with it. The dragon, the lettering and the open background are
      untouched."""
    keep = []
    for p in polys(raw):
        c = p.centroid; a = p.area * s * s
        if not p.interiors and speck[0] <= a < speck[1] and c.y < pile[1] and c.x < pile[0]:
            continue
        keep.append(p)
    out = []
    for p in polys(affinity.scale(unary_union(keep), s, s, origin=(0, 0))):
        holes = []
        for h in p.interiors:
            hp = Polygon(h)
            if hp.area < hole_fill: continue
            op = hp.buffer(-land_min / 2, join_style=1).buffer(land_min / 2, join_style=1).intersection(hp)
            holes += [q.exterior for q in polys(op) if q.area >= piece_min]
        out.append(Polygon(p.exterior, holes))
    return unary_union(out).buffer(0).simplify(0.01)

# ---------------------------------------------------------------- mushroom house
MUSHROOM_JSON = os.path.join(HERE, "mushroom_art.json")   # mushroom_house.png, traced

def mushroom_raw():
    """2026-11-28: the mushroom house with two sleeping sheep (mushroom_house.png, traced by
    trace_art.py at 100 mm wide with no dilation), centred, v up. Ink is the drawing's black:
    its lines, the sheep's faces, ears and legs."""
    return even_odd(json.load(open(MUSHROOM_JSON))["loops"])

def fit_corner(outline, raw, width, margin=6.0, toward=(1, -1)):
    """2026-11-28: the scale that makes the drawing `width` mm wide, and the centre that
    tucks it as far into one corner of the lid as it goes while its ink (not its box) stays
    `margin` inside the edge. toward (+1, -1) is the right-hand, front corner: x right, y
    towards the back."""
    s = width / (raw.bounds[2] - raw.bounds[0])
    h = affinity.scale(raw, s, s, origin=(0, 0)).buffer(0.2).simplify(0.05)
    room = prep(outline.buffer(-margin, join_style=1))
    x0, y0, x1, y1 = outline.bounds; bx0, by0, bx1, by1 = h.bounds
    tx, ty = toward
    ok = lambda cx, cy: room.contains(affinity.translate(h, cx, cy))
    xs = np.arange(x1 - bx1, x0 - bx0, -1.0) if tx > 0 else np.arange(x0 - bx0, x1 - bx1, 1.0)
    ys = np.arange(y0 - by0, y1 - by1, 1.0) if ty < 0 else np.arange(y1 - by1, y0 - by0, -1.0)
    best = None                          # (how far into the corner, cx, cy)
    for cx in xs:                        # coarse, 1 mm steps: for each x from the corner side
        for cy in ys:                    # inwards, the first y from the corner side that fits
            if ok(cx, cy):
                v = tx * cx + ty * cy
                if best is None or v > best[0]: best = (v, cx, cy)
                break
        if best and tx * cx < best[0] - ty * ys[0] - 30: break   # 30 mm past the best: done
    assert best, "drawing doesn't fit at %.1f mm wide" % width
    _, cx, cy = best
    step = 0.25                          # fine: slide into the corner while it still fits
    for _ in range(2):
        while ok(cx + tx * step, cy): cx += tx * step
        while ok(cx, cy + ty * step): cy += ty * step
    return s, cx, cy

def relief_printable(raw, s, stroke_min=0.45, gap_min=0.5, widen=0.12, speck=0.05):
    """The drawing at scale s (still centred on 0), made printable as a raised relief on a
    top surface, where the ink stands up and the paper is the lid:
    - specks of ink under speck mm2 are dropped;
    - any part of a stroke thinner than stroke_min (the tapered ends of the door planks,
      grass and leaves) is thickened, so it prints as a wall rather than vanishing;
    - any white narrower than gap_min that lies within the drawing (the sheep's closed eyes
      and the line under their chins, ~0.3 mm drawn) is widened by `widen` each side, so
      the groove survives instead of filling in."""
    g = drop_small(affinity.scale(raw, s, s, origin=(0, 0)).buffer(0), speck)
    r = stroke_min / 2
    thin = g.difference(g.buffer(-r, join_style=1).buffer(r, join_style=1))
    g = g.union(drop_small(thin, 0.03).buffer(0.1, join_style=1)).buffer(0)   # not the pixel steps along every edge
    env = g.buffer(2.0, join_style=1).buffer(-2.0, join_style=1)      # the drawing's own outline
    white = env.difference(g)
    r = gap_min / 2
    narrow = white.difference(white.buffer(-r, join_style=1).buffer(r, join_style=1))
    narrow = drop_small(narrow, 0.15)      # grooves, not the sharp white corners where lines meet
    g = g.difference(narrow.buffer(widen, join_style=1)).buffer(0)
    return drop_small(g, speck).simplify(0.01)

def _ellipse_like(h, shrink):
    """An ellipse on h's minimum rotated rectangle with h's area (x shrink), and its minor axis."""
    r = h.minimum_rotated_rectangle; c = list(r.exterior.coords)
    a, b = math.dist(c[0], c[1]), math.dist(c[1], c[2])
    ang = math.degrees(math.atan2(c[1][1] - c[0][1], c[1][0] - c[0][0]))
    k = math.sqrt(h.area / (math.pi / 4 * a * b)) * shrink
    e = affinity.rotate(affinity.scale(Point(0, 0).buffer(0.5, 64), a * k, b * k), ang)
    cc = r.centroid
    return affinity.translate(e, cc.x, cc.y), min(a, b) * k

def coins_redrawn(g, s, pile=(-17.0, -2.0), keep=((-1, -9, 5, -1), (6, -9, 11, -5), (23, -12, 60, 0)),
                  fill_max=1.2, coin_max=9.0, rnd=(0.75, 1.1), minor_min=1.1, shrink=0.97):
    """2026-11-26: every coin in the pile redrawn as a clean oval, so the hoard prints as
    plain round islands in an engraved bed instead of ragged ones. g is dragon_simplified()
    at scale s. Only enclosed land whose centre lies in the pile band (pile, in the traced
    drawing's v) and outside the keep boxes (u0, v0, u1, v1: the gem, the sword's hilt and
    the chest) is touched:
    - under fill_max mm2, or too thin for an oval of minor_min: engraved (the coins
      crossed by a bar become solid engraved dots)
    - roughly round (area / its rectangle's ellipse within rnd) and under coin_max mm2: the
      coin's face becomes an ellipse of the same area x shrink on the same rectangle,
      kept within 0.1 mm of the old face so the rings stay even
    - anything else (the crown, goblet, partly hidden coins): left as it was.
    Returns the new drawing and (engraved, ovals, left) counts."""
    out = []; n = [0, 0, 0]
    for p in polys(g):
        holes = []
        for h in p.interiors:
            hp = Polygon(h); c = hp.centroid; u, v = c.x / s, c.y / s
            if not (pile[0] < v < pile[1]) or any(a <= u <= b and lo <= v <= hi for a, lo, b, hi in keep):
                holes.append(h); continue
            if hp.area < fill_max: n[0] += 1; continue
            q = list(hp.minimum_rotated_rectangle.exterior.coords)
            ro = hp.area / (math.pi / 4 * math.dist(q[0], q[1]) * math.dist(q[1], q[2]))
            if hp.area <= coin_max and rnd[0] <= ro <= rnd[1]:
                e, minor = _ellipse_like(hp, shrink)
                if minor < minor_min: n[0] += 1; continue
                holes.append(e.intersection(hp.buffer(0.1, join_style=1)).exterior); n[1] += 1
            else:
                holes.append(h); n[2] += 1
        out.append(Polygon(p.exterior, holes))
    return unary_union(out).buffer(0).simplify(0.01), n

# ---------------------------------------------------------------- window layout
def straight_runs(outline, min_len=3.0):
    """Straight stretches of the outline (collinear edges merged), as (a, t, length)."""
    c = list(outline.exterior.coords)[:-1]; runs = []
    for i in range(len(c)):
        a, b = np.array(c[i]), np.array(c[(i + 1) % len(c)]); L = float(np.hypot(*(b - a)))
        if L < 1e-6: continue
        t = (b - a) / L
        if runs and abs(runs[-1][1][0] * t[1] - runs[-1][1][1] * t[0]) < 1e-4 and runs[-1][1] @ t > 0:
            runs[-1][2] += L
        else:
            runs.append([a, t, L])
    if len(runs) > 1 and abs(runs[0][1][0] * runs[-1][1][1] - runs[0][1][1] * runs[-1][1][0]) < 1e-4 and runs[0][1] @ runs[-1][1] > 0:
        runs[0] = [runs[-1][0], runs[0][1], runs[0][2] + runs[-1][2]]; runs.pop()
    return [r for r in runs if r[2] >= min_len]

def window_layout(outline, w, gap=2.0, end_min=0.6):
    """Whole windows only, centred on each straight run with equal spacing: a run of length
    L gets n = round(L / (w + gap)) windows at L / n apart (the end gaps are half that).
    Rounded corners and the short jogs stay bare."""
    out = []
    for a, t, L in straight_runs(outline):
        n = int(round(L / (w + gap)))
        while n and L / n - w < 2 * end_min: n -= 1
        for i in range(n):
            out.append((a + t * (L * (i + 0.5) / n), t, L, n))
    return out

# ---------------------------------------------------------------- chamfer
def mitred_offset(P, d):
    """The counter-clockwise polygon P moved d inwards with mitred corners, one point per
    vertex (as in chamfer_top.py, which chamfers the cases this way). A segment too short to
    survive the move is dropped and its neighbours' lines meet instead, so both its ends
    land on the same point. Returns (points, number of segments dropped)."""
    n = len(P); lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = P[i], P[(i + 1) % n]
        L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        tx, ty = (x2 - x1) / L, (y2 - y1) / L
        lines.append((x1 - ty * d, y1 + tx * d, tx, ty))
    def meet(i, j, k):          # lines i and j; P[k] moved along line j if they are parallel
        ax, ay, atx, aty = lines[i]; bx, by, btx, bty = lines[j]
        den = atx * bty - aty * btx
        if abs(den) < 1e-9:
            u = (P[k][0] - bx) * btx + (P[k][1] - by) * bty
            return (bx + btx * u, by + bty * u)
        u = ((bx - ax) * bty - (by - ay) * btx) / den
        return (ax + atx * u, ay + aty * u)
    active = [True] * n
    for _ in range(n):
        pts = []
        for k in range(n):
            a = next((k - 1 - m) % n for m in range(n) if active[(k - 1 - m) % n])
            b = next((k + m) % n for m in range(n) if active[(k + m) % n])
            pts.append(meet(a, b, k))
        flipped = [i for i in range(n) if active[i] and
                   (pts[(i + 1) % n][0] - pts[i][0]) * lines[i][2] + (pts[(i + 1) % n][1] - pts[i][1]) * lines[i][3] < -1e-9]
        if not flipped: return pts, n - sum(active)
        active[flipped[0]] = False
    raise SystemExit("offset did not settle")
