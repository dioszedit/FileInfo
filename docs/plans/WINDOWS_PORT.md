# Windows Port Plan / Windows-támogatási terv

Status: **planned — not yet implemented** · Target: FileInfo **v2.0.0**
Állapot: **terv — még nincs megvalósítva** · Cél: FileInfo **v2.0.0**

---

# English

## 1. Goal and scope

Make FileInfo run natively on Windows 10/11 with the same two-panel PySide6
UI and the same metadata coverage wherever the platform allows it. The
existing macOS behaviour must not change.

**Out of scope for this plan:** a web/HTML UI (may come later, independently),
installer/packaging (PyInstaller/MSIX), and Linux support (most of this plan
would enable it almost for free, but it is not a goal here).

## 2. Where we stand

The architecture already separates extraction from presentation, so most of
the code is portable as-is:

| Component | Portable? | Notes |
|---|---|---|
| PySide6 UI (main_window, metadata_panel, worker, deps_dialog, app) | ✅ yes | Qt is cross-platform, incl. dark mode |
| i18n system + locale JSONs | ✅ yes | no change |
| `extractors/media.py` (ffprobe) | ✅ yes | ffprobe exists on Windows |
| `extractors/image.py` (Pillow + exiftool) | ✅ yes | exiftool exists on Windows |
| `extractors/base.py` (`run_tool`, formatters) | ✅ yes | `shutil.which` works; see console-window note below |
| `extractors/fs.py` | ⚠️ partly | `pwd`/`grp` are Unix-only; `st_birthtime` differs |
| `extractors/spotlight.py` (mdls) | ❌ no | Spotlight is macOS-only |
| `thumbnails.py` | ⚠️ partly | ffmpeg/QImageReader portable; `qlmanage` is macOS-only |
| `deps.py` / install hints | ⚠️ partly | `brew install` → `winget install` |
| Launchers (`run.sh`, `FileInfo.command`) | ❌ no | zsh scripts; need `.bat`/`.ps1` |
| "Reveal in Finder" (`open -R`) | ❌ no | → `explorer /select,` |

Estimated split: ~80% of the code is already platform-independent.

## 3. Design: a small platform layer

Introduce one module, `fileinfo/platform_support.py`, that answers three
questions — everything else keeps importing the same APIs:

```python
IS_MACOS / IS_WINDOWS            # sys.platform flags
system_extractor()               # spotlight (mac) | winprops (win) | None
native_thumbnailer(path)         # qlmanage (mac) | shell thumbnail (win) | None
reveal_in_file_manager(path)     # open -R | explorer /select,
```

The extractor dispatcher (`extractors/__init__.py`) calls
`system_extractor()` instead of importing `spotlight` directly. No UI code
changes except `_reveal_in_finder`.

## 4. Work items

### 4.1 `extractors/fs.py` — make Unix-only parts conditional
- Wrap `import pwd, grp` in `try/except ImportError`.
- Owner on Windows: skip the field in v2.0 (optional later: `pywin32`
  `GetSecurityInfo` for the owner name).
- Created time: `st_birthtime` exists only on macOS/BSD; on Windows use
  `st_ctime` (which *is* creation time there).
- `stat.filemode()` works but is meaningless on NTFS ACLs — keep it, it is
  still informative for the `unix`-style bits Python synthesizes.

### 4.2 New extractor: `extractors/winprops.py` (Spotlight equivalent)
- Source: **Windows Property System** — the same data Explorer's *Details*
  tab shows (`System.Media.Duration`, `System.Photo.FNumber`,
  `System.Music.Artist`, `System.Document.PageCount`, …).
- Implementation: `pywin32`'s `propsys` module —
  `propsys.SHGetPropertyStoreFromParsingName()` + enumerate the store,
  format values with `PropVariantToString`.
