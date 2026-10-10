/* Millisecond tick from timer 0. */
#ifndef TIMER_H
#define TIMER_H

#include <stdint.h>

void timer_init(void);
uint16_t timer_ms(void);   /* wraps every 65.5 s: compare times by subtraction */

#endif
