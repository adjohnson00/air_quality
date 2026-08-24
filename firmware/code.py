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
import vlog

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


def _release_pins(pins):
    for pin in pins:
        try:
            pin.deinit()
        except Exception:
            pass


def _pack(reading, bat, usb, page, stale, sampled_at):
    state = {
        "page": page,
        "stale": stale,
        "usb": usb,
        "sampled_at": sampled_at,
        "percent": bat.get("percent") if bat else None,
        "voltage": bat.get("voltage") if bat else None,
        "present": bat.get("present") if bat else False,
        "charge_rate": bat.get("charge_rate") if bat else None,
        "charge_label": bat.get("charge_label") if bat else None,
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
        for _label, key in aqi.PARTICLE_BINS:
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
        bool(state.get("low_batt")),
        bool(state.get("usb")),
        state.get("aqi"),
        state.get("short"),
        _rounded(state.get("pm1")),
        _rounded(state.get("pm25")),
        _rounded(state.get("pm10")),
        _rounded(state.get("percent")),
        state.get("charge_label"),
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


def _sample_interval(usb):
    if usb:
        return config.USB_SAMPLE_INTERVAL_S
    return config.SAMPLE_INTERVAL_S


def _keep_sensor_on(usb):
    return config.keep_sensor_powered(_sample_interval(usb))


def _sample(sensor, usb, page):
    stay_on = _keep_sensor_on(usb)
    print("Sampling PM sensor (LDO2 {} between reads)...".format("stays on" if stay_on else "off"))
    reading = sensor.read(
        config.SENSOR_WARMUP_S, config.SENSOR_SAMPLES, stay_on=stay_on
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
        saved["charge_rate"] = bat.get("charge_rate")
        saved["charge_label"] = bat.get("charge_label")
        saved["age_s"] = None if saved.get("sampled_at") is None else now - saved["sampled_at"]
        vlog.append(saved, _sample_interval(usb))
        return saved
    state = _pack(reading, bat, usb, page, False, now)
    print(
        "PM1.0={} PM2.5={} PM10={} ug/m3 AQI={} {} bat={} V={}{}".format(
            state.get("pm1"),
            state.get("pm25"),
            state.get("pm10"),
            state.get("aqi"),
            state.get("short"),
            state.get("percent"),
            state.get("voltage"),
            (" " + state["charge_label"]) if state.get("charge_label") else "",
        )
    )
    vlog.append(state, _sample_interval(usb))
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


def _battery_is_low(bat):
    voltage = bat.get("voltage")
    if voltage is None:
        return False
    return voltage <= config.LOW_BATTERY_V


def _halt_low_battery(display, sensor, saved, bat, reason):
    if battery.usb_connected():
        print("USB in, skip halt")
        return
    sensor.release()
    ldo = power.claim_ldo2_off()
    state = saved if saved else {}
    state["low_batt"] = True
    state["usb"] = False
    state["present"] = True
    state["voltage"] = bat.get("voltage")
    state["percent"] = bat.get("percent")
    print(
        "Low battery {:.2f} V (wake {}) — showing halt card".format(
            bat.get("voltage") or 0, reason
        )
    )
    _show(display, state, None, True, _now())
    vlog.append(state, _sample_interval(False))
    power.halt_until_usb(config.LOW_BATTERY_SLEEP_S, ldo_pin=ldo)


def _sleep_between_samples(sensor, buttons, seconds):
    """deep/light: LDO2 off, sleep until timer, A, B, or USB plug."""
    _release_pins(buttons or ())
    sensor.power_off()
    hold = (sensor.ldo_pin(),) if config.use_deep_sleep() else None
    power.sleep_interval(
        seconds,
        config.use_deep_sleep(),
        preserve_dios=hold,
    )


def run(display, sensor):
    """Single loop. Polls VBUS. SLEEP_MODE applies on USB and battery."""
    reason = power.wake_reason()
    saved = persist.load() or {"page": 0}
    page = saved.get("page", 0)
    if reason == "timer" and saved.get("present"):
        battery.mark_present()

    usb = battery.usb_connected()
    if saved.get("low_batt") and usb:
        print("USB resume — clearing LOW BATT")
        saved["low_batt"] = False
        saved["usb"] = True
        _show(display, saved, None, True, _now())

    buttons = []
    last_refresh_mono = -_MIN_EINK_S
    next_due = time.monotonic()
    last_usb = usb
    print(
        "Run usb={} sleep={} sample {}s".format(
            usb, config.SLEEP_MODE, _sample_interval(usb)
        )
    )

    if reason == "b" and not config.cpu_always_on():
        page = 1 - page
        saved["page"] = page
        saved["usb"] = usb
        print("Button B: page", page)
        _show(display, saved, None, True, _now())
        _sleep_between_samples(sensor, buttons, _sample_interval(usb))
        if config.use_deep_sleep():
            return
        next_due = time.monotonic()
        reason = "timer"

    while True:
        usb = battery.usb_connected()
        stay_awake = config.cpu_always_on()
        interval = _sample_interval(usb)
        now_mono = time.monotonic()

        if usb != last_usb:
            print("USB connected" if usb else "USB disconnected")
            saved["usb"] = usb
            last_usb = usb
            _show(display, saved, None, True, _now())
            last_refresh_mono = time.monotonic()
            next_due = time.monotonic()
            interval = _sample_interval(usb)

        if stay_awake and not buttons:
            buttons = _buttons()

        force = False
        flip = False
        if buttons:
            if _pressed(buttons[0]):
                force = True
                while _pressed(buttons[0]):
                    time.sleep(0.05)
            if _pressed(buttons[1]):
                flip = True
                while _pressed(buttons[1]):
                    time.sleep(0.05)

        due = now_mono >= next_due
        if flip:
            page = 1 - page
            saved["page"] = page
            saved["usb"] = usb
            print("Button B: page", page)
            _show(display, saved, None, True, _now())
            last_refresh_mono = time.monotonic()
        elif force or due:
            previous = saved
            saved = _sample(sensor, usb, page)
            saved["page"] = page
            if (not usb) and _battery_is_low(
                {"voltage": saved.get("voltage"), "percent": saved.get("percent")}
            ):
                _release_pins(buttons)
                _halt_low_battery(display, sensor, saved, saved, reason)
                return
            can_refresh = force or (now_mono - last_refresh_mono) >= _MIN_EINK_S
            if can_refresh:
                old_refresh = previous.get("refreshed_at")
                saved = _show(display, saved, previous, force, _now())
                if saved.get("refreshed_at") != old_refresh:
                    last_refresh_mono = time.monotonic()
            else:
                persist.save(saved)
            finished = time.monotonic()
            if stay_awake:
                if due:
                    next_due += interval
                    while next_due <= finished:
                        next_due += interval
                else:
                    next_due = finished + interval
            else:
                _sleep_between_samples(sensor, buttons, interval)
                buttons = []
                if config.use_deep_sleep():
                    return
                next_due = time.monotonic()
                reason = "timer"
        elif stay_awake:
            time.sleep(0.1)


def main():
    usb = battery.usb_connected()
    reason = power.wake_reason()
    print("USB connected:" if usb else "On battery:", usb)
    print("Sleep mode:", config.SLEEP_MODE)
    if config.VOLTAGE_LOG:
        if reason == "boot":
            vlog.begin_session()
        else:
            vlog.continue_session(_sample_interval(usb))
    display = display_ui.init_display()
    if not usb:
        bat = battery.read()
        saved = persist.load() or {"page": 0}
        if _battery_is_low(bat):
            sensor = sensor_mod.Sensor(start_on=False)
            _halt_low_battery(display, sensor, saved, bat, reason)
            return
    sensor = sensor_mod.Sensor(start_on=True)
    run(display, sensor)


main()
