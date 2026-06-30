#!/usr/bin/env python3
"""
hymn_to_bulletin.py — Convert a hymn file to a printable sheet-music / service
bulletin in PDF, ODT, or DOCX.

Where hymn_to_presentation.py paginates a hymn into projection slides, this
script lays the same hymn out as a single flowing document suitable for a
printed worship bulletin or a one-page lead sheet:

  • a title heading,
  • a "sheet music" block — the tune rendered in the Musiqwik font with the
    first stanza's words set beneath each melody line,
  • the remaining stanzas printed as numbered prose, and
  • the full citation / copyright block as a footer.

It shares hymn_to_presentation.py's hymn-file parser, melody splitter, lyric
segment/antiphon handling, and stanza tradition-filter, so it accepts the same
arguments and produces the same stanza selection.  It can be run on its own or
triggered from hymn_to_presentation.py via --bulletin.

Usage:
    python3 hymn_to_bulletin.py --file <hymn_file>                  # PDF (default)
    python3 hymn_to_bulletin.py --file <hymn_file> --format odt
    python3 hymn_to_bulletin.py --file <hymn_file> --format docx -o out.docx
    python3 hymn_to_bulletin.py --file <hymn_file> --no-antiphon
    python3 hymn_to_bulletin.py --file <hymn_file> -I lutheran -X saints

Tradition filtering, antiphon handling, and refrain expansion behave exactly as
documented in hymn_to_presentation.py (the logic is imported from it).

Dependencies:
    PDF       — playwright (pip install playwright) + Chromium at /opt/pw-browsers
    ODT/DOCX  — Python standard library only
"""

import argparse
import io
import sys
import zipfile
from dataclasses import dataclass, field
from html import escape as _xe
from pathlib import Path

import hymn_to_presentation as hp


# ---------------------------------------------------------------------------
# Bulletin document model
# ---------------------------------------------------------------------------

@dataclass
class Bulletin:
    title:        str = ''
    attribution:  str = ''
    # The tune as (melody_segment, lyric_line) pairs — first stanza beneath the
    # staff.  When a hymn has no lyrics the lyric half is empty.
    melody_pairs: list = field(default_factory=list)
    # Every stanza's full text, in order, after tradition filtering.
    verses:       list = field(default_factory=list)


def build_bulletin(hymn: dict,
                   max_lyric_chars: int = 40,
                   include_tags: list[str] | None = None,
                   exclude_tags: list[str] | None = None,
                   no_antiphon: bool = False) -> Bulletin:
    """Assemble a Bulletin from a parsed hymn dict, reusing the presentation
    module's melody splitting, antiphon/refrain handling, and stanza filter."""
    abc_lines  = hp._abc_body_lines(hymn['abc_text'])
    bar_counts = hp._barlines_per_line(abc_lines)
    mel_lines  = hp.split_musiqwik(hymn['musiqwik'], bar_counts)

    if not mel_lines:
        print('[warn] No melody lines found; bulletin will contain lyrics only.',
              file=sys.stderr)

    lyrics_text = hymn['lyrics_text']
    if no_antiphon:
        lyrics_text = hp.strip_antiphon(lyrics_text)

    lyrics_text, segment_text = hp.extract_lyric_segment(lyrics_text)
    lyrics_text = hp.expand_inline_segments(lyrics_text, segment_text)

    all_verses = hp.parse_verses(lyrics_text)
    verses = hp.filter_verses(
        all_verses,
        hymn.get('file_tags', []),
        include_tags or [],
        exclude_tags or [],
    )
    verse_texts = [text for text, _tags in verses]

    if verse_texts:
        melody_pairs = hp.verse_to_pairs(verse_texts[0], mel_lines, max_lyric_chars)
    else:
        melody_pairs = [(m, '') for m in mel_lines]

    return Bulletin(
        title=hymn['title'],
        attribution=hymn['attribution'],
        melody_pairs=melody_pairs,
        verses=verse_texts,
    )


# ---------------------------------------------------------------------------
# HTML output (also the source for the PDF renderer)
# ---------------------------------------------------------------------------

