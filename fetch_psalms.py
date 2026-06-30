#!/usr/bin/env python3
"""
Fetch complete, genuine WEB-UE (World English Bible Updated Edition) psalm
texts and save them to a JSON file consumed by psalm_generator.py.

Text source: the BibleNLP/ebible GitHub mirror of eBible.org's USFM corpus
(https://github.com/BibleNLP/ebible). The mirror stores eBible.org's
"engwebu" translation (the same id as https://ebible.org/find/show.php?id=engwebu)
as one verse per line, aligned line-for-line against metadata/vref.txt, which
lists every canonical Bible verse reference in order. ebible.org itself
returns HTTP 403 to automated requests in this environment, but the GitHub
mirror is directly reachable, so this is the genuine WEB-UE text, not a KJV
substitute.

    corpus file:  corpus/eng-engwebu.txt   (one verse per line, WEB-UE text)
    index file:   metadata/vref.txt        (one verse reference per line, e.g. "PSA 18:1")

Both files have the same number of lines and are aligned 1:1, so the psalm
text for "PSA 18:*" is read by finding the matching line numbers in vref.txt
and pulling the corresponding lines from eng-engwebu.txt.

Usage:
    python3 fetch_psalms.py --batch 1,12,18,25,117,118 --output psalms_texts.json
    python3 fetch_psalms.py --batch 1-150 --output psalms_texts.json --update
    python3 fetch_psalms.py --psalm 18
"""

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

VREF_URL = "https://raw.githubusercontent.com/BibleNLP/ebible/main/metadata/vref.txt"
CORPUS_URL = "https://raw.githubusercontent.com/BibleNLP/ebible/main/corpus/eng-engwebu.txt"


def _fetch_lines(url: str) -> List[str]:
    """Fetch a text file as a list of lines.

    Uses curl rather than urllib.request: large files (the ~4.9MB WEB-UE
    corpus) reliably trigger http.client.IncompleteRead through urllib in
    this environment's proxy, while curl fetches them intact every time.
    """
    try:
        result = subprocess.run(
            ["curl", "-sS", "--fail", "-A", "Mozilla/5.0", url],
            capture_output=True, check=True, timeout=60,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise urllib.error.URLError(str(e)) from e
    return result.stdout.decode("utf-8").splitlines()


class WebUePsalter:
    """Loads the WEB-UE corpus once and serves text for any psalm chapter."""

    def __init__(self) -> None:
        try:
            self._vref = _fetch_lines(VREF_URL)
            self._corpus = _fetch_lines(CORPUS_URL)
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            sys.exit(
                f"[error] Could not reach the BibleNLP/ebible GitHub mirror: {e}\n"
                "This script requires that mirror to be reachable; it does not "
                "fall back to KJV or any other translation."
            )

        if len(self._vref) != len(self._corpus):
            sys.exit(
                f"[error] vref.txt ({len(self._vref)} lines) and "
                f"eng-engwebu.txt ({len(self._corpus)} lines) are misaligned; "
                "refusing to guess verse boundaries."
            )

        self._index: Dict[str, int] = {ref: i for i, ref in enumerate(self._vref)}

    def psalm_text(self, psalm_num: int) -> str:
        """Return the full WEB-UE text of a psalm chapter, verses joined with spaces."""
        verses: List[str] = []
        verse_num = 1
        while True:
            ref = f"PSA {psalm_num}:{verse_num}"
            line_no = self._index.get(ref)
            if line_no is None:
                break
            verse_text = self._corpus[line_no].strip()
            if verse_text:
                verses.append(verse_text)
            verse_num += 1

        if not verses:
            raise ValueError(f"No verses found for Psalm {psalm_num} (checked ref '{ref}')")

        return " ".join(verses)


def _parse_psalm_list(spec: str) -> List[int]:
    if "-" in spec:
        start, end = spec.split("-")
        return list(range(int(start), int(end) + 1))
    return [int(p.strip()) for p in spec.split(",") if p.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch genuine WEB-UE psalm texts from the BibleNLP/ebible GitHub mirror"
    )
    parser.add_argument("--psalm", type=int, help="Single psalm number")
    parser.add_argument("--batch", help="Comma-separated or range: '1,12,18' or '1-150'")
    parser.add_argument("--output", default="psalms_texts.json", help="Output JSON file")
    parser.add_argument(
        "--update", action="store_true",
        help="Merge into the existing JSON file instead of overwriting it",
    )
    args = parser.parse_args()

    if args.psalm:
        psalm_list = [args.psalm]
    elif args.batch:
        psalm_list = _parse_psalm_list(args.batch)
    else:
        parser.print_help()
        return 1

    print("[info] Loading WEB-UE corpus from BibleNLP/ebible GitHub mirror...", file=sys.stderr)
    psalter = WebUePsalter()

    output_path = Path(args.output)
    texts: Dict[str, str] = {}
    if args.update and output_path.exists():
        texts = json.loads(output_path.read_text(encoding="utf-8"))

    for psalm_num in psalm_list:
        try:
            texts[str(psalm_num)] = psalter.psalm_text(psalm_num)
            print(f"[ok] Psalm {psalm_num}: {len(texts[str(psalm_num)].split())} words", file=sys.stderr)
        except ValueError as e:
            print(f"[error] {e}", file=sys.stderr)
            return 1

    output_path.write_text(json.dumps(texts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n✓ Saved {len(texts)} psalm(s) to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
