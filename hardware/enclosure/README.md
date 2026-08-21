# 3D-printed enclosure

Two-piece FDM case for the FeatherS3[D] + 2.9" eInk FeatherWing + PMSA003I + 400 mAh LiPo.

![Base](preview_base.png)

![Lid](preview_lid.png)

Outside is about **143 × 54 × 25 mm**. Display faces up. USB-C is on the left. The Plantower sits in its own bay on the right with intake/exhaust slots.

| File | What |
| --- | --- |
| [aq_enclosure_base.stl](aq_enclosure_base.stl) | Floor, USB hole, battery corral, wing pins, sensor posts, vents, A/B/C holes |
| [aq_enclosure_lid.stl](aq_enclosure_lid.stl) | Display window + bezel, inner lip, sensor vents |
| [generate.py](generate.py) | Parametric generator (edit numbers, re-run) |

## Print

| Setting | Value |
| --- | --- |
| Material | PLA is fine; PETG if it will sit in a hot car |
| Layer | 0.20 mm |
| Walls | 3 |
| Infill | 20% gyroid |
| Supports | None if you print as exported |
| Base | floor down (feet on the bed) |
| Lid | **window face on the bed** so the bezel is smooth |

The lid lip is 0.35 mm undersize. If it is too tight, sand the lip; if it rattles, add a wrap of tape or reprint `FIT = 0.25` in `generate.py`.

## Assembly

1. Drop the **400 mAh** pack into the rectangular corral (lips on the long sides). JST toward the USB end.
2. Plug the STEMMA cable into **I2C2** on the Feather, then seat the Feather + eInk stack on the four pins (they go through the wing’s 2.5 mm holes). USB-C should line up with the left wall hole.
3. Route the STEMMA through the notch in the partition into the sensor bay.
4. Seat the PMSA003I on the four shorter pins. The blue can should sit next to the side slots, not buried.
5. Snap the lid on. The window bezel should rest on the e-ink glass, not the PCB ears.

A/B/C poke through the back wall. If a hole is a millimetre off, file it — those positions were taken from the wing fab drawing, not a caliper on your board.

## Airflow

The Plantower needs a path **through** the metal can (fan in, exhaust out). The right-end wall and the back wall of the sensor bay each have four 16 × 2.4 mm slots, and the lid has three slots over the can. Do not block those. Do not seal the sensor in a closed pocket.

## Regenerating

```bash
python3 -m venv .venv
.venv/bin/pip install trimesh manifold3d numpy
.venv/bin/python hardware/enclosure/generate.py
```

Tweaks worth knowing:

- `FIT` — lid looseness
- `USB_Z` / `USB_W` / `USB_H` — if the USB-C hole is high/low/tight
- `BTN_XS` — A/B/C hole positions along the wing
- `DISP_L` / `DISP_W` — window (active area is 66.9 × 29.1 mm)
