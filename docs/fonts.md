# Font Installation Guide

Two fonts are required to render hymn files correctly:

| Purpose      | Font               | Source                                             |
|--------------|--------------------|----------------------------------------------------|
| Melody line  | **MusiQwik**       | https://www.fontspace.com/musiqwik-font-f3722      |
| Lyrics       | **OpenDyslexic Mono** | https://opendyslexic.org/                       |

Both fonts must be installed on any machine used to **create** or **display**
hymn slides.  Install them before opening any `.potx`, `.otp`, `.pptx`,
or `.html` file produced by this project.

---

## MusiQwik

© 2000 Robert Allgeyer.  Free for personal and educational use.

### Windows

1. Download the `.zip` from the FontSpace link above and extract it.
2. Right-click `musiqwik.ttf` → **Install** (installs for current user)  
   or right-click → **Install for all users** (requires admin).
3. No reboot required; restart any open presentation software.

### macOS

1. Download and extract the `.zip`.
2. Double-click `musiqwik.ttf` → **Install Font** in Font Book.
3. Restart any open presentation software.

### Linux (all major distributions)

```bash
mkdir -p ~/.local/share/fonts
cp musiqwik.ttf ~/.local/share/fonts/
fc-cache -fv
```

Verify installation:
```bash
fc-list | grep -i musiqwik
```

---

## OpenDyslexic Mono

Open-source font designed for readers with dyslexia.
License: BitStream Vera Fonts copyright; see https://opendyslexic.org/

### Windows

1. Download the latest release ZIP from https://github.com/antijingoist/opendyslexic/releases
2. Locate `OpenDyslexicMono-Regular.otf` (and optionally Bold, Italic variants).
3. Right-click each `.otf` file → **Install** or **Install for all users**.

### macOS

1. Download the release ZIP and extract it.
2. Double-click `OpenDyslexicMono-Regular.otf` → **Install Font**.
3. Repeat for Bold and Italic variants if desired.

### Linux

```bash
mkdir -p ~/.local/share/fonts
cp OpenDyslexicMono-Regular.otf ~/.local/share/fonts/
fc-cache -fv
```

Verify:
```bash
fc-list | grep -i "opendyslexic"
```

---

## Verifying Fonts in LibreOffice

1. Open LibreOffice Writer or Impress.
2. Click in a text box and type a few characters.
3. In the font name dropdown, type `Musiqwik` — it should appear in the list.
4. Repeat for `OpenDyslexic Mono`.

If a font does not appear after installation, restart LibreOffice fully
(including the Quick Starter on Windows/Linux).

---

## Verifying Fonts in PowerPoint / Microsoft 365

1. Open a blank presentation.
2. Insert a text box and click inside it.
3. In the **Home** tab → **Font** dropdown, search for `Musiqwik`.
4. Repeat for `OpenDyslexic Mono`.

If a font is missing, ensure it was installed **for the current user** or
**for all users**, then restart PowerPoint.

---

## Scripted Output (hymn_to_presentation.py)

When using `hymn_to_presentation.py`, the fonts must be installed before
rendering:

- **HTML output**: fonts are referenced by name; the browser/OS must have
  them installed, or add `@font-face` rules pointing to the font files.
- **PDF output**: fonts are embedded by Playwright/Chromium at render time;
  the fonts must be installed on the machine running the script.
- **PPTX output**: font names are embedded in the file; the fonts must be
  installed on any machine that opens the resulting `.pptx`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Melody line shows garbled boxes or wrong characters | MusiQwik not installed or wrong font applied | Install font; verify text box uses MusiQwik |
| Lyrics show in a generic monospace font | OpenDyslexic Mono not installed | Install font |
| Font appears in OS but not in PowerPoint | PowerPoint caches the font list | Close PowerPoint fully and reopen |
| LibreOffice shows font name but renders wrong glyphs | Wrong font variant selected | Select the exact name `Musiqwik` (no variant suffix) |
