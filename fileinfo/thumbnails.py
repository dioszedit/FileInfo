"""Thumbnail image creation (QImage — safe even on a background thread)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader

from .extractors.base import run_tool
from .extractors.image import IMAGE_EXTENSIONS
from .extractors.media import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS

MAX_PX = 480


def _read_scaled(path: Path) -> QImage | None:
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)  # honor EXIF orientation
    size = reader.size()
    if size.isValid() and (size.width() > MAX_PX or size.height() > MAX_PX):
        scaled = QSize(size)
        scaled.scale(MAX_PX, MAX_PX, Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(scaled)
    image = reader.read()
    return image if not image.isNull() else None


def _video_frame(path: Path) -> QImage | None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "frame.png"
        for seek in ("3", "0"):
            result = run_tool([
                "ffmpeg", "-v", "quiet", "-ss", seek, "-i", str(path),
                "-frames:v", "1", "-vf", f"scale='min({MAX_PX},iw)':-2",
                "-y", str(out),
            ], timeout=30)
            if result is not None and out.exists() and out.stat().st_size > 0:
                image = QImage(str(out))
                return image if not image.isNull() else None
    return None


def _audio_cover(path: Path) -> QImage | None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cover.png"
        result = run_tool([
            "ffmpeg", "-v", "quiet", "-i", str(path),
            "-map", "0:v:0", "-frames:v", "1", "-y", str(out),
        ], timeout=20)
        if result is not None and out.exists() and out.stat().st_size > 0:
            image = QImage(str(out))
            return image if not image.isNull() else None
    return None


def _quicklook(path: Path) -> QImage | None:
    with tempfile.TemporaryDirectory() as tmp:
        run_tool(["qlmanage", "-t", "-s", str(MAX_PX), "-o", tmp, str(path)],
                 timeout=15)
        candidates = list(Path(tmp).glob("*.png"))
        if candidates:
            image = QImage(str(candidates[0]))
            return image if not image.isNull() else None
    return None


def make_thumbnail_image(path: Path) -> QImage | None:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return _read_scaled(path) or _quicklook(path)
    if suffix in VIDEO_EXTENSIONS:
        return _video_frame(path) or _quicklook(path)
    if suffix in AUDIO_EXTENSIONS:
        return _audio_cover(path)  # no cover art -> None -> the panel keeps the file icon
    return _quicklook(path)
