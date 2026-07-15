"""QApplication setup, first-launch language chooser, main window startup."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QPushButton, QVBoxLayout

from . import SETTINGS_APP, SETTINGS_ORG, i18n

ICON_PATH = Path(__file__).resolve().parent / "resources" / "icon.png"


class LanguageDialog(QDialog):
    """Language chooser shown on first launch (in the default language, English)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FileInfo")
        self.setModal(True)
        self.selected = i18n.DEFAULT_LANGUAGE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Choose a language")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        for code, name in i18n.LANGUAGE_NAMES.items():
            btn = QPushButton(name)
            btn.setMinimumSize(220, 40)
            btn.clicked.connect(lambda _=False, c=code: self._choose(c))
            layout.addWidget(btn)

    def _choose(self, code: str) -> None:
        self.selected = code
        self.accept()


def run_gui() -> int:
    # QtWebEngine (the guide viewer) requires this before the QApplication.
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("FileInfo")
    app.setApplicationDisplayName("FileInfo")
    app.setOrganizationName("dioszegiedit")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    saved = settings.value("language")
    if saved:
        i18n.set_language(str(saved))
    else:
        dialog = LanguageDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            i18n.set_language(dialog.selected)
            settings.setValue("language", dialog.selected)
        else:
            # Esc/close: the default language applies to this run only;
            # the chooser appears again on the next launch.
            i18n.set_language(i18n.DEFAULT_LANGUAGE)

    from PySide6.QtCore import QThreadPool

    def drain_workers() -> None:
        pool = QThreadPool.globalInstance()
        pool.clear()
        pool.waitForDone(3000)

    app.aboutToQuit.connect(drain_workers)

    from .main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()
