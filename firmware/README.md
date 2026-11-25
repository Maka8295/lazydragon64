# Lazy Dragon 64 firmware (QMK)

| File | What it is |
|---|---|
| `lazydragon64_left.uf2` | firmware for the left half |
| `lazydragon64_right.uf2` | firmware for the right half |
| `qmk/lazydragon64/` | the QMK keyboard: shared settings in `info.json` and `config.h`, per-half pins in `left/` and `right/`, keymap in `keymaps/default/keymap.c` |
| `build.sh` | copies `qmk/lazydragon64` into a QMK checkout and builds both halves |
| `gen_layout.py` | rewrites the key layout and the LED map in `info.json` from the KiCad board |
| `dragon_screen/` | the OLED pixel art (`art.py`) and `make_art.py`, which turns it into `qmk/lazydragon64/dragon_art.h` |

Each half needs its own file. The reversible board mirrors the RP2040-Zero, so the matrix and the OLED's I2C sit on different GPIOs on each half. The file also fixes which half is which, so nothing has to be set up after flashing.

## Flashing

1. Hold the RP2040-Zero's BOOT button and plug that half into the computer. It shows up as a drive called `RPI-RP2`.
2. Copy the matching `.uf2` onto the drive. The half restarts by itself.
3. Repeat for the other half. Then connect the halves and plug either one into the computer.

Once QMK is on a half, there are two other ways into the bootloader:
- Hold the top outer key (Play on the left, Vol+ on the right) while plugging that half in. This also resets the saved RGB settings.
- Double-tap the RP2040-Zero's RESET button.

A wrong file on a half does no harm; that half's keys just won't work until it gets the right one.

## Layout

This is the Lucca-58HE layout from its KMK code.

```
BASE
,-----------------------------------------.                    ,-----------------------------------------.
| Play | Next |   2  |   3  |   4  |   5  |                    |   6  |   7  |   8  |   9  | Vol- | Vol+ |
|------+------+------+------+------+------|                    |------+------+------+------+------+------|
| Esc  |   1  |   W  |   E  |   R  |   T  |                    |   Y  |   U  |   I  |   O  |   0  | Del  |
|------+------+------+------+------+------+------.      ,------+------+------+------+------+------+------|
| Tab  |   Q  |   S  |   D  |   F  |   G  |      |      |      |   H  |   J  |   K  |   L  |   P  |   =  |
|------+------+------+------+------+------+------|      |------+------+------+------+------+------+------|
|RShift|   A  |   X  |   C  |   V  |   B  |  FN  |      | Kana |   N  |   M  |   ,  |   .  |   ;  |   '  |
|------+------+------+------+------+------+------'      `------+------+------+------+------+------+------|
|LShift|   Z  | Ctrl | Alt  | GUI  | Space  |                | Enter  | Bksp |   [  |   ]  |   /  |   -  |
`-----------------------------------------'                `-----------------------------------------'

