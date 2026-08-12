import json

_PATH = "/last.json"


def load():
    try:
        with open(_PATH, "r") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def save(data):
    try:
        with open(_PATH, "w") as handle:
            json.dump(data, handle)
    except OSError as exc:
        print("persist save failed:", exc)
