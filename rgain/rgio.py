# -*- coding: utf-8 -*-
#
# Copyright (c) 2009-2014 Felix Krull <f_krull@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os.path
import warnings

import mutagen
from mutagen.easyid3 import EasyID3

from rgain import GainData


class AudioFormatError(Exception):
    def __init__(self, filename):
        Exception.__init__(self, u"Did not understand file: %s" % filename)


# some generic helper functions
def parse_db(string):
    string = string.strip()
    if string.lower().endswith("db"):
        string = string[:-2].strip()
    try:
        db = float(string)
    except ValueError:
        db = None
    return db


def parse_peak(string):
    try:
        peak = float(string.strip())
    except ValueError:
        peak = None
    return peak


def almost_equal(a, b, epsilon):
    if a is None and b is None:
        return True
    elif a is None or b is None:
        return False
    return abs(a - b) <= epsilon


# interface for ReplayGain reading/writing class
class BaseTagReaderWriter(object):
    def read_gain(self, filename):
        raise NotImplementedError

    def write_gain(self, filename, track_gain, album_gain):
        raise NotImplementedError


# class to read and write ReplayGain data from/to simple tags. The default tags
# match the rg.org specification for Ogg (at least Vorbis), Flac and WavPack
# files
class SimpleTagReaderWriter(BaseTagReaderWriter):
    TRACK_GAIN_TAG = u"replaygain_track_gain"
    TRACK_PEAK_TAG = u"replaygain_track_peak"
    ALBUM_GAIN_TAG = u"replaygain_album_gain"
    ALBUM_PEAK_TAG = u"replaygain_album_peak"
    REF_LOUDNESS_TAGS = [u"replaygain_reference_loudness"]

    # default behaviour; override in a subclass if necessary, e.g. for MP3
    def _get_tags_object(self, filename):
        return mutagen.File(filename)

    def read_gain(self, filename):
        tags = self._get_tags_object(filename)
        if tags is None:
            raise AudioFormatError(filename)

        track_gain = self._read_gain_data(tags, self.TRACK_GAIN_TAG,
                                          self.TRACK_PEAK_TAG)
        album_gain = self._read_gain_data(tags, self.ALBUM_GAIN_TAG,
                                          self.ALBUM_PEAK_TAG)
        ref_level = self._read_ref_loudness(tags)
        if ref_level is not None:
            if track_gain:
                track_gain.ref_level = ref_level
            if album_gain:
                album_gain.ref_level = ref_level
        return track_gain, album_gain

    def _read_gain_data(self, tags, gain_tag, peak_tag):
        if gain_tag in tags:
            gain = parse_db(tags[gain_tag][0])
            if gain is None:
                return None
            gaindata = GainData(gain)
            if peak_tag in tags:
                peak = parse_peak(tags[peak_tag][0])
                if peak is not None:
                    gaindata.peak = peak
        else:
            gaindata = None
        return gaindata

    def _read_ref_loudness(self, tags):
        for tag in self.REF_LOUDNESS_TAGS:
            if tag in tags:
                ref_level = parse_db(tags[tag][0])
                if ref_level is not None:
                    return ref_level
        return None

    def write_gain(self, filename, track_gain, album_gain):
        tags = self._get_tags_object(filename)
        if tags is None:
            raise AudioFormatError(filename)

        if track_gain:
            tags[self.TRACK_GAIN_TAG] = self._dump_gain(track_gain.gain)
            tags[self.TRACK_PEAK_TAG] = self._dump_peak(track_gain.peak)
            for tag in self.REF_LOUDNESS_TAGS:
                tags[tag] = self._dump_ref_level(track_gain.ref_level)

        if album_gain:
            tags[self.ALBUM_GAIN_TAG] = self._dump_gain(album_gain.gain)
            tags[self.ALBUM_PEAK_TAG] = self._dump_peak(album_gain.peak)

        tags.save()

    def _dump_gain(self, gain):
        return u"%.8f dB" % gain

    def _dump_peak(self, peak):
        return u"%.8f" % peak

    def _dump_ref_level(self, ref_level):
        return u"%i dB" % ref_level


