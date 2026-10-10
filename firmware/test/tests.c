/* Host-side tests for the keymap, debouncing, the USB report and the Amiga protocol. */
#include <stdio.h>
#include <string.h>

#include "amiga.h"
#include "debounce.h"
#include "fake_amiga.h"
#include "keyboard.h"

static int failures, checks;

#define CHECK(cond) do { \
        checks++; \
        if (!(cond)) { failures++; printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); } \
    } while (0)

/* matrix positions, from firmware/src/keymap.h */
#define ESC      0, 0
#define CTRL     3, 0
#define CAPS     3, 1
#define KEY_A    3, 2
#define L_SHIFT  4, 0
#define L_ALT    5, 0
#define L_AMIGA  5, 1
#define R_AMIGA  5, 3
#define R_ALT    5, 4
#define HELP     6, 7

/* ------------------------------------------------------------------ keymap */

static void test_keymap(void)
{
    int seen[128] = {0}, keys = 0;
    for (uint8_t r = 0; r < MATRIX_ROWS; r++)
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            uint8_t code = keyboard_amiga_code(r, c);
            if (code == KEYBOARD_NO_KEY)
                continue;
            CHECK(code < 0x68);
            seen[code]++;
            keys++;
        }
    CHECK(keys == 91);
    for (int i = 0; i < 128; i++)
        CHECK(seen[i] <= 1);
    CHECK(keyboard_amiga_code(ESC) == 0x45);
    CHECK(keyboard_amiga_code(CAPS) == AMIGA_CAPS_LOCK);
    CHECK(keyboard_amiga_code(KEY_A) == 0x20);
    CHECK(keyboard_amiga_code(5, 11) == KEYBOARD_NO_KEY);
}

/* ------------------------------------------------------------------ debounce */

static int changes, last_row, last_col, last_down;

static void on_change(uint8_t row, uint8_t col, bool down)
{
    changes++;
    last_row = row, last_col = col, last_down = down;
}

static void scan(uint8_t row, uint8_t col, bool closed)
{
    uint16_t raw[MATRIX_ROWS] = {0};
    if (closed)
        raw[row] = 1 << col;
    debounce_update(raw, on_change);
}

static void test_debounce(void)
{
    debounce_init();
    changes = 0;
    /* contact bounce, then closed: one press, DEBOUNCE_MS scans after it settles */
    scan(KEY_A, 1); scan(KEY_A, 0); scan(KEY_A, 1); scan(KEY_A, 0);
    for (int i = 0; i < DEBOUNCE_MS - 1; i++)
        scan(KEY_A, 1);
    CHECK(changes == 0);
    scan(KEY_A, 1);
    CHECK(changes == 1 && last_row == 3 && last_col == 2 && last_down);
    CHECK(debounce_state[3] == 1 << 2);
    /* a one-scan glitch open doesn't release it */
    scan(KEY_A, 0);
    for (int i = 0; i < 10; i++)
        scan(KEY_A, 1);
    CHECK(changes == 1);
    /* a real release */
    for (int i = 0; i < DEBOUNCE_MS; i++)
        scan(KEY_A, 0);
    CHECK(changes == 2 && !last_down && debounce_state[3] == 0);
}

/* ------------------------------------------------------------------ USB report */

static void test_hid_report(void)
{
    uint16_t state[MATRIX_ROWS] = {0};
    uint8_t mods, keys[KEYBOARD_HID_KEYS];

    state[3] = 1 << 2;                       /* A */
    state[4] = 1 << 0;                       /* L SHIFT */
    state[5] = 1 << 1;                       /* L AMIGA */
    keyboard_hid_report(state, &mods, keys);
    CHECK(mods == ((1 << 1) | (1 << 3)));   /* left shift, left GUI */
    CHECK(keys[0] == 0x04);
    for (int i = 1; i < KEYBOARD_HID_KEYS; i++)
        CHECK(keys[i] == 0);

    state[1] = 0x7F;                         /* ` and 1-6: seven keys */
    keyboard_hid_report(state, &mods, keys);
    for (int i = 0; i < KEYBOARD_HID_KEYS; i++)
        CHECK(keys[i] == 0x01);              /* rollover error */
}

static void test_bootloader_keys(void)
{
    uint16_t state[MATRIX_ROWS] = {0};
    state[3] = 1 << 0;                       /* CTRL */
    state[5] = (1 << 0) | (1 << 4);          /* both ALTs */
    CHECK(!keyboard_bootloader_keys(state));
    state[6] = 1 << 7;                       /* HELP */
    CHECK(keyboard_bootloader_keys(state));
}

/* ------------------------------------------------------------------ Amiga protocol */

static uint16_t now;

static void run(int ms)
{
    while (ms--)
        amiga_task(now++);
}

static void press(uint8_t row, uint8_t col, bool down)
{
    amiga_key(keyboard_amiga_code(row, col), down);
}

/* Amiga on, keyboard synced and through its power-up stream. */
static void amiga_up(void)
{
    fake_reset();
    amiga_init();
    fake.powered = true;
    run(AMIGA_SETTLE_MS + 20);
    fake.nrx = 0;
}

static void test_amiga_unpowered(void)
{
    fake_reset();
    amiga_init();
    press(KEY_A, true);
    press(KEY_A, false);
    run(1000);
    CHECK(fake.nrx == 0 && fake.syncs == 0);
    CHECK(!fake.driven_unpowered);
    CHECK(!amiga_active());
}

