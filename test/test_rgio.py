import os
import unittest
from pathlib import Path

import pytest

from rgain3.rgio import (
    BaseFormatsMap,
    BaseTagReaderWriter,
    MP3DefaultTagReaderWriter,
    MP3TagReaderWriter,
    SimpleTagReaderWriter,
    UnknownFiletype,
)

DATA_PATH = Path(__file__).parent / "data"


class DummyMatroskaReaderWriter(BaseTagReaderWriter):
    def read_gain(self, filename):
        pass

    def write_gain(self, filename):
        pass


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


@pytest.mark.parametrize("filename,clazz", [
    ("album-tag.mp3", MP3DefaultTagReaderWriter),
    ("album-tag.flac", SimpleTagReaderWriter),
    ("album-tag.mp3.xyz", MP3DefaultTagReaderWriter),
])
def test_get_accessor(filename, clazz):
    format_map = BaseFormatsMap(mp3_format="default")
    path = DATA_PATH / filename
    assert isinstance(format_map.accessor(str(path)), clazz)
    assert format_map.is_supported(str(path)) is True


def test_get_accessor_unknown_type(tmpdir):
    format_map = BaseFormatsMap()
    path = tmpdir / "testfile.mka"
    with open(str(path), "wb") as fp:
        fp.write(os.urandom(1024))  # fill file with random bytes

    with pytest.raises(UnknownFiletype, match="mka"):
        format_map.accessor(str(path))
    assert format_map.is_supported(str(path)) is False


def test_get_accessor_more_mappings(tmpdir):
    more_map = {
        "mka": DummyMatroskaReaderWriter(),
    }
    format_map = BaseFormatsMap(more_mappings=more_map)
    path = tmpdir / "testfile.mka"
    with open(str(path), "wb") as fp:
        fp.write(os.urandom(1024))  # fill file with random bytes

    assert isinstance(format_map.accessor(str(path)), DummyMatroskaReaderWriter)
    assert format_map.is_supported(str(path)) is True
