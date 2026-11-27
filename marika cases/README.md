# lazydragon64 Marika cases

| File | What it is |
|---|---|
| `lazydragon64 Marika Case Left.step` / `.stl` | Left half: moon-phase band round the wall, "Lazy Dragon" in Cloister Black centred on the front wall, Lazy Dragon drawing engraved underneath |
| `lazydragon64 Marika Case Right.step` / `.stl` | Right half: moon-phase band all the way round, no text, Lazy Dragon drawing engraved underneath |
| `chamfer/` | The same two halves with a 1 mm × 45° chamfer on the outer top edge (`… Chamfer.step` / `.stl`) |

Print bottom-down. Both STLs are closed single shells.

## Chamfered versions

- `chamfer/` holds both halves with the edge where the outer wall meets the rim top chamfered 1 mm × 45°.
- Only that edge changes. The inner top edge, the bottom edges, the band, the text, the dragon, the screw recesses and the standoff pockets are exactly as in the files above.
- The chamfer starts 14.1 mm up the outer wall, 2.0 mm above the tips of the tallest sun rays.
- Each chamfer removes 235.2 mm³, all of it in the top 2.5 mm.
- All four STLs are closed single shells with no crossing triangles.
- They were made from the STEP files above with `case-new-outline/chamfer_top.py`, for example:
  `CASE_IN="../marika cases/lazydragon64 Marika Case Left.step" CASE_OUT="../marika cases/chamfer/lazydragon64 Marika Case Left Chamfer" freecadcmd -c "exec(open('chamfer_top.py').read())"`
  Each takes about 1.5 minutes.

## The band

- It is design B ("月の満ち欠け") from the design sheet: a sun with a crescent inside, then on each side a full moon, two crescents, a diamond, a star and a dash.
- The shapes were redrawn as exact geometry rather than traced, since the sheet is a shaded render. They keep the sheet's proportions:
  - Suns are 13.1 mm across the longest rays.
  - Moons are 5.0 mm.
  - Everything is raised 0.8 mm, the same as the ivy cases.
- Every glyph is the same size all the way round both halves.
- Each straight face of wall carries one arrangement, centred on that face and mirror-symmetric. It is the design trimmed from the outside in until it fits. A face too short for a sun stays plain: there are no lone moons or stars.
- Each side of the case shows only one sun. Where a side would have had several, only the one nearest the middle of that side stays, and the other faces on that side are left plain.
- The back wall is the exception: its sun stands alone on the raised middle, and the faces either side of the jogs carry the rest of the design as the two halves of one motif. Outwards from the sun on each side: a full moon, two crescents, a diamond, a star and a dash, at the design's spacing. Both halves sit the same distance from the sun, 8.8 mm further out than in the design, which clears the jogs by 1.5 mm.

  | Face | Left half | Right half |
  |---|---|---|
  | Outer side wall (92 mm) | the whole design | the whole design |
  | Inner side wall (76 mm) | the whole design | the whole design |
  | Inner wall past the thumb keys (13 mm) | plain | plain |
  | Back wall | the sun on the raised middle; beyond each jog, a full moon, two crescents, a diamond, a star and a dash | the same |
  | Front wall (89 mm) | the text, centred | the whole design |
  | Front wall by the thumb keys (29 mm) | the sun alone | plain |

- The corners, the jogs in the wall, the text and the USB notch stay bare, so no glyph wraps round a corner or is split over a step.
- The two halves mirror each other on every wall except the front, where the left half has the text.
- The narrowest gap between two glyphs is 0.67 mm, between a star's tip and a dash.
- The "Lazy Dragon" text is 12 mm tall, the same as on the ivy cases (it was 7.5 mm until 2026-11-28). It is centred on the front wall, between where the front-left corner starts to curve and the jog by the thumb keys: 8 mm from each.

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
  `CASE_IVY=1 CASE_BAND=moon CASE_IVY_NAME=" Marika" freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Left Marika` output.
- **Right:**
  `CASE_IVY=1 CASE_IVY_ONLY=1 CASE_BAND=moon CASE_IVY_NAME=" Marika Only" freecadcmd -c "exec(open('build_case.py').read())"`
  Take its `Right Marika Only` output.

The band's shapes and layout are in `case-new-outline/moon_band.py`. `CASE_MOON_K` sets the size of every glyph (mm per pixel of the design sheet, 0.0975 by default). Each build takes about 4 minutes, and the chamfer about 1.5 minutes. Built 2026-11-28; the first version (2026-11-16) chained whole motifs along each run of wall, across the rounded corners.
