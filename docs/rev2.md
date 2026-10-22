# Rev 2

Rev 1 is a faithful recreation of the original board: through-hole, Mitsumi switches, and the
original 6500/1 mask-ROM controller, which has to come from a donor keyboard. Rev 2 keeps rev 1's
outline, mounting holes and key positions, so it fits the same case, and changes everything else:

- **No donor controller.** An ATmega32U4 runs open firmware in place of the 6500/1.
- **Fab-assembled.** Surface-mount parts, all stocked by JLCPCB; only the switches, stabilisers
  and the Caps Lock LED are fitted by hand.
- **Cherry MX switches** (and compatibles), with a US or an ISO plate.
- **Amiga and USB.** The original Amiga cable and a USB-C socket are both on the board, and the
  keyboard works on either, or both at once.

The details are in [pcb/rev_2/README.md](../pcb/rev_2/README.md) (the board) and
[firmware/README.md](../firmware/README.md) (the firmware).

## The board

- **Controller:** ATmega32U4 at 16 MHz. It flashes over USB from the factory bootloader, with a
  key combination, jumper pads and an ISP header for getting back into it.
- **Power:** a TPS2116 mux takes the Amiga's 5 V when it's there and USB's otherwise, so plugging
  both in never back-feeds either one. It also tells the firmware whether the Amiga is powered.
- **Matrix:** 8 x 12 with a diode per key, so any combination of keys reads correctly.
- **Layout:** the controller, USB-C and power parts sit on the strip behind the keys. USB-C opens
  to the rear, through its own opening in the printed case's back wall, clear of the Amiga jack.
- **Generated:** the schematic, board and plates are built by scripts in `tools/` and routed with
  KiCadRoutingTools, so changes are made in the scripts and regenerated with `make`.
- **Ordering:** the gerbers, BOM, placement and both plates for JLCPCB are built on every push
  that touches rev 2, and published with the firmware hex as a release for each `rev2-v*` tag.

## The firmware

A port of Henryk Richter's [A500KB](https://github.com/HenrykRichter/A500KB) firmware, restructured
for rev 2's matrix and for running both connections at once, with USB from
[LUFA](https://github.com/abcminiuser/lufa).

- **Amiga:** the full keyboard protocol, including the power-up key stream, lost-sync recovery and
  Ctrl-Amiga-Amiga reset. It only talks to the Amiga while the Amiga is powered.
- **USB:** a standard boot-protocol keyboard, built from the same key state.
- **Keymap:** generated from the schematic's key names, so the Amiga codes and USB usages can't drift
  from the board.
- **Tests:** the keymap, debouncing, USB report and Amiga protocol are unit-tested on the host
  against a fake Amiga, in CI on every push that touches the firmware.

Build it with `make firmware`, test it with `make firmware-test`, and flash it with
`make firmware-flash`.

## Status

Designed, routed, and passing DRC; the firmware builds and passes its tests. On the first board,
before its switches were fitted, the firmware flashed over USB and the USB keyboard works on initial
testing. The Amiga side hasn't been tried yet.
