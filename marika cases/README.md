# lazydragon64 Marika cases

| File | What it is |
|---|---|
| `lazydragon64 Marika Case Left.step` / `.stl` | Left half: moon-phase band round the wall, "Lazy Dragon" in Cloister Black at the left end of the front wall, Lazy Dragon drawing engraved underneath |
| `lazydragon64 Marika Case Right.step` / `.stl` | Right half: moon-phase band all the way round, no text, Lazy Dragon drawing engraved underneath |
| `chamfer/` | The same two halves with a 1 mm × 45° chamfer on the outer top edge (`… Chamfer.step` / `.stl`) |

Print bottom-down. Both STLs are closed single shells.

## Chamfered versions

- `chamfer/` holds both halves with the edge where the outer wall meets the rim top chamfered 1 mm × 45°.
- Only that edge changes. The inner top edge, the bottom edges, the band, the text, the dragon, the screw recesses and the standoff pockets are exactly as in the files above.
- The chamfer starts 14.1 mm up the outer wall, 1.5 mm above the tips of the tallest sun rays.
- The left STL is fully clean. On the right one, two triangles touch, without any measurable overlap, at one moon on the outer side wall. It is still closed, and a slicer won't see it.
- They were made from the STEP files above with `case-new-outline/chamfer_top.py`, for example:
  `CASE_IN="../marika cases/lazydragon64 Marika Case Left.step" CASE_OUT="../marika cases/chamfer/lazydragon64 Marika Case Left Chamfer" freecadcmd -c "exec(open('chamfer_top.py').read())"`
  Each takes about 2 minutes.

## The band

- It is design B ("月の満ち欠け") from the design sheet: a sun with a crescent inside, then on each side a full moon, two crescents, a diamond, a star and a dash.
- The shapes were redrawn as exact geometry rather than traced, since the sheet is a shaded render. They keep the sheet's proportions:
  - Suns are 14 mm across the longest rays.
  - Moons are 5.4 mm.
  - Everything is raised 0.8 mm, the same as the ivy cases.
- Each straight section of wall gets its own centred arrangement: whole motifs on the long walls, and a sun with moons or a group of moons on the short ones.
- The band pauses at the jogs in the wall (the steps at the back and round the thumb cluster) and at the USB notch, so no moon is split over a step.
- The "Lazy Dragon" text is 7.5 mm tall (12 mm on the ivy cases). Its left edge is 3 mm from where the front-left corner starts to curve.

## Underside and mounting

Identical to [`case-final`](../case-final):
- the same 90.0 × 47.6 mm dragon
- Ø2.2 screw holes
- Ø4.4 × 1.3 mm flush screw recesses
- Ø4.6 × 0.5 mm standoff pockets, with 1.2 mm of floor under each standoff

The hardware is the same too: M2 × 8 mm standoffs and M2 × 4 screws at both ends. See [`case-final/README.md`](../case-final/README.md).

## Rebuilding

From `case-new-outline/`, with `CASE_OUT` set to a scratch directory:

- **Left:**
  `CASE_IVY=1 CASE_BAND=moon CASE_TEXT_H=7.5 CASE_TEXT_ALIGN=left CASE_IVY_NAME=" Marika" freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Left Marika` output.
- **Right:**
  `CASE_IVY=1 CASE_IVY_ONLY=1 CASE_BAND=moon CASE_IVY_NAME=" Marika Only" freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Right Marika Only` output.

The band's shapes and layout are in `case-new-outline/moon_band.py`. Each build takes about 10 minutes. Built 2026-11-16.
