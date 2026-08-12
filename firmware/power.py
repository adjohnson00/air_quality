import time

import alarm
import board


def wake_reason():
    """How we came out of deep sleep: 'timer', 'a', 'b', or 'boot'."""
    wake = alarm.wake_alarm
    if wake is None:
        return "boot"
    if isinstance(wake, alarm.pin.PinAlarm):
        if wake.pin == board.D11:
            return "a"
        if wake.pin == board.D12:
            return "b"
        return "a"
    return "timer"


def deep_sleep(seconds):
    """Sleep until the interval elapses or button A/B is pressed."""
    if seconds < 1:
        seconds = 1
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds)
    pin_a = alarm.pin.PinAlarm(pin=board.D11, value=False, pull=True)
    pin_b = alarm.pin.PinAlarm(pin=board.D12, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm, pin_a, pin_b)
