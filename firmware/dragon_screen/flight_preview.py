#!/usr/bin/env python3
"""Turn the frames from flight_preview.c into an animated GIF and a contact sheet.

  python3 flight_preview.py frames.bin out.gif [sheet.png first last step]
"""
import struct, sys
from PIL import Image

def frames(path):
    data = open(path, "rb").read()
    n = len(data) // 512
    for i in range(n):
        rows = struct.unpack_from("<128I", data, i * 512)
        im = Image.new("L", (32, 128))
        im.putdata([255 if rows[y] >> x & 1 else 0 for y in range(128) for x in range(32)])
        yield im

def oled(im, scale):
    """the panel as it looks: lit pixels pale blue-white on black, in a dark bezel"""
    big = im.resize((32 * scale, 128 * scale), Image.NEAREST).convert("RGB")
    px = big.load()
    for y in range(big.height):
        for x in range(big.width):
            if px[x, y][0]: px[x, y] = (214, 236, 255)
    framed = Image.new("RGB", (big.width + 2 * scale, big.height + 2 * scale), (24, 24, 28))
    framed.paste(big, (scale, scale))
    return framed

if __name__ == "__main__":
    src, gif = sys.argv[1], sys.argv[2]
    fs = list(frames(src))
    imgs = [oled(f, 3) for f in fs]
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=33, loop=0)
    if len(sys.argv) > 3:
        a, b, step = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
        sel = [oled(fs[i], 3) for i in range(a, min(b, len(fs)), step)]
        sheet = Image.new("RGB", (len(sel) * (sel[0].width + 6), sel[0].height), (90, 90, 90))
        for k, im in enumerate(sel):
            sheet.paste(im, (k * (im.width + 6), 0))
        sheet.save(sys.argv[3])
    print(len(fs), "frames")
