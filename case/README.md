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
  along the back wall when folded, from the end wall to about 55 mm in. Not copied: the case
  has simpler printed legs instead (below).
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
  plate. Rev 2's stack is thinner (see below), so its case adds a 9.5 mm shoulder up to the PCB,
  which rests on it; 9.5 mm clears the head of a plate screw in H1, 7.5 mm from the left hole. A
  column in the top shell, with a heat-set insert, stops level with the key-well skirts (8.65 mm
  below the top, as on the original), so it doesn't reach the plate.
- Three snaps along the front and three along the back (`snap_x`) hold the long edges down between
  the screws. Each is a 10 mm arm hanging from the top shell just inside the tongue, with a hook that
  catches a pocket in the bottom shell's wall below the parting line. The catch face slopes at 30
  degrees (`snap_catch_a`), so the case still pulls apart once the screws are out. They sit clear of
  the parts along both boards' back edges.
- A skirt round each key opening, 8.65 mm deep from the top surface as on the original, stopping
  2.35 mm above the plate (`skirt_h`).
- Flat top and bottom (`smooth`): the label and badge recesses on top, and the label recess
  underneath, are left off, so each shell prints on a flat face and the top's inside is flat too
  (13.55 mm over the PCB everywhere). `smooth = false` puts them back.
- Four round pockets underneath, 13.2 mm across and 1 mm deep (`foot_d`, `foot_depth`), centred where
  the model has its feet, for standard 1/2 inch (12.7 mm) stick-on rubber feet. `feet = "square"`
  makes them the model's 19 mm squares instead. The rear two sit 4.8 mm ahead of the leg notches.
- AMIGA lettering above the keypad (`logo`), engraved 0.7 mm into the top in place of the badge
  recess: the A1200 cover's italic outline (`amiga-logo.dxf`, from the a1200kb-external-case
  project), scaled to the keypad opening's width (60.3 mm, `logo_w`; the A1200's is 94.8) and
  centred over it at the badge's height (`logo_c`).
- Two fold-out legs at the back, after a Logitech keyboard's, centred at x 31.7 and 358
  (`leg_x`). Each is a flat leg, 24 x 19 x 3.2 mm, on two 2.5 mm pins at its back end, lying flush
  in a pocket in the floor (0.6 mm up from the underside). It swings down and back on its pins
  until its back face stops on the pocket's back edge, 10 degrees past upright (`leg_lean`), so the
  case's weight holds it open; its tip stands 16.8 mm below the underside, about 6 degrees of tilt
  on the front feet. Two slots cut a 2 mm rail off each side of the leg: squeeze the rails
  together to put the pins in their holes. A ramp in front of each pocket (`leg_notch`) lets a
  fingertip under the tip. The pocket's box stands 2.8 mm off the floor inside and stops short of
  the PCB's back edge (the render warns if it runs under it). The leg is the same for every
  case. The `leg_sweep` part is a check: the case where a leg swings through it, which must be
  empty.
- A 4P4C jack where the original's is, sized from the jack itself and a test fit
  (`jack_size`): a 22 x 10.5 mm body, 13.5 mm tall, behind the back wall, with a 15.4 mm nose at its
  right end that sits in the 15.5 mm plug opening (x 86.05-101.55), as deep as the wall. The opening
  is a notch from the floor up to the parting line, and a matching notch in the top shell carries it
  on to the top of the jack. The jack sits in an open-topped box, as on the original: 0.3 mm
  clearance round the body, 1.3 mm walls from the floor to the top of the tongue. A short stop inside
  the right wall, 3.5 mm long, stands 2.2 mm off the back wall and fits a slot in the jack. A cutout
  in the front wall's left end lets the wires out (`jack_wires`: 8 mm wide, 2.5 mm of wall left under
  it). All of it is checked with the jack test print (below). The box clears the PCB's step at
  y 134.9 by 0.15 mm (the render warns if it reaches it).
