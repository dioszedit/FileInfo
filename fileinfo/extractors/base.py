"""Shared data model and helper functions for the extractors."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field

from ..i18n import tr


@dataclass
class Field:
    key: str
    value: str


@dataclass
class Section:
    title: str
    fields: list[Field] = field(default_factory=list)

    def add(self, key: str, value: object) -> None:
        """Add a field; empty/None values are skipped."""
        if value is None:
            return
        text = str(value).strip()
        if text:
            self.fields.append(Field(key, text))


def run_tool(cmd: list[str], timeout: int = 15) -> str | None:
    """Run an external command; None if the tool is missing or fails."""
    exe = shutil.which(cmd[0])
    if exe is None:
        return None
    try:
        result = subprocess.run(
            [exe, *cmd[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} B"
            exact = f"{num_bytes:,}".replace(",", " ")
            return f"{size:.2f} {unit} ({exact} {tr('bytes')})"
        size /= 1024
    raise AssertionError("unreachable")


def format_duration(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_bitrate(bits_per_sec: float) -> str:
    kbps = bits_per_sec / 1000
    if kbps >= 10000:
        return f"{kbps / 1000:.1f} Mb/s"
    return f"{kbps:.0f} kb/s"


_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def humanize_key(key: str) -> str:
    """kMDItemPixelHeight -> Pixel Height, album_artist -> Album Artist."""
    for prefix in ("kMDItem", "kMD", "com_apple_"):
        if key.startswith(prefix):
            key = key[len(prefix) :]
            break
    key = key.replace("_", " ").replace("-", " ")
    key = _CAMEL_RE.sub(" ", key)
    words = key.split()
    out = []
    for i, word in enumerate(words):
        if word.isupper():
            out.append(word)  # acronyms (GPS, ISO) stay as-is
        elif i == 0:
            out.append(word.capitalize())
        else:
            out.append(word.lower())
    return " ".join(out)


# The most common ISO-639-2 codes; unknown codes are shown verbatim.
LANGUAGES = {
    "hun": "Hungarian",
    "eng": "English",
    "ger": "German",
    "deu": "German",
    "fre": "French",
    "fra": "French",
    "ita": "Italian",
    "spa": "Spanish",
    "por": "Portuguese",
    "rus": "Russian",
    "pol": "Polish",
    "cze": "Czech",
    "ces": "Czech",
    "slk": "Slovak",
    "slo": "Slovak",
    "rum": "Romanian",
    "ron": "Romanian",
    "srp": "Serbian",
    "hrv": "Croatian",
    "ukr": "Ukrainian",
    "jpn": "Japanese",
    "chi": "Chinese",
    "zho": "Chinese",
    "kor": "Korean",
    "ara": "Arabic",
    "tur": "Turkish",
    "nld": "Dutch",
    "dut": "Dutch",
    "swe": "Swedish",
    "nor": "Norwegian",
    "dan": "Danish",
    "fin": "Finnish",
    "gre": "Greek",
    "ell": "Greek",
    "heb": "Hebrew",
    "hin": "Hindi",
    "tha": "Thai",
    "vie": "Vietnamese",
    "ind": "Indonesian",
    "und": "undetermined",
}


def language_name(code: str) -> str:
    """Name of the track's language in the UI language (English name is the tr() key)."""
    en_name = LANGUAGES.get(code.lower())
    return tr(en_name) if en_name else code
