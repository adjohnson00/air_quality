import time

import board
import busio
import digitalio
from adafruit_pm25.i2c import PM25_I2C


def _median_sample(readings):
    ranked = sorted(readings, key=lambda r: r["pm25 env"])
    return ranked[len(ranked) // 2]


class Sensor:
    """PMSA003I on STEMMA I2C2, power-gated by LDO2."""

    def __init__(self):
        self._ldo = digitalio.DigitalInOut(board.LDO2)
        self._ldo.switch_to_output(value=False)
        self._i2c = None
        self._pm = None

    def power_on(self):
        self._ldo.value = True

    def power_off(self):
        self._pm = None
        if self._i2c is not None:
            try:
                self._i2c.deinit()
            except Exception:
                pass
            self._i2c = None
        self._ldo.value = False

    def read(self, warmup_s, samples=3):
        """Warm up, take samples, power down. Returns one reading dict or None."""
        self.power_on()
        time.sleep(warmup_s)
        try:
            self._i2c = busio.I2C(board.SCL2, board.SDA2, frequency=100000)
            self._pm = PM25_I2C(self._i2c, None)
        except Exception as exc:
            print("PM25 init failed:", exc)
            self.power_off()
            return None

        readings = []
        attempts = samples + 2
        for _ in range(attempts):
            try:
                readings.append(self._pm.read())
            except RuntimeError as exc:
                print("PM25 read failed:", exc)
            if len(readings) >= samples:
                break
            time.sleep(1)

        self.power_off()
        if not readings:
            return None
        return _median_sample(readings)