# MP4 support
class MP4TagReaderWriter(SimpleTagReaderWriter):
    FORMAT = "----:com.apple.iTunes:replaygain_%s_%s"
    TRACK_GAIN_TAG = FORMAT % ("track", "gain")
    TRACK_PEAK_TAG = FORMAT % ("track", "peak")
    ALBUM_GAIN_TAG = FORMAT % ("album", "gain")
    ALBUM_PEAK_TAG = FORMAT % ("album", "peak")
    REF_LOUDNESS_TAGS = []

    # Mutagen 1.22 has a bug (?) such that MP4 values cannot be unicode objects
    # so we encode everything to ASCII here
    # https://code.google.com/p/mutagen/issues/detail?id=164
    def _dump_gain(self, gain):
        return SimpleTagReaderWriter._dump_gain(self, gain).encode("ascii")

    def _dump_peak(self, peak):
        return SimpleTagReaderWriter._dump_peak(self, peak).encode("ascii")

    def _dump_ref_level(self, ref_level):
        return SimpleTagReaderWriter._dump_ref_level(
            self, ref_level).encode("ascii")


# MP3 support base class
class MP3TagReaderWriter(SimpleTagReaderWriter):
    _EXTRA_TXXX_TAGS = [
        u"replaygain_track_gain",
        u"replaygain_track_peak",
        u"replaygain_album_gain",
        u"replaygain_album_peak",
        u"replaygain_reference_loudness",
        u"QuodLibet::replaygain_reference_loudness",
    ]

    class _ReplaygainEasyID3(EasyID3):
        pass

    for key in _EXTRA_TXXX_TAGS:
        _ReplaygainEasyID3.RegisterTXXXKey(u"TXXX:%s" % key, key)

    def _get_tags_object(self, filename):
        return self._ReplaygainEasyID3(filename)


# ID3v2 support for TXXX:replaygain_* frames as specified in
# http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_specification#ID3v2
# and as implemented by at least foobar2000.
class MP3rgorgTagReaderWriter(MP3TagReaderWriter):
    TRACK_GAIN_TAG = u"TXXX:replaygain_track_gain"
    TRACK_PEAK_TAG = u"TXXX:replaygain_track_peak"
    ALBUM_GAIN_TAG = u"TXXX:replaygain_album_gain"
    ALBUM_PEAK_TAG = u"TXXX:replaygain_album_peak"
    REF_LOUDNESS_TAGS = [u"TXXX:replaygain_reference_loudness"]


# clamp RVA2 values to certain limits so that they do not overflow
RVA2_GAIN_MIN = -64
RVA2_GAIN_MAX = float(64 * 512 - 1) / 512.0
RVA2_PEAK_MIN = 0
RVA2_PEAK_MAX = float(2 ** 16 - 1) / float(2 ** 15)


def clamp(v, min, max):
    clamped = False
    if v < min:
        v = min
        clamped = True
    if v > max:
        v = max
        clamped = True
    return v, clamped


def clamp_rva2_gain(v):
    v, clamped = clamp(v, RVA2_GAIN_MIN, RVA2_GAIN_MAX)
    if clamped:
        warnings.warn("gain value was out of bounds for RVA2 frame and was "
                      "clamped to %.2f" % v)
    return v


# I'm not sure if this situation could even reasonably happen, but
# can't hurt to check, right? Right!?
def clamp_rva2_peak(v):
    v, clamped = clamp(v, RVA2_PEAK_MIN, RVA2_PEAK_MAX)
    if clamped:
        warnings.warn("peak value was out of bounds for RVA2 frame and was "
                      "clamped to %.5f" % v)
    return v


def clamp_gain_data(gain_data):
    if gain_data is None:
        return None
    else:
        return GainData(clamp_rva2_gain(gain_data.gain),
                        clamp_rva2_peak(gain_data.peak),
                        gain_data.ref_level)


# ID3v2 support for legacy RVA2-frames-based format according to
# http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_specification#ID3v2
class MP3RVA2TagReaderWriter(MP3TagReaderWriter):
    # EasyID3 maps these to RVA2 by default
    TRACK_GAIN_TAG = u"replaygain_track_gain"
    TRACK_PEAK_TAG = u"replaygain_track_peak"
    ALBUM_GAIN_TAG = u"replaygain_album_gain"
    ALBUM_PEAK_TAG = u"replaygain_album_peak"

    # since there's no proper reference loudness tag for the legacy format, we
    # use reasonably common TXXX tags; these were registered in the superclass
    REF_LOUDNESS_TAGS = [
        u"TXXX:replaygain_reference_loudness",
        u"TXXX:QuodLibet::replaygain_reference_loudness",
    ]

    def _dump_gain(self, gain):
        return SimpleTagReaderWriter._dump_gain(self, clamp_rva2_gain(gain))

    def _dump_peak(self, peak):
        return SimpleTagReaderWriter._dump_peak(self, clamp_rva2_peak(peak))


