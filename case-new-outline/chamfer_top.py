# Chamfer the outer top edge of a finished case. Run:
#   CASE_IN="in.step" CASE_OUT="out" freecadcmd -c "exec(open('chamfer_top.py').read())"
# writes out.step and out.stl. CASE_CHAMFER sets the size (mm, 45 deg; default 1.0).
#
# 2026-11-16: works on the finished STEP rather than inside build_case.py, so the
# chamfered case is the finished one with only that edge changed (same vine or moon
# band, text, dragon, screw recesses and standoff pockets). Only the edge where the
# outer wall meets the rim top is chamfered; the inner top edge and every bottom edge
# stay square. The wall decorations stop below the chamfer: the Ivy Curl band reaches
# z = 13.87 (16.63 mm tall about z = 5.55) and the moon band's sun rays z = 12.08 (12.59
# before 2026-11-28), while
# a 1 mm chamfer starts at z = 14.1. Above CASE_CHAMFER = 1.2 it would cut the ivy.
import os, time
import FreeCAD as App, Part, Mesh
from FreeCAD import Vector as V

SRC, OUT = os.environ["CASE_IN"], os.environ["CASE_OUT"]
C = float(os.environ.get("CASE_CHAMFER", "1.0"))
Z_RIM, Z_OUTLINE = 15.1, -3.1      # rim top; a height where the outer wall is plain
LOG = open(os.environ.get("CASE_LOG", os.devnull), "w")
def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()

t0 = time.time()
shape = Part.Shape(); shape.read(SRC)
assert len(shape.Solids) == 1, "expected one solid, got %d" % len(shape.Solids)
solid = shape.Solids[0]
# The outer wall is a straight-sided prism on a polygon (build_case.py builds it from
# one), so the chamfer is cut as a solid: everything outside a 45 deg "frustum" whose
# side passes through the wall at Z_RIM - C and lies C inside it at Z_RIM. (OCC's
# makeChamfer on the 148 short top edges fails with BRep_API: command not done.)
outer = max(solid.slice(V(0, 0, 1), Z_OUTLINE), key=lambda w: w.BoundBox.DiagonalLength)
P = [(v.Point.x, v.Point.y) for v in outer.OrderedVertexes]
area = sum(P[i - 1][0] * P[i][1] - P[i][0] * P[i - 1][1] for i in range(len(P))) / 2
if area < 0: P.reverse()                       # counter-clockwise, so "left" is inward
def offset(d):
    """the outline moved d inwards with mitred corners: one point per original vertex.
    A segment too short to survive the move (the rounded step corners come as
    alternating 0.04 / 0.27 mm segments) is dropped and its neighbours' lines meet
    instead, so both its ends land on the same point."""
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
# The cutter's foot is the wall outline itself at Z_RIM - C, so every chamfer face meets
# its wall facet exactly; at the top it runs D past the rim.
D = 0.2
lo, _ = offset(0.0)
hi, dropped = offset(C + D)
z0, z1 = Z_RIM - C, Z_RIM + D
pts_lo = [V(x, y, z0) for x, y in lo]; pts_hi = [V(x, y, z1) for x, y in hi]
faces = [Part.Face(Part.makePolygon(pts_lo + [pts_lo[0]]))]
top = [pts_hi[0]] + [q for k, q in enumerate(pts_hi[1:], 1) if (q - pts_hi[k - 1]).Length > 1e-9]
if (top[-1] - top[0]).Length < 1e-9: top.pop()
faces.append(Part.Face(Part.makePolygon(top + [top[0]])))
for i in range(len(P)):
    j = (i + 1) % len(P)
    if (pts_hi[i] - pts_hi[j]).Length < 1e-9:
        faces.append(Part.Face(Part.makePolygon([pts_lo[i], pts_lo[j], pts_hi[i], pts_lo[i]])))
    else:
        faces.append(Part.Face(Part.makePolygon([pts_lo[i], pts_lo[j], pts_hi[j], pts_hi[i], pts_lo[i]])))
shell = Part.Shell(faces); shell.sewShape()          # faces share their edges only once sewn
frustum = Part.Solid(shell)
if frustum.Volume < 0: frustum.reverse()
log("outline", len(P), "vertices, length %.2f; %d short segments close up at the top; frustum valid %s vol %.1f"
    % (outer.Length, dropped, frustum.isValid(), frustum.Volume))
assert frustum.isValid(), "frustum invalid"
if os.environ.get("CASE_CHAMFER_DRY") == "1": raise SystemExit("frustum ok")
bb = solid.BoundBox
box = Part.makeBox(bb.XLength + 20, bb.YLength + 20, C + 1.0, V(bb.XMin - 10, bb.YMin - 10, Z_RIM - C))
cutter = box.cut(frustum)
res = solid.cut(cutter).removeSplitter()
removed = solid.Volume - res.Volume
# the chamfer's cross-section is C^2/2 wherever there is wall at the top
log("chamfer %.2f mm: valid %s solids %d, removed %.2f mm3 (C^2/2 x outline = %.2f, less the USB notch), t %.1f"
    % (C, res.isValid(), len(res.Solids), removed, C * C / 2 * outer.Length, time.time() - t0))
assert res.isValid() and len(res.Solids) == 1, "chamfer failed"

# nothing below the chamfer may change: compare the volume of the top slab
slab = Part.makeBox(1000, 1000, 2.5, V(-500, -500, Z_RIM - 2.4))
d_slab = solid.common(slab).Volume - res.common(slab).Volume
log("volume change inside the top %.1f mm: %.4f mm3, everywhere: %.4f mm3 -> rest unchanged: %s"
    % (2.4 + 0.1, d_slab, removed, abs(d_slab - removed) < 1e-3))

res.exportStep(OUT + ".step")

# STL, with the same mesh checks as build_case.py
def stats(me):
    return "solid %s nonmanifold %s selfint %d comps %d facets %d vol %.1f" % (
        me.isSolid(), me.hasNonManifolds(), len(me.getSelfIntersections()),
        len(me.getSeparateComponents()), me.CountFacets, me.Volume)
def good(me):
    return me.isSolid() and not me.hasNonManifolds() and len(me.getSelfIntersections()) == 0 and len(me.getSeparateComponents()) == 1
best = closed = None
for d in (0.02, 0.01, 0.03, 0.05):
    me = Mesh.Mesh(res.tessellate(d))
    log("  tess", d, stats(me))
    if good(me): best = me; break
    if me.isSolid() and not me.hasNonManifolds() and len(me.getSeparateComponents()) == 1:
        if closed is None or len(me.getSelfIntersections()) < len(closed.getSelfIntersections()): closed = me
if best is None and closed is not None:
    # As in build_case.py: a closed mesh with a few crossing facets beats a repair that
    # opens it. On the Ivy Curl cases two facet pairs cross where the vine turns the back
    # wall's step corners (the same happens meshing the unchamfered case-final STEP);
    # each crossing is about 0.0001 mm long, far below anything a slicer resolves.
    for pr in closed.getSelfIntersections():
        pts = [x for x in pr if not isinstance(x, int)]
        log("  crossing at", tuple(round(c, 3) for c in pts[0]), "length %.5f mm" % (pts[0] - pts[1]).Length)
    best = closed
if best is None: raise SystemExit("no closed tessellation")
best.write(OUT + ".stl")
log(os.path.basename(OUT), stats(best), "GOOD" if good(best) else "CLOSED (crossings listed above)", "t %.1f" % (time.time() - t0))
