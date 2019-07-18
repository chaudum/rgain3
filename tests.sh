#!/bin/bash -xe

pip install -e .
pytest -vvv -s --cache-clear
find . -name __pycache__ -type d | xargs rm -rf
rm -rf .pytest_cache/ .mypy_cache/ rgain.egg-info/
