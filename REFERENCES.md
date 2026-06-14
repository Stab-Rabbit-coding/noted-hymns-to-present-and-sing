# REFERENCES — Standards and Regulations Catalog
# noted-hymns-to-present-and-sing

Standards, specifications, and regulations governing non-cosmetic design decisions in this
repository. Any design decision with a functional effect (file format, encoding, font
selection for readability, copyright methodology) must trace to an entry here.

Citations elsewhere in the repo reference these entries by identifier (e.g., [REF-1]) and
include the chapter, section, or paragraph of the cited standard to allow efficient auditing.

No fabricated or unverifiable references appear in this repository.

---

## Standards and Specifications

### [REF-1] ABC Notation Standard v2.1

| Field | Value |
|---|---|
| Title | ABC Notation Standard |
| Version | v2.1 |
| Issuing body | Chris Walshaw et al. (community maintained) |
| Verified URL | https://abcnotation.com/wiki/abc:standard:v2.1 |

**Decision governed:** Melody encoding format in the `# Melody` section of all hymn files.

**Used in:** All hymn files (ABC header fields X, T, C, S, M, L, Q, K; note syntax; bar
lines); `CLAUDE.md §Melody Encoding`.

ABC v2.1 is the version in active use by the Open Hymnal Project source files (the primary
source for this repository). The standard defines the complete syntax for tune headers, note
pitch and duration, accidentals, bar lines, repeat markers, and stylesheet directives
(including `%%MIDI`).

---

### [REF-2] RFC 3629 — UTF-8, a transformation format of ISO 10646

| Field | Value |
|---|---|
| Title | UTF-8, a transformation format of ISO 10646 |
| RFC | 3629 |
| Date | November 2003 |
| Issuing body | IETF |
| Verified URL | https://www.rfc-editor.org/rfc/rfc3629 |

**Decision governed:** Text encoding of all plain-text files in this repository.

**Used in:** All hymn files; all Markdown documentation files.

Cross-platform compatibility across Linux, Windows, and macOS (`CLAUDE.md §Core
Requirements`) requires a single consistent text encoding. UTF-8 as defined in RFC 3629 §3
satisfies this requirement. Files must be saved without a byte-order mark (BOM); a BOM in a
plain-text file would appear as extraneous characters to ABC parsers and to presentation
software importing the text.

---

## Regulations

### [REF-3] 17 U.S.C. — United States Copyright Law

| Field | Value |
|---|---|
| Title | Copyright Law of the United States and Related Laws |
| Codified at | Title 17, United States Code |
| Issuing body | U.S. Congress; administered by the U.S. Copyright Office |
| Verified URL | https://www.copyright.gov/title17/ |

**Decision governed:** Public domain determination for hymn words, music, and settings.

**Used in:** `CLAUDE.md §Copyright Notes for Lutheran Service Book Content`; `TODO.md §Notes`;
`#Citations and References` in all hymn files.

Relevant provisions:

| Section | Subject |
|---|---|
| 17 U.S.C. § 103 | Derivative works — translations and settings have independent copyright terms |
| 17 U.S.C. § 302 | Duration: works created on or after January 1, 1978 |
| 17 U.S.C. § 303 | Duration: works created before 1978 but first published on or after that date |
| 17 U.S.C. § 304(a) | Duration: works in their first copyright term on January 1, 1978 |
| 17 U.S.C. § 304(b) | Duration of second-term works, extended to 95 years from publication by Pub. L. 105-298 (Sonny Bono Copyright Term Extension Act, 1998) |

**Rule applied in this repository:** Works published in the United States before January 1,
1928 are unambiguously in the public domain (17 U.S.C. § 304(b)). Translations and settings
are treated as derivative works with independent copyright terms (17 U.S.C. § 103); each must
independently qualify as public domain. Pre-1964 works for which copyright was not renewed
after the initial 28-year term entered the public domain upon expiration of that term (under
the Copyright Act of 1909, which governed at the time of publication).

---

## Authoritative Font References

These are not industry standards; they are the authoritative sources for fonts whose
selection constitutes a functional (not merely cosmetic) decision.

### [REF-4] Musiqwik Font

| Field | Value |
|---|---|
| Title | Musiqwik |
| Author | Robert Allgeyer |
| Copyright | © 2000 Robert Allgeyer |
| Verified URL | https://www.fontspace.com/musiqwik-font-f3722 |

**Decision governed:** Font for melody text boxes in presentation files. Musiqwik maps
musical staff elements (notes, clefs, rests, accidentals, bar lines) to specific characters,
making font selection a functional encoding decision, not a cosmetic one. Using any other
font for the melody text box renders the melody text as meaningless characters.

**Used in:** `CLAUDE.md §Fonts (v0.1)`; `CLAUDE.md §Rendering for Presentation`; `README.md`.

The font author's character table is the authoritative reference for which character encodes
which musical symbol. Implementers must consult the Musiqwik documentation distributed with
the font for the complete character map.

---

### [REF-5] OpenDyslexic / OpenDyslexic Mono Font

| Field | Value |
|---|---|
| Title | OpenDyslexic |
| Author | Abelardo Gonzalez |
| Verified URL | https://opendyslexic.org/ |

**Decision governed:** Font for lyrics text boxes. The selection of OpenDyslexic Mono is a
functional accessibility decision: the font uses weighted letter bottoms and unique
letterforms specifically designed to reduce the letter-confusion reading errors associated
with dyslexia. This affects legibility for a portion of the congregation, not merely
aesthetics. See the project site for current license terms.

**Used in:** `CLAUDE.md §Fonts (v0.1)`; `README.md`.

---

## Source Reference

### [REF-6] Open Hymnal Project

| Field | Value |
|---|---|
| Title | Open Hymnal Project |
| Verified URL | http://openhymnal.org |

**Role:** Primary source for ABC notation files and secondary vetting of public domain status.
The Open Hymnal Project publishes only hymns and liturgy whose words, music, and settings are
confirmed public domain or freely licensed, drawing from the Lutheran Service Book tradition.
All ABC source files used in this repository originate from or are cross-referenced against
this project.

**Used in:** `CLAUDE.md §Source Material`; all hymn file `S:` header fields; all hymn file
`#Citations and References` sections.
