# FileInfo — Felhasználói útmutató

A FileInfo egy macOS-re készült fájl-metaadat néző: kiválasztasz egy fájlt a bal oldali fában, és a jobb oldalon azonnal megjelenik minden, ami a fájlról tudható — videóknál a sávok és kodekek, zenéknél a címkék és a borítókép, fényképeknél az EXIF adatok, minden másnál a Spotlight metaadatok.

## Első lépések

### Telepítés

```bash
cd FileInfo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install ffmpeg exiftool
```

### Indítás

| Mód | Hogyan |
|---|---|
| Finderből | Dupla kattintás a `FileInfo.command` fájlra |
| Terminálból | `./run.sh` |
| Parancssori (GUI nélkül) | `./run.sh /útvonal/fájl.mkv` — a metaadatokat a terminálba írja |

Kényelmi tipp — tegyél aliast a `~/.zshrc`-be:
```bash
alias fileinfo='/eleresi/ut/FileInfo/run.sh'
```

## A felület

```
┌──────────────────────────────────────────────────────────┐
│ 📁 Mappa választása  🏠 Saját mappa  🔄 Frissítés  📋 🔍 │  ← eszköztár
├───────────────┬──────────────────────────────────────────┤
│  fájlfa       │              [ előnézeti kép ]           │
│  ▸ Documents  │               fájlnév.mkv                │
│  ▸ Movies     │  ┌ Szűrés a metaadatokban… ┐             │
│  ▾ Music      │  ▾ Általános                             │
│     dal.mp3   │      Név          dal.mp3                │
│  ▸ Pictures   │      Méret        8.13 MB                │
│               │  ▾ Címkék                                │
│               │      Előadó       …                      │
├───────────────┴──────────────────────────────────────────┤
│ 6 szekció betöltve                              ← státusz │
└──────────────────────────────────────────────────────────┘
```

- **Fájlfa (bal)**: a saját mappádból indul. A „Mappa választása…" gombbal bárhová átléphetsz — külső meghajtókhoz válaszd a `/Volumes` mappát.
- **Metaadat-panel (jobb)**: kijelöléskor automatikusan betöltődik (nem kell gombot nyomni). Fent az előnézeti kép, alatta a fájlnév, a szűrőmező és a csoportosított adatok.
- **Szűrőmező**: gépelés közben szűkíti a listát — pl. írd be: `nyelv`, és csak a nyelvi adatok maradnak.
- **Jobb klikk egy soron**: „Érték másolása" / „Sor másolása".
- **Nyelv menü**: a felület nyelve váltható (magyar, angol, német, spanyol, francia); újraindítás után érvényesül.
- **SHA-256 gomb (a panel alján)**: a kijelölt fájl ellenőrzőösszege háttérben számolva, bármekkora fájlra.
- **Sötét és világos mód**: az app automatikusan a rendszer megjelenését követi (Rendszerbeállítások → Megjelenés), élőben vált; külön kapcsoló nincs.
- **Nézet → Rejtett fájlok megjelenítése**: a fa alapból elrejti a pont-kezdetű fájlokat.

### Eszköztár

| Gomb | Mit csinál |
|---|---|
| 📁 Mappa választása… | A fájlfa gyökerének átállítása (külső meghajtó: `/Volumes`) |
| 🏠 Saját mappa | Vissza a saját mappádhoz |
| 🔄 Frissítés (⌘R) | A kijelölt fájl adatainak újraolvasása |
| 📋 Metaadatok másolása | Az összes szekció szövegként a vágólapra |
| 🔍 Megjelenítés Finderben | A kijelölt fájl kijelölése a Finderben |

## Milyen adatokat mutat fájltípusonként

### 🎬 Videó (mp4, mkv, avi, mov, webm…)

Valós példa egy MKV fájlról:

```
=== Konténer ===          Matroska / WebM, 0:05, 230 kb/s, 4 sáv
=== Videó sáv #0 ===      H.264/AVC, 1280 × 720, 16:9, 25 fps, yuv444p, 8 bit
=== Audio sáv #0 ===      AAC (LC), magyar, 1 (mono), 44 100 Hz, alapértelmezett
=== Audio sáv #1 ===      AAC (LC), angol, 1 (mono), 44 100 Hz
=== Felirat sáv #0 ===    SubRip subtitle, magyar
```

Minden sávról külön szekció készül: kodek, nyelv (magyarul kiírva), csatorna-elrendezés (pl. 5.1), bitráta, HDR/színtér-adatok, kényszerített/alapértelmezett jelölők, fejezetek.

