import time

try:
    import board
    import digitalio
    import adafruit_max1704x
except ImportError:
    board = None
    digitalio = None
    adafruit_max1704x = None

_monitor = None
_prev_present = False


def usb_connected():
    if board is None:
        return False
    pin = digitalio.DigitalInOut(board.VBUS)
    pin.switch_to_input()
    present = bool(pin.value)
    pin.deinit()
    return present


def interpret(voltage, percent, usb):
    """Decide whether a LiPo is actually present.

    USB with no cell still puts ~4.0–4.3 V on the charger node and the MAX17048
    SOC runs away (>100%). That is not a pack.
    """
    runaway = percent is not None and (percent > 100.5 or percent < 0)
    v_ok = voltage is not None and 3.2 <= voltage <= 4.35
    if runaway:
        return False, None, None if usb else voltage
    if not v_ok:
        return False, None, None if usb else voltage
    shown = None if percent is None else min(100.0, max(0.0, percent))
    return True, shown, voltage


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
    global _prev_present
    try:
        monitor = _get_monitor()
        voltage = monitor.cell_voltage
        percent = monitor.cell_percent
        usb = usb_connected()
        present, shown_pct, shown_v = interpret(voltage, percent, usb)
        if present and not _prev_present:
            # Pack just appeared after USB-only / unplug. Restart SOC.
            monitor.quick_start = True
            time.sleep(0.5)
            voltage = monitor.cell_voltage
            percent = monitor.cell_percent
            present, shown_pct, shown_v = interpret(voltage, percent, usb)
        _prev_present = present
        return {
            "percent": shown_pct,
            "voltage": shown_v,
            "present": present,
        }
    except Exception as exc:
        print("Fuel gauge read failed:", exc)
        _prev_present = False
        return {"percent": None, "voltage": None, "present": False}
