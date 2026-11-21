// Lazy Dragon 64: the Lucca-58HE layout.
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Ported from the Lucca-58HE KMK code ("LEFT KB AND CODE/code.py" and
// "RIGHT KB AND CODE/code.py"). Its keymap is listed in multiplexer-channel order, so
// each key's physical spot was traced on the Lucca-58HE PCBs (sensor -> 1.5k -> ADG732
// input). Every letter and number in it lands on its QWERTY spot, which confirms the
// trace.
//
// The Lucca-58HE has 29 keys a side; the Lazy Dragon has 32. Its pinky columns sit much
// lower than the Lazy Dragon's, so they move down a row here: on each half the two outer
// columns' bottom four keys are the Lucca's pinky keys and their top keys are new
// (left: play/pause, next track; right: volume down, volume up). The inner key level with
// the home row is also new and does nothing for now (XXXXXXX); the inner key level with
// the bottom row is the Lucca's inner key (MO(1) / Kana).
//
// Changes from the KMK code:
//   - LCAP (KMK's locking caps lock, which this KMK version no longer defines) is KC_CAPS.
//   - The five RGB keys on the FN layer (left half) are new. They sit on keys that did
//     nothing on that layer; without them there would be no way to adjust the lights.

#include QMK_KEYBOARD_H

enum layers { _BASE, _FN };

// clang-format off
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    /*
     * ,-----------------------------------------.                    ,-----------------------------------------.
     * | Play | Next |   2  |   3  |   4  |   5  |                    |   6  |   7  |   8  |   9  | Vol- | Vol+ |
     * |------+------+------+------+------+------|                    |------+------+------+------+------+------|
     * | Esc  |   1  |   W  |   E  |   R  |   T  |                    |   Y  |   U  |   I  |   O  |   0  | Del  |
     * |------+------+------+------+------+------+------.      ,------+------+------+------+------+------+------|
     * | Tab  |   Q  |   S  |   D  |   F  |   G  |      |      |      |   H  |   J  |   K  |   L  |   P  |   =  |
     * |------+------+------+------+------+------+------|      |------+------+------+------+------+------+------|
     * |RShift|   A  |   X  |   C  |   V  |   B  |  FN  |      | Kana |   N  |   M  |   ,  |   .  |   ;  |   '  |
     * |------+------+------+------+------+------+------'      `------+------+------+------+------+------+------|
     * |LShift|   Z  | Ctrl | Alt  | GUI  | Space  |                | Enter  | Bksp |   [  |   ]  |   /  |   -  |
     * `-----------------------------------------'                `-----------------------------------------'
     */
    [_BASE] = LAYOUT(
        KC_MPLY, KC_MNXT, KC_2,    KC_3,    KC_4,    KC_5,                                KC_6,    KC_7,    KC_8,    KC_9,    KC_VOLD, KC_VOLU,
        KC_ESC,  KC_1,    KC_W,    KC_E,    KC_R,    KC_T,                                KC_Y,    KC_U,    KC_I,    KC_O,    KC_0,    KC_DEL,
        KC_TAB,  KC_Q,    KC_S,    KC_D,    KC_F,    KC_G,    XXXXXXX,          XXXXXXX,  KC_H,    KC_J,    KC_K,    KC_L,    KC_P,    KC_EQL,
        KC_RSFT, KC_A,    KC_X,    KC_C,    KC_V,    KC_B,    MO(_FN),          KC_INT2,  KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SCLN, KC_QUOT,
        KC_LSFT, KC_Z,    KC_LCTL, KC_LALT, KC_LGUI, KC_SPC,                                KC_ENT,  KC_BSPC, KC_LBRC, KC_RBRC, KC_SLSH, KC_MINS
    ),

    /*
     * ,-----------------------------------------.                    ,-----------------------------------------.
     * |      |      |  F2  |  F3  |  F4  |  F5  |                    |  F6  |  F7  |  F8  |  F9  |      |      |
     * |------+------+------+------+------+------|                    |------+------+------+------+------+------|
     * |RGB on|  F1  |Effct-|Effct+|Brght-|Brght+|                    |      |      |  Up  |      | F10  | F11  |
     * |------+------+------+------+------+------+------.      ,------+------+------+------+------+------+------|
     * |      |      |      |      | Vol- | Vol+ |      |      |      |   H  | Left | Down |Right |      | F12  |
     * |------+------+------+------+------+------+------|      |------+------+------+------+------+------+------|
     * |      |      |      |      | Prev | Next |  FN  |      | Play |   ~  |   \  |   |  |      |      |PrtScr|
     * |------+------+------+------+------+------+------'      `------+------+------+------+------+------+------|
     * |      |      |      |      | Mute |  Play  |                |  Caps  | Mute | Prev | Next | Vol- | Vol+ |
     * `-----------------------------------------'                `-----------------------------------------'
     * The new top keys pass through (_______), so play/next and volume still work with FN held.
     */
    [_FN] = LAYOUT(
        _______, _______, KC_F2,   KC_F3,   KC_F4,   KC_F5,                               KC_F6,   KC_F7,   KC_F8,   KC_F9,   _______, _______,
        RM_TOGG, KC_F1,   RM_PREV, RM_NEXT, RM_VALD, RM_VALU,                             XXXXXXX, XXXXXXX, KC_UP,   XXXXXXX, KC_F10,  KC_F11,
        XXXXXXX, XXXXXXX, XXXXXXX, XXXXXXX, KC_VOLD, KC_VOLU, XXXXXXX,          XXXXXXX,  KC_H,    KC_LEFT, KC_DOWN, KC_RGHT, XXXXXXX, KC_F12,
        XXXXXXX, XXXXXXX, XXXXXXX, XXXXXXX, KC_MPRV, KC_MNXT, _______,          KC_MPLY,  KC_TILD, KC_BSLS, KC_PIPE, XXXXXXX, XXXXXXX, KC_PSCR,
        XXXXXXX, XXXXXXX, XXXXXXX, XXXXXXX, KC_MUTE, KC_MPLY,                               KC_CAPS, KC_MUTE, KC_MPRV, KC_MNXT, KC_VOLD, KC_VOLU
    )
};
// clang-format on
