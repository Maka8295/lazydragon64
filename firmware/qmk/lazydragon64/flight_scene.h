// Lazy Dragon 64: the dragon flying over the land, seen from above (the right half's screen).
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>

// Draws one frame onto the 32 x 128 upright canvas (fb[y] bit x = pixel (x, y)).
// t is the time in ms; call it once per frame. wpm makes the dragon fly faster.
void flight_draw(uint32_t fb[128], uint32_t t, uint8_t wpm);
