# -*- coding: utf-8 -*-
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

import sys
from optparse import OptionParser
import traceback

import rgain.rgio

stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()
def ou(arg):
    if isinstance(arg, str):
        return arg.decode("ascii").encode(stdout_encoding)
    return arg.encode(stdout_encoding)

def un(arg, encoding):
    if isinstance(arg, str):
        return arg.decode(encoding)
    return arg


class Error(Exception):
    def __init__(self, message, exc_info=None):
        Exception.__init__(self, message)
        # as long as instances are only constructed in exception handlers, this
        # should get us what we want
        self.exc_info = exc_info if exc_info else sys.exc_info()
    
    def __unicode__(self):
        if not self._output_full_exception():
            return Exception.__unicode__(self)
        else:
            return unicode(u"".join(traceback.format_exception(*self.exc_info)))

    def _output_full_exception(self):
        return self.exc_info[0] not in [IOError, rgain.rgio.AudioFormatError]


def common_options():
    opts = OptionParser(version="%prog 1.1")
    
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
                    choices=rgain.rgio.BaseFormatsMap.MP3_DISPLAY_FORMATS)
    
    opts.set_defaults(force=False, dry_run=False, ref_level=89,
        mp3_format="default")
    
    return opts