_CSS = """
@page { size: letter; margin: 1in; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #ffffff; color: #111111;
    font-family: 'OpenDyslexic Mono', monospace;
    padding: 0; line-height: 1.4;
}
h1 {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 24pt; font-weight: bold; text-align: center;
    margin-bottom: 18px;
}
.sheet { margin-bottom: 22px; }
.pair { margin-bottom: 10px; break-inside: avoid; }
.melody {
    font-family: 'Musiqwik', monospace;
    font-size: 22pt; line-height: 1; color: #111111;
    white-space: pre; letter-spacing: 0;
}
.lyric {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 12pt; color: #111111; margin-top: 3px;
}
.verses { margin-bottom: 24px; }
.verse {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 12pt; margin-bottom: 12px; text-align: justify;
}
.verse .num { font-weight: bold; margin-right: 4px; }
.attr {
    font-family: 'OpenDyslexic Mono', monospace;
    font-size: 9pt; color: #555555; white-space: pre-line;
    border-top: 1px solid #cccccc; padding-top: 10px; margin-top: 8px;
}
"""


def to_html(b: Bulletin) -> str:
    out = [
        '<!DOCTYPE html>', '<html lang="en">', '<head>',
        '<meta charset="UTF-8">',
        f'<title>{_xe(b.title)}</title>',
        f'<style>{_CSS}</style>',
        '</head>', '<body>',
        f'<h1>{_xe(b.title)}</h1>',
    ]

    if b.melody_pairs:
        out.append('<div class="sheet">')
        for melody, lyric in b.melody_pairs:
            out.append('<div class="pair">')
            if melody:
                out.append(f'<div class="melody">{_xe(melody)}</div>')
            if lyric:
                out.append(f'<div class="lyric">{_xe(lyric)}</div>')
            out.append('</div>')
        out.append('</div>')

    # Stanzas after the first are printed as numbered prose (the first stanza
    # already appears under the staff above).
    extra = b.verses[1:] if len(b.verses) > 1 else []
    if extra:
        out.append('<div class="verses">')
        for i, verse in enumerate(extra, start=2):
            out.append(
                f'<p class="verse"><span class="num">{i}.</span>{_xe(verse)}</p>'
            )
        out.append('</div>')

    if b.attribution:
        out.append(f'<div class="attr">{_xe(b.attribution)}</div>')

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
        page.pdf(path=str(out), format='Letter', print_background=True,
                 margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'})
        browser.close()


# ---------------------------------------------------------------------------
# ODT output (OpenDocument Text — stdlib only)
# ---------------------------------------------------------------------------

_ODT_STYLES = """\
<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  office:version="1.3">
  <office:font-face-decls>
    <style:font-face style:name="Musiqwik" svg:font-family="Musiqwik"
      xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"/>
    <style:font-face style:name="OpenDyslexic Mono" svg:font-family="OpenDyslexic Mono"
      xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"/>
  </office:font-face-decls>
  <office:styles>
    <style:style style:name="Title" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.25cm"/>
      <style:text-properties style:font-name="OpenDyslexic Mono"
        fo:font-size="24pt" fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="Melody" style:family="paragraph">
      <style:text-properties style:font-name="Musiqwik" fo:font-size="22pt"/>
    </style:style>
    <style:style style:name="Lyric" style:family="paragraph">
      <style:paragraph-properties fo:margin-bottom="0.2cm"/>
      <style:text-properties style:font-name="OpenDyslexic Mono" fo:font-size="12pt"/>
    </style:style>
    <style:style style:name="Verse" style:family="paragraph">
      <style:paragraph-properties fo:text-align="justify" fo:margin-bottom="0.25cm"/>
      <style:text-properties style:font-name="OpenDyslexic Mono" fo:font-size="12pt"/>
    </style:style>
    <style:style style:name="Attr" style:family="paragraph">
      <style:paragraph-properties fo:margin-top="0.4cm"/>
      <style:text-properties style:font-name="OpenDyslexic Mono"
        fo:font-size="9pt" fo:color="#555555"/>
    </style:style>
  </office:styles>
</office:document-styles>"""


def to_odt(b: Bulletin, out: Path) -> None:
    def _p(style: str, text: str) -> str:
        return f'<text:p text:style-name="{style}">{_xe(text)}</text:p>'

    paras: list[str] = [_p('Title', b.title)]

    for melody, lyric in b.melody_pairs:
        if melody:
            paras.append(_p('Melody', melody))
        if lyric:
            paras.append(_p('Lyric', lyric))

    for i, verse in enumerate(b.verses[1:], start=2):
        paras.append(_p('Verse', f'{i}. {verse}'))

    if b.attribution:
        for line in b.attribution.splitlines() or ['']:
            paras.append(_p('Attr', line))

    content_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<office:document-content'
        ' xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
        ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
        ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
        ' xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"'
        ' office:version="1.3">'
        '<office:body><office:text>'
        + ''.join(paras)
        + '</office:text></office:body></office:document-content>'
    )

    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest'
        ' xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"'
        ' manifest:version="1.3">'
        '<manifest:file-entry manifest:full-path="/"'
        ' manifest:media-type="application/vnd.oasis.opendocument.text"'
        ' manifest:version="1.3"/>'
        '<manifest:file-entry manifest:full-path="content.xml"'
        ' manifest:media-type="text/xml"/>'
        '<manifest:file-entry manifest:full-path="styles.xml"'
        ' manifest:media-type="text/xml"/>'
        '</manifest:manifest>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            zipfile.ZipInfo('mimetype'),
            b'application/vnd.oasis.opendocument.text',
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr('META-INF/manifest.xml', manifest)
        zf.writestr('styles.xml', _ODT_STYLES)
        zf.writestr('content.xml', content_xml)
    out.write_bytes(buf.getvalue())


