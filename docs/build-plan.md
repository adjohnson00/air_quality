# Air Quality Monitor — Project Plan

A local, battery-powered PM2.5 monitor for Boise / Meridian fire season. Hardware is the Adafruit-sold stack in `docs/project.md`. This plan turns that BOM into a working device: assemble it, bring up each chip, then ship a duty-cycled CircuitPython firmware that shows US EPA AQI on the e-ink panel.

## Goal

On a shelf or windowsill, the stack should:

- Read PM1.0 / PM2.5 / PM10 from the PMSA003I
- Convert PM2.5 to **US EPA AQI (2024 breakpoints)**
- Show a large AQI number, category, PM2.5 µg/m³, and battery % on the 2.9" grayscale e-ink
- Sleep between samples so the 400 mAh cell lasts days, not hours
- Charge from USB-C and stay usable while plugged in

No cloud, no phone app in v1. The screen is the product.

## Hardware map (do this first, it constrains everything)

```
                    USB-C
                      │
              ┌───────┴────────┐
              │  FeatherS3[D]  │  I2C1 (LDO1, always on): MAX17048 fuel gauge
              │                │  I2C2 (LDO2, IO39): PMSA003I via STEMMA
              │  400 mAh LiPo  │  sandwiched in the header well
              │      under     │
              ├────────────────┤
              │ 2.9" eInk Wing │  SPI: SCK/MOSI/MISO
              │  SSD1680 4-gray│  CS=D9  DC=D10  SRAM CS=D6 (optional)
              │  buttons A/B/C │  RST = Feather RESET (not a GPIO)
              └────────────────┘     BUSY not connected
                       │
              STEMMA 100 mm ──► PMSA003I sitting beside the stack
                                 (fan must have free air)
```

### Pins (CircuitPython names on Unexpected Maker FeatherS3)

| Function | Feather pin | GPIO | Notes |
|---|---|---|---|
| eInk CS | `board.D9` | IO1 | Official #4777 SSD1680 example |
| eInk DC | `board.D10` | IO3 | |
| eInk SRAM CS | `board.D6` | IO38 | Can pass `None` and use onboard RAM |
| eInk SD CS | `board.D5` | IO33 | Unused in v1 |
| eInk RST / BUSY | — | — | RST tied to Feather RESET. BUSY not routed. `busy_pin=None`, never `power_down()` the panel |
| Button A / B / C | `D11` / `D12` / `D13` | IO7 / IO10 / IO11 | |
| I2C1 SDA/SCL | `board.SDA` / `SCL` | IO8 / IO9 | Fuel gauge. `board.I2C()` |
| I2C2 SDA/SCL | `board.SDA2` / `SCL2` | IO16 / IO15 | Sensor. `board.I2C2` / `board.STEMMA_I2C2` |
| LDO2 enable | `board.LDO2` | IO39 | Shared with NeoPixel power. High = I2C2 STEMMA powered |
| VBUS sense | `board.VBUS` | IO34 | USB plugged in |
| Fuel gauge | MAX17048 on I2C1 | addr 0x36 | **Do not** read `board.VBAT` analog — on [D] that pin is the gauge INT |
| PMSA003I | I2C 0x12 | — | 100 kHz. Fan + laser need ~5 V; the breakout boosts from 3.3 V |

I2C2 exists only on the on-board STEMMA jack, not on the long header. Plug the STEMMA cable into **I2C2 (the connector nearer USB)** *before* stacking the wing. The battery creates ~8 mm of gap so the cable can exit the side.

### Power budget (why the firmware must sleep)

PMSA003I active current is ≤ 100 mA at 5 V. Through the 3.3 V boost that is roughly **170–200 mA from the LiPo** while the fan is spinning. Continuous run time on 400 mAh is about **2 hours**.

Recommended duty cycle:

| State | Time | Draw (order of mag.) |
|---|---|---|
| Sensor warmup + 3 samples | 15 s | ~180 mA |
| eInk refresh | ~3 s | ~80 mA |
| Deep sleep | 15 min − that | tens–hundreds of µA |

≈ 0.8–1.2 mAh per cycle → **about 3–5 days** at 15 minutes. On USB, skip sleep and sample every 3 minutes (eInk’s documented minimum refresh interval is 180 s; faster risks damaging the film).

Do **not** leave the sensor on I2C1. I2C1 stays powered in deep sleep (fuel gauge lives there). I2C2 + LDO2 cuts the sensor completely when the chip sleeps.

