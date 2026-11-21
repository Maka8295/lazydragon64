# Lazy Dragon 64

A 64-key reversible split keyboard: column stagger, hot-swap MX sockets, per-key RGB (SK6812MINI-E),
an RP2040-Zero and a 0.91" OLED on each half, halves linked over USB-C.

* Keyboard Maintainer: [Maka8295](https://github.com/Maka8295)
* Hardware Supported: Lazy Dragon 64 PCB with Waveshare RP2040-Zero
* Hardware Availability: [github.com/Maka8295/lazydragon64](https://github.com/Maka8295/lazydragon64)

Each half has its own build, because the mirrored RP2040-Zero puts the matrix and the OLED's I2C
on different GPIOs on each half:

    qmk compile -kb lazydragon64/left -km default
    qmk compile -kb lazydragon64/right -km default

Flash `lazydragon64_left_default.uf2` to the left half and `lazydragon64_right_default.uf2` to the right.

## Bootloader

Enter the bootloader in 3 ways:

* **Bootmagic reset**: hold the top outer key on that half (top-left on the left, top-right on the right) and plug it in.
* **Physical reset button**: hold BOOT on the RP2040-Zero while plugging in, or double-tap its RESET button.
* There is no bootloader key in the default keymap.
