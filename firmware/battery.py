import time

import board
import digitalio
import adafruit_max1704x

_monitor = None


def usb_connected():
    pin = digitalio.DigitalInOut(board.VBUS)
    pin.switch_to_input()
    present = bool(pin.value)
    pin.deinit()
    return present


def _get_monitor():
    global _monitor
    if _monitor is None:
        # Constructing MAX17048() resets the chip; do it once, not every sample.
        _monitor = adafruit_max1704x.MAX17048(board.I2C())
        _monitor.enable_sleep = False
        _monitor.sleep = False
        _monitor.wake()
        time.sleep(0.3)
    return _monitor


def read():
    """MAX17048 on I2C1. Do not use board.VBAT analog on FeatherS3[D]."""
    try:
        monitor = _get_monitor()
        voltage = monitor.cell_voltage
        percent = monitor.cell_percent
        present = voltage is not None and voltage >= 3.2
        return {
            "percent": percent if present else None,
            "voltage": voltage,
            "present": present,
        }
    except Exception as exc:
        print("Fuel gauge read failed:", exc)
        return {"percent": None, "voltage": None, "present": False}