## Firmware decisions

1. **CircuitPython**, not Arduino. The board ships with it; Adafruit already has `adafruit_pm25`, `adafruit_epd` (SSD1680 4-gray), and `adafruit_max1704x`.
2. **`adafruit_epd.Adafruit_SSD1680_Grayscale4`**, not the old `adafruit_il0373` driver. July 2025 boards use SSD1680. Follow [feather_epd_grayscale_2in9_4777.py](https://github.com/adafruit/Adafruit_CircuitPython_EPD/blob/main/examples/feather_epd_grayscale_2in9_4777.py): `vcom=0x24`, rotation 3, subclass `power_down()` as a no-op.
3. **US EPA PM2.5 AQI, 2024 breakpoints** (AirNow / Idaho DEQ use this). Label the screen **AQI** but treat it as instantaneous concentration, not 24-hour NowCast, until we have hourly history.

   | PM2.5 µg/m³ | AQI | Category |
   |---|---|---|
   | 0.0 – 9.0 | 0 – 50 | Good |
   | 9.1 – 35.4 | 51 – 100 | Moderate |
   | 35.5 – 55.4 | 101 – 150 | USG |
   | 55.5 – 125.4 | 151 – 200 | Unhealthy |
   | 125.5 – 225.4 | 201 – 300 | Very Unhealthy |
   | 225.5 – 325.4 | 301 – 500 | Hazardous |

   Use **environmental** (`pm25 env`) values from the sensor.

4. **Refresh the panel only when it matters**: category change, PM2.5 delta ≥ 2 µg/m³, or at least once per hour. Saves eInk life and wake time.
5. **v1 is indoor / porch, local-only.** Outdoor enclosure, rain hood, and WiFi logging are explicit later work. The laser sensor needs a clear intake; a sealed box will lie.

## Assembly (one sitting, no soldering if the wing has sockets)

1. Update CircuitPython from [circuitpython.org](https://circuitpython.org/downloads?q=unexpected+maker) if the shipping build is old. Confirm `board.I2C2`, `board.LDO2`, `board.D9` exist (`dir(board)` in the REPL).
2. Identify **I2C2** on the Feather (near USB). Plug the **100 mm** STEMMA cable there. 50 mm is likely too short once the wing is on.
3. Check LiPo polarity against the JST-PH silkscreen. Seat the 400 mAh cell in the header well. Use the wing’s **normal-height** sockets, not shorty headers.
4. Stack the eInk FeatherWing. Route the STEMMA cable out the side through the battery gap.
5. Leave the PMSA003I **beside** the stack, vents unobstructed. Do not sandwich it.
6. First power-on from **USB-C data** (not charge-only) with the battery connected so the charger and fuel gauge can be verified.

LiPo rules from the Adafruit docs: charge only via the Feather, never unattended for long, never puncture/bend, 400 mA max charge.

## Software architecture

```
firmware/
  code.py              # boot: USB vs battery path, sample loop or deep-sleep
  settings.toml        # SAMPLE_INTERVAL_S, SENSOR_WARMUP_S, refresh thresholds
  aqi.py               # EPA 2024 PM2.5 breakpoints + category colors/labels
  sensor.py            # LDO2 on → warmup → median of 3 reads → LDO2 off
  battery.py           # MAX17048 percent + voltage; VBUS detect
  display_ui.py        # 296×128 4-gray card
  power.py             # alarm deep sleep; pin alarms for buttons
  lib/                 # circup-installed Adafruit libs (gitignored)
```

`code.py` loop (battery):

1. Enable `board.LDO2`.
2. Sleep `SENSOR_WARMUP_S` (default 15).
3. `PM25_I2C(board.I2C2, reset_pin=None)` at 100 kHz. Median of 3 `read()` calls. On checksum error, retry twice then show last-good + a stale flag.
4. Read MAX17048 on `board.I2C()`.
5. `aqi.from_pm25(env)`.
6. If refresh needed → draw card → `display.display()`.
7. Drive `LDO2` low. `alarm.exit_and_deep_sleep_until_alarms(TimeAlarm, optional button PinAlarm)`.

USB (`board.VBUS` high): same sample/draw path, no deep sleep, 180 s interval, serial logging on. This is also the development mode.

### Display card (296×128, landscape)

```
┌──────────────────────────────────────────┐
│  85            MODERATE                  │
│  ████████████░░░░░░░░░░░░                │  4-gray AQI bar
│  PM2.5  28 µg/m³                         │
│  PM10 41    73%    15m ago               │
└──────────────────────────────────────────┘
```

- Page A (default): AQI + PM2.5
- Page B (button B): particle bins 0.3–10 µm
- Button A: force sample + refresh
- Button C: reserved (hold for settings later)

Four gray levels are the category language: black = this is serious, dark/light = mid, white = good. Do not try to fake AirNow’s green/yellow/red.

## Repo layout to create

```
firmware/          # CircuitPython app above
hardware/assembly.md
README.md          # what it is, how to flash, how to read the screen
docs/              # already present — leave as reference
```

Keep secrets out of git. `settings.toml` can live on `CIRCUITPY` and a `settings.toml.example` in the repo.

## Implementation phases

### Phase 0 — Repo and toolchain
Create the tree, `README`, `.gitignore` (`firmware/lib/`, `.DS_Store`). Document `circup install adafruit_pm25 adafruit_epd adafruit_max1704x`. Unit-test `aqi.py` on the host (pure math, no hardware).

### Phase 1 — Hardware bring-up (USB, no sleep)
Assemble per the steps above. REPL checklist:

- `board.I2C().scan()` → `0x36` (MAX17048)
- Enable LDO2, `board.I2C2.scan()` → `0x12` (PMSA003I)
- Feather RGB / blue LED blink so we know the board is alive

### Phase 2 — Sensor
`sensor.py` + serial print of env/standard PM and particle counts. Confirm warmup time empirically (datasheet total response ≤ 10 s; start at 15 s). Median-of-3 to ignore the first dirty sample after the fan spins up.

### Phase 3 — Display
Port the official SSD1680 4-gray FeatherWing example. Draw the AQI card with canned numbers. Confirm rotation, contrast (`vcom=0x24`), and that a refresh takes a few seconds. **Do not** call the driver’s `power_down()`.

### Phase 4 — Integrate live data
Wire sensor → AQI → display. Stale/error card if the sensor nacks. Show battery % from MAX17048.

### Phase 5 — Power management
Implement LDO2 gating and `alarm` deep sleep. Measure:

- USB current during warmup, during refresh, during sleep (USB meter or bench supply)
- Time-to-first-valid-sample after LDO2 on
- Overnight run on battery; confirm the image survives sleep

Tune `SENSOR_WARMUP_S` and `SAMPLE_INTERVAL_S` from that data. Default 15 min.

### Phase 6 — Buttons and polish
A = force sample, B = flip page. Persist last reading + hourly PM2.5 averages in NVM (`alarm.sleep_memory` or a small file) so a reset still has something to show. Optional: compute EPA NowCast once 12 hourly points exist.

### Phase 7 — Field check
Incense or a dusty walk as a smoke proxy. Compare the reading to AirNow / PurpleAir for the Boise area (expect a bias — this is a $45 Plantower, not an FEM). Verify sunlight readability and that the fan is not blocked in the real placement.

## Risks

| Risk | Mitigation |
|---|---|
| Wrong eInk driver (IL0373 vs SSD1680) | Use `Adafruit_SSD1680_Grayscale4`; blank/garbage screen means chipset mismatch |
| STEMMA jack buried under the wing | Cable I2C2 **before** stacking; 100 mm cable |
| 400 mAh dies in an afternoon | LDO2 duty cycle is mandatory; be honest about 3–5 day life |
| Sensor on I2C1 never powers down | I2C2 only |
| Checksum errors after power-gate | Warmup + retries; don’t draw a zero AQI on failure |
| eInk worn by 30 s updates | 180 s floor; skip refresh if the card would not change |
| FeatherS3 vs FeatherS3[D] pin confusion | `board.VBAT` analog is wrong on [D]; use MAX17048 |
| Outdoor rain / condensation | Out of scope for v1; do not seal the sensor |

## Out of scope for v1

- WiFi, Adafruit IO, MQTT, a web dashboard
- CO2 / VOC / humidity (no extra sensors on the BOM)
- Official NowCast as the primary number (needs 12 h of data first)
- 3D-printed outdoor enclosure
- A larger battery (easy later drop-in if 400 mAh is too short)

## What “done” looks like

USB-C plugged in: the panel shows a live AQI card that updates every 3 minutes, serial prints each sample, battery % climbs while charging.

Unplugged: the same card, updates every 15 minutes, survives overnight on the 400 mAh cell, wakes on button A.

That is the monitor. Everything else is a later revision.
