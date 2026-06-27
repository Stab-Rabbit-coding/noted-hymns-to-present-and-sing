#!/usr/bin/env python3
"""
abc_to_musiqwik.py — Convert ABC music notation to MusiQwik font characters.

Usage (interactive):
    python3 abc_to_musiqwik.py

Usage (pipe from file):
    python3 abc_to_musiqwik.py < hymn_file
    python3 abc_to_musiqwik.py --file A_Mighty_Fortress_Trusty_Shield

The output is plain text. Paste it into a presentation text box and apply
the MusiQwik font (by Robert Allgeyer) to render it as staff notation.

Character-table derivation
--------------------------
MusiQwik encodes notes as  chr(DURATION_BASE + PITCH_INDEX)  where:

  PITCH_INDEX  0=A3  1=B3  2=C4(middle C)  3=D4  4=E4  5=F4  6=G4
               7=A4  8=B4  9=C5  10=D5  11=E5  12=F5  13=G5  14=A5

  DURATION_BASE
    64  →  eighth notes   ('@' through 'N')
    80  →  quarter notes  ('P' through '^')
    96  →  half notes     ('`' through 'n')
   112  →  whole notes    ('p' through '~')

Special characters confirmed from font-file glyph analysis:
  '&' (38)  treble clef
  '=' (61)  staff segment (full width)
  '-' (45)  staff segment (narrow spacer)
  '.' (46)  staff + single barline
  ')' (41)  staff + final/double barline
  'O' (79)  eighth rest
  '_' (95)  quarter rest
  'o' (111) half rest
  ';' (59)  whole rest

  Time signatures on staff:
    chr(48) 'C'   common time
    chr(49) '1'   2/2
    chr(50) '2'   2/4
    chr(51) '3'   3/4
    chr(52) '4'   4/4
    chr(53) '5'   3/2
    chr(54) '6'   6/8
    chr(55) '7'   cut time (C|)
"""

import argparse
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# MusiQwik character table
# ---------------------------------------------------------------------------

# Duration bases — add PITCH_INDEX (0–14) to get the note character.
_EIGHTH_BASE  = 64   # '@' … 'N'
_QUARTER_BASE = 80   # 'P' … '^'
_HALF_BASE    = 96   # '`' … 'n'
_WHOLE_BASE   = 112  # 'p' … '~'

# Pitch positions as named constants for readability in error messages.
_PITCH_NAMES = [
    "A3", "B3", "C4", "D4", "E4", "F4", "G4",
    "A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5",
]

# Staff and structural glyphs.
TREBLE_CLEF    = "&"   # chr(38)
STAFF_FULL     = "="   # chr(61) — one staff-width segment, no barline
STAFF_NARROW   = "-"   # chr(45) — narrow gap-filler
BARLINE        = "."   # chr(46) — staff + single barline
FINAL_BARLINE  = ")"   # chr(41) — staff + double/final barline
REPEAT_BEGIN   = "("   # chr(40) — staff + begin-repeat barline
# Repeat-end re-uses FINAL_BARLINE; add dots manually if needed.

# Rests (position-independent; each renders at the conventional staff height).
EIGHTH_REST  = chr(79)   # 'O'
QUARTER_REST = chr(95)   # '_'
HALF_REST    = chr(111)  # 'o'
WHOLE_REST   = chr(59)   # ';'

# Time-signature glyphs (each includes a full staff segment).
_TIME_SIG_CHARS: dict[str, str] = {
    "C":   chr(48),  # common time
    "2/2": chr(49),
    "2/4": chr(50),
    "3/4": chr(51),
    "4/4": chr(52),
    "3/2": chr(53),
    "6/8": chr(54),
    "C|":  chr(55),  # cut time
}

# ---------------------------------------------------------------------------
# Pitch helpers
# ---------------------------------------------------------------------------

# Maps an ABC note letter to a pitch-class index where C=0, D=2, …
# (chromatic semitone distance above C within one octave).
_ABC_LETTER_SEMITONE: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}