# ---------------------------------------------------------------------------
# DOCX output (Office Open XML WordprocessingML — stdlib only)
# ---------------------------------------------------------------------------

_DOCX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml"'
    ' ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)

_DOCX_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
    ' Target="word/document.xml"/>'
    '</Relationships>'
)

_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def to_docx(b: Bulletin, out: Path) -> None:
    def _para(text: str, font: str, half_pts: int,
              *, bold: bool = False, align: str | None = None,
              color: str | None = None) -> str:
        """A single WordprocessingML paragraph with one run, fonts set
        directly so no styles.xml is required."""
        ppr = ''
        if align:
            ppr += f'<w:jc w:val="{align}"/>'
        ppr_xml = f'<w:pPr>{ppr}</w:pPr>' if ppr else ''

        rpr = (
            f'<w:rFonts w:ascii="{_xe(font)}" w:hAnsi="{_xe(font)}" w:cs="{_xe(font)}"/>'
            f'<w:sz w:val="{half_pts}"/><w:szCs w:val="{half_pts}"/>'
        )
        if bold:
            rpr += '<w:b/>'
        if color:
            rpr += f'<w:color w:val="{color}"/>'

        return (
            f'<w:p>{ppr_xml}'
            f'<w:r><w:rPr>{rpr}</w:rPr>'
            f'<w:t xml:space="preserve">{_xe(text)}</w:t></w:r></w:p>'
        )

    body: list[str] = [
        _para(b.title, 'OpenDyslexic Mono', 48, bold=True, align='center'),
    ]

    for melody, lyric in b.melody_pairs:
        if melody:
            body.append(_para(melody, 'Musiqwik', 44))
        if lyric:
            body.append(_para(lyric, 'OpenDyslexic Mono', 24))

    for i, verse in enumerate(b.verses[1:], start=2):
        body.append(_para(f'{i}. {verse}', 'OpenDyslexic Mono', 24, align='both'))

    if b.attribution:
        for line in b.attribution.splitlines() or ['']:
            body.append(_para(line, 'OpenDyslexic Mono', 18, color='555555'))

    # Letter page, 1in margins (twips: 1in = 1440).
    sect = (
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"'
        ' w:header="720" w:footer="720" w:gutter="0"/>'
        '</w:sectPr>'
    )

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_W_NS}">'
        '<w:body>'
        + ''.join(body)
        + sect
        + '</w:body></w:document>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', _DOCX_CONTENT_TYPES)
        zf.writestr('_rels/.rels', _DOCX_RELS)
        zf.writestr('word/document.xml', document_xml)
    out.write_bytes(buf.getvalue())


