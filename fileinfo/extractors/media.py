"""Videó- és audiofájlok adatai ffprobe-bal (JSON kimenet)."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from ..i18n import tr
from .base import (
    Section,
    format_bitrate,
    format_duration,
    format_size,
    humanize_key,
    language_name,
    run_tool,
)

VIDEO_EXTENSIONS = {
    ".mp4", ".m4v", ".mkv", ".avi", ".mov", ".webm", ".ts", ".m2ts",
    ".mts", ".mpg", ".mpeg", ".vob", ".wmv", ".flv", ".3gp", ".ogv",
}
AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".m4b", ".aac", ".ogg", ".oga", ".opus",
    ".wav", ".aiff", ".aif", ".wma", ".ape", ".alac", ".dsf", ".amr",
}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

# Címkék, amelyeket előre sorolunk az audio "Címkék" szekcióban.
_PRIORITY_TAGS = [
    ("title", "Title"),
    ("artist", "Artist"),
    ("album", "Album"),
    ("album_artist", "Album artist"),
    ("track", "Track number"),
    ("disc", "Disc"),
    ("date", "Year / date"),
    ("genre", "Genre"),
    ("composer", "Composer"),
    ("publisher", "Publisher"),
    ("comment", "Comment"),
    ("encoder", "Encoder"),
]


def _fps(stream: dict) -> str | None:
    rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if not rate or rate in ("0/0", "N/A"):
        return None
    try:
        value = float(Fraction(rate))
    except (ValueError, ZeroDivisionError):
        return None
    if value <= 0:
        return None
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{text} fps"


def _stream_lang(stream: dict) -> str | None:
    lang = (stream.get("tags") or {}).get("language")
    return language_name(lang) if lang else None


def _dispositions(stream: dict) -> str | None:
    disp = stream.get("disposition") or {}
    names = {
        "default": tr("default"),
        "forced": tr("forced"),
        "hearing_impaired": tr("hearing impaired"),
        "visual_impaired": tr("visually impaired"),
        "comment": tr("commentary"),
    }
    active = [label for key, label in names.items() if disp.get(key)]
    return ", ".join(active) if active else None


def _video_stream_section(stream: dict, index: int, attached_pic: bool) -> Section:
    title = tr("Cover art") if attached_pic else f'{tr("Video stream")} #{index}'
    sec = Section(title)
    sec.add(tr("Codec"), stream.get("codec_long_name") or stream.get("codec_name"))
    sec.add(tr("Profile"), stream.get("profile"))
    w, h = stream.get("width"), stream.get("height")
    if w and h:
        sec.add(tr("Resolution"), f"{w} × {h}")
    sec.add(tr("Aspect ratio"), stream.get("display_aspect_ratio"))
    if not attached_pic:
        sec.add(tr("Frame rate"), _fps(stream))
    sec.add(tr("Pixel format"), stream.get("pix_fmt"))
    bits = stream.get("bits_per_raw_sample")
    if bits and bits != "N/A":
        sec.add(tr("Bit depth"), f"{bits} bit")
    if stream.get("bit_rate"):
        sec.add(tr("Bitrate"), format_bitrate(float(stream["bit_rate"])))
    sec.add(tr("Color space"), stream.get("color_space"))
    sec.add(tr("Color transfer"), stream.get("color_transfer"))
    sec.add(tr("Color primaries"), stream.get("color_primaries"))
    sec.add(tr("Language"), _stream_lang(stream))
    sec.add(tr("Title"), (stream.get("tags") or {}).get("title"))
    sec.add(tr("Flags"), _dispositions(stream))
    return sec


def _audio_stream_section(stream: dict, index: int) -> Section:
    sec = Section(f'{tr("Audio stream")} #{index}')
    sec.add(tr("Codec"), stream.get("codec_long_name") or stream.get("codec_name"))
    sec.add(tr("Profile"), stream.get("profile"))
    sec.add(tr("Language"), _stream_lang(stream))
    channels = stream.get("channels")
    layout = stream.get("channel_layout")
    if channels:
        sec.add(tr("Channels"), f"{channels} ({layout})" if layout else str(channels))
    if stream.get("sample_rate"):
        sec.add(tr("Sample rate"), f"{int(stream['sample_rate']):,} Hz".replace(",", " "))
    bits = stream.get("bits_per_raw_sample") or stream.get("bits_per_sample")
    if bits and str(bits) not in ("0", "N/A"):
        sec.add(tr("Bit depth"), f"{bits} bit")
    if stream.get("bit_rate"):
        sec.add(tr("Bitrate"), format_bitrate(float(stream["bit_rate"])))
    sec.add(tr("Title"), (stream.get("tags") or {}).get("title"))
    sec.add(tr("Flags"), _dispositions(stream))
    return sec


def _subtitle_stream_section(stream: dict, index: int) -> Section:
    sec = Section(f'{tr("Subtitle stream")} #{index}')
    sec.add(tr("Format"), stream.get("codec_long_name") or stream.get("codec_name"))
    sec.add(tr("Language"), _stream_lang(stream))
    sec.add(tr("Title"), (stream.get("tags") or {}).get("title"))
    sec.add(tr("Flags"), _dispositions(stream))
    return sec


def _container_section(fmt: dict) -> Section:
    sec = Section(tr("Container"))
    sec.add(tr("Format"), fmt.get("format_long_name") or fmt.get("format_name"))
    if fmt.get("duration"):
        sec.add(tr("Duration"), format_duration(float(fmt["duration"])))
    if fmt.get("bit_rate"):
        sec.add(tr("Overall bitrate"), format_bitrate(float(fmt["bit_rate"])))
    if fmt.get("size"):
        sec.add(tr("Size"), format_size(int(fmt["size"])))
    streams = fmt.get("nb_streams")
    if streams:
        sec.add(tr("Stream count"), streams)
    return sec


def _tags_section(fmt: dict, streams: list[dict]) -> Section | None:
    """Konténer- és stream-címkék összegyűjtve (audio fájlok metaadatai)."""
    tags: dict[str, str] = {}
    for source in [fmt] + streams:
        for key, value in (source.get("tags") or {}).items():
            tags.setdefault(key.lower(), str(value))

    # A sáv-specifikus technikai címkék nem ide valók.
    for noise in ("language", "handler_name", "vendor_id", "creation_time",
                  "major_brand", "minor_version", "compatible_brands"):
        tags.pop(noise, None)
    if not tags:
        return None

    sec = Section(tr("Tags"))
    for key, label in _PRIORITY_TAGS:
        if key in tags:
            sec.add(tr(label), tags.pop(key))
    for key in sorted(tags):
        sec.add(humanize_key(key), tags[key])
    return sec if sec.fields else None


def extract(path: Path) -> list[Section]:
    output = run_tool([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", "-show_chapters", str(path),
    ], timeout=30)

    def _hint() -> list[Section]:
        hint = Section(tr("Media"))
        hint.add(tr("Warning"), tr("ffprobe is unavailable or could not read the file. Install: brew install ffmpeg"))
        return [hint]

    if output is None:
        return _hint()
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return _hint()

    sections: list[Section] = []
    fmt = data.get("format") or {}
    streams = data.get("streams") or []

    sections.append(_container_section(fmt))

    is_audio_file = path.suffix.lower() in AUDIO_EXTENSIONS
    if is_audio_file:
        tags = _tags_section(fmt, streams)
        if tags:
            sections.append(tags)

    counters = {"video": 0, "audio": 0, "subtitle": 0}
    for stream in streams:
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            attached = bool((stream.get("disposition") or {}).get("attached_pic"))
            sections.append(_video_stream_section(stream, counters["video"], attached))
            if not attached:
                counters["video"] += 1
        elif codec_type == "audio":
            sections.append(_audio_stream_section(stream, counters["audio"]))
            counters["audio"] += 1
        elif codec_type == "subtitle":
            sections.append(_subtitle_stream_section(stream, counters["subtitle"]))
            counters["subtitle"] += 1

    chapters = data.get("chapters") or []
    if chapters:
        sec = Section(tr("Chapters"))
        for i, ch in enumerate(chapters):
            title = (ch.get("tags") or {}).get("title") or f'{tr("Chapter")} {i + 1}'
            start = ch.get("start_time")
            label = format_duration(float(start)) if start else "?"
            sec.add(f"{i + 1}. {title}", label)
        sections.append(sec)

    return sections
