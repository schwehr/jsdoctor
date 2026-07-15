#!/bin/bash
cd `dirname $0`
PYTHONPATH=. uv run python -m unittest discover -s tests -p '*_test.py'