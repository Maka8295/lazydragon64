// Runs the left half's screen (dragon_screen.c) on a PC through a scripted demo and writes
// its frames to a file, for flight_preview.py (the same 512-byte frames as flight_preview.c).
// Build and run:  cc -O2 -Ipreview_stubs -I../qmk/lazydragon64 hoard_preview.c -o /tmp/hoard_preview
//                 /tmp/hoard_preview frames.bin
// The demo, 50 ms a frame: asleep (zZ), typing (bars, tail flicks), typing fast (eyes open,
// wing flapping), Caps Lock (fire, CAPS lit), then the FN layer held.
#include <stdio.h>
#include "../qmk/lazydragon64/dragon_screen.c"
// the right half's scene isn't drawn here
void flight_draw(uint32_t fb[128], uint32_t t, uint8_t wpm) { (void)fb; (void)t; (void)wpm; }

int main(int argc, char **argv) {
    if (argc < 2) return 1;
    FILE    *f = fopen(argv[1], "wb");
    uint32_t next_key = 3000;
    pv_last_key = 0;
    for (uint32_t t = 6000; t < 6000 + 17000; t += 50) {
        uint32_t s = t - 6000;           // the clock starts 6 s in, so the dragon is already asleep
        pv_now = t;
        int typing = s >= 3000 && s < 15000;
        uint32_t gap = s < 7000 ? 230 : 120;
        pv_wpm   = s < 3000 ? 0 : s < 7000 ? (uint8_t)((s - 3000) * 34 / 4000) : s < 15000 ? (uint8_t)(MIN(72, 34 + (s - 7000) / 120)) : (uint8_t)MAX(0, 72 - (int)(s - 15000) / 40);
        pv_caps  = s >= 11000 && s < 13500;
        pv_layer = s >= 13500 && s < 15500 ? 1 : 0;
        bool kick = false;
        if (typing && s >= next_key) { kick = true; pv_last_key = t; next_key = s + gap; }
        draw_frame(t, kick);
        fwrite(fb, sizeof fb, 1, f);
    }
    fclose(f);
    return 0;
}
