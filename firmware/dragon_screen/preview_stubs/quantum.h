// Stand-ins for the QMK and ChibiOS calls dragon_screen.c makes, so hoard_preview.c can run
// its drawing code on a PC. The preview sets the pv_* values to script a demo.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
typedef uint32_t layer_state_t;
static layer_state_t layer_state, default_layer_state;
static uint32_t pv_now, pv_last_key = 0; static uint8_t pv_wpm, pv_layer; static bool pv_caps;
static inline uint8_t get_highest_layer(layer_state_t s) { (void)s; return pv_layer; }
typedef struct { bool caps_lock; } led_t;
static inline led_t host_keyboard_led_state(void) { return (led_t){pv_caps}; }
static inline uint8_t get_current_wpm(void) { return pv_wpm; }
static inline uint32_t last_input_activity_time(void) { return pv_last_key; }
static inline uint32_t last_input_activity_elapsed(void) { return pv_now - pv_last_key; }
static inline uint32_t timer_read32(void) { return pv_now; }
static inline void keyboard_post_init_user(void) {}
static inline void suspend_power_down_user(void) {}
static inline void suspend_wakeup_init_user(void) {}
