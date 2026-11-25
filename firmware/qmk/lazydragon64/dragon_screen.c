// Lazy Dragon 64: the dragon screen on each half's 0.91" OLED.
// SPDX-License-Identifier: GPL-2.0-or-later
//
// The screen stands upright, so everything here is drawn on a 32 x 128 portrait canvas:
//
//   y   0-10   layer, in a pill (filled when you're off the base layer)
//   y  12-47   the dragon asleep on its hoard (art: ../../dragon_screen/art.py)
//   y  53-83   music bars: 8 bars of 10 segments with falling peak marks
//   y  88-111  "WPM" and the typing speed in double-size digits
//   y 117-127  CAPS, in a pill that fills while Caps Lock is on
//
// The dragon sleeps (zZ) after 4 s without a key, lies there half awake while you type,
// opens its eyes and flaps its wing above 40 wpm, and breathes fire while Caps Lock is on.
// Each key kicks the bars and flicks its tail.
//
// Why a thread of its own: QMK's OLED driver sends to the screen from the main loop, and
// every I2C write holds up the key scan until it finishes (about 1 ms per piece of the
// screen at 400 kHz). An animated screen would do that all the time. Here the screen is
// drawn and sent from a separate ChibiOS thread instead. The RP2040's I2C transfers run on
// interrupts, and while one is in progress this thread sleeps and the key scan carries on,
// so the screen never delays a key. QMK's own OLED feature is therefore turned off
// (info.json) and this file talks to the SSD1306 directly. Only this thread uses I2C.

#include "quantum.h"
#include "i2c_master.h"
#include <ch.h>
#include <string.h>
#include "dragon_art.h"

#ifndef LD64_OLED_ADDRESS
#    define LD64_OLED_ADDRESS 0x3C // 7-bit address of the 0.91" SSD1306 modules
#endif
#ifndef LD64_OLED_TIMEOUT
#    define LD64_OLED_TIMEOUT 60000 // screen off after this long without a key (ms)
#endif
#ifndef LD64_OLED_FLIP
#    define LD64_OLED_FLIP 0 // 1 turns the picture round 180 degrees
#endif
#ifndef LD64_OLED_SHIFT
#    define LD64_OLED_SHIFT 0 // moves the picture this many pixels right (negative: left), as seen upright
#endif
#ifndef LD64_OLED_CONTRAST
#    define LD64_OLED_CONTRAST 0xFF
#endif

#define FRAME_MS 50
#define I2C_TIMEOUT_MS 50
#define SCENE_Y 16
#define BARS_BOTTOM 82
#define SLEEP_AFTER_MS 4000
#define FAST_WPM 40

static uint32_t         fb[128];    // fb[y] bit x = pixel (x, y); x 0-31 left to right, y 0-127 top down
static uint32_t         shown[128]; // what the screen holds now
static bool             shown_valid;
static volatile bool    host_suspended;
static uint32_t         rng = 0x2545F491u;

static uint32_t rnd(void) {
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    return rng;
}

/* ------------------------------------------------------------------ drawing */

static void px(int x, int y, bool on) {
    if ((unsigned)x < 32 && (unsigned)y < 128) {
        if (on)
            fb[y] |= 1u << x;
        else
            fb[y] &= ~(1u << x);
    }
}

static const uint8_t *glyph(char c) {
    const char *p = c ? strchr(dragon_font_chars, c) : NULL;
    return dragon_font[p ? p - dragon_font_chars : 0];
}

static void draw_text(const char *s, int x, int y, int scale, int advance, bool ink) {
    for (; *s; s++, x += advance) {
        const uint8_t *g = glyph(*s);
        for (int col = 0; col < 5; col++)
            for (int row = 0; row < 7; row++)
                if ((g[col] >> row) & 1)
                    for (int sx = 0; sx < scale; sx++)
                        for (int sy = 0; sy < scale; sy++) px(x + col * scale + sx, y + row * scale + sy, ink);
    }
}

// a label in an 11 px tall rounded box, centred; filled = light box with dark text
static void draw_pill(const char *label, int y, bool filled) {
    int w = (int)strlen(label) * 6 + 3, x0 = (32 - w) / 2;
    for (int yy = y; yy <= y + 10; yy++)
        for (int x = x0; x < x0 + w; x++) {
            bool side = x == x0 || x == x0 + w - 1, cap = yy == y || yy == y + 10;
            px(x, yy, !(side && cap) && (filled || side || cap));
        }
    draw_text(label, x0 + 2, y + 2, 1, 6, !filled);
}

static void draw_z(int x, int y, bool big) {
    int n = big ? 4 : 3;
    for (int i = 0; i < n; i++) {
        px(x + i, y, true);
        px(x + i, y + n - 1, true);
    }
    for (int i = 1; i < n - 1; i++) px(x + n - 1 - i, y + i, true);
}

