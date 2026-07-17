"""Image file data: Pillow basics + exiftool for the full EXIF."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ..i18n import tr
from .base import Section, humanize_key, run_tool

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".heif",
    ".tif",
    ".tiff",
    ".gif",
    ".webp",
    ".bmp",
    ".avif",
    ".jp2",
    ".psd",
    ".ico",
    ".dng",
    ".cr2",
    ".cr3",
    ".nef",
    ".arw",
    ".orf",
    ".rw2",
    ".raf",
}

# Priority EXIF tags: (exiftool tag, English label as tr() key, formatter).
# exiftool runs in human-readable mode, so most values are already formatted.
_EXIF_PRIORITY = [
    ("Model", "Camera", None),
    ("Make", "Make", None),
    ("LensModel", "Lens", None),
    ("FNumber", "Aperture", lambda v: f"f/{v}"),
    ("ExposureTime", "Shutter speed", lambda v: f"{v} s"),
    ("ISO", "ISO", None),
    ("FocalLength", "Focal length", None),
    ("FocalLengthIn35mmFormat", "Focal length (35 mm eq.)", None),
    ("ExposureProgram", "Exposure program", None),
    ("ExposureCompensation", "Exposure compensation", lambda v: f"{v} EV"),
    ("MeteringMode", "Metering mode", None),
    ("Flash", "Flash", None),
    ("WhiteBalance", "White balance", None),
    ("DateTimeOriginal", "Taken", None),
    ("Software", "Software", None),
    ("Orientation", "Orientation", None),
    ("ColorSpace", "Color space (EXIF)", None),
]

# exiftool groups not worth showing twice
_SKIP_GROUPS = {"File", "System", "ExifTool", "SourceFile"}
_SKIP_TAGS = {"ThumbnailImage", "PreviewImage", "ThumbnailOffset", "ThumbnailLength"}


def _pillow_section(path: Path) -> Section:
    """Basic data via Pillow; returns an empty section for a broken image."""
    sec = Section(tr("Image"))
    try:
        from PIL import Image

        with Image.open(path) as img:
            sec.add(tr("Resolution"), f"{img.width} × {img.height}")
            sec.add(tr("Format"), img.format)
            sec.add(tr("Color mode"), img.mode)
            if "icc_profile" in img.info:
                sec.add(tr("ICC profile"), tr("yes (embedded)"))
            # For GIF/WebP, n_frames iterates over every frame —
            # a crafted file could tie up a worker thread for minutes.
            if img.format not in ("GIF", "WEBP"):
                frames = getattr(img, "n_frames", 1)
                if frames > 1:
                    sec.add(tr("Frames"), frames)
            dpi = img.info.get("dpi")
            if dpi:
                sec.add("DPI", f"{dpi[0]:g} × {dpi[1]:g}")
        return sec
    except Exception:
        return sec


def _exiftool_sections(path: Path) -> list[Section]:
    # -c "%+.6f": GPS coordinates in signed decimal degrees (for the map link)
    output = run_tool(["exiftool", "-json", "-G", "-c", "%+.6f", "--", str(path)], timeout=20)
    if output is None:
        return []
    try:
        data = json.loads(output)[0]
    except (json.JSONDecodeError, IndexError):
        return []

    # Split "Group:Tag" -> value entries into groups
    grouped: dict[str, dict[str, object]] = {}
    for full_key, value in data.items():
        if ":" in full_key:
            group, tag = full_key.split(":", 1)
        else:
            group, tag = tr("Other"), full_key
        if group in _SKIP_GROUPS or tag in _SKIP_TAGS:
            continue
        grouped.setdefault(group, {})[tag] = value

    sections: list[Section] = []

    # EXIF section with the priority tags
    exif_tags = grouped.pop("EXIF", {})
    maker = grouped.pop("MakerNotes", {})
    if exif_tags or maker:
        sec = Section("EXIF")
        merged = {**maker, **exif_tags}
        for tag, label, fmt in _EXIF_PRIORITY:
            if tag in merged:
                value = merged.pop(tag)
                try:
                    sec.add(tr(label), fmt(value) if fmt else value)
                except (ValueError, ZeroDivisionError, TypeError):
                    sec.add(tr(label), value)
        if sec.fields:
            sections.append(sec)
        if merged:
            other = Section(tr("Other EXIF"))
            for tag in sorted(merged):
                other.add(humanize_key(tag), merged[tag])
            sections.append(other)

    # GPS section with an Apple Maps link
    composite = grouped.pop("Composite", {})
    lat, lon = composite.get("GPSLatitude"), composite.get("GPSLongitude")
    if lat is not None and lon is not None:
        gps = Section("GPS")
        lat_f: float | None
        lon_f: float | None
        try:
            lat_f, lon_f = float(str(lat)), float(str(lon))
            gps.add(tr("Latitude"), f"{lat_f:.6f}")
            gps.add(tr("Longitude"), f"{lon_f:.6f}")
        except (TypeError, ValueError):
            lat_f = lon_f = None
            gps.add(tr("Latitude"), lat)
            gps.add(tr("Longitude"), lon)
        alt = composite.get("GPSAltitude")
        if alt is not None:
            # exiftool returns e.g. "130.5 m Above Sea Level".
            match = re.match(r"([-+]?\d+(?:\.\d+)?)", str(alt))
            if match:
                value = float(match.group(1))
                if "below" in str(alt).lower():
                    value = -value
                gps.add(tr("Altitude"), f"{value:.1f} m")
            else:
                gps.add(tr("Altitude"), alt)
        if lat_f is not None:
            gps.add(tr("Map"), f"https://maps.apple.com/?ll={lat_f:.6f},{lon_f:.6f}")
        sections.append(gps)

    # Remaining groups (ICC_Profile, XMP, IPTC, PNG...)
    for group in sorted(grouped):
        tags = grouped[group]
        if not tags:
            continue
        sec = Section(group.replace("_", " "))
        for tag in sorted(tags):
            sec.add(humanize_key(tag), tags[tag])
        sections.append(sec)

    return sections


def _pillow_exif_fallback(path: Path) -> list[Section]:
    """Simple EXIF from Pillow when exiftool is unavailable."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        with Image.open(path) as img:
            raw = img.getexif()
    except Exception:
        return []
    if not raw:
        return []
    sec = Section(tr("EXIF (basic)"))
    for tag_id, value in raw.items():
        name = TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            continue
        sec.add(humanize_key(name), value)
    sec.add(tr("Tip"), tr("Install exiftool for full EXIF data: brew install exiftool"))
    return [sec]


def extract(path: Path) -> list[Section]:
    sections: list[Section] = []
    pillow_sec = _pillow_section(path)
    if pillow_sec.fields:
        sections.append(pillow_sec)

    if shutil.which("exiftool"):
        sections += _exiftool_sections(path)
    else:
        sections += _pillow_exif_fallback(path)

    return sections
