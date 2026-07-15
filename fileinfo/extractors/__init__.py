"""Extraktor-diszpécser: fájltípus szerint válogatja össze a szekciókat."""

from __future__ import annotations

from pathlib import Path

from ..i18n import tr
from .base import Field, Section
from . import fs, image, media, spotlight

__all__ = ["Field", "Section", "extract_all"]


def _safe(extractor, path: Path) -> list[Section]:
    try:
        return extractor.extract(path)
    except Exception as exc:  # egy hibás extraktor ne vigye el az egészet
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
        # mappákra (pl. .app csomagokra) is működik az mdls
        sections += _safe(spotlight, path)

    return sections
