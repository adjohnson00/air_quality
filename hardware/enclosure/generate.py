#!/usr/bin/env python3
"""Generate a two-piece FDM enclosure for the air-quality stack.

Parts (mm, from Adafruit / UM / Plantower datasheets):
  2.9\" eInk FeatherWing #4777  79.5 x 47.0 (ears), holes 74.3 x 42.0, M2.5
  FeatherS3[D] #6399           52.3 x 22.9, USB-C on the short end
  PMSA003I #4632               PCB 51.0 x 35.5, can 38 x 35 x 12
  LiPo #3898                   36 x 17 x 7.8

Layout (display facing +Z, USB at -X, sensor at +X):
  [USB]  [Feather + wing + battery sandwich]  [sensor bay + vents]

Run:  .venv/bin/python hardware/enclosure/generate.py
"""

from pathlib import Path

import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent

# --- parameters (mm) --------------------------------------------------------
WALL = 2.2
FIT = 0.35
LIP_H = 4.0
LIP_T = 1.3

WING_L = 79.5
WING_W = 47.0
WING_HOLE_DX = 74.3
WING_HOLE_DY = 42.0
PIN_R = 1.05

DISP_L = 67.2
DISP_W = 29.4
WINDOW_LIP = 1.4

STACK_H = 16.5
POCKET = 0.8

BAT_L = 38.0
BAT_W = 18.5
BAT_H = 8.2
BAT_LIP = 1.0

SENS_L = 51.0
SENS_W = 35.5
SENS_H = 14.5
SENS_HOLE_DX = 45.7
SENS_HOLE_DY = 30.5
GAP = 5.0

USB_W = 12.0
USB_H = 6.5
USB_Z = 5.0

SLOT_L = 16.0
SLOT_H = 2.4
SLOT_N = 4
SLOT_PITCH = 5.5

BTN_Y = WING_W / 2 + 0.5
BTN_XS = (-18.0, -3.0, 12.0)
BTN_R = 3.2

FEET = 2.0
POST_H = 4.5

INNER_X = WING_L + GAP + SENS_L + 3.0
INNER_Y = max(WING_W, SENS_W) + 3.0
INNER_Z = STACK_H + 2.0

OUTER_X = INNER_X + 2 * WALL
OUTER_Y = INNER_Y + 2 * WALL
OUTER_Z = INNER_Z + WALL + WALL + LIP_H * 0.15


def _box(sx, sy, sz, cx, cy, cz):
    m = trimesh.creation.box(extents=(sx, sy, sz))
    m.apply_translation((cx, cy, cz))
    return m


def _cyl(r, h, cx, cy, cz, axis="z"):
    m = trimesh.creation.cylinder(radius=r, height=h)
    if axis == "x":
        m.apply_transform(
            trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        )
    elif axis == "y":
        m.apply_transform(
            trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        )
    m.apply_translation((cx, cy, cz))
    return m


def _union(parts):
    acc = parts[0]
    for p in parts[1:]:
        acc = acc.union(p, engine="manifold")
    return acc


def _diff(a, b):
    return a.difference(b, engine="manifold")


def _origin():
    """Enclosure centered on origin; floor at z=0."""
    return 0.0, 0.0, 0.0


def _bays():
    """Centers of the display bay and sensor bay in XY."""
    wing_cx = -INNER_X / 2 + WING_L / 2 + 1.0
    sens_cx = INNER_X / 2 - SENS_L / 2 - 0.5
    return wing_cx, 0.0, sens_cx, 0.0


