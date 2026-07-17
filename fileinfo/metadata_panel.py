"""Right-hand panel: preview, file name, filter, sectioned metadata tree."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QFileInfo
from PySide6.QtGui import QFont, QGuiApplication, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFileIconProvider,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .extractors.base import Section
from .i18n import tr, trf
from .worker import ExtractTask, HashTask, ThumbnailTask, submit

THUMB_HEIGHT = 240


class MetadataPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._request_id = 0
        self._current_path: Path | None = None
        self._sections: list[Section] = []
        self._icon_provider = QFileIconProvider()

        self._thumb = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self._thumb.setMinimumHeight(0)
        self._thumb.hide()

        self._title = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self._title.setFont(font)
        self._title.setWordWrap(True)
        self._title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # The file name is data from the file — never interpret it as HTML.
        self._title.setTextFormat(Qt.TextFormat.PlainText)

        self._filter = QLineEdit(placeholderText=tr("Filter metadata…"))
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._apply_filter)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels([tr("Property"), tr("Value")])
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._context_menu)
        self._tree.header().setStretchLastSection(True)

        # SHA-256 row: computed on demand (a large file can take a while)
        self._hash_button = QPushButton("🔒 " + tr("Compute SHA-256"))
        self._hash_button.clicked.connect(self._start_hash)
        self._hash_button.setEnabled(False)
        self._hash_value = QLineEdit()
        self._hash_value.setReadOnly(True)
        self._hash_value.setFont(QFont("Menlo", 11))
        self._hash_value.hide()
        hash_row = QHBoxLayout()
        hash_row.addWidget(self._hash_button)
        hash_row.addWidget(self._hash_value, stretch=1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._thumb)
        layout.addWidget(self._title)
        layout.addWidget(self._filter)
        layout.addWidget(self._tree, stretch=1)
        layout.addLayout(hash_row)

        QShortcut(QKeySequence.StandardKey.Find, self,
                  activated=lambda: (self._filter.setFocus(),
                                     self._filter.selectAll()))

        # Selection-change debounce: only the last one runs when arrowing quickly.
        self._debounce = QTimer(self, singleShot=True, interval=200)
        self._debounce.timeout.connect(self._start_extraction)
        self._pending_path: Path | None = None

    # -- public API ----------------------------------------------------

    def show_file(self, path: Path) -> None:
        self._pending_path = path
        self._debounce.start()

    def refresh(self) -> None:
        self._debounce.stop()
        if self._pending_path is not None:
            self._start_extraction()

    def current_path(self) -> Path | None:
        return self._current_path

    def metadata_as_text(self) -> str:
        lines: list[str] = []
        if self._current_path is not None:
            lines.append(str(self._current_path))
        for section in self._sections:
            lines.append(f"\n=== {section.title} ===")
            for fld in section.fields:
                lines.append(f"{fld.key}: {fld.value}")
        if not self._hash_value.isHidden() and self._hash_value.text():
            lines.append(f"\nSHA-256: {self._hash_value.text()}")
        return "\n".join(lines)

    # -- extraction ----------------------------------------------------

    def _start_extraction(self) -> None:
        if self._pending_path is None:
            return
        path = self._pending_path
        self._current_path = path
        self._request_id += 1
        request_id = self._request_id

        self._title.setText(path.name)
        self._sections = []
        self._tree.clear()
        loading = QTreeWidgetItem([tr("Loading…"), ""])
        self._tree.addTopLevelItem(loading)
        self._show_icon_fallback(path)
        self._reset_hash_row(path)

        task = ExtractTask(request_id, path)
        task.signals.finished.connect(self._on_extracted)
        task.signals.failed.connect(self._on_failed)
        submit(task)

        if path.is_file():
            thumb_task = ThumbnailTask(request_id, path)
            thumb_task.signals.finished.connect(self._on_thumbnail)
            submit(thumb_task)

    def _on_extracted(self, request_id: int, sections: list) -> None:
        if request_id != self._request_id:
            return
        self._sections = sections
        self._populate(sections)
        self._apply_filter(self._filter.text())
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(trf("{n} sections loaded", n=len(sections)), 3000)

    def _on_failed(self, request_id: int, message: str) -> None:
        if request_id != self._request_id:
            return
        self._sections = []
        self._tree.clear()
        QTreeWidgetItem(self._tree, [tr("Error"), message])
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(f'{tr("Error")}: {message}', 5000)

    def _populate(self, sections: list[Section]) -> None:
        self._tree.clear()
        bold = QFont()
        bold.setBold(True)
        for section in sections:
            top = QTreeWidgetItem([section.title, ""])
            top.setFont(0, bold)
            self._tree.addTopLevelItem(top)
            top.setFirstColumnSpanned(True)
            for fld in section.fields:
                QTreeWidgetItem(top, [fld.key, fld.value])
            top.setExpanded(True)
        self._tree.resizeColumnToContents(0)
        self._tree.setColumnWidth(0, min(self._tree.columnWidth(0), 260))

    # -- SHA-256 ---------------------------------------------------------

    def _reset_hash_row(self, path: Path) -> None:
        self._hash_value.hide()
        self._hash_value.clear()
        self._hash_button.setText("🔒 " + tr("Compute SHA-256"))
        self._hash_button.setEnabled(path.is_file())

    def _start_hash(self) -> None:
        if self._current_path is None or not self._current_path.is_file():
            return
        self._hash_button.setEnabled(False)
        self._hash_button.setText("⏳ " + tr("Computing…"))
        task = HashTask(self._request_id, self._current_path)
        task.signals.finished.connect(self._on_hash)
        task.signals.failed.connect(self._on_hash_failed)
        submit(task)

    def _on_hash(self, request_id: int, digest: str) -> None:
        if request_id != self._request_id:
            return  # another file was selected in the meantime
        self._hash_button.setText("✅ SHA-256")
        self._hash_value.setText(digest)
        self._hash_value.show()
        self._hash_value.setCursorPosition(0)

    def _on_hash_failed(self, request_id: int, message: str) -> None:
        if request_id != self._request_id:
            return
        self._hash_button.setEnabled(True)
        self._hash_button.setText("🔒 " + tr("Compute SHA-256"))
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(f'{tr("Error")}: {message}', 5000)

    # -- preview ---------------------------------------------------------

    def _show_icon_fallback(self, path: Path) -> None:
        icon = self._icon_provider.icon(QFileInfo(str(path)))
        pixmap = icon.pixmap(128, 128)
        if pixmap.isNull():
            self._thumb.hide()
            return
        self._thumb.setPixmap(pixmap)
        self._thumb.show()

    def _on_thumbnail(self, request_id: int, image: object) -> None:
        if request_id != self._request_id:
            return
        if not isinstance(image, QImage) or image.isNull():
            return  # keep the Finder icon
        pixmap = QPixmap.fromImage(image)
        if pixmap.height() > THUMB_HEIGHT:
            pixmap = pixmap.scaledToHeight(
                THUMB_HEIGHT, Qt.TransformationMode.SmoothTransformation)
        self._thumb.setPixmap(pixmap)
        self._thumb.show()

    # -- filtering / clipboard ---------------------------------------------

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            title_match = bool(needle) and needle in top.text(0).lower()
            visible_children = 0
            for j in range(top.childCount()):
                child = top.child(j)
                match = (
                    not needle
                    or title_match
                    or needle in child.text(0).lower()
                    or needle in child.text(1).lower()
                )
                child.setHidden(not match)
                if match:
                    visible_children += 1
            top.setHidden(visible_children == 0 and top.childCount() > 0)

    def _context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if item is None or item.parent() is None:
            return
        menu = QMenu(self)
        copy_value = menu.addAction(tr("Copy value"))
        copy_row = menu.addAction(tr("Copy row"))
        chosen = menu.exec(self._tree.viewport().mapToGlobal(pos))
        if chosen == copy_value:
            QGuiApplication.clipboard().setText(item.text(1))
        elif chosen == copy_row:
            QGuiApplication.clipboard().setText(f"{item.text(0)}: {item.text(1)}")
