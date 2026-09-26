# Baseline — the site before remediation

All figures below were measured against the **live** site on 2026-09-26, before
any change was deployed. Live HEAD at the time: `1bb5aee` (2026-01-31), theme
`jekyll-theme-chirpy 7.4.1`, last deployed 2026-01-31T17:59Z.

## 1. Transport and host behaviour

| Check | Result |
| --- | --- |
| `http://` → `https://` | 301, correct |
| `https://thedead91.github.io/` | 200 |
| `https://www.thedead91.github.io/` | TLS failure — GitHub does not issue certs for `www` on user/org Pages. Not controllable from the repo. |
| Trailing slash | `/page2` → **301** → `/page2/`. The theme's paginator emits the slash-less form, so every pagination link costs a redirect hop. |
| `404` behaviour | Unknown paths correctly return HTTP 404 with the custom page. |
| Non-existent pages | 404 (e.g. `/page9/`, `/index.xml`, `/sw.js`, `/manifest.json`) |
| `X-Robots-Tag` | never present |
| `<meta name="robots">` | never present on any page |
| Hreflang | not applicable (single language, single host) |

Broken internal links: **none** (html-proofer, 898 internal links, 0 failures).

## 2. robots.txt

Came from the **theme**, not the repository (the repo has no `robots.txt`):

```
User-agent: *

Disallow: /norobots/

Sitemap: https://thedead91.github.io/sitemap.xml
```

`/norobots/` does not exist in the repository and never has. It is Chirpy
starter-demo boilerplate. The file is otherwise permissive, so robots.txt was
**not** blocking anything — an important negative result, since "check robots.txt
first" is the usual first hypothesis.

## 3. Sitemap

`/sitemap.xml` → 200, `application/xml`, **validates against the official
sitemaps.org 0.9 XSD**, 203 `<url>` entries, all absolute `https`, no
duplicates, all `<lastmod>` values valid W3C-DATETIME.

Composition of those 203 URLs:

| Kind | Count | Assessment |
| --- | ---: | --- |
| posts | 73 | correct |
| individual tag archive pages | 106 | **thin duplicates** |
| category archive pages + `/categories/` | 12 | mostly legitimate hubs |
| `/tags/` index | 1 | legitimate |
| `/about/`, `/archives/` | 2 | legitimate |
| paginated listings `/page2/`–`/page8/` | 7 | **duplicates of the index** |
| `google18a85a9229001990.html` | 1 | **a site-verification file, not content** |

So **114 of 203 advertised URLs (56%) were navigational or non-content
duplicates**, every one of them self-canonical, indexable, and carrying the
identical meta description `"Yet another blog"`.

## 4. Metadata quality across all 210 HTML documents crawled

| Metric | Value |
| --- | --- |
| Documents with a canonical | all HTML pages |
| Canonical mismatches | 7, all the `/page2`…`/page8` slash-less redirect variants |
| Documents with `<meta name="description">` | 136 carried the literal string `"Yet another blog"` |
| Duplicate `<title>` groups | 15 URLs shared the exact title `TheDead91` (homepage + 7 pagination pages + their 7 redirect variants) |
| Duplicate `<title>` (tag vs post) | ~59 tag pages reused the **exact** title of the single post they listed, because the tags are named after post titles |
| `og:image` | **absent on 100% of pages** — `social_preview_image` was empty |
| `twitter:card` | `summary` (no image) |
| Feed discovery `<link rel="alternate">` | **absent from every page.** The Atom feed exists at `/feed.xml` and was reachable only through a sidebar icon. |
| Viewport | `user-scalable=no, shrink-to-fit=no` — pinch-zoom disabled (WCAG 2.1 SC 1.4.4 failure) |
| Invalid JSON-LD | 0 |
| Documents with no `lang` | 1 (`/posts/2024-09-PowerShell/`, see §7) |

### Tag pages were the dominant problem

Of 106 individual tag archive pages:

