# FileInfo — User Guide

FileInfo is a file metadata viewer for macOS: select a file in the tree on the left and the right panel instantly shows everything known about it — streams and codecs for videos, tags and cover art for music, EXIF for photos, Spotlight metadata for everything else.

## Getting started

### Installation

```bash
cd FileInfo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install ffmpeg exiftool
```

### Launching

| Mode | How |
|---|---|
| From Finder | Double-click `FileInfo.command` |
| From Terminal | `./run.sh` |
| Command line (no GUI) | `./run.sh /path/to/file.mkv` — prints metadata to the terminal |

## The interface

- **File tree (left)**: starts at your home folder. Use "Choose Folder…" to go anywhere — pick `/Volumes` for external drives.
- **Metadata panel (right)**: loads automatically on selection. Preview image on top, then file name, filter box and grouped data.
- **Filter box**: narrows the list as you type.
- **Right-click a row**: "Copy value" / "Copy row".
- **Language menu**: switch the UI language (Hungarian, English, German, Spanish, French); takes effect after a restart.
- **SHA-256 button (bottom of the panel)**: computes the selected file's checksum in the background, for any file size.
- **View → Show hidden files**: the tree hides dotfiles by default, like Finder.

### Toolbar

| Button | What it does |
|---|---|
| 📁 Choose Folder… | Change the root of the file tree |
| 🏠 Home Folder | Back to your home folder |
| 🔄 Refresh (⌘R) | Re-read the selected file's metadata |
| 📋 Copy Metadata | All sections as text to the clipboard |
| 🔍 Reveal in Finder | Show the selected file in Finder |

## What data is shown per file type

- **🎬 Video** (mp4, mkv, avi, mov…): container, video streams (resolution, codec, fps, color data), every audio stream with language and channel layout, subtitle streams, chapters.
- **🎵 Music / audio** (mp3, flac, m4a, ogg…): technical data + Tags section (artist, album, year, genre…) + embedded cover art in the preview.
- **📷 Image / photo** (jpg, png, heic, RAW…): resolution, color mode, ICC profile; for photos the full EXIF (camera, lens, aperture, shutter speed, ISO, GPS with an Apple Maps link) plus XMP/IPTC/ICC groups.
- **📄 Everything else** (PDF, documents, apps…): General section (size, dates, permissions) + Spotlight section with whatever macOS indexed.

## Helper tools

**Help → Check Dependencies…** shows what is installed (✅) and what is missing (❌), with copyable install commands.

| Tool | What it adds | Install |
|---|---|---|
| ffprobe / ffmpeg | video/audio streams, previews, cover art | `brew install ffmpeg` |
| exiftool | full EXIF, GPS, XMP, lens data | `brew install exiftool` |
| mdls | Spotlight metadata | built-in macOS tool |
| qlmanage | PDF/document previews | built-in macOS tool |

## FAQ / Troubleshooting

**Why don't I see EXIF for an image?** — Screenshots and downloaded/messaged images usually carry no EXIF; services strip it. Not a bug.

**How do I reach an external drive?** — 📁 Choose Folder… → pick the drive under Locations, or type `/Volumes`.

**The Spotlight section is empty.** — Spotlight doesn't index every location (temp folders, some external drives). Other sections are unaffected.
