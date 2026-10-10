/* The 8 x 12 key matrix: rows driven low one at a time, columns read with pull-ups. */
#ifndef MATRIX_H
#define MATRIX_H

#include <stdint.h>

#define MATRIX_ROWS 8
#define MATRIX_COLS 12

void matrix_init(void);
/* One scan: bit c of raw[r] is set while the switch at row r, column c is closed. */
void matrix_read(uint16_t raw[MATRIX_ROWS]);

#endif
