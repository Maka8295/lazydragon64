#!/usr/bin/env python3
"""Render the README images with kicad-cli (KiCad 10) into this folder.

  python3 images/make_renders.py [name ...]      # all, or only the named renders

PCB and plates: their own KiCad boards. Cases, lids and the assembly: a temporary board
whose one footprint carries the STEP models (as case-new-outline/build_assembly.py does).
KiCad frames its camera on the board, so for a model on its own the board is drawn as the
model's cavity shrunk 2 mm (with 2.25 mm holes for the screw recesses, so nothing of it shows) and buried inside the model:
in the case floor (case Z -3.3 to -1.7, clear of the 0.6 mm engraving and the screw
recesses) or in the lid's top (Z 27.1 to 28.7, under the 0.6 mm engraving).
Needs shapely, and the STEP files from case-final/, marika cases/ and case-new-outline/.
"""
import os, sys, json, subprocess, tempfile, shutil, uuid
from shapely.geometry import Polygon, Point
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
CF = os.path.join(PROJ, "case-final")
TX, TY = -8.023, 7.669                          # KiCad (x, y) -> case (x + TX, -y + TY)
SCREWS = [(94.005, 72.565), (93.995, 112.995), (170.205, 72.565), (170.215, 132.145)]   # KiCad mm
CASE_PCB_TOP = 3.1
PLATE_GAP = 3.4

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(" ".join(cmd) + "\n" + r.stdout + r.stderr)

# ---- the case's cavity, from the plain case STEP (cached) ----------------------------------
def cavity():
    cache = os.path.join(tempfile.gettempdir(), "ld64_cavity.json")
    if not os.path.exists(cache):
        fc = f"""
import Part, json
from FreeCAD import Vector as V
s = Part.Shape(); s.read({os.path.join(PROJ, "case-new-outline", "Lucca58 Stagger New Outline Case Left.step")!r})
def ring(w): return [(p.x, p.y) for p in w.discretize(Deflection=0.01)]
O = max(s.slice(V(0, 0, 1), -2.0), key=lambda w: w.BoundBox.DiagonalLength)
W = s.slice(V(0, 0, 1), 14.9)[0]
json.dump({{"O": ring(O), "W": ring(W)}}, open({cache!r}, "w"))
"""
        run(["freecadcmd", "-c", fc])
    d = json.load(open(cache))
    O, W = Polygon(d["O"]).buffer(0), Polygon(d["W"]).buffer(0)
    cav = O.difference(W)
    cav = max(cav.geoms, key=lambda g: g.area) if hasattr(cav, "geoms") else cav
    return O, cav

def to_kicad(poly, mirror):
    if mirror: poly = affinity.scale(poly, -1, 1, origin=(0, 0))
    return [(x - TX, -(y - TY)) for x, y in poly.exterior.coords]

# ---- a board file with one footprint carrying models -------------------------------------
def header():
    s = open(os.path.join(PROJ, "plate", "Lucca58 Stagger Plate.kicad_pcb")).read()
    return s[:s.index("\n\t(gr_")]

def gr_poly(pts):
    xy = " ".join(f"(xy {x:.4f} {y:.4f})" for x, y in pts[:-1])
    return (f'\t(gr_poly\n\t\t(pts {xy})\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(fill no)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')

def model(path, off, rot=(0, 0, 0)):
    k = 1 / 2.54 if path.endswith(".wrl") else 1          # KiCad reads VRML in 0.1 inch
    return (f'\t\t(model "{path}"\n\t\t\t(offset\n\t\t\t\t(xyz {off[0]} {off[1]} {off[2]})\n\t\t\t)\n'
            f'\t\t\t(scale\n\t\t\t\t(xyz {k} {k} {k})\n\t\t\t)\n'
            f'\t\t\t(rotate\n\t\t\t\t(xyz {rot[0]} {rot[1]} {rot[2]})\n\t\t\t)\n\t\t)\n')

def footprint(models):
    return (f'\t(footprint "Render:Models"\n\t\t(layer "F.Cu")\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(at 0 0)\n'
            f'\t\t(property "Reference" "M1"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.SilkS")\n\t\t\t(hide yes)\n\t\t\t(uuid "{uuid.uuid4()}")\n'
            '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
            '\t\t(attr board_only exclude_from_pos_files exclude_from_bom)\n' + "".join(models) + "\t)\n")

def scene_board(tmp, name, models, mirror=False, z_board=-3.3):
    """models: [(step, case-frame z shift)] placed in the case frame; the hidden board's bottom
    sits at case Z z_board"""
    O, cav = cavity()
    inner = cav.buffer(-2.0, join_style=2)
    holes = [Point(x + TX, -y + TY).buffer(2.25, 32) for x, y in SCREWS] if z_board < 0 else []
    off_z = -(z_board + 1.6)                       # 3D z = case z + off_z + board thickness
    ms = [model(p, (-TX, -TY, off_z + dz)) for p, dz in models]
    body = header() + "\n" + gr_poly(to_kicad(inner, mirror))
    for h in holes: body += gr_poly(to_kicad(h, mirror))
    body += footprint(ms) + ")\n"
    p = os.path.join(tmp, name + ".kicad_pcb"); open(p, "w").write(body)
    return p

