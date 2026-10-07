# A1000 keyboard PCB measurements

Taken from a reproduction PCB (outline and markings copied from the original, `KCT-A89YC 56-7155B`).
Reference photos are kept out of the repo.

## Confirmed
- Key pitch: 19.05 mm.
- Cable: four wires (black, red, green, white) soldered directly to pads at the left end of the
  component strip, held by a fabric tie through the board. Each passes through a through-hole ferrite.
  The other end goes to a 4P4C modular jack. Black = GND, red = +5V (per owner). By meter, white goes
  to the 6500's pin 38 (PA0) and green to pin 37 (PA1). At the cord's computer end, white is on pin 2
  (KCLK on the A1000 jack). So white = KCLK = PA0 and green = KDAT = PA1, matching the drawing.
- Computer side (A1000 main schematic, J9 KBD): 1 +5V, 2 KCLK, 3 KDAT, 4 GND.
- Three axial resistors are soldered on the solder side next to the X3 cable pads, one lead of each to a
  common pad and the other leads to three separate pads. They aren't on drawing 327063. Value unclear
  from the photo (bands look like red/brown-black-red, so roughly 1K-2K).

## Parts read from an assembled board
- Switches: Mitsumi standard mechanical Type 2 ("KCT" type, matching the `KCT-A89YC` PCB marking).
  13.5 mm square base. Seen from the top, the two pins sit 2.0 mm in from the right edge of the base
  (caliper: pin to far edge ~11.5 mm), so the body and keycap centre is 4.75 mm left of the pin midpoint.
  Cross-check: with that offset the rotated RETURN switch's body centre lands on the home row.
- The short ISO left-shift position (SW92) is wired in parallel with L SHIFT (SW87), checked with a meter.
- Caps Lock LED (inside the Caps Lock switch): leads 2.7 mm apart; the upper lead (towards the F-keys) is the
  anode, checked with a meter.
- Crystal: 3.000 MHz, HC-49/U can about 10 x 13 mm, leads 5 mm apart (marked "3.000 UNI 85 E").
- Controller: 40-pin DIP marked "R10L2-11 / MEXICO A / 0106 / 8535" (Commodore logo).
- Timer: TI NE556N (confirms the 556; the board silkscreen's "NE566N" is a typo).
- Crystal load cap 22 pF; 104 (0.1 uF) ceramic decoupling next to the controller.
- Switches mount in a black steel plate held with small screws.

## From the flatbed scans (200 dpi, calibrated to the 19.05 mm key pitch)
Coordinates are mm, x from the left edge and y up from the front edge, component side up.
Hole and switch centres come from the scan; edges are taken from the caliper.
- Overall length: 389.25 mm.
- Outline, by caliper, looking at the top of the keyboard. The back edge steps; the front edge is straight.
  | Section (left to right) | Width | Depth |
  |---|---|---|
  | Left end | 71.10 | 121.36 |
  | First step | 32.45 | 134.90 |
  | Controller tab | 239.40 (remainder, from scan length) | 144.99 |
  | Keypad end | 46.30 | 119.60 |
  The scan agrees to within ~1 mm on the widths. Its depths read 0.25-0.5 mm high, consistent with edge
  blur at 200 dpi, so use the caliper numbers for the outline and the scan for hole and switch centres.
- 91 switches, matching the schematic. Two pins per switch, 9.04 mm apart, one above the other.
  Centres are in `switch-positions.csv`. Rows are on a 19.05 mm pitch. Keys within a row are 19.05 mm
  apart, but the rows aren't all offset by quarter units, so use the measured positions.
- Round holes (centres from the scan; diameters confirmed by caliper):
  - 7.5 mm, clearance for the case screws: (16.7, 15.3), (318.2, 15.2), (375.7, 110.2)
  - 3.8 mm, screws to the plate: (24.4, 15.3), (25.1, 110.0), (108.7, 15.2), (113.6, 62.7), (209.0, 110.0), (213.5, 15.1),
    (294.6, 62.8), (349.1, 15.2), (361.4, 110.5)
- Rectangular cut-outs, ~6.5 x 10.4 mm: centres (89.3, 14.0) and (204.2, 14.0).

## Switch plate (caliper)
Steel, 1.25 mm thick. Coordinates as above (x from the PCB's left edge, y up from its front edge).
- Outline: 393.25 x 120.9 mm; 2 mm wider than the PCB on each side (x -2.0 to 391.25). The back edge is
  flush with the PCB's left-end back edge (y 121.36), so the front edge is at y 0.46.
- Tab: flat, 18 mm wide, 25 mm deep, on the back edge, its left edge 50.8 mm from the plate's left edge
  (x 48.8-66.8, y 121.36-146.36). 7.5 mm hole centred in it, at (57.8, 133.86). It sits past the PCB's back
  edge, where the PCB is only 121.36 mm deep.
- PCB screw holes: tapped, for screws with a ~2.48 mm thread (likely M2.5; pitch not measured). They line up
  with the PCB's nine 3.8 mm holes; the size difference suggests extruded bosses that sit in those holes.
- Case: through-holes for the case screws line up with the PCB's three 7.5 mm case holes, plus the 7.5 mm hole in the tab.
- Switch cut-outs: 14 x 14 mm.
- The front and back edges are folded into a C shape that holds the plate at a set height above the PCB
  (not measured).
- Stabilizer slots (wide keys other than the space bar): 3 x 15 mm, 2.6 mm from the switch cut-out, under both Shifts, Return (the large
  L-shaped key), Tab, Backspace, keypad 0 and keypad Enter.
- Space bar stabilizer cut-outs: 7.1 mm wide x 11 mm tall, ~115 mm apart centre to centre (caliper), so they sit
  over the PCB's 6.5 x 10.4 mm cut-outs (centres x 89.28 and 204.22, 114.94 mm apart), symmetric about the
  space bar key centre (x 146.81 = pins - 4.75). Use the PCB cut-out centres for the plate.
- SW55 (home row, left of Return) holds a dummy housing on US boards: one leg, no spring, supporting the
  Return keycap. SW41 (Return) body sits behind its pins, in the gap below DEL/HELP.

## Plate, version 1
1.2 mm FR4 (`make plate`), held in place by the switches: no folded edges, and 2.7 mm clearance holes in place
of the tapped M2.5 holes, so screws and spacers can be added later if needed. A steel plate like the original
would need the folded edges measured and the holes drawn at the 2.05 mm tap drill.

## To confirm
- Overall length by ruler (scan: 389.25 mm); that also fixes the tab width.
- Plate (steel only): folded edge dimensions, PCB screw pitch.
- Switch pin hole diameter: about 1.2 mm (rough caliper reading). Check by finding the largest drill bit that fits.
- Cable pad positions (likely the pads marked X3).

## Differences from drawing 327063 rev B
- Resistor values: the repro silkscreen gives R1 510K, R2 82K, R3 150 (LED); the drawing gives 510K and 560K
  for the reset timer. On the assembled board, the resistor beside the 556 reads green-blue-yellow (560K)
  and the one near the crystal reads green-brown-yellow (510K). So the fitted parts match the drawing and
  the "82K" silkscreen looks wrong. Colour bands read from a photo; a meter check would settle it.
- 47 uF 16 V electrolytic fitted, as on the drawing.
- The timer is silkscreened NE566N, but the part fitted is an NE556N.
