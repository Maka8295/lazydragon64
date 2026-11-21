// Left half: RP2040-Zero on the key side, so its pins land on the PCB as drawn.
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

/* OLED on I2C0: SDA GP12, SCL GP5 */
#define I2C_DRIVER I2CD0
#define I2C1_SDA_PIN GP12
#define I2C1_SCL_PIN GP5
