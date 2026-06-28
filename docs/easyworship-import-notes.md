# EasyWorship — Import and Template Notes

EasyWorship 6 and 7 (Softouch Development) can display hymn slides with
MusiQwik melody notation and OpenDyslexic Mono lyrics.

---

## Prerequisites

Install both fonts on the Windows PC running EasyWorship before proceeding.
See `docs/fonts.md` for installation instructions.

EasyWorship runs on Windows only.  For cross-platform workflows, generate
slides with `hymn_to_presentation.py` and import the resulting PPTX file.

---

## Importing a PPTX File (recommended)

The fastest way to bring a hymn into EasyWorship is via the PPTX converter:

1. Generate the PPTX from the command line:
   ```
   python3 hymn_to_presentation.py --file hymns/<section>/<Hymn_File> --format pptx
   ```
2. In EasyWorship, go to **Schedule** → **Add Item** → **Presentation**.
3. Browse to the `.pptx` file and click **Open**.
4. EasyWorship embeds the slides as a presentation object in the schedule.

The MusiQwik and OpenDyslexic Mono fonts must be installed for the
characters to render correctly in EasyWorship's preview and output.

---

## Creating a Native EasyWorship Song Entry

To enter hymn text natively (so EasyWorship can manage verse order and
CCLI reporting), use the Song Editor:

### 1. Open the Song Editor

- Go to **Songs** (Library panel) → click **New Song** (+ button).

### 2. Enter Metadata

- **Title**: full hymn title
- **Author**: words author (from the hymn file's `#Citations` section)
- **Copyright**: "Public Domain" or the license statement from the hymn file

### 3. Enter Verses

- Paste the lyrics for each verse into separate verse slots.
- EasyWorship does not display ABC or MusiQwik notation natively; see the
  melody workflow below.

### 4. Apply a Theme with the Correct Fonts

- Go to **Themes** → **New Theme**.
- Set the **Background** to black (`#000000`) or dark navy (`#1a1a2e`).
- Add a **Text Element** for lyrics; set font to `OpenDyslexic Mono`,
  28–36 pt, white or light gray.
- Save the theme as `Hymn` and apply it to the song.

---

## Adding MusiQwik Melody Lines (manual method)

EasyWorship's Song Editor does not natively support a separate melody font
per slide section.  To add MusiQwik notation:

1. Generate the HTML output to preview the melody/lyric pairing:
   ```
   python3 hymn_to_presentation.py --file hymns/<section>/<Hymn_File> --format html
   ```
2. In the Song Editor, create one slide per verse phrase.
3. In each slide, add a second **Text Element** (formatted as MusiQwik) by
   using **Edit Element** → **Text** and manually entering or pasting the
   MusiQwik characters.
4. Set that element's font to `Musiqwik` at 28–38 pt.

This method is labor-intensive; for large repertoires, prefer the PPTX
import workflow.

---

## EasyWorship 6 vs. EasyWorship 7 Differences

| Feature                       | EW 6           | EW 7           |
|-------------------------------|----------------|----------------|
| PPTX import                   | Yes            | Yes            |
| Per-slide font override        | Limited        | Full support   |
| Multi-element theme           | Yes            | Yes            |
| CCLI SongSelect integration   | Yes            | Yes            |

EasyWorship 7 offers more flexible per-element formatting, making it easier
to add a separate MusiQwik text box on each slide.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Melody characters show as boxes or wrong symbols | MusiQwik not installed in Windows | Install MusiQwik font; restart EasyWorship |
| Font shows in font list but doesn't render | OpenType/TrueType conflict | Re-install the font; use the `.ttf` variant if `.otf` fails |
| PPTX import drops the fonts | Fonts not installed on EW machine | Install both fonts before importing |
| Slides look correct in preview but not on output | Output is configured for a different screen | Check **Output** → **Screen** settings; verify fonts on the output display PC |
