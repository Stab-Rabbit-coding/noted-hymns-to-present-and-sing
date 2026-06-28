# MusiQwik Font — Character Reference

MusiQwik (© 2000 Robert Allgeyer) encodes staff notation as plain text.
Each character includes its surrounding staff lines, so pasting a sequence
of characters produces a continuous notation staff.

Source: `abc_to_musiqwik.py` — the constants below are derived from that
script and are authoritative for this project.

---

## Encoding Formula

```
note_char = chr(DURATION_BASE + PITCH_INDEX)
```

---

## Pitch Index Table

| Index | Note | Description         |
|------:|------|---------------------|
|     0 | A3   | below middle C      |
|     1 | B3   | below middle C      |
|     2 | C4   | middle C            |
|     3 | D4   |                     |
|     4 | E4   |                     |
|     5 | F4   |                     |
|     6 | G4   |                     |
|     7 | A4   | concert A (440 Hz)  |
|     8 | B4   |                     |
|     9 | C5   |                     |
|    10 | D5   |                     |
|    11 | E5   |                     |
|    12 | F5   |                     |
|    13 | G5   |                     |
|    14 | A5   | top of font range   |

Notes outside A3–A5 cannot be represented; `abc_to_musiqwik.py` warns and
skips them.  Transpose the ABC key if the melody sits out of range.

---

## Duration Base Table

| Duration | Base | chr() range |
|----------|-----:|-------------|
| Eighth   |   64 | 64–78       |
| Quarter  |   80 | 80–94       |
| Half     |   96 | 96–110      |
| Whole    |  112 | 112–126     |

---

## Complete Note Character Table

Each cell shows the ASCII character produced by `chr(base + index)`.

### Eighth notes (base 64)

| Pitch | Index | char |
|-------|------:|-----:|
| A3    |     0 | `@`  |
| B3    |     1 | `A`  |
| C4    |     2 | `B`  |
| D4    |     3 | `C`  |
| E4    |     4 | `D`  |
| F4    |     5 | `E`  |
| G4    |     6 | `F`  |
| A4    |     7 | `G`  |
| B4    |     8 | `H`  |
| C5    |     9 | `I`  |
| D5    |    10 | `J`  |
| E5    |    11 | `K`  |
| F5    |    12 | `L`  |
| G5    |    13 | `M`  |
| A5    |    14 | `N`  |

### Quarter notes (base 80)

| Pitch | Index | char |
|-------|------:|-----:|
| A3    |     0 | `P`  |
| B3    |     1 | `Q`  |
| C4    |     2 | `R`  |
| D4    |     3 | `S`  |
| E4    |     4 | `T`  |
| F4    |     5 | `U`  |
| G4    |     6 | `V`  |
| A4    |     7 | `W`  |
| B4    |     8 | `X`  |
| C5    |     9 | `Y`  |
| D5    |    10 | `Z`  |
| E5    |    11 | `[`  |
| F5    |    12 | `\`  |
| G5    |    13 | `]`  |
| A5    |    14 | `^`  |

### Half notes (base 96)

| Pitch | Index | char |
|-------|------:|-----:|
| A3    |     0 | `` ` `` |
| B3    |     1 | `a`  |
| C4    |     2 | `b`  |
| D4    |     3 | `c`  |
| E4    |     4 | `d`  |
| F4    |     5 | `e`  |
| G4    |     6 | `f`  |
| A4    |     7 | `g`  |
| B4    |     8 | `h`  |
| C5    |     9 | `i`  |
| D5    |    10 | `j`  |
| E5    |    11 | `k`  |
| F5    |    12 | `l`  |
| G5    |    13 | `m`  |
| A5    |    14 | `n`  |

### Whole notes (base 112)

| Pitch | Index | char |
|-------|------:|-----:|
| A3    |     0 | `p`  |
| B3    |     1 | `q`  |
| C4    |     2 | `r`  |
| D4    |     3 | `s`  |
| E4    |     4 | `t`  |
| F4    |     5 | `u`  |
| G4    |     6 | `v`  |
| A4    |     7 | `w`  |
| B4    |     8 | `x`  |
| C5    |     9 | `y`  |
| D5    |    10 | `z`  |
| E5    |    11 | `{`  |
| F5    |    12 | `\|` |
| G5    |    13 | `}`  |
| A5    |    14 | `~`  |

---

## Special Characters

| Character | ASCII | Description                        |
|-----------|------:|------------------------------------|
| `&`       |    38 | Treble clef                        |
| `=`       |    61 | Staff segment (full width)         |
| `-`       |    45 | Staff segment (narrow spacer)      |
| `.`       |    46 | Staff + single barline             |
| `)`       |    41 | Staff + final / double barline     |
| `(`       |    40 | Staff + begin-repeat barline       |
| `O`       |    79 | Eighth rest                        |
| `_`       |    95 | Quarter rest                       |
| `o`       |   111 | Half rest                          |
| `;`       |    59 | Whole rest                         |

---

## Time-Signature Characters

Each glyph includes a full staff segment.

| Meter | char | ABC field value |
|-------|------|-----------------|
| Common time (4/4) | `0` (chr 48) | `M:C`   |
| 2/2               | `1` (chr 49) | `M:2/2` |
| 2/4               | `2` (chr 50) | `M:2/4` |
| 3/4               | `3` (chr 51) | `M:3/4` |
| 4/4               | `4` (chr 52) | `M:4/4` |
| 3/2               | `5` (chr 53) | `M:3/2` |
| 6/8               | `6` (chr 54) | `M:6/8` |
| Cut time          | `7` (chr 55) | `M:C\|` |

---

## Presentation Usage

Every MusiQwik string produced by `abc_to_musiqwik.py` begins with:

```
& <time-sig-char> <notes-and-barlines…>
```

1. Copy the content of the `## Musiquik` section from the hymn file.
2. Paste into the melody text box in your slide.
3. Apply the **MusiQwik** font to that text box.
4. Do **not** mix MusiQwik and other fonts in the same text box — each
   character must render in MusiQwik.

### Dotted notes

Dotted durations are approximated to the nearest supported value.
`abc_to_musiqwik.py` emits a warning for each approximated note.
After pasting, locate those positions and manually insert the augmentation
dot using your presentation software's drawing tools.

### Accidentals

MusiQwik has no separate accidental glyphs — accidentals are absorbed into
the diatonic pitch position.  A warning is emitted for chromatic notes.
Add accidental symbols as separate text or drawing objects if needed.

---

## Font Download

- **MusiQwik** by Robert Allgeyer — https://www.fontspace.com/musiqwik-font-f3722
- See `docs/fonts.md` for platform-specific installation instructions.
