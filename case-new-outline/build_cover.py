# Top covers for the Lazy Dragon 64 cases. Run:
#   COVER_OUT=<folder> freecadcmd -c "exec(open('build_cover.py').read())"
# writes "lazydragon64 Cover Left/Right" .step and .stl into COVER_OUT.
#
# 2026-11-26. A lid that rests on the case rim (Z 15.1) and closes over the keys:
# - Walls and top on the case's own outline: the outside and the inside of its walls
#   carry straight on up, so the lid sits flush with the case all round (the chamfered
#   cases' 1 mm top chamfer is ignored). Its underside is one flat, unbroken rim: nothing
#   reaches down into the case, and over the USB notch the rim just runs across (the
#   notch stays open below it).
# - Inside height for XDA caps: MX stem top ~11.6 mm above the plate (plate top Z 8.1),
#   an XDA cap reaches ~4.6 mm above that, so the caps' tops are at about Z 24.3. The
#   ceiling is at Z 27.0, ~2.7 mm clear (COVER_CEIL).
# - The outer top edge is chamfered 1 mm x 45 deg, like the chamfered cases (same method as
#   chamfer_top.py).
# - Plain walls. COVER_WINDOWS=1 adds the gothic windows (taken off 2026-11-26): the window from ~/Downloads/window.png (window_art.json), raised 0.8 mm on the outer
#   walls like the cases' ivy, 0.4 mm above the rim and stopping 0.2 mm below the chamfer
#   (as the ivy stops below the case's), every window whole and centred on a straight run of wall
#   (cover_art.window_layout); the rounded corners and the short jogs stay bare.
# - The Lazy Dragon drawing engraved 0.6 mm into the top, as large as it fits 3 mm inside
#   the edge, with the coin pile simplified (cover_art.dragon_simplified) and every coin
#   redrawn as a clean oval (cover_art.coins_redrawn). Each lid gets its own unmirrored copy.
# Print each lid top-down: the drawing is then on the first layer, like the case undersides,
# and nothing needs support.
import os, sys, time, json, math, re
import FreeCAD as App, Part, Mesh
from FreeCAD import Vector as V
HERE = os.path.expanduser("~/PCBs/lazydragon64/case-new-outline")
sys.path.insert(0, HERE)
import importlib, cover_art; importlib.reload(cover_art)
from cover_art import polys, window, dragon_raw, fit_dragon, dragon_simplified, coins_redrawn, window_layout, mitred_offset
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity

OUT = os.environ.get("COVER_OUT", os.path.expanduser("~/PCBs/lazydragon64/case-final/cover"))
LOG = open(os.environ.get("COVER_LOG", os.devnull), "w")
def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()

CASE = os.path.join(HERE, "Lucca58 Stagger New Outline Case Left.step")   # plain left case
PCB = os.path.expanduser("~/PCBs/lazydragon64/lazydragon64.kicad_pcb")
TX, TY = -8.023, 7.669                     # KiCad (x, y) -> case (x + TX, -y + TY)
Z_FLOOR, Z_RIM, Z_PLATE_TOP = -1.0, 15.1, 8.1
Z_CEIL = float(os.environ.get("COVER_CEIL", "27.0"))
TOP = 2.4                                  # lid thickness over the keys
Z_TOP = Z_CEIL + TOP
NOTCH = (183.265, 197.715)                 # USB notch, case x
CAP_1U, CAP_15U = 18.2, 27.3               # XDA keycaps
CHAMFER = 1.0
WIN_BOTTOM, WIN_TOP_GAP = 0.4, 0.2         # window clear of the rim, and of the chamfer
WINDOWS = os.environ.get("COVER_WINDOWS", "0") == "1"
WIN_H = Z_TOP - CHAMFER - WIN_TOP_GAP - (Z_RIM + WIN_BOTTOM)
WIN_GAP, WIN_RAISE, WIN_EMBED = 2.4, 0.8, 0.3
ART_DEPTH, ART_MARGIN = 0.6, 3.0
os.makedirs(OUT, exist_ok=True)
t0 = time.time()

# ---- the case's outline, cavity and notch ---------------------------------------------
src = Part.Shape(); src.read(CASE)
def ring(w): return [(p.x, p.y) for p in w.discretize(Deflection=0.005)]
O = Polygon(ring(max(src.slice(V(0, 0, 1), -2.0), key=lambda w: w.BoundBox.DiagonalLength))).buffer(0)
WALL = Polygon(ring(src.slice(V(0, 0, 1), Z_RIM - 0.2)[0])).buffer(0)
R = O.difference(WALL)                     # cavity, plus the notch where the wall is cut away
y_in = max(WALL.intersection(box(NOTCH[0] - 1.0, -60, NOTCH[0] - 0.05, -30)).bounds[1],
           WALL.intersection(box(NOTCH[1] + 0.05, -60, NOTCH[1] + 1.0, -30)).bounds[1])
