#!/bin/bash
cd `dirname $0`
PYTHONPATH=. uv run coverage run -m unittest discover -s tests -p '*_test.py'
uv run coverage report -m