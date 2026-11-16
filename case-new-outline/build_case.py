# Lucca58 Stagger case for the extended PCB outline. Run:  freecadcmd -c "exec(open('build_case.py').read())"
#
# There is no parametric source for the Lucca58 case, so this reads the real
# profile from the original STEP and edits it, leaving everything to the right
# of the moved block geometrically identical to the original.
#
# Env vars (all optional):
#   CASE_SRC   folder holding the original "Lucca58 Case Left.step"
#   CASE_OUT   output folder (default: this case folder)
#   CASE_MODE  "stagger" (default) applies the Stagger edit; "regress" rebuilds
#              the unedited original, which is how the method was checked
#   CASE_CLERESTORY  "1" also builds the clerestory (windowed) version (default: off)
#   CASE_LOG   log file (default: none)
import os, math, time, json
import FreeCAD as App, Part, Mesh
from FreeCAD import Vector as V

SRC = os.environ.get("CASE_SRC", os.path.expanduser("~/PCBs/Lucca58/case"))
OUT = os.environ.get("CASE_OUT", os.path.expanduser("~/PCBs/lazydragon64/case-new-outline"))
MODE = os.environ.get("CASE_MODE", "stagger")
CLERESTORY = os.environ.get("CASE_CLERESTORY", "0") == "1"
LOG = open(os.environ.get("CASE_LOG", os.devnull), "w")
def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()

# ---- mapping and heights -------------------------------------------------
# KiCad (x, y) -> Left case (x + TX, -y + TY)
TX, TY = -8.023, 7.669
Z_BOTTOM, Z_HEXTOP, Z_FLOOR, Z_RING, Z_RIM = -4.0, -2.2, -1.0, 1.5, 15.1
NOTCH = (183.265, 197.715)     # long-side cutout, R2 bottom corners

# ---- Stagger edit --------------------------------------------------------
DY = 9.525                     # left block slides down so its bottom meets col 3
X_BLOCK = 110.0                # case-frame x below which standoffs are in the block
# Standoffs in the moved block, KiCad frame. Each sits in the corridor between
# columns, clear of pads and diode/cap/LED bodies on BOTH PCB sides: the old
# four-key-corner spots land on diodes, and the col 2/3 row can no longer move
# rigidly because col 3 stayed put.
NEW_STANDOFFS = [(93.9, 92.25), (93.9, 111.25), (93.9, 130.4),
                 (112.9, 92.25), (112.9, 111.25), (112.9, 130.4)]

# ---- lazydragon64 mounting (2026-11-11), stagger mode only ------------------
# Corne Cherry v4 style, replacing all 15 original M2.5 standoffs. Four M2 x 7.5 mm
# female-female spacers stand on the floor (top at Z_FLOOR), pass through the PCB's
# 5.0 mm clearance holes H1-H4 without touching it, and carry the 1.6 mm FR4 plate:
# floor-to-plate-underside is 2.5 + 1.6 + 3.4 = 7.5 mm, the same as the Corne. One
# M2 x 5 screw goes up through the floor into each spacer and one down through the
# plate. The PCB hangs from the switches, so nothing touches it from below. The floor
# is counterbored to leave 2.0 mm under each spacer, like the Corne's 2.0 mm floor, so
# the M2 x 5 screws get the same 3 mm of thread. The spacer must be a 3.5 mm hex
# (4.04 across corners) or round <= 4.0 mm: parts sit 2.25 mm from each hole on both
# PCB faces. Positions in KiCad mm.
SCREWS = [(94.005, 72.565), (93.995, 112.995), (170.205, 72.565), (170.215, 132.145)]
# 2026-11-14: the counterbore under the case is 1.3 mm deep (floor 1.7 mm under each
# spacer) so an M2 x 5 hex-socket button head (head 3.4 x 1.23 mm) sits flush with the
# bottom. The screw then has 3.3 mm of thread in the spacer. Was 1.0 mm deep (2.0 floor).
SCREW_D, CBORE_D, FLOOR_UNDER_SPACER = 2.2, 4.4, 1.7
# 2026-11-14: LCSC only stocks 8 mm M2 standoffs (the 7.5 mm STTZ1041 is out of stock), so
# each standoff stands in a pocket SPACER_LEN - 7.5 deep (Ø4.6) in the top of the floor.
# Its top, and so the plate, lands where a 7.5 mm standoff on the flat floor would. With
# the 1.3 mm counterbore underneath, 1.2 mm of floor is left under each standoff, and
# the pocket also locates the standoffs during assembly. CASE_SPACER_LEN=7.5: no pocket.
# Screws: M2 x 4 pan head (LCSC C357393) at both ends, 2.8 + 2.4 mm of thread.
SPACER_LEN = float(os.environ.get("CASE_SPACER_LEN", "8.0"))
POCKET_D, POCKET_DEPTH = 4.6, SPACER_LEN - 7.5
assert 0 <= POCKET_DEPTH <= FLOOR_UNDER_SPACER - 1.0, "pocket would leave < 1 mm of floor"
# Optional PCB-support pillars (CASE_PILLARS=1; the Corne has none). Each is placed
# where a 3 mm pillar clears every pad, courtyard and socket body on both faces by 0.3 mm.
PILLARS = [(94.0, 54.0), (94.0, 92.25), (94.0, 130.25), (113.0, 73.25), (113.0, 111.25),
           (132.0, 53.0), (131.25, 88.0), (131.5, 126.5), (151.25, 53.0), (151.25, 72.25),
           (151.25, 110.25), (170.25, 55.5), (170.25, 93.75), (170.25, 112.75), (185.5, 70.25),
           (189.25, 113.75), (196.5, 81.0), (204.5, 108.5), (195.5, 136.0)]
PILLAR_D = 3.0
if os.environ.get("CASE_PILLARS", "0") != "1":
    PILLARS = []
# J1 (USB-C link) is on the key side, under the raised RP2040-Zero, so both plugs
# enter through the original notch and nothing hangs below the PCB there.

# ---- Clerestory parameters (same as the original build) ------------------
W, PITCH, MARGIN = 5.6, 8.0, 1.2
ZB, ZT = 2.4, 13.4
WD, BD, EMB = 0.8, 1.0, 0.3
BANDS = [(1.4, 2.4), (14.0, 15.0)]

