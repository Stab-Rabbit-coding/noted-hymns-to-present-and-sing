#!/usr/bin/env python3
"""
abc_to_musiqwik.py — Convert ABC music notation to MusiQwik font characters.

Usage (interactive):
    python3 abc_to_musiqwik.py

Usage (pipe from file):
    python3 abc_to_musiqwik.py < hymn_file
    python3 abc_to_musiqwik.py --file A_Mighty_Fortress_Trusty_Shield

Usage (fetch from URL and create hymn file):
    python3 abc_to_musiqwik.py --url http://openhymnal.org/Abc/Lord_Keep_Us_Steadfast.abc
    python3 abc_to_musiqwik.py -u http://openhymnal.org/Abc/Lord_Keep_Us_Steadfast.abc -d hymns/

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
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
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
            # Extract just the duration word ("half", "quarter", "eighth") for the
            # warning; the label is already "dotted half" / "dotted quarter" / etc.
            undotted_name = label.split()[1]   # e.g. "half" from "dotted half"
            warnings.append(
                f"Dotted note ({label}, duration={absolute_dur}) approximated "
                f"as an undotted {undotted_name} note; add the dot manually in "
                "your presentation software."
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
    # Strip per-line comments before joining so that %%-style directives (e.g.
    # %%MIDI program 0) don't consume the rest of the body once newlines are gone.
    body = " ".join(re.sub(r"%.*$", "", line) for line in body_lines)
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
# URL fetching and hymn file creation
# ---------------------------------------------------------------------------

_CA_BUNDLE = "/root/.ccr/ca-bundle.crt"
_MAX_CONTENT_BYTES = 512 * 1024  # 512 KB
_FETCH_TIMEOUT = 30  # seconds

_SUSPICIOUS_PATTERNS = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"\beval\s*\(", re.IGNORECASE),
    re.compile(r"\bexec\s*\(", re.IGNORECASE),
    re.compile(r"__import__", re.IGNORECASE),
    re.compile(r"\bos\.system\b", re.IGNORECASE),
    re.compile(r"\bsubprocess\b", re.IGNORECASE),
]

_MAX_LINE_LENGTH = 1000


def _ssl_context() -> ssl.SSLContext:
    """Return an SSL context that loads the custom CA bundle when present."""
    ctx = ssl.create_default_context()
    if os.path.exists(_CA_BUNDLE):
        ctx.load_verify_locations(_CA_BUNDLE)
    return ctx


def fetch_abc_url(url: str) -> str:
    """
    Fetch an ABC file from *url* and return its text.

    Only http and https schemes are accepted.  Content is capped at 512 KB.
    Raises ValueError for unsupported schemes and RuntimeError for network or
    HTTP errors.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Only http/https URLs are supported; got scheme: {parsed.scheme!r}"
        )

    req = urllib.request.Request(
        url, headers={"User-Agent": "abc_to_musiqwik/1.0 (hymn-converter)"}
    )
    open_kwargs: dict = {"timeout": _FETCH_TIMEOUT}
    if parsed.scheme == "https":
        open_kwargs["context"] = _ssl_context()

    try:
        with urllib.request.urlopen(req, **open_kwargs) as resp:
            data = resp.read(_MAX_CONTENT_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} fetching {url}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc.reason}") from exc

    if len(data) > _MAX_CONTENT_BYTES:
        raise RuntimeError(
            f"Content exceeds the {_MAX_CONTENT_BYTES // 1024} KB size limit"
        )

    return data.decode("utf-8", errors="replace")


