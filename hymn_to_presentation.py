#!/usr/bin/env python3
"""
hymn_to_presentation.py — Convert a hymn file to HTML, PDF, or PPTX slides.

Produces one title slide (with full attribution) followed by content slides
showing up to --lines-per-slide (default 3) melody/lyric pairs each.  The
MusiQwik melody line appears immediately above the corresponding lyric line.
Each verse starts on a new slide.

Usage:
    python3 hymn_to_presentation.py --file <hymn_file>
    python3 hymn_to_presentation.py --file <hymn_file> --format pptx
    python3 hymn_to_presentation.py --file <hymn_file> --format pdf -o out.pdf
    python3 hymn_to_presentation.py --file <hymn_file> --lines-per-slide 2

Dependencies:
    PDF  — playwright  (pip install playwright)  +  Chromium at /opt/pw-browsers
    PPTX — python-pptx (pip install python-pptx)
    HTML — stdlib only
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Hymn-file parsing
# ---------------------------------------------------------------------------

def _extract_section(text: str, header_re: str, stop_re: str) -> str:
    m = re.search(header_re, text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ''
    start = m.end()
    stop = re.search(stop_re, text[start:], re.MULTILINE)
    return text[start : start + stop.start()] if stop else text[start:]


def parse_hymn_file(path: Path) -> dict:
    text  = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    title = next((l.strip() for l in lines if l.strip()), '')

    return {
        'title':       title,
        'abc_text':    _extract_section(text, r'^##\s*ABC[^\n]*\n',      r'^##|^#(?!#)'),
        'musiqwik':    _extract_section(text, r'^##\s*Musiquik[^\n]*\n', r'^##|^#(?!#)').strip(),
        'lyrics_text': _extract_section(text, r'^#\s*Lyrics[^\n]*\n',    r'^#(?!#)').strip(),
        'attribution': _extract_section(text, r'^#\s*Citations[^\n]*\n', r'^#(?!#)').strip(),
    }


# ---------------------------------------------------------------------------
# Melody-line splitting
# ---------------------------------------------------------------------------

def _abc_body_lines(abc_text: str) -> list[str]:
    """Non-header, non-directive lines from an ABC block."""
    in_body, result = False, []
    for line in abc_text.splitlines():
        s = line.strip()
        if not in_body:
            if s and not re.match(r'^[A-Za-z]:', s):
                in_body = True
            else:
                continue
        if s and not s.startswith('%'):
            result.append(s)
    return result


def _barlines_per_line(abc_lines: list[str]) -> list[int]:
    """Count measure-ending barlines for each physical ABC body line."""
    counts = []
    for line in abc_lines:
        cleaned = re.sub(r'\|:', '', line)       # begin-repeat doesn't end a measure
        cleaned = re.sub(r'\(\d+', '', cleaned)  # strip triplet/tuplet markers
        n = len(re.findall(r'\|{1,2}|:\|', cleaned))
        if n:
            counts.append(n)
    return counts


def split_musiqwik(musiqwik: str, barlines_per_line: list[int]) -> list[str]:
    """
    Split the MusiQwik string into one segment per melody line.
    Each segment is prefixed with the original clef+time-sig so it is
    self-contained when pasted into a slide.
    """
    if not musiqwik or not barlines_per_line:
        return [musiqwik] if musiqwik else []

    prefix  = musiqwik[:2]   # '&4', '&3', etc.
    content = musiqwik[2:]

    segments: list[str] = []
    pos = 0
    for needed in barlines_per_line:
        found, i = 0, pos
        while i < len(content) and found < needed:
            if content[i] in '.)':
                found += 1
            i += 1
        segments.append(prefix + content[pos:i])
        pos = i

    # Attach any tail to the last segment (shouldn't happen with correct counts)
    if pos < len(content):
        if segments:
            segments[-1] += content[pos:]
        else:
            segments.append(prefix + content[pos:])

    return segments


# ---------------------------------------------------------------------------
# Lyric parsing
# ---------------------------------------------------------------------------

def parse_verses(lyrics_text: str) -> list[str]:
    """Split continuous lyric text into individual verse strings."""
    parts  = re.split(r'(?<!\w)(\d+\.)\s+', lyrics_text)
    verses = []
    if parts and parts[0].strip():
        verses.append(parts[0].strip())
    for i in range(1, len(parts) - 1, 2):
        v = parts[i + 1].strip() if (i + 1) < len(parts) else ''
        if v:
            verses.append(v)
    return verses


def _word_wrap(text: str, max_chars: int) -> list[str]:
    """Word-wrap text into lines of at most max_chars characters."""
    words = text.split()
    if not words:
        return ['']
    lines: list[str] = []
    current = ''
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += ' ' + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or ['']


def verse_to_pairs(verse: str, mel_lines: list[str],
                   max_lyric_chars: int = 25) -> list[tuple[str, str]]:
    """
    Divide verse text across the melody lines then word-wrap each portion
    to max_lyric_chars.  Returns a flat list of (melody_segment, lyric_line)
    pairs where every lyric line is ≤ max_lyric_chars characters.

    The melody segment for each phrase is repeated above every wrapped
    sub-line that belongs to it, so the "appropriate melody" always appears
    directly above each line of lyrics.
    """
    if not mel_lines:
        return [('', line) for line in _word_wrap(verse, max_lyric_chars)]

    words = verse.split()
    n     = len(mel_lines)
    per   = len(words) / n

    pairs: list[tuple[str, str]] = []
    for i, melody in enumerate(mel_lines):
        start = round(i * per)
        end   = min(round((i + 1) * per), len(words))
        group = ' '.join(words[start:end])
        for sub in _word_wrap(group, max_lyric_chars):
            pairs.append((melody, sub))

    return pairs


# ---------------------------------------------------------------------------
# Slide model
# ---------------------------------------------------------------------------

@dataclass
class Slide:
    kind:        str
    title:       str = ''
    attribution: str = ''
    verse_num:   int = 0
    pairs: list = field(default_factory=list)   # [(melody_str, lyric_str)]


def build_slides(hymn: dict, lines_per_slide: int = 3,
                 max_lyric_chars: int = 25) -> list[Slide]:
    slides: list[Slide] = [
        Slide('title', title=hymn['title'], attribution=hymn['attribution'])
    ]

    abc_lines  = _abc_body_lines(hymn['abc_text'])
    bar_counts = _barlines_per_line(abc_lines)
    mel_lines  = split_musiqwik(hymn['musiqwik'], bar_counts)

    if not mel_lines:
        print('[warn] No melody lines found; slides will contain lyrics only.',
              file=sys.stderr)

    for v_idx, verse in enumerate(parse_verses(hymn['lyrics_text'])):
        pairs = verse_to_pairs(verse, mel_lines, max_lyric_chars)

        for start in range(0, max(len(pairs), 1), lines_per_slide):
            slides.append(Slide(
                'content',
                title=hymn['title'],
                verse_num=v_idx + 1,
                pairs=pairs[start : start + lines_per_slide],
            ))

    return slides


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #0d0d1a; }
.slide {
    width: 1280px; height: 720px;
    display: flex; flex-direction: column;
    justify-content: center; align-items: flex-start;
    padding: 56px 80px;
    background: #1a1a2e;
    page-break-after: always; page-break-inside: avoid;
    overflow: hidden;
}
.title-slide { align-items: center; text-align: center; gap: 28px; }
.title-slide h1 {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 48px; font-weight: bold; color: #f0e68c; line-height: 1.25;
}
.title-slide .attr {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 18px; color: #9090b8; white-space: pre-line;
    max-width: 960px; line-height: 1.65;
}
.verse-label {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 15px; color: #6868a0; margin-bottom: 18px;
}
.pair { width: 100%; margin-bottom: 26px; }
.melody {
    font-family: 'Musiqwik', monospace;
    font-size: 38px; line-height: 1; color: #f0e68c;
    white-space: pre; letter-spacing: 0;
}
.lyric {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 26px; line-height: 1.35; color: #e4e4e4;
    margin-top: 6px;
}
@media print {
    body { background: white; }
    .slide {
        background: white;
        page-break-after: always; page-break-inside: avoid;
        width: 100vw; height: 100vh;
    }
    .title-slide h1, .melody { color: #111; }
    .title-slide .attr, .verse-label { color: #555; }
    .lyric { color: #222; }
}
"""


