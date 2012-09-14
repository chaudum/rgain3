# -*- coding: utf-8 -*-
# kate: indent-width 4; indent-mode python;
# 
# Copyright (c) 2009, 2010, 2012 Felix Krull <f_krull@gmx.de>
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

from itertools import combinations
import os.path
import warnings

import mutagen
from mutagen.id3 import ID3, RVA2, TXXX
from mutagen.apev2 import APEv2File

from rgain import GainData


class AudioFormatError(Exception):
    def __init__(self, filename):
        Exception.__init__(self, u"Did not understand file: %s" % filename)

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

# basic tag-based reader/writer, suited for Ogg (Vorbis, Flac, Speex, ...) and
# Flac files at least (also WavPack it seems)
def rg_read_gain(filename):
    tags = mutagen.File(filename)
    if tags is None:
        raise AudioFormatError(filename)

    def read_gain_data(desc):
        gain_tag = u"replaygain_%s_gain" % desc
        peak_tag = u"replaygain_%s_peak" % desc
        if gain_tag in tags:
            gain = parse_db(tags[gain_tag][0])
            if gain is None:
                return None
            gaindata = GainData(gain)
            if peak_tag in tags:
                peak = parse_peak(tags[peak_tag][0])
                if peak is not None:
                    gaindata.peak = peak
            if u"replaygain_reference_loudness" in tags:
                ref_level = parse_db(tags[u"replaygain_reference_loudness"][0])
                if ref_level is not None:
                    gaindata.ref_level = ref_level
        else:
            gaindata = None
        return gaindata
    
    return read_gain_data("track"), read_gain_data("album")

def rg_write_gain(filename, trackdata, albumdata):
    tags = mutagen.File(filename)
    if tags is None:
        raise AudioFormatError(filename)
    
    if trackdata:
        tags[u"replaygain_track_gain"] = u"%.8f dB" % trackdata.gain
        tags[u"replaygain_track_peak"] = u"%.8f" % trackdata.peak
        tags[u"replaygain_reference_loudness"] = u"%i dB" % trackdata.ref_level
    
    if albumdata:
        tags[u"replaygain_album_gain"] = u"%.8f dB" % albumdata.gain
        tags[u"replaygain_album_peak"] = u"%.8f" % albumdata.peak
    
    tags.save()


# ID3v2 support for legacy RVA2-frames-based format according to
# http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_specification#ID3v2
REFERENCE_LOUDNESS_TAGS = [u"replaygain_reference_loudness",
                           u"QuodLibet::replaygain_reference_loudness"]

def mp3_legacy_read_gain(filename):
    tags = ID3(filename)
    if tags is None:
        raise AudioFormatError(filename)
    
    def read_gain_data(desc):
        tag = u"RVA2:%s" % desc
        if tag in tags:
            frame = tags[tag]
            gaindata = GainData(frame.gain, frame.peak)

            # Read all supported reference loudness tags, using the first that
            # exists.
            for t in REFERENCE_LOUDNESS_TAGS:
                if t in ("TXXX:%s" % t for t in tags):
                    gaindata.ref_level = parse_db(tags[t].text[0])
                    break
        else:
            gaindata = None
        return gaindata
    
    return read_gain_data("track"), read_gain_data("album")

def clamp_rva2_gain(v):
	clamped = False
	if v < -64:
		v = -64
		clamped = True
	if v >= 64:
		v = float(64 * 512 - 1) / 512.0
		clamped = True
	if clamped:
		warnings.warn("gain value was out of bounds for RVA2 frame and was clamped to %.2f" % v)
	return v

# I'm not sure if this situation could even reasonably happen, but
# can't hurt to check, right? Right!?
def clamp_rva2_peak(v):
	clamped = False
	if v < 0:
		v = 0
		clamped = True
	if v >= 2:
		v = float(2**16 - 1) / float(2**15)
		clamped = True
	if clamped:
		warnings.warn("peak value was out of bounds for RVA2 frame and was clamped to %.5f" % v)
	return v

def mp3_legacy_write_gain(filename, trackdata, albumdata):
    tags = ID3(filename)
    if tags is None:
        raise AudioFormatError(filename)
    
    if trackdata:
        trackgain = RVA2(desc=u"track", channel=1,
						 gain=clamp_rva2_gain(trackdata.gain),
                         peak=clamp_rva2_peak(trackdata.peak))
        tags.add(trackgain)
        # write reference loudness tags
        for t in REFERENCE_LOUDNESS_TAGS:
            reflevel = TXXX(encoding=3, desc=t,
                            text=[u"%i dB" % trackdata.ref_level])
            tags.add(reflevel)
    if albumdata:
        albumgain = RVA2(desc=u"album", channel=1,
						 gain=clamp_rva2_gain(albumdata.gain),
                         peak=clamp_rva2_peak(albumdata.peak))
        tags.add(albumgain)
    
    tags.save()