# Maps MIDI note number to MusiQwik pitch index.
# Range A3 (MIDI 57) → A5 (MIDI 81).
_MIDI_TO_PITCH_INDEX: dict[int, int] = {
    57: 0,   # A3
    59: 1,   # B3
    60: 2,   # C4
    62: 3,   # D4
    64: 4,   # E4
    65: 5,   # F4
    67: 6,   # G4
    69: 7,   # A4
    71: 8,   # B4
    72: 9,   # C5
    74: 10,  # D5
    76: 11,  # E5
    77: 12,  # F5
    79: 13,  # G5
    81: 14,  # A5
}

# MIDI numbers for the supported range.
_MIDI_MIN = 57  # A3
_MIDI_MAX = 81  # A5


def abc_note_to_midi(letter: str, accidental: int, octave_shift: int) -> int:
    """
    Convert a parsed ABC note to a MIDI note number.

    Parameters
    ----------
    letter       : uppercase note letter A–G
    accidental   : semitone adjustment (-1 flat, 0 natural, +1 sharp)
    octave_shift : additional octave shifts from commas/apostrophes
                   (positive = up, negative = down)

    Returns the MIDI note number.  ABC lowercase letters are handled by
    the caller converting to uppercase + octave_shift += 1.
    """
    # Base MIDI note: C in octave 4 = MIDI 60.
    # ABC uppercase letters default to octave 4 (C4 … B4).
    base_octave_midi = 60  # C4
    semitone = _ABC_LETTER_SEMITONE[letter]
    midi = base_octave_midi + semitone + accidental + octave_shift * 12
    return midi


def midi_to_pitch_index(midi: int) -> Optional[int]:
    """Return MusiQwik pitch index (0–14) for a MIDI note, or None if out of range."""
    return _MIDI_TO_PITCH_INDEX.get(midi)


def note_char(duration_base: int, pitch_index: int) -> str:
    """Return the MusiQwik character for the given duration base and pitch index."""
    return chr(duration_base + pitch_index)

# ---------------------------------------------------------------------------
# ABC header parsing
# ---------------------------------------------------------------------------

# Key-signature sharps/flats: major keys and their diatonic accidentals.
# Each value is a set of uppercase note letters that are raised by a semitone
# (sharps) or lowered (flats, represented as negative).
_KEY_SHARPS: dict[str, set[str]] = {
    "C":  set(),
    "G":  {"F"},
    "D":  {"F", "C"},
    "A":  {"F", "C", "G"},
    "E":  {"F", "C", "G", "D"},
    "B":  {"F", "C", "G", "D", "A"},
    "F#": {"F", "C", "G", "D", "A", "E"},
    "C#": {"F", "C", "G", "D", "A", "E", "B"},
}
_KEY_FLATS: dict[str, set[str]] = {
    "F":  {"B"},
    "Bb": {"B", "E"},
    "Eb": {"B", "E", "A"},
    "Ab": {"B", "E", "A", "D"},
    "Db": {"B", "E", "A", "D", "G"},
    "Gb": {"B", "E", "A", "D", "G", "C"},
    "Cb": {"B", "E", "A", "D", "G", "C", "F"},
}

# Relative minors map to their parallel majors for accidental lookup.
_MINOR_TO_MAJOR: dict[str, str] = {
    "Am": "C",  "Em": "G",  "Bm": "D",  "F#m": "A", "C#m": "E",
    "G#m": "B", "D#m": "F#","A#m": "C#","Dm": "F",  "Gm": "Bb",
    "Cm": "Eb", "Fm": "Ab", "Bbm": "Db","Ebm": "Gb","Abm": "Cb",
}


