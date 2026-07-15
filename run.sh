#!/bin/zsh
DIR="${0:A:h}"
if [[ ! -x "$DIR/.venv/bin/python" ]]; then
  echo "A Python-környezet (.venv) még nincs telepítve. / Python environment (.venv) is not set up yet." >&2
  echo "Telepítés / Setup:  cd '$DIR' && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
PYTHONPATH="$DIR" exec "$DIR/.venv/bin/python" -m fileinfo "$@"
