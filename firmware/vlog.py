import json
import os
import time

import aqi

HEADER = (
    "elapsed_s,voltage,percent,usb,pm1,pm25,pm10,"
    "bin03,bin05,bin10,bin25,bin50,bin100"
)
_DIR_NAME = "data"
_META_NAME = "vlog.json"

_root = ""
_meta = None
# High-res origin for this process. time.time() on the S3 without a 32 kHz
# crystal steps in ~64 s, which stacked many samples on one CSV timestamp.
_t0_mono = None


def set_root(path):
    """Host tests: write under a temp directory instead of CIRCUITPY /."""
    global _root
    _root = (path or "").rstrip("/")


def reset():
    """Drop in-memory session (tests)."""
    global _meta, _t0_mono
    _meta = None
    _t0_mono = None


def _log_dir():
    if _root:
        return _root + "/" + _DIR_NAME
    return "/" + _DIR_NAME


def _abspath(name):
    return _log_dir() + "/" + name


def _listdir():
    try:
        return os.listdir(_log_dir())
    except OSError:
        return []


def _readonly():
    if _root:
        return False
    try:
        import storage

        return bool(storage.getmount("/").readonly)
    except Exception:
        return None


def _enabled():
    try:
        import config

        return config.VOLTAGE_LOG != 0
    except Exception:
        return True


def _ensure_dir():
    path = _log_dir()
    try:
        os.mkdir(path)
        print("vlog mkdir", path)
    except OSError:
        pass
    return path


def _write_text(path, text, mode):
    """Create/append and flush so the file survives reset/deep sleep."""
    handle = open(path, mode)
    try:
        handle.write(text)
        handle.flush()
        try:
            os.sync()
        except AttributeError:
            pass
    finally:
        handle.close()


def next_volt_name(names):
    best = 0
    for name in names:
        if not name.startswith("volt") or not name.endswith(".csv"):
            continue
        mid = name[4:-4]
        if mid.isdigit():
            n = int(mid)
            if n > best:
                best = n
    return "volt{}.csv".format(best + 1)


def compute_elapsed(now, t0, last_elapsed, interval_s):
    if t0 is None:
        return 0
    try:
        now = float(now)
        t0 = float(t0)
    except (TypeError, ValueError):
        return int(last_elapsed or 0) + int(interval_s or 0)
    if now < t0:
        return int(last_elapsed or 0) + int(interval_s or 0)
    return int(now - t0)


def _cell(value, kind):
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if kind == "v":
        return "{:.2f}".format(number)
    if kind == "pct":
        return "{}".format(int(round(number)))
    if kind == "n":
        return "{}".format(int(round(number)))
    return "{:g}".format(number)


def format_row(elapsed_s, state):
    present = bool(state.get("present"))
    voltage = state.get("voltage")
    percent = state.get("percent") if present else None
    usb = 1 if state.get("usb") else 0
    # USB with no cell still has a charger-node voltage; do not log that.
    if (not present) and usb and not state.get("low_batt"):
        voltage = None
    failed = bool(state.get("stale"))
    pm1 = None if failed else state.get("pm1")
    pm25 = None if failed else state.get("pm25")
    pm10 = None if failed else state.get("pm10")
    bins = []
    for _label, key in aqi.PARTICLE_BINS:
        bins.append(None if failed else state.get(key))
    cells = [
        str(int(elapsed_s)),
        _cell(voltage, "v"),
        _cell(percent, "pct"),
        str(usb),
        _cell(pm1, "pm"),
        _cell(pm25, "pm"),
        _cell(pm10, "pm"),
    ]
    for value in bins:
        cells.append(_cell(value, "n"))
    return ",".join(cells)


def _load_meta():
    global _meta
    if _meta is not None:
        return _meta
    try:
        with open(_abspath(_META_NAME), "r") as handle:
            _meta = json.load(handle)
            return _meta
    except (OSError, ValueError):
        _meta = None
        return None


def _save_meta():
    if _meta is None:
        return
    try:
        _write_text(_abspath(_META_NAME), json.dumps(_meta), "w")
    except OSError as exc:
        print("vlog meta save failed:", exc)


def begin_session():
    global _meta, _t0_mono
    if not _enabled():
        print("vlog disabled (VOLTAGE_LOG=0)")
        _meta = None
        _t0_mono = None
        return
    _ensure_dir()
    name = next_volt_name(_listdir())
    _t0_mono = None
    _meta = {"path": name, "t0": None, "last_elapsed": 0}
    dest = _abspath(name)
    print("vlog session", dest, "readonly=", _readonly())
    try:
        _write_text(dest, HEADER + "\n", "w")
        print("vlog created", dest)
    except OSError as exc:
        print("vlog create failed:", dest, exc)
        print("vlog hint: hold A on reset to copy firmware; reboot without A to log")
    _save_meta()


def continue_session(interval_s=60):
    global _meta, _t0_mono
    if not _enabled():
        _meta = None
        return
    _ensure_dir()
    meta = _load_meta()
    if not meta or not meta.get("path"):
        begin_session()
        return
    if meta["path"] not in _listdir():
        print("vlog missing", meta["path"], "— new file")
        begin_session()
        return
    last = int(meta.get("last_elapsed") or 0)
    _t0_mono = time.monotonic() - last - interval_s
    print("vlog continue", _abspath(meta["path"]), "readonly=", _readonly())


def _elapsed(now, interval_s):
    """Seconds since first sample. Prefer monotonic; `now` is a test clock."""
    global _t0_mono
    if now is not None:
        if _meta.get("t0") is None:
            _meta["t0"] = now
            return 0
        return compute_elapsed(
            now, _meta.get("t0"), _meta.get("last_elapsed"), interval_s
        )
    mono = time.monotonic()
    if _t0_mono is None:
        last = int(_meta.get("last_elapsed") or 0)
        _t0_mono = mono - last
        return last
    elapsed = int(mono - _t0_mono)
    if elapsed < 0:
        elapsed = int(_meta.get("last_elapsed") or 0) + int(interval_s or 0)
        _t0_mono = mono - elapsed
    return elapsed


def append(state, interval_s=60, now=None):
    global _meta
    if not _enabled():
        return
    if _meta is None:
        _load_meta()
    if _meta is None:
        begin_session()
    elapsed = _elapsed(now, interval_s)
    line = format_row(elapsed, state or {})
    print("vlog", line)
    path = _meta.get("path")
    if path:
        dest = _abspath(path)
        try:
            _write_text(dest, line + "\n", "a")
        except OSError as exc:
            print("vlog write failed:", dest, exc)
    _meta["last_elapsed"] = elapsed
    _save_meta()