# ---------------------------------------------------------------------------
# Public entry point (importable; used by hymn_to_presentation.py --bulletin)
# ---------------------------------------------------------------------------

def generate_bulletin(src: Path, fmt: str = 'pdf', output: Path | None = None,
                      *, max_lyric_chars: int = 40,
                      include: list[str] | None = None,
                      exclude: list[str] | None = None,
                      no_antiphon: bool = False) -> Path:
    """Parse the hymn at *src* and write a bulletin in *fmt* (pdf|odt|docx).

    Returns the path written.  Shared by the CLI below and by
    hymn_to_presentation.py's --bulletin option.
    """
    hymn = hp.parse_hymn_file(src)
    b = build_bulletin(hymn, max_lyric_chars, include, exclude, no_antiphon)
    out = output if output else Path(src.name + '.' + fmt)

    if fmt == 'pdf':
        to_pdf(to_html(b), out)
    elif fmt == 'odt':
        to_odt(b, out)
    elif fmt == 'docx':
        to_docx(b, out)
    else:
        raise ValueError(f'Unsupported bulletin format: {fmt}')

    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description='Convert a hymn file to a printable sheet-music / service '
                    'bulletin in PDF, ODT, or DOCX.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('--file', '-f', required=True,
                    help='Path to the hymn file')
    ap.add_argument('--format', choices=['pdf', 'odt', 'docx'],
                    default='pdf', help='Output format (default: pdf)')
    ap.add_argument('--output', '-o',
                    help='Output file path (default: <hymn_name>.<format>)')
    # Accepted for parity with hymn_to_presentation.py.  A bulletin flows the
    # tune continuously rather than paginating, so --lines-per-slide does not
    # affect the layout; it is honoured silently so the two tools share an
    # identical argument surface.
    ap.add_argument('--lines-per-slide', type=int, default=3, metavar='N',
                    help='Accepted for parity with hymn_to_presentation.py; '
                         'a bulletin is not paginated, so this is ignored')
    ap.add_argument('--max-lyric-chars', type=int, default=40, metavar='C',
                    help='Max characters per lyric line under the staff (default: 40)')
    ap.add_argument('--include', '-I', action='append', default=[], metavar='TAG',
                    help='Include only stanzas matching this tag (tradition or theological); '
                         'tradition tags also imply doctrinal exclusions (repeatable)')
    ap.add_argument('--exclude', '-X', action='append', default=[], metavar='TAG',
                    help='Exclude stanzas matching this tag (tradition or theological; repeatable)')
    ap.add_argument('--no-antiphon', action='store_true',
                    help='Omit the [Antiphon]/[Antiphon closes] text from psalm chant settings '
                         '(antiphon is included by default)')
    args = ap.parse_args()

    src = Path(args.file)
    if not src.exists():
        sys.exit(f'Error: file not found: {src}')

    hymn = hp.parse_hymn_file(src)

    # Same interactive tradition-filter prompt as hymn_to_presentation.py.
    if not args.include and not args.exclude:
        preview_text = hymn['lyrics_text']
        if args.no_antiphon:
            preview_text = hp.strip_antiphon(preview_text)
        preview_text, _segment = hp.extract_lyric_segment(preview_text)
        args.include, args.exclude = hp._prompt_tradition_filter(
            hymn['title'],
            hymn.get('file_tags', []),
            hp.parse_verses(preview_text),
        )

    out = generate_bulletin(
        src, args.format,
        Path(args.output) if args.output else None,
        max_lyric_chars=args.max_lyric_chars,
        include=args.include,
        exclude=args.exclude,
        no_antiphon=args.no_antiphon,
    )

    print(f'Written bulletin → {out}')


if __name__ == '__main__':
    main()
