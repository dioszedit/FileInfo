"""macOS Spotlight metadata via the mdls command."""

from __future__ import annotations

import plistlib
from datetime import datetime
from pathlib import Path

from ..i18n import tr
from .base import Section, humanize_key, run_tool

# These already appear in another section, or are noise.
_SKIP_PREFIXES = (
    "kMDItemFS",
    "kMDItemDisplayName",
    "kMDItemLogicalSize",
    "kMDItemPhysicalSize",
    "kMDItemDocumentIdentifier",
)


def _format_value(value: object) -> str | None:
    if isinstance(value, bool):
        return tr("yes") if value else tr("no")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (list, tuple)):
        parts = [str(_format_value(v)) for v in value if v is not None]
        return ", ".join(p for p in parts if p) or None
    if isinstance(value, bytes):
        return None
    return str(value)


def extract(path: Path) -> list[Section]:
    output = run_tool(["mdls", "-plist", "-", str(path)])
    if not output:
        return []
    try:
        data = plistlib.loads(output.encode())
    except Exception:
        return []

    sec = Section("Spotlight")
    for key in sorted(data):
        clean = key.lstrip("_")
        if any(clean.startswith(p) for p in _SKIP_PREFIXES):
            continue
        formatted = _format_value(data[key])
        if formatted:
            sec.add(humanize_key(clean), formatted)

    return [sec] if sec.fields else []
