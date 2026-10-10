# Rev 2 firmware (ATmega32U4) and its host-side unit tests.  Run through the repo's Makefile
# (`make firmware`, `make firmware-test`), which runs this in the firmware container.

MCU   := atmega32u4
F_CPU := 16000000
BUILD ?= ../build/firmware
NAME  := amiga-1000-keyboard-rev2

LUFA := lufa/LUFA
LUFA_SRC := $(addprefix $(LUFA)/Drivers/USB/, \
	Core/AVR8/Device_AVR8.c Core/AVR8/Endpoint_AVR8.c Core/AVR8/EndpointStream_AVR8.c \
	Core/AVR8/USBController_AVR8.c Core/AVR8/USBInterrupt_AVR8.c Core/ConfigDescriptors.c \
	Core/DeviceStandardReq.c Core/Events.c Core/USBTask.c Class/Device/HIDClassDevice.c)
SRC := $(addprefix src/, main.c timer.c matrix.c debounce.c keyboard.c amiga.c amiga_hal.c \
	usb.c descriptors.c bootloader.c) $(LUFA_SRC)
OBJ := $(SRC:%.c=$(BUILD)/obj/%.o)

CC := avr-gcc
CFLAGS := -mmcu=$(MCU) -DF_CPU=$(F_CPU)UL -DF_USB=$(F_CPU)UL -DARCH=ARCH_AVR8 \
	-DUSE_LUFA_CONFIG_HEADER -Isrc -Ilufa -Os -std=gnu99 -Wall \
	-funsigned-char -funsigned-bitfields -fshort-enums -fno-strict-aliasing \
	-ffunction-sections -fdata-sections -mrelax
LDFLAGS := -mmcu=$(MCU) -Wl,--gc-sections -mrelax

# Host tests: the pure logic against a fake Amiga.
TEST_SRC := test/tests.c test/fake_amiga.c src/debounce.c src/keyboard.c src/amiga.c
TEST_CFLAGS := -Isrc -Itest -std=gnu99 -Wall -Wextra -Werror -g

.PHONY: all test clean
all: $(BUILD)/$(NAME).hex

$(BUILD)/$(NAME).elf: $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $^
	avr-size --mcu=$(MCU) -C $@ | grep -E 'Program|Data'

$(BUILD)/$(NAME).hex: $(BUILD)/$(NAME).elf
	avr-objcopy -O ihex -R .eeprom $< $@

$(BUILD)/obj/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ): src/*.h

test:
	@mkdir -p $(BUILD)
	gcc $(TEST_CFLAGS) -o $(BUILD)/tests $(TEST_SRC)
	$(BUILD)/tests

clean:
	rm -rf $(BUILD)
