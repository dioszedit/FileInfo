"""Background tasks via QThreadPool, with staleness protection."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class ExtractSignals(QObject):
    finished = Signal(int, list)   # request_id, list[Section]
    failed = Signal(int, str)


class ExtractTask(QRunnable):
    def __init__(self, request_id: int, path: Path) -> None:
        super().__init__()
        self.request_id = request_id
        self.path = path
        self.signals = ExtractSignals()

    def run(self) -> None:
        from .extractors import extract_all
        try:
            sections = extract_all(self.path)
        except Exception as exc:
            self.signals.failed.emit(self.request_id, str(exc))
            return
        self.signals.finished.emit(self.request_id, sections)


class ThumbnailSignals(QObject):
    finished = Signal(int, object)  # request_id, QImage | None


class ThumbnailTask(QRunnable):
    def __init__(self, request_id: int, path: Path) -> None:
        super().__init__()
        self.request_id = request_id
        self.path = path
        self.signals = ThumbnailSignals()

    def run(self) -> None:
        from .thumbnails import make_thumbnail_image
        try:
            image = make_thumbnail_image(self.path)
        except Exception:
            image = None
        self.signals.finished.emit(self.request_id, image)


def submit(task: QRunnable) -> None:
    QThreadPool.globalInstance().start(task)
