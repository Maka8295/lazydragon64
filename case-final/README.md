# lazydragon64 final cases

| File | What it is |
|---|---|
| `lazydragon64 Case Left.step` / `.stl` | Left half: Ivy Curl vine wrap, "Lazy Dragon" in Cloister Black on the front wall, Lazy Dragon drawing engraved underneath |
| `lazydragon64 Case Right.step` / `.stl` | Right half: Ivy Curl vine all the way round (stops only at the USB notch), no front text, Lazy Dragon drawing engraved underneath |

Print bottom-down. Both STLs are closed single shells.

## Underside (both halves)

- The dragon is 90.0 × 47.6 mm (80% of the original trace), centred on the case outline and engraved 0.6 mm.
- It reads upright when the half is turned over left to right, like a page.
- All four screw recesses sit outside the drawing on both halves; the nearest line is 1.8 mm (left) and 6.1 mm (right) from a recess edge.

## Mounting hardware (Corne v4 style)

Per half:
- **4 × M2 female–female spacers, 8 mm.** Round no wider than Ø4.0, or a 3.5 mm hex. They pass through the PCB's Ø5 holes. (The design height is 7.5 mm; 8 mm lifts the plate/PCB 0.5 mm, which is fine. Don't use 7 mm.)
- **8 × M2 screws with a head no wider than 3.5 mm and no taller than 1.3 mm.** For example, M2 × 5 hex-socket button heads. Or the LCSC Shuntian pan heads (datasheet head 3.30 × 1.30 mm): C357393 M2 × 4 for the floor and C357534 M2 × 6 for the plate.
  - 4 go up through the case floor.
  - 4 go down through the plate.
- The recesses under the case are Ø4.4 × 1.3 mm deep, so these heads sit flush with the bottom.

## Rebuilding

From `case-new-outline/`, with `CASE_OUT` set to a scratch directory:

- **Left:**
  `CASE_IVY=1 CASE_IVY_ART=ivy_curl.json CASE_IVY_MAX_BAND=17 CASE_IVY_NAME=" Ivy Curl" CASE_IVY_PHASE=6.0 freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Left Ivy Curl` output.
- **Right:**
  `CASE_IVY=1 CASE_IVY_ONLY=1 CASE_IVY_PHASE=6.0 CASE_IVY_ART=ivy_curl.json CASE_IVY_MAX_BAND=17 CASE_IVY_NAME=" Ivy Curl Only" freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Right Ivy Curl Only` output.

Each build takes about 10 minutes. Built 2026-11-14.
