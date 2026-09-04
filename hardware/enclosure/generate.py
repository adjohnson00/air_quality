#!/usr/bin/env python3
"""Two-piece FDM enclosure for the air-quality stack (rev 2).

Layout (display facing +Z):
  LEFT (-X)   antenna RP-SMA bulkhead (filled, drill later)
  BOTTOM (-Y) USB-C opening (stack connector comes out the bottom)
  CENTER      1\" Feather + eInk stack over a 1/2\" battery cage
  RIGHT (+X)  PMSA003I inline; I/O at the TOP (+Y)
              black fan = exhaust, blue-aluminum hole = intake
              divider keeps those two paths apart

Mounting holes and air ports print SOLID at wall thickness with a raised
ring as a drill guide. USB-C is a real opening.

Lid: display can bolt on the inside (buttons hidden) or the outside
(buttons accessible). Same four filled bosses.

Run:  .venv/bin/python hardware/enclosure/generate.py
"""

from pathlib import Path

import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent

# --- mm -----------------------------------------------------------------
WALL = 2.2
FIT = 0.35
LIP_H = 4.5
LIP_T = 1.3

IN = 25.4
STACK_H = 1.00 * IN          # screen + Feather + USB out the bottom
BAT_CAGE_H = 0.50 * IN       # 3/8\" cell, 1/2\" cage
RIDGE_H = 0.5625 * IN        # 9/16\" snug over the PMSA003I can

WING_L = 79.5
WING_W = 47.0
WING_HOLE_DX = 74.3
WING_HOLE_DY = 42.0

DISP_L = 67.2
DISP_W = 29.4

# Pack: 2.00\" x 1-5/16\" x 3/8\". Cage interior adds ~2 mm clearance.
BAT_L = 52.8
BAT_W = 35.3
BAT_LIP = 1.2
BAT_WALL = 1.6

SENS_L = 51.0
SENS_W = 35.5
SENS_HOLE_DX = 45.7
SENS_HOLE_DY = 30.5
GAP = 6.0
PLENUM = 9.0                 # intake/exhaust channels at +Y of the sensor

# RP-SMA bulkhead: ~6.5 mm drill, 1/4-36 thread. Print filled.
SMA_DRILL = 6.5
SMA_PAD = 8.0
SMA_RING = 10.5
SMA_Z = BAT_CAGE_H + 10.0    # mid-stack on the left wall

USB_W = 13.0
USB_H = 8.0

LID_T = 3.2
POCKET = 1.2                 # inner/outer wing pockets on the lid
BOSS_R = 2.8                 # filled 5.6 mm pad (drill 2.5 later)
RING_R = 3.6
RING_H = 0.7
AIR_PAD = 5.0                # filled air-port pads (drill later)
AIR_RING = 6.5

FEET = 2.0

INNER_X = WING_L + GAP + SENS_L + 4.0
INNER_Y = max(WING_W, SENS_W + PLENUM) + 4.0
INNER_Z = BAT_CAGE_H + STACK_H + 3.0

OUTER_X = INNER_X + 2 * WALL
OUTER_Y = INNER_Y + 2 * WALL
OUTER_Z = INNER_Z + WALL


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


def _filled_pad(cx, cy, cz, axis="z", pad=BOSS_R, ring=RING_R, h=WALL, rh=RING_H):
    """Solid pad + raised ring. Drill the pad later."""
    body = _cyl(pad, h, cx, cy, cz, axis=axis)
    # ring sits on the +axis face
    if axis == "z":
        r = _cyl(ring, rh, cx, cy, cz + h / 2 + rh / 2 - 0.05, axis=axis)
        hole = _cyl(pad + 0.15, rh + 0.2, cx, cy, cz + h / 2 + rh / 2 - 0.05, axis=axis)
    elif axis == "x":
        r = _cyl(ring, rh, cx + h / 2 + rh / 2 - 0.05, cy, cz, axis=axis)
        hole = _cyl(pad + 0.15, rh + 0.2, cx + h / 2 + rh / 2 - 0.05, cy, cz, axis=axis)
    else:
        r = _cyl(ring, rh, cx, cy + h / 2 + rh / 2 - 0.05, cz, axis=axis)
        hole = _cyl(pad + 0.15, rh + 0.2, cx, cy + h / 2 + rh / 2 - 0.05, cz, axis=axis)
    r = _diff(r, hole)
    return _union([body, r])


def _bays():
    """Display bay center and sensor bay center."""
    wing_cx = -INNER_X / 2 + WING_L / 2 + 1.5
    wing_cy = -2.0
    # Sensor inline to the right; shifted -Y so plenums sit at +Y (top)
    sens_cx = INNER_X / 2 - SENS_L / 2 - 1.0
    sens_cy = -INNER_Y / 2 + SENS_W / 2 + 2.0
    return wing_cx, wing_cy, sens_cx, sens_cy


