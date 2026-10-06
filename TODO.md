# TODO

1. **PCB measurements** - measure an original board: outline, mounting holes, switch positions, connector placement.
2. **Layout/routing** - lay out and route the PCB in KiCad.
3. **Print test fit** - print the board outline 1:1 and test it against the case and keycaps.
4. **Create plate from original** - model the switch plate from the original.
5. **Fab** - order boards.
6. **Custom case**

## Open questions from the schematic
- Add solder jumpers to swap KCLK/KDAT, so the board takes either the original A1000 controller
  or a 6570 from an A500/A2000/A3000 keyboard (those need the two lines swapped).
- Identify the transistor and diode part numbers.
- Assign footprints (switches, connector, passives) before layout.
