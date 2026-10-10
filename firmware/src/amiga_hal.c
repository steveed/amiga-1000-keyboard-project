/* KCLK/KDAT bit timing from Henryk Richter's A500KB (amiga_kbsend, amiga_kbsync): data set 20 us
   before the clock falls, clock low 20 us, high 20 us or more. */
#include <avr/io.h>
#include <util/delay.h>

#include "amiga_hal.h"
#include "board.h"

static bool kdat_was_low;   /* the Amiga had KDAT low as we let go of it */

static void line_low(uint8_t bit) { DDRD |= _BV(bit); }
static void line_release(uint8_t bit) { DDRD &= ~_BV(bit); }

void amiga_hal_init(void)
{
    PORTD &= ~(_BV(KCLK_BIT) | _BV(KDAT_BIT));   /* never a pull-up: the Amiga pulls them up */
    amiga_hal_release();
    EICRA = (EICRA & ~(_BV(ISC31) | _BV(ISC30))) | _BV(ISC31);   /* INT3 flag on a falling KDAT */
    EIFR = _BV(INTF3);
}

bool amiga_hal_powered(void)
{
    return AMIGA_PWR_PIN & _BV(AMIGA_PWR_BIT);
}

void amiga_hal_release(void)
{
    line_release(KCLK_BIT);
    line_release(KDAT_BIT);
}

void amiga_hal_kclk_low(bool low)
{
    if (low)
        line_low(KCLK_BIT);
    else
        line_release(KCLK_BIT);
}

void amiga_hal_clock_out(uint8_t bits, uint8_t count)
{
    while (count--) {
        if (bits & 0x80)
            line_low(KDAT_BIT);
        else
            line_release(KDAT_BIT);
        bits <<= 1;
        _delay_us(20);
        /* that was the last falling edge of ours on KDAT: any later one is the Amiga's handshake */
        if (!count)
            EIFR = _BV(INTF3);
        line_low(KCLK_BIT);
        _delay_us(20);
        line_release(KCLK_BIT);
        _delay_us(20);
    }
    _delay_us(20);
    line_release(KDAT_BIT);
    _delay_us(1);
    /* if we were holding KDAT low for a 1 bit, the Amiga's handshake makes no edge of its own */
    kdat_was_low = !(PIND & _BV(KDAT_BIT));
}

bool amiga_hal_handshake(void)
{
    if (kdat_was_low || (EIFR & _BV(INTF3))) {
        kdat_was_low = false;
        EIFR = _BV(INTF3);
        return true;
    }
    return false;
}

bool amiga_hal_kdat_low(void)
{
    return !(PIND & _BV(KDAT_BIT));
}
