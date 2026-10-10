#include <avr/io.h>
#include <util/delay.h>

#include "matrix.h"

/* Rows: PF0, PF1, PF4, PF5, PF6, PF7, PC6, PD7.  Each key is COLn - switch - diode - ROWn, so a
   closed switch pulls its column low while its row is driven low; the rows not being read are
   driven high and their diodes block. */
static volatile uint8_t *const row_port[MATRIX_ROWS] = {
    &PORTF, &PORTF, &PORTF, &PORTF, &PORTF, &PORTF, &PORTC, &PORTD,
};
static const uint8_t row_bit[MATRIX_ROWS] = { 0, 1, 4, 5, 6, 7, 6, 7 };

#define ROWS_F  0xF3   /* PF0, PF1, PF4-PF7 */
#define COLS_B  0x7F   /* PB0-PB6: columns 0-6 */
#define COLS_D  0x73   /* PD0, PD1, PD4-PD6: columns 7-11 */

/* Time for a column to recover through its pull-up after the previous row lets go. */
#define SETTLE_US 10

static void rows_idle(void)
{
    PORTF |= ROWS_F;
    PORTC |= _BV(PC6);
    PORTD |= _BV(PD7);
}

void matrix_init(void)
{
    rows_idle();
    DDRF |= ROWS_F;
    DDRC |= _BV(PC6);
    DDRD |= _BV(PD7);

    DDRB &= ~COLS_B;
    PORTB |= COLS_B;
    DDRD &= ~COLS_D;
    PORTD |= COLS_D;
}

static uint16_t read_cols(void)
{
    uint8_t b = PINB, d = PIND;
    uint16_t high = (b & COLS_B)
                  | (uint16_t)(d & 0x03) << 7
                  | (uint16_t)((d >> 4) & 0x07) << 9;
    return ~high & 0x0FFF;
}

void matrix_read(uint16_t raw[MATRIX_ROWS])
{
    for (uint8_t r = 0; r < MATRIX_ROWS; r++) {
        *row_port[r] &= ~_BV(row_bit[r]);
        _delay_us(SETTLE_US);
        raw[r] = read_cols();
        *row_port[r] |= _BV(row_bit[r]);
    }
}
