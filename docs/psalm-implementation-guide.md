# Gregorian Chant Psalm Implementation Guide

## Overview

This document describes the implementation of Gregorian chant psalm settings (section 8.0 in TODO.md) and the automation workflow for completing all 150 psalms.

## Completed Psalms

The following 6 psalms have been completed with genuine WEB-UE text and
historically-cited tone assignments:

| Psalm | Tone | Antiphon | Tone source |
|-------|------|----------|--------------|
| 1   | 1 | Blessed is the man | Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone I — *Beatus vir qui non abiit* |
| 12  | 4 | Help, LORD | Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone IV — *Salvum me fac, Domine* |
| 18  | 1 | I love you, LORD, my strength | Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone I — *Diligam te, Domine* |
| 25  | 8 | To you, LORD, I lift up my soul | Roman Gradual, Introit for Advent I "Ad te levavi animam meam", Mode VIII |
| 117 | 9 (Tonus Peregrinus) | Praise the LORD, all you nations | Sarum Tonale / St. Dunstan's Plainsong Psalter, Tonus Peregrinus — *Laudate Dominum omnes gentes* |
| 118 | 1 | Give thanks to the LORD | Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone I — *Confitemini Domino* |

File location: `hymns/8.0_Psalm_Settings/Psalm_001` through `Psalm_150` (zero-padded numbering)

## Psalm 18/19 numbering bug (fixed)

An earlier pass generated `Psalm_018` with the text "The heavens declare the
glory of God..." — that is Psalm 19 in the WEB-UE's Hebrew/Protestant
numbering. The root cause is almost certainly a Vulgate/Septuagint vs.
Hebrew/Masoretic numbering mismatch: the Vulgate folds Hebrew Psalms 9 and 10
into a single Psalm 9, shifting every subsequent psalm number down by one, so
Vulgate Psalm 18 ("Caeli enarrant gloriam Dei") corresponds to Hebrew/WEB-UE
Psalm 19. The WEB-UE uses Hebrew numbering throughout, so `Psalm_018` must
contain "I love you, LORD, my strength..." (Diligam te, Domine), not the
"heavens declare" text. This has been corrected; the WEB-UE text is fetched
directly from a verified source (see below) rather than transcribed by hand,
to avoid reintroducing numbering mistakes.

## Text source: WEB-UE via the BibleNLP/ebible GitHub mirror

`ebible.org` and `worldenglish.bible` return HTTP 403 to automated requests
in this environment. The genuine WEB-UE text remains available through the
**BibleNLP/ebible** GitHub mirror (`https://github.com/BibleNLP/ebible`),
which republishes eBible.org's USFM-derived corpora as plain text:

- `corpus/eng-engwebu.txt` — the WEB-UE ("engwebu") text, one verse per line
- `metadata/vref.txt` — one canonical verse reference per line (e.g. `PSA 18:1`)

Both files have the same number of lines (41,899) and are aligned 1:1, so
the full text of any psalm chapter is recovered by finding the matching
`PSA <n>:<verse>` references in `vref.txt` and reading the corresponding
lines from `eng-engwebu.txt`.

`fetch_psalms.py` automates this:

```bash
python3 fetch_psalms.py --batch 1,12,18,25,117,118 --output psalms_texts.json
python3 fetch_psalms.py --batch 1-150 --output psalms_texts.json --update
```

It fetches both files with `curl` (Python's `urllib.request` has proven
unreliable on the ~4.9 MB corpus file in this environment, failing with
`http.client.IncompleteRead`; `curl` fetches it intact every time), verifies
the two files have matching line counts before trusting any verse boundary,
and writes a `psalms_texts.json` consumed by `psalm_generator.py`. It does
**not** fall back to KJV or any other translation if the mirror is
unreachable — it exits with an error instead, so a script failure can never
silently substitute the wrong translation.

## Chant tone assignment

Gregorian/Sarum liturgical practice does not have one universal, fixed
psalm-number-to-tone chart — strictly speaking, "the tone of the psalm comes
from the antiphon" sung with it on a given occasion, i.e. the mode of
whichever antiphon is proper to that day's office. Rather than fabricate a
single canonical answer or fall back to an arbitrary rotation
(`(psalm_num - 1) % 8 + 1`, used in an earlier draft and rejected), each tone
in `ANTIPHON_ASSIGNMENTS` (`psalm_generator.py`) is a real, attested
historical assignment with a citation — see the table above.

