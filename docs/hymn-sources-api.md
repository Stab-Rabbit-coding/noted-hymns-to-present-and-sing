# Hymn Sources — API and Access Reference

This document covers the access protocols, URL patterns, authentication
requirements, and rate limits for external hymn collections used by this
project.  Use it when sourcing new ABC notation files, lyrics, or tune
metadata, or when automating bulk imports.

---

## 1. Open Hymnal Project

**URL:** http://openhymnal.org  
**GitHub mirror:** https://github.com/mzealey/openhymnal

### What it provides

- ABC notation for ~1 300 Lutheran and ecumenical hymns
- All items confirmed public domain (words, music, and setting)
- Companion PDF hymnals

### Access — no authentication required

| Resource | URL pattern | Notes |
|----------|-------------|-------|
| Individual ABC file (live) | `http://openhymnal.org/Abc/<Filename>.abc` | Filename visible in `#Citations and References` of every hymn file; returns 403 in scripted environments |
| Full collection (live) | `http://openhymnal.org/OpenHymnal2014.06.abc` | ~4 MB; all tunes concatenated; last updated June 2014; also returns 403 in scripted environments |
| GitHub mirror directory listing | `https://github.com/mzealey/openhymnal/tree/master/Complete/<HymnName>` | Lists the `.abc` file(s) in that hymn's subdirectory |
| GitHub mirror raw file | `https://raw.githubusercontent.com/mzealey/openhymnal/master/Complete/<HymnName>/<Filename>.abc` | Returns raw ABC text; **this is the primary working access path** |

### GitHub mirror: actual file structure

The mirror at `github.com/mzealey/openhymnal` uses a **subdirectory-per-hymn**
layout under `Complete/`, not flat files under `Choir/`:

```
Complete/
├── O_Sacred_Head_Now_Wounded/
│   └── O_Sacred_Head_Now_Wounded-Passion_Chorale-Herzlich_Tut_Mich_Verlangen.abc
├── Jesus_In_Thy_Dying_Woes/
│   └── Jesus_In_Thy_Dying_Woes-Words_On_The_Cross_The_Litany.abc
└── <HymnName>/
    └── <HymnName>-<TuneName>[-<AlternateName>].abc
```

**Important differences from the live-site filenames:**