# ---- read the real profile ------------------------------------------------
def poly_of(w):
    segs = [(e.Vertexes[0].Point, e.Vertexes[-1].Point) for e in w.Edges]
    used = [False] * len(segs); pts = [segs[0][0], segs[0][1]]; used[0] = True
    for _ in range(len(segs) - 1):
        p = pts[-1]; best = None
        for i, (a, b) in enumerate(segs):
            if used[i]: continue
            da, db = (a - p).Length, (b - p).Length
            if best is None or min(da, db) < best[0]:
                best = (min(da, db), i, b if da < db else a)
        used[best[1]] = True; pts.append(best[2])
    if (pts[0] - pts[-1]).Length < 1e-6: pts = pts[:-1]
    return [(p.x, p.y) for p in pts]

src = Part.Shape(); src.read(os.path.join(SRC, "Lucca58 Case Left.step"))
big = lambda ws: max(ws, key=lambda w: w.BoundBox.DiagonalLength)
small = lambda ws: [w for w in ws if w.BoundBox.DiagonalLength < 20]
O = poly_of(big(src.slice(V(0, 0, 1), -3.1)))
WALL = poly_of(big(src.slice(V(0, 0, 1), 5.19)))
HEX = [poly_of(w) for w in small(src.slice(V(0, 0, 1), -3.1))]
HOLE = [poly_of(w) for w in small(src.slice(V(0, 0, 1), -1.6))]
RINGW = [poly_of(w) for w in small(src.slice(V(0, 0, 1), 0.69))]
def size(p): return max(q[0] for q in p) - min(q[0] for q in p)
def centre(p):
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
RING = [p for p in RINGW if size(p) > 4]
log("read O", len(O), "wall", len(WALL), "hex", len(HEX), "hole", len(HOLE), "ring", len(RING))

def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ((dx * dx + dy * dy) or 1)))
    return math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1])
def on_outer(p):
    return min(seg_dist(p, O[i], O[(i + 1) % len(O)]) for i in range(len(O))) < 0.01

# Inner wall = the unbroken run of wall vertices that are not on the outer path.
flags = [on_outer(p) for p in WALL]
n = len(WALL)
start = next(i for i in range(n) if flags[i] and not flags[(i + 1) % n])
I = []
i = (start + 1) % n
while not flags[i]:
    I.append(WALL[i]); i = (i + 1) % n
log("inner path", len(I), "bbox x", min(p[0] for p in I), max(p[0] for p in I), "y", min(p[1] for p in I), max(p[1] for p in I))

def find(poly, x, y):
    return min(range(len(poly)), key=lambda k: math.hypot(poly[k][0] - x, poly[k][1] - y))
if MODE == "stagger":
    # outer: col 3 bottom (106.52,-140.748), left bottom (100.52,-131.223) -> top step (100.516,-46.022)
    keep = find(O, 106.520, -140.748)
    a = find(O, 100.520, -131.223) + 1      # first vertex of the left-bottom run past the step
    b = find(O, 100.516, -46.022)
    O2 = O[:keep + 1] + [(x, y - DY) for x, y in O[a:b + 1]] + O[b + 1:]
    # Fill the divot under the middle-finger column so the outer wall runs straight
    # from the ring-finger column to the pointer column. Only the outer profile
    # changes: the inner wall keeps its bump up to that column's bottom key. The two
    # sides differ by 4 um, so level them or the clerestory stops treating this as
    # one straight run and drops its windows.
    fill_from = find(O2, 157.672, -140.752)
    fill_to = find(O2, 106.520, -140.748)
    assert 0 < fill_from < fill_to
    O2 = O2[:fill_from] + [(O2[fill_from][0], O2[fill_to][1])] + O2[fill_to:]
    log("outer verts", len(O), "->", len(O2))
    # inner runs the other way round the wall, so handle it by its own landmarks
    i_top = find(I, 104.516, -50.022)
    i_low = find(I, 104.520, -127.223)
    i_end = find(I, 106.520, -136.748)
    log("inner idx top", i_top, "low", i_low, "end", i_end, "of", len(I))
    assert i_top < i_low < i_end
    I2 = I[:i_top] + [(x, y - DY) for x, y in I[i_top:i_low + 1]] + I[i_end + 1:]
    log("inner verts", len(I), "->", len(I2))
    # Extended outline. Columns 1 and 2 now reach column 3's top edge, so the left
    # block's top corner rises and the old step goes. The MCU area's top wall moves
    # up 2.5 mm, and the outer wall runs straight from there to the middle-finger
    # bump. The inner wall keeps column 6's lower edge, so that section is solid.
    at = lambda P, x, y: min(range(len(P)), key=lambda k: math.hypot(P[k][0] - x, P[k][1] - y))
    TL, MCU = 19.043, 2.5
    a = at(O2, 62.416, -61.547); b = at(O2, 68.416, -55.547)
    d = at(O2, 106.516, -36.504); e = at(O2, 147.622, -36.504)
    f_ = at(O2, 198.772, -39.004); g_ = at(O2, 204.772, -45.004)
    top = O2[e][1]
    left = [(x, y + TL) for x, y in O2[a:b + 1]]; left[-1] = (left[-1][0], top)
    right = [(x, y + MCU) for x, y in O2[f_:g_ + 1]]; right[0] = (right[0][0], top)
    O = O2[:a] + left + O2[d + 1:e + 1] + right + O2[g_ + 1:]
    log("outer verts ->", len(O))
    i_e = at(I2, 123.571, -40.504); i_s = at(I2, 68.416, -59.547); i_c = at(I2, 66.416, -61.547)
    i_r = at(I2, 200.772, -45.004)
    MID = 171.6945                       # mirrors column 5's inner step to the new one
    step = [(2 * MID - x, y) for x, y in reversed(I2[1:12])]
    corner = [(x, y + TL) for x, y in I2[i_s:i_c + 1]]
    I = [(I2[0][0], I2[0][1] + MCU)] + step + I2[1:i_e + 1] + corner + I2[i_c + 1:i_r] + [(x, y + MCU) for x, y in I2[i_r:]]
    log("inner verts ->", len(I))
    # The original standoffs are replaced by SCREWS/PILLARS (see base()). The
    # 2026-11-07 build moved six of them to NEW_STANDOFFS instead; see git history.
    HEX, HOLE, RING = [], [], []

# ---- build ---------------------------------------------------------------
def face(poly):
    pts = [V(x, y, 0) for x, y in poly]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))
def prism(poly, z0, z1):
    s = face(poly).extrude(V(0, 0, z1 - z0)); s.translate(V(0, 0, z0)); return s

