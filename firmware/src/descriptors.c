/* USB descriptors, adapted from LUFA's Keyboard class driver demo (licence in descriptors.h). */
#include "descriptors.h"

/* pid.codes VID and this project's PID (https://pid.codes/1209/A10B/). */
#define USB_VID 0x1209
#define USB_PID 0xA10B

const USB_Descriptor_HIDReport_Datatype_t PROGMEM KeyboardReport[] = {
    HID_DESCRIPTOR_KEYBOARD(6)
};

const USB_Descriptor_Device_t PROGMEM DeviceDescriptor = {
    .Header                 = {.Size = sizeof(USB_Descriptor_Device_t), .Type = DTYPE_Device},
    .USBSpecification       = VERSION_BCD(1, 1, 0),
    .Class                  = USB_CSCP_NoDeviceClass,
    .SubClass               = USB_CSCP_NoDeviceSubclass,
    .Protocol               = USB_CSCP_NoDeviceProtocol,
    .Endpoint0Size          = FIXED_CONTROL_ENDPOINT_SIZE,
    .VendorID               = USB_VID,
    .ProductID              = USB_PID,
    .ReleaseNumber          = VERSION_BCD(0, 1, 0),
    .ManufacturerStrIndex   = STRING_ID_Manufacturer,
    .ProductStrIndex        = STRING_ID_Product,
    .SerialNumStrIndex      = NO_DESCRIPTOR,
    .NumberOfConfigurations = FIXED_NUM_CONFIGURATIONS,
};

const USB_Descriptor_Configuration_t PROGMEM ConfigurationDescriptor = {
    .Config = {
        .Header                 = {.Size = sizeof(USB_Descriptor_Configuration_Header_t), .Type = DTYPE_Configuration},
        .TotalConfigurationSize = sizeof(USB_Descriptor_Configuration_t),
        .TotalInterfaces        = 1,
        .ConfigurationNumber    = 1,
        .ConfigurationStrIndex  = NO_DESCRIPTOR,
        .ConfigAttributes       = USB_CONFIG_ATTR_RESERVED,
        .MaxPowerConsumption    = USB_CONFIG_POWER_MA(100),
    },
    .HID_Interface = {
        .Header                 = {.Size = sizeof(USB_Descriptor_Interface_t), .Type = DTYPE_Interface},
        .InterfaceNumber        = INTERFACE_ID_Keyboard,
        .AlternateSetting       = 0,
        .TotalEndpoints         = 1,
        .Class                  = HID_CSCP_HIDClass,
        .SubClass               = HID_CSCP_BootSubclass,
        .Protocol               = HID_CSCP_KeyboardBootProtocol,
        .InterfaceStrIndex      = NO_DESCRIPTOR,
    },
    .HID_KeyboardHID = {
        .Header                 = {.Size = sizeof(USB_HID_Descriptor_HID_t), .Type = HID_DTYPE_HID},
        .HIDSpec                = VERSION_BCD(1, 1, 1),
        .CountryCode            = 0,
        .TotalReportDescriptors = 1,
        .HIDReportType          = HID_DTYPE_Report,
        .HIDReportLength        = sizeof(KeyboardReport),
    },
    .HID_ReportINEndpoint = {
        .Header                 = {.Size = sizeof(USB_Descriptor_Endpoint_t), .Type = DTYPE_Endpoint},
        .EndpointAddress        = KEYBOARD_EPADDR,
        .Attributes             = (EP_TYPE_INTERRUPT | ENDPOINT_ATTR_NO_SYNC | ENDPOINT_USAGE_DATA),
        .EndpointSize           = KEYBOARD_EPSIZE,
        .PollingIntervalMS      = 5,
    },
};

const USB_Descriptor_String_t PROGMEM LanguageString = USB_STRING_DESCRIPTOR_ARRAY(LANGUAGE_ID_ENG);
const USB_Descriptor_String_t PROGMEM ManufacturerString = USB_STRING_DESCRIPTOR(L"amiga-1000-keyboard-project");
const USB_Descriptor_String_t PROGMEM ProductString = USB_STRING_DESCRIPTOR(L"Amiga 1000 Keyboard rev 2");

uint16_t CALLBACK_USB_GetDescriptor(const uint16_t wValue, const uint16_t wIndex,
                                    const void **const DescriptorAddress)
{
    const uint8_t type = wValue >> 8;
    const uint8_t number = wValue & 0xFF;
    const void *address = NULL;
    uint16_t size = NO_DESCRIPTOR;

    (void)wIndex;
    switch (type) {
    case DTYPE_Device:
        address = &DeviceDescriptor;
        size = sizeof(USB_Descriptor_Device_t);
        break;
    case DTYPE_Configuration:
        address = &ConfigurationDescriptor;
        size = sizeof(USB_Descriptor_Configuration_t);
        break;
    case DTYPE_String:
        switch (number) {
        case STRING_ID_Language:
            address = &LanguageString;
            size = pgm_read_byte(&LanguageString.Header.Size);
            break;
        case STRING_ID_Manufacturer:
            address = &ManufacturerString;
            size = pgm_read_byte(&ManufacturerString.Header.Size);
            break;
        case STRING_ID_Product:
            address = &ProductString;
            size = pgm_read_byte(&ProductString.Header.Size);
            break;
        }
        break;
    case HID_DTYPE_HID:
        address = &ConfigurationDescriptor.HID_KeyboardHID;
        size = sizeof(USB_HID_Descriptor_HID_t);
        break;
    case HID_DTYPE_Report:
        address = &KeyboardReport;
        size = sizeof(KeyboardReport);
        break;
    }
    *DescriptorAddress = address;
    return size;
}
