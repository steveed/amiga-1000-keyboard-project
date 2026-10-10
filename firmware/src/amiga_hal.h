/* The KCLK/KDAT lines and the Amiga power sense, for amiga.c.  amiga_hal.c implements them on the
   AVR; the unit tests have a fake Amiga behind them. */
#ifndef AMIGA_HAL_H
#define AMIGA_HAL_H

#include <stdbool.h>
#include <stdint.h>

void amiga_hal_init(void);
bool amiga_hal_powered(void);
/* Let go of both lines. */
void amiga_hal_release(void);
/* Hold KCLK low (the Amiga's hard reset) or let it go. */
void amiga_hal_kclk_low(bool low);
/* Clock out `count` bits of `bits`, most significant first; a 1 pulls KDAT low.  Returns with
   both lines released, ready to catch the handshake. */
void amiga_hal_clock_out(uint8_t bits, uint8_t count);
/* True once the Amiga has pulled KDAT low since the last amiga_hal_clock_out (it may already
   have let go again). */
bool amiga_hal_handshake(void);
bool amiga_hal_kdat_low(void);

#endif
