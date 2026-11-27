# lazydragon64 final cases

| File | What it is |
|---|---|
| `lazydragon64 Case Left.step` / `.stl` | Left half: Ivy Curl vine wrap, "Lazy Dragon" in Cloister Black on the front wall, Lazy Dragon drawing engraved underneath |
| `lazydragon64 Case Right.step` / `.stl` | Right half: Ivy Curl vine all the way round (stops only at the USB notch), no front text, Lazy Dragon drawing engraved underneath |
| `chamfer/` | The same two halves with a 1 mm × 45° chamfer on the outer top edge (`… Chamfer.step` / `.stl`) |

Print bottom-down. Both STLs are closed single shells.

## Chamfered versions

- `chamfer/` holds both halves with the edge where the outer wall meets the rim top chamfered 1 mm × 45°.
- Only that edge changes. The inner top edge, the bottom edges, the vine, the text, the dragon, the screw recesses and the standoff pockets are exactly as in the files above.
- The chamfer starts 14.1 mm up the outer wall, 0.2 mm above the highest point of the vine, so it doesn't cut into the vine.
- Their STLs are closed. Two pairs of triangles cross, by about 0.0001 mm each, where the vine turns the back wall's step corners. Re-meshing the unchamfered STEP files gives the same two, and a slicer won't see them.
- They were made from the STEP files above with `case-new-outline/chamfer_top.py`, for example:
  `CASE_IN="../case-final/lazydragon64 Case Left.step" CASE_OUT="../case-final/chamfer/lazydragon64 Case Left Chamfer" freecadcmd -c "exec(open('chamfer_top.py').read())"`
  Each takes about 3 minutes.

## Underside (both halves)

- The dragon is 90.0 × 47.6 mm (80% of the original trace), centred on the case outline and engraved 0.6 mm.
- It reads upright when the half is turned over left to right, like a page.
- All four screw recesses sit outside the drawing on both halves; the nearest line is 1.8 mm (left) and 6.1 mm (right) from a recess edge.

## Mounting hardware (Corne v4 style)

Per half:
- **4 × M2 × 8 mm female–female standoffs.** LCSC C50378452 (XHHD STTZ1005, round brass). Use any round standoff no wider than Ø4.0 or a 3.5 mm hex; they pass through the PCB's Ø5 holes.
  - Each standoff stands in a Ø4.6 × 0.5 mm pocket in the case floor, so its top lands exactly at the designed plate height.
  - Use 8 mm, not 7.5 mm: a 7.5 mm standoff would sit 0.5 mm low and put the hotswap sockets on the floor.
- **8 × M2 × 4 screws, the same screw at both ends of each standoff:** LCSC C357393 (Shuntian PM2X4, nickel-plated Phillips pan head, head 3.30 × 1.30 mm).
  - Four go up through the case floor and sit flush in the Ø4.4 × 1.3 mm recesses underneath. The floor under each standoff is 1.2 mm, so 2.8 mm of the thread goes into the standoff.
  - Four go down through the 1.6 mm plate, so 2.4 mm of the thread goes into the standoff. Don't put washers under these heads.
  - Tighten snug, not hard: the brass threads strip easily.
- Any M2 head no wider than 3.5 mm and no taller than 1.3 mm works.
- The two screws in a standoff must not meet in the middle: (floor screw − 1.2) + (plate screw − 1.6) must be under 8 mm.
  - M2 × 4 at both ends gives 5.2 mm.
  - M2 × 6 at both ends gives 9.2 mm, which is too long.

## Rebuilding

From `case-new-outline/`, with `CASE_OUT` set to a scratch directory:

- **Left:**
  `CASE_IVY=1 CASE_IVY_ART=ivy_curl.json CASE_IVY_MAX_BAND=17 CASE_IVY_NAME=" Ivy Curl" CASE_IVY_PHASE=6.0 freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Left Ivy Curl` output.
- **Right:**
  `CASE_IVY=1 CASE_IVY_ONLY=1 CASE_IVY_PHASE=6.0 CASE_IVY_ART=ivy_curl.json CASE_IVY_MAX_BAND=17 CASE_IVY_NAME=" Ivy Curl Only" freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Right Ivy Curl Only` output.

Each build takes about 10 minutes. Built 2026-11-14.

## No-dragon versions (2026-11-25)

- `chamfer-no-dragon/` holds the chamfered halves with the underside drawing filled back in: the bottom is plain. Everything else (vine, text, chamfer, screw recesses, standoff pockets) is unchanged.
- The Lucca58 source STEPs `build_case.py` reads are gone, so these weren't rebuilt. They were made from the `chamfer/` STEPs with `case-new-outline/fill_art.py`, which fills the 0.6 mm engraving exactly (it checks the volume added equals the ceiling area × 0.6):
  `CASE_IN="../case-final/chamfer/lazydragon64 Case Left Chamfer.step" CASE_OUT="../case-final/chamfer-no-dragon/lazydragon64 Case Left Chamfer No Dragon" freecadcmd -c "exec(open('fill_art.py').read())"`
