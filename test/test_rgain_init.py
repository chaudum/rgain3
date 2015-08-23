from __future__ import unicode_literals

import unittest

import rgain


class TestGainData(unittest.TestCase):
    def test_eq(self):
        gd1 = rgain.GainData(-5, 0.5, 80)
        gd2 = rgain.GainData(-5, 0.5, 80)
        self.assertTrue(gd1 == gd2)
        self.assertFalse(gd1 != gd2)

    def test_not_eq(self):
        gd1 = rgain.GainData(-5, 0.5, 80)
        gd2 = rgain.GainData(-5, 0.6, 80)
        self.assertTrue(gd1 != gd2)
        self.assertFalse(gd1 == gd2)

    def test_bad_type(self):
        gd1 = rgain.GainData(-5, 0.6, 89)
        gd2 = "not GainData"
        self.assertTrue(gd1 != gd2)
        self.assertFalse(gd1 == gd2)

    def test_eq_gain_type(self):
        gd1 = rgain.GainData(0, 0, 0, rgain.GainData.TP_TRACK)
        gd2 = rgain.GainData(0, 0, 0, rgain.GainData.TP_TRACK)
        gd3 = rgain.GainData(0, 0, 0, rgain.GainData.TP_ALBUM)
        gd4 = rgain.GainData(0, 0, 0)
        self.assertEqual(gd1, gd2)
        self.assertNotEqual(gd1, gd3)
        self.assertNotEqual(gd1, gd4)
        self.assertNotEqual(gd3, gd4)
