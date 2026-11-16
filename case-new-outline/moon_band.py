# Moon-phase band ("Marika" cases), design B of ~/Downloads/image0(1).png:
#   dash  star  diamond  )  )  full  SUN  full  (  (  diamond  star  dash
# The motif is redrawn here as exact shapes (circles, crescents, superellipse stars,
# tapered dashes, a 24-ray sun) instead of being traced, since the source is a shaded
# render. Sizes and spacings were measured from the image in pixels (moon 51 px, sun
# rays to 63/67 px radius) and are kept in those units; MOON_K converts to mm.
#
# Shapes are lists of "parts": (add, [subtract...]) where each primitive is
# ("c", x, y, r) or ("p", [(x, y), ...]). An element is the union of its parts.
# Coordinates: u along the wall (arc length, mm), v up the wall (mm). build_case.py
# turns them into faces; preview() rasterises them.
#
# Layout: the clear zones (front text, USB notch) split the band into stretches. Each
# stretch holds a whole number of motifs. Element sizes never change; the spacing
# factor f (inside a motif), the join between motifs and the end margins absorb the
# length, chosen so no sun lands on a rounded corner. A long join gets a star, or a
# diamond-star-diamond group, so it doesn't read as a gap.
import math

MOON_K = 0.100            # mm per source pixel: sun 12.6 mm across the long rays, moons 5.1 mm

# ---- primitives (source pixels) ---------------------------------------------------
def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, hi = half(pts), half(list(reversed(pts)))
    return lo[:-1] + hi[:-1]

def _circle_pts(x, y, r, n=48):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

def _superellipse(a, b, p, n=120):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n; c, s = math.cos(t), math.sin(t)
        out.append((a * math.copysign(abs(c) ** (2 / p), c), b * math.copysign(abs(s) ** (2 / p), s)))
    return out

R_MOON = 25.5
# crescent = disc(R) minus disc(r2) offset by d away from the lit side, fitted to the
# image (bounding-box width and ink area): thin 38 px wide / 41 % of a disc, thick
# 39.5 px / 59 %. (offset d, inner radius r2)
CRESCENT = {"thin": (0.47 * R_MOON, 0.87 * R_MOON), "thick": (0.79 * R_MOON, 0.86 * R_MOON)}

def dash(direction):        # tapered dash, point towards `direction` (+1 = +u)
    head = _circle_pts(-direction * 8.5, 0, 5.5, 32)
    tip = _circle_pts(direction * 13.2, 0, 0.9, 12)
    return [(("p", _hull(head + tip)), [])]

def star():                 # four-point sparkle, 29 px
    return [(("p", _superellipse(14.5, 14.5, 0.8)), [])]

def diamond():              # small concave diamond, 20 x 15 px
    return [(("p", _superellipse(10.0, 7.5, 0.9)), [])]

def full():
    return [(("c", 0, 0, R_MOON), [])]

def crescent(kind, lit):    # lit = +1: bright limb towards +u, i.e. ")"
    d, r2 = CRESCENT[kind]
    return [(("c", 0, 0, R_MOON), [("c", -lit * d, 0, r2)])]

# sun: 12 long rays at 0, 30, ... deg (the four cardinal ones longer) and 12 short rays
# between them, standing on a thin ring; a crescent sits inside, opening towards +u.
# The crescent is 1 px smaller and the ring 0.5 px wider than measured, so the groove
# between them is 0.65 mm at MOON_K 0.1 (0.4 mm in the image) and prints.
SUN_RING = (34.5, 37.5)
SUN_LONG, SUN_LONG_CARD, SUN_SHORT = 63.0, 67.0, 52.0
SUN_LONG_W, SUN_SHORT_W = 10.0, 8.0     # base widths; short rays widened from ~6.5 to print
SUN_CRES = (27.0, -1.0, 0.30, 0.833)    # outer r, centre u, inner offset / r, inner r / r

def sun(open_dir=+1):
    parts = [(("c", 0, 0, SUN_RING[1]), [("c", 0, 0, SUN_RING[0])])]
    for i in range(24):
        a = math.radians(15 * i)
        if i % 2 == 0:
            tip = SUN_LONG_CARD if i % 6 == 0 else SUN_LONG; w = SUN_LONG_W
        else:
            tip = SUN_SHORT; w = SUN_SHORT_W
        r0 = SUN_RING[0] + 1.0
        ca, sa = math.cos(a), math.sin(a)
        q = [(r0, -w / 2), (tip, -0.5), (tip, 0.5), (r0, w / 2)]
        parts.append((("p", [(x * ca - y * sa, x * sa + y * ca) for x, y in q]), []))
    r, cu, off, rr = SUN_CRES
    parts.append((("c", open_dir * cu, 0, r), [("c", open_dir * (cu + off * r), 0, rr * r)]))
    return parts