def parse_key(key_str: str) -> dict[str, int]:
    """
    Parse an ABC K: field value and return a mapping of note letter → semitone
    adjustment (e.g., {"F": 1, "C": 1} for D major).

    Handles major keys and common minor keys.  Returns an empty dict for
    unrecognized keys (safe fallback — no accidentals applied).
    """
    key_str = key_str.strip()

    # Resolve minor to its relative major for accidental purposes.
    if key_str in _MINOR_TO_MAJOR:
        key_str = _MINOR_TO_MAJOR[key_str]

    if key_str in _KEY_SHARPS:
        return {letter: 1 for letter in _KEY_SHARPS[key_str]}
    if key_str in _KEY_FLATS:
        return {letter: -1 for letter in _KEY_FLATS[key_str]}

    # Chromatic / exotic keys — no adjustment; caller will warn.
    return {}


def parse_header(lines: list[str]) -> dict[str, str]:
    """
    Extract ABC header fields from a list of text lines.

    Returns a dict mapping field letter to value, e.g. {"M": "4/4", "L": "1/4", "K": "D"}.
    Stops collecting header fields once the first body line is encountered
    (a body line is any line that is not blank and does not start with a letter
    followed by a colon).
    """
    fields: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Header fields match "X:value" where X is a single letter.
        match = re.match(r"^([A-Za-z]):\s*(.*)$", stripped)
        if match:
            key, value = match.group(1).upper(), match.group(2).strip()
            fields[key] = value
        else:
            # Body has started; stop parsing headers.
            break
    return fields

# ---------------------------------------------------------------------------
# ABC body tokeniser
# ---------------------------------------------------------------------------

# Regex that matches one ABC token at a time (in order of precedence).
_TOKEN_RE = re.compile(
    r"""
    (?P<chord>   \[[^\]]+\]           )  # [chord] — skip
  | (?P<barline> \|:|\|{1,2}|:\|     )  # barlines and repeats
  | (?P<note>
        (?P<acc>   [\^_=]{0,2}        )  # accidental (^^, _, =, etc.)
        (?P<pitch> [A-Ga-gz]          )  # note letter or 'z' for rest
        (?P<oct>   [,']*              )  # octave shifts
        (?P<dur>   \d*/*\d*           )  # duration (e.g. 2, /, /2, 3/2)
    )
  | (?P<space>   \s+                  )  # whitespace — skip
  | (?P<other>   .                    )  # anything else — skip with warning
    """,
    re.VERBOSE,
)


def parse_duration(dur_str: str, default_length: Fraction) -> Fraction:
    """
    Convert an ABC duration string to an absolute note length as a Fraction.

    Parameters
    ----------
    dur_str       : the raw duration suffix from the ABC body (may be empty)
    default_length: the L: field value, e.g. Fraction(1, 4) for L:1/4

    Returns the absolute duration as a Fraction where Fraction(1, 1) = whole note.
    """
    if not dur_str or dur_str in ("", "/"):
        # Bare "/" is shorthand for ×(1/2).
        multiplier = Fraction(1, 2) if dur_str == "/" else Fraction(1)
        return default_length * multiplier

    # Full fraction like "3/2" or just "2" or just "/2".
    if "/" in dur_str:
        parts = dur_str.split("/", 1)
        numerator   = int(parts[0]) if parts[0] else 1
        denominator = int(parts[1]) if parts[1] else 2
        multiplier = Fraction(numerator, denominator)
    else:
        multiplier = Fraction(int(dur_str))

    return default_length * multiplier


