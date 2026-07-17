"""Filesystem-level data: size, dates, permissions."""

from __future__ import annotations

import contextlib
import grp
import mimetypes
import pwd
import stat as stat_mod
from datetime import datetime
from pathlib import Path

from ..i18n import tr
from .base import Section, format_size


def _format_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def extract(path: Path) -> list[Section]:
    sec = Section(tr("General"))
    st = path.lstat()

    sec.add(tr("Name"), path.name)
    sec.add(tr("Path"), str(path))

    if path.is_symlink():
        with contextlib.suppress(OSError):
            sec.add(tr("Symlink target"), str(path.readlink()))
        st = path.stat() if path.exists() else st

    if path.is_dir():
        kind = tr("Folder")
    else:
        mime, _ = mimetypes.guess_type(path.name)
        kind = mime or (path.suffix.lstrip(".").upper() + " " + tr("file") if path.suffix else tr("File"))
    sec.add(tr("Type"), kind)

    if not path.is_dir():
        sec.add(tr("Size"), format_size(st.st_size))

    birthtime = getattr(st, "st_birthtime", None)
    if birthtime:
        sec.add(tr("Created"), _format_time(birthtime))
    sec.add(tr("Modified"), _format_time(st.st_mtime))
    sec.add(tr("Last accessed"), _format_time(st.st_atime))

    sec.add(tr("Permissions"), stat_mod.filemode(st.st_mode))
    try:
        owner = pwd.getpwuid(st.st_uid).pw_name
        group = grp.getgrgid(st.st_gid).gr_name
        sec.add(tr("Owner"), f"{owner} / {group}")
    except KeyError:
        sec.add(tr("Owner"), f"{st.st_uid} / {st.st_gid}")

    return [sec]
