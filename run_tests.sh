#!/bin/bash
set -e
cd `dirname $0`
uv run coverage run -m pytest
uv run coverage report -m