// Lazy Dragon 64: the dragon flying over the land, seen from above (the right half's screen).
// SPDX-License-Identifier: GPL-2.0-or-later
//
// The dragon flies up the screen, so the land scrolls down past it: sea, a coast, fields, a
// village and a castle, a forest with a river, a lake, and round again. Now and then a
// cloud drifts by below it, faster than the land because it is nearer. The dragon flaps
// for a few seconds, then glides with its wings level; its tail never stops swaying. Every
// 5 to 13 seconds it glides, opens its jaws and breathes fire ahead of itself; the flames
// roll forward, slow down and drift back past it as smoke. Typing faster makes it fly
// faster and beat its wings harder.
//
// The art (dragon parts, ground, clouds) is in flight_art.h, made by
// ../../dragon_screen/flight_art.py. This file has no QMK dependencies, so
// ../../dragon_screen/flight_preview.c can run it on a PC to make a preview.

#include "flight_scene.h"
#include <stdbool.h>
#include <string.h>
#include "flight_art.h"

#define DRAGON_Y 72  // canvas row of the snout
#define SPARKS 56

typedef struct {
    int16_t x, y;   // 1/16 px
    int16_t vx, vy; // 1/16 px per frame
    uint8_t age, life; // frames; life 0 = free slot
} spark_t;

static spark_t  sparks[SPARKS];
static uint32_t rng = 0x9E3779B9u;
static bool     started;
static uint32_t last_t, ground_q8, flap_ms;
static uint32_t next_fire, fire_start, fire_end, glide_end, next_glide, next_cloud;
static int8_t   cloud = -1, cloud_x;
static int32_t  cloud_y_q8;

static uint32_t rnd(void) {
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    return rng;
}

static uint32_t rnd_range(uint32_t lo, uint32_t hi) {
    return lo + rnd() % (hi - lo + 1);
}

// t has reached at (works across the millisecond counter wrapping round)
static bool reached(uint32_t t, uint32_t at) {
    return (int32_t)(t - at) >= 0;
}

static uint32_t shift(uint32_t row, int dx) {
    return dx >= 0 ? row << dx : row >> -dx;
}

// bits x0..x1, clipped to the canvas
static uint32_t span(int x0, int x1) {
    if (x0 < 0) x0 = 0;
    if (x1 > 31) x1 = 31;
    if (x0 > x1) return 0;
    uint32_t hi = x1 == 31 ? 0xFFFFFFFFu : (1u << (x1 + 1)) - 1;
    return hi & ~((1u << x0) - 1);
}

/* ------------------------------------------------------------------ fire */

// half-widths of the rows of a round blob of radius 1, 2 and 3
static const int8_t disc_hw[4][7] = {{0}, {0, 1, 0}, {1, 2, 2, 2, 1}, {1, 2, 3, 3, 3, 2, 1}};

static void disc(uint32_t *fb, int cx, int cy, int r, bool on, bool ring) {
    for (int i = 0; i <= 2 * r; i++) {
        int y = cy - r + i;
        if (y < 0 || y > 127) continue;
        int      hw = disc_hw[r][i];
        uint32_t m  = span(cx - hw, cx + hw);
        if (ring && r > 1 && i > 0 && i < 2 * r) m &= ~span(cx - disc_hw[r - 1][i - 1], cx + disc_hw[r - 1][i - 1]);
        fb[y] = on ? fb[y] | m : fb[y] & ~m;
    }
}

static void spark_spawn(int x16, int y16) {
    for (int i = 0; i < SPARKS; i++) {
        spark_t *s = &sparks[i];
        if (s->life) continue;
        s->x  = x16 + (int)(rnd() % 17) - 8;
        s->y  = y16 - (int)(rnd() % 80); // spread over the first 5 px, so the jet has no gaps
        s->vx = (int)(rnd() % 17) - 8;   // up to half a pixel a frame sideways: a cone
        s->vy = -(int16_t)rnd_range(64, 88);
        s->age = 0;
        // most burn out at the end of the jet; one in four lives on as smoke
        s->life = rnd() % 4 ? rnd_range(8, 12) : rnd_range(24, 32);
        return;
    }
}