def duration_to_base(absolute_dur: Fraction, warnings: list[str]) -> Optional[int]:
    """
    Map an absolute note duration to the appropriate MusiQwik duration base.

    Supported durations:  1/1  1/2  1/4  1/8
    Dotted notes are rounded to the nearest supported duration; a warning
    is appended to *warnings*.

    Returns the MusiQwik duration base integer, or None if unrenderable.
    """
    # Exact matches.
    exact = {
        Fraction(1, 1): _WHOLE_BASE,
        Fraction(1, 2): _HALF_BASE,
        Fraction(1, 4): _QUARTER_BASE,
        Fraction(1, 8): _EIGHTH_BASE,
    }
    if absolute_dur in exact:
        return exact[absolute_dur]

    # Approximate dotted notes by rounding to the nearest supported value.
    thresholds = [
        (Fraction(3, 4), _HALF_BASE,    "dotted half"),
        (Fraction(3, 8), _QUARTER_BASE, "dotted quarter"),
        (Fraction(3, 16), _EIGHTH_BASE, "dotted eighth"),
    ]
    for threshold, base, label in thresholds:
        if absolute_dur == threshold:
            warnings.append(
                f"Dotted note ({label}, duration={absolute_dur}) approximated "
                f"as {_PITCH_NAMES[0][0:0]}; render the dot manually in your "
                "presentation software."
            )
            return base

    # Note is too short or an unusual duration.
    if absolute_dur >= Fraction(1, 1):
        warnings.append(
            f"Duration {absolute_dur} ≥ whole note; rendered as whole note."
        )
        return _WHOLE_BASE
    if absolute_dur <= Fraction(1, 16):
        warnings.append(
            f"Duration {absolute_dur} ≤ 1/16 note; rendered as eighth note."
        )
        return _EIGHTH_BASE

    # Generic fallback: pick the closest supported value.
    supported = [Fraction(1, 8), Fraction(1, 4), Fraction(1, 2), Fraction(1, 1)]
    closest = min(supported, key=lambda x: abs(x - absolute_dur))
    warnings.append(
        f"Unsupported duration {absolute_dur}; approximated as {closest}."
    )
    return exact[closest]


def rest_char_for_duration(absolute_dur: Fraction) -> str:
    """Return the MusiQwik rest character closest to *absolute_dur*."""
    if absolute_dur >= Fraction(1, 1):
        return WHOLE_REST
    if absolute_dur >= Fraction(1, 2):
        return HALF_REST
    if absolute_dur >= Fraction(1, 4):
        return QUARTER_REST
    return EIGHTH_REST

# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------


def convert_abc_body(
    body: str,
    default_length: Fraction,
    key_accidentals: dict[str, int],
) -> tuple[str, list[str]]:
    """
    Convert the note-bearing body of an ABC tune to MusiQwik characters.

    Parameters
    ----------
    body             : the body text (everything after the header)
    default_length   : L: field as a Fraction
    key_accidentals  : mapping letter → semitone from parse_key()

    Returns
    -------
    musiqwik_text    : the encoded MusiQwik string
    warnings         : list of human-readable warning strings
    """
    output: list[str] = []
    warnings: list[str] = []

    # Active accidentals within the current measure (reset at each barline).
    # Maps uppercase note letter → semitone adjustment.
    measure_accidentals: dict[str, int] = {}

    for match in _TOKEN_RE.finditer(body):
        kind = match.lastgroup

        if kind == "barline":
            bar_str = match.group("barline")
            measure_accidentals.clear()

            if bar_str in ("||", ":|"):
                output.append(FINAL_BARLINE)
            elif bar_str == "|:":
                output.append(REPEAT_BEGIN)
            else:
                # Plain "|" — single barline.
                output.append(BARLINE)

        elif kind == "note":
            pitch_letter = match.group("pitch")
            acc_str      = match.group("acc")
            oct_str      = match.group("oct")
            dur_str      = match.group("dur")

            # Rest.
            if pitch_letter.lower() == "z":
                absolute_dur = parse_duration(dur_str, default_length)
                output.append(rest_char_for_duration(absolute_dur))
                continue

            # --- Determine pitch ---
            # ABC: lowercase = one octave above uppercase.
            is_lower = pitch_letter.islower()
            upper    = pitch_letter.upper()

            # Octave shifts from commas (down) and apostrophes (up).
            extra_octaves = oct_str.count("'") - oct_str.count(",")
            if is_lower:
                extra_octaves += 1  # lowercase implies +1 octave vs. uppercase

            # Accidental precedence: explicit in note > measure carry-over > key.
            if acc_str == "^" or acc_str == "^^":
                semitones = len(acc_str)   # 1 or 2 semitones up
                measure_accidentals[upper] = semitones
            elif acc_str == "_" or acc_str == "__":
                semitones = -len(acc_str)
                measure_accidentals[upper] = semitones
            elif acc_str == "=":
                measure_accidentals[upper] = 0  # natural overrides key
            # No explicit accidental: check measure carry-over, then key sig.
            acc_semitones = measure_accidentals.get(
                upper,
                key_accidentals.get(upper, 0),
            )

            midi = abc_note_to_midi(upper, acc_semitones, extra_octaves)

            # MusiQwik only covers A3–A5.
            if midi < _MIDI_MIN or midi > _MIDI_MAX:
                warnings.append(
                    f"Note {pitch_letter}{oct_str} (MIDI {midi}) is outside the "
                    f"MusiQwik range A3–A5; skipped."
                )
                continue

            pitch_index = midi_to_pitch_index(midi)
            if pitch_index is None:
                # Chromatic note (e.g. F# where only F and G are in the table).
                # Use the diatonic position (same staff line) as approximation.
                diatonic_midi = abc_note_to_midi(upper, 0, extra_octaves)
                pitch_index   = midi_to_pitch_index(diatonic_midi)
                if pitch_index is None:
                    warnings.append(
                        f"Cannot map MIDI {midi} to a MusiQwik pitch; skipped."
                    )
                    continue
                warnings.append(
                    f"Chromatic note at MIDI {midi} rendered at diatonic position "
                    f"{_PITCH_NAMES[pitch_index]} (accidental not shown)."
                )

            # --- Determine duration ---
            absolute_dur = parse_duration(dur_str, default_length)
            base = duration_to_base(absolute_dur, warnings)
            if base is None:
                warnings.append(f"Could not determine duration for {dur_str!r}; skipped.")
                continue

            output.append(note_char(base, pitch_index))

        # "chord", "space", "other" — silently skip.

    return "".join(output), warnings


