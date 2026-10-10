/* After LUFA's Keyboard class driver demo (licence in descriptors.h). */
#include <LUFA/Drivers/USB/USB.h>

#include "debounce.h"
#include "descriptors.h"
#include "keyboard.h"
#include "usb.h"

static uint8_t prev_report[sizeof(USB_KeyboardReport_Data_t)];
static bool caps_led;

static USB_ClassInfo_HID_Device_t keyboard_hid = {
    .Config = {
        .InterfaceNumber        = INTERFACE_ID_Keyboard,
        .ReportINEndpoint       = {
            .Address            = KEYBOARD_EPADDR,
            .Size               = KEYBOARD_EPSIZE,
            .Banks              = 1,
        },
        .PrevReportINBuffer     = prev_report,
        .PrevReportINBufferSize = sizeof(prev_report),
    },
};

void usb_init(void)
{
    USB_Init();
}

void usb_task(void)
{
    HID_Device_USBTask(&keyboard_hid);
    USB_USBTask();
}

bool usb_configured(void)
{
    return USB_DeviceState == DEVICE_STATE_Configured;
}

bool usb_caps_lock(void)
{
    return caps_led && usb_configured();
}

void EVENT_USB_Device_Disconnect(void)
{
    caps_led = false;
}

void EVENT_USB_Device_ConfigurationChanged(void)
{
    HID_Device_ConfigureEndpoints(&keyboard_hid);
    USB_Device_EnableSOFEvents();
}

void EVENT_USB_Device_ControlRequest(void)
{
    HID_Device_ProcessControlRequest(&keyboard_hid);
}

void EVENT_USB_Device_StartOfFrame(void)
{
    HID_Device_MillisecondElapsed(&keyboard_hid);
}

bool CALLBACK_HID_Device_CreateHIDReport(USB_ClassInfo_HID_Device_t *const info, uint8_t *const report_id,
                                         const uint8_t report_type, void *data, uint16_t *const size)
{
    USB_KeyboardReport_Data_t *report = data;

    (void)info, (void)report_id, (void)report_type;
    keyboard_hid_report(debounce_state, &report->Modifier, report->KeyCode);
    *size = sizeof(USB_KeyboardReport_Data_t);
    return false;   /* let the driver send it only when it changes or the idle period runs out */
}

void CALLBACK_HID_Device_ProcessHIDReport(USB_ClassInfo_HID_Device_t *const info, const uint8_t report_id,
                                          const uint8_t report_type, const void *data, const uint16_t size)
{
    (void)info, (void)report_id;
    if (report_type == HID_REPORT_ITEM_Out && size >= 1)
        caps_led = *(const uint8_t *)data & HID_KEYBOARD_LED_CAPSLOCK;
}
