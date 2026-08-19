import json

_PATH = "/last.json"
_cache = None


def _fs_writable():
    try:
        import storage

        return not storage.getmount("/").readonly
    except Exception:
        return False


def load():
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(_PATH, "r") as handle:
            _cache = json.load(handle)
            return _cache
    except (OSError, ValueError):
        return None


def save(data):
    global _cache
    _cache = data
    if not _fs_writable():
        return
    try:
        with open(_PATH, "w") as handle:
            json.dump(data, handle)
    except OSError:
        pass
