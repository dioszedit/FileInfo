"""Background tasks via QThreadPool, with staleness protection."""

from __future__ import annotations

import contextlib
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, SignalInstance

# Set once at app exit: running tasks abort at the next opportunity.
_shutting_down = False


def _safe_emit(signal: SignalInstance, *args: object) -> None:
    # During shutdown the signal's QObject may already be destroyed on the
    # C++ side while the worker thread is still finishing — ignore that.
    with contextlib.suppress(RuntimeError):
        signal.emit(*args)


class ExtractSignals(QObject):
    finished = Signal(int, list)  # request_id, list[Section]
    failed = Signal(int, str)


class ExtractTask(QRunnable):
    def __init__(self, request_id: int, path: Path) -> None:
        super().__init__()
        self.request_id = request_id
        self.path = path
        self.signals = ExtractSignals()

    def run(self) -> None:
        from .extractors import extract_all

        if _shutting_down:
            return
        try:
            sections = extract_all(self.path)
        except Exception as exc:
            _safe_emit(self.signals.failed, self.request_id, str(exc))
            return
        _safe_emit(self.signals.finished, self.request_id, sections)


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

        if _shutting_down:
            return
        try:
            image = make_thumbnail_image(self.path)
        except Exception:
            image = None
        _safe_emit(self.signals.finished, self.request_id, image)


class HashSignals(QObject):
    finished = Signal(int, str)  # request_id, hex digest
    failed = Signal(int, str)


class HashTask(QRunnable):
    """SHA-256 in chunks — constant memory even for huge files."""

    CHUNK = 4 * 1024 * 1024

    def __init__(self, request_id: int, path: Path) -> None:
        super().__init__()
        self.request_id = request_id
        self.path = path
        self.signals = HashSignals()

    def run(self) -> None:
        import hashlib

        try:
            digest = hashlib.sha256()
            with self.path.open("rb") as fh:
                while chunk := fh.read(self.CHUNK):
                    if _shutting_down:
                        return
                    digest.update(chunk)
        except OSError as exc:
            _safe_emit(self.signals.failed, self.request_id, str(exc))
            return
        _safe_emit(self.signals.finished, self.request_id, digest.hexdigest())


def submit(task: QRunnable) -> None:
    QThreadPool.globalInstance().start(task)


def shutdown_workers(timeout_ms: int = 3000) -> None:
    """Cancel queued tasks and drain the running ones; called once at app exit."""
    global _shutting_down
    _shutting_down = True
    pool = QThreadPool.globalInstance()
    pool.clear()
    pool.waitForDone(timeout_ms)
