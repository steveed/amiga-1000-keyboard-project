/* Per-key debouncing: a key changes state once its switch has read the other way on DEBOUNCE_MS
   consecutive scans (one scan per millisecond). */
#ifndef DEBOUNCE_H
#define DEBOUNCE_H

#include <stdbool.h>
#include <stdint.h>

#include "matrix.h"

#define DEBOUNCE_MS 5

typedef void (*debounce_change_fn)(uint8_t row, uint8_t col, bool down);

/* Debounced state: bit c of debounce_state[r] is set while that key is down. */
extern uint16_t debounce_state[MATRIX_ROWS];

void debounce_init(void);
/* Feed one scan; calls on_change for each key that settles into a new state. */
void debounce_update(const uint16_t raw[MATRIX_ROWS], debounce_change_fn on_change);

#endif
