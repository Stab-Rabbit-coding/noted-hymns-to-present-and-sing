#!/usr/bin/env python3
"""
Build a comprehensive searchable index of all hymns and psalms.

Scans the hymns directory, extracts metadata from each file (title, aliases,
tune, tags, location), and generates a JSON index for fast searching.

Usage:
    python3 build_index.py
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any

def parse_hymn_file(filepath: str) -> Dict[str, Any]:
    """
    Parse a hymn file and extract metadata.

    Returns a dict with keys:
        - title: main title
        - aliases: list of alternate names
        - tune: tune name(s)
        - tags: list of tags
        - file: relative file path
        - location: section/directory
        - section_number: numeric section (e.g. 7.14, 8.23)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    # Extract title (first non-empty line)
    lines = content.split('\n')
    title = lines[0].strip() if lines else ""

    if not title:
        return None

    # Extract aliases (Also known as line)
    aliases = []
    tune = ""

    for line in lines[1:20]:  # Check first 20 lines for metadata
        if line.startswith("Also known as:"):
            aliases_text = line.replace("Also known as:", "").strip()
            # Parse aliases - they're often in semicolon-separated format
            aliases = [a.strip() for a in aliases_text.split(';')]
        elif line.startswith("Tune:"):
            tune = line.replace("Tune:", "").strip()
        elif line.startswith("Tags:"):
            tags_text = line.replace("Tags:", "").strip()
            break

    # Extract tags
    tags = []
    tags_match = re.search(r'Tags:\s*(.+?)(?:\n|$)', content)
    if tags_match:
        tags_text = tags_match.group(1).strip()
        tags = [t.strip() for t in tags_text.split(',')]

    # Get relative path and location info
    rel_path = os.path.relpath(filepath, '/home/user/noted-hymns-to-present-and-sing')
    location_match = re.search(r'hymns/([^/]+)/(.+)', rel_path)
    if location_match:
        section_dir = location_match.group(1)
        filename = location_match.group(2)
        # Extract section number from directory name (e.g., "7.14_Discipleship" -> "7.14")
        section_num = re.match(r'(\d+\.\d+)', section_dir)
        section_number = section_num.group(1) if section_num else section_dir
    else:
        section_dir = ""
        filename = os.path.basename(filepath)
        section_number = ""

    return {
        'title': title,
        'aliases': aliases,
        'tune': tune,
        'tags': tags,
        'file': rel_path,
        'location': section_dir,
        'section_number': section_number,
        'filename': filename,
    }

def build_index(hymns_dir: str = '/home/user/noted-hymns-to-present-and-sing/hymns') -> List[Dict[str, Any]]:
    """
    Scan hymns directory and build index of all hymns and psalms.
    """
    index = []

    if not os.path.isdir(hymns_dir):
        print(f"Error: Directory {hymns_dir} not found")
        return index

    # Walk through all files in the hymns directory
    for root, dirs, files in os.walk(hymns_dir):
        for filename in sorted(files):
            # Skip hidden files and directories
            if filename.startswith('.'):
                continue

            filepath = os.path.join(root, filename)
            hymn_data = parse_hymn_file(filepath)

            if hymn_data:
                index.append(hymn_data)

    return index

def save_index(index: List[Dict[str, Any]], output_file: str = '/home/user/noted-hymns-to-present-and-sing/hymn_index.json'):
    """Save the index to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"Index saved to {output_file}")
        print(f"Total entries: {len(index)}")
        return True
    except Exception as e:
        print(f"Error saving index: {e}")
        return False

def print_index_stats(index: List[Dict[str, Any]]):
    """Print statistics about the index."""
    sections = {}
    tag_counts = {}

    for entry in index:
        # Count by section
        section = entry.get('section_number', 'Unknown')
        sections[section] = sections.get(section, 0) + 1

        # Count by tag
        for tag in entry.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    print("\n=== Index Statistics ===")
    print(f"Total hymns/psalms: {len(index)}")
    print(f"\nBy section:")
    for section in sorted(sections.keys(), key=lambda x: (float(x.split('.')[0]) if x != 'Unknown' else 999, float(x.split('.')[1]) if '.' in x else 0)):
        print(f"  {section}: {sections[section]}")

    print(f"\nTop 15 tags:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {tag}: {count}")

if __name__ == '__main__':
    print("Building hymn index...")
    index = build_index()

    if index:
        print_index_stats(index)
        save_index(index)
    else:
        print("No hymns found!")
