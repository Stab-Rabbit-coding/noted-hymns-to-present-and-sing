# ProPresenter — Template Setup Notes

ProPresenter 6 and 7 (Renewed Vision) can display hymn slides with MusiQwik
melody notation and OpenDyslexic Mono lyrics once the fonts are installed and
a theme is configured.

---

## Prerequisites

Install both fonts on the Mac or Windows machine running ProPresenter before
proceeding.  See `docs/fonts.md` for platform-specific instructions.

---

## Creating a Hymn Theme (ProPresenter 7)

### 1. Open the Theme Editor

- Go to **Library** → **Themes** → click **+** (New Theme).
- Name the theme `Hymn` or `Hymn — MusiQwik`.

### 2. Configure the Slide Background

- Set **Background** → **Color** → `#1a1a2e` (dark navy) or solid black
  `#000000`, depending on your projection preference.

### 3. Add the Melody Text Element

- Click **Add Element** → **Text**.
- Rename the element `Melody`.
- Set **Font** → `Musiqwik`, size **38–44 pt**, color **#F0E68C** (gold) or white.
- Position the box in the **upper third** of the slide
  (approximately top 30 % of the slide area).
- Set alignment to **Left**.

### 4. Add the Lyrics Text Element

- Click **Add Element** → **Text**.
- Rename the element `Lyrics`.
- Set **Font** → `OpenDyslexic Mono`, size **28–36 pt**, color **#E4E4E4**
  (light gray) or white.
- Position the box in the **lower two-thirds** of the slide.
- Set alignment to **Left**.
- Enable **Word Wrap**.

### 5. Save the Theme

- Click **Save**.  The theme is now available for any presentation.

---

## Building a Hymn Presentation

For each hymn:

1. Create a new **Presentation** in ProPresenter.
2. Apply the `Hymn` theme.
3. For each slide, paste:
   - The MusiQwik characters into the **Melody** text element.
   - The corresponding lyric line(s) into the **Lyrics** text element.

You can use the HTML output from `hymn_to_presentation.py` as a reference to
see how many lines belong on each slide:

```bash
python3 hymn_to_presentation.py --file hymns/7.9_The_Word_of_God/A_Mighty_Fortress_Is_Our_God --format html
```

Open the resulting `.html` file in a browser to preview the slide layout,
then recreate the same groupings in ProPresenter.

---

## ProPresenter 6 Notes

The workflow is the same; the UI labels differ slightly:

- Theme editor is under **Preferences** → **Themes**.
- Text elements are called **Text Boxes**.
- Font settings are in the **Inspector** panel on the right.

---

## Live Display Tips

- Use **Stage Display** to show the next slide's lyrics to the worship leader
  without projecting them to the congregation.
- Set the **Slide Transition** to **Cut** (no fade) to avoid blurring the
  MusiQwik notation during transitions.
- Test the MusiQwik font rendering on the actual projection system before the
  service — some projectors render sub-pixel fonts differently than monitors.

---

## Importing from HTML (alternative workflow)

ProPresenter 7 can import from a variety of sources.  While it cannot import
HTML directly, you can:

1. Generate the HTML with `hymn_to_presentation.py --format html`.
2. Open the HTML in a browser and use it as a reference while manually
   building the ProPresenter presentation.
3. Alternatively, generate a PPTX (`--format pptx`) and import it into
   ProPresenter via **File** → **Import** → **PowerPoint**.

Note: the PPTX import preserves font names but may not render MusiQwik
characters until the font is installed on the ProPresenter machine.