# the motif, element centres in source pixels from the sun (symmetric, as measured,
# except the diamond and dash sit 1.5 px further from the star so their gaps are 0.7 mm)
DASH_U, STAR_U = 352.8, 317.3
HALF = [("full", 107.5), ("thick", 172.5), ("thin", 234.3), ("diamond", 285.0), ("star", STAR_U), ("dash", DASH_U)]
HALF_W = {"full": R_MOON, "thick": R_MOON, "thin": R_MOON, "diamond": 10.0, "star": 14.5, "dash": 14.1}
MOTIF_SPAN = 2 * DASH_U     # first to last element centre
JOIN_MIN = 40.0             # dash centre to dash centre between neighbouring motifs (tips 12 px apart)

def element(kind, side=+1, sun_open=+1):
    if kind == "sun": return sun(sun_open)
    if kind == "full": return full()
    if kind in ("thick", "thin"): return crescent(kind, -side)   # lit side faces the sun
    if kind == "diamond": return diamond()
    if kind == "star": return star()
    return dash(side)                                           # points away from the sun

def motif(sun_open=+1):
    """[(u_px, kind, side)] for one motif centred on its sun."""
    out = [(0.0, "sun", 0)]
    for side in (-1, +1):
        for kind, u in HALF:
            out.append((side * u, kind, side))
    return sorted(out)

def join_fill(J):
    """elements between two motifs whose dash centres are J px apart, from the join centre"""
    if J >= 126: return [(-30.8, "diamond"), (0.0, "star"), (30.8, "diamond")]
    if J >= 70: return [(0.0, "star")]
    return []

def scale_parts(parts, k, du, dv):
    def sp(pr):
        if pr[0] == "c": return ("c", du + k * pr[1], dv + k * pr[2], k * pr[3])
        return ("p", [(du + k * x, dv + k * y) for x, y in pr[1]])
    return [(sp(a), [sp(s) for s in subs]) for a, subs in parts]

# Short wall sections take one centred group instead of whole motifs: the motif's core
# (sun with 0-3 moons a side, then diamond and star), or a sunless moon group (full moon
# with crescents lit towards it), or star groups. Same spacing as in the motif.
def _sym(centre, pairs):
    out = [(0.0, centre, 0)] if centre else []
    for kind, u in pairs:
        out += [(-u, kind, -1), (u, kind, +1)]
    return sorted(out)
_CORE = [("full", 107.5), ("thick", 172.5), ("thin", 234.3), ("diamond", 285.0), ("star", 317.3)]
_MOONS = [("thick", 65.0), ("thin", 126.8), ("diamond", 177.5), ("star", 209.8)]
VARIANTS = {}
for _i in range(len(_CORE) + 1):
    VARIANTS["sun+%d" % _i] = _sym("sun", _CORE[:_i])
for _i in range(len(_MOONS) + 1):
    VARIANTS["moon+%d" % _i] = _sym("full", _MOONS[:_i])
VARIANTS["star"] = [(0.0, "star", 0)]
VARIANTS["diamond-star-diamond"] = [(-32.3, "diamond", 0), (0.0, "star", 0), (32.3, "diamond", 0)]

def variant_halfspan(name):
    return max(abs(u) + HALF_MM[kind] for u, kind, _ in VARIANTS[name])

# ---- layout ---------------------------------------------------------------------
def stretch_layout(a, b, n, f, J, m0, k):
    """[(s, kind, side)] for n motifs from s = a + m0, motif spacing f, joins J px"""
    out = []
    s = a + m0 + k * HALF_W["dash"] + k * f * DASH_U       # first sun
    for j in range(n):
        for u, kind, side in motif():
            out.append((s + k * f * u, kind, side))
        if j < n - 1:
            mid = s + k * (f * DASH_U + J / 2)
            for u, kind in join_fill(J):
                out.append((mid + k * u, kind, 0))
            s += k * (2 * f * DASH_U + J)
    return out

HALF_MM = {"sun": SUN_LONG_CARD, "full": R_MOON, "thick": R_MOON, "thin": R_MOON, "diamond": 10.0, "star": 14.5, "dash": 14.1}
# penalty for an element overlapping a corner of each kind; a sun may sit on a plain
# rounded corner only if it is centred there (like the corner sun in the design sheet)
PENALTY = {"sun": (1000, 1000), "full": (2, 150), "thick": (2, 150), "thin": (2, 150),
           "star": (0, 8), "diamond": (0, 8), "dash": (0, 8)}     # (convex corner, step)

