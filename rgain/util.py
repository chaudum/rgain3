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

import contextlib
import sys


def getfilesystemencoding():
    # get file system encoding, making sure never to return None
    return sys.getfilesystemencoding() or sys.getdefaultencoding()


@contextlib.contextmanager
def gobject_signals(obj, *signals):
    """Context manager to connect and disconnect GObject signals using a ``with``
    statement.
    """
    signal_ids = []
    try:
        for signal in signals:
            signal_ids.append(obj.connect(*signal))
        yield
    finally:
        for signal_id in signal_ids:
            obj.disconnect(signal_id)
