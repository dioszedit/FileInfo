"""Dependency status dialog with installation instructions."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .deps import check_dependencies, homebrew_available
from .i18n import tr, trf

HOMEBREW_INSTALL = ('/bin/bash -c "$(curl -fsSL '
                    'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')


class DepsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Dependency Check"))
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)

        intro = QLabel(tr(
            "FileInfo relies on external tools for part of the metadata. "
            "Anything missing can be installed with the command shown — the "
            "app keeps working meanwhile, just shows less data."))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        grid = QGridLayout()
        grid.setColumnStretch(2, 1)
        bold = QFont()
        bold.setBold(True)

        row = 0
        missing_installable = False
        for dep in check_dependencies():
            ok = dep.path is not None
            status = QLabel("✅" if ok else "❌")
            name = QLabel(dep.name)
            name.setFont(bold)
            install = dep.install_cmd or tr("built-in tool")
            desc = QLabel(dep.purpose if ok else
                          f"{dep.purpose}\n" + trf("Install: {cmd}", cmd=install))
            desc.setWordWrap(True)
            grid.addWidget(status, row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(name, row, 1, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(desc, row, 2)
            if not ok and dep.install_cmd:
                missing_installable = True
                copy_btn = QPushButton(tr("Copy command"))
                copy_btn.clicked.connect(
                    lambda _=False, cmd=dep.install_cmd: self._copy(cmd))
                grid.addWidget(copy_btn, row, 3, Qt.AlignmentFlag.AlignTop)
            row += 1
        layout.addLayout(grid)

        if missing_installable and not homebrew_available():
            brew_label = QLabel(
                tr("<b>The Homebrew package manager is not installed either.</b> Install it first by running this command in Terminal (details: ")
                + '<a href="https://brew.sh">brew.sh</a>):<br>'
                + f"<code>{HOMEBREW_INSTALL}</code>")
            brew_label.setWordWrap(True)
            brew_label.setOpenExternalLinks(True)
            brew_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextBrowserInteraction)
            layout.addWidget(brew_label)
            brew_copy = QPushButton(tr("Copy Homebrew install command"))
            brew_copy.clicked.connect(lambda: self._copy(HOMEBREW_INSTALL))
            layout.addWidget(brew_copy)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _copy(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)
        sender = self.sender()
        if isinstance(sender, QPushButton):
            sender.setText(tr("Copied ✓"))
