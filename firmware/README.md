# Rev 2 firmware

Firmware for the rev 2 board's ATmega32U4, ported from Henryk Richter's
[A500KB](https://github.com/HenrykRichter/A500KB) firmware (same licence, CC BY-NC-SA 4.0) and
restructured for rev 2: its 8 x 12 diode matrix, and the Amiga and USB connections both live at
once. USB is [LUFA](https://github.com/abcminiuser/lufa) (`lufa/`, a submodule pinned to release
LUFA-210130; its licence is in `lufa/LUFA/License.txt`).

After cloning, fetch LUFA with `git submodule update --init`.

## Building

- `make firmware` regenerates `src/keymap.h` from the rev 2 matrix (`tools/gen_keymap.py`), then
  builds `build/firmware/amiga-1000-keyboard-rev2.hex`.
- `make firmware-test` runs the unit tests on the host compiler: keymap, debouncing, the USB report
  and the Amiga protocol against a fake Amiga (`test/fake_amiga.c`).
- `make firmware-flash` flashes the board over USB. Unlike the other targets it runs on the host,
  because Docker Desktop on macOS can't pass USB through: `brew install dfu-programmer`.

## Flashing

A blank 32U4 runs straight into its factory USB (DFU) bootloader, so a new board flashes with
`make firmware-flash` as it comes. After that, hold **Ctrl + both Alts + Help** (with USB connected)
to get back to the bootloader. If the firmware can't get there, short JP2 (BOOT) while shorting
JP1 (RESET), or use the ISP header (J3). See `pcb/rev_2/README.md`.

No fuse changes are needed: the firmware turns off the factory clock divider and JTAG itself.

## How it works

- `matrix.c` scans the matrix once a millisecond: each row is driven low in turn and the columns
  are read with pull-ups. `debounce.c` accepts a change after 5 ms steady.
- `amiga.c` speaks the Amiga keyboard protocol as a state machine, so it never blocks waiting
  for the Amiga: sync, the power-up stream (`$FD`, keys already down, `$FE`), lost-sync recovery
  (`$F9` and a retransmit), buffer overflow (`$FA`), Caps Lock latched in the keyboard, and
  Ctrl-Amiga-Amiga holding KCLK low for at least 500 ms (the A1000 has no reset warning). It runs
  only while the Amiga's 5 V is the board's supply (AMIGA_PWR, PE6), and it only ever pulls KCLK
  and KDAT low. The Amiga's handshake pulse is latched by KDAT's INT3 edge flag, so it can't be
  missed between polls. `amiga_hal.c` has the pins and bit timing.
- `usb.c` is a boot-protocol USB keyboard (6 keys plus modifiers) built from the same debounced
  state.
- Caps Lock: while the Amiga is on, the keyboard latches it and the LED shows that; on USB alone,
  the LED follows the host.
- `keymap.h` is generated: each key's Amiga raw key code and USB usage, looked up by its name
  in the rev 1 schematic. HELP sends the HID Help usage, which most PC hosts ignore.

## Before release

- The USB ID is pid.codes' test ID (`1209:0001`), for private testing only: request a project PID
  from [pid.codes](https://pid.codes) before boards go to other people.

## Still to check on hardware

- Everything: the first boards haven't arrived. In particular the factory DFU bootloader on a
  blank chip, the Amiga handshake catch, the matrix settle time (10 us per row), the reset on a
  real A1000, and both connections live together.