# ID3v2 support for TXXX:replaygain_* frames as specified in
# http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_specification#ID3v2
# and as implemented by at least foobar2000.
def mp3_rgorg_read_gain(filename):
    tags = ID3(filename)
    if tags is None:
        raise AudioFormatError(filename)
    
    def read_gain_data(desc):
        gain_tag = u"TXXX:replaygain_%s_gain" % desc
        peak_tag = u"TXXX:replaygain_%s_peak" % desc
        if gain_tag in tags:
            gain = parse_db(tags[gain_tag].text[0])
            if gain is None:
                return None
            gaindata = GainData(gain)
            if peak_tag in tags:
                peak = parse_peak(tags[peak_tag].text[0])
                if peak is not None:
                    gaindata.peak = peak
            if u"TXXX:replaygain_reference_loudness" in tags:
                ref_level = parse_db(tags[
                    u"TXXX:replaygain_reference_loudness"
                ].text[0])
                if ref_level is not None:
                    gaindata.ref_level = ref_level
        else:
            gaindata = None
        return gaindata
    
    return read_gain_data("track"), read_gain_data("album")

def mp3_rgorg_write_gain(filename, trackdata, albumdata):
    tags = ID3(filename)
    if tags is None:
        raise AudioFormatError(filename)
    
    def write_gain_data(desc, gaindata):
        gain_frame = TXXX(encoding=3, desc=u"replaygain_%s_gain" % desc,
                          text=[u"%.8f dB" % gaindata.gain])
        tags.add(gain_frame)
        peak_frame = TXXX(encoding=3, desc=u"replaygain_%s_peak" % desc,
                          text=[u"%.8f" % gaindata.peak])
        tags.add(peak_frame)
    
    if trackdata:
        write_gain_data("track", trackdata)
        tags.add(TXXX(encoding=3, desc=u"replaygain_reference_loudness",
                      text=[u"%i dB" % trackdata.ref_level]))
    if albumdata:
        write_gain_data("album", albumdata)
    
    tags.save()

# Special compatible MP3 support that
#  - reads both rg.org and legacy gain, compares them, returns them if they
#    match, else returns no gain data
#  - writes both rg.org and legacy gain
GAIN_EPSILON = 0.1
PEAK_EPSILON = 0.001
REF_LEVEL_EPSILON = 0.1

# For these three functions, b is always the legacy values, i.e. the potentially
# clamped ones.
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

def mp3_default_read_gain(filename):
    rgorg = mp3_rgorg_read_gain(filename)
    legacy = mp3_legacy_read_gain(filename)
    # We want to ensure we have all bits of data so if we only have one format,
    # we say we have none to enforce recalculation.
    if rgorg[0] is None or legacy[0] is None:
        return (None, None)
    if (not gaindata_almost_equal(rgorg[0], legacy[0]) or
            not gaindata_almost_equal(rgorg[1], legacy[1])):
        # The different formats are not similar enough.
        return (None, None)
    else:
        return rgorg

def mp3_default_write_gain(filename, trackdata, albumdata):
    mp3_legacy_write_gain(filename, trackdata, albumdata)
    mp3_rgorg_write_gain(filename, trackdata, albumdata)

# code to pull everything together
class UnknownFiletype(Exception):
    pass

class BaseFormatsMap(object):
    
    BASE_MAP = {
        ".ogg": (rg_read_gain, rg_write_gain),
        ".oga": (rg_read_gain, rg_write_gain),
        ".flac": (rg_read_gain, rg_write_gain),
        ".wv": (rg_read_gain, rg_write_gain),
    }

    MP3_FORMATS = {
        None: (mp3_default_read_gain, mp3_default_write_gain),
        "default": (mp3_default_read_gain, mp3_default_write_gain),
        "replaygain.org": (mp3_rgorg_read_gain, mp3_rgorg_write_gain),
        "fb2k": (mp3_rgorg_read_gain, mp3_rgorg_write_gain),
        "legacy": (mp3_legacy_read_gain, mp3_legacy_write_gain),
        "ql": (mp3_legacy_read_gain, mp3_legacy_write_gain),
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
    
    @property
    def supported_formats(self):
        return (set(self.BASE_MAP.iterkeys()) |
                set(self.more_mappings.iterkeys()))
    
    def read_gain(self, filename):
        ext = os.path.splitext(filename)[1]
        if ext in self.more_mappings:
            accessor = self.more_mappings[ext]
        elif ext in self.BASE_MAP:
            accessor = self.BASE_MAP[ext]
        else:
            raise UnknownFiletype(ext)
        
        return accessor[0](filename)
    
    def write_gain(self, filename, trackgain, albumgain):
        ext = os.path.splitext(filename)[1]
        if ext in self.more_mappings:
            accessor = self.more_mappings[ext]
        elif ext in self.BASE_MAP:
            accessor = self.BASE_MAP[ext]
        else:
            raise UnknownFiletype(ext)
        
        accessor[1](filename, trackgain, albumgain)
