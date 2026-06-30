#!/usr/bin/env python3
"""
Generate complete Gregorian chant psalm files from source data.

Usage:
  python3 psalm_generator.py --psalm 1 --tone 1 --file hymns/8.0_Psalm_Settings/Psalm_001
  python3 psalm_generator.py --batch 1,12,18,25,117,118  # Process multiple psalms
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

# Gregorian Psalm Tones (8 tones from ancient liturgy)
GREGORIAN_TONES = {
    1: {
        "reciting": "D5",
        "mediant": "F-E-D",
        "final": "G",
        "abc_tone": "d d d d | d d d d | d d e d | d2 c B | A4 ||",
        "description": "Tone 1: Reciting D5, mediant F-E-D, final G"
    },
    2: {
        "reciting": "C5",
        "mediant": "F-E-D-E",
        "final": "E",
        "abc_tone": "c c c c | c c c c | c c d c | B A G A | A4 ||",
        "description": "Tone 2: Reciting C5, mediant F-E-D-E, final E"
    },
    3: {
        "reciting": "B4",
        "mediant": "G-A-B-c",
        "final": "E",
        "abc_tone": "B B B B | B B B B | G A B c | c B A G | G4 ||",
        "description": "Tone 3: Reciting B4, mediant G-A-B-c, final E"
    },
    4: {
        "reciting": "A4",
        "mediant": "G-F-E",
        "final": "E",
        "abc_tone": "A A A A | A A A A | G G F E | D2 E F | G4 ||",
        "description": "Tone 4: Reciting A4, mediant G-F-E, final E"
    },
    5: {
        "reciting": "G4",
        "mediant": "c-B-G",
        "final": "E",
        "abc_tone": "G G G G | G G G G | c c B G | G F E D | E4 ||",
        "description": "Tone 5: Reciting G4, mediant c-B-G, final E"
    },
    6: {
        "reciting": "F4",
        "mediant": "G-A-G-F",
        "final": "F",
        "abc_tone": "F F F F | F F F F | G G A G | G F E D | F4 ||",
        "description": "Tone 6: Reciting F4, mediant G-A-G-F, final F"
    },
    7: {
        "reciting": "G4",
        "mediant": "A-B-c",
        "final": "G",
        "abc_tone": "G G G G | G G G G | G A B c | c B A G | G4 ||",
        "description": "Tone 7: Reciting G4, mediant A-B-c, final G"
    },
    8: {
        "reciting": "G4",
        "mediant": "A-G",
        "final": "C",
        "abc_tone": "G G G G | G G G G | G G A G | G F E D | C4 ||",
        "description": "Tone 8: Reciting G4, mediant A-G, final C"
    }
}

# Antiphon assignments for psalms
ANTIPHON_ASSIGNMENTS = {
    1: {"tone": 1, "antiphon": "Blessed is the man"},
    12: {"tone": 4, "antiphon": "Help, O Lord"},
    18: {"tone": 3, "antiphon": "The heavens declare"},
    25: {"tone": 8, "antiphon": "Unto you, O Lord"},
    117: {"tone": 1, "antiphon": "Praise the Lord"},
    118: {"tone": 6, "antiphon": "Give thanks to the Lord"}
}

# Psalm text database (reference texts - update with full WEB-UE versions)
PSALM_TEXTS = {
    1: "Blessed is the man that walketh not in the counsel of the ungodly, nor standeth in the way of sinners, nor sitteth in the seat of the scornful. But his delight is in the law of the LORD; and in his law doth he meditate day and night.",
    12: "Help, LORD; for the godly man ceaseth; for the faithful fail from among the children of men. They speak vanity every one with his neighbour: with flattering lips and with a double heart do they speak.",
    18: "The heavens declare the glory of God; and the firmament sheweth his handywork. Day unto day uttereth speech, and night unto night sheweth knowledge.",
    25: "Unto thee, O LORD, do I lift up my soul. O my God, I trust in thee: let me not be ashamed, let not mine enemies triumph over me.",
    117: "Praise the LORD, all ye nations: praise him, all ye people. For his merciful kindness is great toward us: and the truth of the LORD endureth for ever. Praise ye the LORD.",
    118: "O give thanks unto the LORD; for he is good: because his mercy endureth for ever."
}

class PsalmGenerator:
    def __init__(self, psalms_dir: Optional[str] = None):
        self.psalms_dir = Path(psalms_dir or "hymns/8.0_Psalm_Settings")
        self.psalms_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_psalm_file(self, psalm_num: int, tone: Optional[int] = None, 
                          psalm_text: Optional[str] = None) -> str:
        """Generate a complete psalm file with proper structure."""
        
        if tone is None and psalm_num in ANTIPHON_ASSIGNMENTS:
            tone = ANTIPHON_ASSIGNMENTS[psalm_num]["tone"]
        if tone is None:
            tone = 1
        if tone not in GREGORIAN_TONES:
            raise ValueError(f"Invalid tone: {tone}. Must be 1-8.")
        
        antiphon = ""
        if psalm_num in ANTIPHON_ASSIGNMENTS:
            antiphon = ANTIPHON_ASSIGNMENTS[psalm_num]["antiphon"]
        
        if psalm_text is None:
            psalm_text = PSALM_TEXTS.get(psalm_num, 
                f"[Psalm {psalm_num} text — World English Bible Updated Edition to be added]")
        
        tone_data = GREGORIAN_TONES[tone]
        return self._build_psalm_content(psalm_num, tone, tone_data, antiphon, psalm_text)
    
    def _build_psalm_content(self, psalm_num: int, tone: int, tone_data: Dict,
                            antiphon: str, psalm_text: str) -> str:
        """Build the complete psalm file content."""
        
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
[Antiphon] {antiphon} [Psalm text follows]

{psalm_text}

[Antiphon closes] {antiphon}

#Citations and References

Psalm: {psalm_num} (World English Bible Updated Edition)
Chant: 'Gregorian Psalm Tone {tone}' Ancient Gregorian chant; public domain.
Setting: Traditional antiphonal setting with Gregorian chant tone; public domain.
copyright: public domain.

https://openhymnal.org/
"""
        return content
    
    def save_psalm(self, psalm_num: int, tone: Optional[int] = None,
                  psalm_text: Optional[str] = None, overwrite: bool = False) -> Path:
        """Save a psalm file to disk."""
        
        psalm_padded = f"{psalm_num:03d}"
        filename = self.psalms_dir / f"Psalm_{psalm_padded}"
        
        if filename.exists() and not overwrite:
            with open(filename, 'r') as f:
                content = f.read()
                if "[to be added]" in content:
                    print(f"Stub found: {filename} (can overwrite with --force)")
        
        content = self.generate_psalm_file(psalm_num, tone, psalm_text)
        
        with open(filename, 'w') as f:
            f.write(content)
        
        print(f"Generated: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description="Generate Gregorian chant psalm files")
    parser.add_argument("--psalm", type=int, help="Single psalm number to generate")
    parser.add_argument("--tone", type=int, help="Gregorian tone (1-8); auto-assigned if not specified")
    parser.add_argument("--batch", help="Comma-separated psalm numbers: 1,12,18,25,117,118")
    parser.add_argument("--dir", default="hymns/8.0_Psalm_Settings", help="Output directory")
    parser.add_argument("--text-file", help="JSON file mapping psalm numbers to text")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    texts = PSALM_TEXTS.copy()
    if args.text_file and Path(args.text_file).exists():
        with open(args.text_file, 'r') as f:
            texts.update(json.load(f))
    
    gen = PsalmGenerator(args.dir)
    psalms_to_generate = []
    
    if args.psalm:
        psalms_to_generate.append(args.psalm)
    elif args.batch:
        psalms_to_generate = [int(p.strip()) for p in args.batch.split(',')]
    else:
        parser.print_help()
        return 1
    
    for psalm_num in psalms_to_generate:
        try:
            tone = ANTIPHON_ASSIGNMENTS.get(psalm_num, {}).get("tone")
            if args.tone:
                tone = args.tone
            text = texts.get(psalm_num)
            gen.save_psalm(psalm_num, tone, text, overwrite=args.force)
        except Exception as e:
            print(f"Error generating Psalm {psalm_num}: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
