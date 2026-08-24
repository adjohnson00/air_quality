# US EPA PM2.5 AQI, 2024 breakpoints (AirNow / Idaho DEQ).
# Instantaneous concentration, not 24-hour NowCast.

# Plantower cumulative >size counts per 0.1 L. Keys match adafruit_pm25.
PARTICLE_BINS = (
    (">0.3um", "particles 03um"),
    (">0.5um", "particles 05um"),
    (">1.0um", "particles 10um"),
    (">2.5um", "particles 25um"),
    (">5.0um", "particles 50um"),
    (">10um", "particles 100um"),
)

# (C_low, C_high, I_low, I_high, category, short label)
_BREAKPOINTS = (
    (0.0, 9.0, 0, 50, "Good", "GOOD"),
    (9.1, 35.4, 51, 100, "Moderate", "MODERATE"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "USG"),
    (55.5, 125.4, 151, 200, "Unhealthy", "UNHEALTHY"),
    (125.5, 225.4, 201, 300, "Very Unhealthy", "V. UNHEALTHY"),
    (225.5, 325.4, 301, 500, "Hazardous", "HAZARDOUS"),
)


def truncate_pm25(ug_m3):
    """EPA truncates PM2.5 to one decimal place (not round)."""
    if ug_m3 < 0:
        return 0.0
    return int(ug_m3 * 10) / 10.0


def from_pm25(ug_m3):
    """Return AQI fields for a PM2.5 concentration in µg/m³."""
    c = truncate_pm25(float(ug_m3))
    if c > 325.4:
        return {
            "pm25": c,
            "aqi": 500,
            "category": "Hazardous",
            "short": "HAZARDOUS",
        }
    for c_lo, c_hi, i_lo, i_hi, category, short in _BREAKPOINTS:
        if c_lo <= c <= c_hi:
            if c_hi == c_lo:
                aqi = i_hi
            else:
                aqi = ((i_hi - i_lo) / (c_hi - c_lo)) * (c - c_lo) + i_lo
                aqi = int(aqi + 0.5)
            return {
                "pm25": c,
                "aqi": aqi,
                "category": category,
                "short": short,
            }
    return {
        "pm25": c,
        "aqi": 0,
        "category": "Good",
        "short": "GOOD",
    }
