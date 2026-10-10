/* What the keys mean: Amiga codes, the USB report and the bootloader key combination. */
#ifndef KEYBOARD_H
#define KEYBOARD_H

#include <stdbool.h>
#include <stdint.h>

#include "matrix.h"

#define KEYBOARD_NO_KEY 0xFF
#define KEYBOARD_HID_KEYS 6

/* The Amiga raw key code at a matrix position, or KEYBOARD_NO_KEY. */
uint8_t keyboard_amiga_code(uint8_t row, uint8_t col);

/* A boot-protocol keyboard report from the keys down: modifier bits and up to six usages, or
   six "rollover error" usages when more than six other keys are down. */
void keyboard_hid_report(const uint16_t state[MATRIX_ROWS], uint8_t *modifier,
                         uint8_t keys[KEYBOARD_HID_KEYS]);

/* Ctrl, both Alts and Help held: jump to the USB bootloader. */
bool keyboard_bootloader_keys(const uint16_t state[MATRIX_ROWS]);

#endif