def layout(P, zones, corners, k=MOON_K, sun_open=+1, log=print):
    """Place motifs in every stretch between zones (s-intervals, wrapping at P).
    corners: (a, b, kind) s-intervals of wall that isn't straight; kind "convex" is a
    plain rounded corner, "step" is a jog in the wall (S-bend), where elements break up.
    Each join between motifs is chosen on its own (dynamic programming over the sun
    positions), so the suns can dodge the corners without stretching the motifs.
    Returns [(s_centre, kind, parts_mm)] and a list of per-stretch summaries."""
    zs = sorted(((lo % P, (lo % P) + (hi - lo)) for lo, hi in zones))
    stretches = []
    for i, (lo, hi) in enumerate(zs):
        nlo = zs[(i + 1) % len(zs)][0] + (P if i + 1 == len(zs) else 0)
        stretches.append((hi, nlo))
    cs = [(ca + w, cb + w, kind) for ca, cb, kind in corners for w in (-P, 0, P, 2 * P)]
    def penalty(s, kind):
        h = k * HALF_MM[kind] + 0.3; pen = 0.0
        for ca, cb, ck in cs:
            if s + h > ca and s - h < cb:
                if kind == "sun" and ck == "convex" and abs(s - (ca + cb) / 2) < 1.0: pen += 15
                else: pen += PENALTY[kind][1 if ck == "step" else 0]
        return pen
    GRID, JSTEP, MMIN, MMAX = 0.5, 4, 1.5, 12.0
    mcost = lambda m: 0.3 * max(0.0, m - 4.0) ** 2        # bare wall at the ends of a stretch
    placed, summary = [], []
    for a, b in stretches:
        L = b - a; best = None
        for fi in range(0, 21, 4):
            f = 1.0 + 0.01 * fi
            hm = k * (f * DASH_U + HALF_W["dash"])           # sun to the outer tip of its dash
            mot = [(k * f * u, kind) for u, kind, _ in motif()]
            npos = int((L - 2 * hm - 2 * MMIN) / GRID) + 1
            if npos < 1: continue
            pos = [a + MMIN + hm + i * GRID for i in range(npos)]
            mpen = [sum(penalty(sp + du, kind) for du, kind in mot) for sp in pos]
            # joins: J px between the two dashes, or "S" = shared (the two motifs overlap so
            # their outer stars coincide: one star between the two diamonds, no dashes)
            Js = ["S"] + list(range(int(JOIN_MIN), 241, JSTEP))
            jcost = {"S": (int(round(k * f * 2 * STAR_U / GRID)), 0.5, [(k * f * STAR_U, "star")])}
            for J in Js[1:]:
                D = k * (2 * f * DASH_U + J)
                jcost[J] = (int(round(D / GRID)), 2.0 * ((J - 50) / 100) ** 2, [(k * (f * DASH_U + J / 2) + k * u, kd) for u, kd in join_fill(J)])
            # DP: cost[i] of a chain ending with a sun at pos[i]; start margin in [MMIN, MMAX]
            INF = float("inf")
            cost = [mpen[i] + mcost(pos[i] - hm - a) if pos[i] - hm - a <= MMAX else INF for i in range(npos)]
            back = [[None] * npos]
            for n in range(1, 12):
                # close the chain here: end margin in [MMIN, MMAX]
                for i in range(npos):
                    if cost[i] < INF and b - pos[i] - hm <= MMAX:
                        m0 = None
                        c = cost[i] + 100 * (f - 1.0) ** 2 + mcost(b - pos[i] - hm)
                        if best is None or c < best[0]:
                            best = (c, f, n, i, [row[:] for row in back], cost[:], pos[:])
                nxt = [INF] * npos; bk = [None] * npos
                for i in range(npos):
                    if cost[i] == INF: continue
                    for J in Js:
                        di, jc, fill = jcost[J]
                        t = i + di
                        if t >= npos: break
                        c = cost[i] + jc + mpen[t] + sum(penalty(pos[i] + du, kd) for du, kd in fill)
                        if c < nxt[t]: nxt[t] = c; bk[t] = (i, J)
                if all(c == INF for c in nxt): break
                cost = nxt; back.append(bk)
        # one centred group instead, for sections too short for whole motifs
        single = None
        for name, els in VARIANTS.items():
            hs = k * max(abs(u) + HALF_MM[kind] for u, kind, _ in els)
            lo, hi = a + MMIN + hs, b - MMIN - hs
            if hi < lo: continue
            for i in range(int((hi - lo) / GRID) + 1):
                sc = lo + i * GRID
                m0, m1 = sc - hs - a, b - sc - hs
                pen = sum(penalty(sc + k * u, kind) for u, kind, _ in els)
                c = pen + mcost(m0) + mcost(m1) + 0.05 * (m0 - m1) ** 2 + (0.0 if name.startswith("sun") else 1.0)
                if single is None or c < single[0]: single = (c, name, sc, m0, m1, pen)
        if single is not None and (best is None or single[0] < best[0]):
            c, name, sc, m0, m1, pen = single
            items = [(sc + k * u, kind, side) for u, kind, side in VARIANTS[name]]
            bad = [(kind, round(x % P, 1)) for x, kind, _ in items if penalty(x, kind) >= 10]
            summary.append(dict(start=a, end=b, length=L, group=name, centre=round(sc % P, 1), margins=(m0, m1), flagged=bad, cost=c))
            log("moon stretch %.1f-%.1f (%.1f mm): group %s at %.1f, margins %.1f / %.1f mm, cost %.1f, flagged %s"
                % (a, b, L, name, sc % P, m0, m1, c, bad))
            for x, kind, side in items:
                placed.append((x % P, kind, scale_parts(element(kind, side, sun_open), k, x % P, 0.0)))
            continue
        if best is None:
            log("moon stretch %.1f-%.1f (%.1f mm): nothing fits, left bare" % (a, b, L)); continue
        c, f, n, i, back, _, pos = best
        suns, joins = [pos[i]], []
        for row in reversed(back[1:n]):
            i, J = row[i]; suns.append(pos[i]); joins.append(J)
        suns.reverse(); joins.reverse()
        hm = k * (f * DASH_U + HALF_W["dash"])
        items = []
        for j, sc in enumerate(suns):
            shared = {-1: j > 0 and joins[j - 1] == "S", +1: j < len(joins) and joins[j] == "S"}
            items += [(sc + k * f * u, kind, side) for u, kind, side in motif()
                      if not (side and shared[side] and kind in ("dash", "star"))]
            if j < len(joins):
                if joins[j] == "S":
                    items.append((sc + k * f * STAR_U, "star", 0))
                else:
                    mid = sc + k * (f * DASH_U + joins[j] / 2)
                    items += [(mid + k * u, kd, 0) for u, kd in join_fill(joins[j])]
        bad = [(kind, round(s % P, 1)) for s, kind, _ in items if penalty(s, kind) >= 10]
        m0, m1 = suns[0] - hm - a, b - suns[-1] - hm
        summary.append(dict(start=a, end=b, length=L, motifs=n, spacing=f, joins_mm=[J if J == "S" else round(J * k, 1) for J in joins],
                            margins=(m0, m1), suns=[round(x % P, 1) for x in suns], on_steps=bad, cost=c))
        log("moon stretch %.1f-%.1f (%.1f mm): %d motifs, spacing x%.2f, joins %s mm, margins %.1f / %.1f mm, suns at %s, cost %.1f, flagged %s"
            % (a, b, L, n, f, [J if J == "S" else round(J * k, 1) for J in joins], m0, m1, [round(x % P, 1) for x in suns], c, bad))
        for s, kind, side in items:
            placed.append((s % P, kind, scale_parts(element(kind, side, sun_open), k, s % P, 0.0)))
    return placed, summary

