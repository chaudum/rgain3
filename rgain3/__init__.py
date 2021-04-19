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

import sys
import traceback
from argparse import ArgumentParser

import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst  # noqa isort:skip

from rgain3.lib import GSTError, __version__  # noqa isort:skip
from rgain3.lib.rgio import AudioFormatError, BaseFormatsMap # noqa isort:skip


__all__ = [
    "Error",
    "init_gstreamer",
    "common_parser",
]


class Error(Exception):
    def __init__(self, message, exc_info=None):
        super().__init__(message)
        # as long as instances are only constructed in exception handlers, this
        # should get us what we want
        self.exc_info = exc_info if exc_info else sys.exc_info()

    def __str__(self):
        if not self._output_full_exception():
            return super().__str__()
        else:
            return "".join(traceback.format_exception(*self.exc_info))

    def _output_full_exception(self):
        return self.exc_info[0] not in [
            IOError, AudioFormatError, GSTError,
        ]


def init_gstreamer():
    """Properly initialise GStreamer for the command-line interfaces.

    Specifically, GStreamer options are parsed and processed by GStreamer, but
    it is also kept from taking over the main help output (by pretending -h
    or --help wasn't passed, if necessary). --help-gst should be documented in
    the main help output as a switch to display GStreamer options."""
    # Strip any --help options from the command line.
    stripped_options = []
    for opt in ["-h", "--help"]:
        if opt in sys.argv:
            sys.argv.remove(opt)
            stripped_options.append(opt)
    # Then, pass any remaining options to GStreamer.
    sys.argv = Gst.init(sys.argv)
    # Finally, restore any help options so optparse can eat them.
    for opt in stripped_options:
        sys.argv.append(opt)


def common_parser(**kwargs) -> ArgumentParser:
    """Create a new ArgumentParser instance with default arguments that are
    used both by `replaygain` and `collectiongain`.

    The function takes any keyword arguments that are valid for the
    instantiation of the `ArgumentParser` class. However, `add_help` and
    `allow_abbrev` are overwritten with static defaults.
    """
    kwargs["add_help"] = True
    kwargs["allow_abbrev"] = False

    parser = ArgumentParser(**kwargs)
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + (__version__ or "-"),
    )
    parser.add_argument(
        "-f", "--force",
        dest="force",
        action="store_true",
        help="Recalculate Replay Gain even if the file already contains gain."
        "information.",
    )
    parser.add_argument(
        "-d", "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Don't actually modify any files.",
    )
    parser.add_argument(
        "-r", "--reference-loudness",
        type=int,
        dest="ref_level",
        default=89,
        metavar="REF",
        help="Set the reference loudness to REF dB (default: %(default)s dB).",
    )
    parser.add_argument(
        "--mp3-format",
        type=str,
        dest="mp3_format",
        default="default",
        choices=BaseFormatsMap.MP3_DISPLAY_FORMATS,
        help="Choose the Replay Gain data format for MP3 files. The default "
        "setting should be compatible with most decent software music players, "
        "so it is generally not necessary to mess with this setting. Check the "
        "README or man page for more information.",
    )
    # This option only exists to show up in the help output; if it's actually
    # specified, GStreamer should eat it.
    parser.add_argument(
        "--help-gst",
        dest="help_gst",
        action="store_true",
        help="Show GStreamer options.",
    )
    return parser
