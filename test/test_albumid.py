from __future__ import unicode_literals

import os.path
import unittest

import mutagen
from mutagen.id3 import ID3FileType

import rgain.albumid


DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


# Of the basic functions, we only test one because they're all very similar.
class TestGetAlbum(unittest.TestCase):
    def test_no_tags_flac(self):
        tags = mutagen.File(os.path.join(DATA_PATH, "no-tags.flac"))
        self.assertEqual(rgain.albumid.get_album(tags), None)

    def test_no_tags_mp3(self):
        tags = ID3FileType(os.path.join(DATA_PATH, "no-tags.mp3"))
        self.assertEqual(rgain.albumid.get_album(tags), None)

    def test_album_flac(self):
        tags = mutagen.File(os.path.join(DATA_PATH,
                                         "album-tag.flac"))
        self.assertEqual(rgain.albumid.get_album(tags), "Test Album")

    def test_album_mp3(self):
        tags = ID3FileType(os.path.join(DATA_PATH,
                                        "album-tag.mp3"))
        self.assertEqual(rgain.albumid.get_album(tags), "Test Album")


class TestGetMBAlbumID_MP3(unittest.TestCase):
    def test_no_tags(self):
        tags = ID3FileType(os.path.join(DATA_PATH, "no-tags.mp3"))
        self.assertEqual(rgain.albumid.get_musicbrainz_album_id(tags), None)

    def test_album_id_form1(self):
        tags = ID3FileType(os.path.join(DATA_PATH, "mb-album-id-form1.mp3"))
        self.assertEqual(rgain.albumid.get_musicbrainz_album_id(tags),
                         "TXXX:MusicBrainz Album Id")

    def test_album_id_form2(self):
        tags = ID3FileType(os.path.join(DATA_PATH, "mb-album-id-form2.mp3"))
        self.assertEqual(rgain.albumid.get_musicbrainz_album_id(tags),
                         "TXXX:MUSICBRAINZ_ALBUMID")


class TestGetAlbumArtist(unittest.TestCase):
    def test_no_tags_flac(self):
        tags = mutagen.File(os.path.join(DATA_PATH, "no-tags.flac"))
        self.assertEqual(rgain.albumid.get_albumartist(tags), None)

    def test_no_tags_mp3(self):
        tags = ID3FileType(os.path.join(DATA_PATH, "no-tags.mp3"))
        self.assertEqual(rgain.albumid.get_albumartist(tags), None)

    def test_albumartist_flac(self):
        tags = mutagen.File(os.path.join(DATA_PATH,
                                         "albumartist.flac"))
        self.assertEqual(rgain.albumid.get_albumartist(tags),
                         "Test Album Artist")

    def _mp3_test(self, suffix):
        tags = ID3FileType(
            os.path.join(DATA_PATH, "albumartist-%s.mp3" % suffix))
        self.assertEqual(rgain.albumid.get_albumartist(tags),
                         "Test Album Artist - %s" % suffix)

    def test_albumartist_mp3_TPE2(self):
        self._mp3_test("TPE2")

    def test_albumartist_mp3_TXXX_albumartist(self):
        self._mp3_test("TXXX_albumartist")

    def test_albumartist_mp3_TXXX_QL_albumartist(self):
        self._mp3_test("TXXX_QL_albumartist")

    def test_albumartist_mp3_TXXX_ALBUM_ARTIST(self):
        self._mp3_test("TXXX_ALBUM_ARTIST")


class TestGetAlbumId(unittest.TestCase):
    def test_no_tags_flac(self):
        tags = mutagen.File(os.path.join(DATA_PATH, "no-tags.flac"))
        self.assertEqual(rgain.albumid.get_album_id(tags), None)

    def test_no_tags_mp3(self):
        tags = ID3FileType(os.path.join(DATA_PATH, "no-tags.mp3"))
        self.assertEqual(rgain.albumid.get_album_id(tags), None)

    def test_album_flac(self):
        tags = mutagen.File(os.path.join(DATA_PATH,
                                         "album-tag.flac"))
        self.assertEqual(rgain.albumid.get_album_id(tags), "Test Album")

    def test_only_album_mp3(self):
        tags = ID3FileType(os.path.join(DATA_PATH,
                                        "album-tag.mp3"))
        self.assertEqual(rgain.albumid.get_album_id(tags), "Test Album")

    def test_only_albumartist(self):
        tags = mutagen.File(os.path.join(DATA_PATH,
                                         "albumartist.flac"))
        self.assertEqual(rgain.albumid.get_album_id(tags), None)

    def test_mb_album_id_only(self):
        tags = mutagen.File(os.path.join(DATA_PATH, "mb-album-id.flac"))
        self.assertEqual(rgain.albumid.get_album_id(tags), "MB Album ID")

    def test_mb_album_id_and_more(self):
        tags = mutagen.File(os.path.join(DATA_PATH,
                                         "mb-album-id-and-more.flac"))
        self.assertEqual(rgain.albumid.get_album_id(tags), "MB Album ID")

    def test_album_and_mb_albumartist(self):
        tags = ID3FileType(
            os.path.join(DATA_PATH, "album-and-mb-albumartist.mp3"))
        self.assertEqual(rgain.albumid.get_album_id(tags),
                         "MB Album Artist ID - Album Title")

    def test_album_and_albumartist(self):
        tags = ID3FileType(
            os.path.join(DATA_PATH, "album-and-albumartist.mp3"))
        self.assertEqual(rgain.albumid.get_album_id(tags),
                         "Album Artist - Album Title")

    def test_album_and_artist(self):
        tags = ID3FileType(os.path.join(DATA_PATH,
                                        "album-artist.mp3"))
        self.assertEqual(rgain.albumid.get_album_id(tags),
                         "Test Artist - Test Album")
