# -*- coding: utf-8 -*-
#
# Copyright (c) 2009-2015 Felix Krull <f_krull@gmx.de>
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

from .version import __version__


__all__ = ["__version__", "GainData"]


class GainData(object):
    TP_UNDEFINED = "TP_UNDEFINED"
    TP_TRACK = "TP_TRACK"
    TP_ALBUM = "TP_ALBUM"

    """A class that contains Replay Gain data.

    Arguments for ``__init__`` are also instance variables. These are:
     - ``gain``: the gain (in dB, relative to ``ref_level``)
     - ``peak``: the peak
     - ``ref_level``: the used reference level (in dB)
    """

    def __init__(self, gain, peak=1.0, ref_level=89, gain_type=TP_UNDEFINED):
        self.gain = gain
        self.peak = peak
        self.ref_level = ref_level
        self.gain_type = gain_type

    def __str__(self):
        return ("gain=%.2f dB; peak=%.8f; reference-level=%i dB" %
                (self.gain, self.peak, self.ref_level))

    def __repr__(self):
        return "GainData(%s, %s, %s, %s)" % (self.gain, self.peak,
                                             self.ref_level, self.gain_type)

    def __eq__(self, other):
        return isinstance(other, GainData) and (
            self.gain == other.gain and
            self.peak == other.peak and
            self.ref_level == other.ref_level and
            self.gain_type == other.gain_type)

    def __ne__(self, other):
        return not self.__eq__(other)


class GSTError(Exception):
    def __init__(self, gerror, debug):
        self.domain = gerror.domain
        self.code = gerror.code
        # any string from glib stuff should be a UTF-8 byte string, right?
        self.message = gerror.message.decode("utf-8")
        self.debug = debug.decode("utf-8")

    def __unicode__(self):
        return u"GST error: %s (%s)" % (self.message, self.debug)
