#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  echo "A Python-környezet (.venv) még nincs telepítve. / Python environment (.venv) is not set up yet."
  echo ""
  echo "Telepítés / Setup:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  echo ""
  read -s -k '?Nyomj egy billentyűt a bezáráshoz / Press any key to close...'
  exit 1
fi
exec .venv/bin/python -m fileinfo
