# Air quality monitor

Local, battery-powered PM2.5 monitor for fire season in the Boise / Meridian area.

Hardware is an Unexpected Maker FeatherS3[D], Adafruit 2.9" grayscale eInk FeatherWing, PMSA003I particle sensor, STEMMA QT cable, and a 400 mAh LiPo.

- [docs/project.md](docs/project.md) — BOM and goals
- [docs/build-plan.md](docs/build-plan.md) — pin map, power budget, firmware plan
- [hardware/assembly.md](hardware/assembly.md) — how to stack the boards
- [docs/](docs/) — vendor datasheets and learn guides

## Firmware

CircuitPython on the FeatherS3[D]. Source is in [`firmware/`](firmware/).

### Libraries

On a computer with the board mounted as `CIRCUITPY`:

```bash
pip install circup
circup install adafruit_pm25 adafruit_epd adafruit_max1704x adafruit_register neopixel
```

Copy `font5x8.bin` from the [Adafruit_CircuitPython_framebuf](https://github.com/adafruit/Adafruit_CircuitPython_framebuf/blob/main/examples/font5x8.bin) repo onto the root of `CIRCUITPY`. The eInk text routines need it.

### Install

1. Assemble the stack ([hardware/assembly.md](hardware/assembly.md)).
2. Copy `firmware/bringup.py` to `CIRCUITPY/code.py` and confirm I2C addresses in the serial console.
3. Copy the rest of `firmware/` onto `CIRCUITPY` (`code.py`, `aqi.py`, `sensor.py`, `battery.py`, `display_ui.py`, `power.py`, `persist.py`, `config.py`, `settings.toml`).
4. The board resets and draws the AQI card.

USB plugged in: sample every 3 minutes (eInk minimum). Unplugged: sample every 15 minutes and deep-sleep. Button A forces a sample. Button B flips to particle counts.

### Tests (no hardware)

```bash
python3 -m unittest tests.test_aqi
```
