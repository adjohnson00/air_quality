import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware"))

import aqi  # noqa: E402


class TestAqi(unittest.TestCase):
    def test_truncate_does_not_round(self):
        self.assertEqual(aqi.truncate_pm25(9.19), 9.1)
        self.assertEqual(aqi.truncate_pm25(9.09), 9.0)
        self.assertEqual(aqi.truncate_pm25(-1), 0.0)

    def test_good_band(self):
        r = aqi.from_pm25(0)
        self.assertEqual(r["aqi"], 0)
        self.assertEqual(r["short"], "GOOD")
        self.assertEqual(aqi.from_pm25(9.0)["aqi"], 50)
        self.assertEqual(aqi.from_pm25(9.0)["short"], "GOOD")

    def test_moderate_starts_at_9_1(self):
        r = aqi.from_pm25(9.1)
        self.assertEqual(r["aqi"], 51)
        self.assertEqual(r["short"], "MODERATE")

    def test_usg_and_unhealthy(self):
        self.assertEqual(aqi.from_pm25(35.5)["short"], "USG")
        self.assertEqual(aqi.from_pm25(35.5)["aqi"], 101)
        self.assertEqual(aqi.from_pm25(55.5)["short"], "UNHEALTHY")
        self.assertEqual(aqi.from_pm25(55.5)["aqi"], 151)

    def test_very_unhealthy_and_hazardous(self):
        self.assertEqual(aqi.from_pm25(125.5)["short"], "V. UNHEALTHY")
        self.assertEqual(aqi.from_pm25(225.5)["short"], "HAZARDOUS")
        self.assertEqual(aqi.from_pm25(325.4)["aqi"], 500)
        self.assertEqual(aqi.from_pm25(400)["aqi"], 500)
        self.assertEqual(aqi.from_pm25(400)["short"], "HAZARDOUS")

    def test_interpolation_mid_moderate(self):
        # C=22.2 is near the middle of 9.1–35.4 → AQI ~75–76
        r = aqi.from_pm25(22.25)
        self.assertEqual(r["short"], "MODERATE")
        self.assertGreaterEqual(r["aqi"], 74)
        self.assertLessEqual(r["aqi"], 77)

    def test_known_12_ug(self):
        # (100-51)/(35.4-9.1)*(12.0-9.1)+51 = 56.399 → 56
        self.assertEqual(aqi.from_pm25(12.0)["aqi"], 56)


if __name__ == "__main__":
    unittest.main()
