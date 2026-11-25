// Lazy Dragon 64: custom RGB Matrix effects.
// SPDX-License-Identifier: GPL-2.0-or-later
//
// DUNGEON_BREATH (2026-11-25): a slow breath in the dungeonOS colours (~/Dotfiles: moss
// #6E7F5A, brass #A88A5B). At rest the keys glow a dim moss green; each breath swells to
// brass and rolls left to right across both halves, about 4 s a breath at the default
// speed. The palette's colours are greyish, which LEDs show as near-white, so their hues
// are kept (moss 87 deg, brass 37 deg) and the saturation raised.
// The brightness setting (FN + Brght-/+) sets the peak and the speed setting the pace;
// the hue keys don't apply to this effect.
//
// Not built on effect_runner_i: that hands effects an 8-bit time, and slowing it down
// (time / 2) made the breath jump back half a cycle every time it wrapped. This keeps its
// own phase from the 32-bit timer. The colour is blended in RGB between two fixed colours
// rather than through HSV, which wobbles in hue at the low brightness the breath rests at.

RGB_MATRIX_EFFECT(DUNGEON_BREATH)

#ifdef RGB_MATRIX_CUSTOM_EFFECT_IMPLS

// SK6812 green is much brighter than red, so these lean red of the palette's hues: the
// first brass (255, 166, 25) looked almost white at the peak. Amber needs green well under
// half of red; the moss keeps some red so it reads olive rather than pure green.
static const uint8_t db_moss[3]  = {70, 160, 12};
static const uint8_t db_brass[3] = {255, 70, 4};
#    define DB_REST 80 // resting glow, out of 255 of the peak

static bool DUNGEON_BREATH(effect_params_t* params) {
    RGB_MATRIX_USE_LIMITS(led_min, led_max);
    // 256 phase steps a breath; speed 128 (default) gives 512 * 256 / 33 ms, about 4 s
    uint32_t t    = (g_rgb_timer * (uint32_t)qadd8(rgb_matrix_config.speed / 4, 1)) >> 9;
    uint8_t  peak = rgb_matrix_config.hsv.v;
    for (uint8_t i = led_min; i < led_max; i++) {
        RGB_MATRIX_TEST_LED_FLAGS();
        // subtracting x makes each swell travel left to right
        uint8_t w = sin8((uint8_t)(t - g_led_config.point[i].x / 2));
        w         = scale8(w, w); // linger dim, swell briefly
        uint8_t v = scale8(peak, DB_REST + scale8(255 - DB_REST, w));
        uint8_t c[3];
        for (int k = 0; k < 3; k++) c[k] = scale8(lerp8by8(db_moss[k], db_brass[k], w), v);
        rgb_matrix_set_color(i, c[0], c[1], c[2]);
    }
    return rgb_matrix_check_finished_leds(led_max);
}

#endif // RGB_MATRIX_CUSTOM_EFFECT_IMPLS
