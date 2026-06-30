#!/usr/bin/env python3
"""
Generate complete Gregorian chant psalm files with full verse texts.

Usage:
    python3 psalm_generator.py --batch 1,12,18,25,117,118 --force
    python3 psalm_generator.py --batch 1-150 --text-file psalms_texts.json --include-doxology
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

GREGORIAN_TONES = {
    1: {"reciting": "D5", "mediant": "F-E-D", "final": "G",
        "abc_tone": "d d d d | d d d d | d d e d | d2 c B | A4 ||",
        "description": "Tone 1: Reciting D5, mediant F-E-D, final G"},
    2: {"reciting": "C5", "mediant": "F-E-D-E", "final": "E",
        "abc_tone": "c c c c | c c c c | c c d c | B A G A | A4 ||",
        "description": "Tone 2: Reciting C5, mediant F-E-D-E, final E"},
    3: {"reciting": "B4", "mediant": "G-A-B-c", "final": "E",
        "abc_tone": "B B B B | B B B B | G A B c | c B A G | G4 ||",
        "description": "Tone 3: Reciting B4, mediant G-A-B-c, final E"},
    4: {"reciting": "A4", "mediant": "G-F-E", "final": "E",
        "abc_tone": "A A A A | A A A A | G G F E | D2 E F | G4 ||",
        "description": "Tone 4: Reciting A4, mediant G-F-E, final E"},
    5: {"reciting": "G4", "mediant": "c-B-G", "final": "E",
        "abc_tone": "G G G G | G G G G | c c B G | G F E D | E4 ||",
        "description": "Tone 5: Reciting G4, mediant c-B-G, final E"},
    6: {"reciting": "F4", "mediant": "G-A-G-F", "final": "F",
        "abc_tone": "F F F F | F F F F | G G A G | G F E D | F4 ||",
        "description": "Tone 6: Reciting F4, mediant G-A-G-F, final F"},
    7: {"reciting": "G4", "mediant": "A-B-c", "final": "G",
        "abc_tone": "G G G G | G G G G | G A B c | c B A G | G4 ||",
        "description": "Tone 7: Reciting G4, mediant A-B-c, final G"},
    8: {"reciting": "G4", "mediant": "A-G", "final": "C",
        "abc_tone": "G G G G | G G G G | G G A G | G F E D | C4 ||",
        "description": "Tone 8: Reciting G4, mediant A-G, final C"},
    9: {"reciting": "A4 (1st half) / G4 (2nd half)", "mediant": "G-A-G-E", "final": "D",
        "abc_tone": "A A A A | A A A A | G A G E | G G G G | G F E D | D4 ||",
        "description": "Tonus Peregrinus ('wandering tone'): reciting A4 in the first half-verse, "
                        "G4 in the second, final D — the one Gregorian tone outside the standard "
                        "8-tone system, traditionally proper to Psalm 113/117 (Vulgate)/114"},
}

# Traditional tone assignments, researched and cited per psalm rather than
# auto-rotated. Gregorian/Sarum practice does not have one universal fixed
# psalm-to-tone chart -- strictly, "the tone of the psalm comes from the
# antiphon" sung with it on a given occasion. The citations below record a
# real, attested historical assignment for each psalm currently in this
# project so the choice is traceable rather than arbitrary. Adding a new
# psalm requires the same kind of citation; see the error raised below if
# none is supplied.
ANTIPHON_ASSIGNMENTS = {
    1: {"tone": 1, "antiphon": "Blessed is the man",
        "source": "Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone I; "
                   "Latin incipit 'Beatus vir qui non abiit'"},
    12: {"tone": 4, "antiphon": "Help, LORD",
         "source": "Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone IV; "
                    "Latin incipit 'Salvum me fac, Domine'"},
    18: {"tone": 1, "antiphon": "I love you, LORD, my strength",
         "source": "Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone I; "
                    "Latin incipit 'Diligam te, Domine'"},
    25: {"tone": 8, "antiphon": "To you, LORD, I lift up my soul",
         "source": "Roman Gradual, Introit for Advent I 'Ad te levavi animam meam', Mode VIII"},
    117: {"tone": 9, "antiphon": "Praise the LORD, all you nations",
          "source": "Sarum Tonale / St. Dunstan's Plainsong Psalter, Tonus Peregrinus; "
                     "Latin incipit 'Laudate Dominum omnes gentes'"},
    118: {"tone": 1, "antiphon": "Give thanks to the LORD",
          "source": "Sarum Tonale / St. Dunstan's Plainsong Psalter, Tone I; "
                     "Latin incipit 'Confitemini Domino'"},
}

DOXOLOGY = "Glory be to the Father, and to the Son, and to the Holy Spirit; as it was in the beginning, is now, and ever shall be, world without end. Amen."

class PsalmGenerator:
    def __init__(self, psalms_dir: Optional[str] = None, texts: Optional[Dict] = None):
        self.psalms_dir = Path(psalms_dir or "hymns/8.0_Psalm_Settings")
        self.psalms_dir.mkdir(parents=True, exist_ok=True)
        self.texts = texts or {}
    
    def generate_psalm_file(self, psalm_num: int, tone: Optional[int] = None, 
                          psalm_text: Optional[str] = None,
                          include_doxology: bool = False) -> str:
        """Generate a complete psalm file with full text."""
        
        if tone is None and psalm_num in ANTIPHON_ASSIGNMENTS:
            tone = ANTIPHON_ASSIGNMENTS[psalm_num]["tone"]
        if tone is None:
            raise ValueError(
                f"No traditional tone assignment found for Psalm {psalm_num}. "
                "This project does not auto-assign tones by rotation. Research a "
                "real, citable historical assignment (e.g. via the Sarum Tonale / "
                "St. Dunstan's Plainsong Psalter, or the antiphon's liturgical mode "
                "in the Roman Gradual) and add it to ANTIPHON_ASSIGNMENTS with a "
                "'source' citation, or pass --tone explicitly."
            )
        if tone not in GREGORIAN_TONES:
            raise ValueError(f"Invalid tone: {tone}")

        antiphon = ANTIPHON_ASSIGNMENTS.get(psalm_num, {}).get("antiphon", f"Psalm {psalm_num}")
        source = ANTIPHON_ASSIGNMENTS.get(psalm_num, {}).get("source")

        if psalm_text is None:
            psalm_text = self.texts.get(str(psalm_num),
                f"[Psalm {psalm_num} text — World English Bible Updated Edition to be added]")

        tone_data = GREGORIAN_TONES[tone]
        return self._build_psalm_content(psalm_num, tone, tone_data, antiphon,
                                        psalm_text, include_doxology, source)

    def _build_psalm_content(self, psalm_num: int, tone: int, tone_data: Dict,
                            antiphon: str, psalm_text: str, include_doxology: bool,
                            source: Optional[str] = None) -> str:
        """Build complete psalm file content."""
        
        doxology_section = ""
        if include_doxology:
            doxology_section = f"\n\n{DOXOLOGY}"

        chant_line = f"Chant: 'Gregorian Psalm Tone {tone}' Ancient Gregorian chant; public domain."
        if source:
            chant_line = (
                f"Chant: 'Gregorian Psalm Tone {tone}' Ancient Gregorian chant; public domain. "
                f"Traditional assignment per {source}."
            )

        content = f"""Psalm {psalm_num}