def count_islands(kind):
    return 2 if kind == "sun" else 1     # the sun's crescent is separate from its rays

def preview(placed, P, zones, corners, Hb, path, px_per_mm=6):
    """Unrolled band as a PNG: gold elements, red zones, grey corners."""
    from PIL import Image, ImageDraw
    W, H = int(P * px_per_mm) + 1, int((Hb + 6) * px_per_mm)
    img = Image.new("RGB", (W, H), (28, 30, 48))
    dr = ImageDraw.Draw(img)
    to = lambda u, v: (u * px_per_mm, H / 2 - v * px_per_mm)
    for a, b, ck in corners:
        for w in (-P, 0):
            dr.rectangle([to(a + w, Hb / 2 + 2), to(b + w, -Hb / 2 - 2)], fill=(60, 62, 80) if ck == "convex" else (40, 90, 90))
    for lo, hi in zones:
        for w in (-P, 0):
            dr.rectangle([to(lo + w, Hb / 2 + 2), to(hi + w, -Hb / 2 - 2)], fill=(110, 30, 30))
    for s, kind, parts in placed:
        for w in (-P, 0, P):
            for add, subs in parts:
                m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
                def draw(pr, val):
                    if pr[0] == "c":
                        x, y, r = pr[1] + w, pr[2], pr[3]
                        md.ellipse([to(x - r, y + r), to(x + r, y - r)], fill=val)
                    else:
                        md.polygon([to(x + w, y) for x, y in pr[1]], fill=val)
                draw(add, 255)
                for sb in subs: draw(sb, 0)
                img.paste((222, 184, 110), mask=m)
    img.save(path)
