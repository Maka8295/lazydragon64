# The dragon screen talks to the OLED itself, from its own thread (see dragon_screen.c).
I2C_DRIVER_REQUIRED = yes
SRC += dragon_screen.c
