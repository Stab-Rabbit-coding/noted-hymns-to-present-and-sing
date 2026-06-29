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
| Individual ABC file | `http://openhymnal.org/Abc/<Filename>.abc` | Filename visible in `#Citations and References` of every hymn file |
| Full collection (one file) | `http://openhymnal.org/OpenHymnal2014.06.abc` | ~4 MB; all tunes concatenated; last updated June 2014 |
| GitHub mirror (individual) | `https://raw.githubusercontent.com/mzealey/openhymnal/master/Choir/<Filename>.abc` | Same filenames as the live site; updated irregularly |
| GitHub mirror (bulk) | clone `https://github.com/mzealey/openhymnal` | `Choir/` and `Complete/` directories hold individual ABC files |

### Rate limits and access notes

No rate limit is documented.  The live site (`openhymnal.org`) has returned
`403 Forbidden` responses in automated environments — likely Cloudflare bot
protection.  Workarounds:

1. **Prefer the GitHub mirror** for scripted access; GitHub's CDN does not
   apply the same bot filter.
2. **Download the bulk file once** (`OpenHymnal2014.06.abc`) and split it
   locally — each tune begins with an `X:` field.
3. For one-off lookups, open the URL in a browser (not a script) — the site
   works normally for interactive use.

### Using `abc_to_musiqwik.py --url`

The script accepts a full Open Hymnal ABC URL:

```
python3 abc_to_musiqwik.py --url http://openhymnal.org/Abc/A_Mighty_Fortress-Ein_Feste_Burg.abc
```

If the live site returns 403, substitute the GitHub raw URL:

```
python3 abc_to_musiqwik.py --url https://raw.githubusercontent.com/mzealey/openhymnal/master/Choir/A_Mighty_Fortress-Ein_Feste_Burg.abc
```

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
| Open Hymnal Project (GitHub) | ABC | None | None (Git/raw URL) | Scripted ABC access; more reliable |
| Open Hymnal (bulk file) | ABC | None | None (single download) | Offline bulk import |
| Hymnary.org | JSON / CSV / HTML | None | Scripture JSON; CSV export | Metadata, cross-references, lyrics verification |
| abcnotation.com | ABC | None | None (HTML search) | Secondary ABC source; verify quality |
| pdhymns.com | PDF / PPT | None | None (direct download) | Visual melody verification |
| OpenLP / Worship Leader | OpenLyrics XML | None | None (file export) | Lyrics-only content |
| IMSLP | PDF | None (read) | MediaWiki API (metadata) | Score verification, harmonization lookup |

---

## Environment Notes (this execution environment)

In the managed remote execution environment used by Claude Code sessions for
this repository, outbound HTTP is routed through a proxy that blocks several
hymn-source domains:

- `openhymnal.org` — 403 on all ABC file requests
- `hymnary.org` — 403 on some automated requests

**Workarounds used in this repository:**

1. ABC notation for hymn files has been encoded from memory or reference
   scores where the live Open Hymnal fetch was blocked.  These encodings
   should be verified against the original Open Hymnal ABC files when access
   is available (browser, unproxied environment, or GitHub raw URL).
2. The GitHub mirror (`raw.githubusercontent.com/mzealey/openhymnal`) is not
   subject to the same block and should be preferred in scripts.
3. The `--url` flag of `abc_to_musiqwik.py` accepts any HTTP/HTTPS URL; swap
   in the GitHub raw URL when the live site is inaccessible.
