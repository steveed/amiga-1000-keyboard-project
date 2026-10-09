# Case

A printable case for the PCB and switch plate, shaped after the original Amiga 1000 keyboard.
Everything is generated from [`a1000_case.scad`](a1000_case.scad); `make case` writes the four
printable STLs and an assembly preview to `build/case/`.

Coordinates are the PCB's, as in [`docs/measurements.md`](../docs/measurements.md): x from the
PCB's left edge, y up from its front edge. z = 0 is the parting line between the two shells.

## Where the shape comes from

No original case was measured. The outside is taken from a 1:8 scale model of the keyboard (a 3MF,
"Keyboard PRINTABLE v8"; not kept in the repo). Its keycaps were fitted to
`docs/switch-positions.csv`: 66 single-width caps match at a scale of 7.99 with 0.27 mm RMS error,
so the model is accurate to well under a millimetre in plan. At full size:

- Case 405.7 x 157.9 x 23.6 mm, 25.85 mm on the model's feet. It overhangs the PCB by 8.0 mm at the left,
  8.45 at the right, 8.15 at the front and 4.8 behind the controller tab.
- Flat top, no wedge. The front and back edges are rounded (about r 5.9). The ends are square.
- A groove round the middle at the parting line (the model steps it; here it is one 1.6 x 1.2 mm groove).
- One stepped opening for the main block and the top row, and one for the keypad. Every keycap
  centre has at least 9.69 mm clear to the edge, so a full 19.05 mm cap envelope fits.
- The model's key wells have a floor at z = 0.8, read here as the plate top.
- A sloped label recess behind the keys (x 31.5-282.1, y 125.9-143.4), its floor rising from
  z 8.34 at the front to 10.27 at the back.
- A 15.5 mm badge recess at the rear right, 0.5 mm deep, where the original has the Amiga logo.
- A 0.3 mm label recess underneath, and four 19 mm square feet, 2.25 mm tall.

## From photos of an original case

Photos of an original top and bottom case (not kept in the repo), scaled from a steel rule in
the frame. Positions are good to a few millimetres.

- Overall length agrees with the model: about 406 mm.
- The bottom case has bosses at all four case-screw positions: the PCB's three 7.5 mm holes and
  the plate tab. The top case has matching bosses, so four screws, as modelled here.
- The keyboard cable is a coiled telephone handset cable. It plugs into a 4P4C jack that sits
  in a 15.5 mm notch in the bottom case's back wall, in a moulded pocket, left of J1 (x 123),
  which is wired to the jack.
- Rear corners: spring-loaded fold-out legs. Each is a hinged leg with a wire spring, lying
  along the back wall when folded, from the end wall to about 55 mm in. Not modelled yet;
  the model's two rear feet sit about where they fold.
- The top case has small ribs or hooks along the inside of its front wall. Not modelled.
- The plate carries an aluminium channel over the controller strip.

## Inside (designed here, not from the original)

- The bottom shell has a 3.8 mm tongue, as on the original, that locates the top shell's walls.
  Below the parting line it thickens the wall down to the floor, so it prints on a base instead of
  in mid-air.
- Four M3 screws from underneath, at the PCB's three 7.5 mm case holes and the plate tab's hole.
  Each bottom boss carries a 7 mm spigot up through the PCB and plate. Under the PCB the boss is a
  1 mm shoulder on the floor, as on the original, so the spigot passes through the PCB's clearance
  hole and the board is never propped up by the case. Under the plate tab the boss runs up to the
  plate. A column in the top shell lands on the plate, with a heat-set insert.
- A skirt round each key opening runs down to 0.3 mm above the plate.
- Four 19 mm square pockets underneath, 1 mm deep (`foot_depth`), where the model has its feet,
  for stick-on rubber feet instead of printed ones.
- A 4P4C jack where the original's is, in an open-topped box measured from the original:
  x 78.3-101.55 (23.25 wide), 10.5 deep from the back wall, with walls from the floor to the top of
  the tongue. The plug opening in the back wall is 15.5 mm wide (x 86.05-101.55), its right side
  lined up with the box's, as on the original. It is a notch up to the parting line, and a matching
  notch in the top shell carries it on to the top of the jack. The box clears the PCB's step at
  y 134.9 by 1.75 mm (the render warns if it reaches it).

## Assumed, needs checking

- **Plate to PCB spacing** (`plate_to_pcb`, 5.0 mm). Not measured. It sets the PCB height and
  so the room under it (3.5 mm to the floor at 5.0, for the leads and the three resistors on the
  solder side).
- **Plate height** (`plate_top_z`, 0.8). From the model's well floor. It decides how far the
  keycaps stand proud of the top.
- **Jack** (`jack_h`, `jack_plug`, `jack_box_t`). The jack height, plug opening and box wall
  thickness are typical values; the box's outside size is measured from the original.
- **Tall parts under the label recess.** Y1 is laid flat on the original (about 5 mm tall), so it
  fits; standing up (13.5 mm) it would not, with 12.3 mm above the PCB there. C8 and the socketed
  controller fit too.

## Printing

| part | size (mm) | orientation |
|---|---|---|
| top_left | 220 x 158 x 12 | face down |
| top_right | 198 x 158 x 12 | face down |
| bottom_left | 193 x 158 x 14 | base down |
| bottom_right | 227 x 158 x 14 | base down |

The STLs come out in their print orientation. Each shell splits into two on a 45 degree scarf
(glue it), and the two splits are staggered so the shells bridge each other's joint. The rounded
edges stop at 45 degrees and finish with a small chamfer at the bed (`print_safe`), so nothing
needs supports. The exception is the label recess, which prints as a ~17 mm bridge.

## Hardware

- 4 M3 x 14 screws, pan or button head (12-16 works: the head sits 3 mm up in a counterbore and the insert runs 5 mm up the column).
- 4 M3 heat-set inserts, 4 mm hole.
- 4 stick-on rubber feet, up to 19 mm square or round, for the pockets underneath.