def cyl(d, x, y, z0, z1):                    # x, y in KiCad mm
    return Part.makeCylinder(d / 2, z1 - z0, V(x + TX, -y + TY, z0))
def hexagon(af, x, y):                       # flats facing +-x, like the original pockets
    R = af / math.sqrt(3); cx, cy = x + TX, -y + TY
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(30, 360, 60)]

def base():
    s = prism(O, Z_BOTTOM, Z_RIM)
    s = s.cut(prism(I, Z_FLOOR, Z_RIM + 1))
    if MODE == "stagger":
        if PILLARS:   # embedded 0.3 into the floor so nothing is coplanar
            s = s.fuse([cyl(PILLAR_D, x, y, Z_FLOOR - 0.3, Z_RING) for x, y in PILLARS]).removeSplitter()
        s = s.cut([cyl(SCREW_D, x, y, Z_BOTTOM - 1, Z_FLOOR + 0.5) for x, y in SCREWS])
        z_cb = Z_FLOOR - FLOOR_UNDER_SPACER
        s = s.cut([cyl(CBORE_D, x, y, Z_BOTTOM - 1, z_cb) for x, y in SCREWS])
        if POCKET_DEPTH > 0:   # standoff seat, open to the cavity above
            s = s.cut([cyl(POCKET_D, x, y, Z_FLOOR - POCKET_DEPTH, Z_FLOOR + 0.5) for x, y in SCREWS])
        return s.removeSplitter()
    # rings are embedded 0.3 into the floor so nothing is coplanar
    s = s.fuse([prism(r, Z_FLOOR - 0.3, Z_RING) for r in RING]).removeSplitter()
    s = s.cut([prism(h, Z_HEXTOP - 0.1, Z_RING + 0.5) for h in HOLE])
    s = s.cut([prism(h, Z_BOTTOM - 1, Z_HEXTOP) for h in HEX])
    return s.removeSplitter()

def notch_tool(extra=0.0):
    c = Part.makeBox(NOTCH[1] - NOTCH[0] + 2 * extra, 12, 25, V(NOTCH[0] - extra, -44.0, Z_FLOOR))
    return c.makeFillet(2.0, [e for e in c.Edges if abs(e.BoundBox.ZMax - Z_FLOOR) < 1e-6 and e.BoundBox.YLength > 1])

t0 = time.time()
plain = base().cut(notch_tool()).removeSplitter()
log("plain valid", plain.isValid(), "solids", len(plain.Solids), "vol", round(plain.Volume, 2), "bbox", plain.BoundBox, "t", round(time.time() - t0, 1))

# ---- clerestory (same recipe as the original) ----------------------------
def lancet(w, zb, ztop):
    zs = ztop - w * math.sin(math.radians(60)); h = w / 2
    def arcpt(cx, ang): return V(cx + w * math.cos(math.radians(ang)), zs + w * math.sin(math.radians(ang)), 0)
    e = [Part.LineSegment(V(-h, zb, 0), V(h, zb, 0)).toShape(),
         Part.LineSegment(V(h, zb, 0), V(h, zs, 0)).toShape(),
         Part.Arc(V(h, zs, 0), arcpt(-h, 30), V(0, ztop, 0)).toShape(),
         Part.Arc(V(0, ztop, 0), arcpt(h, 150), V(-h, zs, 0)).toShape(),
         Part.LineSegment(V(-h, zs, 0), V(-h, zb, 0)).toShape()]
    return Part.Face(Part.Wire(e)), zs
def disc(r, x, y): return Part.Face(Part.Wire(Part.makeCircle(r, V(x, y, 0))))
def trefoil(cx, cy, dist, r, ring):
    cs = [(cx + dist * math.cos(math.radians(a)), cy + dist * math.sin(math.radians(a))) for a in (90, 210, 330)]
    outer = disc(r + ring, *cs[0]).fuse([disc(r + ring, *c) for c in cs[1:]])
    inner = disc(r, *cs[0]).fuse([disc(r, *c) for c in cs[1:]])
    return outer.cut(inner)
def window_face(W, zb, ztop, t=0.7):
    outer, zs = lancet(W, zb, ztop)
    frame = outer.cut(outer.makeOffset2D(-t))
    tr_h = 0.5
    transom = Part.makePlane(W, tr_h, V(-W / 2, zs - tr_h / 2, 0))
    tre = trefoil(0, zs + 1.3, 0.6, 0.62, 0.4)
    return frame.fuse([transom, tre]).common(outer).removeSplitter()

