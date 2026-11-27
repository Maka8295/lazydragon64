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
# Layout: one centred, mirror-symmetric group per straight face of wall, and only one sun
# on each side of the case (see layout()).
import math

MOON_K = 0.0975           # mm per source pixel: sun 13.1 mm across, moons 5.0 mm (build_case.py passes CASE_MOON_K)

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
# how far each element reaches from its centre along the wall (source px)
HALF_MM = {"sun": SUN_LONG_CARD, "full": R_MOON, "thick": R_MOON, "thin": R_MOON, "diamond": 10.0, "star": 14.5, "dash": 14.1}

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

def scale_parts(parts, k, du, dv):
    def sp(pr):
        if pr[0] == "c": return ("c", du + k * pr[1], dv + k * pr[2], k * pr[3])
        return ("p", [(du + k * x, dv + k * y) for x, y in pr[1]])
    return [(sp(a), [sp(s) for s in subs]) for a, subs in parts]

# Groups smaller than the whole motif: its core (the sun with 0-5 elements a side), or a
# sunless moon group (full moon with crescents lit towards it), or a lone star. Same
# spacing as in the motif.
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

# ---- layout ---------------------------------------------------------------------
# 2026-11-28: one symmetric arrangement per wall face. The band is cut at every corner
# (rounded or stepped) and at the clear zones (front text, USB notch); each straight
# piece of wall left over gets one group, centred on it and mirror-symmetric, so every
# face of the case reads as balanced on its own. The group is the design itself trimmed
# from the outside in until it fits: the whole motif on the long walls, then the sun
# with fewer moons, then a lone sun; faces too short for that stay plain. The
# glyphs are the same size everywhere (one scale k for the whole case) and the spacing
# inside a group is always the design's, so faces differ only in how much of the motif
# they show. (The 2026-11-16 layout filled each stretch between zones with motifs
# chained across the rounded corners, which left them off-centre.)
# No lone glyphs (2026-11-28): a face too short for a sun, or a moon with its crescents,
# stays plain rather than carrying a single moon or star.
GROUPS = ["motif", "sun+5", "sun+3", "sun+2", "sun+1", "sun+0", "moon+1"]
MARGIN = 1.5          # mm of bare wall between a group and a corner or zone, at least

def group(name):
    """[(u_px, kind, side)] of a named group, centred on 0"""
    return motif() if name == "motif" else VARIANTS[name]

def group_halfspan(name):
    return max(abs(u) + HALF_MM[kind] for u, kind, _ in group(name))

def faces(P, zones, corners):
    """the straight pieces of wall that are clear of every corner and zone, as s-intervals"""
    cuts = sorted([(a % P, (a % P) + (b - a)) for a, b in zones] + [(a % P, (a % P) + (b - a)) for a, b, _ in corners])
    merged = []
    for a, b in cuts:
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    # a cut running past P wraps onto the start
    while len(merged) > 1 and merged[-1][1] - P >= merged[0][0]:
        merged[0][0] = min(merged[0][0], merged[-1][0] - P); merged[0][1] = max(merged[0][1], merged[-1][1] - P); merged.pop()
    out = []
    for i in range(len(merged)):
        a = merged[i][1]
        b = merged[i + 1][0] if i + 1 < len(merged) else merged[0][0] + P
        if b - a > 0.0: out.append((a, b))
    return out

def walls(P, corners):
    """The case's sides as you see them: s-intervals between consecutive rounded corners
    (the jogs, the text and the notch don't split a side)."""
    cv = sorted((a % P, (a % P) + (b - a)) for a, b, kind in corners if kind == "convex")
    return [(cv[i][1], cv[i + 1][0] if i + 1 < len(cv) else cv[0][0] + P) for i in range(len(cv))]

def has_sun(name):
    return bool(name) and (name == "motif" or name.startswith("sun"))