Tags: ancient, liturgical, psalm

# Melody

## ABC
X:1
T:Psalm {psalm_num} — Gregorian Chant Tone {tone}
C:Gregorian chant; ancient, public domain
S:Traditional Gregorian psalm tone; public domain
M:C
L:1/4
K:C
%% {tone_data['description']}
{tone_data['abc_tone']}

## Musiquik
[Psalm {psalm_num} Musiquik rendering to be generated by abc_to_musiqwik.py]

#Lyrics
[Antiphon] {antiphon}

{psalm_text}{doxology_section}

[Antiphon closes] {antiphon}

#Citations and References

Psalm: {psalm_num} (World English Bible Updated Edition)
{chant_line}
Setting: Traditional antiphonal setting with Gregorian chant tone; public domain.
copyright: public domain.

https://openhymnal.org/
"""
        return content
    
    def save_psalm(self, psalm_num: int, tone: Optional[int] = None,
                  psalm_text: Optional[str] = None, include_doxology: bool = False,
                  overwrite: bool = False) -> Path:
        """Save a psalm file to disk."""
        
        psalm_padded = f"{psalm_num:03d}"
        filename = self.psalms_dir / f"Psalm_{psalm_padded}"
        
        if filename.exists() and not overwrite:
            with open(filename, 'r') as f:
                content = f.read()
                if "[to be added]" in content:
                    print(f"[info] Stub found: {filename}")
        
        content = self.generate_psalm_file(psalm_num, tone, psalm_text, include_doxology)
        
        with open(filename, 'w') as f:
            f.write(content)
        
        print(f"✓ Generated: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description="Generate Gregorian chant psalm files with complete texts")
    parser.add_argument("--psalm", type=int, help="Single psalm number")
    parser.add_argument("--tone", type=int, help="Gregorian tone (1-8); auto-assigned if not specified")
    parser.add_argument("--batch", help="Comma-separated or range: '1,12,18' or '1-150'")
    parser.add_argument("--dir", default="hymns/8.0_Psalm_Settings", help="Output directory")
    parser.add_argument("--text-file", default="psalms_texts.json", help="JSON file with psalm texts")
    parser.add_argument("--include-doxology", action="store_true", help="Add Gloria Patri to each psalm")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    texts = {}
    text_file = Path(args.text_file)
    if text_file.exists():
        with open(text_file, 'r') as f:
            texts = json.load(f)
        print(f"[info] Loaded {len(texts)} psalm texts from {args.text_file}")
    else:
        print(f"[warn] Text file not found: {args.text_file}", file=sys.stderr)
    
    gen = PsalmGenerator(args.dir, texts)
    psalms_to_generate = []
    
    if args.psalm:
        psalms_to_generate.append(args.psalm)
    elif args.batch:
        if "-" in args.batch:
            start, end = args.batch.split("-")
            psalms_to_generate = list(range(int(start), int(end) + 1))
        else:
            psalms_to_generate = [int(p.strip()) for p in args.batch.split(",")]
    else:
        parser.print_help()
        return 1
    
    print(f"[info] Generating {len(psalms_to_generate)} psalms...\n")
    
    for psalm_num in psalms_to_generate:
        try:
            tone = ANTIPHON_ASSIGNMENTS.get(psalm_num, {}).get("tone")
            if args.tone:
                tone = args.tone
            text = texts.get(str(psalm_num))
            gen.save_psalm(psalm_num, tone, text, args.include_doxology, args.force)
        except Exception as e:
            print(f"[error] Psalm {psalm_num}: {e}", file=sys.stderr)
            return 1
    
    print(f"\n✓ Complete! Run abc_to_musiqwik.py to generate MusiQwik renderings:")
    print(f"   for i in {{{psalms_to_generate[0]:03d}..{psalms_to_generate[-1]:03d}}}; do")
    print(f"     python3 abc_to_musiqwik.py --file hymns/8.0_Psalm_Settings/Psalm_$i")
    print(f"   done")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
