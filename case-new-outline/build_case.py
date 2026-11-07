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
#   CASE_LOG   log file (default: none)
import os, math, time
import FreeCAD as App, Part, Mesh
from FreeCAD import Vector as V

SRC = os.environ.get("CASE_SRC", os.path.expanduser("~/PCBs/Lucca58/case"))
OUT = os.environ.get("CASE_OUT", os.path.expanduser("~/PCBs/lazydragon64/case-new-outline"))
MODE = os.environ.get("CASE_MODE", "stagger")
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
    # standoffs
    block = sorted(range(len(HEX)), key=lambda k: centre(HEX[k]))
    block = [k for k in block if centre(HEX[k])[0] < X_BLOCK]
    assert len(block) == len(NEW_STANDOFFS), len(block)
    def nearest(lst, c):
        return min(range(len(lst)), key=lambda k: math.hypot(centre(lst[k])[0] - c[0], centre(lst[k])[1] - c[1]))
    targets = [(px + TX, -py + TY) for px, py in NEW_STANDOFFS]
    for k, t in zip(block, targets):
        c = centre(HEX[k])
        h = nearest(HOLE, c); r = nearest(RING, c)
        dx, dy = t[0] - c[0], t[1] - c[1]
        log("standoff", [round(v, 3) for v in c], "->", [round(v, 3) for v in t])
        HEX[k] = [(x + dx, y + dy) for x, y in HEX[k]]
        HOLE[h] = [(x + dx, y + dy) for x, y in HOLE[h]]
        RING[r] = [(x + dx, y + dy) for x, y in RING[r]]

# ---- build ---------------------------------------------------------------
def face(poly):
    pts = [V(x, y, 0) for x, y in poly]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))
def prism(poly, z0, z1):
    s = face(poly).extrude(V(0, 0, z1 - z0)); s.translate(V(0, 0, z0)); return s

def base():
    s = prism(O, Z_BOTTOM, Z_RIM)
    s = s.cut(prism(I, Z_FLOOR, Z_RIM + 1))
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

t0 = time.time()
cler, nwin = clerestory(plain)
log("clerestory time", round(time.time() - t0, 1))

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
    best = None
    for d in (0.02, 0.01, 0.03, 0.05):
        me = Mesh.Mesh(shape.tessellate(d))
        log("  tess", d, stats(me))
        if good(me): return me
        if best is None: best = me
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

for name, left in (("", plain), (" Clerestory", cler)):
    out = os.path.join(OUT, PFX + " Left" + name)
    left.exportStep(out + ".step")
    me = mesh_of(left); me.write(out + ".stl")
    log(PFX + " Left" + name, stats(me), "GOOD" if good(me) else "NOT CLEAN")
    r = mirror(left)
    outr = os.path.join(OUT, PFX + " Right" + name)
    r.exportStep(outr + ".step")
    mr = Mesh.Mesh(me)
    mr.transform(App.Matrix(-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))
    mr.harmonizeNormals()
    if mr.Volume < 0: mr.flipNormals()
    mr.write(outr + ".stl")
    log(PFX + " Right" + name, stats(mr), "GOOD" if good(mr) else "NOT CLEAN")
log("DONE windows", nwin)