y_out = O.intersection(box(NOTCH[0] + 1, -60, NOTCH[1] - 1, 0)).bounds[3]
CAV = max(polys(R.difference(box(NOTCH[0] - 0.01, y_in + 1e-4, NOTCH[1] + 0.01, 0)).buffer(0)), key=lambda p: p.area)
log("outline", [round(c, 3) for c in O.bounds], "perimeter", round(O.length, 2), "cavity", round(CAV.area, 1),
    "notch wall y", round(y_in, 3), "to", round(y_out, 3))

# ---- keycaps: a check that they are all inside the lid ----------------------------------
pcb = open(PCB).read()
def footprints(pat):
    for m in re.finditer(r'\n\t\(footprint "(%s)"' % pat, pcb):
        seg = pcb[m.start():]; e = seg.find("\n\t(footprint", 5); yield m.group(1), seg[:e if e > 0 else None]
def to_case(seg, lx, ly):
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', seg)
    ax, ay, t = float(at.group(1)), float(at.group(2)), math.radians(float(at.group(3) or 0))
    return ax + lx * math.cos(t) + ly * math.sin(t) + TX, -(ay - lx * math.sin(t) + ly * math.cos(t)) + TY
caps = []
for name, seg in footprints(r'parts:hotswap_reversible[^"]*'):
    h = re.search(r'\(pad "" np_thru_hole circle\s*\(at ([-\d.]+) ([-\d.]+)[^)]*\)\s*\(size 4 4\)', seg)
    x, y = to_case(seg, float(h.group(1)), float(h.group(2)))
    hw = (CAP_15U if name.endswith("1.5U") else CAP_1U) / 2
    caps.append(box(x - hw, y - CAP_1U / 2, x + hw, y + CAP_1U / 2))
assert len(caps) == 32 and CAV.contains(unary_union(caps)), "keycaps don't fit the cavity"
log("keycaps", len(caps), "closest to the wall %.3f" % min(CAV.exterior.distance(c) for c in caps))

# ---- 2D parts -----------------------------------------------------------------------------
WIN, WIN_W = window(WIN_H)
layout = window_layout(O, WIN_W, WIN_GAP)
log("window %.2f x %.2f mm, %d holes, %d windows; runs:" % (WIN_W, WIN_H, len(WIN.interiors), len(layout)),
    sorted({(round(L, 2), n, round(L / n - WIN_W, 2)) for _, _, L, n in layout}, reverse=True))
RAW = dragon_raw()

# ---- solids ---------------------------------------------------------------------------------
def wire(c):
    pts = [V(x, y, 0) for x, y in c]
    if (pts[0] - pts[-1]).Length > 1e-9: pts.append(pts[0])
    return Part.makePolygon(pts)
def face(g):
    fs = []
    for p in polys(g):
        f = Part.Face(wire(p.exterior.coords))
        if p.interiors: f = f.cut([Part.Face(wire(h.coords)) for h in p.interiors])
        fs += f.Faces
    return fs
def prism(g, z0, z1):
    sols = []
    for f in face(g):
        s = f.extrude(V(0, 0, z1 - z0)); s.translate(V(0, 0, z0)); sols.append(s)
    return sols[0] if len(sols) == 1 else Part.makeCompound(sols)

body = prism(O, Z_RIM, Z_TOP).cut(prism(CAV, Z_RIM - 1, Z_CEIL))
# chamfer: cut away everything outside a 45 deg frustum whose foot is the outline at
# Z_TOP - CHAMFER and whose top lies CHAMFER (+ D) inside it, D above the top
P = [c for c in O.exterior.coords][:-1]
if O.exterior.is_ccw is False: P.reverse()
D = 0.2
lo, _ = mitred_offset(P, 0.0); hi, dropped = mitred_offset(P, CHAMFER + D)
pl = [V(x, y, Z_TOP - CHAMFER) for x, y in lo]; ph = [V(x, y, Z_TOP + D) for x, y in hi]
fr = [Part.Face(wire(lo))]
top = [ph[0]] + [q for k, q in enumerate(ph[1:], 1) if (q - ph[k - 1]).Length > 1e-9]
if (top[-1] - top[0]).Length < 1e-9: top.pop()
fr.append(Part.Face(Part.makePolygon(top + [top[0]])))
for i in range(len(P)):
    j = (i + 1) % len(P)
    if (ph[i] - ph[j]).Length < 1e-9: fr.append(Part.Face(Part.makePolygon([pl[i], pl[j], ph[i], pl[i]])))
    else: fr.append(Part.Face(Part.makePolygon([pl[i], pl[j], ph[j], ph[i], pl[i]])))
for f in fr[:1]: f.translate(V(0, 0, Z_TOP - CHAMFER))
shell = Part.Shell(fr); shell.sewShape(); frustum = Part.Solid(shell)
if frustum.Volume < 0: frustum.reverse()
assert frustum.isValid(), "chamfer frustum invalid"
bb = body.BoundBox
cutter = Part.makeBox(bb.XLength + 20, bb.YLength + 20, CHAMFER + 1.0, V(bb.XMin - 10, bb.YMin - 10, Z_TOP - CHAMFER)).cut(frustum)
v0 = body.Volume; body = body.cut(cutter).removeSplitter()
log("chamfer %.1f mm: removed %.2f mm3 (C^2/2 x perimeter = %.2f), %d short segments close up, valid %s"
    % (CHAMFER, v0 - body.Volume, CHAMFER ** 2 / 2 * O.length, dropped, body.isValid()))
