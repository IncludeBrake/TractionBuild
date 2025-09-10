#!/bin/bash
set -e
python_version=$(cat .python-version)
if [[ "$(python --version)" != *"$python_version"* ]]; then
  echo "ERROR: Requires Python $python_version"
  exit 1
fi
[ -d .venv ] || python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.lock
pre-commit install
ruff check --fix .
mypy .
pytest -q
echo "Bootstrap complete"
