#!/bin/sh
# Build the Lazy Dragon 64 firmware for both halves.
#
# Needs a QMK checkout and the qmk CLI (https://docs.qmk.fm/newbs_getting_started).
# Set QMK_HOME if the checkout isn't at ~/qmk_firmware. The keyboard source in
# qmk/lazydragon64 is copied into the checkout's keyboards/ folder, then both halves
# are compiled and their .uf2 files copied next to this script.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
QMK_HOME=${QMK_HOME:-$HOME/qmk_firmware}
KEYMAP=${KEYMAP:-default}
export QMK_HOME

rsync -a --delete "$HERE/qmk/lazydragon64/" "$QMK_HOME/keyboards/lazydragon64/"
cd "$QMK_HOME"
for side in left right; do
    qmk compile -kb "lazydragon64/$side" -km "$KEYMAP"
    cp ".build/lazydragon64_${side}_${KEYMAP}.uf2" "$HERE/lazydragon64_${side}.uf2"
done
echo "Built $HERE/lazydragon64_left.uf2 and $HERE/lazydragon64_right.uf2"