- The STLs are closed, with the same two ~0.0001 mm facet crossings as the chamfered files.
- `lazydragon64_no_dragon_X1C_heavy_overture_matte.3mf` is a Bambu Studio project for an X1C on a Textured PEI plate with Overture Matte PLA: 0.12 mm layers, solid (100% infill, 4 walls), outer wall 60 mm/s at 2000 mm/s² for the vine, Arachne walls, aligned seam. About 184 g and 7.5 h for both halves.

## Top covers (2026-11-26)

`cover/lazydragon64 Cover Left/Right.step` / `.stl`: a plain lid for each half that rests on the case rim and closes over the keys.

- **Fit:**
  - The lid's walls carry the case's own walls straight up, so it sits flush all round.
  - Its underside is one flat, unbroken rim: nothing reaches down into the case.
  - Over the USB notch the rim just runs across. The notch stays open below it, so the cables can stay plugged in.
  - Nothing holds the lid sideways but its own weight.
- **Edge:** the outer top edge is chamfered 1 mm × 45°, like the `chamfer/` cases.
- **Height:**
  - The lid is 14.3 mm tall.
  - Inside, the ceiling is 18.9 mm above the plate, about 2.7 mm over XDA keycaps on MX switches. That figure is estimated: stem top ~11.6 mm above the plate, cap top ~4.6 mm above that.
  - For taller caps, rebuild with a higher `COVER_CEIL`.
- **Fit check:** checked against all three left cases and the PCB assembly in `case-new-outline/3d models/`.
  - There is no overlap with any case or with any part in the assembly.
  - The lid covers the whole rim. On the chamfered cases its outer 1 mm sits over their chamfer, which leaves a small V-groove at the join.
  - The closest part is the RP2040-Zero's USB-C: 0.54 mm from the lid's inner wall and 11 mm below the ceiling.
  - The assembly has no switches, keycaps or OLED, so the keycap clearance above is an estimate.
- **Top:**
  - The Lazy Dragon drawing is engraved 0.6 mm, about 135 × 72 mm: the largest that fits 3 mm inside the edge. The width is the limit.
  - Each lid has its own unmirrored copy.
  - The coin pile is simplified for printing:
    - the loose marks in the pile are gone;
    - the specks and thin strands of land between coins are engraved;
    - every coin (65 of them) is redrawn as a clean oval, so the hoard prints as plain round islands in an engraved bed;
    - coins too small for an oval, or crossed by a bar, become solid engraved dots (14 of them).
  - The dragon, the crown, goblet, gem, sword, chest and the lettering are as drawn.
- **Printing:**
  - Print top-down: the drawing goes on the plate, like the case undersides, and nothing needs support.
  - About 72 g each, solid.
  - Use the same slicer settings as the no-dragon case project: Arachne, `filter_out_gap_fill`, Textured PEI.
- **Alternative right lid, "Mushroom House"** (`cover/lazydragon64 Cover Right Mushroom House.step` / `.stl`, 2026-11-28):
  - The same right lid, with the mushroom house and its two sleeping sheep raised 0.6 mm on the top instead of the engraved dragon.
  - The drawing is small, 70 × 43 mm (about half the lid's width), and sits in the front corner at the outer end, 6 mm in from the right and front edges; the rest of the top is plain. `COVER_MUSHROOM_W` sets its width, and `COVER_MUSHROOM_W=0` makes it as large as fits and centres it, like the dragon (135 × 82 mm).
  - It reads upright from the front of the keyboard.
  - It was made printable:
    - every line is at least 0.45 mm wide (at this size most of the drawn lines are thinner, so they are thickened to about 0.5 mm);
    - the sheep's closed eyes and the lines under their chins are widened by 0.24 mm, to grooves about 0.45 mm wide (drawn they'd be 0.2 mm at this size and fill in);
    - specks under 0.05 mm² are dropped.
  - It is 14.9 mm tall and about 74 g, solid.
  - **Print it top-up**, with the drawing facing up; it can't go on the plate like the engraved lids. Its ceiling then spans the key area, so turn on supports, tree style and on the build plate only. They stand inside the lid, under the ceiling, and nothing touches the drawing.
  - Source: `case-new-outline/mushroom_house.png`, traced into `mushroom_art.json` with `python3 trace_art.py mushroom_house.png mushroom_art.json 100 0`.
- **Rebuilding:** from `case-new-outline/`:
  `freecadcmd -c "exec(open('build_cover.py').read())"`
  (2D art and the chamfer offset in `cover_art.py`). It takes about 4 minutes.
  - `COVER_RIGHT_ART=mushroom` builds only the Mushroom House right lid (about 3 minutes). Both builds need shapely (`python-shapely` on Arch).
  - `COVER_WINDOWS=1` puts back the raised gothic windows (from `window.png`, traced into `window_art.json`), 42 per lid on the straight runs of wall.
