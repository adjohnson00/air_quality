# Runs before code.py. Radios stay off; this project is local-only.
#
# CIRCUITPY is host-writable (MCU cannot log) until we remount.
# Hold button A at reset to keep it that way so you can copy firmware.
# Otherwise remount writable so /data logs actually land on flash.
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

try:
    import board
    import digitalio
    import storage

    btn = digitalio.DigitalInOut(board.D11)
    btn.switch_to_input(pull=digitalio.Pull.UP)
    hold_a = not btn.value
    btn.deinit()
    if hold_a:
        print("boot: CIRCUITPY host-writable (A held) — logs will not write")
    else:
        storage.remount("/", readonly=False)
        print("boot: CIRCUITPY writable for /data logs")
except Exception as exc:
    print("boot remount skipped:", exc)