def clerestory(solid):
    pts = [V(x, y, 0) for x, y in O]; pts.append(pts[0])
    F = Part.Face(Part.makePolygon(pts))
    runs = []; cur = None
    for a, b in zip(pts[:-1], pts[1:]):
        d = b - a; key = None
        if abs(d.y) < 1e-3 and abs(d.x) > 1e-4: key = ('y', round(a.y, 2), d.x > 0)
        elif abs(d.x) < 1e-3 and abs(d.y) > 1e-4: key = ('x', round(a.x, 2), d.y > 0)
        if key and cur and cur[0] == key: cur[2] = b
        else:
            if cur: runs.append(cur)
            cur = [key, a, b] if key else None
    if cur: runs.append(cur)
    runs = [r for r in runs if (r[2] - r[1]).Length >= W + 2 * MARGIN]
    Z = V(0, 0, 1)
    ws = window_face(W, ZB, ZT).extrude(V(0, 0, WD + EMB)); ws.translate(V(0, 0, -EMB))
    sols = ws.Solids
    ws = sols[0].fuse(sols[1:]).removeSplitter() if len(sols) > 1 else sols[0]
    windows = []; info = []
    for key, a, b in runs:
        t0_ = (b - a); t0_.normalize()
        n_ = V(t0_.y, -t0_.x, 0)
        mid = (a + b) * 0.5
        if F.isInside(mid + n_ * 0.5, 1e-6, True): n_ = n_ * -1
        t_ = Z.cross(n_)
        s0, s1 = sorted([(a - mid).dot(t_), (b - mid).dot(t_)])
        intervals = [(s0 + MARGIN, s1 - MARGIN)]
        if key[0] == 'y' and n_.y > 0 and min(a.x, b.x) < NOTCH[0] < max(a.x, b.x):
            c0, c1 = sorted([(V(NOTCH[0], a.y, 0) - mid).dot(t_), (V(NOTCH[1], a.y, 0) - mid).dot(t_)])
            intervals = [(lo, min(hi, c0 - 1.5)) for lo, hi in intervals] + [(max(lo, c1 + 1.5), hi) for lo, hi in intervals]
        for lo, hi in intervals:
            L = hi - lo
            if L < W: continue
            k = int((L - W) // PITCH) + 1
            start_ = (lo + hi) / 2 - (k - 1) * PITCH / 2
            for i_ in range(k):
                u = start_ + i_ * PITCH
                M = App.Matrix(t_.x, Z.x, n_.x, 0, t_.y, Z.y, n_.y, 0, t_.z, Z.z, n_.z, 0, 0, 0, 0, 1)
                w_ = ws.copy(); w_.transformShape(M); w_.translate(mid + t_ * u)
                windows.append(w_)
            info.append((key, round(L, 1), k))
    log("clerestory runs", len(runs), "windows", len(windows))
    for i_ in info: log("   ", i_)
    # join 2 keeps the visible band clean. The inward offset ends up buried in the
    # wall, and join 2 fails on the filled outline, so it uses join 0.
    off = F.makeOffset2D(BD, 2); inn = F.makeOffset2D(-EMB, 0)
    bands = []
    for z0, z1 in BANDS:
        b_ = off.cut(inn).extrude(V(0, 0, z1 - z0)); b_.translate(V(0, 0, z0)); bands.append(b_)
    res = solid
    for b_ in bands:
        res = res.fuse(b_).removeSplitter(); log("  after band solids", len(res.Solids))
    res = res.fuse(windows).removeSplitter(); log("  after windows solids", len(res.Solids))
    res = res.cut(notch_tool(0.02)).removeSplitter()
    log("clerestory valid", res.isValid(), "solids", len(res.Solids), "vol", round(res.Volume, 2), "bbox", res.BoundBox)
    return res, len(windows)

variants = [("", plain)]
if CLERESTORY:
    t0 = time.time()
    cler, nwin = clerestory(plain)
    log("clerestory time", round(time.time() - t0, 1))
    variants.append((" Clerestory", cler))
else:
    nwin = 0

# ---- decorations (2026-11-11), stagger mode -----------------------------------
# Bottom: the Lazy Dragon drawing (~/Pictures/dragon.jpg, traced into dragon_art.json
# by trace_art.py at 112.5 mm wide with 1 px of line thickening) is engraved ART_DEPTH
# into the bottom face. By default (CASE_ART_ROT=180, 2026-11-13) it reads upright when
# the half is turned over left-to-right, like a page. CASE_ART_ROT=0 gives the original
# orientation, upright when turned over front-to-back; only that one keeps every
# counterbore on both halves 3.6 mm from the ink. At 180 the left-middle screw (H2) lands
# in the coin pile, so its ART_CLEAR circle leaves a small blank ring there.
# Front: TEXT in Cloister Black, raised TEXT_RAISE on the longest straight run of the
# user-facing wall. Each half gets its own unmirrored copies so both read correctly.
# CASE_IVY_ONLY=1 (with CASE_IVY=1): no front text and no plaque gap, so the vine runs all
# the way round and stops only at the USB notch. Since 2026-11-14 the bottom drawing is
# still engraved (user wants the dragon on both undersides); CASE_IVY_ONLY_ART=0 leaves
# the bottom plain as before.
IVY_ONLY = os.environ.get("CASE_IVY_ONLY", "0") == "1"
DECOR = os.environ.get("CASE_DECOR", "1") == "1" and MODE == "stagger" and not IVY_ONLY
IVY_ONLY_ART = IVY_ONLY and MODE == "stagger" and os.environ.get("CASE_IVY_ONLY_ART", "1") == "1"
ART_JSON = os.environ.get("CASE_ART", os.path.expanduser("~/PCBs/lazydragon64/case-new-outline/dragon_art.json"))
# 2026-11-14: the drawing is centred on the case outline's bounding box and scaled to
# ART_SCALE (0.80 = 90.0 x 47.6 mm). That is the largest round size at which no screw
# comes within ART_CLEAR of any line (max 0.805; H3 is the limit at 4.0 mm), so all four
# counterbores sit outside the drawing. Before: full size at KiCad (142, 102), where H2
# cut a blank ring into the coin pile. The ART_CLEAR cut stays as a guard and the build
# logs whether it removed anything.
_ox = [x for x, _ in O]; _oy = [y for _, y in O]
ART_CENTER = ((min(_ox) + max(_ox)) / 2 - TX, -((min(_oy) + max(_oy)) / 2 - TY))   # KiCad mm
ART_SCALE = float(os.environ.get("CASE_ART_SCALE", "0.80"))
ART_DEPTH, ART_CLEAR = 0.6, 3.6     # mm
ART_ROT = int(os.environ.get("CASE_ART_ROT", "180"))             # 0 or 180, about ART_CENTER
assert ART_ROT in (0, 180), "CASE_ART_ROT must be 0 or 180"
TEXT, FONT = "Lazy Dragon", os.path.expanduser("~/.local/share/fonts/CloisterBlack.ttf")
TEXT_RAISE, TEXT_EMBED = 0.6, 0.3
# 2026-11-16: CASE_TEXT_H sets the text's height (default 12 mm, capped at 85 % of the
# run's length) and CASE_TEXT_ALIGN=left puts its left edge CASE_TEXT_MARGIN from the
# run's left end instead of centring it (Marika cases: 7.5 mm, left, 3 mm).
TEXT_H = float(os.environ.get("CASE_TEXT_H", "12.0"))
TEXT_ALIGN = os.environ.get("CASE_TEXT_ALIGN", "center")
TEXT_MARGIN = float(os.environ.get("CASE_TEXT_MARGIN", "3.0"))
assert TEXT_ALIGN in ("center", "left"), "CASE_TEXT_ALIGN must be center or left"

def inside_O(x, y):
    c = False
    for i in range(len(O)):
        (x1, y1), (x2, y2) = O[i], O[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def front_run():
    # longest straight run of the outline whose outside faces the user (-y); collinear
    # edges split by a vertex count as one run
    runs = []
    for i in range(len(O)):
        (x1, y1), (x2, y2) = O[i], O[(i + 1) % len(O)]
        if abs(y2 - y1) < 1e-3 and abs(x2 - x1) > 1e-4 and inside_O((x1 + x2) / 2, y1 + 0.5):
            runs.append([min(x1, x2), max(x1, x2), round(y1, 3)])
    runs.sort(key=lambda r: (r[2], r[0])); merged = []
    for r in runs:
        if merged and merged[-1][2] == r[2] and abs(merged[-1][1] - r[0]) < 1e-3:
            merged[-1][1] = max(merged[-1][1], r[1])
        else:
            merged.append(r)
    return max(merged, key=lambda r: r[1] - r[0])
def glyph_faces(size):
    # font outlines as fine polygons: OCC booleans with the spline outlines gave invalid solids
    faces = []
    for ws in Part.makeWireString(TEXT, FONT, size, 0):
        if not ws: continue
        polys = []
        for w in ws:
            pts = w.discretize(Deflection=0.01)
            if (pts[0] - pts[-1]).Length > 1e-6: pts.append(pts[0])
            polys.append(Part.makePolygon(pts))
        faces.append(Part.makeFace(polys, "Part::FaceMakerBullseye"))
    return faces

def art_tool(side):
    d = json.load(open(ART_JSON))
    cx, cy = side * (ART_CENTER[0] + TX), -ART_CENTER[1] + TY
    k = -1 if ART_ROT == 180 else 1          # 180: turn the drawing half a turn in place
    wires = []
    for lp in d["loops"]:
        pts = [V(cx + k * ART_SCALE * u, cy - k * ART_SCALE * v, 0) for u, v in lp]
        wires.append(Part.makePolygon(pts + [pts[0]]))
    face = Part.makeFace(wires, "Part::FaceMakerBullseye")
    tool = face.extrude(V(0, 0, ART_DEPTH + 0.5)); tool.translate(V(0, 0, Z_BOTTOM - 0.5))
    clear = [Part.makeCylinder(ART_CLEAR, 5, V(side * (x + TX), -y + TY, Z_BOTTOM - 1)) for x, y in SCREWS]
    cut = tool.cut(clear)
    lost = tool.Volume - cut.Volume
    log("art side", side, "centre KiCad", tuple(round(c, 3) for c in ART_CENTER), "scale", ART_SCALE,
        "screw clearance removed %.4f mm3" % lost, "(clips the drawing!)" if lost > 1e-3 else "(clear)")
    return cut

def text_solid(side):
    x0, x1, yw = front_run()
    bb = Part.makeCompound(glyph_faces(10.0)).BoundBox
    k = min(TEXT_H / bb.YLength, 0.85 * (x1 - x0) / bb.XLength)
    faces = glyph_faces(10.0 * k)
    bb = Part.makeCompound(faces).BoundBox
    cx = (x0 + x1) / 2 if TEXT_ALIGN == "center" else x0 + TEXT_MARGIN + bb.XLength / 2
    if side < 0: x0, x1, cx = -x1, -x0, -cx      # the right half's run, mirrored
    # rotate +90 about x: local x -> case +x (reads left to right from the front),
    # local y -> +z, extrusion (local +z) -> -y, i.e. out of the wall
    pl = App.Placement(V(cx, yw + TEXT_EMBED, (Z_BOTTOM + Z_RIM) / 2), App.Rotation(V(1, 0, 0), 90))
    sols = []
    for f in faces:
        s = f.extrude(V(0, 0, TEXT_RAISE + TEXT_EMBED))
        s.translate(V(-bb.Center.x, -bb.Center.y, 0))
        s.Placement = pl.multiply(s.Placement)
        sols.append(s)
    sol = Part.makeCompound(sols)
    log("text side", side, "run x", round(x0, 2), round(x1, 2), "y", round(yw, 3), "scale", round(k, 3), "align", TEXT_ALIGN, "size", sol.BoundBox)
    return sol

def engrave(shape, side):   # bottom drawing only, no front text (vine-only halves)
    t0 = time.time()
    s = shape.cut(art_tool(side)).removeSplitter()
    log("engraved side", side, "valid", s.isValid(), "solids", len(s.Solids), "t", round(time.time() - t0, 1))
    return s

def decorate(shape, side):
    t0 = time.time()
    s = shape.cut(art_tool(side)).removeSplitter()
    s = s.fuse(text_solid(side).Solids).removeSplitter()
    log("decorated side", side, "valid", s.isValid(), "solids", len(s.Solids), "t", round(time.time() - t0, 1))
    return s

# ---- ivy wrap (2026-11-11): CASE_IVY=1 writes separate " Ivy" files ------------
# One repeat of ~/Downloads/Ornamental Ivy Vine Divider.png, traced by trace_art.py into
# ivy_border.json (image columns 24-2138, plus 4 px of overlap), is raised IVY_RAISE as a
# band centred on the outer wall. Exactly IVY_N repeats fit the outer perimeter, so the
# vine joins up where it wraps round. The outline is unrolled by arc length, and each
# wall facet gets the part of the band over it, extruded along its own normal. A
# rounded plaque around the front text and the USB notch are left clear. The pattern is
# shifted along the wall so those cuts cross bare stem rather than leaves. The right
# half gets the mirror image, so its plaque lands on its own text.
IVY = os.environ.get("CASE_IVY", "0") == "1" and (DECOR or (IVY_ONLY and MODE == "stagger"))
IVY_PHASE = os.environ.get("CASE_IVY_PHASE")   # force the vine's phase (mm), e.g. to match another build
IVY_FILL = os.environ.get("CASE_IVY_FILL", "1") == "1"
IVY_JSON = os.environ.get("CASE_IVY_ART", os.path.expanduser("~/PCBs/lazydragon64/case-new-outline/ivy_border.json"))
IVY_N, IVY_RAISE, IVY_EMBED = 6, 0.8, 0.3
IVY_MAX_BAND = float(os.environ.get("CASE_IVY_MAX_BAND", "14.5"))   # mm; alternating tiles: band = 2 x reach from the stem
IVY_NAME = os.environ.get("CASE_IVY_NAME", " Ivy")
PLAQUE_PAD, PLAQUE_R, NOTCH_PAD = (3.0, 1.5), 2.0, 1.0      # mm
# 2026-11-16, Marika cases: CASE_BAND=moon wraps the moon-phase band of moon_band.py
# (design B of ~/Downloads/image0(1).png) instead of a traced ivy tile. It goes through
# the same unrolled-band path below (facet strips, corner wedges, checks). The jogs in
# the wall are left bare and every straight section between them, the text and the
# notch gets its own centred arrangement (see moon_band.layout). CASE_MOON_K is the
# scale in mm per source pixel. The crescent inside each sun opens to the right as seen
# from outside, like the design (CASE_MOON_SUN_OPEN=-1: to the left). The band's s runs
# right to left along the outside of the left half's walls, so the band is drawn with
# the crescent reversed for the left half; an IVY_ONLY build is used for its mirrored
# right half, and the mirror turns it back, so that one is drawn the right way round.
BAND = os.environ.get("CASE_BAND", "ivy")
assert BAND in ("ivy", "moon"), "CASE_BAND must be ivy or moon"
MOON_K = float(os.environ.get("CASE_MOON_K", "0.105"))
MOON_SUN_OPEN = int(os.environ.get("CASE_MOON_SUN_OPEN", "1"))
# 2026-11-11 second version: CASE_IVY_ART=ivy_minimalist.json CASE_IVY_NAME=" Ivy Minimalist".
# That tile (make_ivy_tile.py, ~/Downloads/Minimalist Ivy Vine Divider.png) alternates
# normal and upside-down copies, and its zones end only on bare stem (cut_ok).

def unrolled():
    pts = [V(x, y, 0) for x, y in O]; n = len(pts); edges = []; s = 0.0
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]; L = (b - a).Length
        if L < 1e-6: continue
        t = (b - a) * (1.0 / L); nrm = V(t.y, -t.x, 0); mid = (a + b) * 0.5
        if inside_O(mid.x + nrm.x * 0.05, mid.y + nrm.y * 0.05): nrm = nrm * -1
        edges.append((a, t, nrm, s, s + L)); s += L
    return edges, s
def s_of(edges, x, y):
    p = V(x, y, 0); best = None
    for a, t, nrm, s0, s1 in edges:
        u = max(0.0, min(s1 - s0, (p - a).dot(t))); d = (a + t * u - p).Length
        if best is None or d < best[0]: best = (d, s0 + u)
    return best[1]

def wall_corners(edges, P):
    """(a, b, kind) for every stretch of wall between straight runs of >= 10 mm: "convex"
    for a plain rounded corner (a single 90 deg turn), "step" for a jog in the wall"""
    runs = []
    for a, t, nrm, s0, s1 in edges:
        if runs and (runs[-1][2] - nrm).Length < 1e-3: runs[-1][4] = s1
        else: runs.append([a, t, nrm, s0, s1])
    runs = [r for r in runs if r[4] - r[3] >= 10.0]
    out = []
    for i in range(len(runs)):
        r0, r1 = runs[i], runs[(i + 1) % len(runs)]
        a, b = r0[4], r1[3] + (P if i + 1 == len(runs) else 0)
        turn = r0[2].x * r1[2].y - r0[2].y * r1[2].x
        out.append((a, b, "convex" if abs(abs(turn) - 1) < 1e-3 and b - a < 10 else "step"))
    return out

def moon_band_face(edges, P, zc, zones):
    import sys
    sys.path.insert(0, os.path.expanduser("~/PCBs/lazydragon64/case-new-outline"))
    import moon_band as mb
    corners = wall_corners(edges, P)
    log("wall corners", [(round(a, 1), round(b, 1), c) for a, b, c in corners])
    steps = [(a, b) for a, b, c in corners if c == "step"]
    sun_open = MOON_SUN_OPEN * (1 if IVY_ONLY else -1)
    placed, summary = mb.layout(P, list(zones) + steps, corners, k=MOON_K, sun_open=sun_open, log=log)
    def prim(pr, w):
        if pr[0] == "c":
            return Part.Face(Part.Wire(Part.makeCircle(pr[3], V(pr[1] + w, zc + pr[2], 0))))
        q = [V(x + w, zc + y, 0) for x, y in pr[1]]
        return Part.Face(Part.makePolygon(q + [q[0]]))
    # Each element is merged as a thin solid and its base kept: fusing the flat faces
    # directly leaves e.g. every sun ray a separate face on top of the ring. Elements
    # never touch each other, so the band is just the compound of their bases.
    faces = []; islands = 0
    for s, kind, parts in placed:
        islands += mb.count_islands(kind)
        for w in (-P, 0.0, P):      # copies one wrap either side, like the ivy tiles
            sols = []
            for add, subs in parts:
                f = prim(add, w)
                if subs: f = f.cut([prim(x, w) for x in subs])
                sols += [g.extrude(V(0, 0, 1)) for g in f.Faces]
            u = sols[0].fuse(sols[1:]).removeSplitter() if len(sols) > 1 else sols[0]
            faces += [g for g in u.Faces if g.BoundBox.ZMax < 1e-6]
    band = Part.makeCompound(faces)
    Hb = 2 * MOON_K * mb.SUN_LONG_CARD + 1.0
    log("moon band: elements", len(placed), "islands", islands, "faces", len(band.Faces), "band height", round(Hb, 2))
    return band, Hb, islands

def ivy_pieces():
    t0 = time.time()
    edges, P = unrolled(); zc = (Z_BOTTOM + Z_RIM) / 2
    d = json.load(open(IVY_JSON)) if BAND == "ivy" else {"period_px": 1, "height_px": 1, "loops": []}   # moon: unused
    per = d["period_px"]
    ALT = d.get("alternate", False)            # make_ivy_tile.py: copies alternate normal / 180 deg
    if ALT:   # fewest copies (even, so the alternation closes round the wrap) that fit IVY_MAX_BAND
        N = next(n for n in range(2, 40, 2) if 2 * d["half_height_px"] * (P / n) / per <= IVY_MAX_BAND)
        L = P / N; k = L / per; Hb = 2 * d["half_height_px"] * k
    else:
        N = IVY_N; L = P / N; k = L / per; Hb = d["height_px"] * k
    # clear zones in s: the front text and the USB notch
    ytop = max(y for x, y in O)
    sc, sd = sorted((s_of(edges, NOTCH[0], ytop), s_of(edges, NOTCH[1], ytop)))
    need = [(sc - NOTCH_PAD, sd + NOTCH_PAD)]
    sa = sb = None
    if not IVY_ONLY:
        tb = text_solid(+1).BoundBox
        sa, sb = sorted((s_of(edges, tb.XMin, tb.YMax), s_of(edges, tb.XMax, tb.YMax)))
        need.insert(0, (sa - PLAQUE_PAD[0], sb + PLAQUE_PAD[0]))
    def orient(j): return ALT and j % 2 == 1   # rotated copy
    if BAND == "moon":
        zones = need; phase = 0.0; N = L = k = 0
    elif "cut_ok" in d:
        # End the vine only on bare-stem columns: each zone edge moves outwards to the
        # nearest column marked cut_ok, so no leaf is sliced and no fragment is left behind.
        ok = d["cut_ok"]
        def ok_at(s, ph):
            j = math.floor((s - ph) / L); u = (s - ph - j * L) / k
            col = int(round(per - u if orient(j) else u))
            return ok[min(max(col, 0), per)]
        def grow(s, ph, direction):
            for i in range(int(20.0 / k)):
                if ok_at(s + direction * i * k, ph): return i * k
            return None
        def zones_for(ph):
            out = []
            for lo, hi in need:
                a, b = grow(lo, ph, -1), grow(hi, ph, +1)
                if a is None or b is None: return None
                out.append((lo - a, hi + b, a + b))
            return out
        span = 2 * L if ALT else L
        phases = [float(IVY_PHASE)] if IVY_PHASE else [i * 0.25 for i in range(int(span / 0.25))]
        cands = [(sum(z[2] for z in zs), ph, zs) for ph in phases for zs in [zones_for(ph)] if zs]
        if not cands: raise SystemExit("no bare-stem cut for the zones at phase(s) %s" % phases[:4])
        extra, phase, zs = min(cands)
        zones = [(lo, hi) for lo, hi, _ in zs]
        log("ivy cut at bare stem: phase", phase, "zones grown by", round(extra, 2), "mm in total")
    else:
        # older border: put the cuts where the pattern has the least ink, +-0.6 mm
        ink = d["column_ink"]; win = max(1, int(0.6 / k))
        cuts = [c for z in need for c in z]
        def cost(ph):
            return sum(max(ink[(int(((sx - ph) % L) / k) + j) % per] for j in range(-win, win + 1)) for sx in cuts)
        phase = min((i * 0.25 for i in range(int(L / 0.25))), key=cost)
        zones = need
    n_expect = len(zones)
    if BAND == "moon":
        band, Hb, n_expect = moon_band_face(edges, P, zc, zones)
    else:
        log("ivy N", N, "L", round(L, 3), "band", round(Hb, 2), "k mm/px", round(k, 5), "phase", phase,
            "zones", [(round(a, 1), round(b, 1)) for a, b in zones])
        tiles = []
        for j in range(-2, N + 2):
            s0 = phase + j * L
            for lp in d["loops"]:
                if orient(j): q = [V(s0 + (per - u) * k, zc - v * k, 0) for u, v in lp]
                else: q = [V(s0 + u * k, zc + v * k, 0) for u, v in lp]
                tiles.append(Part.Face(Part.makePolygon(q + [q[0]])))
        band = tiles[0].fuse(tiles[1:]).removeSplitter() if len(tiles) > 1 else tiles[0]
    # zones repeated one wrap either side, since the tiles run past both ends of [0, P]
    clear = [Part.makePlane(hi - lo, Hb + 4, V(lo + w, zc - Hb / 2 - 2, 0)) for lo, hi in zones for w in (-P, 0, P)]
    band = band.cut(clear).removeSplitter()
    # Floating check over one full turn that starts inside the first zone, so no element
    # straddles the window's ends: every piece must be a whole stretch of vine between
    # two zones (one piece per zone), and none may be a scrap.
    m = (zones[0][0] + zones[0][1]) / 2
    turn = band.common(Part.makePlane(P, Hb + 4, V(m, zc - Hb / 2 - 2, 0)))
    areas = sorted((round(f.Area, 1) for f in turn.Faces), reverse=True)
    log("ivy band pieces over one turn (mm2):", areas, "expected", n_expect)
    if len(areas) != n_expect:
        log("WARNING: band pattern has", len(areas), "separate pieces, expected", n_expect)
    if os.environ.get("CASE_IVY_DRY") == "1":   # dump the unrolled band and stop
        json.dump({"P": P, "zc": zc, "Hb": Hb, "zones": zones, "text_s": [sa, sb], "notch_s": [sc, sd],
                   "start": m, "faces": [[[(p.x, p.y) for p in w.discretize(Deflection=0.02)] for w in f.Wires] for f in turn.Faces]},
                  open(os.path.join(OUT, "ivy_band.json"), "w"))
        raise SystemExit("ivy dry run")
    pieces = []
    n = len(edges)
    # Filled joints (2026-11-13). Each wall facet's strip of the band is extruded straight
    # out along that facet's own normal. On the rounded outside corners (6 deg per 0.63 mm
    # facet) neighbouring strips fan apart, which left a V slit ~0.08 mm wide through the
    # vine at every joint, the pieces touching only along a line at the wall. Each slit is
    # now filled with a wedge carrying the band's exact profile at that corner (where the
    # vertical line s = s_corner crosses ink). Both strips end on that same line, so the
    # wedge meets them face to face with matching outlines and nothing is left floating.
    # (Trimming the strips at the bisector planes instead left slivers floating: each
    # side then shows the vine from a little beyond the corner.) Inside corners overlap
    # rather than open, so they keep the 0.3 mm run-on. CASE_IVY_FILL=0 skips the wedges.
    def column(sc):   # z intervals where the band has ink on the vertical line s = sc
        cut = band.section(Part.makeLine(V(sc, zc - Hb, 0), V(sc, zc + Hb, 0)))
        iv = sorted((min(e.Vertexes[0].Point.y, e.Vertexes[-1].Point.y), max(e.Vertexes[0].Point.y, e.Vertexes[-1].Point.y))
                    for e in cut.Edges)
        out = []
        for lo, hi in iv:
            if out and lo <= out[-1][1] + 1e-6: out[-1][1] = max(out[-1][1], hi)
            else: out.append([lo, hi])
        return [(lo, hi) for lo, hi in out if hi - lo > 0.01]
    wedges = 0
    for i, (a, t, nrm, s0, s1) in enumerate(edges):
        e0 = 0.3 if t.dot(edges[i - 1][2]) > 0.05 else 0.0
        e1 = 0.3 if edges[(i + 1) % n][1].dot(nrm) > 0.05 else 0.0
        strip = Part.makePlane(s1 - s0 + e0 + e1, Hb + 4, V(s0 - e0, zc - Hb / 2 - 2, 0))
        part = band.common(strip)
        if part.Area >= 1e-4:
            part.translate(V(-s0, 0, 0))
            m = V(t.y, -t.x, 0); sg = 1 if m.dot(nrm) > 0 else -1
            sol = part.extrude(V(0, 0, sg * (IVY_RAISE + IVY_EMBED))); sol.translate(V(0, 0, -sg * IVY_EMBED))
            M = App.Matrix(t.x, 0, m.x, a.x, t.y, 0, m.y, a.y, 0, 1, 0, 0, 0, 0, 0, 1)
            sol.transformShape(M)
            pieces.extend(sol.Solids)
        # outside corner at the start of this facet: this wall turns away from the
        # previous wall's outward normal
        if IVY_FILL and t.dot(edges[i - 1][2]) < -1e-6:
            na = edges[i - 1][2]
            for lo, hi in column(s0):
                tri = [V(a.x, a.y, lo), V(a.x + na.x * IVY_RAISE, a.y + na.y * IVY_RAISE, lo),
                       V(a.x + nrm.x * IVY_RAISE, a.y + nrm.y * IVY_RAISE, lo)]
                pieces.append(Part.Face(Part.makePolygon(tri + [tri[0]])).extrude(V(0, 0, hi - lo)))
                wedges += 1
    log("ivy joint wedges", wedges)
    if os.environ.get("CASE_IVY_CHECK", "1") == "1":
        # 3D connectivity: every stretch of vine between two zones must be one solid. A
        # joint that only touches along a line (the old slits) splits it into several.
        t1 = time.time()
        # Count it only clear of the wall: inside the wall the strips overlap, which joined
        # the old slit pieces even though the raised vine was cut through at every joint.
        rel = pieces[0].fuse(pieces[1:]).removeSplitter()
        wall = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in O] + [V(O[0][0], O[0][1], 0)])).makeOffset2D(0.05)
        bb = wall.BoundBox
        outside = Part.makePlane(bb.XLength + 20, bb.YLength + 20, V(bb.XMin - 10, bb.YMin - 10, 0)).cut(wall)
        outside = outside.extrude(V(0, 0, Z_RIM - Z_BOTTOM + 20)); outside.translate(V(0, 0, Z_BOTTOM - 10))
        raised = rel.common(outside)
        vols = sorted((round(x.Volume, 3) for x in raised.Solids), reverse=True)
        log("ivy relief alone: solids", len(rel.Solids), "| raised part (>0.05 mm off the wall): solids", len(vols),
            "expected", n_expect, "smallest", vols[-5:], "valid", rel.isValid(), "t", round(time.time() - t1, 1))
        if os.environ.get("CASE_IVY_CHECK_ONLY") == "1": raise SystemExit("ivy check only")
    log("ivy pieces", len(pieces), "t", round(time.time() - t0, 1))
    return pieces

