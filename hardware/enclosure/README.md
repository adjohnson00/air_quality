# 3D-printed enclosure (rev 2)

Two-piece FDM case. Display faces up. USB-C out the **bottom**. RP-SMA antenna bulkhead on the **left**. PMSA003I inline on the **right**, I/O at the **top**.

![Base](preview_base.png)

![Lid](preview_lid.png)

Outside is about **145 × 56 × 45 mm**.

```
  TOP (+Y)     intake ○ | ○ exhaust     (drill later; raised rings)
               ─────────┴─────────
  LEFT (-X)    [RP-SMA]  [ 2.9" eInk ]  [ PMSA003I ]
  BOTTOM (-Y)            [ USB-C     ]
  UNDER STACK            [ battery cage, 1/2" ]
```

| File | What |
| --- | --- |
| [aq_enclosure_base.stl](aq_enclosure_base.stl) | Battery cage, USB opening, SMA pad, sensor shelf + 9/16" ridge, intake/exhaust divider |
| [aq_enclosure_lid.stl](aq_enclosure_lid.stl) | Window, inner + outer wing pockets, filled mounting bosses |
| [generate.py](generate.py) | Parametric generator |

## What changed vs rev 1

- Stack is **1"** (Feather + eInk + USB out the bottom). Battery is **not** in the sandwich.
- Battery lives in a **low-lipped cage** under the stack: 3/8" cell, **1/2"** cage height. Interior of the cage is 70 × 38 mm — measure your new pack and set `BAT_L` / `BAT_W` if it is smaller/larger.
- **Lid mounts the display.** Same four bosses work two ways:
  - **Inside** the lid → glass in the window, buttons hidden
  - **Outside** the lid → wing sits in the outer pocket, buttons reachable
- **RP-SMA** (uFL pigtail, threaded barrel) on the left end. Printed **solid** with a raised ring; drill 6.5 mm after printing.
- **No printed through-holes** except USB-C. Wing, sensor, SMA, and air ports are filled pads at wall thickness with a raised ring as a drill guide.
- Sensor is inline to the right. A wall splits **intake** (hole in the blue aluminum) from **exhaust** (black fan). Each path ends at a raised ring on the top wall — drill those after you confirm alignment. A **9/16" ridge** over the module mounting holes sits snug on the can.

## Drill later

| Mark | Size | Where |
| --- | --- | --- |
| 4 rings on the lid | 2.5 mm | eInk FeatherWing corners |
| 4 rings on the sensor shelf | 2.5 mm | PMSA003I PCB |
| 1 ring on the left wall | 6.5 mm | RP-SMA bulkhead |
| 2 rings on the top wall | ~8–10 mm | intake (left of the divider) and exhaust (right, fan) |

## Print

| Setting | Value |
| --- | --- |
| Material | PLA; PETG if it will sit in a hot car |
| Layer | 0.20 mm |
| Walls | 3 |
| Infill | 20% gyroid |
| Supports | None |
| Base | floor down (feet on the bed) |
| Lid | **outer face / window on the bed** so the outside pocket is smooth |

Lid lip is 0.35 mm undersize (`FIT`). Sand if tight.

## Assembly

1. Drop the pack into the cage under the display bay, JST toward USB.
2. uFL pigtail on the Feather; RP-SMA barrel waits until you drill the left pad.
3. STEMMA into I2C2, cable through the partition notch (back/right of the display).
4. **Inside mount:** seat the wing in the inner lid pocket, glass in the window, screw after drilling. Buttons face the battery cage.
5. **Outside mount:** seat the wing in the outer lid pocket, glass facing out, buttons on the back of the wing in the open. Screw after drilling.
6. PMSA003I on the right-hand shelf. Fan toward the **top-right** port, blue intake hole toward the **top-left** port. The ridge should rest on the can. Snap the lid on.
7. Drill intake and exhaust only after a dry fit so the holes line up with the fan and the aluminum inlet. Do not let those two volumes mix.

## Regenerating

```bash
.venv/bin/python hardware/enclosure/generate.py
```

| Knob | Default | Meaning |
| --- | --- | --- |
| `BAT_L` / `BAT_W` | 70 / 38 | Cage inside, mm |
| `BAT_CAGE_H` | 12.7 | 1/2" |
| `STACK_H` | 25.4 | 1" electronics |
| `RIDGE_H` | 14.3 | 9/16" over the sensor |
| `SMA_Z` | cage + 10 | Height of the SMA pad |
| `FIT` | 0.35 | Lid looseness |
