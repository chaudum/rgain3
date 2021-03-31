import unittest

from rgain3.lib import GainData, GainType


class TestGainData(unittest.TestCase):
    def test_str(self):
        self.assertEqual(
            str(GainData(-1.2)),
            "gain=-1.20 dB; peak=1.00000000; reference-level=89 dB"
        )
        self.assertEqual(
            str(GainData(-1.2, 0.6, 88, GainType.TP_ALBUM)),
            "gain=-1.20 dB; peak=0.60000000; reference-level=88 dB"
        )

    def test_repr(self):
        self.assertEqual(
            repr(GainData(-1.2)),
            "GainData(-1.2, 1.0, 89, GainType.TP_UNDEFINED)",
        )
        self.assertEqual(
            repr(GainData(-1.2, 0.6, 88, GainType.TP_ALBUM)),
            "GainData(-1.2, 0.6, 88, GainType.TP_ALBUM)",
        )

    def test_eq(self):
        gd1 = GainData(-5, 0.5, 80)
        gd2 = GainData(-5, 0.5, 80)
        self.assertTrue(gd1 == gd2)
        self.assertFalse(gd1 != gd2)

    def test_not_eq(self):
        gd1 = GainData(-5, 0.5, 80)
        gd2 = GainData(-5, 0.6, 80)
        self.assertTrue(gd1 != gd2)
        self.assertFalse(gd1 == gd2)

    def test_bad_type(self):
        gd1 = GainData(-5, 0.6, 89)
        gd2 = "not GainData"
        self.assertTrue(gd1 != gd2)
        self.assertFalse(gd1 == gd2)

    def test_eq_gain_type(self):
        gd1 = GainData(0, 0, 0, GainType.TP_TRACK)
        gd2 = GainData(0, 0, 0, GainType.TP_TRACK)
        gd3 = GainData(0, 0, 0, GainType.TP_ALBUM)
        gd4 = GainData(0, 0, 0)
        self.assertEqual(gd1, gd2)
        self.assertNotEqual(gd1, gd3)
        self.assertNotEqual(gd1, gd4)
        self.assertNotEqual(gd3, gd4)
