import os
import uuid
from pathlib import Path

import pytest

from rgain3.util import extension_for_file, parse_db, parse_peak


@pytest.mark.parametrize("in_value,expected", [
    ("invalid", None),
    ("", None),
    ("1", 1.0),
    ("1.0", 1.0),
    ("1 db", 1.0),
    ("1.0 DB", 1.0),
    ("1.0 dB", 1.0),
    ("1.0dB", 1.0),
    (" 1.0dB ", 1.0),
])
def test_parse_db(in_value, expected):
    assert parse_db(in_value) == expected


@pytest.mark.parametrize("in_value,expected", [
    ("invalid", None),
    ("", None),
    ("1dB", None),
    ("1", 1.0),
    ("1.0", 1.0),
    (" 1.0 ", 1.0),
])
def test_parse_peak(in_value, expected):
    assert parse_peak(in_value) == expected


@pytest.mark.parametrize("filename,filetype", [
    ("album-tag.mp3", "mp3"),
    ("album-tag.flac", "flac"),
    ("album-tag.mp3.xyz", "mp3"),  # different extension than file format
])
def test_extension_for_file(filename, filetype):
    path = Path(__file__).parent / "data" / filename
    assert extension_for_file(str(path)) == filetype


def test_extension_for_file_does_not_exist():
    path = Path(__file__).parent / "data" / uuid.uuid4().hex
    with pytest.raises(FileNotFoundError):
        extension_for_file(str(path))


def test_extension_for_file_fallback(tmpdir):
    path = tmpdir / "testfile.iso"
    with open(str(path), "wb") as fp:
        fp.write(os.urandom(1024))
    extension_for_file(str(path)) == "iso"