* **105 rendered fewer than 1,200 characters of text**; median **59 characters**,
  minimum 25.
* Each listed exactly one post (the tags are per-challenge and per-NPC name).
* Each used the **same `<title>` as that post**.

That is ~106 indexable, self-canonicalised, near-empty pages that compete with
the 73 real posts they point at.

## 5. Structured data

* Posts: valid `BlogPosting` with `headline`, `datePublished`, `dateModified`,
  `author`, `mainEntityOfPage`, `url`. Accurate.
* Non-post pages: jekyll-seo-tag's `WebSite` object, which includes a `headline`
  property that does not belong on `WebSite`. Cosmetic; not worth fighting the
  gem over.

**Important limitation found:** the installed `jekyll-seo-tag 2.9.0` has **no
support whatsoever for a robots meta tag** — grepping the gem's `lib/` for
`robots` returns nothing. Any `noindex` therefore has to be emitted by the site
itself. This is why `_includes/metadata-hook.html` is overridden.

## 6. Lighthouse (live site, before changes)

| Page | SEO | Accessibility | Best Practices |
| --- | ---: | ---: | ---: |
| `/` | **100** | 95 | 100 |
| a post | **100** | 93 | 100 |
| `/page2/` | **100** | 95 | 100 |

The accessibility failures were: an anchor with no discernible name (the footer
copyright link — `social.name` was commented out in `_config.yml`, so the
footer rendered `© 2026 <a href="…"></a>.` with an empty anchor), plus, on
posts, theme-level heading-anchor and Mermaid contrast issues.

**This is the headline lesson of the audit: the site scored a perfect 100 on
Lighthouse SEO while Google had never heard of a single post.** Lighthouse SEO
audits the markup of one URL; it cannot see whether the site is crawled or
indexed.

## 7. One genuine HTML-validity defect

`/posts/2024-09-PowerShell/` emitted a **second `<html><head><title>` element
inside `<body>`**. Cause: in the post's markdown a fenced code block begins on
the line immediately after a list item, so kramdown treats the fence as a lazy
continuation of the list, emits the fence markers as literal prose, and the raw
markup inside the block leaks into the document.

A scan of the built output found this on exactly **1 of 203** documents
(4 leaked fence markers). A second post, `/posts/2025-20-Snowcat-RCE-&-Priv-Esc/`,
contains literal ``` ``` ``` characters, but those sit **inside** a `<pre>`
block — the author is deliberately using a 4-backtick fence to display 3-backtick
markers — so that is correct rendering, not a defect.

## 8. Build reproducibility

`Gemfile.lock` was in `.gitignore`, so every build resolved the newest allowed
versions.

* Live site was built with chirpy **7.4.1**.
* A fresh `bundle install` resolved chirpy **7.6.0**.
* 7.6.0 combined with this site's `compress_html` settings emits
  `<html lang="en"data-bs-theme="dark">` — a missing attribute separator, i.e.
  invalid HTML on every page.

`Gemfile` also declared `jekyll-theme-chirpy", "~> 7.4"`, which in RubyGems
means `>= 7.4, < 8.0` — so the minor version was never actually pinned.

## 9. Deployment

`.github/workflows/pages-deploy.yml` builds with `actions/deploy-pages`, and the
repository's Actions history shows the legacy `pages build and deployment`
dynamic workflow **also** running on every push. On 2026-01-31 alone there were
8 `github-pages` deployments. Two pipelines were competing.

The live build is the Actions artifact, not the legacy branch build: the sitemap
contains `lastmod` values such as `2026-01-06T13:27:29+01:00`, which can only be
produced by the repository's own `_plugins/posts-lastmod-hook.rb` (it shells out
to `git log`). GitHub's legacy branch builder does not execute `_plugins/`.

## 10. Google Search Console state

Properties the authorised account owns: `https://thedead91.github.io/`,
`sc-domain:thedead91.com`, `https://holidayhackchallenge.thedead91.com/`.

