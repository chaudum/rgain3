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

import sys
from optparse import OptionParser
import traceback


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
    def __init__(self, message):
        Exception.__init__(self, message)
        # as long as instances are only constructed in exception handlers, this
        # should get us what we want
        self.exc_info = sys.exc_info()
    
    def __unicode__(self):
        # not a particularly good metric
        if not __debug__:
            return Exception.__unicode__(self)
        else:
            return unicode(traceback.format_exception(*self.exc_info))


def common_options():
    opts = OptionParser(version="%prog 1.0")
    
    opts.add_option("-f", "--force", help="Recalculate Replay Gain even if the "
                    "file already contains gain information.", dest="force",
                    action="store_true")
    opts.add_option("-d", "--dry-run", help="Don't actually modify any files.",
                    dest="dry_run", action="store_true")
    opts.add_option("-r", "--reference-loudness", help="Set the reference "
                    "loudness to REF dB (default: %default dB)", metavar="REF",
                    dest="ref_level", action="store", type="int")
    opts.add_option("--mp3-format", help="Choose the Replay Gain data format "
                    "for MP3 files. Since there is no commonly accepted "
                    "standard for Replay Gain in MP3 files, you need to "
                    "choose. Possible formats are 'ql' (used by Quod Libet), "
                    "'fb2k' (read and written by foobar2000, also understood "
                    "by Quod Libet) and 'mp3gain' (tags as written by the "
                    "'mp3gain' program; this doesn't modify the MP3 audio "
                    "data as said program does). Default is '%default'.",
                    dest="mp3_format", action="store", type="choice",
                    choices=["ql", "fb2k", "mp3gain"])
    
    opts.set_defaults(force=False, dry_run=False, ref_level=89, mp3_format="ql")
    
    return opts

