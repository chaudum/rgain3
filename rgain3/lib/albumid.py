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

from functools import partial

from mutagen.id3 import ID3FileType
from mutagen.mp4 import MP4, AtomDataType, MP4FreeForm


def _get_mp4_tag_value(value):
    """Get the string from an optionally free form MP4 tag value"""
    if isinstance(value, MP4FreeForm):
        if value.dataformat == AtomDataType.UTF8:
            return value.decode('utf-8')

        if value.dataformat == AtomDataType.UTF16:
            return value.decode('utf-16be')

    return value


def _get_simple_tag(tags, mp3_keys, mp4_keys, default_key):
    """Retrieve a tag value, using either one of a few MP3 or MP4 tags or a
    generic one for other formats."""
    if isinstance(tags, ID3FileType):
        for k in mp3_keys:
            frame = tags.get(k, None)
            if frame:
                return frame.text[0]
    if isinstance(tags, MP4):
        for k in mp4_keys:
            vs = tags.get(k, None)
            if vs:
                return _get_mp4_tag_value(vs[0])
    else:
        vs = tags.get(default_key, None)
        if vs:
            return vs[0]

    # default fall-through
    return None


get_musicbrainz_album_id = partial(
    _get_simple_tag,
    mp3_keys=[
        "TXXX:MusicBrainz Album Id",
        "TXXX:MUSICBRAINZ_ALBUMID",
    ],
    mp4_keys=[
        "----:com.apple.iTunes:MusicBrainz Album Id",
        "----:com.apple.iTunes:MUSICBRAINZ_ALBUMID",
    ],
    default_key="musicbrainz_albumid",
)

get_musicbrainz_albumartist_id = partial(
    _get_simple_tag,
    mp3_keys=[
        "TXXX:MusicBrainz Album Artist Id",
        "TXXX:MUSICBRAINZ_ALBUMARTISTID",
    ],
    mp4_keys=[
        "----:com.apple.iTunes:MusicBrainz Album Artist Id",
        "----:com.apple.iTunes:MUSICBRAINZ_ALBUMARTISTID",
    ],
    default_key="musicbrainz_albumartistid",
)

get_musicbrainz_artist_id = partial(
    _get_simple_tag,
    mp3_keys=[
        "TXXX:MusicBrainz Artist Id",
        "TXXX:MUSICBRAINZ_ARTISTID",
    ],
    mp4_keys=[
        "----:com.apple.iTunes:MusicBrainz Artist Id",
        "----:com.apple.iTunes:MUSICBRAINZ_ARTISTID",
    ],
    default_key="musicbrainz_artistid",
)

get_album = partial(
    _get_simple_tag,
    mp3_keys=["TALB"],
    mp4_keys=["\xa9alb"],
    default_key="album",
)

get_artist = partial(
    _get_simple_tag,
    mp3_keys=["TPE1"],
    mp4_keys=["\xa9ART"],
    default_key="artist",
)


# XXX: We're not doing case-insensitive checking anymore. Let's hope that
# doesn't regress anything...
# For MP3, in that order:
#  - a generic "TXXX:albumartist"
#  - QL's "TXXX:QuodLibet::albumartist"
#  - fb2k's legacy "TXXX:ALBUM ARTIST"
#  - finally, "TPE2" as used by at least fb2k and Picard. According to
#    the ID3 standard, this is performer, but fb2k uses it for album
#    artist since 1.1.6, citing "compatibility with other players"; see
#    http://wiki.hydrogenaudio.org/index.php?title=Foobar2000:ID3_Tag_Mapping
get_albumartist = partial(
    _get_simple_tag,
    mp3_keys=[
        "TXXX:albumartist",
        "TXXX:QuodLibet::albumartist",
        "TXXX:ALBUM ARTIST",
        "TPE2",
    ],
    mp4_keys=["aART"],
    default_key="albumartist",
)


def _take_first_tag(tags, default, functions):
    """Return the first tag value that isn't None."""
    for f in functions:
        value = f(tags)
        if value is not None:
            return value
    return default


def get_album_id(tags):
    """Try to determine an album id based on the given tags.

    The basic logic is as follows:
    - If a MusicBrainz album ID exists, use that.
    - If an album tag exists, combine that with:
      - a MusicBrainz album artist ID if it exists,
      - otherwise an album artist tag if it exists,
      - otherwise an artist tag if it exists,
      - otherwise, nothing
      and use the result.
    - Otherwise, assume non-album track.
    """
    mb_album_id = get_musicbrainz_album_id(tags)
    if mb_album_id is not None:
        return mb_album_id
    album = get_album(tags)
    if album is not None:
        artist_part = _take_first_tag(tags, None, [
            get_musicbrainz_albumartist_id,
            get_albumartist,
            get_artist])
        if artist_part is None:
            return album
        else:
            return "{} - {}".format(artist_part, album)
    else:
        return None
