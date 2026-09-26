# Google indexing & crawl-architecture audit — thedead91.github.io

Audit date: 2026-09-26
Target: `https://thedead91.github.io/` (Search Console property
`https://thedead91.github.io/`, URL-prefix, permission `siteOwner`)

## Files

| File | Contents |
| --- | --- |
| `BASELINE.md` | The site as an external crawler saw it before any change |
| `ROOT_CAUSE.md` | Findings classified CONFIRMED / HIGH CONFIDENCE / POSSIBLE |
| `CHANGES.md` | Every repository and deployment change, with rationale |
| `URL_MATRIX.csv` / `.json` | Per-URL reconciliation, 204 URLs, 25 columns |

`docs/` is listed in `exclude:` in `_config.yml`, so nothing in this directory is
published.

## The one-paragraph version

Nothing was blocking the posts. Every post returned HTTP 200, rendered ~20,000
characters of real server-side HTML, carried a correct self-referencing
canonical, valid `BlogPosting` structured data, and no `noindex`. The failure
was **discovery and prioritisation**: in the site's entire lifetime Google has
crawled exactly **four** URLs — the four pages reachable from the site-wide
sidebar — and has **never discovered a single one of the 73 posts**. All four
URLs it did crawl are `Crawled - currently not indexed`. Meanwhile the site was
advertising 203 URLs, 140+ of them near-empty duplicate pages, and the Google
Indexing API (a restricted API that does not cover ordinary blog posts) had
been fired at every one of them on 15 successful workflow runs.
