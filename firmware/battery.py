import board
import digitalio
import adafruit_max1704x


def usb_connected():
    pin = digitalio.DigitalInOut(board.VBUS)
    pin.switch_to_input()
    present = bool(pin.value)
    pin.deinit()
    return present


def read():
    """MAX17048 on I2C1. Do not use board.VBAT analog on FeatherS3[D]."""
    try:
        monitor = adafruit_max1704x.MAX17048(board.I2C())
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
