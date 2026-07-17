"""Checks for the presence of helper tools."""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from .i18n import tr


@dataclass
class DepStatus:
    name: str
    path: str | None  # None = not installed
    purpose: str  # what it is for (English tr() key)
    install_cmd: str | None  # None = built-in macOS tool
    critical: bool


def check_dependencies() -> list[DepStatus]:
    def which(name: str) -> str | None:
        return shutil.which(name)

    return [
        DepStatus(
            "ffprobe",
            which("ffprobe"),
            tr("Detailed video and audio file data (streams, codecs, tags)"),
            "brew install ffmpeg",
            critical=True,
        ),
        DepStatus(
            "ffmpeg",
            which("ffmpeg"),
            tr("Video preview frame and audio cover art extraction"),
            "brew install ffmpeg",
            critical=False,
        ),
        DepStatus(
            "exiftool",
            which("exiftool"),
            tr("Full EXIF: camera settings, lens, GPS"),
            "brew install exiftool",
            critical=False,
        ),
        DepStatus(
            "mdls",
            which("mdls"),
            tr("macOS Spotlight metadata for every file type"),
            None,
            critical=False,
        ),
        DepStatus(
            "qlmanage",
            which("qlmanage"),
            tr("QuickLook previews (PDF, documents)"),
            None,
            critical=False,
        ),
    ]


def missing_dependencies() -> list[DepStatus]:
    return [d for d in check_dependencies() if d.path is None]


def homebrew_available() -> bool:
    return shutil.which("brew") is not None
