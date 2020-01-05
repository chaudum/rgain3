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

import sys
import traceback
from optparse import OptionParser

import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst  # noqa isort:skip

import rgain3.rgio  # noqa  isort:skip
from rgain3 import __version__  # noqa isort:skip


__all__ = [
    "Error",
    "init_gstreamer",
    "common_options",
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
            IOError, rgain3.rgio.AudioFormatError, rgain3.GSTError,
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


def common_options():
    opts = OptionParser(version="%%prog %s" % __version__)

    opts.add_option("-f", "--force", help="Recalculate Replay Gain even if the "
                    "file already contains gain information.", dest="force",
                    action="store_true")
    opts.add_option("-d", "--dry-run", help="Don't actually modify any files.",
                    dest="dry_run", action="store_true")
    opts.add_option("-r", "--reference-loudness", help="Set the reference "
                    "loudness to REF dB (default: %default dB)", metavar="REF",
                    dest="ref_level", action="store", type="int")
    opts.add_option("--mp3-format", help="Choose the Replay Gain data format "
                    "for MP3 files. The default setting should be compatible "
                    "with most decent software music players, so it is "
                    "generally not necessary to mess with this setting. Check "
                    "the README or man page for more information.",
                    dest="mp3_format", action="store", type="choice",
                    choices=rgain3.rgio.BaseFormatsMap.MP3_DISPLAY_FORMATS)
    # This option only exists to show up in the help output; if it's actually
    # specified, GStreamer should eat it.
    opts.add_option("--help-gst", help="Show GStreamer options.",
                    dest="help_gst", action="store_true")

    opts.set_defaults(
        force=False, dry_run=False, ref_level=89, mp3_format="default")

    return opts
