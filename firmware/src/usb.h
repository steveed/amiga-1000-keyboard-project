/* The USB keyboard (LUFA's HID class driver), reporting the debounced keys. */
#ifndef USB_H
#define USB_H

#include <stdbool.h>

void usb_init(void);
void usb_task(void);
bool usb_configured(void);
/* The host's Caps Lock LED; false while USB is unplugged. */
bool usb_caps_lock(void);

#endif