def make_base():
    ox, oy, _ = OUTER_X, OUTER_Y, OUTER_Z
    wing_cx, wing_cy, sens_cx, sens_cy = _bays()

    body = _box(ox, oy, WALL + INNER_Z, 0, 0, (WALL + INNER_Z) / 2)
    cavity = _box(INNER_X, INNER_Y, INNER_Z + 1, 0, 0, WALL + INNER_Z / 2 + 0.5)
    base = _diff(body, cavity)

    # Lip recess so the lid drops on
    lip_cut = _box(
        INNER_X + 2 * LIP_T + FIT,
        INNER_Y + 2 * LIP_T + FIT,
        LIP_H + 0.4,
        0,
        0,
        WALL + INNER_Z - LIP_H / 2 + 0.2,
    )
    base = _diff(base, lip_cut)

    # Wing pocket
    pocket = _box(
        WING_L + 1.2,
        WING_W + 1.2,
        POCKET + 0.4,
        wing_cx,
        wing_cy,
        WALL + POST_H + POCKET / 2,
    )
    base = _diff(base, pocket)

    # Battery corral — walls on the floor under the Feather (left half of wing)
    bx = wing_cx - WING_L / 2 + 8 + BAT_L / 2
    by = wing_cy
    bt = 1.6
    bh = 7.0
    corral = [
        _box(BAT_L + 2 * bt, bt, bh, bx, by + (BAT_W / 2 + bt / 2), WALL + bh / 2),
        _box(BAT_L + 2 * bt, bt, bh, bx, by - (BAT_W / 2 + bt / 2), WALL + bh / 2),
        _box(bt, BAT_W, bh, bx + (BAT_L / 2 + bt / 2), by, WALL + bh / 2),
        _box(bt, BAT_W, bh, bx - (BAT_L / 2 + bt / 2), by, WALL + bh / 2),
    ]
    for sign in (-1, 1):
        corral.append(
            _box(
                BAT_L - 6,
                BAT_LIP,
                1.1,
                bx,
                by + sign * (BAT_W / 2 + bt - 0.2),
                WALL + bh + 0.4,
            )
        )
    base = _union([base] + corral)

    # Partition between display bay and sensor, with a STEMMA cable notch
    px = (wing_cx + WING_L / 2 + sens_cx - SENS_L / 2) / 2
    partition = _box(WALL, INNER_Y - 0.8, INNER_Z - LIP_H - 1, px, 0, WALL + (INNER_Z - LIP_H - 1) / 2)
    notch = _box(WALL + 2, 7.0, 7.0, px, 0, WALL + 5.0)
    partition = _diff(partition, notch)
    base = _union([base, partition])

    # Locating pins for the wing (press into 2.5 mm holes)
    pins = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            pins.append(
                _cyl(
                    PIN_R,
                    POST_H + 2.0,
                    wing_cx + sx * WING_HOLE_DX / 2,
                    wing_cy + sy * WING_HOLE_DY / 2,
                    WALL + (POST_H + 2.0) / 2,
                )
            )
            shoulder = _cyl(
                2.2,
                POST_H,
                wing_cx + sx * WING_HOLE_DX / 2,
                wing_cy + sy * WING_HOLE_DY / 2,
                WALL + POST_H / 2,
            )
            pins.append(shoulder)
    base = _union([base] + pins)

    # Sensor posts
    sp = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            sp.append(
                _cyl(
                    PIN_R,
                    3.2,
                    sens_cx + sx * SENS_HOLE_DX / 2,
                    sens_cy + sy * SENS_HOLE_DY / 2,
                    WALL + 1.6,
                )
            )
            sp.append(
                _cyl(
                    2.2,
                    2.0,
                    sens_cx + sx * SENS_HOLE_DX / 2,
                    sens_cy + sy * SENS_HOLE_DY / 2,
                    WALL + 1.0,
                )
            )
    base = _union([base] + sp)

    # USB-C on the -X wall, aligned to the Feather USB end
    usb_x = -ox / 2
    usb = _box(
        WALL + 4,
        USB_W,
        USB_H,
        usb_x,
        wing_cy,
        WALL + USB_Z,
    )
    base = _diff(base, usb)

    # Air slots: +X wall (sensor exhaust) and +Y wall (intake)
    cuts = []
    slot_z0 = WALL + 5.0
    for i in range(SLOT_N):
        z = slot_z0 + i * SLOT_PITCH
        cuts.append(_box(WALL + 4, SLOT_L, SLOT_H, ox / 2, sens_cy, z))
        cuts.append(
            _box(SLOT_L, WALL + 4, SLOT_H, sens_cx, oy / 2, z)
        )
    for c in cuts:
        base = _diff(base, c)

    # Button holes through +Y wall (A/B/C on the wing's back edge)
    for dx in BTN_XS:
        hole = _cyl(
            BTN_R,
            WALL + 4,
            wing_cx + dx,
            oy / 2,
            WALL + INNER_Z - 6.0,
            axis="y",
        )
        base = _diff(base, hole)

    # Corner feet
    feet = []
    inset = 6.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            feet.append(
                _cyl(
                    4.0,
                    FEET,
                    sx * (ox / 2 - inset),
                    sy * (oy / 2 - inset),
                    -FEET / 2 + 0.05,
                )
            )
    base = _union([base] + feet)

    return base


def make_lid():
    ox, oy = OUTER_X, OUTER_Y
    wing_cx, wing_cy, sens_cx, sens_cy = _bays()
    lid_t = WALL + 0.4

    plate = _box(ox, oy, lid_t, 0, 0, lid_t / 2)

    # Display window
    window = _box(
        DISP_L,
        DISP_W,
        lid_t + 2,
        wing_cx,
        wing_cy,
        lid_t / 2,
    )
    lid = _diff(plate, window)

    # Bezel that rests on the panel
    bezel = _box(
        DISP_L + 2 * WINDOW_LIP,
        DISP_W + 2 * WINDOW_LIP,
        1.0,
        wing_cx,
        wing_cy,
        -0.3,
    )
    bezel_hole = _box(DISP_L, DISP_W, 2.0, wing_cx, wing_cy, -0.3)
    bezel = _diff(bezel, bezel_hole)
    lid = _union([lid, bezel])

    # Inner lip that seats in the base
    lip = _box(
        INNER_X + 2 * LIP_T,
        INNER_Y + 2 * LIP_T,
        LIP_H,
        0,
        0,
        -LIP_H / 2 + 0.2,
    )
    lip_in = _box(
        INNER_X - FIT,
        INNER_Y - FIT,
        LIP_H + 1,
        0,
        0,
        -LIP_H / 2 + 0.2,
    )
    lip = _diff(lip, lip_in)
    lid = _union([lid, lip])

    # Sensor vents in the lid
    for i in range(3):
        y = sens_cy + (i - 1) * 6.0
        slot = _box(22.0, 2.2, lid_t + 3, sens_cx, y, lid_t / 2)
        lid = _diff(lid, slot)

    return lid


def main():
    print(f"outer {OUTER_X:.1f} x {OUTER_Y:.1f} x {OUTER_Z + FEET:.1f} mm")
    print("building base...")
    base = make_base()
    print("building lid...")
    lid = make_lid()
    base_path = OUT / "aq_enclosure_base.stl"
    lid_path = OUT / "aq_enclosure_lid.stl"
    base.export(base_path)
    lid.export(lid_path)
    print("wrote", base_path.name, f"{base_path.stat().st_size / 1024:.0f} KB")
    print("wrote", lid_path.name, f"{lid_path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
