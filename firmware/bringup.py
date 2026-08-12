"""Hardware bring-up. Copy to CIRCUITPY as code.py for the first power-on.

Expected I2C1 scan: 0x36 (MAX17048 fuel gauge)
Expected I2C2 scan (after LDO2 on): 0x12 (PMSA003I)
"""

import time

import board
import busio
import digitalio
import neopixel


def _scan(label, i2c):
    while not i2c.try_lock():
        pass
    try:
        found = list(i2c.scan())
    finally:
        i2c.unlock()
    hex_addrs = ["0x{:02x}".format(addr) for addr in found]
    print(label, hex_addrs)
    return found


def main():
    print("=== air quality bring-up ===")
    print("board pins:", dir(board))
    for name in ("D9", "D10", "D11", "I2C2", "LDO2", "SDA2", "SCL2", "VBUS"):
        print("  has", name, hasattr(board, name))

    vbus = digitalio.DigitalInOut(board.VBUS)
    vbus.switch_to_input()
    print("VBUS (USB):", vbus.value)
    vbus.deinit()

    print("Scanning I2C1 (fuel gauge)...")
    found1 = _scan("I2C1", board.I2C())
    if 0x36 in found1:
        print("MAX17048 OK")
    else:
        print("MAX17048 NOT FOUND at 0x36")

    print("Enabling LDO2 and scanning I2C2 (PMSA003I)...")
    ldo = digitalio.DigitalInOut(board.LDO2)
    ldo.switch_to_output(value=True)
    time.sleep(1)
    i2c2 = busio.I2C(board.SCL2, board.SDA2, frequency=100000)
    found2 = _scan("I2C2", i2c2)
    if 0x12 in found2:
        print("PMSA003I OK")
    else:
        print("PMSA003I NOT FOUND at 0x12 — check STEMMA is on I2C2 (near USB)")
    i2c2.deinit()
    ldo.value = False

    print("Blinking NeoPixel")
    pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
    for color in ((255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0)):
        pixels[0] = color
        time.sleep(0.4)
    print("Bring-up done. Replace code.py with the monitor firmware.")


main()
