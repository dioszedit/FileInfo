"""Simple translation module.

Source strings in the code are English; tr() translates them from the
selected language's dictionary. Dictionaries live in
fileinfo/locales/<code>.json (English source string -> translated string).
Adding a language = adding one JSON file with a "_language_name" key —
nothing else to change. A missing entry falls back to the English source
string, so the app never breaks.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LANGUAGE = "en"

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def _discover() -> dict[str, str]:
    """Available languages: {code: native name}. English is built in."""
    names = {"en": "English"}
    for f in sorted(_LOCALES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            names[f.stem] = data.get("_language_name", f.stem)
        except (OSError, json.JSONDecodeError):
            continue
    return names


LANGUAGE_NAMES = _discover()

_current = DEFAULT_LANGUAGE
_table: dict[str, str] = {}


def set_language(lang: str) -> None:
    global _current, _table
    _current = lang if lang in LANGUAGE_NAMES else DEFAULT_LANGUAGE
    if _current == DEFAULT_LANGUAGE:
        _table = {}
        return
    try:
        _table = json.loads(
            (_LOCALES_DIR / f"{_current}.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _table = {}


def language() -> str:
    return _current


def tr(text: str) -> str:
    if _current == DEFAULT_LANGUAGE:
        return text
    return _table.get(text, text)


def trf(text: str, **kwargs) -> str:
    """tr() + .format(); on a bad translation placeholder it falls back
    to the English source string instead of crashing."""
    translated = tr(text)
    try:
        return translated.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text.format(**kwargs)


def load_saved_language() -> str | None:
    """Load the saved language from QSettings (used by both GUI and CLI)."""
    from PySide6.QtCore import QSettings

    from . import SETTINGS_APP, SETTINGS_ORG
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    lang = settings.value("language")
    if lang:
        set_language(str(lang))
        return str(lang)
    return None
