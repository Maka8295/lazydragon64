// Runs flight_scene.c on a PC and writes its frames to a file, for flight_preview.py.
// Build and run:  cc -O2 -I../qmk/lazydragon64 flight_preview.c -o /tmp/flight_preview
//                 /tmp/flight_preview frames.bin [seconds] [wpm]
#include <stdio.h>
#include <stdlib.h>
#include "../qmk/lazydragon64/flight_scene.c"

int main(int argc, char **argv) {
    if (argc < 2) return 1;
    int      seconds = argc > 2 ? atoi(argv[2]) : 30;
    int      wpm     = argc > 3 ? atoi(argv[3]) : 0;
    FILE    *f       = fopen(argv[1], "wb");
    uint32_t fb[128];
    for (uint32_t t = 0; t < (uint32_t)seconds * 1000; t += 33) {
        flight_draw(fb, t, (uint8_t)wpm);
        fwrite(fb, sizeof fb, 1, f);
    }
    fclose(f);
    return 0;
}
