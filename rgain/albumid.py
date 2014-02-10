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

import mutagen
from mutagen.id3 import ID3FileType

def _mp3_get_frame_data(tags, frame_key, default=None):
    frame = tags.get(frame_key, None)
    if frame is not None:
        return frame.text[0]
    else:
        return default

def _default_get_tag(tags, key, default=None):
    value = tags.get(key, None)
    if value is not None:
        return value[0]
    else:
        return default

def _get_simple_tag(tags, mp3_key, default_key):
    if isinstance(tags, ID3FileType):
        return _mp3_get_frame_data(tags, mp3_key, None)
    else:
        return _default_get_tag(tags, default_key, None)

get_musicbrainz_album_id = lambda tags: _get_simple_tag(tags,
    "TXXX:MusicBrainz Album Id",
    "musicbrainz_albumid")

get_musicbrainz_albumartist_id = lambda tags: _get_simple_tag(tags,
    "TXXX:MusicBrainz Album Artist Id",
    "musicbrainz_albumartistid")

get_musicbrainz_artist_id = lambda tags: _get_simple_tag(tags,
    "TXXX:MusicBrainz Artist Id",
    "musicbrainz_artistid")

get_album = lambda tags: _get_simple_tag(tags,
    "TALB",
    "album")

get_artist = lambda tags: _get_simple_tag(tags,
    "TPE1",
    "artist")

def get_albumartist(tags):
    if isinstance(tags, ID3FileType):
        # We try several tags to get the album artist from an MP3 file:
        #  - a generic "TXXX:albumartist"
        #  - QL's "TXXX:QuodLibet::albumartist"
        #  - fb2k's legacy "TXXX:ALBUM ARTIST"
        #  - finally, "TPE2" as used by at least fb2k and Picard. According to
        #    the ID3 standard, this is performer, but fb2k uses it for album
        #    artist since 1.1.6, citing "compatibility with other players"; see
        #    http://wiki.hydrogenaudio.org/index.php?title=Foobar2000:ID3_Tag_Mapping
        #  - if none of these exist, we assume no album artist tag
        # All of these frame names are matched regardless of capitalisation.
        TAGS = [t.lower() for t in [
            "TXXX:albumartist",
            "TXXX:QuodLibet::albumartist",
            "TXXX:ALBUM ARTIST",
            "TPE2"]]
        for key, frame in tags.iteritems():
            if key.lower() in TAGS:
                return frame.text[0]
        # Nothing matched.
        return None
    else:
        # We just use the rather standard "albumartist"
        return _default_get_tag(tags, "albumartist", None)


def _take_first_tag(tags, default, functions):
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
            return u"%s - %s" % (artist_part, album)
    else:
        return None
