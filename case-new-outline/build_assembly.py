# Assemble the left half of lazydragon64 (case + PCB + plate + spacers) into one STEP.
#   python3 build_assembly.py            (run from anywhere; needs kicad-cli and freecadcmd)
# Writes into "3d models/":
#   lazydragon64 PCB.step           PCB with parts, as set up in the board (left-hand build)
#   lazydragon64 Plate.step         switch plate
#   M2 spacers 7.5mm.step           the four spacers, already in place
#   lazydragon64 Left Assembly.step everything stacked: floor -> 2.5 mm -> PCB -> 3.4 mm -> plate
# The assembly is exported by KiCad from a temporary copy of the board with one hidden
# footprint carrying the case, plate and spacer models, so the PCB keeps its colours.
import os, re, shutil, subprocess, tempfile, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
OUT = os.path.join(HERE, "3d models")
BOARD = os.path.join(PROJ, "lazydragon64.kicad_pcb")
PLATE_PCB = os.path.join(PROJ, "plate", "Lucca58 Stagger Plate.kicad_pcb")
CASE = os.path.join(HERE, "Lucca58 Stagger New Outline Case Left.step")
TX, TY = -8.023, 7.669               # KiCad (x, y) -> case (x + TX, -y + TY), as in build_case.py
CASE_PCB_TOP = 3.1                   # case frame: floor top -1.0, PCB 1.5..3.1, plate underside 6.5
PLATE_GAP = 3.4                      # MX: PCB top to plate underside with a 1.6 mm plate
SPACERS = [(94.005, 72.565), (93.995, 112.995), (170.205, 72.565), (170.215, 132.145)]
SPACER_AF, SPACER_LEN = 3.5, 7.5
os.makedirs(OUT, exist_ok=True)
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
step = lambda src, dst, *a: run(["kicad-cli", "pcb", "export", "step", "--user-origin", "0x0mm", "-f", *a, "-o", dst, src])
pcb_step = os.path.join(OUT, "lazydragon64 PCB.step")
plate_step = os.path.join(OUT, "lazydragon64 Plate.step")
spacer_step = os.path.join(OUT, "M2 spacers 7.5mm.step")
step(BOARD, pcb_step, "--subst-models")
step(PLATE_PCB, plate_step, "--board-only")
# spacers in KiCad's 3D frame (x, -y), z relative to the PCB top: floor top is at -4.1
fc = f"""
import Part, math
from FreeCAD import Vector as V
R = {SPACER_AF} / math.sqrt(3); sols = []
for x, y in {SPACERS!r}:
    pts = [V(x + R * math.cos(math.radians(a)), -y + R * math.sin(math.radians(a)), 0) for a in range(0, 360, 60)]
    s = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, {SPACER_LEN}))
    s = s.cut(Part.makeCylinder(0.8, {SPACER_LEN} + 2, V(x, -y, -1)))
    s.translate(V(0, 0, -{CASE_PCB_TOP} - 1.0)); sols.append(s)
Part.makeCompound(sols).exportStep({spacer_step!r})
"""
run(["freecadcmd", "-c", fc])
# temporary board with one hidden footprint carrying the extra models
tmp = tempfile.mkdtemp(prefix="ld64asm-")
for ext in (".kicad_pcb", ".kicad_pro"):
    shutil.copy(os.path.join(PROJ, "lazydragon64" + ext), os.path.join(tmp, "assembly" + ext))
def model(path, off):
    return (f'\t\t(model "{path}"\n\t\t\t(offset\n\t\t\t\t(xyz {off[0]} {off[1]} {off[2]})\n\t\t\t)\n'
            '\t\t\t(scale\n\t\t\t\t(xyz 1 1 1)\n\t\t\t)\n\t\t\t(rotate\n\t\t\t\t(xyz 0 0 0)\n\t\t\t)\n\t\t)\n')
fp = (f'\t(footprint "Assembly:Case_Plate_Spacers"\n\t\t(layer "F.Cu")\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(at 0 0)\n'
      f'\t\t(property "Reference" "ASSY1"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.SilkS")\n\t\t\t(hide yes)\n\t\t\t(uuid "{uuid.uuid4()}")\n'
      '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
      '\t\t(attr board_only exclude_from_pos_files exclude_from_bom)\n'
      + model(CASE, (-TX, -TY, -CASE_PCB_TOP))        # case frame -> KiCad 3D frame
      + model(plate_step, (0, 0, PLATE_GAP))
      + model(spacer_step, (0, 0, 0))
      + '\t)\n')
p = os.path.join(tmp, "assembly.kicad_pcb"); s = open(p).read()
i = s.find("\n\t(footprint "); assert i > 0
open(p, "w").write(s[:i + 1] + fp + s[i + 1:])
asm = os.path.join(OUT, "lazydragon64 Left Assembly.step")
step(p, asm, "--subst-models")
if os.environ.get("ASSY_KEEP") == "1":       # keep the temporary board, e.g. for kicad-cli pcb render
    print("assembly:", asm, "| temp board:", p)
else:
    shutil.rmtree(tmp); print("assembly:", asm)