def abc_to_musiqwik(text: str) -> tuple[str, list[str]]:
    """
    Full pipeline: parse an ABC tune and return (musiqwik_string, warnings).

    The returned MusiQwik string begins with the treble clef and time signature,
    followed by the encoded notes and barlines from the tune body.
    """
    lines = text.splitlines()

    # Split into header lines and body.
    header_end = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not re.match(r"^[A-Za-z]:", stripped):
            header_end = i
            break
    else:
        header_end = len(lines)

    body_lines = lines[header_end:]
    body         = " ".join(body_lines)

    # Remove inline comments (%...) and continuation characters (\).
    body = re.sub(r"%[^\n]*", "", body)
    body = body.replace("\\", " ")

    # Parse header fields.
    fields = parse_header(lines)

    # Default note length.
    l_str = fields.get("L", "1/4")
    try:
        num, den = l_str.split("/")
        default_length = Fraction(int(num), int(den))
    except (ValueError, AttributeError):
        default_length = Fraction(1, 4)

    # Time signature glyph.
    meter = fields.get("M", "4/4").strip()
    time_glyph = _TIME_SIG_CHARS.get(meter, _TIME_SIG_CHARS.get("4/4"))

    # Key signature accidentals.
    key_str = fields.get("K", "C")
    key_accidentals = parse_key(key_str)

    warnings: list[str] = []

    # Convert body.
    body_output, body_warnings = convert_abc_body(body, default_length, key_accidentals)
    warnings.extend(body_warnings)

    # Build the final MusiQwik string:
    #   treble clef + time signature + notes/barlines
    musiqwik = TREBLE_CLEF + time_glyph + body_output

    return musiqwik, warnings

# ---------------------------------------------------------------------------
# Interactive conversation interface
# ---------------------------------------------------------------------------

_BANNER = """
╔══════════════════════════════════════════════════╗
║   ABC → MusiQwik Converter                       ║
║   Paste ABC notation, then enter a blank line.   ║
║   Type  quit  or  exit  to leave.                ║
╚══════════════════════════════════════════════════╝
"""

