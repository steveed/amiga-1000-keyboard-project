# A1000 keyboard PCB measurements

Taken from a reproduction PCB (outline and markings copied from the original, `KCT-A89YC 56-7155B`).
Reference photos are kept out of the repo.

## Confirmed
- Key pitch: 19.05 mm.
- Cable: four wires (black, red, green, white) soldered directly to pads at the left end of the
  component strip, held by a fabric tie through the board. Each passes through a through-hole ferrite.
  The other end goes to a 4P4C modular jack. Black = GND, red = +5V (per owner); green and white are
  KCLK/KDAT, which way round not yet confirmed.
- Computer side (A1000 main schematic, J9 KBD): 1 +5V, 2 KCLK, 3 KDAT, 4 GND.
- Three axial resistors are soldered on the solder side next to the X3 cable pads, one lead of each to a
  common pad and the other leads to three separate pads. They aren't on drawing 327063. Value unclear
  from the photo (bands look like red/brown-black-red, so roughly 1K-2K).

## Parts read from an assembled board
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

## To confirm
- Overall length by ruler (scan: 389.25 mm); that also fixes the tab width.
- Switch pin hole diameter: about 1.2 mm (rough caliper reading). Check by finding the largest drill bit that fits.
- Cable pad positions (likely the pads marked X3).

## Differences from drawing 327063 rev B
- Resistor values: the repro silkscreen gives R1 510K, R2 82K, R3 150 (LED); the drawing gives 510K and 560K
  for the reset timer. On the assembled board, the resistor beside the 556 reads green-blue-yellow (560K)
  and the one near the crystal reads green-brown-yellow (510K). So the fitted parts match the drawing and
  the "82K" silkscreen looks wrong. Colour bands read from a photo; a meter check would settle it.
- 47 uF 16 V electrolytic fitted, as on the drawing.
- The timer is silkscreened NE566N, but the part fitted is an NE556N.
