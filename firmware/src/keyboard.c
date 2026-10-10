#include "keyboard.h"

#ifdef __AVR__
#include <avr/pgmspace.h>
#define KEYMAP_FLASH PROGMEM
#define KEYMAP_READ(x) pgm_read_byte(&(x))
#else
#define KEYMAP_FLASH
#define KEYMAP_READ(x) (x)
#endif
#include "keymap.h"

#define HID_ROLLOVER    0x01
#define HID_FIRST_MOD   0xE0   /* Left Ctrl; 0xE0-0xE7 are modifier bits 0-7 */

#define AMIGA_HELP  0x5F
#define AMIGA_CTRL  0x63
#define AMIGA_L_ALT 0x64
#define AMIGA_R_ALT 0x65

uint8_t keyboard_amiga_code(uint8_t row, uint8_t col)
{
    uint8_t code = KEYMAP_READ(keymap_amiga[row][col]);
    return code == KEYMAP_NONE ? KEYBOARD_NO_KEY : code;
}

void keyboard_hid_report(const uint16_t state[MATRIX_ROWS], uint8_t *modifier,
                         uint8_t keys[KEYBOARD_HID_KEYS])
{
    uint8_t n = 0;
    bool rollover = false;

    *modifier = 0;
    for (uint8_t r = 0; r < MATRIX_ROWS; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            if (!(state[r] & (uint16_t)1 << c))
                continue;
            uint8_t usage = KEYMAP_READ(keymap_hid[r][c]);
            if (usage >= HID_FIRST_MOD)
                *modifier |= 1 << (usage - HID_FIRST_MOD);
            else if (n < KEYBOARD_HID_KEYS)
                keys[n++] = usage;
            else if (usage)
                rollover = true;
        }
    }
    for (uint8_t i = 0; i < KEYBOARD_HID_KEYS; i++) {
        if (rollover)
            keys[i] = HID_ROLLOVER;
        else if (i >= n)
            keys[i] = 0;
    }
}

static bool down(const uint16_t state[MATRIX_ROWS], uint8_t code)
{
    for (uint8_t r = 0; r < MATRIX_ROWS; r++)
        for (uint8_t c = 0; c < MATRIX_COLS; c++)
            if ((state[r] & (uint16_t)1 << c) && KEYMAP_READ(keymap_amiga[r][c]) == code)
                return true;
    return false;
}

bool keyboard_bootloader_keys(const uint16_t state[MATRIX_ROWS])
{
    return down(state, AMIGA_CTRL) && down(state, AMIGA_L_ALT) && down(state, AMIGA_R_ALT)
        && down(state, AMIGA_HELP);
}
