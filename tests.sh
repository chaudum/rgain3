#!/bin/sh -xe

pip install -e .
pytest -vvv -s --cache-clear
find . -name __pycache__ -type d -exec rm -rf {} +
rm -rf .pytest_cache/ .mypy_cache/ rgain.egg-info/
