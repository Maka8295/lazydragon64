# Emboss an Art Deco fan pattern over the whole top rim of a finished case STEP.
#   freecadcmd -c "import sys; sys.argv=['x', IN_STEP, OUT_BASE]; exec(open('add_rim_pattern.py').read())"
# writes OUT_BASE.step and OUT_BASE.stl. RIM_PREVIEW=1 only writes OUT_BASE_pattern.json (2D).
# The pattern is rebuilt as geometry from the reference (fan period 338 px, arch radius
# 178 px, row pitch 162 px, alternate rows offset half a fan), with printable widths and
# fewer rays. Each arch is a circle drawn as a thick arc. The rays of a fan run from the
# point where the two arches in front of it meet up to its own arch. Rows lower down sit
# in front, so each fan is clipped by the three circles in front of it. Fans open
# towards the back of the case. The pattern is clipped to the rim top (inset INSET).
import FreeCAD as App, Part, Mesh, math, sys, os, time, json
from FreeCAD import Vector as V
IN, OUTB = sys.argv[1], sys.argv[2]
FAN_W = float(os.environ.get("RIM_FAN_W", "6.0"))       # mm, fan width (horizontal period)
R_RATIO, H_RATIO = 178 / 338, 162 / 338                 # arch radius and row pitch, per fan width
ARC_W, RAY_W, N_RAYS = 0.7, 0.4, 9                      # mm, mm, rays per fan (odd: one is vertical)
HUB_R = 0.45                                            # mm, solid hub where a fan's rays meet
RAISE, EMBED = 0.5, 0.2                                  # mm
INSET = float(os.environ.get("RIM_INSET", "0"))         # mm plain margin along both rim edges (0 = cover the whole rim)
t0 = time.time()
case = Part.Shape(); case.read(IN)
case = case.Solids[0] if len(case.Solids) == 1 else case
ztop = case.BoundBox.ZMax
tops = [f for f in case.Faces if abs(f.BoundBox.ZMin - ztop) < 1e-4 and abs(f.BoundBox.ZMax - ztop) < 1e-4]
rim = tops[0] if len(tops) == 1 else tops[0].fuse(tops[1:]).removeSplitter()
rim2d = rim.copy(); rim2d.translate(V(0, 0, -ztop))
inner = rim2d.makeOffset2D(-INSET) if INSET > 0 else rim2d
bb = rim2d.BoundBox
P = FAN_W; r = P * R_RATIO; h = P * H_RATIO
cusp = math.sqrt(r * r - (P / 2) ** 2)                  # height of a row's meeting points above its centres
x0 = (bb.XMin + bb.XMax) / 2; y0 = bb.YMin
Z0, Z1 = ztop - EMBED, ztop + RAISE
def disk(c, rad): return Part.Face(Part.Wire(Part.makeCircle(rad, V(c[0], c[1], 0))))
def prism(face):
    s = face.extrude(V(0, 0, Z1 - Z0)); s.translate(V(0, 0, Z0)); return s
