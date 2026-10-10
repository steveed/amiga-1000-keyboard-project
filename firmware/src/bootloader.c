#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/wdt.h>
#include <util/delay.h>
#include <LUFA/Drivers/USB/USB.h>

#include "bootloader.h"

/* The factory fuses give the 32U4 a 4 KB boot section, at the top of its 32 KB flash. */
#define BOOTLOADER_START 0x7000
#define MAGIC 0xDC42ACCA

static uint32_t boot_key __attribute__((section(".noinit")));

/* Runs before main, after the watchdog reset bootloader_jump() set up. */
void bootloader_check(void) __attribute__((used, naked, section(".init3")));
void bootloader_check(void)
{
    if ((MCUSR & _BV(WDRF)) && boot_key == MAGIC) {
        boot_key = 0;
        MCUSR &= ~_BV(WDRF);
        wdt_disable();
        ((void (*)(void))(BOOTLOADER_START / 2))();
    }
}

void bootloader_jump(void)
{
    USB_Disable();
    cli();
    wdt_disable();
    _delay_ms(250);   /* let the host see the keyboard go before the bootloader appears */
    boot_key = MAGIC;
    wdt_enable(WDTO_15MS);
    for (;;)
        ;
}
