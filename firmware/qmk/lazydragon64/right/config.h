// Right half: RP2040-Zero mirrored, so U1 pad n is the module's pin 24 - n.
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#define LD64_RIGHT

/* OLED on I2C1: SDA GP10, SCL GP27 */
#define I2C_DRIVER I2CD1
#define I2C1_SDA_PIN GP10
#define I2C1_SCL_PIN GP27

/* OLED orientation: upside down at 0 on the first built right half (2026-11-25). */
#define LD64_OLED_FLIP 1

/* Screen: the dragon flying over the land, seen from above (flight_scene.c). The left
 * half keeps the dragon on its hoard with the layer, WPM and Caps Lock indicators. */
#define LD64_SCREEN_FLIGHT 1
