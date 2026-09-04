#!/usr/bin/env python3
"""Two-piece FDM enclosure for the air-quality stack (rev 2).

Layout (display facing +Z):
  LEFT (-X)   antenna RP-SMA bulkhead (filled, drill later)
  BOTTOM (-Y) closed; STEMMA wall in the sensor bay
  CENTER      1\" Feather + eInk stack over a 1/2\" battery cage
  RIGHT (+X)  PMSA003I on the FLOOR, centered on the display in Y.
              Air-channel lips/divider near the +Y wall. Freestanding
              -Y lip stops short of the two bottom holes (STEMMA).

Mounting holes and air ports print SOLID at wall thickness with a raised
ring as a drill guide. No USB opening — plug in with the lid off
(connector faces the AQI bay).

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
STACK_H = 1.00 * IN          # screen + Feather + USB (lid-off, toward AQI)
BAT_CAGE_H = 0.50 * IN       # 3/8\" cell, 1/2\" cage
RIDGE_H = 0.5625 * IN        # 9/16\" snug over the PMSA003I can

# 2.9" grayscale eInk FeatherWing (Adafruit 4777), from Eagle.
# PCB 3.125" x 1.850". Holes are a 74.30 x 42.16 mm rectangle, centered.
# The e-ink MODULE (obstruction) is 79.0 x 36.7 mm — almost the full PCB
# length, so the four holes sit *inside* that rectangle in X and just
# outside it in Y (corner tabs). Lid opening is the module, with corner
# pads unioned back so the holes still have something to screw through.
WING_L = 79.375
WING_W = 46.990
WING_HOLE_DX = 74.295
WING_HOLE_DY = 42.164
PANEL_L = 79.0
PANEL_W = 36.7
PANEL_OX = 0.16              # panel center − PCB center, along WING_L
PANEL_OY = -0.10
TAB_R = 4.2                  # corner pad that holds each hole in the opening

# Pack: 2.00\" x 1-5/16\" x 3/8\". Cage interior adds ~2 mm clearance.
BAT_L = 52.8
BAT_W = 35.3
BAT_LIP = 1.2
BAT_WALL = 1.6

# PMSA003I breakout (Adafruit 4632). Eagle: 35.56 x 50.80 mm, header at y=0,
# can/fan at y=50.8. In the case the 2\" axis runs along +X (header toward
# the display, can at the far wall). PCB-left edge is the TOP of the display
# so two corner holes sit on +Y and the third is at -Y nearest the display.
SENS_W = 35.56               # board width (PCB x) → enclosure Y
SENS_L = 50.80               # header → can (PCB y) → enclosure X
# M2.5 holes in board-local mm (origin = header-left corner).
# 3 corners + 1 on the output-side edge (not a 4-corner rectangle).
# "inside" = open on the PCB (screw down from above). "outside" = under the
# can (drill from the bottom, screw up).
SENS_HOLES = (
    (2.54, 2.54, "inside"),     # header left  → top, near display
    (33.02, 2.54, "inside"),    # header right → bottom, near display
    (2.754, 48.3, "outside"),   # can-end left → top, far end
    (32.754, 15.3, "outside"),  # output-side edge → bottom
)
SENS_STEMMA = (33.02, 8.89)  # QT jack on the bottom edge, near the display
GAP = 6.0
PLENUM = 9.0                 # intake/exhaust channels at +Y of the sensor
CHANNEL_LIP = 3.5            # how far the 9/16\" lip sits onto the can (not a roof)
CHANNEL_LIP_T = 1.8          # lip thickness; roofs the air channel only
DIV_FROM_FAR = 0.875 * IN    # 7/8\" from the far end (1-1/8\" from the display side)

# RP-SMA bulkhead: ~6.5 mm drill, 1/4-36 thread. Print filled.
SMA_DRILL = 6.5
SMA_PAD = 8.0
SMA_RING = 10.5
SMA_Z = BAT_CAGE_H + 10.0    # mid-stack on the left wall

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


def _filled_pad(cx, cy, cz, axis="z", pad=BOSS_R, ring=RING_R, h=WALL, rh=RING_H, ring_dir=1):
    """Solid pad + raised ring. Drill the pad later. ring_dir +1 = +axis face."""
    body = _cyl(pad, h, cx, cy, cz, axis=axis)
    s = 1 if ring_dir >= 0 else -1
    if axis == "z":
        rz = cz + s * (h / 2 + rh / 2 - 0.05)
        r = _cyl(ring, rh, cx, cy, rz, axis=axis)
        hole = _cyl(pad + 0.15, rh + 0.2, cx, cy, rz, axis=axis)
    elif axis == "x":
        rx = cx + s * (h / 2 + rh / 2 - 0.05)
        r = _cyl(ring, rh, rx, cy, cz, axis=axis)
        hole = _cyl(pad + 0.15, rh + 0.2, rx, cy, cz, axis=axis)
    else:
        ry = cy + s * (h / 2 + rh / 2 - 0.05)
        r = _cyl(ring, rh, cx, ry, cz, axis=axis)
        hole = _cyl(pad + 0.15, rh + 0.2, cx, ry, cz, axis=axis)
    r = _diff(r, hole)
    return _union([body, r])


def _ring(cx, cy, cz, pad=BOSS_R, ring=RING_R, rh=RING_H):
    """Raised drill-guide ring on the XY plane, centered at cz."""
    r = _cyl(ring, rh, cx, cy, cz)
    return _diff(r, _cyl(pad + 0.15, rh + 0.2, cx, cy, cz))


def _bays():
    """Display bay center and sensor bay center."""
    wing_cx = -INNER_X / 2 + WING_L / 2 + 1.5
    # USB / bottom of the display sits on the -Y wall
    wing_cy = -INNER_Y / 2 + WING_W / 2 + 1.5
    # Sensor to the right, centered on the display in Y so the air-channel
    # lips sit near the +Y wall and there is room under the module for STEMMA.
    sens_cx = INNER_X / 2 - SENS_L / 2 - 1.0
    sens_cy = wing_cy
    return wing_cx, wing_cy, sens_cx, sens_cy


def _sens_xy(sens_cx, sens_cy, px, py):
    """Board-local mm (header-left origin) → enclosure XY.

    Header toward the display (-X), can toward +X.
    PCB left edge at +Y (top of display), right edge at -Y.
    """
    return (
        sens_cx + (py - SENS_L / 2),
        sens_cy + (SENS_W / 2 - px),
    )


def make_base():
    ox, oy = OUTER_X, OUTER_Y
    wing_cx, wing_cy, sens_cx, sens_cy = _bays()
    floor_z = WALL
    shelf_z = WALL + BAT_CAGE_H  # top of battery cage (USB / stack height)

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

    # --- partition display | sensor ---
    px = (wing_cx + WING_L / 2 + sens_cx - SENS_L / 2) / 2
    part_h = INNER_Z - LIP_H - 1
    partition = _box(WALL, INNER_Y - 0.6, part_h, px, 0, floor_z + part_h / 2)
    stemma_x, stemma_y = _sens_xy(sens_cx, sens_cy, *SENS_STEMMA)
    notch = _box(
        WALL + 3,
        14.0,
        14.0,
        px,
        stemma_y - 2.0,
        floor_z + 7.0,
    )
    partition = _diff(partition, notch)
    base = _union([base, partition])

    # Freestanding -Y lip, battery-cage style, snug to the module edge.
    # Stops before the two bottom-side mounting holes so the STEMMA cable
    # can reach the QT jack. Far +X end kisses the enclosure wall.
    wall_t = BAT_WALL
    lip_h = 10.0
    y_pcb0 = sens_cy - SENS_W / 2
    lip_y = y_pcb0 - 0.4 - wall_t / 2
    bot_holes_x = [
        _sens_xy(sens_cx, sens_cy, hx, hy)[0]
        for hx, hy, _how in SENS_HOLES
        if _sens_xy(sens_cx, sens_cy, hx, hy)[1] < sens_cy
    ]
    x0 = max(bot_holes_x) + 6.0
    x1 = INNER_X / 2 + 0.4
    bot_lip = _box(
        x1 - x0,
        wall_t,
        lip_h,
        (x0 + x1) / 2,
        lip_y,
        floor_z + lip_h / 2,
    )
    base = _union([base, bot_lip])

    # --- PMSA003I on the floor (no raised shelf) ---
    # Interior rings at all 4 holes so the PCB sits level (~0.4 mm).
    # The two under-can holes also get a ring on the OUTSIDE of the floor
    # so you can drill from below and screw up.
    marks = []
    for hx, hy, how in SENS_HOLES:
        x, y = _sens_xy(sens_cx, sens_cy, hx, hy)
        marks.append(_ring(x, y, WALL + RING_H / 2 - 0.05, rh=0.4))
        if how == "outside":
            marks.append(_ring(x, y, -RING_H / 2 + 0.05, rh=0.7))
    base = _union([base] + marks)

    # Air ducts at +Y (top of the display). Module open on top. A 9/16"
    # lip sits a few mm onto the can and roofs the plenum to the +Y wall.
    # Divider is 7/8" from the far end: intake toward the display, exhaust
    # (fan) toward +X. Slicer supports fill the ducts; pull before assembly.
    y_top = sens_cy + SENS_W / 2
    y_inner = INNER_Y / 2
    wall_t = 1.8
    into_wall = 1.0
    far_x = sens_cx + SENS_L / 2
    divider_x = far_x - DIV_FROM_FAR

    lip_y0 = y_top - CHANNEL_LIP
    lip_y1 = y_inner + into_wall
    lip_sy = lip_y1 - lip_y0
    lip_cy = (lip_y0 + lip_y1) / 2
    lip_top = floor_z + RIDGE_H + CHANNEL_LIP_T
    lip_z = lip_top - CHANNEL_LIP_T / 2

    # Divider lives in the plenum only (not through the can). A 0.6 mm
    # kiss onto the +Y face seals intake from exhaust at the I/O.
    duct_h = lip_top - floor_z
    div_y0 = y_top - 0.6
    div_sy = lip_y1 - div_y0
    div_cy = (div_y0 + lip_y1) / 2
    divider = _box(wall_t, div_sy, duct_h, divider_x, div_cy, floor_z + duct_h / 2)
    base = _union([base, divider])

    # Intake lip: partition → divider. Exhaust lip: divider → +X inner wall.
    x_part = px + WALL / 2
    x_plus = INNER_X / 2
    for x0, x1 in (
        (x_part - 0.4, divider_x + 0.4),
        (divider_x - 0.4, x_plus + 0.4),
    ):
        base = _union(
            [
                base,
                _box(x1 - x0, lip_sy, CHANNEL_LIP_T, (x0 + x1) / 2, lip_cy, lip_z),
            ]
        )

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

    # Air ports on the TOP (+Y) wall: intake (toward display) and exhaust (fan, far)
    air_z = floor_z + RIDGE_H * 0.55
    near_x = sens_cx - SENS_L / 2
    intake_x = (near_x + divider_x) / 2
    exhaust_x = (divider_x + far_x) / 2
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

    # Through-opening is the e-ink MODULE (79.0 x 36.7), not the glass.
    # The four holes lie inside that rectangle in X, so they are restored
    # as corner tabs after the cut.
    panel_cx = wing_cx + PANEL_OX
    panel_cy = wing_cy + PANEL_OY
    window = _box(PANEL_L + 0.6, PANEL_W + 0.8, LID_T + 4, panel_cx, panel_cy, LID_T / 2)
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

    # Corner tabs + filled pads at the real hole pattern, rings both faces
    bosses = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = wing_cx + sx * WING_HOLE_DX / 2
            cy = wing_cy + sy * WING_HOLE_DY / 2
            bosses.append(_cyl(TAB_R, LID_T, cx, cy, LID_T / 2))
            bosses.append(_cyl(BOSS_R, LID_T, cx, cy, LID_T / 2))
            o = _cyl(RING_R, RING_H, cx, cy, LID_T + RING_H / 2 - 0.05)
            o = _diff(o, _cyl(BOSS_R + 0.15, RING_H + 0.3, cx, cy, LID_T + RING_H / 2 - 0.05))
            bosses.append(o)
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

    # Clearance over the 9/16\" channel lips (lid must not crush them).
    # No extra vents — air goes through the drilled ports in the base.
    return lid


def _preview(mesh, path, title, elev=22, azim=-50):
    """Translucent matplotlib snapshot so the README shows the current STL."""
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(9.5, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    faces = mesh.triangles
    if len(faces) > 9000:
        rng = np.random.default_rng(0)
        faces = faces[rng.choice(len(faces), 9000, replace=False)]
    coll = Poly3DCollection(
        faces,
        alpha=0.38,
        facecolor="#5b8fc9",
        edgecolor="#2a4a68",
        linewidths=0.07,
    )
    ax.add_collection3d(coll)
    c = np.array(mesh.centroid, dtype=float)
    m = float(np.max(mesh.extents)) * 0.58
    ax.set_xlim(c[0] - m, c[0] + m)
    ax.set_ylim(c[1] - m, c[1] + m)
    ax.set_zlim(c[2] - m, c[2] + m)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title)
    fig.savefig(path, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)


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
    print("previews...")
    _preview(
        base,
        OUT / "preview_base.png",
        "base — no USB hole, AQI Y-centered, bottom lip stops at holes",
        elev=28,
        azim=-48,
    )
    _preview(
        lid,
        OUT / "preview_lid.png",
        "lid — module opening + corner hole tabs",
        elev=70,
        azim=-90,
    )
    print("wrote preview_base.png preview_lid.png")


if __name__ == "__main__":
    main()
