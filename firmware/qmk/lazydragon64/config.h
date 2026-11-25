// Lazy Dragon 64: settings shared by both halves.
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

/* Split link: full-duplex PIO UART over the D+/D- pair of the USB-C cable (J1).
 * TX is GP3 and RX is GP29 on both halves. The mirrored RP2040-Zero puts MOSI on GP3
 * on the left and on GP29 on the right, so a straight-through cable crosses them. */
#define SERIAL_USART_FULL_DUPLEX
#define SERIAL_USART_TX_PIN GP3
#define SERIAL_USART_RX_PIN GP29
#define SERIAL_USART_SPEED 1000000 // QMK's default is 230400. Lower this if halves drop out.
#define SERIAL_PIO_USE_PIO1        // keep the split link off PIO0, which drives the LEDs

/* If a half ever starts up thinking it is the USB half when it isn't, reboot it. */
#define SPLIT_WATCHDOG_ENABLE

/* Double-tap the RP2040-Zero's RESET button to get the RPI-RP2 drive. */
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET_TIMEOUT 200U

/* OLED: 0.91" 128x32 SSD1306 on J2, driven by dragon_screen.c from its own thread (QMK's
 * OLED feature is off). The module stands lengthwise over the RP2040-Zero. Each half sets
 * LD64_OLED_FLIP in its own config.h (1 turns the picture round 180 degrees).
 * On the first built right half the picture sat too far left, so it is moved one pixel
 * right (2026-11-25). The drawing is a full 32 px wide, so its rightmost column (the edge
 * of the hoard and of the last WPM digit) falls off. Two pixels cut off the dragon's tail. */
#define LD64_OLED_SHIFT 1
#define LD64_OLED_TIMEOUT 60000 // screen off after a minute without a key

/* LEDs: the dungeonOS breath (rgb_matrix_kb.inc) is the default effect. The hue/sat in
 * info.json (dark green) still apply to the other effects, e.g. solid colour. */
#define RGB_MATRIX_DEFAULT_MODE RGB_MATRIX_CUSTOM_DUNGEON_BREATH