- Or a common wired 616E jack (KLS12-199, HWS8282), with `jack_type = "616e"` or
  `make case JACK=616e`. Its size is the larger of the two makers' drawings (`j616_size`:
  11.4 x 10.2 mm, 17.42 tall). It stands on the floor centred in the notch, in a box like the
  other's but with no stop or wire cutout, since its wires leave from the top of its back. A filler
  closes the notch in both shells 0.6 mm in from the outside (`j616_fill`), so the notch still
  shows, with a 9 x 8.5 mm hole for the plug from the floor up (`j616_hole`). At 17.42 mm it only
  leaves 1.2 mm under the flat top; with `smooth = false` it only just fits under the label recess,
  so the label skin above it is thinned from 1.6 to 1.0 mm (`j616_skin`), leaving 0.4 mm. Not test-fitted yet: the plug hole's size and position are
  from the drawings.
- A USB-C opening in the back wall for rev 2's socket (J2), which opens to the rear on the PCB's
  back edge at x 125, about 31 mm right of the jack. The socket's mouth is 4.8 mm in from the
  outside, so the opening takes the plug's moulding too: 13 x 7.5 mm, corners r 2 (`usb_open`),
  centred on the socket 1.6 mm above the PCB, across the parting line in both shells. Rev 2 only.

## Rev 1 or rev 2

`board_rev` (`make case REV=1`, files with a `-rev1` suffix; rev 2 is the default) picks the board:

- **Rev 2:** the MX plate is 1.6 mm FR4, and plate, switches and PCB measure 6.65 mm from the plate
  top to the PCB's underside. The shoulders under the PCB come up to meet it, the tab boss stops
  under the thicker plate, and there's the USB-C opening.
- **Rev 1:** a 1.2 mm plate, and an assumed 5 mm from plate top to PCB top. The Mitsumi board with
  its clear cover underneath is closer to 9 mm.

`make case-spacers` writes three rings, 9.5 mm across and 2.85 mm tall, that put a rev 2 board in a
case printed for rev 1: they slide over the three PCB spigots under the board, and lift it so the
plate's tab also rests on the rev 1 tab boss.

## Assumed, needs checking

- **Rev 1 plate to PCB spacing** (`rev1_to_pcb`, 5.0 mm). Not measured. It sets the PCB height and
  so the room under it (3.5 mm to the floor at 5.0, for the leads and the three resistors on the
  solder side). Rev 2's is measured.
- **Plate height** (`plate_top_z`, 0.8). From the model's well floor. It decides how far the
  keycaps stand proud of the top.
- **Tall parts under the label recess.** Y1 is laid flat on the original (about 5 mm tall), so it
  fits; standing up (13.5 mm) it would not, with 12.3 mm above the PCB there. C8 and the socketed
  controller fit too.

## Printing

| part | size (mm) | orientation |
|---|---|---|
| top_left | 220 x 158 x 15 | face down |
| top_right | 198 x 158 x 15 | face down |
| bottom_left | 193 x 158 x 16 | base down |
| bottom_right | 227 x 158 x 16 | base down |
| top (`make case-one`) | 406 x 158 x 15 | face down |
| bottom (`make case-one`) | 406 x 158 x 16 | base down |
| jack_test_bottom | 50 x 25 x 16 | base down |
| jack_test_top | 50 x 25 x 12 | face down |
| joint_test_top_left / _right | 52 / 62 x 11 x 15 | face down |
| joint_test_bottom_left / _right | 25 / 93 x 18 x 16 | base down |
| leg (print two) | 27 x 21 x 3.2 | flat, as written |
| leg_test | 40 x 33 x 16 | base down |

The STLs come out in their print orientation. Each shell splits into two on a 45 degree scarf
(glue it), and the two splits are staggered so the shells bridge each other's joint. The rounded
edges stop at 45 degrees and finish with a small chamfer at the bed (`print_safe`), so nothing
needs supports. The leg pockets' roofs print as 25 mm bridges.

