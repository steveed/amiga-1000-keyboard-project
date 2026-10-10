/* The Amiga keyboard protocol (Amiga Hardware Reference Manual, appendix H), non-blocking, so
   USB keeps running while a key code waits for its handshake. */
#ifndef AMIGA_H
#define AMIGA_H

#include <stdbool.h>
#include <stdint.h>

#define AMIGA_CAPS_LOCK  0x62
#define AMIGA_CTRL       0x63
#define AMIGA_L_AMIGA    0x66
#define AMIGA_R_AMIGA    0x67

#define AMIGA_LOST_SYNC  0xF9
#define AMIGA_OVERFLOW   0xFA
#define AMIGA_POWERUP_START 0xFD
#define AMIGA_POWERUP_END   0xFE

#define AMIGA_SYNC_MS    143   /* the Amiga's handshake must come within this */
#define AMIGA_SETTLE_MS  100   /* after the Amiga's 5 V appears, before the first sync */
#define AMIGA_RESET_MS   500   /* Ctrl-Amiga-Amiga holds KCLK low at least this long */

void amiga_init(void);
/* A key went down or up: its raw key code (0x00-0x67). */
void amiga_key(uint8_t code, bool down);
/* Run the protocol; call it every pass of the main loop.  It needn't catch the handshake pulse
   as it happens: the HAL latches it. */
void amiga_task(uint16_t now_ms);
/* True while the Amiga is powered and so owns the Caps Lock state. */
bool amiga_active(void);
bool amiga_caps_lock(void);

#endif
