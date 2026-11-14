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
