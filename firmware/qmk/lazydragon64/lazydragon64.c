// Lazy Dragon 64
// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"

/* Each half is its own build (left/ and right/), because the mirrored RP2040-Zero
 * puts the matrix and the OLED's I2C on different GPIOs on each half. So the side is
 * fixed at compile time instead of being read from a pin or from EEPROM. */
bool is_keyboard_left_impl(void) {
#ifdef LD64_RIGHT
    return false;
#else
    return true;
#endif
}

/* Matrix scan speed. After a column is released, QMK waits MATRIX_IO_DELAY (30 us) for
 * any row that column pulled low to float back up before reading the next column. A row
 * can only have been pulled low through a pressed key, so when the column just read had
 * no key down there is nothing to wait for. Skipping the wait in that case makes an idle
 * scan of all 7 columns take a few microseconds instead of ~210 us, and the first key
 * press is seen that much sooner. */
void matrix_output_unselect_delay(uint8_t line, bool key_pressed) {
    if (key_pressed) {
        matrix_io_delay();
    }
}
