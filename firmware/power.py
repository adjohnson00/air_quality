import time

import alarm
import board


def disable_rf():
    """Keep Wi-Fi and Bluetooth off. We never connect; this powers the radios down."""
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
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds)
    pin_a = alarm.pin.PinAlarm(pin=board.D11, value=False, pull=True)
    pin_b = alarm.pin.PinAlarm(pin=board.D12, value=False, pull=True)
    return (time_alarm, pin_a, pin_b)


def deep_sleep(seconds):
    """Lowest power. Restarts code.py on wake. RAM is lost except persist file."""
    disable_rf()
    alarm.exit_and_deep_sleep_until_alarms(*_interval_alarms(seconds))


def light_sleep(seconds):
    """CPU paused, RAM kept, execution continues after return. More current than deep."""
    disable_rf()
    alarm.light_sleep_until_alarms(*_interval_alarms(seconds))


def sleep_interval(seconds, deep):
    if deep:
        print("Deep sleep {}s".format(seconds))
        deep_sleep(seconds)
        return
    print("Light sleep {}s".format(seconds))
    light_sleep(seconds)


def halt_until_usb(seconds):
    """Deep sleep until USB is plugged in, button A, or a long recheck timer.

    The FeatherS3[D] cannot software-latch the 3.3 V EN pin; deep sleep is the
    lowest power state firmware can enter. The e-ink image stays.
    """
    if seconds < 1:
        seconds = 1
    disable_rf()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds)
    pin_a = alarm.pin.PinAlarm(pin=board.D11, value=False, pull=True)
    pin_usb = alarm.pin.PinAlarm(pin=board.VBUS, value=True, pull=False)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm, pin_a, pin_usb)
