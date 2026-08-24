import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware"))

import config  # noqa: E402
import vlog  # noqa: E402


class TestNextVoltName(unittest.TestCase):
    def test_first_file(self):
        self.assertEqual(vlog.next_volt_name([]), "volt1.csv")
        self.assertEqual(vlog.next_volt_name(["last.json", "code.py"]), "volt1.csv")

    def test_increments_highest(self):
        names = ["volt1.csv", "volt2.csv", "volt10.csv", "volt.csv"]
        self.assertEqual(vlog.next_volt_name(names), "volt11.csv")


class TestElapsed(unittest.TestCase):
    def test_first_sample(self):
        self.assertEqual(vlog.compute_elapsed(100, None, 0, 60), 0)

    def test_rtc_continues(self):
        self.assertEqual(vlog.compute_elapsed(1161, 1000, 120, 60), 161)

    def test_rtc_reset_falls_back(self):
        self.assertEqual(vlog.compute_elapsed(5, 1000, 120, 60), 180)


class TestFormatRow(unittest.TestCase):
    def test_full_row(self):
        state = {
            "present": True,
            "voltage": 4.123,
            "percent": 96.6,
            "usb": False,
            "stale": False,
            "pm1": 3,
            "pm25": 5.0,
            "pm10": 7,
            "particles 03um": 812,
            "particles 05um": 240,
            "particles 10um": 48,
            "particles 25um": 6,
            "particles 50um": 1,
            "particles 100um": 0,
        }
        self.assertEqual(
            vlog.format_row(0, state),
            "0,4.12,97,0,3,5,7,812,240,48,6,1,0",
        )

    def test_usb_no_pack_blanks_voltage(self):
        line = vlog.format_row(
            10,
            {"present": False, "voltage": 4.2, "percent": 140, "usb": True},
        )
        self.assertEqual(line, "10,,,1,,,,,,,,,")

    def test_dying_pack_keeps_voltage(self):
        line = vlog.format_row(
            10,
            {"present": False, "voltage": 3.18, "percent": None, "usb": False},
        )
        self.assertTrue(line.startswith("10,3.18,"))

    def test_halt_keeps_zero_percent(self):
        line = vlog.format_row(
            99,
            {
                "present": True,
                "voltage": 3.18,
                "percent": 0.0,
                "usb": False,
                "low_batt": True,
            },
        )
        self.assertTrue(line.startswith("99,3.18,0,0"))

    def test_stale_blanks_pm_and_bins(self):
        line = vlog.format_row(
            60,
            {
                "present": True,
                "voltage": 3.9,
                "percent": 50,
                "usb": False,
                "stale": True,
                "pm1": 3,
                "pm25": 5,
                "pm10": 7,
                "particles 03um": 100,
            },
        )
        self.assertEqual(line, "60,3.90,50,0,,,,,,,,,")


class TestSleepHelpers(unittest.TestCase):
    def setUp(self):
        self.prev = config.SLEEP_MODE

    def tearDown(self):
        config.SLEEP_MODE = self.prev

    def test_no_is_awake_not_deep(self):
        config.SLEEP_MODE = "no"
        self.assertFalse(config.use_deep_sleep())
        self.assertTrue(config.cpu_always_on())
        self.assertFalse(config.sensor_always_on())
        self.assertFalse(config.keep_sensor_powered(60))
        self.assertTrue(config.keep_sensor_powered(15))

    def test_full_keeps_sensor_on(self):
        config.SLEEP_MODE = "full"
        self.assertFalse(config.use_deep_sleep())
        self.assertTrue(config.cpu_always_on())
        self.assertTrue(config.sensor_always_on())
        self.assertTrue(config.keep_sensor_powered(60))

    def test_light_not_deep(self):
        config.SLEEP_MODE = "light"
        self.assertFalse(config.use_deep_sleep())
        self.assertTrue(config.use_light_sleep())
        self.assertFalse(config.cpu_always_on())


class TestSessionFiles(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.mkdtemp()
        vlog.set_root(self.td)
        vlog.reset()

    def tearDown(self):
        vlog.reset()
        vlog.set_root("")
        shutil.rmtree(self.td, ignore_errors=True)

    def _data(self):
        return os.path.join(self.td, "data")

    def _read(self, name):
        with open(os.path.join(self._data(), name), "r") as handle:
            return handle.read()

    def test_boot_opens_new_file_and_leaves_old(self):
        vlog.begin_session()
        vlog.append(
            {
                "present": True,
                "voltage": 4.1,
                "percent": 90,
                "usb": False,
                "pm1": 1,
                "pm25": 2,
                "pm10": 3,
            },
            now=1000,
            interval_s=60,
        )
        vlog.reset()
        vlog.begin_session()
        names = sorted(n for n in os.listdir(self._data()) if n.startswith("volt"))
        self.assertEqual(names, ["volt1.csv", "volt2.csv"])
        self.assertIn("4.10,90,0,1,2,3", self._read("volt1.csv"))
        self.assertEqual(self._read("volt2.csv"), vlog.HEADER + "\n")

    def test_continue_appends_same_file(self):
        vlog.begin_session()
        vlog.append(
            {"present": True, "voltage": 4.1, "percent": 90, "usb": False},
            now=1000,
            interval_s=60,
        )
        vlog.reset()
        vlog.continue_session()
        vlog.append(
            {"present": True, "voltage": 4.0, "percent": 80, "usb": False},
            now=1060,
            interval_s=60,
        )
        names = [n for n in os.listdir(self._data()) if n.startswith("volt")]
        self.assertEqual(names, ["volt1.csv"])
        body = self._read("volt1.csv").strip().splitlines()
        self.assertEqual(body[0], vlog.HEADER)
        self.assertTrue(body[1].startswith("0,4.10,90,0"))
        self.assertTrue(body[2].startswith("60,4.00,80,0"))

    def test_production_clock_is_monotonic_not_injected(self):
        vlog.begin_session()
        state = {"present": True, "voltage": 4.0, "percent": 50, "usb": False}
        vlog.append(state, interval_s=60)
        time.sleep(1.1)
        vlog.append(state, interval_s=60)
        body = self._read("volt1.csv").strip().splitlines()
        first = int(body[1].split(",")[0])
        second = int(body[2].split(",")[0])
        self.assertEqual(first, 0)
        self.assertGreaterEqual(second, 1)

    def test_creates_data_directory(self):
        vlog.begin_session()
        self.assertTrue(os.path.isdir(self._data()))


if __name__ == "__main__":
    unittest.main()