def add_ivy(shape, pieces):
    t0 = time.time()
    s = shape.fuse(pieces).removeSplitter()
    log("ivy fused valid", s.isValid(), "solids", len(s.Solids), "t", round(time.time() - t0, 1))
    return s

if IVY:
    variants = [(IVY_NAME, plain)]

# ---- export --------------------------------------------------------------
PFX = "Lucca58 Stagger New Outline Case" if MODE == "stagger" else "Regress Case"
mirror = lambda s: s.mirror(V(0, 0, 0), V(1, 0, 0))
def stats(me):
    return "solid %s nonmanifold %s selfint %d comps %d facets %d vol %.1f" % (
        me.isSolid(), me.hasNonManifolds(), len(me.getSelfIntersections()),
        len(me.getSeparateComponents()), me.CountFacets, me.Volume)
def good(me):
    return me.isSolid() and not me.hasNonManifolds() and len(me.getSelfIntersections()) == 0 and len(me.getSeparateComponents()) == 1
def mesh_of(shape):
    best = None; closed = None
    for d in (0.02, 0.01, 0.03, 0.05):
        me = Mesh.Mesh(shape.tessellate(d))
        log("  tess", d, stats(me))
        if good(me): return me
        if best is None: best = me
        if me.isSolid() and not me.hasNonManifolds() and len(me.getSeparateComponents()) == 1:
            if closed is None or len(me.getSelfIntersections()) < len(closed.getSelfIntersections()): closed = me
    if closed is not None:   # a closed mesh with a few crossing facets beats a repair that opens it
        log("  keeping closed tessellation", stats(closed))
        return closed
    me = best
    me.fixSelfIntersections(); me.removeDuplicatedPoints(); me.harmonizeNormals()
    log("  after fixSelfIntersections", stats(me))
    if good(me): return me
    bad = set()
    for a in me.getSelfIntersections(): bad.add(a[0]); bad.add(a[1])
    me.removeFacets(sorted(bad)); me.fillupHoles(20, 1)
    me.removeDuplicatedPoints(); me.harmonizeNormals()
    log("  after facet repair", stats(me))
    return me