Each joint has two dowels, front and back, so the halves can't slide while the glue sets: a block
inside the wall, split with the joint, with a 2 mm hole along the case through both halves. Push a
20 mm length of 1.75 mm filament into each hole, then slide the halves together flat on the bench.

`make case-one` writes the shells in one piece each instead (`split = false`), with no joints or
dowels, for a bed that takes 406 x 158 mm, or one about 400 mm square with the part laid diagonally.
They take the same `JACK=616e`.

`make case` and `make case-one` also write the leg. `make case-legs` writes it with a test piece of
the floor round the left leg's pocket (40 mm wide, from just ahead of the notch to the back), to try
the pins' fit and the swing before printing the whole case.

`make case-jack` writes the two jack test pieces: just the corner of each shell round the jack
(x 70-120, from y 125 to the back), to try the jack in its box and the two shells round it before
printing the whole case. `make case-jack JACK=616e` writes the 616E's, with a `-616e` suffix,
as does `make case JACK=616e` for the whole case.

`make case-joint` writes four test pieces: a strip along the front of each shell (x 160-262, the
front 18 mm), split at its joint like the full case. It has the front dowel of each joint and the
snap at x 255, to try the filament in its holes, glue each strip, and snap the top strip onto the
bottom before printing the whole case.

`make label` writes a 1:1 sticker for the label recess underneath (`build/case/*-label-rev1.svg` and
`-rev2.svg`), laid out like the original Commodore label but with this project's name and the board
revision. Print it at 100% on sticker paper and cut on the grey outline; it sits 0.5 mm inside the
recess all round (with `smooth = false`; otherwise stick it where the recess was, x 80-150, y 53-104).

## Keycaps (rev 2)

`make keycaps` writes `build/case/*-<key>-keycap.stl` from [`a1000_keycaps.scad`](a1000_keycaps.scad):
MX caps for rev 2 in the A1000's sizes, for the keys an off-the-shelf MX set doesn't cover.

| key | size | stems |
|---|---|---|
| `return` | 1.25U over 2U, between `]`/`'` and HELP/UP | switch, vertical 2U stabiliser, dummy switch in SW55 |
| `tilde` | 1.25U | switch |
| `backspace` | 1.75U | switch |
| `tab` | 1.75U | switch |
| `lshift` | 2.5U (US) | switch, 2U stabiliser |
| `rshift` | 2U | switch, 2U stabiliser |

The A500KB's US Return cap is 1.5U over 2.25U and runs into HELP and UP.

The profile is Cherry's (GMK), with the figures from [KeyV2](https://github.com/rsheldiii/KeyV2)'s
cherry profile: a height and tilt for each row, a 0.65 mm cylindrical dish, and the top narrowed to
11.85 x 14.64 mm and moved 2 mm back. Each cap takes the Cherry row of its board row: `~` and
Backspace the number row (9.8 mm, flat), Tab the top letter row (7.45 mm, 2.5°), Return the home row
(6.55 mm, 5° over its two rows), the Shifts the bottom row (7.35 mm, 11.5°). They'll sit with a GMK
or other Cherry-profile set; they are not the A1000's own sculpt.

Print them top down, stems up; the dish needs a little support or a raft. `cross_w` sets the stem fit.

## Hardware

- 4 M3 x 16 screws, pan or button head (15-17 works: the head sits 3 mm up in a counterbore and the insert runs 5 mm up the column, from 3.15 mm above the parting line).
- 4 M3 heat-set inserts, 4 mm hole.
- About 80 mm of 1.75 mm filament, cut into four 20 mm dowels for the joints.
- 4 stick-on rubber feet, 1/2 inch (12.7 mm) round, about 3.5 mm tall (3M SJ5012 or similar),
  for the pockets underneath. 1 mm sits in the pocket.
