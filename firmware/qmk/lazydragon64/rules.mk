# The dragon screen talks to the OLED itself, from its own thread (see dragon_screen.c).
I2C_DRIVER_REQUIRED = yes
SRC += dragon_screen.c flight_scene.c # flight_scene.c: the right half's screen

# Dungeon Breath, the default effect (rgb_matrix_kb.inc)
RGB_MATRIX_CUSTOM_KB = yes