static void test_amiga_wire_order(void)
{
    amiga_up();
    press(ESC, true);
    press(ESC, false);
    run(10);
    CHECK(fake.nrx == 2);
    CHECK(fake.wire[0] == 0x8A);   /* $45: bits 6-0 then up = 0 */
    CHECK(fake.wire[1] == 0x8B);   /* $C5: the same, up = 1 */
}

static void test_amiga_powerup(void)
{
    fake_reset();
    amiga_init();
    press(KEY_A, true);            /* held while the Amiga starts */
    press(CAPS, true);             /* Caps Lock is latched off at power-up, never in the stream */
    fake.powered = true;
    run(AMIGA_SETTLE_MS - 1);
    CHECK(fake.syncs == 0);
    run(20);
    CHECK(fake.syncs == 1);
    CHECK(fake.nrx == 3);
    CHECK(fake.rx[0] == AMIGA_POWERUP_START && fake.rx[1] == 0x20 && fake.rx[2] == AMIGA_POWERUP_END);
    CHECK(!amiga_caps_lock());
    press(KEY_A, false);
    run(5);
    CHECK(fake.nrx == 4 && fake.rx[3] == 0xA0);
}

static void test_amiga_keeps_syncing(void)
{
    fake_reset();
    amiga_init();
    fake.powered = true;
    fake.quiet = 1000;             /* the Amiga isn't listening yet (still booting) */
    run(AMIGA_SETTLE_MS + 10 * AMIGA_SYNC_MS + 5);
    CHECK(fake.syncs == 11);
    CHECK(fake.nrx == 0);
}

static void test_amiga_caps_lock(void)
{
    amiga_up();
    press(CAPS, true);
    press(CAPS, false);
    run(10);
    CHECK(amiga_caps_lock());
    press(CAPS, true);
    press(CAPS, false);
    run(10);
    CHECK(!amiga_caps_lock());
    CHECK(fake.nrx == 2 && fake.rx[0] == 0x62 && fake.rx[1] == 0xE2);
}

static void test_amiga_lost_sync(void)
{
    amiga_up();
    fake.quiet = 3;                /* misses the code and the next two sync pulses */
    press(KEY_A, true);
    run(5);
    CHECK(fake.nrx == 1 && fake.syncs == 1);
    run(AMIGA_SYNC_MS);
    CHECK(fake.syncs == 2);        /* gave up on the handshake: resyncing */
    run(2 * AMIGA_SYNC_MS + 10);
    CHECK(fake.syncs == 4);
    /* answered: "lost sync", then the code again */
    CHECK(fake.nrx == 3 && fake.rx[1] == AMIGA_LOST_SYNC && fake.rx[2] == 0x20);
    press(KEY_A, false);
    run(5);
    CHECK(fake.nrx == 4 && fake.rx[3] == 0xA0);
}

static void test_amiga_overflow(void)
{
    amiga_up();
    fake.quiet = 1;                /* hold up the first code while more pile in */
    for (int i = 0; i < 20; i++) {
        press(KEY_A, true);
        press(KEY_A, false);
    }
    run(AMIGA_SYNC_MS + 200);
    /* the 32-code queue kept 31 of the 40 after the one in flight; then $FA reported the loss */
    int fa = 0;
    for (int i = 0; i < fake.nrx; i++)
        fa += fake.rx[i] == AMIGA_OVERFLOW;
    CHECK(fa == 1);
    CHECK(fake.rx[fake.nrx - 1] == AMIGA_OVERFLOW);
}

static void test_amiga_reset(void)
{
    amiga_up();
    press(CTRL, true);
    press(L_AMIGA, true);
    press(R_AMIGA, true);
    run(2);
    CHECK(fake.kclk_low);
    press(CTRL, false);
    press(L_AMIGA, false);
    press(R_AMIGA, false);
    run(AMIGA_RESET_MS - 10);
    CHECK(fake.kclk_low);          /* held for the full 500 ms even when let go sooner */
    run(20);
    CHECK(!fake.kclk_low);
    /* then starts over, as after power-up */
    int before = fake.nrx;
    run(AMIGA_SETTLE_MS + 20);
    CHECK(fake.nrx == before + 2 && fake.rx[before] == AMIGA_POWERUP_START);
}

static void test_amiga_power_loss(void)
{
    amiga_up();
    press(CAPS, true);
    run(5);
    CHECK(amiga_caps_lock());
    fake.quiet = 1;
    press(KEY_A, true);
    run(2);                        /* mid-transfer, waiting for a handshake */
    fake.powered = false;
    run(500);
    CHECK(!amiga_active());
    CHECK(!amiga_caps_lock());
    CHECK(!fake.driven_unpowered);
}

int main(void)
{
    struct { const char *name; void (*fn)(void); } tests[] = {
        {"keymap", test_keymap},
        {"debounce", test_debounce},
        {"hid report", test_hid_report},
        {"bootloader keys", test_bootloader_keys},
        {"amiga: unpowered", test_amiga_unpowered},
        {"amiga: wire order", test_amiga_wire_order},
        {"amiga: power-up stream", test_amiga_powerup},
        {"amiga: keeps syncing", test_amiga_keeps_syncing},
        {"amiga: caps lock", test_amiga_caps_lock},
        {"amiga: lost sync", test_amiga_lost_sync},
        {"amiga: overflow", test_amiga_overflow},
        {"amiga: reset", test_amiga_reset},
        {"amiga: power loss", test_amiga_power_loss},
    };
    for (size_t i = 0; i < sizeof tests / sizeof tests[0]; i++) {
        int before = failures;
        tests[i].fn();
        printf("%s %s\n", failures == before ? "ok  " : "FAIL", tests[i].name);
    }
    printf("%d checks, %d failed\n", checks, failures);
    return failures != 0;
}
