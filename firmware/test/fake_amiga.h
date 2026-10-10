/* A fake Amiga behind amiga_hal.h: it records what the keyboard clocks out and answers each
   transfer with a handshake, unless told to stay quiet. */
#ifndef FAKE_AMIGA_H
#define FAKE_AMIGA_H

#include <stdbool.h>
#include <stdint.h>

struct fake_amiga {
    bool powered;
    int quiet;              /* transfers left to ignore (no handshake) */
    bool kclk_low;
    uint8_t rx[256];        /* codes received, unrotated: bit 7 is the up flag */
    uint8_t wire[256];      /* the same, in the order the bits went out */
    int nrx;
    int syncs;              /* sync pulses (single 1 bits) */
    bool driven_unpowered;  /* the keyboard touched a line with the Amiga off */
    bool pending;
};

extern struct fake_amiga fake;
void fake_reset(void);

#endif