### Search Analytics, 2023-01-01 → 2026-09-25 (site lifetime)

Only **4 URLs** have ever produced a single impression:

| URL | clicks | impressions | avg position |
| --- | ---: | ---: | ---: |
| `/` | 1 | 165 | 5.03 |
| `/archives/` | 0 | 19 | 5.74 |
| `/tags/` | 0 | 17 | 6.47 |
| `/categories/` | 0 | 4 | 2.50 |

Total: **1 click, 205 impressions** since the site's first commit (2025-11-29).
First impression 2025-12-22; last 2026-08-02.

The only ranking queries are four variants of *Schrödinger's Scope holiday hack
challenge*, and **all 14 of those impressions are attributed to the homepage**,
not to the post. That is the signature of a post that is not in the index: Google
matches the query against the homepage, which lists the post title and summary.

### URL Inspection (the authoritative signal)

| URL | coverageState | lastCrawl | pageFetch | robots | verdict |
| --- | --- | --- | --- | --- | --- |
| `/` | Crawled - currently not indexed | 2026-06-11 | SUCCESSFUL | ALLOWED | NEUTRAL |
| `/categories/` | Crawled - currently not indexed | 2026-09-17 | SUCCESSFUL | ALLOWED | NEUTRAL |
| `/archives/` | Crawled - currently not indexed | 2026-06-07 | SUCCESSFUL | ALLOWED | NEUTRAL |
| `/tags/` | Crawled - currently not indexed | 2026-05-30 | SUCCESSFUL | ALLOWED | NEUTRAL |
| 7 sampled posts (2023/2024/2025) | **URL is unknown to Google** | — | — | — | NEUTRAL |
| `/page2/`, `/page8/` | URL is unknown to Google | — | — | — | NEUTRAL |
| `/about/` | URL is unknown to Google | — | — | — | NEUTRAL |
| `/tags/elf-hunt/`, `/tags/snowblind-ambush/` | URL is unknown to Google | — | — | — | NEUTRAL |
| `/categories/sans-holiday-hack-challenge-2025/` and `-2023/` | URL is unknown to Google | — | — | — | NEUTRAL |
| `/404.html` | URL is unknown to Google | — | — | — | NEUTRAL |
| `/google18a85a9229001990.html` | URL is unknown to Google | — | — | — | NEUTRAL |

For all four crawled URLs, `userCanonical == googleCanonical`, robots is
`ALLOWED` and the fetch was `SUCCESSFUL`. There is **no technical block and no
canonical conflict** anywhere. `referringUrls` and `sitemaps` are empty
throughout.

### Submitted sitemaps

| Submitted path | Last submitted | State |
| --- | --- | --- |
| `…/sitemap.xml` | 2025-12-22 | `isPending: true`, 0 errors, 0 warnings |
| `…/sitemap.xml?v=2` | 2025-12-24 | `isPending: true` — a stale cache-buster duplicate |
| `…/feed.xml` | 2026-01-05 | `isPending: true` — **an Atom feed submitted as a sitemap** |

All three have been `isPending` for 8–9 months. Two of the three were never
valid sitemap submissions in the first place.

## 11. Google Indexing API misuse

`.github/workflows/google-indexing.yml` posted `urlNotifications:publish`
`URL_UPDATED` (and `URL_DELETED`) notifications for every sitemap URL via a
service account, using the `https://www.googleapis.com/auth/indexing` scope.

The public Actions history shows **19 runs, 15 successful, all on 2026-01-31**,
triggered by `push`, `deployment_status` and `workflow_run` on
`pages-build-deployment` (which does exist as a dynamic workflow, so the
`workflow_run` trigger does fire). The workflow was therefore live and would
re-fire on the next deploy.

The Indexing API is documented for job posting pages and broadcast/live-blog
events. SANS Holiday Hack Challenge write-ups are ordinary blog posts and are
outside its supported use cases. Google states that using it on out-of-scope
pages can result in those pages being dropped from the index.