- The subdirectory is named after the hymn title (same naming convention as this
  repo's hymn files).
- The `.abc` filename often appends a second tune name or German original name
  that the live-site URL omits.  Example:
  - Live site: `O_Sacred_Head_Now_Wounded-Passion_Chorale.abc`
  - GitHub:    `O_Sacred_Head_Now_Wounded-Passion_Chorale-Herzlich_Tut_Mich_Verlangen.abc`
- The `Choir/` directory in the repo contains **multi-part choral arrangements**
  (Canon, JesuJoyOfMansDesiring, etc.), not hymn ABC files.  Do **not** use
  `Choir/` paths for individual hymn tunes.

**ABC file format in the mirror** — files are SATB four-voice arrangements.
The melody is always the `[V: S1V1]` voice.  Extract it for single-line use:

```
[V: S1V1] [Q:1/4=100] E | A G F E | D2 E B | ...
```

Strip the `[V: S1V1]` prefix and any `!sintro!`/`!eintro!` markers before
pasting into the `## ABC` section of a hymn file.

### Mirror coverage

The mirror is a partial export — not every Open Hymnal hymn is present.
Coverage confirmed by directory inspection (June 2026):

| Hymn | In mirror? | Path |
|------|-----------|------|
| O Sacred Head, Now Wounded | ✅ | `Complete/O_Sacred_Head_Now_Wounded/` |
| Jesus, In Thy Dying Woes | ✅ | `Complete/Jesus_In_Thy_Dying_Woes/` |
| Upon the Cross Extended | ❌ | not present |
| Christ, the Life of All the Living | ❌ | not present |
| O Perfect Life of Love | ❌ | not present |
| Not All the Blood of Beasts | ❌ | not present |

When a hymn is absent from the mirror and the live site returns 403, ABC must
be encoded from memory or a printed score and flagged for later verification.

### Browsing the mirror directory

To find a hymn's subdirectory name and the exact `.abc` filename within it,
fetch the GitHub tree page:

```
https://github.com/mzealey/openhymnal/tree/master/Complete/<HymnName>
```

The page lists files; the raw download URL is then:

```
https://raw.githubusercontent.com/mzealey/openhymnal/master/Complete/<HymnName>/<filename>.abc
```

The GitHub API also works for a partial directory listing (no auth required
for public repos, but WebFetch may truncate the response):

```
https://api.github.com/repos/mzealey/openhymnal/contents/Complete
```

### Rate limits and access notes

No rate limit is documented.  The live site (`openhymnal.org`) returns
`403 Forbidden` in all scripted/automated environments tested.  Workarounds:

1. **Use the GitHub mirror** (`Complete/<HymnName>/`) for scripted access.
2. **Download the bulk file once** when you have browser access — split on
   `X:` fields to extract individual tunes.
3. For one-off lookups, open the URL in a browser (not a script).

### Using `abc_to_musiqwik.py --url`

The `--url` flag accepts any HTTP/HTTPS URL that returns raw ABC text.
Use the GitHub raw URL when the live site is inaccessible:

```
python3 abc_to_musiqwik.py --url https://raw.githubusercontent.com/mzealey/openhymnal/master/Complete/O_Sacred_Head_Now_Wounded/O_Sacred_Head_Now_Wounded-Passion_Chorale-Herzlich_Tut_Mich_Verlangen.abc
```

Note: the `--url` flag is designed for single-voice ABC files.  The SATB
files in the mirror will need manual voice extraction first.

---

## 2. Hymnary.org

**URL:** https://hymnary.org  
**Operator:** Calvin University (Grand Rapids, Michigan)

### What it provides

- Bibliographic metadata for ~1 million hymn instances
- Text of many hymns (public domain and licensed)
- Tune metadata (composer, meter, key)
- Cross-references across ~6 600 hymnals

### Access — no authentication required for read operations

#### Scripture-reference JSON API

Returns hymns associated with a Bible passage.

```
GET https://hymnary.org/api/scripture?reference=John+3:16
GET https://hymnary.org/api/scripture?book=John&fromChapter=3&fromVerse=16&toChapter=3&toVerse=21
```

Response: JSON array, up to 100 results per call.  Fields include hymn title,
author, tune name, and hymnary.org identifier.

#### Search CSV export

Append `&export=csv` to any Hymnary search URL to download results as CSV.

```
https://hymnary.org/search?qu=in_first_line:grace&export=csv
https://hymnary.org/search?qu=tune_name:PASSION+CHORALE&export=csv
```

#### Hymnal/hymn text pages

Individual hymn text pages are HTML — no dedicated JSON endpoint for full text.
Scraping is possible but fragile; prefer the CSV export or Scripture API for
structured data.

#### Tune/meter search

```
https://hymnary.org/search?qu=meter:CMD
https://hymnary.org/search?qu=tune_name:ARLINGTON
```

### Rate limits and access notes

No rate limit is publicly documented.  Hymnary.org has also returned `403`
responses in some automated environments.  Best practice:

- Cache responses locally; do not poll repeatedly for the same query.
- Use the CSV export for batch lookups rather than scraping individual pages.
- For interactive lookup, open pages in a browser.

### Copyright caution

Hymnary.org hosts texts under a variety of licenses.  A text appearing on the
site does **not** guarantee it is public domain.  Always verify the copyright
date independently (see `docs/extensibility-guide.md` §Copyright Verification
Checklist) before adding to this repository.

---

## 3. ABC Notation Repository (abcnotation.com)

**URL:** https://abcnotation.com

### What it provides

- User-submitted ABC files for folk, traditional, and sacred music
- Search by title, composer, or tune name

### Access

No API.  The site offers a search form at `https://abcnotation.com/search`.
Results link to individual ABC files hosted on third-party sites.
Authentication: none.

### Notes

Content quality varies — user submissions are not editorially reviewed for
accuracy.  Cross-check any ABC file against a verified source before using it
here.

---

## 4. Public Domain Hymns (pdhymns.com)

**URL:** https://pdhymns.com

### What it provides

- Sheet music PDFs and PowerPoint files for ~300 public domain hymns
- Cross-references to 12 major hymnals

### Access

No API.  Files are directly downloadable via links on individual hymn pages.
Authentication: none.  Sheet music is in PDF or image format — not usable
directly as ABC source but useful for visual melody verification.

---

## 5. OpenLP Song Database

**URL:** https://openlp.org  
**Song database export:** https://openlp.io (community-maintained)

### What it provides

- Song lyrics in OpenLyrics XML format
- Public domain hymns and contemporary worship songs

### Access

- The OpenLP application exports songs in OpenLyrics XML — no live API.
- Community databases (e.g., from Worship Leader App) publish nightly exports
  in OpenSong, OpenLP, and Quelea formats; download links vary by maintainer.
- Authentication: none for public-domain exports.

### Notes

OpenLP files contain **lyrics only** — no melody encoding.  Use as a source
for `#Lyrics` content verification, not for ABC notation.

---

## 6. IMSLP (Petrucci Music Library)

**URL:** https://imslp.org

### What it provides

- Score PDFs for public domain music, including many hymn tunes and settings
- Country-by-country public domain status for each score

### Access

No programmatic API for score downloads.  Individual score pages list PDF
download links.  A MediaWiki API is available for metadata:

```
GET https://imslp.org/api.php?action=query&titles=Symphony_No.5_(Beethoven,_Ludwig_van)&prop=revisions&format=json
```

Authentication: none for read access.  An IMSLP account is required to
contribute scores.

### Notes

IMSLP is most useful for **verifying tune harmonizations** and locating
original edition page images.  It does not provide ABC notation.  For hymn
tunes specifically, check the "Hymn Tunes" category at
`https://imslp.org/wiki/Category:Hymn_tunes`.

---

## Summary Table

| Source | Format | Auth | API | Best use |
|--------|--------|------|-----|----------|
| Open Hymnal Project (live) | ABC | None | None (file download) | Primary ABC source; may 403 in scripts |
| Open Hymnal Project (GitHub) | ABC (SATB) | None | None (Git/raw URL) | Scripted ABC access; partial mirror; extract S1V1 for melody |
| Open Hymnal (bulk file) | ABC | None | None (single download) | Offline bulk import |
| Hymnary.org | JSON / CSV / HTML | None | Scripture JSON; CSV export | Metadata, cross-references, lyrics verification |
| abcnotation.com | ABC | None | None (HTML search) | Secondary ABC source; verify quality |
| pdhymns.com | PDF / PPT | None | None (direct download) | Visual melody verification |
| OpenLP / Worship Leader | OpenLyrics XML | None | None (file export) | Lyrics-only content |
| IMSLP | PDF | None (read) | MediaWiki API (metadata) | Score verification, harmonization lookup |

---

## Environment Notes (Claude Code remote execution environment)

In the managed remote execution environment used by Claude Code sessions for
this repository, outbound HTTP is routed through a proxy.  The following
access outcomes were observed in June 2026 sessions:

### Blocked (403 Forbidden)

Every request to these domains returned 403, whether via `WebFetch` tool or
via `abc_to_musiqwik.py --url`:

- `openhymnal.org` — all paths including `/Abc/`, `/OpenHymnal2014.06.abc`
- `hymnary.org` — all page URLs
- `ccel.org` — hymn text pages
- `lutheranchoralebook.com` — all pages
- `hymntime.com` — all pages
- `traditionalmusic.co.uk` — PDF downloads
- `pgdp.net` — wiki pages

### Accessible

These sources returned content successfully:

- `github.com/mzealey/openhymnal` — tree pages (via `WebFetch`)
- `raw.githubusercontent.com/mzealey/openhymnal` — raw ABC files (via `WebFetch`)
- `api.github.com/repos/mzealey/openhymnal` — partial directory JSON (via `WebFetch`)
- Web search (`WebSearch` tool) — all queries succeeded; useful for metadata

### Workarounds used in this repository

1. For melody retrieval: use the GitHub mirror `Complete/<HymnName>/` path.
2. For hymns not in the mirror: encode ABC from memory; flag in the `C:` field
   or commit message for later verification against a score or browser fetch.
3. For tune/composer metadata: use `WebSearch` — it reliably returns
   attribution facts even when the underlying pages are blocked.

---

## Tool and Query Patterns for Claude Code Sessions

This section documents successful and failed tool/query combinations observed
during sessions working on this repository.  Use it as a decision tree before
spending time on approaches that are known not to work.

### Quick decision tree

```
Need ABC notation for a hymn?
  → Check mzealey/openhymnal Complete/ directory first (WebFetch tree page)
  → If found: fetch raw file, extract S1V1 voice
  → If not found: encode from memory; note for verification

Need tune/composer metadata?
  → WebSearch with tune name + composer + year keywords
  → Works even when hymnary.org pages are blocked

Need lyrics verification?
  → WebSearch for hymn title + Watts/Gerhardt/etc + "stanza" or "text"
  → ccel.org links often appear in results but pages are blocked — use cached snippets in search results instead
```

### Confirmed working tool calls

#### 1. Discover what's in the GitHub mirror directory

```
WebFetch(
  url="https://github.com/mzealey/openhymnal/tree/master/Complete/<HymnName>",
  prompt="List all files in this directory. What .abc files are present and what are their exact filenames?"
)
```

Returns: filename(s) of `.abc` files in that hymn's subdirectory, or 404 if the hymn is not present.

**Tip:** 404 from this call definitively means the hymn is absent from the mirror.

#### 2. Retrieve raw ABC content from the mirror

```
WebFetch(
  url="https://raw.githubusercontent.com/mzealey/openhymnal/master/Complete/<HymnName>/<filename>.abc",
  prompt="Return ONLY the raw text verbatim. Include every header line (X:, T:, C:, S:, M:, L:, Q:, K:) and every note sequence line exactly as it appears."
)
```

Returns: full SATB ABC file.  Extract the `[V: S1V1]` lines for the melody.

**Tip:** Be explicit in the prompt that you need verbatim output including note
sequences — otherwise the model summarizing the fetch may paraphrase and omit
the actual notes.

#### 3. Tune attribution lookup via WebSearch

```
WebSearch(query='"<TuneName>" <Composer> <Year> meter key "Hymns Ancient and Modern" OR hymnary')
WebSearch(query='"<HymnTitle>" tune composer "<Setting source>" OR "<Alternative tune name>"')
```

Reliably returns: composer name, year, alternate tune names, meter, key.

**Examples that worked:**

| Query | Key finding |
|-------|-------------|
| `"O Perfect Life of Love" Baker 1875 tune "Contemplation" OR "Aber" composer Dykes OR Monk` | Confirmed ABER by William H. Monk; Dykes attribution wrong |
| `"Christ the Life of All the Living" tune "Jesu meines Lebens Leben" composer Schop 1641 OR Darmstadt 1687` | Confirmed Unknown composer; pub. Darmstadt 1687 |
| `"Upon the Cross Extended" Heermann Massie tune name "Passion Chorale" OR "O Welt" LSB 430` | Confirmed Passion Chorale (same tune as O Sacred Head) |
| `Arlington tune Thomas Arne 1762 "Not All the Blood of Beasts" LSB 431 tune name` | Confirmed ARLINGTON/Arne for Open Hymnal version; LSB uses SOUTHWELL |
| `"Contemplation" Dykes tune name hymn 1875 "Hymns Ancient and Modern"` | Revealed CONTEMPLATION is by Ouseley (not Dykes); Dykes did not compose it |

#### 4. Browse the GitHub tree for a directory listing

```
WebFetch(
  url="https://github.com/mzealey/openhymnal/tree/master/Complete",
  prompt="List every directory name shown on this page."
)
```

Returns: ~100 hymn subdirectory names per page.  Pagination via `?after=<LastEntry>` 
does **not** work reliably through WebFetch — the tool returns the same first page
regardless of the `after` parameter.  Use direct subdirectory access instead of
trying to paginate the full listing.

#### 5. GitHub API partial directory listing

```
WebFetch(
  url="https://api.github.com/repos/mzealey/openhymnal/contents/Complete",
  prompt="List every 'name' field in the JSON. Specifically look for entries containing: <keywords>."
)
```

Returns: partial JSON (WebFetch model may truncate large arrays).  Useful for
spot-checking presence of a hymn by name.  Not reliable as a complete directory scan.

### Confirmed non-working approaches

| Approach | Outcome | Reason |
|----------|---------|--------|
| `WebFetch(openhymnal.org/Abc/...)` | 403 | Proxy/Cloudflare block |
| `WebFetch(hymnary.org/text/...)` | 403 | Proxy block |
| `WebFetch(ccel.org/...)` | 403 | Proxy block |
| `WebFetch(raw.githubusercontent.com/mzealey/openhymnal/master/Choir/<file>.abc)` | 404 | Wrong path — hymn ABC files are in `Complete/`, not `Choir/` |
| GitHub code search (`github.com/search?q=repo:mzealey...&type=code`) | Requires sign-in | Login wall blocks WebFetch |
| `mcp__github__search_code` on external repo | Permission denied | MCP tools scoped to this repo only |
| `WebFetch` with `?after=` pagination on GitHub tree | Returns first page | Pagination state not preserved |

### Metadata sources that surface via WebSearch even when direct fetch fails

When `WebFetch` on a hymn resource page returns 403, `WebSearch` often returns
useful snippet-level data extracted from the same page by Google/Bing:

- **Hymnary.org tune pages** — meter, key, melodic incipit (solfege numbers)
- **Hymnary.org text pages** — standard tune pairings, composer credits
- **Wikipedia tune articles** — confirmed public domain dates, key/meter
- **IMSLP category pages** — page listings accessible via search snippets

**Effective query patterns for metadata recovery:**

```
# When hymnary.org page is blocked:
WebSearch(query='site:hymnary.org "<TuneName>" OR "<HymnTitle>" meter composer')

# For meter and solfege incipit:
WebSearch(query='"<TuneName>" tune meter "short meter" OR "common meter" OR "long meter" incipit key')

# For public domain date verification:
WebSearch(query='"<Composer name>" died year hymn composer public domain')
```
