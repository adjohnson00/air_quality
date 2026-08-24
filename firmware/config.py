import os


def get_int(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        try:
            return int(float(raw))
        except ValueError:
            return default


def get_float(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


SAMPLE_INTERVAL_S = get_int("SAMPLE_INTERVAL_S", 60)
USB_SAMPLE_INTERVAL_S = get_int("USB_SAMPLE_INTERVAL_S", 60)
SENSOR_WARMUP_S = get_int("SENSOR_WARMUP_S", 5)
MAX_STALE_REFRESH_S = get_int("MAX_STALE_REFRESH_S", 3600)
SENSOR_SAMPLES = get_int("SENSOR_SAMPLES", 3)
# If the sample interval is shorter than this, leave LDO2/PMSA003I powered.
KEEP_SENSOR_ON_BELOW_S = get_int("KEEP_SENSOR_ON_BELOW_S", 30)
LOW_BATTERY_V = get_float("LOW_BATTERY_V", 3.2)
LOW_BATTERY_SLEEP_S = get_int("LOW_BATTERY_SLEEP_S", 3600)


def get_str(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    cleaned = raw.strip().strip('"').strip("'").lower()
    return cleaned if cleaned else default


# deep = lowest power, code.py restarts each wake
# light = RAM kept, faster wake, more sleep current
# no = CPU always on; LDO2/sensor on only for each sample
# full = CPU and LDO2/sensor always on
_SLEEP_MODES = ("deep", "light", "no", "full")
SLEEP_MODE = get_str("SLEEP_MODE", "deep")
if SLEEP_MODE not in _SLEEP_MODES:
    SLEEP_MODE = "deep"

# 1 = append voltN.csv each sample; 0 = off
VOLTAGE_LOG = get_int("VOLTAGE_LOG", 1)


def use_deep_sleep():
    return SLEEP_MODE == "deep"


def use_light_sleep():
    return SLEEP_MODE == "light"


def cpu_always_on():
    return SLEEP_MODE in ("no", "full")


def sensor_always_on():
    return SLEEP_MODE == "full"


def keep_sensor_powered(interval_s):
    """Leave LDO2 up after a sample.

    full: always. no: only if the interval is too short to power-cycle.
    deep/light: yes for the wake; sleep path turns LDO2 off.
    """
    if SLEEP_MODE == "full":
        return True
    if SLEEP_MODE == "no":
        return interval_s < KEEP_SENSOR_ON_BELOW_S
    return True
