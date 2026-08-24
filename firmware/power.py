import time

import alarm
import board
import digitalio
import config


def disable_rf():
    """Radios off. boot.py does this at reset; call again before sleep (light sleep does not re-run boot.py)."""
    try:
        import wifi

        wifi.radio.enabled = False
    except Exception:
        pass
    try:
        import _bleio

        _bleio.adapter.enabled = False
    except Exception:
        pass


def wake_reason():
    """How we came out of deep sleep: 'timer', 'a', 'b', or 'boot'."""
    wake = alarm.wake_alarm
    if wake is None:
        return "boot"
    if isinstance(wake, alarm.pin.PinAlarm):
        if wake.pin == board.VBUS:
            return "usb"
        if wake.pin == board.D11:
            return "a"
        if wake.pin == board.D12:
            return "b"
        return "a"
    return "timer"


def _interval_alarms(seconds):
    if seconds < 1:
        seconds = 1
    alarms = [
        alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds),
        alarm.pin.PinAlarm(pin=board.D11, value=False, pull=True),
        alarm.pin.PinAlarm(pin=board.D12, value=False, pull=True),
    ]
    try:
        alarms.append(alarm.pin.PinAlarm(pin=board.VBUS, value=True, pull=False))
    except Exception:
        pass
    return tuple(alarms)


def _enter_deep_sleep(alarms, preserve_dios):
    disable_rf()
    dios = preserve_dios if preserve_dios else ()
    try:
        alarm.exit_and_deep_sleep_until_alarms(*alarms, preserve_dios=dios)
    except TypeError:
        alarm.exit_and_deep_sleep_until_alarms(*alarms)


def claim_ldo2_off(existing=None):
    """Own LDO2 as a driven-low output. Returns the pin for preserve_dios."""
    if existing is not None:
        try:
            existing.value = False
            print("LDO2 off (existing pin)")
            return existing
        except Exception:
            try:
                existing.deinit()
            except Exception:
                pass
    pin = digitalio.DigitalInOut(board.LDO2)
    pin.switch_to_output(value=False)
    print("LDO2 off (claimed)")
    return pin


def deep_sleep(seconds, preserve_dios=None):
    """Lowest power. Restarts code.py on wake. RAM is lost except persist file."""
    _enter_deep_sleep(_interval_alarms(seconds), preserve_dios)


def light_sleep(seconds):
    """CPU paused, RAM kept, execution continues after return. More current than deep."""
    disable_rf()
    alarm.light_sleep_until_alarms(*_interval_alarms(seconds))


def sleep_interval(seconds, deep=None, preserve_dios=None):
    if config.cpu_always_on():
        return
    if deep is None:
        deep = config.use_deep_sleep()
    if deep:
        print("Deep sleep {}s".format(seconds))
        deep_sleep(seconds, preserve_dios=preserve_dios)
        return
    print("Light sleep {}s".format(seconds))
    light_sleep(seconds)


def halt_until_usb(seconds, ldo_pin=None):
    """Deep sleep until USB is plugged in, button A, or a long recheck timer.

    Halt is always deep sleep (even if SLEEP_MODE is light). LDO2 must be a
    driven-low output passed as preserve_dios or the pad resets and the
    Plantower comes back on.
    """
    if seconds < 1:
        seconds = 1
    ldo_pin = claim_ldo2_off(ldo_pin)
    try:
        import supervisor

        print("Halt usb_connected", supervisor.runtime.usb_connected)
    except Exception:
        pass
    print("Halt sleep {}s (wake USB or A) LDO2={}".format(seconds, ldo_pin.value))
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds)
    alarms = [time_alarm]
    try:
        alarms.append(alarm.pin.PinAlarm(pin=board.D11, value=False, pull=True))
    except Exception as exc:
        print("Halt A alarm skipped:", exc)
    try:
        alarms.append(alarm.pin.PinAlarm(pin=board.VBUS, value=True, pull=False))
    except Exception as exc:
        print("Halt VBUS alarm skipped:", exc)
    try:
        _enter_deep_sleep(tuple(alarms), (ldo_pin,))
    except Exception as exc:
        print("Halt deep sleep failed:", exc)
        # Do not return with the fan on. Idle here with LDO2 held off.
        while True:
            ldo_pin.value = False
            time.sleep(10)
