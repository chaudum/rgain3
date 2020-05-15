import os.path
import unittest
from pathlib import Path

from rgain3.rgio import MP3TagReaderWriter

DATA_PATH = Path(os.path.dirname(__file__)) / "data"


class TestGetTagsObject(unittest.TestCase):
    def setUp(self):
        self.reader_writer = MP3TagReaderWriter()

    def test_no_headers_mp3(self):
        tags = self.reader_writer._get_tags_object(
            str(DATA_PATH / "missing-headers.mp3")
        )
        self.assertEqual(tags.keys(), [])
        self.assertTrue(tags.filename.endswith("missing-headers.mp3"))

    def test_no_tags_mp3(self):
        tags = self.reader_writer._get_tags_object(
            str(DATA_PATH / "no-tags.mp3")
        )
        self.assertEqual(tags.keys(), [])
        self.assertTrue(tags.filename.endswith("no-tags.mp3"))

    def test_album_mp3(self):
        tags = self.reader_writer._get_tags_object(
            str(DATA_PATH / "album-tag.mp3")
        )
        self.assertEqual(tags.keys(), ["album"])
        self.assertTrue(tags.filename.endswith("album-tag.mp3"))