# Special compatible MP3 support that
#  - reads both rg.org and legacy gain, compares them, returns them if they
#    match, else returns no gain data
#  - writes both rg.org and legacy gain
class MP3DefaultTagReaderWriter(BaseTagReaderWriter):
    def __init__(self, rgorg_readerwriter, rva2_readerwriter):
        self.rgorg = rgorg_readerwriter
        self.rva2 = rva2_readerwriter

    def read_gain(self, filename):
        rgorg_track_gain, rgorg_album_gain = self.rgorg.read_gain(filename)
        rva2_track_gain, rva2_album_gain = self.rva2.read_gain(filename)
        # We want to ensure we have all bits of data so if we only have one
        # format, we say we have none to enforce recalculation.
        if rgorg_track_gain is None or rva2_track_gain is None:
            # ensure that track gain exists for both
            return (None, None)
        if (not gaindata_almost_equal(rgorg_track_gain, rva2_track_gain) or
                not gaindata_almost_equal(rgorg_album_gain, rva2_album_gain)):
            # The different formats are not similar enough.
            return (None, None)
        else:
            # the formats seem to match, we obviously use the non-clamped one
            return (rgorg_track_gain, rgorg_album_gain)

    def write_gain(self, filename, track_gain, album_gain):
        self.rgorg.write_gain(filename, track_gain, album_gain)
        self.rva2.write_gain(filename, track_gain, album_gain)

GAIN_EPSILON = 0.1
PEAK_EPSILON = 0.001
REF_LEVEL_EPSILON = 0.1


# For these three functions, b is always the legacy values, i.e. the
# potentially clamped ones.
def gain_almost_equal(a, b):
    return (almost_equal(a, b, GAIN_EPSILON) or
            almost_equal(clamp_rva2_gain(a), b, GAIN_EPSILON))


def peak_almost_equal(a, b):
    return (almost_equal(a, b, PEAK_EPSILON) or
            almost_equal(clamp_rva2_peak(a), b, PEAK_EPSILON))


def gaindata_almost_equal(a, b):
    # Ensure neither element is None.
    if a is None:
        return b is None
    if b is None:
        return a is None
    if a == b:
        return True

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        return (gain_almost_equal(a.gain, b.gain) and
                peak_almost_equal(a.peak, b.peak) and
                almost_equal(a.ref_level, b.ref_level, REF_LEVEL_EPSILON))


# code to pull everything together
class UnknownFiletype(Exception):
    pass


class BaseFormatsMap(object):
    _simplereaderwriter = SimpleTagReaderWriter()
    _mp4readerwriter = MP4TagReaderWriter()
    _mp3_rgorg_readerwriter = MP3rgorgTagReaderWriter()
    _mp3_rva2_readerwriter = MP3RVA2TagReaderWriter()
    _mp3_default_readerwriter = MP3DefaultTagReaderWriter(
        _mp3_rgorg_readerwriter,
        _mp3_rva2_readerwriter)

    BASE_MAP = {
        ".ogg": _simplereaderwriter,
        ".oga": _simplereaderwriter,
        ".flac": _simplereaderwriter,
        ".wv": _simplereaderwriter,
        ".m4a": _mp4readerwriter,
        ".mp4": _mp4readerwriter,
    }

    MP3_FORMATS = {
        None: _mp3_default_readerwriter,
        "default": _mp3_default_readerwriter,
        "replaygain.org": _mp3_rgorg_readerwriter,
        "fb2k": _mp3_rgorg_readerwriter,
        "legacy": _mp3_rva2_readerwriter,
        "ql": _mp3_rva2_readerwriter,
    }

    MP3_DISPLAY_FORMATS = ["default", "replaygain.org", "legacy", "ql", "fb2k"]
    MP3_DEFAULT_FORMAT = "default"

    def __init__(self, mp3_format=None, more_mappings=None):
        # yeah, you need to choose
        self.more_mappings = more_mappings if more_mappings else {}
        if mp3_format in self.MP3_FORMATS:
            self.more_mappings[".mp3"] = self.MP3_FORMATS[mp3_format]
        else:
            raise ValueError("invalid MP3 format %r" % mp3_format)

    def is_supported_format(self, ext):
        ext_lower = ext.lower()
        return ext_lower in self.BASE_MAP or ext_lower in self.more_mappings

    def read_gain(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.more_mappings:
            accessor = self.more_mappings[ext]
        elif ext in self.BASE_MAP:
            accessor = self.BASE_MAP[ext]
        else:
            raise UnknownFiletype(ext)

        return accessor.read_gain(filename)

    def write_gain(self, filename, trackgain, albumgain):
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.more_mappings:
            accessor = self.more_mappings[ext]
        elif ext in self.BASE_MAP:
            accessor = self.BASE_MAP[ext]
        else:
            raise UnknownFiletype(ext)
        
        accessor.write_gain(filename, trackgain, albumgain)
