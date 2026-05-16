import unittest
from utils import clean_name

class TestCleanName(unittest.TestCase):
    def test_clean_name_with_punctuation(self):
        self.assertEqual(clean_name("Odell Beckham Jr."), "odellbeckhamjr")
        self.assertEqual(clean_name("Amon-Ra St. Brown"), "amonrastbrown")
        self.assertEqual(clean_name("Michael Pittman Jr."), "michaelpittmanjr")
        self.assertEqual(clean_name("DJ Chark"), "djchark")

    def test_clean_name_with_spaces(self):
        self.assertEqual(clean_name(" Jeremiyah  Love  "), "jeremiyahlove")

    def test_clean_name_with_numbers(self):
        self.assertEqual(clean_name("Marvin Harrison 123"), "marvinharrison")

    def test_clean_name_invalid_input(self):
        self.assertEqual(clean_name(None), "")
        self.assertEqual(clean_name(123), "")
        self.assertEqual(clean_name(123.45), "")

if __name__ == '__main__':
    unittest.main()
