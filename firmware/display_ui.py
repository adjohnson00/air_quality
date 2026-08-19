import board
import digitalio
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4

_CHAR_W = 5
_PAD = 6


class WingGrayscale4(Adafruit_SSD1680_Grayscale4):
    # RST is tied to Feather RESET, not a GPIO. Never deep-sleep the panel.
    def power_down(self):
        pass


def init_display():
    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D9)
    dc = digitalio.DigitalInOut(board.D10)
    display = WingGrayscale4(
        128,
        296,
        spi,
        cs_pin=cs,
        dc_pin=dc,
        sramcs_pin=None,
        rst_pin=None,
        busy_pin=None,
        vcom=0x24,
    )
    display.rotation = 3
    return display


def _text_width(text, size):
    return len(text) * _CHAR_W * size


def _age_label(age_s):
    if age_s is None:
        return ""
    if age_s < 90:
        return "now"
    if age_s < 3600:
        return "{}m ago".format(int(age_s / 60))
    return "{}h ago".format(int(age_s / 3600))


def _draw_aqi_bar(display, aqi_value, y, height):
    width = display.width
    display.rect(0, y, width, height, Adafruit_EPD.BLACK)
    inner_w = width - 2
    inner_h = height - 2
    # Four equal bands: good / moderate / usg / unhealthy+
    bands = (
        Adafruit_EPD.WHITE,
        Adafruit_EPD.LIGHT,
        Adafruit_EPD.DARK,
        Adafruit_EPD.BLACK,
    )
    seg = inner_w // 4
    for i, color in enumerate(bands):
        x = 1 + i * seg
        w = seg if i < 3 else inner_w - 3 * seg
        display.fill_rect(x, y + 1, w, inner_h, color)
        if i > 0:
            display.vline(x, y, height, Adafruit_EPD.BLACK)
    if aqi_value is None:
        return
    clamped = aqi_value
    if clamped < 0:
        clamped = 0
    if clamped > 200:
        clamped = 200
    marker_x = 1 + int(inner_w * clamped / 200)
    if marker_x < 2:
        marker_x = 2
    if marker_x > width - 3:
        marker_x = width - 3
    display.fill_rect(marker_x - 1, y, 3, height, Adafruit_EPD.BLACK)


def draw_card(display, state):
    """Page 0: AQI card. Page 1: particle bins."""
    display.fill(Adafruit_EPD.WHITE)
    page = state.get("page", 0)
    if page == 1:
        _draw_bins(display, state)
    else:
        _draw_aqi(display, state)


def _draw_aqi(display, state):
    width = display.width
    stale = state.get("stale", False)
    aqi_value = state.get("aqi")
    short = state.get("short") or "--"
    if stale and aqi_value is None:
        display.text("NO DATA", _PAD, 8, Adafruit_EPD.BLACK, size=3)
        display.text("sensor failed", _PAD, 48, Adafruit_EPD.DARK, size=2)
        return

    aqi_text = "--" if aqi_value is None else str(int(aqi_value))
    display.text(aqi_text, _PAD, 4, Adafruit_EPD.BLACK, size=4)
    cat_x = _PAD + _text_width(aqi_text, 4) + 10
    max_cat = width - cat_x - _PAD
    cat_size = 2
    if _text_width(short, cat_size) > max_cat:
        cat_size = 1
    display.text(short, cat_x, 12, Adafruit_EPD.DARK, size=cat_size)

    _draw_aqi_bar(display, aqi_value, 42, 18)

    display.text(_pm_line(state), _PAD, 72, Adafruit_EPD.BLACK, size=1)
    display.text(_status_line(state), _PAD, 108, Adafruit_EPD.DARK, size=1)


def _draw_bins(display, state):
    display.text("PARTICLES / 0.1L", _PAD, 4, Adafruit_EPD.BLACK, size=2)
    bins = (
        ("0.3um", "particles 03um"),
        ("0.5um", "particles 05um"),
        ("1.0um", "particles 10um"),
        ("2.5um", "particles 25um"),
        ("5.0um", "particles 50um"),
        ("10um", "particles 100um"),
    )
    y = 28
    for label, key in bins:
        value = state.get(key)
        text = "{}  {}".format(label, "--" if value is None else value)
        display.text(text, _PAD, y, Adafruit_EPD.BLACK, size=1)
        y += 12
    display.text(_pm_line(state), _PAD, 96, Adafruit_EPD.DARK, size=1)
    display.text(_status_line(state), _PAD, 112, Adafruit_EPD.DARK, size=1)


def _fmt_pm(value):
    if value is None:
        return "--"
    return "{:g}".format(value)


def _pm_line(state):
    return "PM1.0 {}  PM2.5 {}  PM10 {} ug/m3".format(
        _fmt_pm(state.get("pm1")),
        _fmt_pm(state.get("pm25")),
        _fmt_pm(state.get("pm10")),
    )


def _status_line(state):
    bits = []
    pct = state.get("percent")
    voltage = state.get("voltage")
    if pct is not None:
        bits.append("{}%".format(int(round(pct))))
    if voltage is not None and voltage >= 0.1:
        bits.append("{:.2f}V".format(voltage))
    if state.get("usb"):
        bits.append("USB")
    age = _age_label(state.get("age_s"))
    if age:
        bits.append(age)
    if state.get("stale"):
        bits.append("STALE")
    return "  ".join(bits)


def refresh(display):
    display.display()
