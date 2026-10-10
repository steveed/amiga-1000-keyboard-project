#include <string.h>

#include "amiga_hal.h"
#include "fake_amiga.h"

struct fake_amiga fake;

void fake_reset(void)
{
    memset(&fake, 0, sizeof fake);
}

void amiga_hal_init(void) {}

bool amiga_hal_powered(void)
{
    return fake.powered;
}

void amiga_hal_release(void)
{
    fake.kclk_low = false;
}

void amiga_hal_kclk_low(bool low)
{
    if (!fake.powered)
        fake.driven_unpowered = true;
    fake.kclk_low = low;
}

void amiga_hal_clock_out(uint8_t bits, uint8_t count)
{
    if (!fake.powered)
        fake.driven_unpowered = true;
    if (count == 1) {
        fake.syncs++;
    } else {
        fake.wire[fake.nrx] = bits;
        fake.rx[fake.nrx++] = (uint8_t)(bits >> 1 | bits << 7);
    }
    if (fake.quiet > 0)
        fake.quiet--;
    else
        fake.pending = true;
}

bool amiga_hal_handshake(void)
{
    bool h = fake.pending;
    fake.pending = false;
    return h;
}

bool amiga_hal_kdat_low(void)
{
    return false;
}
