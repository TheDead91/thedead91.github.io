# Post-deployment verification and Search Console actions

Deploy: commit `bd60253` on `main`, 2026-09-26T12:54Z.
Both GitHub Actions workflows reported `success`. No `Google Indexing API` run
was created for this commit, confirming the workflow is gone.

## Live verification (2026-09-26, after propagation)

`last-modified: Sat, 26 Sep 2026 12:56:33 GMT` confirmed the new build was
served, not a cached artefact.

| Check | Result |
| --- | --- |
| `robots.txt` | repository version served; fully permissive; one `Sitemap:` line |
| `sitemap.xml` | 89 `<loc>`, **validates against the sitemaps.org 0.9 XSD** |
| — posts | 73 |
| — category archives | 11 |
| — taxonomy indexes | 2 |
| — `about/`, `archives/`, homepage | 3 |
| — tag archive pages | **0** (was 106) |
| — paginated listings | **0** (was 7) |
| — site-verification file | **0** (was 1) |
| `<title>` on `/page2/`…`/page8/` | `Page N of 8 \| TheDead91` (was `TheDead91` on all 7) |
| `<meta name="robots">` on tag archives | `noindex, follow` |
| `<meta name="robots">` on `/404.html` | `noindex, follow` |
| Posts / categories / homepage / pagination | no `noindex` — indexable |
| Canonicals | exactly one per page, self-referencing, canonical host |
| `og:image` | present on every page (was absent everywhere) |
| `link rel="alternate"` feed discovery | present on every page (was absent everywhere) |
| Viewport | `width=device-width initial-scale=1, viewport-fit=cover` — pinch-zoom allowed (was `user-scalable=no`) |
| Footer copyright | `© 2026 Andrea Lamonato.` (was `© 2026 <a></a>.`) |
| `/posts/2024-09-PowerShell/` | 0 stray `<html>/<head>/<title>` in `<body>`, 0 unrendered fences (was 1 and 4) |
| Googlebot fetch of a post | 200, 73,398 bytes of HTML |
| 404 for unknown paths | still HTTP 404 |

### Lighthouse on the deployed site

| Page | SEO | Accessibility | Best Practices |
| --- | ---: | ---: | ---: |
| `/` | 100 | **100** (was 95) | 100 |
| `/page2/` | 100 | **100** (was 95) | 100 |
| a post | 100 | 93 (unchanged) | 100 |

The post's remaining accessibility findings are theme-level and out of indexing
scope: heading anchor links with no accessible name (23 on one page),
post-navigation `aria-label`/visible-text mismatches, and Mermaid edge-label
contrast. They live in the theme's `_includes/refactor-content.html`.

Note that SEO was 100 **before** the remediation too. Lighthouse audits the
markup of a single URL; it cannot observe whether a site is crawled or indexed.

## Search Console actions performed

1. **Deleted** the submission `https://thedead91.github.io/feed.xml`
   (submitted 2026-01-05). An Atom feed is not a sitemap; this was never a valid
   submission.
2. **Deleted** the submission `https://thedead91.github.io/sitemap.xml?v=2`
   (submitted 2025-12-24). A stale cache-buster duplicate of the real sitemap.
3. **Re-submitted** `https://thedead91.github.io/sitemap.xml`
   (2026-09-26T12:59:17Z). Search Console now lists exactly one sitemap, with
   0 errors and 0 warnings.
4. **Re-inspected** 13 representative URLs via the URL Inspection API.

No other property was touched. `sc-domain:thedead91.com` and
`https://holidayhackchallenge.thedead91.com/` were left alone; they are separate
properties and outside this mission's scope.

## Google's index state immediately after deployment — UNCHANGED

This is the honest result and it is expected.

| URL | coverageState before | coverageState after |
| --- | --- | --- |
| `/` | Crawled - currently not indexed | Crawled - currently not indexed |
| `/categories/` | Crawled - currently not indexed | Crawled - currently not indexed |
| `/archives/` | Crawled - currently not indexed | Crawled - currently not indexed |
| `/tags/` | Crawled - currently not indexed | Crawled - currently not indexed |
| `/about/`, `/page2/` | URL is unknown to Google | URL is unknown to Google |
| 4 sampled posts (2023/2024/2025) | URL is unknown to Google | URL is unknown to Google |
| `/tags/elf-hunt/` | URL is unknown to Google | URL is unknown to Google |
| `/categories/sans-holiday-hack-challenge-2025/` | URL is unknown to Google | URL is unknown to Google |
| `/404.html` | URL is unknown to Google | URL is unknown to Google |

`lastCrawlTime` values are unchanged (`/` still 2026-06-11). The `sitemaps`
field is still empty for every URL, meaning Google has not yet processed the
re-submitted sitemap.

**No improvement is being claimed.** The URL Inspection API reports Google's
most recently *stored* index state; it does not trigger a re-crawl, and it
exposes no "request indexing" operation. Google will recrawl on its own
schedule, and the changes made here are designed to be discovered when it does.

## What remains dependent on Google

1. Processing of the re-submitted sitemap and the resulting change to the
   `sitemaps` field in URL Inspection.
2. Re-crawl of the homepage and the four navigation pages, and the outcome of
   `Crawled - currently not indexed`.
3. First-ever discovery and crawling of the 73 posts. The posts are reachable
   from the homepage, all eight pagination pages, `/archives/`, `/categories/`
   and the crawlable `noindex, follow` tag pages, and all 73 are in the sitemap.
4. Removal of the 106 tag pages from the index, which requires Google to crawl
   and honour their new `noindex`.
5. Any residual effect of the historical Indexing API misuse, which is not
   something a technical change can undo.

No manual action or "request indexing" step is available for this property: the
URL Inspection API has no such method, and the Search Console web UI's
"Request indexing" is a manual, per-URL operation.
