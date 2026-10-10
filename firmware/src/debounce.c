/* Debouncing as in Henryk Richter's A500KB: a count per key of how long its switch has disagreed
   with its state, reset whenever they agree. */
#include "debounce.h"

uint16_t debounce_state[MATRIX_ROWS];
static uint8_t count[MATRIX_ROWS][MATRIX_COLS];

void debounce_init(void)
{
    for (uint8_t r = 0; r < MATRIX_ROWS; r++) {
        debounce_state[r] = 0;
        for (uint8_t c = 0; c < MATRIX_COLS; c++)
            count[r][c] = 0;
    }
}

void debounce_update(const uint16_t raw[MATRIX_ROWS], debounce_change_fn on_change)
{
    for (uint8_t r = 0; r < MATRIX_ROWS; r++) {
        uint16_t differ = raw[r] ^ debounce_state[r];
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            uint16_t bit = (uint16_t)1 << c;
            if (!(differ & bit)) {
                count[r][c] = 0;
            } else if (++count[r][c] >= DEBOUNCE_MS) {
                count[r][c] = 0;
                debounce_state[r] ^= bit;
                on_change(r, c, debounce_state[r] & bit);
            }
        }
    }
}