// drift: how fast the air moves back past the dragon (1/16 px per frame)
static void sparks_step(int drift) {
    for (int i = 0; i < SPARKS; i++) {
        spark_t *s = &sparks[i];
        if (!s->life) continue;
        if (s->age) { // drawn where it was born first
            s->x += s->vx;
            s->y += s->vy;
        }
        if (s->age >= 8) { // past the end of the jet: slow down, then fall behind as smoke
            s->vy += (drift - s->vy) / 5;
            s->vx -= s->vx / 4;
        }
        if (++s->age >= s->life || s->y > 132 * 16) s->life = 0;
    }
}

// the first few pixels of the jet: a narrow flickering cone straight out of the mouth
static void jet_root(uint32_t *fb, int x, int y0) {
    for (int i = 1; i <= 9; i++) {
        int y = y0 - i;
        if (y < 0) break;
        int hw = (i + 1) / 3 + (int)(rnd() % 2);
        fb[y] &= ~span(x - hw - 1, x + hw + 1);
        fb[y] |= span(x - hw + (int)(rnd() % 2), x + hw - (int)(rnd() % 2));
    }
}

// the jet: small hot blobs at the mouth, bigger ones further out, breaking into rings at
// the end; then smoke rings and the odd ember
static void sparks_draw(uint32_t *fb) {
    for (int i = 0; i < SPARKS; i++) { // a dark border round the flame, so it stands out
        spark_t *s = &sparks[i];
        if (s->life && s->age >= 3 && s->age < 8) disc(fb, s->x >> 4, s->y >> 4, 3, false, false);
    }
    for (int i = 0; i < SPARKS; i++) {
        spark_t *s = &sparks[i];
        if (!s->life) continue;
        int x = s->x >> 4, y = s->y >> 4, a = s->age;
        if (a < 2)
            disc(fb, x, y, 1, true, false);
        else if (a < 8) {
            disc(fb, x, y, 2, true, false);
            if ((a + i) & 1) disc(fb, x, y, 0, false, false); // flicker
        } else if (a < 12)
            disc(fb, x, y, 2, true, true);
        else if (a < 22) {
            if ((a + i) % 3 == 0) disc(fb, x, y, a < 17 ? 2 : 3, true, true);
        } else if (rnd() % 3 == 0)
            disc(fb, x, y, 0, true, false);
    }
}

/* ------------------------------------------------------------------ the dragon */

static void part_halo(uint32_t *fb, const uint32_t *halo_rows, int h, int y0, int dx) {
    for (int r = 0; r < h; r++) {
        int y = y0 + r;
        if (y >= 0 && y < 128) fb[y] &= ~shift(halo_rows[r], dx);
    }
}

static void part_draw(uint32_t *fb, const uint32_t *sil, const uint32_t *ink, int h, int y0, int dx) {
    for (int r = 0; r < h; r++) {
        int y = y0 + r;
        if (y >= 0 && y < 128) fb[y] = (fb[y] & ~shift(sil[r], dx)) | shift(ink[r], dx);
    }
}

/* ------------------------------------------------------------------ one frame */

