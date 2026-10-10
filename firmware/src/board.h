/* Rev 2 board pins (see pcb/rev_2/README.md, "Pins").  The matrix pins are in matrix.c. */
#ifndef BOARD_H
#define BOARD_H

#include <avr/io.h>

/* Amiga keyboard lines, open drain: the firmware only pulls them low (DDR set, PORT clear) and
   never drives them high or enables a pull-up, so nothing reaches a switched-off Amiga.  KDAT is
   INT3, whose edge flag catches the Amiga's handshake pulse between polls. */
#define KCLK_BIT   PD2
#define KDAT_BIT   PD3

/* TPS2116 status: high while the Amiga's 5 V is the supply in use (R6 pulls it up). */
#define AMIGA_PWR_PIN  PINE
#define AMIGA_PWR_BIT  PE6

/* Caps Lock LED, active high through R3 (OC1C, for dimming later). */
#define CAPS_LED_BIT   PB7

#endif
