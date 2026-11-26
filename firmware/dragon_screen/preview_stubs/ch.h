#pragma once
#include <stdint.h>
typedef uint32_t systime_t;
#define THD_WORKING_AREA(n, s) char n[s]
#define THD_FUNCTION(n, a) void n(void *a)
#define NORMALPRIO 128
#define TIME_MS2I(x) (x)
static inline systime_t chVTGetSystemTimeX(void) { return 0; }
static inline systime_t chTimeAddX(systime_t a, systime_t b) { return a + b; }
static inline void chThdSleepMilliseconds(uint32_t m) { (void)m; }
static inline void chThdSleepUntilWindowed(systime_t a, systime_t b) { (void)a; (void)b; }
static inline void chRegSetThreadName(const char *n) { (void)n; }
static inline void *chThdCreateStatic(void *w, unsigned s, int p, void (*f)(void *), void *a) { (void)w; (void)s; (void)p; (void)f; (void)a; return 0; }
