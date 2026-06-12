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

<ABC notation — see Melody Encoding below>

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

---

## Adding a New Hymn — Checklist

1. Confirm all three components are public domain: words, music, setting
2. Find the ABC source at Open Hymnal Project or equivalent
3. Create a new file using the naming convention
4. Populate `# Melody` with ABC notation
5. Populate `#Lyrics` with all verses
6. Populate `#Citations and References` with full attribution and source URL
7. Mark the item Done in `TODO.md`

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

```
/
├── CLAUDE.md                      ← this file (implementation guide)
├── README.md                      ← project overview
├── TODO.md                        ← work breakdown structure
├── A_Mighty_Fortress_Trusty_Shield
└── <additional hymn files…>
```

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
