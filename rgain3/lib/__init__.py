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

import enum
from dataclasses import dataclass

from .version import __version__

__all__ = ["__version__", "GainData"]


class GainType(enum.Enum):
    TP_UNDEFINED = "TP_UNDEFINED"
    TP_TRACK = "TP_TRACK"
    TP_ALBUM = "TP_ALBUM"


@dataclass
class GainData:
    """A class that contains Replay Gain data.

    Arguments for ``__init__`` are also instance variables. These are:
     - ``gain``: the gain (in dB, relative to ``ref_level``)
     - ``peak``: the peak
     - ``ref_level``: the used reference level (in dB)
    """

    gain: float
    peak: float = 1.0
    ref_level: int = 89
    gain_type: GainType = GainType.TP_UNDEFINED


class GSTError(Exception):
    def __init__(self, gerror, debug):
        self.domain = gerror.domain
        self.code = gerror.code
        self.message = gerror.message
        self.debug = debug

    def __str__(self):
        return "GST error: {} ({})".format(self.message, self.debug)
