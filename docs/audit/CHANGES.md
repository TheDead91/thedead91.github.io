# Changes

Everything below is a generator-, template- or configuration-level fix. No
generated output was hand-patched, and no post content was rewritten.

## Removed

### `.github/workflows/google-indexing.yml`, `.github/workflows/scripts/index.py`

The Google Indexing API was being used to push `URL_UPDATED` notifications for
every sitemap URL — ordinary blog posts, outside the API's documented scope.
Public Actions history: 19 runs, 15 successful. The trigger was live and would
have re-fired on the next deploy. Deleted outright and replaced by ordinary
crawl/sitemap discovery. See `ROOT_CAUSE.md` R2.

### `jekyll-sitemap` from `_config.yml` `plugins:`

It emitted every generated URL it could reach. `sitemap.xml` in the repository is
now the single source of truth, and `tools/seo_check.py` fails the build if that
file goes missing, so there is no silent fallback to an all-inclusive sitemap.

## Added

### `_plugins/seo-indexing.rb`

The single place that decides what this site wants indexed. It runs as a
Jekyll `Generator` at `priority :lowest` so it executes after `jekyll-archives`
(`:normal`) and `jekyll-paginate` (`:lowest`) have created their pages. It:

1. **Drops the theme's `/robots.txt` and `/404.html` page objects.** Jekyll merges
   a theme's `assets/` into `site.pages`, so a repository file with the same
   destination produces a `Conflict: The following destination is shared by
   multiple files` warning and an **empty** output file. Verified before fixing.
2. Marks every page and post indexable by default, then opts specific classes out
   with a stated reason.
3. **Per-post tag archives** → `noindex, follow`, a unique `Tag: <name>` title
   and a description naming the post count. They stay crawlable, so their links
   keep feeding the posts.
4. **Paginated listings** → kept indexable (they are the only crawl path to the
   older posts) but given a unique `Page N of M` title and description, and kept
   out of the sitemap. jekyll-paginate assigns a `Pager` to page 1 as well, so
   the homepage is explicitly excluded from this treatment.
5. **Category archives** → real per-page descriptions and a `lastmod` derived
   from the newest post they list.
6. Publishes the resulting indexable set to `site.data["seo_sitemap"]`.

Two behaviours could not be expressed as page data and are applied in a
`post_render` pass registered for **both `:pages` and `:documents`** (posts are
`Jekyll::Document`, so a pages-only hook silently skips all 73):

* `<title>` / `og:title` for pages that set `seo_title`. The theme omits the page
  title whenever `page.layout == "home"`, and jekyll-paginate clones
  `index.html`, so all eight `/pageN/` pages rendered a byte-identical
  `<title>TheDead91</title>`. `jekyll-archives::Archive#title` is a Ruby reader
  hidden behind a `PageDrop`, so `page.data["title"]` is shadowed and a per-tag
  rename written to data is discarded.
* The viewport meta tag: `user-scalable=no` and `shrink-to-fit=no` are stripped.
  Pinch-zoom being disabled fails WCAG 2.1 SC 1.4.4.

### `sitemap.xml`

Replaces the generated one. It is now only a formatter — it renders
`site.data["seo_sitemap"]` — which is what guarantees the sitemap and the on-page
index directives cannot drift apart. Emits `<loc>` and `<lastmod>` only;
`<changefreq>` and `<priority>` are ignored by Google and were noise.

### `robots.txt`

Overrides the theme's starter boilerplate. Fully permissive, with a comment
explaining that index-level decisions are made with `noindex, follow` rather
than `Disallow`, because a robots.txt disallow would also remove those pages
from the crawl graph and stop engines following the links they contain to the
posts.

### `404.html`

Overrides the theme's copy. Adds `seo_noindex` and a real description.

### `_includes/metadata-hook.html`

Overrides the theme's empty placeholder (the theme calls it inside `<head>`).
Adds:

* `<link rel="alternate" type="application/atom+xml">` — the feed existed at
  `/feed.xml` but no page advertised it.