// three z's drifting up from the dragon's nose, 2.4 s each, staggered
static void draw_zzz(uint32_t t) {
    for (uint32_t k = 0; k < 3; k++) {
        uint32_t p   = (t + k * 800) % 2400;
        bool     big = p >= 1100;
        int      y   = SCENE_Y + 9 - (int)(p * 13 / 2400);
        draw_z((int)(p * 2 / 2400), y - (big ? 3 : 2), big);
    }
}

// a glint on one piece of the hoard every 1.7 s
static void draw_sparkle(uint32_t t) {
    static const int8_t at[][2] = {{8, 26}, {2, 21}, {18, 20}, {14, 22}, {27, 27}};
    if (t % 1700 >= 340) return;
    const int8_t *s = at[(t / 1700) % 5];
    int x = s[0], y = SCENE_Y + s[1];
    px(x, y, true), px(x - 1, y, true), px(x + 1, y, true), px(x, y - 1, true), px(x, y + 1, true);
    px(x - 1, y - 1, false), px(x + 1, y - 1, false), px(x - 1, y + 1, false), px(x + 1, y + 1, false);
}

/* ------------------------------------------------------------------ music bars */

static uint8_t level[8], peak[8], hold[8], energy;

static void update_bars(bool kick, bool asleep, uint8_t wpm, uint32_t frame) {
    static const uint8_t shape[8] = {170, 230, 255, 215, 190, 210, 175, 140};
    if (kick) energy = energy > 145 ? 255 : energy + 110;
    uint32_t drive = asleep ? 0 : MAX(energy, MIN(255, wpm * 3));
    energy         = energy * 7 / 8;
    for (int i = 0; i < 8; i++) {
        uint32_t target = drive * shape[i] / 255 * (140 + rnd() % 116) / 255; // 0-255
        target          = (target * 10 + 127) / 255;                          // 0-10 segments
        if (target > level[i])
            level[i] = target;
        else if (level[i] > target)
            level[i]--;
        if (level[i] >= peak[i]) {
            peak[i] = level[i];
            hold[i] = 8;
        } else if (hold[i]) {
            hold[i]--;
        } else if (frame & 1) {
            peak[i]--;
        }
    }
}

static void draw_bars(void) {
    for (int i = 0; i < 8; i++) {
        int x0 = i * 4;
        for (int s = 0; s < level[i]; s++)
            for (int x = 0; x < 3; x++) {
                px(x0 + x, BARS_BOTTOM - 3 * s, true);
                px(x0 + x, BARS_BOTTOM - 3 * s - 1, true);
            }
        for (int x = 0; x < 3; x++) px(x0 + x, BARS_BOTTOM - 3 * peak[i] + 1, true);
    }
}

/* ------------------------------------------------------------------ one frame */

static uint32_t kick_at, frames;

static void draw_frame(uint32_t t, bool kick) {
    uint8_t layer  = get_highest_layer(layer_state | default_layer_state);
    bool    caps   = host_keyboard_led_state().caps_lock;
    uint8_t wpm    = get_current_wpm();
    bool    asleep = last_input_activity_elapsed() > SLEEP_AFTER_MS;
    bool    fast   = !asleep && wpm > FAST_WPM;
    if (kick) kick_at = t;
    update_bars(kick, asleep, wpm, frames++);

    memset(fb, 0, sizeof(fb));

    char label[5] = "BASE";
    if (layer == 1)
        strcpy(label, "FN");
    else if (layer > 1)
        label[0] = 'L', label[1] = '0' + layer % 10, label[2] = 0;
    draw_pill(label, 0, layer != 0);

    int eye  = caps ? 2 : asleep ? 0 : fast ? 2 : 1;
    if (!asleep && !caps && t % 3700 < 140) eye = 0; // blink
    int wing = caps || (fast && (t / 180) & 1) ? 1 : 0;
    int tail = !asleep && t - kick_at < 160 ? 1 : 0;
    int fire = caps ? 1 + ((t / 110) & 1) : 0;
    const uint32_t *pose = dragon_poses[DRAGON_POSE(eye, wing, tail, fire)];
    for (int y = 0; y < 32; y++) fb[SCENE_Y + y] |= pose[y];
    if (asleep && !caps) draw_zzz(t);
    draw_sparkle(t);

    draw_bars();

    char digits[4] = {'0' + wpm / 100 % 10, '0' + wpm / 10 % 10, '0' + wpm % 10, 0};
    draw_text("WPM", 7, 88, 1, 6, true);
    draw_text(digits, 0, 98, 2, 11, true);
    draw_pill("CAPS", 117, caps);
}

/* ------------------------------------------------------------------ SSD1306 */

