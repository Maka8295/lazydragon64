#pragma once
#include <stdint.h>
typedef int i2c_status_t;
#define I2C_STATUS_SUCCESS 0
static inline void i2c_init(void) {}
static inline i2c_status_t i2c_transmit(uint8_t a, const uint8_t *d, uint16_t n, uint16_t t) { (void)a; (void)d; (void)n; (void)t; return 0; }
