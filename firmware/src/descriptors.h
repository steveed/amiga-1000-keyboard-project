/* USB descriptors, adapted from LUFA's Keyboard class driver demo:

     LUFA Library, Copyright (C) Dean Camera, 2021.
     Permission to use, copy, modify, distribute, and sell this software and its documentation
     for any purpose is hereby granted without fee, provided that the above copyright notice
     appear in all copies and that both that the copyright notice and this permission notice and
     warranty disclaimer appear in supporting documentation, and that the name of the author not
     be used in advertising or publicity pertaining to distribution of the software without
     specific, written prior permission.  The author disclaims all warranties with regard to
     this software (see firmware/lufa/LUFA/License.txt). */
#ifndef DESCRIPTORS_H
#define DESCRIPTORS_H

#include <avr/pgmspace.h>
#include <LUFA/Drivers/USB/USB.h>

typedef struct {
    USB_Descriptor_Configuration_Header_t Config;
    USB_Descriptor_Interface_t            HID_Interface;
    USB_HID_Descriptor_HID_t              HID_KeyboardHID;
    USB_Descriptor_Endpoint_t             HID_ReportINEndpoint;
} USB_Descriptor_Configuration_t;

enum InterfaceDescriptors_t {
    INTERFACE_ID_Keyboard = 0,
};

enum StringDescriptors_t {
    STRING_ID_Language     = 0,
    STRING_ID_Manufacturer = 1,
    STRING_ID_Product      = 2,
};

#define KEYBOARD_EPADDR (ENDPOINT_DIR_IN | 1)
#define KEYBOARD_EPSIZE 8

uint16_t CALLBACK_USB_GetDescriptor(const uint16_t wValue, const uint16_t wIndex,
                                    const void **const DescriptorAddress)
    ATTR_WARN_UNUSED_RESULT ATTR_NON_NULL_PTR_ARG(3);

#endif
