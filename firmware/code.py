import time

import board
import digitalio

import aqi
import battery
import config
import display_ui
import persist
import power
import sensor as sensor_mod

_MIN_EINK_S = 30


def _now():
    try:
        return time.time()
    except Exception:
        return int(time.monotonic())


def _buttons():
    pins = []
    for name in (board.D11, board.D12):
        pin = digitalio.DigitalInOut(name)
        pin.switch_to_input(pull=digitalio.Pull.UP)
        pins.append(pin)
    return pins


def _pressed(pin):
    return not pin.value


def _pack(reading, bat, usb, page, stale, sampled_at):
    state = {
        "page": page,
        "stale": stale,
        "usb": usb,
        "sampled_at": sampled_at,
        "percent": bat.get("percent") if bat else None,
        "voltage": bat.get("voltage") if bat else None,
        "present": bat.get("present") if bat else False,
        "aqi": None,
        "short": None,
        "category": None,
        "pm25": None,
        "pm10": None,
        "pm1": None,
    }
    if reading:
        pm25 = reading.get("pm25 env")
        converted = aqi.from_pm25(pm25)
        state.update(converted)
        state["pm10"] = reading.get("pm100 env")
        state["pm1"] = reading.get("pm10 env")
        for key in (
            "particles 03um",
            "particles 05um",
            "particles 10um",
            "particles 25um",
            "particles 50um",
            "particles 100um",
        ):
            state[key] = reading.get(key)
    return state


def _rounded(value):
    if value is None:
        return None
    return int(round(float(value)))


def _card_key(state):
    """Visible eInk fields; ignore age so a stable reading does not flash the panel."""
    return (
        state.get("page", 0),
        state.get("aqi"),
        state.get("short"),
        _rounded(state.get("pm1")),
        _rounded(state.get("pm25")),
        _rounded(state.get("pm10")),
        _rounded(state.get("percent")),
        bool(state.get("stale")),
    )


def _should_refresh(previous, current, force, now):
    if force:
        return True
    if previous is None or previous.get("refreshed_at") is None:
        return True
    if _card_key(previous) != _card_key(current):
        return True
    return (now - previous.get("refreshed_at", now)) >= config.MAX_STALE_REFRESH_S


def _sample(sensor, usb, page):
    print("Sampling PM sensor...")
    reading = sensor.read(
        config.SENSOR_WARMUP_S, config.SENSOR_SAMPLES, stay_on=usb
    )
    bat = battery.read()
    now = _now()
    stale = reading is None
    if stale:
        print("No sensor reading")
        saved = persist.load() or {}
        saved["stale"] = True
        saved["usb"] = usb
        saved["page"] = page
        saved["percent"] = bat.get("percent")
        saved["voltage"] = bat.get("voltage")
        saved["present"] = bat.get("present")
        saved["age_s"] = None if saved.get("sampled_at") is None else now - saved["sampled_at"]
        return saved
    state = _pack(reading, bat, usb, page, False, now)
    print(
        "PM1.0={} PM2.5={} PM10={} ug/m3 AQI={} {} bat={} V={}".format(
            state.get("pm1"),
            state.get("pm25"),
            state.get("pm10"),
            state.get("aqi"),
            state.get("short"),
            state.get("percent"),
            state.get("voltage"),
        )
    )
    return state


def _show(display, state, previous, force, now):
    if state.get("sampled_at") is not None:
        state["age_s"] = now - state["sampled_at"]
    if not _should_refresh(previous, state, force, now):
        print("Skip eInk refresh")
        persist.save(state)
        return state
    print("Refreshing eInk...")
    display_ui.draw_card(display, state)
    display_ui.refresh(display)
    state["refreshed_at"] = now
    persist.save(state)
    return state


def run_usb(display, sensor):
    saved = persist.load() or {"page": 0}
    page = saved.get("page", 0)
    buttons = _buttons()
    last_sample = 0
    last_refresh_mono = -_MIN_EINK_S
    print("USB mode, sample every {}s".format(config.USB_SAMPLE_INTERVAL_S))
    while True:
        now_mono = time.monotonic()
        force = False
        flip = False
        if _pressed(buttons[0]):
            force = True
            while _pressed(buttons[0]):
                time.sleep(0.05)
        if _pressed(buttons[1]):
            flip = True
            while _pressed(buttons[1]):
                time.sleep(0.05)
        due = (now_mono - last_sample) >= config.USB_SAMPLE_INTERVAL_S
        if flip:
            page = 1 - page
            saved["page"] = page
            saved["usb"] = True
            if (now_mono - last_refresh_mono) >= _MIN_EINK_S:
                _show(display, saved, None, True, _now())
                last_refresh_mono = time.monotonic()
            else:
                persist.save(saved)
        elif force or due:
            previous = saved
            saved = _sample(sensor, True, page)
            saved["page"] = page
            can_refresh = force or (now_mono - last_refresh_mono) >= _MIN_EINK_S
            if can_refresh:
                old_refresh = previous.get("refreshed_at")
                saved = _show(display, saved, previous, force, _now())
                if saved.get("refreshed_at") != old_refresh:
                    last_refresh_mono = time.monotonic()
            else:
                persist.save(saved)
            last_sample = time.monotonic()
        time.sleep(0.1)


def run_battery(display, sensor):
    reason = power.wake_reason()
    print("Battery wake:", reason)
    saved = persist.load() or {"page": 0}
    page = saved.get("page", 0)
    force = reason in ("a", "boot")
    if reason == "b":
        page = 1 - page
        saved["page"] = page
        saved["usb"] = False
        _show(display, saved, None, True, _now())
    else:
        saved = _sample(sensor, False, page)
        saved["page"] = page
        _show(display, saved, persist.load(), force, _now())
    print("Deep sleep {}s".format(config.SAMPLE_INTERVAL_S))
    power.deep_sleep(config.SAMPLE_INTERVAL_S)


def main():
    usb = battery.usb_connected()
    print("USB connected:" if usb else "On battery:", usb)
    display = display_ui.init_display()
    sensor = sensor_mod.Sensor()
    if usb:
        run_usb(display, sensor)
    else:
        run_battery(display, sensor)


main()