static bool oled_cmd(const uint8_t *cmds, uint8_t n) {
    uint8_t buf[32];
    buf[0] = 0x00; // control byte: commands follow
    memcpy(buf + 1, cmds, n);
    return i2c_transmit(LD64_OLED_ADDRESS << 1, buf, n + 1, I2C_TIMEOUT_MS) == I2C_STATUS_SUCCESS;
}

// QMK's own SSD1306 128 x 32 set-up, left with the display off
static bool oled_hw_init(void) {
    static const uint8_t seq[] = {
        0xAE,       0xD5, 0x80, 0xA8, 0x1F, 0x40, 0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xD3, 0x00,
        0xDA, 0x02, 0x81, LD64_OLED_CONTRAST, 0xD9, 0xF1, 0xDB, 0x20, 0xA4, 0xA6, 0x2E,
    };
    return oled_cmd(seq, sizeof(seq));
}

// The panel is 128 columns of four 8-pixel pages. Each canvas row y becomes one column.
// LD64_OLED_SHIFT moves canvas column x to x + shift; columns pushed past an edge are lost.
static uint32_t shifted(uint32_t row) {
#if LD64_OLED_SHIFT >= 0
    return row << LD64_OLED_SHIFT;
#else
    return row >> -(LD64_OLED_SHIFT);
#endif
}

static uint8_t page_byte(int col, int page) {
#if LD64_OLED_FLIP
    return (shifted(fb[127 - col]) >> (8 * page)) & 0xFF;
#else
    uint8_t v = (shifted(fb[col]) >> (24 - 8 * page)) & 0xFF, r = 0;
    for (int b = 0; b < 8; b++) r |= ((v >> b) & 1) << (7 - b);
    return r;
#endif
}

// send only the band of rows that changed
static bool oled_push(void) {
    int lo = -1, hi = -1;
    for (int y = 0; y < 128; y++)
        if (!shown_valid || fb[y] != shown[y]) {
            if (lo < 0) lo = y;
            hi = y;
        }
    if (lo < 0) return true;
#if LD64_OLED_FLIP
    uint8_t c0 = 127 - hi, c1 = 127 - lo;
#else
    uint8_t c0 = lo, c1 = hi;
#endif
    const uint8_t window[] = {0x21, c0, c1, 0x22, 0, 3};
    if (!oled_cmd(window, sizeof(window))) return false;
    static uint8_t buf[1 + 4 * 128];
    uint16_t       n = 0;
    buf[n++]         = 0x40; // control byte: display data follows
    for (int page = 0; page < 4; page++)
        for (int c = c0; c <= c1; c++) buf[n++] = page_byte(c, page);
    if (i2c_transmit(LD64_OLED_ADDRESS << 1, buf, n, I2C_TIMEOUT_MS) != I2C_STATUS_SUCCESS) return false;
    memcpy(shown, fb, sizeof(fb));
    shown_valid = true;
    return true;
}

/* ------------------------------------------------------------------ the thread */

static THD_WORKING_AREA(dragon_wa, 2048);

static THD_FUNCTION(dragon_thread, arg) {
    (void)arg;
    chRegSetThreadName("dragon_screen");
    i2c_init();
    bool     ready = false, on = false;
    uint32_t last_act = last_input_activity_time();
    for (;;) {
        systime_t start = chVTGetSystemTimeX();
        if (!ready) {
            // no answer (no screen fitted, or it glitched): try again in a second
            ready       = oled_hw_init();
            on          = false;
            shown_valid = false;
            if (!ready) {
                chThdSleepMilliseconds(1000);
                continue;
            }
        }
        uint32_t act  = last_input_activity_time();
        bool     kick = act != last_act;
        last_act      = act;
        if (!host_suspended && last_input_activity_elapsed() < LD64_OLED_TIMEOUT) {
            draw_frame(timer_read32(), kick);
            ready = oled_push();
            if (ready && !on) {
                static const uint8_t display_on[] = {0xAF};
                ready = on = oled_cmd(display_on, 1);
            }
        } else if (on) {
            static const uint8_t display_off[] = {0xAE};
            ready = oled_cmd(display_off, 1);
            on    = false;
        }
        chThdSleepUntilWindowed(start, chTimeAddX(start, TIME_MS2I(FRAME_MS)));
    }
}

// Above the main loop's priority so a finished transfer is followed up at once. It spends
// almost all its time asleep, so the main loop gets the processor back immediately.
void keyboard_post_init_kb(void) {
    chThdCreateStatic(dragon_wa, sizeof(dragon_wa), NORMALPRIO + 1, dragon_thread, NULL);
    keyboard_post_init_user();
}

void suspend_power_down_kb(void) {
    host_suspended = true;
    suspend_power_down_user();
}

void suspend_wakeup_init_kb(void) {
    host_suspended = false;
    suspend_wakeup_init_user();
}
