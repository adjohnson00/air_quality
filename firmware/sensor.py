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

    def __init__(self, start_on=False):
        self._ldo = digitalio.DigitalInOut(board.LDO2)
        self._ldo.switch_to_output(value=bool(start_on))
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
        print("LDO2 off")

    def ldo_pin(self):
        """DigitalInOut for LDO2, still owned. Drive it low before preserve_dios."""
        return self._ldo

    def release(self):
        """Power down and free the LDO2 pin so halt can hold it low."""
        self.power_off()
        if self._ldo is not None:
            try:
                self._ldo.deinit()
            except Exception:
                pass
            self._ldo = None

    def read(self, warmup_s, samples=3, stay_on=False):
        """Warm up, take samples. Power down unless stay_on (USB / development)."""
        cold = self._pm is None
        if cold:
            if not self._ldo.value:
                self.power_on()
            print("PM25 warmup {}s...".format(warmup_s))
            time.sleep(warmup_s)
            try:
                self._i2c = busio.I2C(board.SCL2, board.SDA2, frequency=100000)
                self._pm = PM25_I2C(self._i2c, None)
            except Exception as exc:
                print("PM25 init failed:", exc)
                self.power_off()
                return None

        readings = []
        attempts = samples + 8 if cold else samples + 2
        for i in range(attempts):
            try:
                readings.append(self._pm.read())
            except RuntimeError as exc:
                if cold and i < 6:
                    print("PM25 still starting...")
                else:
                    print("PM25 read failed:", exc)
            if len(readings) >= samples:
                break
            time.sleep(1)

        if not stay_on:
            self.power_off()
        if not readings:
            return None
        return _median_sample(readings)
