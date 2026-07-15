"""Extractor dispatcher: assembles the sections based on file type."""

from __future__ import annotations

from pathlib import Path

from ..i18n import tr
from .base import Field, Section
from . import fs, image, media, spotlight

__all__ = ["Field", "Section", "extract_all"]


def _safe(extractor, path: Path) -> list[Section]:
    try:
        return extractor.extract(path)
    except Exception as exc:  # one broken extractor must not take down the rest
        err = Section(tr("Errors"))
        err.add(type(exc).__name__, str(exc) or tr("unknown error"))
        return [err]


def extract_all(path: Path) -> list[Section]:
    path = Path(path)
    sections = _safe(fs, path)

    if path.is_file():
        suffix = path.suffix.lower()
        if suffix in media.MEDIA_EXTENSIONS:
            sections += _safe(media, path)
        elif suffix in image.IMAGE_EXTENSIONS:
            sections += _safe(image, path)
    if path.exists():
        # mdls works for folders too (e.g. .app bundles)
        sections += _safe(spotlight, path)

    return sections