* `<meta name="robots" content="noindex, follow">` when a page sets
  `seo_noindex`. This is required because **jekyll-seo-tag 2.9.0 has no robots
  support at all** — grepping the installed gem's `lib/` for `robots` returns
  nothing.

### `tools/seo_check.py`

Regression gate, standard library only so it runs unchanged in CI. Asserts
intent rather than exact wording: sitemap contains only indexable canonical
URLs and exists in the build; every post is in the sitemap; no post, category or
hub page is accidentally `noindex`; tag archives are `noindex` yet still
`follow`; exactly one self-referencing canonical per page on the canonical host;
no duplicate title/description among *generated* pages; no page carries the
placeholder description; viewport permits zoom; feed and `og:image` present;
`lang` declared; JSON-LD parses and every post has `BlogPosting`; internal links
resolve; robots.txt declares a sitemap and blocks nothing. Also detects unrendered
code fences and stray `<html>/<head>/<body>` elements inside `<body>`.

## Modified

| File | Change |
| --- | --- |
| `Gemfile` | `jekyll-theme-chirpy` pinned to `~> 7.4.1` (was `~> 7.4`, which permits 7.6). Declared `jekyll-include-cache`, `jekyll-archives`, `jekyll-seo-tag`, `jekyll-paginate`, `jekyll-sass-converter` explicitly instead of relying on transitive resolution. |
| `Gemfile.lock` | **Now committed.** Was gitignored, so builds floated and the next release would have shipped `<html lang="en"data-bs-theme="dark">` on every page. |
| `.gitignore` | Stopped ignoring `Gemfile.lock`. Added `service_account.json`, `client_secret*.json`, `oauth-client.json`, `token.json`, `credentials.json`, `*.pem`, `.env*` — the deleted workflow used to write a service-account key into the working tree. |
| `_config.yml` | `social.name: Andrea Lamonato` (the footer rendered `© 2026 <a></a>.` with an empty anchor). `social_preview_image: /assets/img/profile_photo.jpg` (no `og:image` existed anywhere). `exclude:` extended with the credential patterns and `indexed_urls.txt`. |
| `.github/workflows/pages-deploy.yml` | Added the `tools/seo_check.py` gate after html-proofer. |
| `_posts/2024/2024-12-02-2024-09-PowerShell.md` | **Whitespace only: 11 blank lines inserted.** A fenced code block on the line directly after a list item is a lazy continuation in kramdown, so the fence was emitted as literal prose and the raw `<html><head><title>` inside it leaked into `<body>`. `git diff -w` on this file is empty; not one character of prose or code changed. |

## Deliberately not changed

* **Post titles and descriptions that repeat across years.** "Holiday Hack
  Orientation" legitimately titles three different posts, one per challenge
  year. `tools/seo_check.py` reports these as information, not failure —
  rewriting them would be editing content to satisfy a metric.
* **Three pre-existing outbound `http://` links** in the author's prose
  (`kc7cyber.com`, `1amstudios.com`, and `paulweb.neighborhood`, which is an
  in-fiction CTF domain). Confirmed present at `HEAD` before any change. CI
  already runs html-proofer with `--no-enforce-https`.
* **Post permalinks.** Derived from filenames, so some slugs are imperfect
  (`2023-03-Linux-101` from a filename containing a space;
  `2025-20-Snowcat-RCE-&-Priv-Esc` contains a raw `&`). Changing them would break
  live URLs. Documented, not touched.
* **Theme-level accessibility issues** on posts: heading anchor links with no
  accessible name (23 on one page), post-navigation `aria-label` mismatches, and
  Mermaid edge-label contrast. Real, but they live in the theme's
  `_includes/refactor-content.html`; fixing them means forking a ~200-line
  include, which is a poor trade against this mission's scope. Recorded as
  follow-up.
* **The legacy Pages pipeline.** See `ROOT_CAUSE.md` R6 — needs a repo-admin
  change to the Pages source setting.
