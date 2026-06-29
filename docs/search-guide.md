# Hymn & Psalm Search Index

The hymn and psalm collection includes a comprehensive, searchable index that allows you to find items by:
- **Title and aliases** — exact and substring matching
- **Tune name** — melody/setting name
- **Tags** — theological, traditional, and form-based categories
- **Section** — liturgical grouping

## Quick Start

### Build the Index

First, generate the index from all hymn files:

```bash
python3 build_index.py
```

This creates `hymn_index.json` containing metadata for all 410+ entries.

### Search

Search for hymns and psalms using `search_hymns.py`:

```bash
python3 search_hymns.py <query> [options]
```

## Search Examples

### Search by Title

Find items by partial title match (case-insensitive):

```bash
python3 search_hymns.py "Mighty"
python3 search_hymns.py "Gloria"
python3 search_hymns.py "Psalm"
```

### Search by Alias (Alternate Names)

Searches also match aliases. For example, "Veni Creator Spiritus" will find entries known by that Latin title:

```bash
python3 search_hymns.py "Veni Creator"
```

### Search by Tune Name

Use `--tune` to search in melody/tune names instead of titles:

```bash
python3 search_hymns.py --tune "Old Hundredth"
python3 search_hymns.py --tune "Greensleeves"
```

### Filter by Tag

Use `--tag` to filter results. You can use this alone or combine with a title search:

```bash
# All ancient hymns
python3 search_hymns.py --tag ancient --limit 10

# All hymns tagged "liturgical"
python3 search_hymns.py --tag liturgical

# Ancient hymns that mention "Gloria"
python3 search_hymns.py "Gloria" --tag ancient

# Lutheran hymns tagged as "sacramental"
python3 search_hymns.py --tag lutheran --tag sacramental
```

### List All Tags

See all available tags with counts:

```bash
python3 search_hymns.py --list-tags
```

Output shows each tag and how many hymns/psalms carry it:
```
Available tags:

  lutheran: 238
  ancient: 208
  liturgical: 205
  ecumenical: 182
  psalm: 159
  ...
```

### Detailed Results

Add `--detail` to see more information about each result:

```bash
python3 search_hymns.py "Peace" --detail
```

Output includes title, aliases, tune, tags, and file location:
```
[7.15] Beautiful Savior
  Aliases: Schönster Herr Jesu (German); Fairest Lord Jesus (trans.)
  Tune: Schönster Herr Jesu (Münster Gesangbuch, 1677)
  Tags: ancient, lutheran, ecumenical, trust
  File: hymns/7.15_Trust/Beautiful_Savior
```

### Limit Results

Use `--limit N` to show only the first N results:

```bash
python3 search_hymns.py --tag ancient --limit 10
```

### Case-Sensitive Search

Use `--case-sensitive` for exact-case matching (rarely needed):

```bash
python3 search_hymns.py --case-sensitive "GLORIA"
```

## Tag Categories

### Tradition Tags

Identify where a hymn originates and where it's used:

| Tag | Meaning |
|-----|---------|
| `ancient` | Pre-AD 1050, undivided church |
| `lutheran` | Lutheran tradition (LCMS, ELCA, LSB scope) |
| `roman` | Roman Catholic tradition |
| `reformed` | Reformed / Calvinist tradition |
| `baptist` | Baptist tradition |
| `anglican` | Anglican / Episcopal tradition |
| `eastern` | Eastern Orthodox tradition |
| `ecumenical` | Used across multiple traditions |

### Theological Content Tags

Identify the primary theological theme:

| Tag | Meaning |
|-----|---------|
| `sacramental` | Focus on sacraments as means of grace |
| `real-presence` | Affirms Christ's presence in Lord's Supper |
| `baptism` | Focus on baptism |
| `baptismal-regeneration` | Baptism as regeneration |
| `lords-supper` | Focus on Holy Communion |
| `absolution` | Confession and absolution focus |
| `sola-fide` | Faith alone (justification) |
| `sola-gratia` | Grace alone (salvation ground) |
| `solus-christus` | Christ alone (mediation) |
| `sola-scriptura` | Scripture alone (authority) |
| `reformation` | General Reformation era character |

### Form & Function Tags