void flight_draw(uint32_t fb[128], uint32_t t, uint8_t wpm) {
    if (!started || t - last_t > 1000) {
        // first frame, or the screen was off: start the timings afresh from now
        started    = true;
        last_t     = t;
        fire_start = fire_end = glide_end = t;
        next_fire  = t + 3000; // the first fire soon, so you see it
        next_glide = t + 2500;
        next_cloud = t + 1500;
    }
    uint32_t dt = t - last_t;
    last_t      = t;

    // speed: land scrolls 23 px/s when idle, up to about 94 px/s typing fast
    uint32_t speed = 6 + wpm / 6; // 1/256 px per ms
    if (speed > 24) speed = 24;
    ground_q8 = (ground_q8 + speed * dt) % ((uint32_t)FL_GROUND_H << 8);
    int drift = (int)(speed * 33 / 16); // the same speed in 1/16 px per 33 ms frame

    // fire: glide, open the jaws, breathe for about a second
    bool firing = reached(t, fire_start) && !reached(t, fire_end);
    if (reached(t, next_fire)) {
        fire_start = t;
        fire_end   = t + rnd_range(900, 1400);
        glide_end  = fire_end + 300;
        next_fire  = fire_end + rnd_range(5000, 13000);
        firing     = true;
    }

    // flapping and gliding
    uint32_t period = wpm > 110 ? 430 : 760 - wpm * 3u; // ms per wingbeat
    bool     gliding = !reached(t, glide_end);
    int      flap    = 0;
    if (gliding) {
        flap_ms = 0;
    } else {
        flap_ms += dt;
        flap = (int)((flap_ms % period) * FL_FLAPS / period);
        // a glide now and then, starting when the wings come level; less often when typing fast
        if (reached(t, next_glide) && flap == 0 && flap_ms > period) {
            glide_end  = t + rnd_range(500, 1400);
            next_glide = glide_end + rnd_range(1800, 4200) + wpm * 30u;
            flap       = 0;
        }
    }

    // the land
    int scroll = (int)(ground_q8 >> 8);
    for (int y = 0; y < 128; y++) {
        int r = (y - scroll) % FL_GROUND_H;
        fb[y] = fl_ground[r < 0 ? r + FL_GROUND_H : r];
    }

    // a cloud, below the dragon, moving twice as fast as the land
    if (cloud < 0 && reached(t, next_cloud)) {
        cloud      = (int8_t)(rnd() % FL_CLOUDS);
        cloud_x    = (int8_t)rnd_range(0, 32 - fl_clouds[cloud].w + 8) - 4;
        cloud_y_q8 = -(int32_t)fl_clouds[cloud].h << 8;
    }
    if (cloud >= 0) {
        cloud_y_q8 += (int32_t)(speed * 2 * dt);
        const fl_cloud_t *c  = &fl_clouds[cloud];
        int               cy = (int)(cloud_y_q8 >> 8);
        if (cy >= 128) {
            cloud      = -1;
            next_cloud = t + rnd_range(2500, 9000);
        } else {
            for (int r = 0; r < c->h; r++) {
                int y = cy + r;
                if (y >= 0 && y < 128) fb[y] = (fb[y] & ~shift(c->sil[r], cloud_x)) | shift(c->ink[r], cloud_x);
            }
        }
    }

    // where the dragon is: a slow side-to-side drift, a surge on the downstroke, and a
    // little recoil while breathing fire
    static const int8_t sway[4] = {0, 1, 0, -1};
    int                 dx      = sway[(t / 1500) % 4];
    int                 y0      = DRAGON_Y + (firing ? 1 : 0) - (!gliding && (flap == 1 || flap == 2) ? 1 : 0);

    // fire, behind the dragon so the smoke passes under it
    if (firing)
        for (int k = 0; k < 4; k++) spark_spawn((16 + dx) * 16 - 8, (y0 - 3) * 16); // ahead of the snout
    sparks_step(drift);
    sparks_draw(fb);
    if (firing) jet_root(fb, 15 + dx + (int)(rnd() % 2), y0);

    const uint32_t(*body)[FL_BODY_H] = fl_body[firing ? 1 : 0];
    const uint32_t(*wing)[FL_WING_H] = fl_wing[gliding ? 0 : flap];
    const uint32_t(*tail)[FL_TAIL_H] = fl_tail[(t / 140) % FL_TAIL_PHASES];
    part_halo(fb, tail[2], FL_TAIL_H, y0 + FL_TAIL_TOP, dx);
    part_halo(fb, wing[2], FL_WING_H, y0 + FL_WING_TOP, dx);
    part_halo(fb, body[2], FL_BODY_H, y0, dx);
    part_draw(fb, tail[0], tail[1], FL_TAIL_H, y0 + FL_TAIL_TOP, dx);
    part_draw(fb, wing[0], wing[1], FL_WING_H, y0 + FL_WING_TOP, dx);
    part_draw(fb, body[0], body[1], FL_BODY_H, y0, dx);
}