def layout(P, zones, corners, k=MOON_K, sun_open=+1, one_sun=True, log=print):
    """Place one centred, symmetric group on every wall face.
    zones: s-intervals kept bare (text, notch, wall jogs); corners: (a, b, kind) s-intervals
    of wall that isn't straight. With one_sun (2026-11-28, "where there are several suns,
    plain looks better, except the main one"), each side of the case keeps only the sun
    nearest its middle; the other faces on that side that would have had a sun are left
    plain. Returns [(s_centre, kind, parts_mm)] and per-face summaries."""
    plan = []
    for a, b in faces(P, zones, corners):
        L = b - a
        name = next((g for g in GROUPS if 2 * k * group_halfspan(g) <= L - 2 * MARGIN), None)
        if name is None:
            if L >= 2.0: log("moon face %.1f-%.1f (%.1f mm): too short, left bare" % (a % P, b % P, L))
            continue
        plan.append([a, b, name])
    if one_sun:
        for wa, wb in walls(P, corners):
            W = wb - wa
            on = [f for f in plan if has_sun(f[2]) and ((f[0] + f[1]) / 2 - wa) % P <= W]
            if len(on) < 2: continue
            main = min(on, key=lambda f: abs(((f[0] + f[1]) / 2 - wa) % P - W / 2))
            for f in on:
                if f is not main:
                    log("moon face %.1f-%.1f: left plain, the side %.1f-%.1f keeps its main sun at %.1f"
                        % (f[0] % P, f[1] % P, wa % P, wb % P, ((main[0] + main[1]) / 2) % P))
                    f[2] = None
    placed, summary = [], []
    for a, b, name in plan:
        if name is None: continue
        L = b - a; c = (a + b) / 2
        m = L / 2 - k * group_halfspan(name)
        summary.append(dict(start=a % P, end=b % P, length=L, group=name, centre=c % P, margin=m))
        log("moon face %.1f-%.1f (%.1f mm): %s centred at %.1f, %.1f mm bare each end" % (a % P, b % P, L, name, c % P, m))
        for u, kind, side in group(name):
            x = (c + k * u) % P
            placed.append((x, kind, scale_parts(element(kind, side, sun_open), k, x, 0.0)))
    if one_sun:
        for x, kind, side, info in flanks(plan, P, k):
            if info: summary.append(info); log(info["log"])
            placed.append((x % P, kind, scale_parts(element(kind, side, sun_open), k, x % P, 0.0)))
    return placed, summary

# 2026-11-28 (the user's sketch of the back wall): where a side's only sun stands alone on a
# short face between two jogs (the back wall's raised middle) and the faces either side were
# left plain, those two faces carry the rest of the design as the two halves of one motif:
# outwards from the sun, a full moon, two crescents, the diamond, the star and the dash, at
# the design's spacing (the diamond and star were left out at first and put back the same
# day). Both halves sit the same distance from the sun, moved out just far enough that the
# full moons clear the jogs by MARGIN; if either half then doesn't fit its face, both faces
# stay plain.
FLANK = HALF

def flanks(plan, P, k):
    """[(s, kind, side, summary or None)] for the flanking halves (see FLANK)."""
    out = []
    inner = k * min(u - HALF_MM[kind] for kind, u in FLANK)     # sun centre to the full moon's near edge
    outer = k * max(u + HALF_MM[kind] for kind, u in FLANK)     # ... to the dash's far end
    n = len(plan)
    for i, (a, b, name) in enumerate(plan):
        if name != "sun+0" or n < 3: continue
        before, after = plan[i - 1], plan[(i + 1) % n]
        if before[2] is not None or after[2] is not None: continue
        c = (a + b) / 2
        rel = lambda s: (s - c + P / 2) % P - P / 2               # s relative to the sun, -P/2..P/2
        ga, gb = rel(before[0]), rel(before[1]); fa, fb = rel(after[0]), rel(after[1])
        d = max(0.0, fa + MARGIN - inner, -(gb - MARGIN) - inner)
        if fb - MARGIN < outer + d or ga + MARGIN > -(outer + d): continue
        for side in (-1, +1):
            for kind, u in FLANK:
                out.append((c + side * (k * u + d), kind, side, None))
        out[-1] = out[-1][:3] + (dict(start=before[0] % P, end=after[1] % P, group="flanks", centre=c % P, shift=d,
            log="moon flanks round the sun at %.1f: half the design each side, %.1f mm further out than "
                "in the design, dash ends at %.1f and %.1f (faces %.1f-%.1f and %.1f-%.1f)"
                % (c % P, d, (c - outer - d) % P, (c + outer + d) % P, before[0] % P, before[1] % P, after[0] % P, after[1] % P)),)
    return out

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