def cyl(c, rad): return Part.makeCylinder(rad, Z1 - Z0 + 2, V(c[0], c[1], Z0 - 1))
def centre(i, j): return (x0 + i * P + (P / 2 if j % 2 else 0), y0 + j * h)
# Everything is built as solids. A 2D union left each fan as ~39 abutting faces, and
# dropping the small ones opened gaps where the rays converge. Those gaps were the 1648
# open edges in every STL. Solid unions merge properly.
def content(i, j):
    a = centre(i, j)
    ring = disk(a, r + ARC_W / 2).cut(disk(a, r - ARC_W / 2))
    upper = Part.makePlane(4 * r, 2 * r, V(a[0] - 2 * r, a[1], 0))
    faces = [ring.common(upper)]
    T = (a[0], a[1] - h + cusp)                         # where the two arches in front meet
    dy0 = T[1] - a[1]
    th_max = math.radians(62)
    for k in range(N_RAYS):
        th = math.pi / 2 - th_max + 2 * th_max * k / (N_RAYS - 1)
        ux, uy = math.cos(th), math.sin(th)
        bq = dy0 * uy; L = -bq + math.sqrt(bq * bq - (dy0 * dy0 - r * r))   # T + L*u lands on the arch
        nx, ny = -uy * RAY_W / 2, ux * RAY_W / 2
        p = [V(T[0] + nx, T[1] + ny, 0), V(T[0] + L * ux + nx, T[1] + L * uy + ny, 0),
             V(T[0] + L * ux - nx, T[1] + L * uy - ny, 0), V(T[0] - nx, T[1] - ny, 0)]
        faces.append(Part.Face(Part.makePolygon(p + [p[0]])))
    faces.append(disk(T, HUB_R))                        # solid hub where the rays meet
    sols = [prism(f) for f in faces]
    sh = sols[0].fuse(sols[1:]).removeSplitter()
    fl = (a[0] - P / 2, a[1] - h); fr = (a[0] + P / 2, a[1] - h); fb = (a[0], a[1] - 2 * h)
    # rows in front hide this fan; clip at their centre-lines so the strokes overlap
    return sh.cut([cyl(c, r) for c in (fl, fr, fb)]).removeSplitter()
# fans whose circle reaches the rim
cells = []
for j in range(-2, int((bb.YMax - y0) / h) + 3):
    for i in range(int((bb.XMin - x0) / P) - 2, int((bb.XMax - x0) / P) + 3):
        c = centre(i, j)
        if inner.distToShape(Part.Vertex(V(c[0], c[1], 0)))[0] <= r + ARC_W: cells.append((i, j))
print("fans touching the rim:", len(cells), "t", round(time.time() - t0, 1)); sys.stdout.flush()
pieces = [content(i, j) for i, j in cells]
pat = pieces[0].fuse(pieces[1:]).removeSplitter()
pat = pat.common(prism(inner)).removeSplitter()
# scraps where the pattern meets the rim edges, too small to print: drop whole solids only
keep = [sol for sol in pat.Solids if sol.Volume >= 0.08 * (Z1 - Z0)]
print("pattern solids", len(pat.Solids), "kept", len(keep), "top area", round(sum(sol.Volume for sol in keep) / (Z1 - Z0), 1),
      "rim area", round(rim2d.Area, 1), "t", round(time.time() - t0, 1)); sys.stdout.flush()
if os.environ.get("RIM_PREVIEW") == "1":
    tops = [f for sol in keep for f in sol.Faces if abs(f.BoundBox.ZMin - Z1) < 1e-6 and abs(f.BoundBox.ZMax - Z1) < 1e-6]
    json.dump({"rim": [[(p.x, p.y) for p in w.discretize(Deflection=0.02)] for w in rim2d.Wires],
               # outer boundary first: after booleans f.Wires[0] is not always the outer one
               "faces": [[[(p.x, p.y) for p in w.discretize(Deflection=0.01)]
                          for w in [f.OuterWire] + [w for w in f.Wires if not w.isSame(f.OuterWire)]] for f in tops]},
              open(OUTB + "_pattern.json", "w"))
    raise SystemExit("preview written")
res = case.fuse(keep).removeSplitter()
print("fused valid", res.isValid(), "solids", len(res.Solids), "t", round(time.time() - t0, 1)); sys.stdout.flush()
res.exportStep(OUTB + ".step")
def good(me):
    return me.isSolid() and not me.hasNonManifolds() and len(me.getSeparateComponents()) == 1
best = None
for d in (0.02, 0.01, 0.03):
    me = Mesh.Mesh(res.tessellate(d)); si = len(me.getSelfIntersections())
    print("  tess", d, "closed", good(me), "selfint", si); sys.stdout.flush()
    if good(me) and (best is None or si < best[0]): best = (si, me)
    if good(me) and si == 0: break
(best[1] if best else me).write(OUTB + ".stl")
print("done", "t", round(time.time() - t0, 1))