`psalm_generator.py` raises an error rather than silently assigning a tone
when a psalm has no entry in `ANTIPHON_ASSIGNMENTS` and no `--tone` is given
explicitly. To add a new psalm, research a citable traditional assignment
(e.g. via the Sarum Tonale / St. Dunstan's Plainsong Psalter, or the
liturgical mode of the psalm's proper antiphon in the Roman Gradual) and add
it with its `source` string, or pass `--tone` to use an explicit, undocumented
tone for draft purposes.

### Tonus Peregrinus (Tone 9)

Psalm 117 is traditionally sung to the *Tonus Peregrinus* ("wandering tone"),
the one Gregorian psalm tone outside the standard 8-tone system. Unlike
Tones 1–8, it uses two different reciting notes — one for each half-verse —
rather than a single constant reciting tone. It has been added to
`GREGORIAN_TONES` as tone `9` in `psalm_generator.py`, with a simplified ABC
phrase consistent with the project's existing simplified house style for
Tones 1–8.

## Antiphon format

Each generated psalm file opens with `[Antiphon] <text>` and closes with
`[Antiphon closes] <text>`, both showing the antiphon in full (rather than
the `[Antiphon]` + once-only `Antiphon: <text>` convention used for refrains
elsewhere in the project — psalmody antiphons are short enough that the
inline-repeat form stays readable). The antiphon is a default-on feature of
the `.1` chant setting per psalm. To export a psalm without the antiphon
(e.g. when the antiphon is being sung separately by a cantor/choir slide),
pass `--no-antiphon` to `hymn_to_presentation.py`:

```bash
python3 hymn_to_presentation.py --file hymns/8.0_Psalm_Settings/Psalm_018 --no-antiphon
```

This strips the leading `[Antiphon] ...` and trailing `[Antiphon closes] ...`
lines before slides are built; it is a no-op on hymn files that don't use the
`[Antiphon]` marker.

## Gloria Patri (doxology)

`psalm_generator.py --include-doxology` appends the Gloria Patri ("Glory be
to the Father...") after the psalm body, matching LSB office practice. It is
off by default so a psalm chant setting can also be used outside an Office
context without manual editing.

## Automation scripts

### `fetch_psalms.py` — fetch genuine WEB-UE text

```bash
python3 fetch_psalms.py --psalm 18
python3 fetch_psalms.py --batch 1,12,18,25,117,118 --output psalms_texts.json
python3 fetch_psalms.py --batch 1-150 --output psalms_texts.json --update
```

### `psalm_generator.py` — generate psalm files

```bash
# Single psalm, tone from ANTIPHON_ASSIGNMENTS (or pass --tone explicitly)
python3 psalm_generator.py --psalm 18 --force

# Batch, with full WEB-UE texts from psalms_texts.json
python3 psalm_generator.py --batch 1,12,18,25,117,118 --text-file psalms_texts.json --force

# With Gloria Patri appended
python3 psalm_generator.py --batch 1,12,18,25,117,118 --text-file psalms_texts.json --include-doxology --force
```

After generating or editing any psalm file's `## ABC` section, run
`abc_to_musiqwik.py` to refresh the `## Musiquik` rendering, per the standard
project workflow documented in `CLAUDE.md`:

```bash
for i in 001 012 018 025 117 118; do
  python3 abc_to_musiqwik.py --file "hymns/8.0_Psalm_Settings/Psalm_$i"
done
```

## Extending to the remaining 144 psalms

For each new psalm:

1. `python3 fetch_psalms.py --psalm N --output psalms_texts.json --update`
2. Research and cite a traditional tone assignment, add it to
   `ANTIPHON_ASSIGNMENTS` in `psalm_generator.py` (or pass `--tone` for a
   provisional, uncited draft)
3. `python3 psalm_generator.py --psalm N --text-file psalms_texts.json --force`
4. `python3 abc_to_musiqwik.py --file hymns/8.0_Psalm_Settings/Psalm_0NN`
5. Mark the item done in `TODO.md`

## References

- **WEB-UE source:** BibleNLP/ebible GitHub mirror, `corpus/eng-engwebu.txt`
  aligned against `metadata/vref.txt` — https://github.com/BibleNLP/ebible
  (mirrors https://ebible.org/engwebu/, which itself returns 403 to automated
  requests in this environment)
- **Gregorian Psalm Tones:** Traditional 8-tone system (Tones 1–8) plus the
  Tonus Peregrinus (Tone 9)
- **Sarum Tonale:** St. Dunstan's Plainsong Psalter — historical English use
  tone assignments cited per psalm above
- **LSB Usage:** Lutheran Service Book (2006) psalm settings and office rubrics
- **ABC Notation:** See `CLAUDE.md` for ABC notation specifications
- **MusiQwik Font:** Psalm tone characters mapped via `abc_to_musiqwik.py`
- **Public domain status:** `docs/WEB-UE-COPYRIGHT.md`

## Support

For issues or questions about psalm implementation:
1. Check this document first
2. Review `CLAUDE.md` section on psalm format
3. Examine completed psalm files (Psalm_001, etc.) as examples
4. Consult `abc_to_musiqwik.py` output warnings for text completeness issues
