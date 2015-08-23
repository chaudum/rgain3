from __future__ import unicode_literals
import os.path
import unittest

from rgain import GainData, rgcalc, util


# Have to set up GStreamer for all these tests.
import gi
gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst
Gst.init([])


DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


class TestReplayGain(unittest.TestCase):
    def test_no_files(self):
        with self.assertRaises(ValueError):
            rgcalc.calculate([])

    def test_silence(self):
        f = os.path.join(DATA_PATH, "no-tags.flac")
        t, a = rgcalc.calculate([f])

        # Gain and peak determined experimentally for this file.
        self.assertAlmostEqual(a.gain, 64.82, 5)
        self.assertAlmostEqual(a.peak, 0.000244, 5)
        self.assertEqual(a.ref_level, 89)
        self.assertEqual(a.gain_type, GainData.TP_ALBUM)

        self.assertEqual(len(t), 1)
        for k in t:
            self.assertEqual(k, f)
            gain = t[k]
            self.assertAlmostEqual(gain.gain, 64.82, 5)
            self.assertAlmostEqual(gain.peak, 0.000244, 5)
            self.assertEqual(gain.ref_level, 89)
            self.assertEqual(gain.gain_type, GainData.TP_TRACK)

    def test_custom_ref_level(self):
        f = os.path.join(DATA_PATH, "no-tags.flac")
        t, a = rgcalc.calculate([f], ref_lvl=105)

        self.assertAlmostEqual(a.gain, 80.82, 5)
        self.assertAlmostEqual(a.peak, 0.000244, 5)
        self.assertEqual(a.ref_level, 105)
        self.assertEqual(a.gain_type, GainData.TP_ALBUM)

        self.assertEqual(len(t), 1)
        for k in t:
            self.assertEqual(k, f)
            gain = t[k]
            self.assertAlmostEqual(gain.gain, 80.82, 5)
            self.assertAlmostEqual(gain.peak, 0.000244, 5)
            self.assertEqual(gain.ref_level, 105)
            self.assertEqual(gain.gain_type, GainData.TP_TRACK)

    def test_track_started_finished_signals(self):
        tracks = [os.path.join(DATA_PATH, "no-tags.flac"),
                  os.path.join(DATA_PATH, "no-tags.mp3")]
        rg = rgcalc.ReplayGain(tracks)
        events = []

        def event(*args):
            events.append(list(args))

        loop = GObject.MainLoop()
        with util.gobject_signals(
                rg,
                ("track_started", event),
                ("track_finished", event),
                ("all-finished", lambda *args: loop.quit())):
            rg.start()
            loop.run()

        self.assertEqual(len(events), 4)
        self.assertEqual(events[0], [rg, tracks[0]])
        self.assertEqual(events[1], [rg, tracks[0], rg.track_data[tracks[0]]])
        self.assertEqual(events[2], [rg, tracks[1]])
        self.assertEqual(events[3], [rg, tracks[1], rg.track_data[tracks[1]]])
