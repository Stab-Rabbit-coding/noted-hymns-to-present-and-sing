#!/usr/bin/env python3
"""
Search the hymn and psalm index by name, aliases, tune, and tags.

Usage:
    python3 search_hymns.py [options] <query>

Examples:
    # Search by title
    python3 search_hymns.py "Amazing Grace"

    # Search by tag
    python3 search_hymns.py --tag lutheran

    # Search by tune
    python3 search_hymns.py --tune "Old Hundredth"

    # Search by title and filter by tag
    python3 search_hymns.py --tag ancient "Our Father"

    # Case-insensitive search
    python3 search_hymns.py "gospel"

    # List all available tags
    python3 search_hymns.py --list-tags

    # Show detailed info
    python3 search_hymns.py --detail "Psalm 23"
"""

import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

class HymnSearcher:
    def __init__(self, index_file: str = 'hymn_index.json'):
        """Initialize the searcher with an index file."""
        self.index_file = index_file
        self.index = []
        self.load_index()

    def load_index(self):
        """Load the hymn index from JSON file."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
            print(f"Loaded index with {len(self.index)} entries", file=sys.stderr)
        except FileNotFoundError:
            print(f"Error: Index file '{self.index_file}' not found.", file=sys.stderr)
            print("Run 'python3 build_index.py' first to generate the index.", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in index file: {e}", file=sys.stderr)
            sys.exit(1)

    def search_by_name(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search by title or aliases."""
        results = []
        query_pattern = query if case_sensitive else query.lower()

        for entry in self.index:
            # Search title
            title = entry.get('title', '')
            title_search = title if case_sensitive else title.lower()

            if query_pattern in title_search:
                results.append(entry)
                continue

            # Search aliases
            for alias in entry.get('aliases', []):
                alias_search = alias if case_sensitive else alias.lower()
                if query_pattern in alias_search:
                    results.append(entry)
                    break

        return results

    def search_by_tag(self, tag: str, results: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Filter results by tag (case-insensitive)."""
        tag_lower = tag.lower()
        search_space = results if results is not None else self.index

        filtered = []
        for entry in search_space:
            if any(t.lower() == tag_lower for t in entry.get('tags', [])):
                filtered.append(entry)

        return filtered

    def search_by_tags(self, tags: List[str], results: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Filter results by multiple tags (AND logic - must have all)."""
        search_space = results if results is not None else self.index
        tags_lower = [t.lower() for t in tags]

        filtered = []
        for entry in search_space:
            entry_tags_lower = [t.lower() for t in entry.get('tags', [])]
            if all(tag in entry_tags_lower for tag in tags_lower):
                filtered.append(entry)

        return filtered

    def search_by_tune(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search by tune name."""
        results = []
        query_pattern = query if case_sensitive else query.lower()

        for entry in self.index:
            tune = entry.get('tune', '')
            tune_search = tune if case_sensitive else tune.lower()

            if query_pattern in tune_search:
                results.append(entry)

        return results

    def get_all_tags(self) -> Dict[str, int]:
        """Get all tags in the index with counts."""
        tag_counts = {}
        for entry in self.index:
            for tag in entry.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    def format_result(self, entry: Dict[str, Any], detail: bool = False) -> str:
        """Format a single search result."""
        output = []

        # Title and location
        title = entry.get('title', 'Unknown')
        section = entry.get('section_number', '')
        location = entry.get('location', '')

        if section:
            output.append(f"[{section}] {title}")
        else:
            output.append(title)

        if not detail:
            return '\n'.join(output)

        # Detailed output
        if entry.get('aliases'):
            output.append(f"  Aliases: {'; '.join(entry['aliases'])}")

        if entry.get('tune'):
            output.append(f"  Tune: {entry['tune']}")

        if entry.get('tags'):
            output.append(f"  Tags: {', '.join(entry['tags'])}")

        if entry.get('file'):
            output.append(f"  File: {entry['file']}")

        return '\n'.join(output)

    def print_results(self, results: List[Dict[str, Any]], detail: bool = False, limit: Optional[int] = None):
        """Print formatted search results."""
        if not results:
            print("No results found.")
            return

        if limit:
            results = results[:limit]

        print(f"\nFound {len(results)} result(s):\n")
        for i, result in enumerate(results, 1):
            print(self.format_result(result, detail=detail))
            if i < len(results):
                print()

    def print_tags(self):
        """Print all available tags with counts."""
        tags = self.get_all_tags()
        print("\nAvailable tags:\n")
        for tag in sorted(tags.keys()):
            print(f"  {tag}: {tags[tag]}")


def main():
    parser = argparse.ArgumentParser(
        description='Search hymn and psalm index by name, tune, and tags.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python3 search_hymns.py "Amazing Grace"
  python3 search_hymns.py --tag lutheran
  python3 search_hymns.py --tune "Old Hundredth"
  python3 search_hymns.py --tag ancient --detail
  python3 search_hymns.py --list-tags
        '''
    )

    parser.add_argument('query', nargs='?', help='Search query (title, alias, or tune)')
    parser.add_argument('--tag', action='append', help='Filter by tag (can be used multiple times)')
    parser.add_argument('--tune', action='store_true', help='Search in tune names instead of titles')
    parser.add_argument('--detail', action='store_true', help='Show detailed information')
    parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    parser.add_argument('--list-tags', action='store_true', help='List all available tags')
    parser.add_argument('--limit', type=int, help='Limit results to N entries')
    parser.add_argument('--index', default='hymn_index.json', help='Path to index file')

    args = parser.parse_args()

    searcher = HymnSearcher(args.index)

    # List tags
    if args.list_tags:
        searcher.print_tags()
        return

    # Need a query for other operations
    if not args.query and not args.tag:
        parser.print_help()
        return

    # Perform search
    results = []

    if args.query:
        if args.tune:
            results = searcher.search_by_tune(args.query, case_sensitive=args.case_sensitive)
        else:
            results = searcher.search_by_name(args.query, case_sensitive=args.case_sensitive)

    # Filter by tags
    if args.tag:
        if results:
            results = searcher.search_by_tags(args.tag, results)
        else:
            results = searcher.search_by_tags(args.tag)

    # Print results
    searcher.print_results(results, detail=args.detail, limit=args.limit)


if __name__ == '__main__':
    main()
