/* Amiga 1000 keyboard, rev 2: an ATmega32U4 that talks to the Amiga and to USB at once.

   Ported from Henryk Richter's A500KB firmware (github.com/HenrykRichter/A500KB, CC BY-NC-SA
   4.0), restructured for rev 2's matrix and for both connections being live together.  USB is
   LUFA (firmware/lufa). */
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/power.h>
#include <avr/wdt.h>

#include "amiga.h"
#include "board.h"
#include "bootloader.h"
#include "debounce.h"
#include "keyboard.h"
#include "matrix.h"
#include "timer.h"
#include "usb.h"

static void jtag_off(void)
{
    /* the JTAG pins are matrix rows; JTD has to be written twice within four cycles */
    uint8_t m = MCUCR | _BV(JTD);
    MCUCR = m;
    MCUCR = m;
}

static void key_changed(uint8_t row, uint8_t col, bool down)
{
    uint8_t code = keyboard_amiga_code(row, col);
    if (code != KEYBOARD_NO_KEY)
        amiga_key(code, down);
}

static void caps_led(bool on)
{
    if (on)
        PORTB |= _BV(CAPS_LED_BIT);
    else
        PORTB &= ~_BV(CAPS_LED_BIT);
}

int main(void)
{
    MCUSR = 0;
    wdt_disable();
    clock_prescale_set(clock_div_1);   /* the factory fuses divide the clock by 8 */
    jtag_off();

    DDRB |= _BV(CAPS_LED_BIT);
    caps_led(false);
    matrix_init();
    debounce_init();
    amiga_init();
    timer_init();
    usb_init();
    sei();
    wdt_enable(WDTO_250MS);

    uint16_t last_scan = timer_ms();
    for (;;) {
        wdt_reset();
        uint16_t now = timer_ms();
        if (now != last_scan) {
            uint16_t raw[MATRIX_ROWS];
            last_scan = now;
            matrix_read(raw);
            debounce_update(raw, key_changed);
            /* only with USB up, as the bootloader is no use without it */
            if (usb_configured() && keyboard_bootloader_keys(debounce_state))
                bootloader_jump();
        }
        amiga_task(now);
        usb_task();
        /* the Amiga owns Caps Lock while it's on; otherwise the USB host does */
        caps_led(amiga_active() ? amiga_caps_lock() : usb_caps_lock());
    }
}
