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
import logging
import sys
from typing import Optional, Union

logger = logging.getLogger(__name__)


def _ensure_str(value: Union[str, bytes]) -> str:
    if isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        return value.decode()
    raise TypeError


def _str_to_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except ValueError:
        logger.info("Could not convert '%s' to float", value)
    return None


def parse_db(value: Union[str, bytes]) -> Optional[float]:
    # The db value from mutagen _should_ by of type str, but there are cases
    # where we get bytes, see https://github.com/chaudum/rgain3/issues/38
    value = _ensure_str(value.strip())
    if value.lower().endswith("db"):
        value = value[:-2].strip()
    return _str_to_float(value)


def parse_peak(value: str) -> Optional[float]:
    # The db value from mutagen _should_ by of type str, but there are cases
    # where we get bytes, see https://github.com/chaudum/rgain3/issues/38
    value = _ensure_str(value.strip())
    return _str_to_float(value)


def almost_equal(
    a: Optional[float], b: Optional[float], epsilon: float
) -> bool:
    if a is None and b is None:
        return True
    elif a is None or b is None:
        return False
    return abs(a - b) <= epsilon


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
