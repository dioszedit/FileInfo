"""Main window: file tree + metadata panel, toolbar, menus, status bar."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, QSettings, Qt
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
    QSplitter,
    QTextBrowser,
    QToolBar,
    QTreeView,
    QVBoxLayout,
)

from . import SETTINGS_APP, SETTINGS_ORG, i18n
from .deps import missing_dependencies
from .deps_dialog import DepsDialog
from .i18n import tr, trf
from .metadata_panel import MetadataPanel

_DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def _guide_paths() -> tuple[Path, Path]:
    """(HTML, markdown fallback) in the UI language; English if unavailable."""
    html = _DOCS_DIR / f"guide_{i18n.language()}.html"
    if not html.exists():
        html = _DOCS_DIR / "guide_en.html"
    md = _DOCS_DIR / ("FELHASZNALOI_UTMUTATO.md" if i18n.language() == "hu"
                      else "USER_GUIDE.md")
    return html, md


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FileInfo")
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

        # -- file tree ---------------------------------------------------
        self._model = QFileSystemModel(self)
        self._model.setRootPath("/")
        self._apply_hidden_filter(
            self._settings.value("showHidden", False, type=bool))

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        for column in range(1, self._model.columnCount()):
            self._tree.hideColumn(column)
        self._tree.setHeaderHidden(True)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._tree.selectionModel().selectionChanged.connect(self._on_selection)

        # -- metadata panel ------------------------------------------------
        self._panel = MetadataPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._tree)
        splitter.addWidget(self._panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self._splitter = splitter

        self._build_toolbar()
        self._build_menu()
        self.statusBar().showMessage(tr("Select a file in the tree on the left"))

        self._restore_state()
        self._warn_missing_deps()

    # -- construction ------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = QToolBar(tr("Toolbar"))
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)

        choose = QAction("📁 " + tr("Choose Folder…"), self)
        choose.setShortcut(QKeySequence.StandardKey.Open)
        choose.triggered.connect(self._choose_folder)
        toolbar.addAction(choose)

        home = QAction("🏠 " + tr("Home Folder"), self)
        home.triggered.connect(lambda: self._set_root(Path.home()))
        toolbar.addAction(home)

        toolbar.addSeparator()

        refresh = QAction("🔄 " + tr("Refresh"), self)
        refresh.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh.triggered.connect(self._panel.refresh)
        toolbar.addAction(refresh)

        copy_meta = QAction("📋 " + tr("Copy Metadata"), self)
        copy_meta.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_meta.triggered.connect(self._copy_metadata)
        toolbar.addAction(copy_meta)

        reveal = QAction("🔍 " + tr("Reveal in Finder"), self)
        reveal.triggered.connect(self._reveal_in_finder)
        toolbar.addAction(reveal)

    def _apply_hidden_filter(self, show_hidden: bool) -> None:
        filters = (QDir.Filter.AllDirs | QDir.Filter.Files
                   | QDir.Filter.NoDotAndDotDot)
        if show_hidden:
            filters |= QDir.Filter.Hidden
        self._model.setFilter(filters)

    def _toggle_hidden(self, checked: bool) -> None:
        self._settings.setValue("showHidden", checked)
        self._apply_hidden_filter(checked)

    def _build_menu(self) -> None:
        view_menu = self.menuBar().addMenu(tr("View"))
        hidden = QAction(tr("Show hidden files"), self)
        hidden.setCheckable(True)
        hidden.setChecked(self._settings.value("showHidden", False, type=bool))
        hidden.toggled.connect(self._toggle_hidden)
        view_menu.addAction(hidden)

        lang_menu = self.menuBar().addMenu(tr("Language"))
        for code, name in i18n.LANGUAGE_NAMES.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(code == i18n.language())
            action.triggered.connect(
                lambda _=False, c=code: self._switch_language(c))
            lang_menu.addAction(action)

        help_menu = self.menuBar().addMenu(tr("Help"))

        guide = QAction(tr("User Guide"), self)
        guide.triggered.connect(self._open_guide)
        help_menu.addAction(guide)

        deps = QAction(tr("Check Dependencies…"), self)
        deps.triggered.connect(lambda: DepsDialog(self).exec())
        help_menu.addAction(deps)

    # -- actions -------------------------------------------------------------

    def _set_root(self, folder: Path) -> None:
        self._tree.setRootIndex(self._model.index(str(folder)))
        self._settings.setValue("rootFolder", str(folder))
        self.statusBar().showMessage(trf("Root: {folder}", folder=folder), 3000)

    def _choose_folder(self) -> None:
        current = self._settings.value("rootFolder", str(Path.home()))
        folder = QFileDialog.getExistingDirectory(
            self, tr("Choose Folder"), current)
        if folder:
            self._set_root(Path(folder))

    def _on_selection(self, selected, _deselected) -> None:
        indexes = selected.indexes()
        if not indexes:
            return
        index: QModelIndex = indexes[0]
        path = Path(self._model.filePath(index))
        self.statusBar().showMessage(tr("Extracting…"))
        self._panel.show_file(path)

    def _copy_metadata(self) -> None:
        text = self._panel.metadata_as_text()
        if text:
            QGuiApplication.clipboard().setText(text)
            self.statusBar().showMessage(tr("Metadata copied to clipboard"), 3000)

    def _reveal_in_finder(self) -> None:
        path = self._panel.current_path()
        if path is None:
            return
        try:
            subprocess.run(["open", "-R", str(path)], check=False, timeout=10)
        except (subprocess.TimeoutExpired, OSError):
            pass

    def _open_guide(self) -> None:
        guide_html, _ = _guide_paths()
        if guide_html.exists():
            try:
                self._open_guide_webengine()
                return
            except Exception:
                pass  # WebEngine missing/broken -> Markdown fallback
        self._open_guide_fallback()

    def _open_guide_webengine(self) -> None:
        """Nice in-app HTML guide; external links open in the browser."""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtWebEngineCore import QWebEnginePage
        from PySide6.QtWebEngineWidgets import QWebEngineView

        class GuidePage(QWebEnginePage):
            def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame):
                if url.scheme() in ("http", "https"):
                    QDesktopServices.openUrl(url)
                    return False
                return True

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("User Guide"))
        dialog.resize(980, 720)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        view = QWebEngineView()
        page = GuidePage(view)
        view.setPage(page)
        view.load(QUrl.fromLocalFile(str(_guide_paths()[0])))
        layout.addWidget(view)
        dialog.exec()

    def _open_guide_fallback(self) -> None:
        """Markdown fallback when QtWebEngine is unavailable."""
        guide_md = _guide_paths()[1]
        if not guide_md.exists():
            self.statusBar().showMessage(tr("User guide not found"), 3000)
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("User Guide"))
        dialog.resize(760, 640)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(guide_md.read_text(encoding="utf-8"))
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(tr("Close"))
        buttons.rejected.connect(dialog.reject)
        buttons.clicked.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def _switch_language(self, code: str) -> None:
        if code == i18n.language():
            return
        self._settings.setValue("language", code)
        self._settings.sync()
        box = QMessageBox(self)
        box.setWindowTitle(tr("Restart required"))
        box.setText(tr("The language change takes effect after a restart. Restart now?"))
        restart = box.addButton(tr("Restart now"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr("Later"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() == restart:
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("splitter", self._splitter.saveState())
            self._settings.sync()
            # New process + clean exit (execv under a running Cocoa app
            # would print "Task policy set failed" to the console).
            try:
                subprocess.Popen(
                    [sys.executable, "-m", "fileinfo"],
                    cwd=Path(__file__).resolve().parent.parent,
                    start_new_session=True)
            except OSError as exc:
                self.statusBar().showMessage(f'{tr("Error")}: {exc}', 5000)
                return
            from PySide6.QtWidgets import QApplication
            QApplication.quit()

    # -- dependencies -----------------------------------------------------------

    def _warn_missing_deps(self) -> None:
        missing = missing_dependencies()
        if not missing:
            return
        names = ", ".join(d.name for d in missing)
        self.statusBar().showMessage(
            trf("Missing helper tool: {names} — see the Help menu for details",
                names=names))
        if not self._settings.value("depsWarned", False, type=bool):
            self._settings.setValue("depsWarned", True)
            DepsDialog(self).exec()

    # -- window state -----------------------------------------------------------

    def _restore_state(self) -> None:
        geometry = self._settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.resize(1100, 720)
        splitter_state = self._settings.value("splitter")
        if splitter_state is not None:
            self._splitter.restoreState(splitter_state)
        else:
            self._splitter.setSizes([320, 780])
        root = self._settings.value("rootFolder", str(Path.home()))
        self._tree.setRootIndex(self._model.index(root))

    def closeEvent(self, event) -> None:
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("splitter", self._splitter.saveState())
        super().closeEvent(event)
