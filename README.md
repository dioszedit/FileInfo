# FileInfo

A file metadata viewer for macOS: detailed data for videos, music, images and any other file in a clean two-panel UI — streams and codecs, music tags with cover art, full EXIF, Spotlight metadata.

Speaks five languages (English, Deutsch, Español, Français, magyar): a language chooser appears on first launch; switch any time in the **Language** menu.

## Features

- 🎬 **Video**: container, video/audio/subtitle streams with codecs, languages, channel layouts, HDR/color data, chapters
- 🎵 **Music**: technical data, tags (artist, album, year, genre…) and embedded cover art shown as the preview
- 📷 **Photos**: resolution, color mode, ICC profile, full EXIF (camera, lens, aperture, shutter speed, ISO) and GPS with an Apple Maps link
- 📄 **Everything else**: file-system details plus whatever macOS Spotlight has indexed (PDFs, documents, apps…)
- 🖼 Preview thumbnails (photo, video frame, album cover, QuickLook), live metadata filter, copy to clipboard, reveal in Finder
- 🌗 Follows the system light/dark appearance

## Install

```bash
# Python 3.10+ required — if you only have Apple's built-in 3.9:
brew install python

git clone https://github.com/dioszedit/FileInfo.git && cd FileInfo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install ffmpeg exiftool   # for full metadata
```

## Run

- From Finder: double-click `FileInfo.command`
- From Terminal: `./run.sh`
- CLI mode (no GUI): `./run.sh /path/to/file.mkv`

Full guide: [docs/USER_GUIDE.md](docs/USER_GUIDE.md) · magyarul: [docs/FELHASZNALOI_UTMUTATO.md](docs/FELHASZNALOI_UTMUTATO.md)

## Contributing a translation

Add one file: `fileinfo/locales/<code>.json` — copy an existing one (e.g. `de.json`), set `"_language_name"` to the language's native name and translate the values. The keys are the English source strings; a missing key simply falls back to English. The app picks the new language up automatically, no code changes needed. Optionally add a translated user guide as `docs/guide_<code>.html` (copy the structure of `guide_en.html`) — languages without one get the English guide.

## Requirements

- macOS, Python 3.10+ (developed on 3.14), PySide6 ≥ 6.10, Pillow
- Optional but recommended: `ffmpeg`/`ffprobe` (media data, previews), `exiftool` (full EXIF) — the built-in **Help → Check Dependencies…** dialog tells you what's missing and how to install it

## License

[MIT](LICENSE)
