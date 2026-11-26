# Building the Lazy Dragon 64

This guide covers one keyboard: two halves, each built on the same PCB but set up as mirror images. Work on one half at a time, or both side by side.

## What you need

**Parts:**
- **Electronic parts:** see the bill of materials in the [README](README.md#bill-of-materials-one-keyboard). [`lcsc_cart.csv`](lcsc_cart.csv) is an LCSC cart for about three keyboards.
- **Mounting hardware (per keyboard):**
  - 8 × M2 × 8 mm female–female standoffs
  - 16 × M2 × 4 pan-head screws
- **Switches and keycaps:** 64 MX switches; keycaps are 62 × 1U and 2 × 1.5U.
- **Cables:** a USB-C to USB-C cable to join the halves, and a USB-C cable to the computer.

**Fabricated and printed parts:**
- **PCB:** [`production/lazydragon64.zip`](production). 4 layers, 1.6 mm, 1 oz copper on every layer. You need two.
- **Plate:** [`plate/production/Lucca58_Stagger_Plate.zip`](plate/production), or `marikaplate.zip`. 1.6 mm FR4. You need two.
- **Case:** printed. See [Printing the case](#6-printing-the-case).

**Tools:**
- Fine-tip soldering iron, flux, solder wick and tweezers
- A magnifier
- A multimeter with a continuity beeper
- A small Phillips screwdriver

## Which side gets what

The RP2040-Zero (U1), the split-link USB-C (J1) and the OLED socket (J2) go on the **switch face**, the one that faces up. Everything else goes on the **underside**, facing the case floor.

| | Switch face (U1, J1, J2) | Underside (everything else) | Bridge these jumpers (underside) |
|---|---|---|---|
| **Left half** | F (front silkscreen) | B | JP1, JP2, JP8, JP10, JP12, JP14 |
| **Right half** | B (back silkscreen) | F | JP4, JP5, JP7, JP9, JP11, JP13 |

Pick a board for each half and mark it L or R before you start.

## 1. Underside

Use plenty of flux and work from the smallest parts to the biggest.

1. **Jumpers.**
   - Bridge only that half's six jumpers, each with a blob of solder across its two pads.
   - Leave the other six open. The wrong pair puts 5 V on an RP2040 GPIO.
2. **32 diodes (1N4148W, SOD-123).** Each outline is closed at one end like a bracket. The band on the diode goes at that closed end.
3. **32 × 100 nF capacitors**, one beside each LED.
4. **C1 (1 µF).** It has a footprint on both faces; fit it on this face only.
5. **32 LEDs (SK6812MINI-E).**
   - They mount upside down. Drop the body into the hole from this side so the lens points through to the switch face.
   - Each LED has one angled corner on its housing and a notch in the same leg: that's GND, pin 3 in the datasheet. It goes on the pad next to the small filled square on the outline.
   - Keep the iron around 300 °C and touch each pad for no more than about 3 seconds.
   - Solder hides the notch, so check orientation by the housing corner afterwards.
6. **32 hot-swap sockets (CPG151101S11).** Seat each socket flush and solder both pads. The 1.5U thumb key uses the same socket.

## 2. Switch face

1. **J1, the split-link USB-C.** Do it first: it sits under the RP2040-Zero and is the finest-pitch part.
   - Its mouth sits flush with the board edge.
   - Afterwards check under magnification for bridges, and check that VBUS isn't shorted to GND.
2. **Headers on the RP2040-Zero.** Solder the male pins to the Zero with their plastic strip on the Zero's underside, the usual way.
   - On the 4.68 mm machined sockets, that lifts the Zero to about 7.2 mm above the PCB.
   - That height leaves room for both USB-C plugs, the Zero's and J1's, one above the other.
3. **The Zero's sockets.**
   - Cut 9, 9 and 5 positions from the 25-pin socket strips.
   - Plug the Zero into them, set the Zero and sockets onto the board, and solder the sockets from the underside.
   - Using the Zero as a jig keeps the sockets straight.
4. **J2.** Solder the 4-pin socket for the OLED.

## 3. Checks before power

With the RP2040-Zero unplugged, use the multimeter's continuity beeper.

- **Short:** J1's VBUS must not beep to GND.
- **5 V:** look at the two corner holes of the Zero's sockets at the USB end (the board's top edge). The one that beeps to J1's VBUS must be where the Zero's 5V pin goes; check the pinout printed on the Zero. The other corner hole must not beep to VBUS.
- **GND:** the hole for the Zero's GND pin, next to 5V, must beep to J1's GND.

## 4. Firmware and testing

Do this before fitting the OLED, which covers the Zero's BOOT button.

1. Hold BOOT on the RP2040-Zero and plug it straight into the computer. A drive called `RPI-RP2` appears.
2. Copy [`firmware/lazydragon64_left.uf2`](firmware) to the left half's Zero, or `lazydragon64_right.uf2` to the right half's. The Zero restarts by itself.
3. Plug the Zero into its sockets and connect it to the computer.
   - The LEDs should start a slow wave from olive green to amber (the default "Dungeon Breath" effect).
   - If the chain stops partway, the fault is at the first dark LED or the one just before it.
4. Short each socket's two contacts with tweezers. Each key should register; any online key tester will show it.
5. Join the halves with the USB-C cable between their J1 ports, plug the computer into either Zero, and test the other half the same way.

Once the firmware is on, you can get into flashing mode without the BOOT button: hold the top outer key of a half while plugging that half in.

See [`firmware/README.md`](firmware/README.md) for the layout and settings.

## 5. OLED

1. **Check the regulator.** J2 feeds the module 5 V, so it needs its own 3.3 V regulator. Look for a small 3-pin chip marked "662K" on the back of the module. The module's datasheet contradicts itself on this, so don't plug in a module without one.
2. **Check the pin order.** The jumpers make it the same on both halves:
   - GND goes in the J2 hole nearest the half's inner edge (the edge facing the other half), then VCC, SCL and SDA.
   - The module lies lengthwise over the RP2040-Zero, screen up.
3. **Set the height.**
   - Before soldering the module's pins, dry-fit it with a USB cable plugged into the Zero.
   - Set it high enough to clear the Zero's USB-C port and the plug, then solder.
4. **Picture the wrong way up?** The firmware ships set for this mounting. If the picture is upside down, change `LD64_OLED_FLIP` in that half's `firmware/qmk/lazydragon64/left/config.h` or `right/config.h` and rebuild. `LD64_OLED_SHIFT` in `config.h` nudges it sideways.

## 6. Printing the case

Print the halves bottom-down. The finished cases:
- **[`case-final/`](case-final):** the Ivy Curl vine wrap with "Lazy Dragon" on the front wall.
  - `chamfer/`: the same with a 1 mm chamfer on the top outer edge.
  - `chamfer-no-dragon/`: the chamfered halves with a plain underside.
- **[`marika cases/`](marika%20cases):** a moon-phase band, with its own `chamfer/` versions.

There are Bambu Studio projects for an X1C (Textured PEI plate, Overture Matte PLA, solid):
- `chamfer-no-dragon/lazydragon64_no_dragon_X1C_heavy_overture_matte.3mf`, at 0.12 mm layers
- `chamfer/lazydragon64_chamfer_X1C_heavy_overture_matte.3mf`, the dragon version, at 0.16 mm

**Lids:** [`case-final/cover/`](case-final/cover) has a lid for each half. It sits on the case rim and covers the keys, with the dragon engraved on top.
- Print each lid top-down. `cover/lazydragon64_cover_X1C_heavy_overture_matte.3mf` has both, set up that way, with the same settings: about 138 g and 6 h.
- The lid's inside clears XDA keycaps by about 2.7 mm. That figure is estimated, so check it with your caps.

## 7. Assembling the case

Per half: 4 standoffs, 4 floor screws and 4 plate screws.

1. **Standoffs.**
   - Put an M2 × 4 screw up through each of the four holes in the case floor, so its head sits flush in the recess underneath.
   - Screw an M2 × 8 brass standoff onto it so the standoff seats in its pocket.
   - Tighten until snug; brass threads strip easily.
2. **Switches.** Clip the switches into the plate, corners first. Then press the PCB onto their pins, supporting each socket from behind as you press so it isn't pushed off its pads.
3. **Into the case.** Lower the plate, switches and PCB together into the case so the standoffs pass through the Ø5 holes in the PCB.
4. **Plate screws.** Screw the plate to the standoffs with M2 × 4 screws, without washers. The PCB hangs from the switches.
5. **Keycaps.** The two 1.5U caps go on the inner thumb keys.

The hardware is explained in [`case-final/README.md`](case-final/README.md#mounting-hardware-corne-v4-style), including why the standoffs must be 8 mm and the screws no longer than 4 mm.

## Using it

- **Computer cable:** it goes into either RP2040-Zero's own USB-C port, never into J1. J1 only joins the halves.
- **Split cable:** connect or disconnect it only while the keyboard is unplugged from the computer.
- **Power:** all 64 LEDs run from the one USB port. If a laptop port cuts out, turn the brightness down (FN + Brght-).
