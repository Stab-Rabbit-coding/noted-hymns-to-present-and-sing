# noted-hymns-to-present-and-sing — Implementation Guide

## Purpose

Text-based hymns with melody notation for presentation slides during divine services
(YouTube broadcasts, overhead projection). Congregations need melody lines, not only lyrics.

## Core Requirements

- **Text-based** — plain text files, not images
- **Cross-platform** — Linux, Windows, macOS
- **Presentation-compatible** — PowerPoint, LibreOffice Draw, ProPresenter, EasyWorship, OBS

---

## Fonts (v0.1)

| Content | Font | Source |
|---------|------|--------|
| Musical notation (melody line) | Musiqwik | https://www.fontspace.com/musiqwik-font-f3722 (© 2000 Robert Allgeyer) |
| Lyrics | OpenDyslexic Mono | https://opendyslexic.org/ |

Both fonts must be installed on any system used to create or render the presentation files.
In presentation software, apply Musiqwik to the melody text box and OpenDyslexic Mono to
the lyrics text box.

---

## Source Material

- **Primary source**: Open Hymnal Project — http://openhymnal.org
  - ABC notation files: `openhymnal.org/Abc/<filename>.abc`
- **Repertoire scope**: Liturgy and hymns from the Lutheran Service Book (LSB), published by
  Concordia Publishing House, but drawn only from public domain or royalty-free authorized sources
- **Copyright rule**: Include only items where the **words, music, AND setting** are all public
  domain or explicitly licensed for free reproduction without royalties

---

## File Naming Convention

`<Title_Words_Abbreviated>` — plain text file, no extension, underscores for spaces.

Examples:
```
A_Mighty_Fortress_Trusty_Shield
Beautiful_Savior
Now_Thank_We_All_Our_God
```

Match the first distinctive words of the title. Use the English title even for Latin or German
originals.

---

## File Structure

Every hymn file uses this exact three-section layout:

```
<Full Hymn Title>

# Melody

## ABC
<ABC notation — see Melody Encoding below>

## Musiquik
<ASCII that, when rendered in Musiquik font, matches the ABC melody and can be copied into presentation software>

#Lyrics
<All verses, continuous prose. Verse numbers inline: "2.", "3.", "4.">

#Citations and References

Words: <Author, Year. Translation credit if applicable.>
Music: '<Tune name>' <Composer, Year.>
Setting: <Setting source, Year.>
copyright: <Status — public domain or license statement>

<Source URL>
```

---

## Melody Encoding

### Format: ABC Notation

Store the melody as ABC notation in the `# Melody` section. ABC is the source format
used by the Open Hymnal Project and is the authoritative reference for each hymn's tune.

```
X:1                  — tune index (always 1 per file)
T:Title              — tune title
C:Composer, Year     — composer and date
S:Source             — source attribution
M:4/4                — meter  (C = common/4/4, C| = cut time, 3/4, 6/8, etc.)
L:1/4                — default note length
Q:1/4=88             — tempo (optional)
K:D                  — key signature (D = D major, Dm = D minor, G, etc.)
```

**Pitch names**: `C D E F G A B` (middle octave, uppercase); `c d e f g a b` (octave above)
`C,` or `D,` = octave below middle.

**Note lengths**: `D` = default length; `D2` = double; `D4` = quadruple; `D/` = half default length.

**Sharps/flats**: `^F` = F#; `_B` = Bb; `=B` = B natural.

**Barlines**: `|`   **Repeats**: `|:` … `:|`   **Double barline**: `||`

### Rendering for Presentation

ABC notation stored in the file is the reference representation. To render in presentation software:

1. Open the ABC source at the Open Hymnal Project URL in the `#Citations and References` section
2. Use an ABC-to-image converter (e.g., abcjs, abc2svg, MuseScore) to generate a staff image
   for visual reference while manually encoding the melody
3. Apply the Musiqwik font to the melody text box in the presentation file
4. Follow the Musiqwik character table to encode each note and staff element

---

## Lyrics Format

- All verses in a single continuous text block (no hard line breaks within a verse)
- Verse numbers inline at the start of each new verse: `2.`, `3.`, `4.`
- Preserve historical orthography present in the public domain source
- Verse 1 has no leading number

### Refrains, Choruses, Responses, and Antiphons

Repeating lyrical segments are written **once** at the bottom of the `#Lyrics`
block and referenced inline wherever they are sung.  This prevents file bloat
and keeps the structure clear for presentation.

**Inline reference marker** — placed after each verse or invocation where the
segment is sung:

```
[Refrain]    [Chorus]    [Response]    [Antiphon]
```

**Labeled definition** — appears once, after a blank line, at the end of the
`#Lyrics` block:

```
Refrain: <full text of the refrain>
Chorus: <full text of the chorus>
Response: <congregational response text>
Antiphon: <antiphon text>
```

Only the first labeled definition in the block is parsed by the script;
subsequent ones may appear but will not be extracted automatically.

**Strophic hymn with refrain** (e.g. *Eternal Father, Strong to Save*):

```
#Lyrics
Eternal Father, strong to save, Whose arm hath bound the restless wave...  [Refrain]  2. O Christ, whose voice the waters heard...  [Refrain]  3. O Holy Spirit, who didst brood...  [Refrain]  4. O Trinity of love and power...  [Refrain]

Refrain: O hear us when we cry to Thee For those in peril on the sea.
```

**Litanic canticle with repeating response** (e.g. *Benedicite, Omnia Opera*):

```
#Lyrics
O all ye works of the Lord, bless ye the Lord: [Refrain]  O ye angels of the Lord, bless ye the Lord: [Refrain]  O ye heavens, bless ye the Lord: [Refrain]  ...

Refrain: praise him, and magnify him for ever.
```