for name, left in variants:
    if IVY:     # vine first, on the plain case; it has no handedness, so the right half
        #         inherits it by mirroring. Fusing the mirrored pieces onto the decorated
        #         right half instead once ran for 26+ minutes without finishing.
        left = add_ivy(left, ivy_pieces())
    r = mirror(left)
    if DECOR:   # decorate each half separately so the art and text are never mirrored
        left, r = decorate(left, +1), decorate(r, -1)
    elif IVY_ONLY_ART:
        left, r = engrave(left, +1), engrave(r, -1)
    out = os.path.join(OUT, PFX + " Left" + name)
    left.exportStep(out + ".step")
    me = mesh_of(left); me.write(out + ".stl")
    log(PFX + " Left" + name, stats(me), "GOOD" if good(me) else "NOT CLEAN")
    outr = os.path.join(OUT, PFX + " Right" + name)
    r.exportStep(outr + ".step")
    if DECOR or IVY_ONLY_ART:   # the drawing is not mirrored, so mesh the right half itself
        mr = mesh_of(r)
    else:
        mr = Mesh.Mesh(me)
        mr.transform(App.Matrix(-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))
        # A mirror reverses every facet's winding, so the copy is inside out until flipped.
        # (Mesh.Volume read positive either way, so the old "if Volume < 0" check never
        # fired and the vine-only right half STL came out inside out; fixed 2026-11-14.)
        mr.flipNormals()
    mr.write(outr + ".stl")
    log(PFX + " Right" + name, stats(mr), "GOOD" if good(mr) else "NOT CLEAN")
log("DONE windows", nwin)
