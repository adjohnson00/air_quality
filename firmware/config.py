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


SAMPLE_INTERVAL_S = get_int("SAMPLE_INTERVAL_S", 900)
USB_SAMPLE_INTERVAL_S = get_int("USB_SAMPLE_INTERVAL_S", 180)
SENSOR_WARMUP_S = get_int("SENSOR_WARMUP_S", 15)
PM25_REFRESH_DELTA = get_int("PM25_REFRESH_DELTA", 2)
MAX_STALE_REFRESH_S = get_int("MAX_STALE_REFRESH_S", 3600)
SENSOR_SAMPLES = get_int("SENSOR_SAMPLES", 3)