def validate_abc_content(text: str) -> None:
    """
    Raise ValueError if *text* contains unsafe or non-ABC content.

    Checks performed:
    - No null bytes
    - No line longer than 1 000 characters
    - No suspicious patterns (script tags, eval, os.system, etc.)
    - Minimum required ABC fields present: X:, T:, K:
    """
    if "\x00" in text:
        raise ValueError("Content contains null bytes")

    for lineno, line in enumerate(text.splitlines(), 1):
        if len(line) > _MAX_LINE_LENGTH:
            raise ValueError(
                f"Line {lineno} exceeds {_MAX_LINE_LENGTH} characters ({len(line)} chars)"
            )

    for pattern in _SUSPICIOUS_PATTERNS:
        if pattern.search(text):
            raise ValueError(
                f"Content contains a suspicious pattern: {pattern.pattern!r}"
            )

    missing = []
    if not re.search(r"^X:\s*\d+", text, re.MULTILINE):
        missing.append("X:")
    if not re.search(r"^T:", text, re.MULTILINE):
        missing.append("T:")
    if not re.search(r"^K:", text, re.MULTILINE):
        missing.append("K:")
    if missing:
        raise ValueError(
            f"Content is missing required ABC header field(s): {', '.join(missing)}"
        )


def parse_full_abc(text: str) -> dict:
    """
    Parse a complete ABC file into its components.

    Returns a dict with:
        header      : dict of uppercase field letter → value (first occurrence wins)
        abc_for_file: the ABC text with W: lines removed (for the ## ABC section)
        w_fields    : list of raw W: values in document order
    """
    w_fields: list[str] = []
    non_w_lines: list[str] = []
    header: dict[str, str] = {}

    for line in text.splitlines():
        stripped = line.strip()

        w_match = re.match(r"^W:\s*(.*)", stripped)
        if w_match:
            w_fields.append(w_match.group(1))
            continue

        non_w_lines.append(line)

        h_match = re.match(r"^([A-Za-z]):\s*(.*)", stripped)
        if h_match:
            key = h_match.group(1).upper()
            if key not in header:
                header[key] = h_match.group(2).strip()

    return {
        "header": header,
        "abc_for_file": "\n".join(non_w_lines).strip(),
        "w_fields": w_fields,
    }


def _verses_from_w_fields(w_fields: list[str]) -> list[str]:
    """
    Group W: field values into verse strings.

    Open Hymnal convention: a blank W: line separates verses; lines within a
    verse are joined with a single space.  Leading verse numbers ("2. ", "3. ")
    are stripped so the caller can re-insert them uniformly.
    """
    verses: list[str] = []
    current: list[str] = []

    for value in w_fields:
        if not value.strip():
            if current:
                verses.append(" ".join(current))
                current = []
        else:
            current.append(value.strip())

    if current:
        verses.append(" ".join(current))

    # Strip any leading verse number prefix (e.g. "2. " or "3. ").
    return [re.sub(r"^\d+\.\s+", "", v, count=1) for v in verses]


def _safe_filename(title: str) -> str:
    """Derive a repository-style filename from a hymn title."""
    title = re.sub(r"\s*\([^)]*\)", "", title).strip()   # drop parenthetical subtitle
    return re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")


def _build_citation(header: dict, source_url: str) -> str:
    """Build the #Citations and References block from ABC header fields."""
    composer = header.get("C", "Unknown")
    source_field = header.get("S", "")
    z_field = header.get("Z", "")   # transcriber / arranger — sometimes carries word credit
    tune_name = header.get("T", "Unknown")

    # S: in Open Hymnal: "Open Hymnal Project, YYYY; openhymnal.org/Abc/..."
    setting = source_field.split(";")[0].strip() if source_field else ""

    words_credit = z_field if z_field else composer
    lines = [
        f"Words: {words_credit}.",
        f"Music: '{tune_name}' {composer}.",
    ]
    if setting:
        lines.append(f"Setting: {setting}.")
    lines.append(
        "copyright: public domain. This score is a part of the Open Hymnal Project."
    )
    lines.append("")
    lines.append(source_url)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lyrics completeness checks (canticle-aware truncation detection)
# ---------------------------------------------------------------------------

