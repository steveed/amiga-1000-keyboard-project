/* The Amiga keyboard protocol, after Henryk Richter's A500KB, rebuilt as a state machine so that
   it never waits in a loop.  Each code goes out as 8 bits, key code first and the up flag last,
   and the Amiga answers with a handshake pulse on KDAT.  With no handshake in 143 ms the keyboard
   has lost sync: it clocks out 1 bits, one per 143 ms, until one is answered, then sends
   "lost sync" ($F9) and the code again.  After power-up it sends $FD, the keys already down, $FE.

   The A1000 has no reset warning: Ctrl-Amiga-Amiga holds KCLK low, which resets the machine. */
#include "amiga.h"
#include "amiga_hal.h"

enum state {
    OFF,            /* no Amiga power: lines let go */
    SETTLE,         /* Amiga power just appeared */
    SYNC,           /* clocked out a 1 bit, waiting for its handshake */
    WAIT_ACK,       /* sent a code, waiting for its handshake */
    WAIT_RELEASE,   /* handshake seen, waiting for KDAT to come back up */
    IDLE,
    RESET,          /* holding KCLK low */
};

#define QUEUE_SIZE 32

static uint8_t state;
static uint16_t since;          /* when the current state began */
static uint8_t queue[QUEUE_SIZE], q_head, q_count;
static bool overflow;           /* a code was dropped: send $FA when there's room */
static uint8_t held[16];        /* raw key codes down, a bit each */
static bool caps;
static bool powerup;            /* first sync not yet made: send the power-up stream after it */
static bool lost;               /* resyncing after a missed handshake */
static uint8_t prefix;          /* $F9 to send before retransmitting, or 0 */
static uint8_t inflight;        /* the queued code being sent, kept until the Amiga takes it */
static bool have_inflight, sending_prefix;

static bool is_held(uint8_t code) { return held[code >> 3] & (1 << (code & 7)); }

static void set_held(uint8_t code, bool down)
{
    if (down)
        held[code >> 3] |= 1 << (code & 7);
    else
        held[code >> 3] &= ~(1 << (code & 7));
}

static void push(uint8_t b)
{
    if (q_count == QUEUE_SIZE) {
        overflow = true;
        return;
    }
    queue[(q_head + q_count++) % QUEUE_SIZE] = b;
}

static uint8_t pop(void)
{
    uint8_t b = queue[q_head];
    q_head = (q_head + 1) % QUEUE_SIZE;
    q_count--;
    return b;
}

static void enter(uint8_t s, uint16_t now)
{
    state = s;
    since = now;
}

static void sync_pulse(uint16_t now)
{
    amiga_hal_clock_out(0x80, 1);
    enter(SYNC, now);
}

static void start_powerup(uint16_t now)
{
    q_head = q_count = 0;
    overflow = lost = have_inflight = false;
    prefix = 0;
    caps = false;
    powerup = true;
    sync_pulse(now);
}

static void send(uint8_t b, uint16_t now)
{
    /* bits 6-0 then the up flag (bit 7) */
    amiga_hal_clock_out((uint8_t)(b << 1 | b >> 7), 8);
    enter(WAIT_ACK, now);
}

static void send_powerup_stream(void)
{
    push(AMIGA_POWERUP_START);
    for (uint8_t code = 0; code < 0x68; code++)
        if (code != AMIGA_CAPS_LOCK && is_held(code))
            push(code);
    push(AMIGA_POWERUP_END);
}

/* Codes are queued only once the Amiga is listening: before the power-up stream, keys down are
   picked up from `held` instead. */
static bool queueing(void)
{
    return state != OFF && state != SETTLE && state != RESET && !powerup;
}

void amiga_init(void)
{
    amiga_hal_init();
    state = OFF;
    for (uint8_t i = 0; i < sizeof held; i++)
        held[i] = 0;
    caps = false;
}

void amiga_key(uint8_t code, bool down)
{
    set_held(code, down);
    if (!queueing())
        return;
    if (code == AMIGA_CAPS_LOCK) {
        /* Caps Lock latches in the keyboard: down sends the new state, release sends nothing */
        if (down) {
            caps = !caps;
            push(caps ? AMIGA_CAPS_LOCK : AMIGA_CAPS_LOCK | 0x80);
        }
        return;
    }
    push(down ? code : code | 0x80);
}

void amiga_task(uint16_t now)
{
    if (!amiga_hal_powered()) {
        if (state != OFF) {
            amiga_hal_release();
            state = OFF;
            caps = false;
        }
        return;
    }
    if (state == OFF) {
        enter(SETTLE, now);
        return;
    }

    uint16_t elapsed = now - since;
    bool reset_keys = is_held(AMIGA_CTRL) && is_held(AMIGA_L_AMIGA) && is_held(AMIGA_R_AMIGA);
    if (reset_keys && state != RESET && state != SETTLE) {
        amiga_hal_release();
        amiga_hal_kclk_low(true);
        enter(RESET, now);
        return;
    }

    switch (state) {
    case SETTLE:
        if (elapsed >= AMIGA_SETTLE_MS)
            start_powerup(now);
        break;

    case RESET:
        if (!reset_keys && elapsed >= AMIGA_RESET_MS) {
            amiga_hal_kclk_low(false);
            enter(SETTLE, now);   /* the Amiga restarts: sync and send the power-up stream again */
        }
        break;

    case SYNC:
        if (amiga_hal_handshake())
            enter(WAIT_RELEASE, now);
        else if (elapsed >= AMIGA_SYNC_MS)
            sync_pulse(now);
        break;

    case WAIT_ACK:
        if (amiga_hal_handshake()) {
            if (sending_prefix)
                prefix = 0;
            else
                have_inflight = false;
            enter(WAIT_RELEASE, now);
        } else if (elapsed >= AMIGA_SYNC_MS) {
            lost = true;
            sync_pulse(now);
        }
        break;

    case WAIT_RELEASE:
        if (!amiga_hal_kdat_low()) {
            if (powerup) {
                powerup = lost = false;
                send_powerup_stream();
            } else if (lost) {
                lost = false;
                prefix = AMIGA_LOST_SYNC;
            }
            enter(IDLE, now);
        } else if (elapsed >= AMIGA_SYNC_MS) {
            lost = true;
            sync_pulse(now);
        }
        break;

    case IDLE:
        if (overflow && q_count < QUEUE_SIZE) {
            overflow = false;
            push(AMIGA_OVERFLOW);
        }
        sending_prefix = prefix != 0;
        if (sending_prefix) {
            send(prefix, now);
        } else if (have_inflight || q_count) {
            if (!have_inflight) {
                inflight = pop();
                have_inflight = true;
            }
            send(inflight, now);
        }
        break;
    }
}

bool amiga_active(void)
{
    return state != OFF;
}

bool amiga_caps_lock(void)
{
    return caps;
}
