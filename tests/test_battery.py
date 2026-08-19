import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware"))

import battery  # noqa: E402


class TestBatteryInterpret(unittest.TestCase):
    def test_usb_runaway_soc_is_not_a_pack(self):
        present, pct, volts = battery.interpret(4.3, 117.0, True)
        self.assertFalse(present)
        self.assertIsNone(pct)
        self.assertIsNone(volts)

    def test_usb_runaway_at_nominal_voltage(self):
        present, pct, volts = battery.interpret(4.08, 141.0, True)
        self.assertFalse(present)
        self.assertIsNone(pct)

    def test_full_pack_on_usb(self):
        present, pct, volts = battery.interpret(4.18, 98.5, True)
        self.assertTrue(present)
        self.assertEqual(pct, 98.5)
        self.assertEqual(volts, 4.18)

    def test_clamps_slightly_over_100(self):
        present, pct, volts = battery.interpret(4.20, 100.2, True)
        self.assertTrue(present)
        self.assertEqual(pct, 100.0)

    def test_no_cell_low_voltage(self):
        present, pct, volts = battery.interpret(0.2, 0.0, True)
        self.assertFalse(present)
        self.assertIsNone(pct)


if __name__ == "__main__":
    unittest.main()