def _e(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


def to_html(slides: list[Slide]) -> str:
    title = _e(slides[0].title) if slides else ''
    out   = [
        '<!DOCTYPE html>', '<html lang="en">', '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=1280">',
        f'<title>{title}</title>',
        f'<style>{_CSS}</style>',
        '</head>', '<body>',
    ]

    for sl in slides:
        if sl.kind == 'title':
            attr_html = _e(sl.attribution).replace('\n', '<br>')
            out += [
                '<div class="slide title-slide">',
                f'<h1>{_e(sl.title)}</h1>',
                f'<div class="attr">{attr_html}</div>',
                '</div>',
            ]
        else:
            out += [
                '<div class="slide">',
                f'<p class="verse-label">Verse {sl.verse_num}</p>',
            ]
            for melody, lyric in sl.pairs:
                out += [
                    '<div class="pair">',
                    f'<div class="melody">{_e(melody)}</div>',
                    f'<div class="lyric">{_e(lyric)}</div>',
                    '</div>',
                ]
            out.append('</div>')

    out += ['</body>', '</html>']
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# PDF output (Playwright + pre-installed Chromium)
# ---------------------------------------------------------------------------

_CHROMIUM = '/opt/pw-browsers/chromium'


def to_pdf(html: str, out: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit('PDF requires playwright: pip install playwright')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=_CHROMIUM)
        page    = browser.new_page()
        page.set_content(html, wait_until='domcontentloaded')
        page.pdf(path=str(out), width='1280px', height='720px',
                 print_background=True)
        browser.close()


# ---------------------------------------------------------------------------
# PPTX output (python-pptx)
# ---------------------------------------------------------------------------

def to_pptx(slides: list[Slide], out: Path) -> None:
    try:
        from pptx import Presentation
        from pptx.util import Emu, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        sys.exit('PPTX requires python-pptx: pip install python-pptx')

    DARK   = RGBColor(0x1a, 0x1a, 0x2e)
    GOLD   = RGBColor(0xF0, 0xE6, 0x8C)
    WHITE  = RGBColor(0xE4, 0xE4, 0xE4)
    DIM    = RGBColor(0x90, 0x90, 0xB8)

    prs = Presentation()
    prs.slide_width  = Emu(9_144_000)  # 10 in
    prs.slide_height = Emu(5_143_500)  # 5.625 in  (16:9)

    W  = int(prs.slide_width)
    H  = int(prs.slide_height)
    MX = int(W * 0.06)
    MY = int(H * 0.08)

    blank = prs.slide_layouts[6]

    def _bg(sl):
        f = sl.background.fill
        f.solid()
        f.fore_color.rgb = DARK

    def _box(sl, left, top, width, height, lines_: list[tuple],
             fname: str, fsize: float, color: RGBColor,
             bold: bool = False, align=None, wrap: bool = True):
        """Add a text box; lines_ is a list of (text, font_name, font_size, color)
        or a single (text, …) tuple used for every paragraph."""
        from pptx.util import Pt
        box = sl.shapes.add_textbox(left, top, width, height)
        tf  = box.text_frame
        tf.word_wrap = wrap
        for i, (txt, fn, fs, clr) in enumerate(lines_):
            p  = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            if align:
                p.alignment = align
            run = p.add_run()
            run.text           = txt
            run.font.name      = fn
            run.font.size      = Pt(fs)
            run.font.color.rgb = clr
            run.font.bold      = bold
        return box

    def _tb(sl, left, top, width, height, text: str,
            fname: str, fsize: float, color: RGBColor,
            bold=False, align=None, wrap=True):
        """Single-font, multi-paragraph text box (splits on newlines)."""
        text_lines = text.splitlines() or ['']
        rows = [(t, fname, fsize, color) for t in text_lines]
        return _box(sl, left, top, width, height, rows,
                    fname, fsize, color, bold=bold, align=align, wrap=wrap)

    for data in slides:
        sl = prs.slides.add_slide(blank)
        _bg(sl)

        if data.kind == 'title':
            from pptx.enum.text import PP_ALIGN
            _tb(sl, MX, int(H * 0.20), W - 2*MX, int(H * 0.28),
                data.title, 'OpenDyslexic Mono', 36, GOLD,
                bold=True, align=PP_ALIGN.CENTER)
            _tb(sl, MX, int(H * 0.52), W - 2*MX, int(H * 0.42),
                data.attribution, 'OpenDyslexic Mono', 15, DIM,
                align=PP_ALIGN.CENTER)
        else:
            from pptx.enum.text import PP_ALIGN
            _tb(sl, MX, int(MY * 0.4), W - 2*MX, int(H * 0.08),
                f'Verse {data.verse_num}', 'OpenDyslexic Mono', 13, DIM)

            n      = len(data.pairs)
            avail  = H - MY - int(H * 0.12)
            pair_h = avail // max(n, 1)
            mel_h  = int(pair_h * 0.44)
            lyr_h  = int(pair_h * 0.50)

            for i, (melody, lyric) in enumerate(data.pairs):
                y = MY + int(H * 0.10) + i * pair_h
                _tb(sl, MX, y,          W - 2*MX, mel_h,
                    melody, 'Musiqwik', 26, GOLD, wrap=False)
                _tb(sl, MX, y + mel_h,  W - 2*MX, lyr_h,
                    lyric,  'OpenDyslexic Mono', 19, WHITE)

    prs.save(str(out))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description='Convert a hymn file to HTML, PDF, or PPTX presentation slides.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('--file', '-f', required=True,
                    help='Path to the hymn file')
    ap.add_argument('--format', choices=['html', 'pdf', 'pptx'], default='html',
                    help='Output format (default: html)')
    ap.add_argument('--output', '-o',
                    help='Output file path (default: <hymn_name>.<format>)')
    ap.add_argument('--lines-per-slide', type=int, default=3, metavar='N',
                    help='Max melody/lyric pairs per content slide (default: 3)')
    ap.add_argument('--max-lyric-chars', type=int, default=25, metavar='C',
                    help='Max characters per lyric line (default: 25)')
    args = ap.parse_args()

    src = Path(args.file)
    if not src.exists():
        sys.exit(f'Error: file not found: {src}')

    hymn   = parse_hymn_file(src)
    slides = build_slides(hymn, args.lines_per_slide, args.max_lyric_chars)
    out    = Path(args.output) if args.output else Path(src.name + '.' + args.format)

    if args.format == 'html':
        html = to_html(slides)
        out.write_text(html, encoding='utf-8')
    elif args.format == 'pdf':
        to_pdf(to_html(slides), out)
    elif args.format == 'pptx':
        to_pptx(slides, out)

    print(f'Written {len(slides)} slides → {out}')


if __name__ == '__main__':
    main()
