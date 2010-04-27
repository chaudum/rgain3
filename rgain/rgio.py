# -*- coding: utf-8 -*-
# 
# Copyright (c) 2009, 2010 Felix Krull <f_krull@gmx.de>
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

import mutagen
from mutagen.id3 import ID3, RVA2, TXXX
from mutagen.apev2 import APEv2File

from rgain import GainData



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

# basic tag-based reader/writer, suited for Ogg (Vorbis, Flac, Speex, ...) and
# Flac files at least (also WavPack it seems)
def rg_read_gain(filename):
    tags = mutagen.File(filename)
    
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
    
    if trackdata:
        tags[u"replaygain_track_gain"] = u"%.8f dB" % trackdata.gain
        tags[u"replaygain_track_peak"] = u"%.8f" % trackdata.peak
        tags[u"replaygain_reference_loudness"] = u"%i dB" % trackdata.ref_level
    
    if albumdata:
        tags[u"replaygain_album_gain"] = u"%.8f dB" % albumdata.gain
        tags[u"replaygain_album_peak"] = u"%.8f" % albumdata.peak
    
    tags.save()


# ID3 for Quod Libet
def mp3_ql_read_gain(filename):
    tags = ID3(filename)
    
    def read_gain_data(desc):
        tag = u"RVA2:%s" % desc
        if tag in tags:
            frame = tags[tag]
            gaindata = GainData(frame.gain, frame.peak)
            if u"TXXX:QuodLibet::replaygain_reference_loudness" in tags:
                ref_level = parse_db(tags[
                    u"TXXX:QuodLibet::replaygain_reference_loudness"
                ].text[0])
                if ref_level is not None:
                    gaindata.ref_level = ref_level
        else:
            gaindata = None
        return gaindata
    
    return read_gain_data("track"), read_gain_data("album")

def mp3_ql_write_gain(filename, trackdata, albumdata):
    tags = ID3(filename)
    
    if trackdata:
        trackgain = RVA2(desc=u"track", channel=1, gain=trackdata.gain,
                         peak=trackdata.peak)
        tags.add(trackgain)
        # write QL reference loudness
        reflevel = TXXX(encoding=3,
                        desc=u"QuodLibet::replaygain_reference_loudness",
                        text=[u"%i dB" % trackdata.ref_level])
        tags.add(reflevel)
    if albumdata:
        albumgain = RVA2(desc=u"album", channel=1, gain=albumdata.gain,
                         peak=albumdata.peak)
        tags.add(albumgain)
    
    tags.save()


# ID3 for foobar2000
def mp3_fb2k_read_gain(filename):
    tags = ID3(filename)
    
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

def mp3_fb2k_write_gain(filename, trackdata, albumdata):
    tags = ID3(filename)
    
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


# APE v2 tags as written by mp3gain
# I hope this works
def mp3_mp3gain_read_gain(filename):
    tags = APEv2File(filename)
    
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

def mp3_mp3gain_write_gain(filename, trackdata, albumdata):
    tags = APEv2File(filename)
    
    if trackdata:
        tags[u"replaygain_track_gain"] = u"%.8f dB" % trackdata.gain
        tags[u"replaygain_track_peak"] = u"%.8f" % trackdata.peak
        tags[u"replaygain_reference_loudness"] = u"%i dB" % trackdata.ref_level
    
    if albumdata:
        tags[u"replaygain_album_gain"] = u"%.8f dB" % albumdata.gain
        tags[u"replaygain_album_peak"] = u"%.8f" % albumdata.peak
    
    tags.save()


# rudimentary MP3 all-in-one support
def create_mp3_checks(ql=False, fb2k=False, mp3gain=False):
    def mp3_check_gain(filename):
        trackdata = None
        albumdata = None
        if mp3gain:
            trackdata, albumdata = mp3_mp3gain_read_gain(filename)
            if trackdata is None or albumdata is None:
                return trackdata, albumdata
        if fb2k:
            trackdata, albumdata = mp3_fb2k_read_gain(filename)
            if trackdata is None or albumdata is None:
                return trackdata, albumdata
        if ql:
            trackdata, albumdata = mp3_ql_read_gain(filename)
            if trackdata is None or albumdata is None:
                return trackdata, albumdata
        return trackdata, albumdata
    
    def mp3_write_gain(filename, trackdata, albumdata):
        if mp3gain:
            mp3_mp3gain_write_gain(filename, trackdata, albumdata)
        if fb2k:
            mp3_fb2k_write_gain(filename, trackdata, albumdata)
        if ql:
            mp3_ql_write_gain(filename, trackdata, albumdata)
    
    return mp3_check_gain, mp3_write_gain



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
    
    def __init__(self, mp3_format, more_mappings=None):
        # yeah, you need to choose
        self.more_mappings = more_mappings if more_mappings else {}
        if mp3_format == "ql":
            self.more_mappings[".mp3"] = (mp3_ql_read_gain, mp3_ql_write_gain)
        elif mp3_format == "fb2k":
            self.more_mappings[".mp3"] = (mp3_fb2k_read_gain,
                                          mp3_fb2k_write_gain)
        elif mp3_format == "mp3gain":
            self.more_mappings[".mp3"] = (mp3_mp3gain_read_gain,
                                          mp3_mp3gain_write_gain)
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