### 🎵 Zene / hang (mp3, flac, m4a, ogg, wav…)

Valós példa egy MP3 fájlról:

```
=== Konténer ===       MP2/3 (MPEG audio layer 2/3), 0:03, 202 kb/s
=== Címkék ===         Cím: Minta dal · Előadó: Minta Előadó · Album: Minta Album
                       Év: 2024 · Műfaj: Pop · Kódoló: Lavf
=== Audio sáv #0 ===   MP3, 1 (mono), 44 100 Hz, 192 kb/s
=== Borítókép ===      PNG, 300 × 300
```

A beágyazott **borítókép** az előnézeti területen jelenik meg. Ha a fájlban nincs borító, a fájl ikonja látszik helyette.

### 📷 Kép / fénykép (jpg, png, heic, tiff, RAW…)

Valós példa egy iPhone-nal készült fotóról:

```
=== Kép ===        2048 × 1463, JPEG, RGB, beágyazott ICC profil
=== EXIF ===       Fényképezőgép: iPhone 14 Pro Max
                   Objektív: back triple camera 6.86mm f/1.78
                   Rekesz: f/1.8 · Záridő: 1/1000 s · ISO: 80
                   Gyújtótáv: 6.9 mm (24 mm ekv.) · Program AE
                   Fénymérés: Multi-segment · Vaku: Off, Did not fire
=== GPS ===        Szélesség: -8.439906 · Hosszúság: 115.281236
                   Térkép: https://maps.apple.com/?ll=-8.439906,115.281236
=== XMP, IPTC, ICC Profile… ===   minden további beágyazott adat
```

A GPS szekció **Térkép** sora átmásolható a böngészőbe — az Apple Maps a készítés helyét mutatja. Képernyőképeknél és letöltött képeknél EXIF általában nincs — ilyenkor csak a „Kép" szekció jelenik meg, ez normális.

### 📄 Minden más (PDF, dokumentumok, appok…)

Valós példa egy PDF-ről (Spotlight szekció):

```
Number of pages: 62 · Version: 1.4 · Creator: ReportLab
Content creation date: 2026-04-30 · Security method: None
```

Minden fájlhoz jár az **Általános** szekció (méret, dátumok, jogosultságok, tulajdonos) és a **Spotlight** szekció (amit a macOS indexelt a fájlról). A Spotlight-mezők
nevei angolul jelennek meg — ezek közvetlenül a rendszer kulcsaiból származnak.

## Segédprogramok

A FileInfo külső eszközökre támaszkodik — a **Súgó → Függőségek ellenőrzése…** menüpont mutatja, mi van meg (✅) és mi hiányzik (❌), másolható telepítési paranccsal.

| Eszköz | Mit ad hozzá | Ha hiányzik | Telepítés |
|---|---|---|---|
| ffprobe/ffmpeg | videó/audio sávok, előnézet, borítókép | nincs média-adat és videó-előnézet | `brew install ffmpeg` |
| exiftool | teljes EXIF, GPS, XMP, objektív-adatok | csak alap EXIF (Pillow) | `brew install exiftool` |
| mdls | Spotlight metaadatok | nincs Spotlight szekció | beépített macOS eszköz |
| qlmanage | PDF/dokumentum előnézet | csak fájlikon | beépített macOS eszköz |

Ha a Homebrew sincs telepítve, a függőség-dialógus annak telepítését is elmagyarázza (részletek: [brew.sh](https://brew.sh)).

## GYIK / hibaelhárítás

**Miért nem látok EXIF-et egy képnél?** — Képernyőképek, letöltött/üzenetküldőn kapott képek gyakran nem tartalmaznak EXIF-et (a szolgáltatók törlik). Ez nem hiba.

**Hogyan érem el a pendrive-ot / külső lemezt?** — 📁 Mappa választása… → bal oldalt a Helyek közül a meghajtó, vagy írd be: `/Volumes`.

**A hálózati meghajtón lévő fájl lassan töltődik be.** — A kinyerés a fájl olvasási sebességétől függ; a felület közben nem fagy le, és mindig az utoljára kijelölt fájl adatai jelennek meg.

**Egy fájlnál üres a Spotlight szekció.** — A Spotlight nem indexel minden helyet (pl. ideiglenes mappák, egyes külső meghajtók). A többi szekciót ez nem érinti.

**Elsőre furcsa helyen nyílik az ablak / szétesett a panel.** — Az ablak mérete és az elválasztó pozíciója mentődik; húzd a helyére, és a következő indításkor már úgy nyílik.
