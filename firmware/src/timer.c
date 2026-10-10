#include <avr/interrupt.h>
#include <avr/io.h>
#include <util/atomic.h>

#include "timer.h"

static volatile uint16_t ticks;

ISR(TIMER0_COMPA_vect)
{
    ticks++;
}

void timer_init(void)
{
    TCCR0A = _BV(WGM01);                 /* CTC */
    TCCR0B = _BV(CS01) | _BV(CS00);      /* F_CPU / 64 = 250 kHz */
    OCR0A = F_CPU / 64 / 1000 - 1;       /* 1 kHz */
    TIMSK0 = _BV(OCIE0A);
}

uint16_t timer_ms(void)
{
    uint16_t t;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        t = ticks;
    }
    return t;
}
