# Fill the engraved bottom drawing back in on a finished case. Run:
#   CASE_IN="in.step" CASE_OUT="out" freecadcmd -c "exec(open('fill_art.py').read())"
# writes out.step and out.stl.
#
# 2026-11-25: the Lucca58 source STEPs that build_case.py reads (~/PCBs/Lucca58/case)
# are gone, so a plain-bottomed case can't be rebuilt. This works on the finished STEP
# instead: the drawing is engraved ART_DEPTH (0.6 mm) straight up into the bottom face,
# so its pockets are exactly the downward faces at Z_BOTTOM + 0.6 pushed down 0.6 mm.
# Those prisms are fused back on. Nothing else is at that height (the screw recesses'
# ceilings are at +1.3), and the script checks the volume added equals ceiling area x 0.6.
import os, time
import FreeCAD as App, Part, Mesh
from FreeCAD import Vector as V

SRC, OUT = os.environ["CASE_IN"], os.environ["CASE_OUT"]
ART_DEPTH = 0.6
LOG = open(os.environ.get("CASE_LOG", os.devnull), "w")
def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()

t0 = time.time()
shape = Part.Shape(); shape.read(SRC)
assert len(shape.Solids) == 1, "expected one solid, got %d" % len(shape.Solids)
solid = shape.Solids[0]
zb = solid.BoundBox.ZMin
ceil = [f for f in solid.Faces
        if f.BoundBox.ZLength < 1e-6 and abs(f.BoundBox.ZMin - (zb + ART_DEPTH)) < 1e-3]
area = sum(f.Area for f in ceil)
log("ceiling faces", len(ceil), "area %.2f mm2" % area)
assert ceil, "no engraving found at Z_BOTTOM + %.1f" % ART_DEPTH
plugs = [f.extrude(V(0, 0, -ART_DEPTH)) for f in ceil]
res = solid.fuse(plugs).removeSplitter()
assert len(res.Solids) == 1 and res.isValid(), "fuse gave %d solids, valid %s" % (len(res.Solids), res.isValid())
res = res.Solids[0]
added = res.Volume - solid.Volume
log("volume added %.3f mm3, expected %.3f -> %s" % (added, area * ART_DEPTH, abs(added - area * ART_DEPTH) < 0.05))
left = [f for f in res.Faces if f.BoundBox.ZLength < 1e-6 and abs(f.BoundBox.ZMin - (zb + ART_DEPTH)) < 1e-3]
log("faces left at the engraving height", len(left))
assert not left, "engraving not fully filled"
res.exportStep(OUT + ".step")

# STL, with the same mesh checks as chamfer_top.py / build_case.py
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
    # the vine's two known ~0.0001 mm facet crossings at the back wall's step corners
    for pr in closed.getSelfIntersections():
        pts = [x for x in pr if not isinstance(x, int)]
        log("  crossing at", tuple(round(c, 3) for c in pts[0]), "length %.5f mm" % (pts[0] - pts[1]).Length)
    best = closed
if best is None: raise SystemExit("no closed tessellation")
best.write(OUT + ".stl")
log(os.path.basename(OUT), stats(best), "GOOD" if good(best) else "CLOSED (crossings listed above)", "t %.1f" % (time.time() - t0))
