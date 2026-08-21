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
PM25_REFRESH_DELTA = get_int("PM25_REFRESH_DELTA", 1)
MAX_STALE_REFRESH_S = get_int("MAX_STALE_REFRESH_S", 3600)
SENSOR_SAMPLES = get_int("SENSOR_SAMPLES", 3)
# If the sample interval is shorter than this, leave LDO2/PMSA003I powered.
KEEP_SENSOR_ON_BELOW_S = get_int("KEEP_SENSOR_ON_BELOW_S", 30)
LOW_BATTERY_V = get_float("LOW_BATTERY_V", 3.2)
LOW_BATTERY_SLEEP_S = get_int("LOW_BATTERY_SLEEP_S", 3600)