FN (hold FN)
,-----------------------------------------.                    ,-----------------------------------------.
|      |      |  F2  |  F3  |  F4  |  F5  |                    |  F6  |  F7  |  F8  |  F9  |      |      |
|------+------+------+------+------+------|                    |------+------+------+------+------+------|
|RGB on|  F1  |Effct-|Effct+|Brght-|Brght+|                    |      |      |  Up  |      | F10  | F11  |
|------+------+------+------+------+------+------.      ,------+------+------+------+------+------+------|
|      |      |      |      | Vol- | Vol+ |      |      |      |   H  | Left | Down |Right |      | F12  |
|------+------+------+------+------+------+------|      |------+------+------+------+------+------+------|
|      |      |      |      | Prev | Next |  FN  |      | Play |   ~  |   \  |   |  |      |      |PrtScr|
|------+------+------+------+------+------+------'      `------+------+------+------+------+------+------|
|      |      |      |      | Mute |  Play  |                |  Caps  | Mute | Prev | Next | Vol- | Vol+ |
`-----------------------------------------'                `-----------------------------------------'
```

- The KMK keymap is listed in multiplexer-channel order, not key order. Each key's position was traced on the Lucca-58HE PCBs (sensor, then its 1.5k resistor, then the ADG732 input). Every letter and number landed on its QWERTY spot, so the modifier positions it gives can be trusted.
- The Lucca-58HE has 29 keys a side, and this board has 32. The Lucca's pinky columns sit much lower, so they move down a row here. That frees the top key of the two outer columns on each half:
  - left: play/pause and next track
  - right: volume down and volume up
- The inner key beside G / H is also new and does nothing for now. The inner key beside B / N is the Lucca's inner key (FN / Kana).
- Blank keys on FN do nothing, as in the KMK code (it used `XXXXXXX`, not transparent keys).
- Changed from the KMK code:
  - **Caps.** `LCAP` (locking caps lock, no longer defined in that KMK version) is now plain Caps Lock.
  - **RGB keys.** The five RGB keys on FN are new; those keys did nothing on that layer before. "Effect" steps through the lighting effects.
- **Kana** sends the Japanese Katakana/Hiragana key (`KC_INT2`), as KMK's `KANA` did.

## Screen

Each half's OLED shows the Lazy Dragon screen (`qmk/lazydragon64/dragon_screen.c`). From top to bottom:
- **Layer:** an outlined BASE, or a filled FN.
- **Dragon:** the dragon from the case bottom, asleep on its hoard. It wakes, flicks its tail, flaps its wing and breathes fire as you type (details below).
- **Music bars:** eight bars that jump with each key and settle to your typing speed, with falling peak marks.
- **Words per minute.**
- **CAPS:** filled while Caps Lock is on.

The dragon:
- **Asleep:** after 4 s without a key; z's drift up.
- **Typing:** half awake, and it flicks its tail at each key.
- **Above 40 wpm:** eyes open and it flaps its wing.
- **Caps Lock on:** it breathes fire on the hoard.
- **Glints:** now and then something in the hoard glints.

The screen goes off after a minute without a key, and while the computer sleeps.

**Thread.** The screen is drawn and sent from its own thread, not from QMK's main loop:
- In stock QMK, every write to the OLED holds up the key scan until it finishes, about 1 ms at a time.
- The RP2040 sends I2C on interrupts. While a transfer runs, the screen thread sleeps and the key scan carries on.
- Only the rows that changed are sent.

So QMK's own OLED feature is off and `dragon_screen.c` talks to the SSD1306 directly.

**Changing the art.** Edit `dragon_screen/art.py`, run `python3 make_art.py` in that folder, then rebuild. `poses.png` shows every pose so you can check them.

## Latency settings

QMK rather than ZMK, because this is a wired RP2040 board:
- **ZMK** is built for wireless nRF52 boards. Its wired split support is newer, and its RGB support drives the LEDs as one underglow strip, with no per-key effects.
- **QMK** has mature RP2040 support, a full-duplex PIO split link, eager debounce and 1000 Hz polling.

What's set here:

| Setting | Value | Effect |
|---|---|---|
| USB polling | 1 ms (`polling_interval: 1`) | the fastest full-speed USB allows. On average a key waits 0.5 ms for the next poll. |
| Debounce | `sym_eager_pk`, 5 ms | a press or release is sent on the first scan that sees it, then that key ignores changes for 5 ms |
| Matrix scan | wait for rows only after a column with a key down | an idle scan of all 7 columns takes microseconds instead of ~210 µs (`lazydragon64.c`) |
| Split link | full-duplex PIO UART, 1 Mbaud (QMK's default is 230400) | keys on the half that isn't plugged in cross the link in about a quarter of the time |
| OLED | drawn and sent from its own thread | the animation never holds up the key scan |
| NKRO | on | |

Adjust if needed:
- **Doubled letters.** If a key types twice, it is chattering. Change `debounce_type` in `info.json` to `asym_eager_defer_pk`: presses stay instant, releases wait 5 ms.
- **Right half drops out.** If the right half drops out or types the wrong keys, lower `SERIAL_USART_SPEED` in `config.h` (try 460800).

## Check on first power-up

- **OLED orientation.** The picture is drawn upright for a module standing lengthwise over the RP2040-Zero. If it is upside down, flip `LD64_OLED_FLIP` in that half's `left/config.h` or `right/config.h` (both halves ship flipped). `LD64_OLED_SHIFT` in `config.h` moves the picture sideways a pixel at a time.
- **LED current.** All 64 LEDs run from one USB port. The colour and brightness carry over from the Lucca-58HE: hue 0, saturation 100, brightness 100 out of 255, and capped at 100.
  - That colour draws about 0.8 A for the whole keyboard (SK6812MINI-E: 12 mA per colour at full). Full white at the cap draws about 1 A.
  - Most desktop ports supply that, but it is above USB 2.0's 500 mA. If a laptop port cuts out, turn the brightness down (FN + Brght-) or lower `max_brightness` in `info.json`.
  - The LEDs switch off when the computer sleeps.

## Building

```
./build.sh
```

This needs a QMK checkout at `~/qmk_firmware` (or set `QMK_HOME`) and the `qmk` CLI with its ARM toolchain on `PATH`. Built 2026-11-22 against QMK `80973aa0` with QMK's GCC 15.2 toolchain.

If the board's switches or LEDs change, rerun `gen_layout.py` with KiCad's Python before building.