def assembly_board(tmp, case_step, extra=()):
    """the real PCB with the case, plate and spacers stacked on it, as build_assembly.py"""
    for ext in (".kicad_pcb", ".kicad_pro"):
        shutil.copy(os.path.join(PROJ, "lazydragon64" + ext), os.path.join(tmp, "assembly" + ext))
    m3d = os.path.join(PROJ, "case-new-outline", "3d models")
    ms = [model(case_step, (-TX, -TY, -CASE_PCB_TOP)),
          model(os.path.join(m3d, "lazydragon64 Plate.step"), (0, 0, PLATE_GAP)),
          model(os.path.join(m3d, "M2 spacers 7.5mm.step"), (0, 0, 0))]
    ms += [model(p, (-TX, -TY, -CASE_PCB_TOP + dz)) for p, dz in extra]
    p = os.path.join(tmp, "assembly.kicad_pcb"); s = open(p).read()
    i = s.find("\n\t(footprint "); open(p, "w").write(s[:i + 1] + footprint(ms) + s[i + 1:])
    return p

def render(board, out, rotate=None, side="top", zoom=1.0, w=1600, h=1000, pan=None):
    cmd = ["kicad-cli", "pcb", "render", "--quality", "high", "--background", "transparent", "--perspective",
           "-w", str(w), "-h", str(h), "--side", side, "--zoom", str(zoom), "-o", out]
    if rotate: cmd += ["--rotate", rotate]
    if pan: cmd += ["--pan", pan]
    run(cmd + [board]); trim(out); print("wrote", os.path.relpath(out, PROJ), flush=True)

def trim(path, pad=0.03):
    """crop a transparent render to what is drawn, plus a margin"""
    from PIL import Image
    im = Image.open(path); x0, y0, x1, y1 = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    m = int(pad * max(x1 - x0, y1 - y0))
    im.crop((max(0, x0 - m), max(0, y0 - m), min(im.width, x1 + m), min(im.height, y1 + m))).save(path)

ISO_FL = "-50,0,-30"      # from the front left, above
ISO_FR = "-50,0,30"       # from the front right, above

def jobs(tmp):
    I = lambda n: os.path.join(HERE, n)
    pcb = os.path.join(PROJ, "lazydragon64.kicad_pcb")
    plate = os.path.join(PROJ, "plate", "Lucca58 Stagger Plate.kicad_pcb")
    marika_plate = os.path.join(PROJ, "plate", "marikaplate.kicad_pcb")
    cl = os.path.join(CF, "chamfer", "lazydragon64 Case Left Chamfer.step")
    cr = os.path.join(CF, "chamfer", "lazydragon64 Case Right Chamfer.step")
    ml = os.path.join(PROJ, "marika cases", "lazydragon64 Marika Case Left.step")
    lid_l = os.path.join(CF, "cover", "lazydragon64 Cover Left.step")
    return {
        "pcb-top": lambda: render(pcb, I("pcb-top.png"), side="top", zoom=0.95),
        "pcb-bottom": lambda: render(pcb, I("pcb-bottom.png"), side="bottom", zoom=0.95),
        "pcb-angle": lambda: render(pcb, I("pcb-angle.png"), rotate=ISO_FL, zoom=0.95),
        "plate": lambda: render(plate, I("plate.png"), rotate=ISO_FL, zoom=0.95),
        "plate-marika": lambda: render(marika_plate, I("plate-marika.png"), rotate=ISO_FL, zoom=0.95),
        "case-left": lambda: render(scene_board(tmp, "case_l", [(cl, 0)]), I("case-left.png"), rotate=ISO_FL, zoom=0.9),
        "case-right": lambda: render(scene_board(tmp, "case_r", [(cr, 0)], mirror=True), I("case-right.png"), rotate=ISO_FR, zoom=0.9),
        "case-bottom": lambda: render(scene_board(tmp, "case_b", [(cl, 0)]), I("case-bottom.png"), side="bottom", zoom=0.9),
        "case-marika": lambda: render(scene_board(tmp, "case_m", [(ml, 0)]), I("case-marika.png"), rotate=ISO_FL, zoom=0.9),
        "cover": lambda: render(scene_board(tmp, "lid", [(lid_l, 0)], z_board=27.1), I("cover.png"), rotate=ISO_FL, zoom=0.9),
        "cover-on-case": lambda: render(scene_board(tmp, "lid_case", [(cl, 0), (lid_l, 0)]), I("cover-on-case.png"), rotate=ISO_FL, zoom=0.85),
        "assembly": lambda: render(assembly_board(tmp, cl), I("assembly.png"), rotate=ISO_FL, zoom=0.9),
    }

if __name__ == "__main__":
    tmp = tempfile.mkdtemp(prefix="ld64render-")
    try:
        js = jobs(tmp)
        for name in (sys.argv[1:] or list(js)):
            js[name]()
    finally:
        shutil.rmtree(tmp)
