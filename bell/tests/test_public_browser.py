import unittest

from verify_public_browser import localized_ratio_present


class LocalizedRatioTest(unittest.TestCase):
    def test_narrow_ratio_accepts_browser_decimal_separator(self):
        self.assertTrue(localized_ratio_present("1.00195×", "1.00195×"))
        self.assertTrue(localized_ratio_present("1,00195×", "1.00195×"))
        self.assertFalse(localized_ratio_present("1×", "1.00195×"))


if __name__ == "__main__":
    unittest.main()