# Title keywords that identify a canticle rather than a strophic hymn.
# Canticles are prose scripture texts chanted to a psalm tone; verse count is
# not a meaningful truncation signal for them.
_CANTICLE_KEYWORDS: frozenset = frozenset([
    "magnificat", "benedictus", "nunc dimittis", "benedicite",
    "te deum", "gloria in excelsis", "jubilate", "deus misereatur",
    "venite", "cantate", "phos hilaron", "quicumque vult", "athanasian",
    "benedic anima", "ecce nunc", "bonum est confiteri",
])

_CREED_KEYWORDS: frozenset = frozenset([
    "creed", "athanasian", "quicumque", "nicene", "apostles",
])

# Phrases marking a Gloria Patri doxology — expected at the end of most canticles
# when used in Lutheran daily office.
_DOXOLOGY_MARKERS: list = [
    "glory be to the father",
    "gloria patri",
    "world without end",
    "as it was in the beginning",
    "sicut erat in principio",
]

# For specific canticles: phrases that appear near the end of the complete
# scriptural source.  Absence suggests the text was cut short.
# Keys are substrings matched against the lowercased title.
_CANTICLE_CLOSING_PHRASES: dict = {
    "magnificat": [
        "to his seed for ever",        # Luke 1:55 — final clause
        "he hath holpen his servant",  # Luke 1:54
    ],
    "benedictus": [
        "to guide our feet into the way of peace",  # Luke 1:79 — final clause
        "through the tender mercy",                  # Luke 1:78
    ],
    "nunc dimittis": [
        "glory of thy people israel",  # Luke 2:32 — final clause
        "all people",                  # Luke 2:31
    ],
    "jubilate": [
        "his truth endureth to all generations",  # Psalm 100:5 — final verse
        "into his courts with praise",             # Psalm 100:4
    ],
    "deus misereatur": [
        "all the ends of the earth shall fear him",  # Psalm 67:7 — final clause
        "god shall bless us",                         # Psalm 67:7
    ],
    "benedicite": [
        "praise him, and magnify him for ever",  # recurring refrain
        "works of the lord",                      # opening call
    ],
    "te deum": [
        "let me never be confounded",  # traditional closing verse
        "in thee have i trusted",      # near the end
    ],
}

# Phrases whose *absence* in a Lutheran canticle is intentional, not truncation.
# Lutheran worship omits Marian invocations and intercessory appeals to saints.
_LUTHERAN_INTENTIONAL_OMISSIONS: list = [
    ("holy mary, pray for us",
     "Marian intercession — intentionally omitted in Lutheran use"),
    ("queen of heaven",
     "Marian title — intentionally omitted in Lutheran worship"),
    ("mother of god, pray for us",
     "Marian intercession — intentionally omitted"),
    ("holy mother of god",
     "Marian title — not part of Lutheran liturgical texts"),
    ("hail mary",
     "Ave Maria — not used in Lutheran worship"),
    ("all ye holy angels and archangels, pray for us",
     "invocation of angels as intercessors — not part of Lutheran practice"),
]


def detect_content_type(title: str) -> str:
    """
    Classify a piece as 'hymn', 'canticle', or 'creed' based on title keywords.

    Canticles are prose scripture texts set to a psalm tone; verse count is not
    a valid truncation check for them.  Returns one of 'hymn', 'canticle', 'creed'.
    """
    lower = title.lower()
    for kw in _CREED_KEYWORDS:
        if kw in lower:
            return "creed"
    for kw in _CANTICLE_KEYWORDS:
        if kw in lower:
            return "canticle"
    if re.search(r"\bpsalm\s*\d+\b", lower):
        return "canticle"
    return "hymn"


