# Quick Start: Searching Hymns & Psalms

The repository includes a searchable index of all 410+ hymns and psalms. Search by name, alias, tune, or tags instantly.

## Basic Usage

```bash
# Search by title
python3 search_hymns.py "Gloria"

# Search by tag
python3 search_hymns.py --tag lutheran

# Search by tune
python3 search_hymns.py --tune "Old Hundredth"

# Combine search and filters
python3 search_hymns.py "Savior" --tag ancient

# See all available tags
python3 search_hymns.py --list-tags

# Get detailed info
python3 search_hymns.py "Psalm 23" --detail
```

## Common Searches

```bash
# All psalms
python3 search_hymns.py "Psalm" --limit 10

# All liturgical items
python3 search_hymns.py --tag liturgical --limit 5

# All ancient hymns
python3 search_hymns.py --tag ancient --tag liturgical --limit 5

# Baptism-related hymns
python3 search_hymns.py --tag baptism --detail

# Hymns with a specific tune
python3 search_hymns.py --tune "Watts"
```

## Examples

### Find all hymns about grace and justification
```bash
python3 search_hymns.py "grace" --tag sola-fide
```

### List all Lutheran hymns from the office
```bash
python3 search_hymns.py --tag lutheran --tag office
```

### Get details on all Lord's Supper hymns
```bash
python3 search_hymns.py --tag lords-supper --detail --limit 20
```

### Search for hymns by German name
```bash
python3 search_hymns.py "Veni Creator"
```

## Available Tags

**Traditions:**
- `lutheran`, `roman`, `reformed`, `baptist`, `anglican`, `eastern`, `ancient`, `ecumenical`

**Theology:**
- `sacramental`, `lords-supper`, `baptism`, `sola-fide`, `sola-gratia`, `solus-christus`, `sola-scriptura`

**Form:**
- `liturgical`, `office`, `psalm`, `canticle`, `creed`

See `docs/search-guide.md` for the complete tag taxonomy and detailed documentation.

## Rebuilding the Index

If you add new hymns or modify titles/tags, rebuild the index:

```bash
python3 build_index.py
```

Takes < 1 second for 410+ entries.

## More Information

See `docs/search-guide.md` for:
- Complete search syntax
- Programmatic API usage
- Tag meanings and taxonomy
- Integration with presentation tools
- Troubleshooting

## Technical Details

- **Index file**: `hymn_index.json` (158 KB)
- **Search time**: < 10ms per query
- **Format**: Python scripts (Python 3.6+)
- **Dependencies**: None (uses only standard library)