Identify liturgical use and type:

| Tag | Meaning |
|-----|---------|
| `liturgical` | Part of formal liturgy |
| `office` | Daily Office (Matins, Vespers, Compline) |
| `psalm` | Psalm setting |
| `canticle` | Prose canticle (chanted to a tone) |
| `creed` | Credal text (Nicene, Apostles', Athanasian) |
| `intercession` | Prayer of intercession |

## Index Structure

The index file (`hymn_index.json`) is a JSON array with one object per hymn/psalm:

```json
[
  {
    "title": "Gloria in Excelsis Deo (The Greater Doxology)",
    "aliases": [],
    "tune": "",
    "tags": ["ancient", "lutheran", "roman", "anglican", "ecumenical", "liturgical"],
    "file": "hymns/6.2_Ancient_Hymnic_Canticles/Gloria_in_Excelsis",
    "location": "6.2_Ancient_Hymnic_Canticles",
    "section_number": "6.2",
    "filename": "Gloria_in_Excelsis"
  },
  ...
]
```

Fields:
- **title** — Main hymn/psalm title
- **aliases** — List of alternate names (from "Also known as" line)
- **tune** — Melody or tune name
- **tags** — List of searchable tags
- **file** — Relative path to hymn file (for use with presentation tools)
- **location** — Directory (section grouping)
- **section_number** — Numeric section identifier (e.g., "7.14", "8.23")
- **filename** — Filename without path

## Programmatic Use

Import `HymnSearcher` into your Python scripts:

```python
from search_hymns import HymnSearcher

searcher = HymnSearcher('hymn_index.json')

# Search by title
results = searcher.search_by_name('Gloria')

# Search by tag
lutheran = searcher.search_by_tag('lutheran')

# Filter by multiple tags (AND logic)
ancient_liturgical = searcher.search_by_tags(['ancient', 'liturgical'])

# Search by tune
old_hundredth = searcher.search_by_tune('Old Hundredth')

# Get all tags with counts
tags = searcher.get_all_tags()

# Format a result for display
print(searcher.format_result(results[0], detail=True))
```

## Workflow

### When to Rebuild the Index

Rebuild the index whenever:
- Adding new hymn/psalm files
- Modifying titles, aliases, tune names, or tags
- Adding new sections

Rebuild is fast (< 1 second for 410+ entries):

```bash
python3 build_index.py
```

### Keeping the Index Current

For CI/CD workflows, you can add index generation to your build:

```bash
# Rebuild and verify in GitHub Actions, etc.
python3 build_index.py
git add hymn_index.json
git commit -m "Update hymn index"
```

Alternatively, distribute the index as part of release bundles so end-users have a working search tool out of the box.

## Integration with `hymn_to_presentation.py`

The search index complements the existing `hymn_to_presentation.py` export tool:

1. **Search** — Use `search_hymns.py` to find hymns by name, tune, or tag
2. **Export** — Use the file path from search results with `hymn_to_presentation.py`:

```bash
# Search for all ancient liturgical hymns
python3 search_hymns.py --tag ancient --tag liturgical --detail

# Export one result
python3 hymn_to_presentation.py --file hymns/2.0_Divine_Service_Liturgy/Gloria_in_Excelsis_Deo --format pptx
```

## Troubleshooting

### "Index file not found"

Run `build_index.py` first:

```bash
python3 build_index.py
```

### No results for a known hymn

Check:
1. Exact spelling in the hymn file (title is first line)
2. The hymn may be known by an alias — try `--detail` to see all names
3. Try searching for part of the title: `search_hymns.py "Peace"` instead of `search_hymns.py "Peace of Christ"`

### Want to exclude certain tags?

Use the `HymnSearcher` API directly in Python:

```python
from search_hymns import HymnSearcher

searcher = HymnSearcher()
all_hymns = searcher.search_by_name('')  # Empty query returns all
# Filter programmatically to exclude certain tags
filtered = [h for h in all_hymns if 'decision' not in h['tags']]
```

## Performance

- **Search time**: < 10ms for 410+ entries on typical hardware
- **Index size**: ~150 KB JSON
- **Rebuild time**: < 1 second

Index is read once on startup, all searches are in-memory, so subsequent queries are very fast.
