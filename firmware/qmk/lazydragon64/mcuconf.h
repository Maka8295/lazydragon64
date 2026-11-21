// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include_next <mcuconf.h>

/* The OLED is on I2C0 on the left half and I2C1 on the right (see left/ and right/config.h). */
#undef RP_I2C_USE_I2C0
#define RP_I2C_USE_I2C0 TRUE
#undef RP_I2C_USE_I2C1
#define RP_I2C_USE_I2C1 TRUE