def check_lyrics_completeness(
    full_text: str,
    title: str,
    content_type: str,
    verse_count: Optional[int] = None,
) -> list:
    """
    Return a list of warning strings about possible text truncation.

    Strategy differs by content type:

    hymn     — warn when verse_count < 3 (if count is known), noting that
                Lutheran settings may intentionally omit verses invoking saints.
    canticle — ignore verse count; instead check for a complete final sentence,
                the presence of a closing Gloria Patri doxology, and key phrases
                expected near the end of the scriptural source.
    creed    — verify the text ends with 'Amen' and is not suspiciously short.

    For all types, an abrupt (non-sentence-final) ending triggers a warning.
    Messages prefixed with '[info]' are informational rather than warnings; the
    caller should print them at the info level.
    """
    warnings: list = []
    if not full_text.strip():
        warnings.append("No lyrics found — verify the source file.")
        return warnings

    lower_text = full_text.lower()
    title_lower = title.lower()

    # Universal: abrupt ending without sentence-final punctuation.
    last_char = full_text.rstrip()[-1] if full_text.strip() else ""
    sentence_endings = {".", "!", "?", '"', "”", "'", "’", ")", "]"}
    if last_char not in sentence_endings:
        warnings.append(
            f"Text ends without sentence-final punctuation "
            f"(last character: {last_char!r}) — may be truncated. "
            "Verify against the original source."
        )

    # --- Hymn checks ---
    if content_type == "hymn":
        if verse_count is not None and verse_count < 3:
            warnings.append(
                f"Only {verse_count} verse(s) found. Lutheran settings sometimes "
                "intentionally omit verses invoking saints or containing content "
                "inconsistent with Lutheran theology, but fewer than 3 verses may "
                "also indicate truncation — compare with the original source."
            )
        return warnings

    # --- Canticle checks ---
    if content_type == "canticle":
        has_doxology = any(marker in lower_text for marker in _DOXOLOGY_MARKERS)
        if not has_doxology:
            warnings.append(
                "No Gloria Patri doxology found ('Glory be to the Father… "
                "world without end. Amen.'). Lutheran office use appends the doxology "
                "to canticles — verify whether it is intentionally absent for this "
                "specific liturgical use, or whether the text is incomplete."
            )

        # Check for canticle-specific closing phrases.
        for key, phrases in _CANTICLE_CLOSING_PHRASES.items():
            if key in title_lower:
                for phrase in phrases:
                    if phrase not in lower_text:
                        warnings.append(
                            f"Expected phrase not found: '{phrase}'. "
                            f"This phrase appears near the end of the {title!r} "
                            "scriptural source — verify all verses are present. "
                            "Compare with the KJV or other public-domain source."
                        )
                break  # only match the first canticle key

        word_count = len(full_text.split())
        if word_count < 60:
            warnings.append(
                f"Canticle text is short ({word_count} words). "
                "Verify all scriptural verses are included."
            )

        # Flag Catholic-only phrases that are present but unexpected in Lutheran use.
        # These signal an *addition*, not a truncation — print at info level.
        for phrase, reason in _LUTHERAN_INTENTIONAL_OMISSIONS:
            if phrase in lower_text:
                warnings.append(
                    f"[info] Text contains '{phrase}' ({reason})."
                )
        return warnings

    # --- Creed checks ---
    if content_type == "creed":
        if "amen" not in lower_text[-200:]:
            warnings.append(
                "Creed text does not appear to end with 'Amen' — may be incomplete."
            )
        word_count = len(full_text.split())
        if word_count < 80:
            warnings.append(
                f"Creed text is short ({word_count} words) — verify the full text "
                "is present."
            )
        return warnings

    return warnings


