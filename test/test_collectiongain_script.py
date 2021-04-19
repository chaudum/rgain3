from argparse import ArgumentError

import pytest

from rgain3.collectiongain import PositiveIntOrNone


@pytest.mark.parametrize("i,o", [(None, None), ("1", 1), ("42", 42)])
def test_positiveintornone_success(i, o):
    T = PositiveIntOrNone("jobs")
    assert T(i) == o


@pytest.mark.parametrize("i", ["foo", "3.141592"])
def test_positiveintornone_error(i):
    T = PositiveIntOrNone("jobs")
    with pytest.raises(ArgumentError) as exc_info:
        T(i)
    err_msg = "invalid literal for int() with base 10: '{}'".format(i)
    assert exc_info.value.message == err_msg


def test_positiveintornone_zero():
    T = PositiveIntOrNone("jobs")
    with pytest.raises(ArgumentError) as exc_info:
        T(0)
    err_msg = "jobs must be at least 1"
    assert exc_info.value.message == err_msg