# windows: built flat (x along the wall, y up, z out of the wall), then stood on the wall
inside = lambda x, y: O.contains(Polygon([(x - 1e-3, y - 1e-3), (x + 1e-3, y - 1e-3), (x, y + 1e-3)]))
wsol = Part.Face(wire(WIN.exterior.coords)).cut([Part.Face(wire(h.coords)) for h in WIN.interiors])
wsol = wsol.extrude(V(0, 0, WIN_RAISE + WIN_EMBED)); wsol.translate(V(0, 0, -WIN_EMBED))
z_sill = Z_RIM + WIN_BOTTOM
wins = []
for c, t, L, n in (layout if WINDOWS else []):
    nrm = (t[1], -t[0])
    if inside(c[0] + nrm[0] * 0.05, c[1] + nrm[1] * 0.05): nrm = (-nrm[0], -nrm[1])
    u = t if (t[1] * nrm[0] - t[0] * nrm[1]) > 0 else -t     # keep (along, up, out) right-handed
    M = App.Matrix(u[0], 0, nrm[0], c[0], u[1], 0, nrm[1], c[1], 0, 1, 0, z_sill, 0, 0, 0, 1)
    w = wsol.copy(); w.transformShape(M, True); wins.append(w)
log("parts ready t %.1f" % (time.time() - t0))
left = body.fuse(wins).removeSplitter() if wins else body
log("windows", len(wins))
log("left body valid", left.isValid(), "solids", len(left.Solids), "vol %.1f" % left.Volume, "t %.1f" % (time.time() - t0))
assert len(left.Solids) == 1 and left.isValid()

def engrave(shape, outline, tag):
    s, cx, cy = fit_dragon(outline, RAW, ART_MARGIN)
    art, n = coins_redrawn(dragon_simplified(RAW, s), s)
    log(tag, "coins: %d engraved solid, %d redrawn as ovals, %d left as drawn" % tuple(n))
    art = affinity.translate(art, cx, cy)
    assert outline.buffer(-ART_MARGIN + 0.5).contains(art)
    tool = prism(art, Z_TOP - ART_DEPTH, Z_TOP + 0.5)
    t1 = time.time()
    res = shape.cut(tool).removeSplitter()
    log(tag, "dragon scale %.4f (%.1f x %.1f mm) centre (%.2f, %.2f), %d pieces, engraved area %.1f mm2"
        % (s, art.bounds[2] - art.bounds[0], art.bounds[3] - art.bounds[1], cx, cy, len(polys(art)), art.area),
        "| valid", res.isValid(), "solids", len(res.Solids), "t %.1f" % (time.time() - t1))
    assert len(res.Solids) == 1 and res.isValid()
    return res, art

right = left.mirror(V(0, 0, 0), V(1, 0, 0))     # the right case is the left one mirrored in x = 0
left, art_l = engrave(left, O, "left")
right, art_r = engrave(right, affinity.scale(O, -1, 1, origin=(0, 0)), "right")

# ---- export, with the same mesh checks as the case builds ------------------------------------
def stats(me):
    return "solid %s nonmanifold %s selfint %d comps %d facets %d vol %.1f" % (
        me.isSolid(), me.hasNonManifolds(), len(me.getSelfIntersections()),
        len(me.getSeparateComponents()), me.CountFacets, me.Volume)
def good(me):
    return me.isSolid() and not me.hasNonManifolds() and len(me.getSelfIntersections()) == 0 and len(me.getSeparateComponents()) == 1
for tag, shape in (("Left", left), ("Right", right)):
    out = os.path.join(OUT, "lazydragon64 Cover " + tag)
    shape.exportStep(out + ".step")
    best = None
    for d in (0.02, 0.01, 0.03, 0.05):
        me = Mesh.Mesh(shape.tessellate(d)); log("  tess", d, stats(me))
        if good(me): best = me; break
    if best is None: raise SystemExit("no clean tessellation for " + tag)
    best.write(out + ".stl")
    bb = shape.BoundBox
    log("Cover", tag, stats(best), "GOOD | bbox %.2f x %.2f x %.2f" % (bb.XLength, bb.YLength, bb.ZLength),
        "| PLA at 1.24 g/cm3, solid: %.0f g" % (shape.Volume * 1.24e-3))
json.dump({"z": {"rim": Z_RIM, "ceil": Z_CEIL, "top": Z_TOP, "sill": z_sill},
           "outline": list(O.exterior.coords), "windows": [[list(c), list(t)] for c, t, _, _ in layout],
           "window_w": WIN_W}, open(os.path.join(OUT, "cover_layout.json"), "w"))
log("DONE t %.1f" % (time.time() - t0))