def _extract_lyrics_section(text: str) -> Optional[str]:
    """Pull the raw prose text from a hymn file's #Lyrics section."""
    match = re.search(
        r"^#\s*Lyrics[^\n]*\n(.*?)(?=^#|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if match:
        return match.group(1).strip()
    return None


def _emit_completeness_warnings(warnings: list, source: str) -> None:
    """Print completeness warnings to stderr, using [info] level for informational items."""
    for w in warnings:
        if w.startswith("[info]"):
            print(f"[info] {w[6:].strip()}", file=sys.stderr)
        else:
            print(f"[warn] {w}", file=sys.stderr)


def create_hymn_from_url(url: str, output_dir: Path) -> Path:
    """
    Fetch an ABC file from *url*, convert it, and write a complete hymn file.

    Returns the path of the created file.  Progress and warnings go to stderr.
    Raises ValueError or RuntimeError on failure.
    """
    print(f"[info] Fetching {url} …", file=sys.stderr)
    raw = fetch_abc_url(url)

    print("[info] Validating content …", file=sys.stderr)
    validate_abc_content(raw)

    parsed = parse_full_abc(raw)
    header       = parsed["header"]
    abc_for_file = parsed["abc_for_file"]
    w_fields     = parsed["w_fields"]

    title = header.get("T", "Untitled Hymn")
    print(f"[info] Title: {title}", file=sys.stderr)

    # Convert melody.
    print("[info] Converting melody to MusiQwik …", file=sys.stderr)
    musiqwik, mel_warnings = abc_to_musiqwik(abc_for_file)
    for w in mel_warnings:
        print(f"[warn] {w}", file=sys.stderr)

    # Parse lyrics from W: fields.
    verses = _verses_from_w_fields(w_fields)
    if not verses:
        print(
            "[warn] No W: lyrics fields found; #Lyrics section will be empty.",
            file=sys.stderr,
        )
    else:
        content_type = detect_content_type(title)
        full_lyrics = "  ".join(verses)
        _emit_completeness_warnings(
            check_lyrics_completeness(
                full_lyrics, title, content_type, verse_count=len(verses)
            ),
            source=url,
        )

    # Format lyrics as continuous prose with inline verse numbers.
    if verses:
        parts = [verses[0]] + [f"{i}. {v}" for i, v in enumerate(verses[1:], start=2)]
        lyrics_text = "  ".join(parts)
    else:
        lyrics_text = "(no lyrics found)"

    citation_text = _build_citation(header, url)

    hymn_content = (
        f"{title}\n\n"
        f"# Melody\n\n"
        f"## ABC\n{abc_for_file}\n\n"
        f"## Musiquik\n{musiqwik}\n\n"
        f"#Lyrics\n{lyrics_text}\n\n"
        f"#Citations and References\n\n"
        f"{citation_text}\n"
    )

    filename = _safe_filename(title) or "Untitled_Hymn"
    out_path = output_dir / filename

    if out_path.exists():
        print(
            f"[warn] File already exists and will be overwritten: {out_path}",
            file=sys.stderr,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(hymn_content, encoding="utf-8")
    print(f"[info] Hymn file written: {out_path}", file=sys.stderr)
    return out_path


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
        "--url", "-u",
        metavar="URL",
        help=(
            "Fetch an ABC file from URL (http or https), convert it to MusiQwik, "
            "and write a complete hymn file. "
            "Hymns with fewer than 3 verses are flagged as possibly truncated."
        ),
    )
    parser.add_argument(
        "--output-dir", "-d",
        metavar="DIR",
        default=".",
        help="Directory in which to write the hymn file created with --url (default: .).",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run the built-in A Mighty Fortress example and exit.",
    )
    return parser


def _extract_melody_section(text: str) -> Optional[str]:
    """
    Pull just the ABC content from a hymn file.

    Prefers the ## ABC subsection when the file uses the structured
    (## ABC / ## Musiquik) format; falls back to the full # Melody block
    for files that have not yet been migrated to the new layout.

    Returns None when no melody section is found at all — callers should
    skip conversion rather than attempt to parse the full file text as ABC.
    """
    # New format: ## ABC subsection under # Melody.
    abc_match = re.search(
        r"^##\s*ABC[^\n]*\n(.*?)(?=^##|^#|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if abc_match:
        extracted = abc_match.group(1).strip()
        # Treat a placeholder comment "(None…)" or blank content as absent
        # so that text-only liturgical files are handled gracefully.
        if extracted and not extracted.startswith("("):
            return extracted

    # Legacy format: raw ABC directly under # Melody.
    melody_match = re.search(
        r"^#\s*Melody\s*\n(.*?)(?=^#|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if melody_match:
        extracted = melody_match.group(1).strip()
        if extracted and not extracted.startswith("("):
            return extracted

    # No usable melody section found — signal the caller to skip conversion.
    return None


def _update_musiqwik_section(path: Path, musiqwik_text: str) -> None:
    """
    Write *musiqwik_text* into the ## Musiquik subsection of the hymn file.

    If the subsection already exists its content is replaced.  If it is
    absent it is inserted after the ## ABC subsection.
    """
    text = path.read_text(encoding="utf-8")

    # Locate the ## Musiquik header line.
    m_header = re.search(r"^##\s*Musiquik[^\n]*\n", text, re.MULTILINE)
    if m_header:
        # Replace everything from after the header to the next section marker.
        content_start = m_header.end()
        m_next = re.search(r"^#", text[content_start:], re.MULTILINE)
        content_end = content_start + m_next.start() if m_next else len(text)
        new_text = text[:content_start] + musiqwik_text + "\n\n" + text[content_end:]
        path.write_text(new_text, encoding="utf-8")
        print(f"[info] ## Musiquik section updated in {path}", file=sys.stderr)
        return

    # No ## Musiquik yet — insert after the ## ABC block.
    m_abc = re.search(r"^##\s*ABC[^\n]*\n", text, re.MULTILINE)
    if m_abc:
        abc_content_start = m_abc.end()
        m_abc_end = re.search(r"^#", text[abc_content_start:], re.MULTILINE)
        abc_end = abc_content_start + m_abc_end.start() if m_abc_end else len(text)
        new_text = (
            text[:abc_end].rstrip("\n")
            + "\n\n## Musiquik\n"
            + musiqwik_text
            + "\n\n"
            + text[abc_end:].lstrip("\n")
        )
        path.write_text(new_text, encoding="utf-8")
        print(f"[info] ## Musiquik section inserted in {path}", file=sys.stderr)
        return

    print("[warn] No ## ABC or ## Musiquik section found; file not updated.", file=sys.stderr)


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

    if args.url:
        try:
            out = create_hymn_from_url(args.url, Path(args.output_dir))
            print(out)
        except (ValueError, RuntimeError) as exc:
            sys.exit(f"Error: {exc}")
        return

    if args.file:
        path = Path(args.file)
        if not path.exists():
            sys.exit(f"Error: file not found: {path}")
        raw_text = path.read_text(encoding="utf-8")
        abc_text = _extract_melody_section(raw_text)
        # _extract_melody_section returns None for text-only files (e.g. spoken
        # liturgical items like an Examination of Conscience) that deliberately
        # contain no ## ABC subsection or contain only a placeholder comment.
        if abc_text is None:
            print(
                f"[warn] No ## ABC notation found in {path}; "
                "skipping MusiQwik conversion for this text-only file.",
                file=sys.stderr,
            )
            return
        result, warnings = abc_to_musiqwik(abc_text)
        if warnings:
            for w in warnings:
                print(f"[warn] {w}", file=sys.stderr)
        print(result)
        _update_musiqwik_section(path, result)

        # Check lyrics completeness using canticle-aware detection.
        lyrics_raw = _extract_lyrics_section(raw_text)
        if lyrics_raw:
            title_guess = path.name.replace("_", " ")
            content_type = detect_content_type(title_guess)
            _emit_completeness_warnings(
                check_lyrics_completeness(lyrics_raw, title_guess, content_type),
                source=str(path),
            )
        return

    run_interactive()


if __name__ == "__main__":
    main()