**Liturgical call-and-response** (e.g. *Salutation and Response*):

```
#Lyrics
The Lord be with you.

Response: And also with you.
```

The `abc_to_musiqwik.py` script recognises these conventions:
- `[Refrain]` (and its variants) at the end of a verse does not trigger the
  "abrupt ending" warning, since `]` is a sentence-final character.
- Word counts for canticle/creed completeness checks exclude the labeled
  segment text so that a short antiphon does not skew the analysis.
- When creating a hymn file with `--url`, the script automatically detects
  repeating trailing text across verses and formats the `#Lyrics` block with
  `[Refrain]` markers and a `Refrain:` definition.

---

## ABC-to-MusiQwik Workflow (Repeatable for Every Song)

Use `abc_to_musiqwik.py` for every hymn to produce the MusiQwik presentation string.
Run it any time the `## ABC` subsection changes.

### Step 1 — Obtain the ABC source

Fetch the ABC file from the Open Hymnal Project:

```
https://openhymnal.org/Abc/<Hymn_File_Name>.abc
```

The filename follows the pattern visible in `#Citations and References` (e.g.
`Eternal_Father_Strong_To_Save-Melita.abc`).  Paste the ABC header and body
into the `## ABC` subsection under `# Melody` in the hymn file.

### Step 2 — Run the converter

```
python3 abc_to_musiqwik.py --file <path/to/hymn_file>
```

The script reads the `## ABC` subsection, converts the notation to MusiQwik font
characters, prints the result to stdout, and **saves it directly to the
`## Musiquik` subsection** of the same file.  Warnings about out-of-range notes
or unsupported durations go to stderr.

Example (from the repo root):

```
python3 abc_to_musiqwik.py --file hymns/7.13_The_Church_and_Ministry/Eternal_Father_Strong_to_Save
python3 abc_to_musiqwik.py --file hymns/7.10_Holy_Baptism/I_Bind_Unto_Myself_Today
```

### Step 3 — Copy into presentation software

Open the hymn file and copy the content of the `## Musiquik` section.  Paste it
into the melody text box in your slide and apply the **MusiQwik** font.  The
characters render as staff notation with clef, time signature, notes, and
barlines already encoded.

### Step 4 — Verify against the rendered ABC

Open the `## ABC` source at `https://abcjs.net/abcjs-editor.html` to get a
visual staff reference.  Compare it with the MusiQwik rendering in your slide.
Adjust any note flagged by a stderr warning by editing the melody text box
directly in the presentation software.

### Workflow notes

- Notes outside the MusiQwik range A3–A5 are skipped with a warning — transpose
  the ABC key if the melody sits too high or low for the font's staff.
- Dotted notes are approximated to the nearest supported duration; add the dot
  manually in the presentation text box after pasting.
- The script also accepts stdin: `python3 abc_to_musiqwik.py < hymn_file`
  (stdin mode prints to stdout only; it does not write back to a file).

---

## Adding a New Hymn — Checklist

1. Confirm all three components are public domain: words, music, setting
2. Find the ABC source at Open Hymnal Project or equivalent
3. Create the hymn file under `hymns/<section_dir>/` using the naming convention
4. Populate the `## ABC` subsection under `# Melody` with ABC notation
5. Run `python3 abc_to_musiqwik.py --file <hymn_file>` — this saves the output to `## Musiquik` automatically; confirm no unexpected warnings
6. Populate `#Lyrics` with all verses
7. Populate `#Citations and References` with full attribution and source URL
8. Mark the item Done in `TODO.md`

---

## Verification Checklist

- [ ] File named correctly (underscores, no extension)
- [ ] All three section headers present (`# Melody`, `#Lyrics`, `#Citations and References`)
- [ ] ABC notation header fields complete (X, T, C, S, M, L, K)
- [ ] All verses included
- [ ] Citations complete: words, music, setting, copyright, source URL
- [ ] Item added to / updated in `TODO.md`
- [ ] ABC parses without errors (test at https://abcjs.net/abcjs-editor.html or similar)

---

## Repository Layout

Hymn files are organised into a directory tree that mirrors the TODO section
numbers, making them easy to locate by liturgical category.

```
/
├── CLAUDE.md                             ← this file (implementation guide)
├── README.md                             ← project overview
├── TODO.md                               ← work breakdown structure
├── abc_to_musiqwik.py                    ← ABC-to-MusiQwik converter script
├── A_Mighty_Fortress_Trusty_Shield       ← legacy root-level file (7.9)
└── hymns/
    ├── 7.10_Holy_Baptism/
    │   └── I_Bind_Unto_Myself_Today
    ├── 7.13_The_Church_and_Ministry/
    │   └── Eternal_Father_Strong_to_Save
    └── <additional section dirs…>/
        └── <hymn files named per convention>
```

New hymns go under `hymns/<section_number>_<Section_Name>/`.  Use underscores for
spaces in both directory and file names.  Directory names begin with the
two-digit TODO section number so `ls` orders them numerically.

---

## Copyright Notes for Lutheran Service Book Content

The LSB (2006) contains a mix of ancient, public domain, and modern copyrighted material.
Items that are clearly public domain for this project:

- Medieval and Renaissance Latin/German hymns and chant (pre-1700)
- Martin Luther's hymns and settings (1483–1546)
- 17th–18th century German chorales where the English translation is also pre-1928
- Ancient liturgical texts (Kyrie, Gloria, Sanctus, Agnus Dei, Te Deum, canticles from Scripture)
- Gregorian chant tones

Items that require verification before inclusion:

- Any hymn with a 20th-century translation credit
- Any setting first published after 1927
- Hymns explicitly marked © in the LSB index

When in doubt, cross-reference with the Open Hymnal Project, which only publishes
public domain material sourced from the LSB tradition.