def make_base():
    ox, oy = OUTER_X, OUTER_Y
    wing_cx, wing_cy, sens_cx, sens_cy = _bays()
    floor_z = WALL
    shelf_z = WALL + BAT_CAGE_H  # top of battery cage / sensor shelf

    body = _box(ox, oy, WALL + INNER_Z, 0, 0, (WALL + INNER_Z) / 2)
    cavity = _box(INNER_X, INNER_Y, INNER_Z + 2, 0, 0, WALL + INNER_Z / 2 + 1)
    base = _diff(body, cavity)

    lip_cut = _box(
        INNER_X + 2 * LIP_T + FIT,
        INNER_Y + 2 * LIP_T + FIT,
        LIP_H + 0.5,
        0,
        0,
        WALL + INNER_Z - LIP_H / 2 + 0.25,
    )
    base = _diff(base, lip_cut)

    # --- battery cage (low lip, under the display stack) ---
    bx, by = wing_cx, wing_cy
    bh = BAT_CAGE_H
    bt = BAT_WALL
    cage = [
        _box(BAT_L + 2 * bt, bt, bh, bx, by + (BAT_W / 2 + bt / 2), floor_z + bh / 2),
        _box(BAT_L + 2 * bt, bt, bh, bx, by - (BAT_W / 2 + bt / 2), floor_z + bh / 2),
        _box(bt, BAT_W, bh, bx + (BAT_L / 2 + bt / 2), by, floor_z + bh / 2),
        _box(bt, BAT_W, bh, bx - (BAT_L / 2 + bt / 2), by, floor_z + bh / 2),
    ]
    for sign in (-1, 1):
        cage.append(
            _box(
                BAT_L - 8,
                BAT_LIP,
                1.2,
                bx,
                by + sign * (BAT_W / 2 + bt - 0.15),
                floor_z + bh + 0.4,
            )
        )
    base = _union([base] + cage)

    # --- partition display | sensor, STEMMA notch at the back (+Y) ---
    px = (wing_cx + WING_L / 2 + sens_cx - SENS_L / 2) / 2
    part_h = INNER_Z - LIP_H - 1
    partition = _box(WALL, INNER_Y - 0.6, part_h, px, 0, floor_z + part_h / 2)
    notch = _box(WALL + 3, 8.0, 8.0, px, INNER_Y / 2 - 10, shelf_z + 4)
    partition = _diff(partition, notch)
    base = _union([base, partition])

    # --- sensor shelf at battery-cage height ---
    shelf = _box(SENS_L + 3, SENS_W + 3, 1.6, sens_cx, sens_cy, shelf_z - 0.8)
    base = _union([base, shelf])

    # Filled sensor mounting pads (drill later) on the shelf
    pads = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            pads.append(
                _filled_pad(
                    sens_cx + sx * SENS_HOLE_DX / 2,
                    sens_cy + sy * SENS_HOLE_DY / 2,
                    shelf_z + WALL / 2,
                    h=WALL,
                )
            )
    base = _union([base] + pads)

    # Ridge ~9/16\" above the mounting-hole plane, snug on the can
    # Three walls + a top bar over the can (open toward +Y plenums)
    rh = RIDGE_H
    rz = shelf_z + rh / 2
    ridge = [
        _box(SENS_L + 2, 1.8, rh, sens_cx, sens_cy - SENS_W / 2 - 0.7, rz),
        _box(1.8, SENS_W + 2, rh, sens_cx - SENS_L / 2 - 0.7, sens_cy, rz),
        _box(1.8, SENS_W + 2, rh, sens_cx + SENS_L / 2 + 0.7, sens_cy, rz),
        # top bar (ceiling) over the module, 1.6 mm thick
        _box(SENS_L + 2, SENS_W + 1, 1.6, sens_cx, sens_cy, shelf_z + rh + 0.8),
    ]
    base = _union([base] + ridge)

    # Divider: splits intake (blue hole, -X half of sensor) from
    # exhaust (black fan, +X half). Both plenums open to +Y.
    div_y = (sens_cy + SENS_W / 2 + (INNER_Y / 2)) / 2
    divider = _box(
        1.8,
        INNER_Y / 2 - (sens_cy + SENS_W / 2) + 4,
        rh + 2,
        sens_cx,
        div_y,
        shelf_z + (rh + 2) / 2,
    )
    base = _union([base, divider])

    # Plenum walls at +Y so each path only exits through its drill pad
    # (the outer +Y wall of the enclosure is the exit; pads mark drill spots)

    # USB-C — real opening, bottom wall, under the 1\" stack
    usb = _box(
        USB_W,
        WALL + 5,
        USB_H,
        wing_cx,
        -oy / 2,
        shelf_z + USB_H / 2 + 2.0,
    )
    base = _diff(base, usb)

    # RP-SMA bulkhead on the LEFT end — filled pad + ring, drill later
    sma = _filled_pad(
        -ox / 2 + WALL / 2,
        wing_cy,
        floor_z + SMA_Z,
        axis="x",
        pad=SMA_PAD / 2,
        ring=SMA_RING / 2,
        h=WALL,
        rh=0.9,
    )
    base = _union([base, sma])

    # Air ports on the TOP (+Y) wall: intake (left of divider) and exhaust (right)
    air_z = shelf_z + RIDGE_H * 0.45
    intake_x = sens_cx - SENS_L / 4
    exhaust_x = sens_cx + SENS_L / 4
    for ax in (intake_x, exhaust_x):
        pad = _filled_pad(
            ax,
            oy / 2 - WALL / 2,
            air_z,
            axis="y",
            pad=AIR_PAD,
            ring=AIR_RING,
            h=WALL,
            rh=0.9,
        )
        base = _union([base, pad])

    # Corner feet
    feet = []
    inset = 7.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            feet.append(
                _cyl(
                    4.2,
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

    plate = _box(ox, oy, LID_T, 0, 0, LID_T / 2)

    # Through-window for the active area (works for inside or outside mount)
    window = _box(DISP_L, DISP_W, LID_T + 4, wing_cx, wing_cy, LID_T / 2)
    lid = _diff(plate, window)

    # Outer pocket — wing sits here when mounted OUTSIDE (buttons accessible)
    outer_pocket = _box(
        WING_L + 1.4,
        WING_W + 1.4,
        POCKET + 0.4,
        wing_cx,
        wing_cy,
        LID_T + POCKET / 2 - 0.15,
    )
    lid = _diff(lid, outer_pocket)

    # Inner pocket — wing sits here when mounted INSIDE (buttons hidden)
    inner_pocket = _box(
        WING_L + 1.4,
        WING_W + 1.4,
        POCKET + 0.4,
        wing_cx,
        wing_cy,
        -POCKET / 2 + 0.15,
    )
    lid = _diff(lid, inner_pocket)

    # Filled mounting bosses at the wing hole pattern, both faces get a ring
    bosses = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = wing_cx + sx * WING_HOLE_DX / 2
            cy = wing_cy + sy * WING_HOLE_DY / 2
            pad = _cyl(BOSS_R, LID_T, cx, cy, LID_T / 2)
            bosses.append(pad)
            # outer ring
            o = _cyl(RING_R, RING_H, cx, cy, LID_T + RING_H / 2 - 0.05)
            o = _diff(o, _cyl(BOSS_R + 0.15, RING_H + 0.3, cx, cy, LID_T + RING_H / 2 - 0.05))
            bosses.append(o)
            # inner ring
            i = _cyl(RING_R, RING_H, cx, cy, -RING_H / 2 + 0.05)
            i = _diff(i, _cyl(BOSS_R + 0.15, RING_H + 0.3, cx, cy, -RING_H / 2 + 0.05))
            bosses.append(i)
    lid = _union([lid] + bosses)

    # Inner lip that seats in the base
    lip = _box(
        INNER_X + 2 * LIP_T,
        INNER_Y + 2 * LIP_T,
        LIP_H,
        0,
        0,
        -LIP_H / 2 + 0.15,
    )
    lip_in = _box(INNER_X - FIT, INNER_Y - FIT, LIP_H + 1.2, 0, 0, -LIP_H / 2 + 0.15)
    lip = _diff(lip, lip_in)
    lid = _union([lid, lip])

    # Clearance over the sensor ridge (lid must not crush the 9/16\" bar)
    # No extra vents — air goes through the drilled ports in the base.
    return lid


def main():
    print(
        f"outer {OUTER_X:.1f} x {OUTER_Y:.1f} x {OUTER_Z + FEET:.1f} mm  "
        f"(stack {STACK_H:.1f} + cage {BAT_CAGE_H:.1f} + ridge {RIDGE_H:.1f})"
    )
    print("building base...")
    base = make_base()
    print("building lid...")
    lid = make_lid()
    base_path = OUT / "aq_enclosure_base.stl"
    lid_path = OUT / "aq_enclosure_lid.stl"
    base.export(base_path)
    lid.export(lid_path)
    print("wrote", base_path.name, f"{base_path.stat().st_size / 1024:.0f} KB",
          "watertight", base.is_watertight, "ext", np.round(base.extents, 1))
    print("wrote", lid_path.name, f"{lid_path.stat().st_size / 1024:.0f} KB",
          "watertight", lid.is_watertight, "ext", np.round(lid.extents, 1))


if __name__ == "__main__":
    main()