- Present it as one **"Windows properties"** section (new tr() key),
  mirroring how the Spotlight section works: skip keys that duplicate the
  General section, humanize the rest (`System.Photo.FNumber` → "Photo f
  number").
- Dependency: `pywin32` — add to requirements with an environment marker so
  macOS installs are unaffected:
  `pywin32>=306; sys_platform == 'win32'`.
- Graceful degradation if `pywin32` import fails (same pattern as exiftool).

### 4.3 `thumbnails.py` — QuickLook replacement
- Keep the existing order: QImageReader → ffmpeg frame / cover art → native.
- Windows native step: `IShellItemImageFactory::GetImage` via `pywin32`
  (gives the same thumbnail Explorer shows, incl. PDFs and documents).
- Fallback remains `QFileIconProvider` (already cross-platform).

### 4.4 `deps.py` / `deps_dialog.py` — per-OS tool lists
- Tool list becomes platform-aware: on Windows drop `mdls`/`qlmanage`,
  add a `pywin32` check (a Python package, verified by import, not PATH).
- Install commands per OS: `brew install ffmpeg` → `winget install
  Gyan.FFmpeg`; `brew install exiftool` → `winget install
  OliverBetz.ExifTool`. The Homebrew help block is shown only on macOS.
- New tr() keys for the winget commands' descriptions (all 4 locales).

### 4.5 UI touches (`main_window.py`)
- `_reveal_in_finder` → `platform_support.reveal_in_file_manager()`
  (`explorer /select,<path>` on Windows; note: Explorer needs backslashes).
- The `/Volumes` hints in guides/status stay macOS-only; drives appear as
  `C:\`, `D:\` roots natively in QFileSystemModel — the "Choose Folder…"
  flow already covers them, docs get a Windows sentence.
- Menu label "Reveal in Finder" → platform-dependent label
  ("Show in Explorer" on Windows; new tr() key chosen at build time).
- Window icon: `icon.png` already works for the Qt window/taskbar; add a
  generated `icon.ico` to `resources/` for future packaging.

### 4.6 `run_tool` polish for Windows
- Add `creationflags=subprocess.CREATE_NO_WINDOW` (Windows only) so ffprobe/
  exiftool calls don't flash console windows.
- exiftool on Windows is `exiftool.exe` — `shutil.which` handles it; no
  change needed, just covered by tests.

### 4.7 Launchers
- `run.bat`: venv check with the same friendly bilingual message, then
  `.venv\Scripts\python.exe -m fileinfo %*`.
- Optional `run.ps1` for PowerShell users.
- README gets a Windows install/run section (`py -3 -m venv .venv`,
  `.venv\Scripts\pip install -r requirements.txt`).

### 4.8 Docs and i18n
- All 5 HTML guides + 2 MD guides: add a short "On Windows" note to the
  install/launch sections and to the helper-tools table.
- New tr() keys: "Windows properties" section title, Explorer menu label,
  winget-based dependency descriptions. All four locale files updated
  together (the key-set consistency check already guards this).

### 4.9 Verification
- **On macOS (regression):** the full existing check suite — CLI on
  MKV/MP3/JPEG-with-GPS/PDF, GUI smoke, locale consistency — must be
  unchanged.
- **On Windows (new):** manual checklist on a Windows 10/11 machine or VM:
  - install flow from README (winget + venv) works from scratch
  - CLI: `run.bat sample.mkv` shows the same media sections as macOS
  - Windows-properties section appears for media/photo/PDF
  - thumbnails: photo, video frame, MP3 cover, PDF (shell thumbnail)
  - Show in Explorer, hidden-files toggle (NTFS hidden attribute), ⌘→Ctrl
    shortcuts, language switch + restart
  - missing-tool path: rename ffprobe away → dependency dialog shows winget
    command
- Optional later: a GitHub Actions `windows-latest` job that runs the
  extractor CLI against the generated sample files (ffmpeg via choco).

## 5. Milestones

1. **M1 — runs on Windows** (fs.py guards, launchers, run_tool no-window,
   reveal-in-Explorer): app starts, media/image/General sections work.
2. **M2 — parity features** (winprops extractor, shell thumbnails, per-OS
   deps dialog): Windows-properties + previews complete.
3. **M3 — polish & docs** (guides, README, icons, verification checklist)
   → tag **v2.0.0**, GitHub release with a "now runs on Windows" note.

Estimated effort: 1–2 days of focused work + access to a Windows machine for
testing. Risks: Property System coverage differs from Spotlight (some fields
exist only on one platform — expected, not a bug); `pywin32` API verbosity
around PROPVARIANT conversion; console encoding (cp1250) for CLI output —
mitigated by `PYTHONIOENCODING=utf-8` in `run.bat`.

---

# Magyar

## 1. Cél és terjedelem

A FileInfo fusson natívan Windows 10/11-en, ugyanazzal a kétpaneles PySide6
felülettel és — ahol a platform engedi — ugyanazzal a metaadat-lefedettséggel.
A meglévő macOS-viselkedés nem változhat.

**Nem része ennek a tervnek:** a webes/HTML felület (később, ettől
függetlenül jöhet), a telepítőcsomag-készítés (PyInstaller/MSIX) és a
Linux-támogatás (a terv nagy része azt is majdnem ingyen hozná, de itt nem
cél).

## 2. Honnan indulunk

Az architektúra már most szétválasztja a kinyerést és a megjelenítést, ezért
a kód nagy része változtatás nélkül hordozható — a részletes táblázatot lásd
fent az angol részben (2. pont). A lényeg: a felület, az i18n, valamint az
ffprobe- és exiftool-alapú extraktorok ✅ mennek; az `fs.py` és a
`thumbnails.py` ⚠️ részben igazítandó; az `mdls` (Spotlight), a `qlmanage`,
a zsh-indítók és az `open -R` ❌ macOS-specifikusak. A kód ~80%-a már most
platformfüggetlen.

## 3. Megoldás: egy vékony platform-réteg

Egyetlen új modul, a `fileinfo/platform_support.py` válaszol minden
platformkérdésre (melyik rendszer-extraktor, melyik natív miniatűr-készítő,
hogyan kell fájlt felfedni a fájlkezelőben) — minden más kód ugyanazokat a
függvényeket hívja, mint eddig. A diszpécser nem közvetlenül a
`spotlight`-ot importálja, hanem a platform-rétegtől kéri el a
rendszer-extraktort.

## 4. Feladatok

- **4.1 `fs.py`**: a Unix-only `pwd`/`grp` import feltételessé tétele;
  Windowson a tulajdonos mező kimarad (v2.0-ban); létrehozási dátumként
  `st_ctime` (Windowson az pont azt jelenti).
- **4.2 Új extraktor: `winprops.py`** — a Spotlight windowsos megfelelője a
  **Windows Property System** (az Intéző „Részletek" fülének adatai:
  `System.Music.Artist`, `System.Photo.FNumber`, `System.Document.PageCount`
  stb.). Megvalósítás `pywin32`-vel (`propsys`); egy új „Windows
  properties" szekcióként jelenik meg, a Spotlight-szekció mintájára
  (duplikátum-szűrés + kulcs-humanizálás). A `pywin32` csak Windowson
  települ: `pywin32>=306; sys_platform == 'win32'` a requirements-ben.
- **4.3 `thumbnails.py`**: a QuickLook helyett az Intéző miniatűr-gyára
  (`IShellItemImageFactory`) — ugyanazt az előnézetet adja, amit az Intéző
  mutat (PDF-re, dokumentumokra is). A sorrend és a fallback (fájlikon)
  marad.
- **4.4 `deps.py`/dialógus**: platformfüggő eszközlista — Windowson
  `mdls`/`qlmanage` helyett `pywin32`-ellenőrzés; `brew install` helyett
  `winget install Gyan.FFmpeg` / `winget install OliverBetz.ExifTool`; a
  Homebrew-segítség csak macOS-en látszik. Új fordítási kulcsok mind a 4
  nyelven.
- **4.5 Felület**: „Megjelenítés Finderben" → Windowson „Show in Explorer"
  (`explorer /select,`); a meghajtók (`C:\`, `D:\`) a fában natívan
  megjelennek; a `resources/` mappába `icon.ico` is készül a meglévő
  ikonból (későbbi csomagoláshoz).
- **4.6 `run_tool`**: Windowson `CREATE_NO_WINDOW` flag, hogy a
  ffprobe/exiftool hívások ne villantsanak fel konzolablakokat.
- **4.7 Indítók**: `run.bat` (ugyanazzal a barátságos, kétnyelvű
  venv-ellenőrzéssel), opcionális `run.ps1`; a README Windows-telepítési
  szekciót kap (`py -3 -m venv .venv`, `.venv\Scripts\...`).
- **4.8 Dokumentáció**: mind az 5 HTML- és 2 MD-útmutató rövid „Windowson"
  megjegyzést kap a telepítés/indítás részeknél és az eszköz-táblázatban.
- **4.9 Ellenőrzés**: macOS-en a teljes meglévő teszt-sor változatlan
  eredménnyel (regresszió); Windowson kézi ellenőrzőlista (telepítés a
  README szerint nulláról, CLI- és GUI-próbák, miniatűrök, Explorer-felfedés,
  rejtett fájlok, nyelvváltás, hiányzó-eszköz útvonal winget-paranccsal).
  Később opcionálisan GitHub Actions `windows-latest` job a CLI-tesztekre.

## 5. Mérföldkövek

1. **M1 — elindul Windowson**: fs-őrfeltételek, indítók, konzolablak-mentes
   `run_tool`, Explorer-felfedés → média/kép/Általános szekciók működnek.
2. **M2 — paritás**: winprops-extraktor, shell-miniatűrök, platformfüggő
   függőség-dialógus.
3. **M3 — csiszolás és dokumentáció** → **v2.0.0** tag és GitHub release.

Becsült ráfordítás: 1–2 nap koncentrált munka + egy Windows-gép vagy VM a
teszteléshez. Kockázatok: a Property System lefedettsége eltér a
Spotlightétól (lesz mező, ami csak az egyiken létezik — ez várt viselkedés);
a `pywin32` PROPVARIANT-kezelése körülményes; a Windows-konzol kódolása
(cp1250) a CLI-kimenetnél — ellenszere a `PYTHONIOENCODING=utf-8` a
`run.bat`-ban.
