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
    # 2.9 V is the charger trickle threshold / pack still present. 3.2 was the
    # halt line, so a 3.18 V trigger was treated as "no pack" and dropped from the CSV.
    v_ok = voltage is not None and 2.9 <= voltage <= 4.35
    if runaway:
        return False, None, None if usb else voltage
    if not v_ok:
        return False, None, None if usb else voltage
    shown = None if percent is None else min(100.0, max(0.0, percent))
    return True, shown, voltage


# ModelGauge CRATE is noisy near zero; this is "clearly charging", not C/10.
_CHARGE_RATE_MIN = 2.0


def charge_label(usb, present, charge_rate):
    """Footer text while USB is putting energy into a real pack.

    charge_rate is MAX17048 CRATE in percent/hour (voltage-model, not mA).
    """
    if not usb or not present or charge_rate is None:
        return None
    if charge_rate < _CHARGE_RATE_MIN:
        return None
    return "+{:.0f}%/h".format(charge_rate)


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


def mark_present():
    """Pack was already in use (e.g. deep-sleep wake). Do not quick-start."""
    global _prev_present
    _prev_present = True


def read():
    """MAX17048 on I2C1. Do not use board.VBAT analog on FeatherS3[D]."""
    global _prev_present
    try:
        monitor = _get_monitor()
        voltage = monitor.cell_voltage
        percent = monitor.cell_percent
        rate = monitor.charge_rate
        usb = usb_connected()
        present, shown_pct, shown_v = interpret(voltage, percent, usb)
        if present and not _prev_present:
            # First sighting this boot (or after USB-only). OCV-based SOC, not a learn cycle.
            print("Battery appeared; MAX17048 quick-start")
            monitor.quick_start = True
            time.sleep(0.5)
            voltage = monitor.cell_voltage
            percent = monitor.cell_percent
            rate = monitor.charge_rate
            present, shown_pct, shown_v = interpret(voltage, percent, usb)
        _prev_present = present
        if not present:
            rate = None
        return {
            "percent": shown_pct,
            "voltage": shown_v,
            "present": present,
            "charge_rate": rate,
            "charge_label": charge_label(usb, present, rate),
        }
    except Exception as exc:
        print("Fuel gauge read failed:", exc)
        _prev_present = False
        return {
            "percent": None,
            "voltage": None,
            "present": False,
            "charge_rate": None,
            "charge_label": None,
        }
