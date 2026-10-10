/* Jump to the 32U4's factory USB (DFU) bootloader, through a watchdog reset so every peripheral
   starts clean (LUFA's recommended method). */
#ifndef BOOTLOADER_H
#define BOOTLOADER_H

void bootloader_jump(void) __attribute__((noreturn));

#endif
