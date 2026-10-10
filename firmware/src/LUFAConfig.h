/* LUFA compile-time options: a full-speed, device-only keyboard with flash descriptors. */
#ifndef LUFA_CONFIG_H
#define LUFA_CONFIG_H

#define USE_STATIC_OPTIONS          (USB_DEVICE_OPT_FULLSPEED | USB_OPT_REG_ENABLED | USB_OPT_AUTO_PLL)
#define USB_DEVICE_ONLY
#define USE_FLASH_DESCRIPTORS
#define FIXED_CONTROL_ENDPOINT_SIZE 8
#define FIXED_NUM_CONFIGURATIONS    1
#define NO_INTERNAL_SERIAL
#define NO_DEVICE_REMOTE_WAKEUP
#define NO_DEVICE_SELF_POWER

#endif
