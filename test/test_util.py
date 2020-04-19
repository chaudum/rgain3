import pytest

from rgain3.util import parse_db, parse_peak


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