_HELP = """
Commands
--------
  help      — show this message
  example   — load the A Mighty Fortress sample
  quit/exit — leave the program

Input format
------------
Paste a complete ABC tune (headers + body) then press Enter on an empty line
to trigger conversion.  You may also pipe a file through stdin.

Output
------
The MusiQwik text is printed to stdout.  Copy it into your presentation
software and apply the MusiQwik font to render it as staff notation.

Font note
---------
MusiQwik by Robert Allgeyer — https://www.fontspace.com/musiqwik-font-f3722
Each character already includes the surrounding staff lines, so just type
(or paste) the output characters in sequence.
"""

_EXAMPLE_ABC = """\
X:1
T:A Mighty Fortress Is Our God (Ein Feste Burg, Rhythmic)
C:Martin Luther, 1529
M:4/4
L:1/4
K:D
D D E F | E2 D2 | D E F G | A4 |
B A B c | d c B A | G2 E2 | D4 |
d d d e | f e d A | A4 |
B A B c | d2 c B | A4 | G F E D | D4 ||
"""


def run_interactive() -> None:
    """Run the interactive conversation loop."""
    # Detect non-interactive stdin (file pipe) early.
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        result, warnings = abc_to_musiqwik(raw)
        if warnings:
            for w in warnings:
                print(f"[warn] {w}", file=sys.stderr)
        print(result)
        return

    print(_BANNER)

    while True:
        print("\nEnter ABC tune (blank line to convert, or a command):")
        lines: list[str] = []

        while True:
            try:
                line = input()
            except EOFError:
                # Ctrl-D: treat buffered lines as input, then exit.
                if lines:
                    break
                print("\nGoodbye.")
                return

            stripped = line.strip().lower()
            if not lines and stripped in ("quit", "exit"):
                print("Goodbye.")
                return
            if not lines and stripped == "help":
                print(_HELP)
                break
            if not lines and stripped == "example":
                lines = _EXAMPLE_ABC.splitlines()
                break
            if stripped == "" and lines:
                # Blank line after content signals end of input.
                break
            if stripped == "" and not lines:
                # Leading blank line — ignore and re-prompt.
                continue
            lines.append(line)

        if not lines:
            continue

        raw = "\n".join(lines)
        result, warnings = abc_to_musiqwik(raw)

        if warnings:
            print("\n--- Warnings ---")
            for w in warnings:
                print(f"  • {w}")

        print("\n--- MusiQwik output ---")
        print(result)
        print("--- end ---")
        print(
            "\nCopy the output above, paste into your presentation text box, "
            "and apply the MusiQwik font."
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert ABC notation to MusiQwik font characters.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to a hymn file containing ABC notation (reads the # Melody section).",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run the built-in A Mighty Fortress example and exit.",
    )
    return parser


def _extract_melody_section(text: str) -> str:
    """
    Pull just the ABC content from a hymn file that uses the project's
    three-section format (# Melody, #Lyrics, #Citations and References).
    """
    # Match from "# Melody" header to the next section header or end of file.
    match = re.search(
        r"#\s*Melody\s*\n(.*?)(?=^#|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if match:
        return match.group(1).strip()
    # No section header found — return the whole text as-is.
    return text


def main() -> None:
    parser = _build_arg_parser()
    args   = parser.parse_args()

    if args.example:
        result, warnings = abc_to_musiqwik(_EXAMPLE_ABC)
        if warnings:
            for w in warnings:
                print(f"[warn] {w}", file=sys.stderr)
        print(result)
        return

    if args.file:
        path = Path(args.file)
        if not path.exists():
            sys.exit(f"Error: file not found: {path}")
        raw_text = path.read_text(encoding="utf-8")
        abc_text = _extract_melody_section(raw_text)
        result, warnings = abc_to_musiqwik(abc_text)
        if warnings:
            for w in warnings:
                print(f"[warn] {w}", file=sys.stderr)
        print(result)
        return

    run_interactive()


if __name__ == "__main__":
    main()
