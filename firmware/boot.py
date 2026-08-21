# Runs before code.py. Radios stay off; this project is local-only.
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
