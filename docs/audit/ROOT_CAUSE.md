# Root-cause assessment

Classification is strict:

* **CONFIRMED** — direct evidence demonstrates the problem.
* **HIGH CONFIDENCE** — multiple independent signals support the diagnosis.
* **POSSIBLE** — plausible, not demonstrated.

## Headline

The posts were never blocked. They were never **found**. Google has crawled four
URLs on this site in its entire lifetime, all four reachable from the site-wide
sidebar, and has never discovered one of the 73 posts.

---

## R1 — The site's own URL inventory was mostly non-content duplicates

**CONFIRMED.**

Direct measurements:

* 203 URLs in the deployed sitemap, of which **114 (56%)** were navigational or
  non-content: 106 per-post tag archive pages, 7 paginated listings, 1
  site-verification file.
* **105 of the 106 tag pages rendered under 1,200 characters of text**
  (median 59, min 25), each listing exactly one post.
* Each of those tag pages used the **exact `<title>` of the post it listed**.
* **136 documents** carried the identical meta description `"Yet another blog"`.
* **15 URLs** shared the byte-identical title `TheDead91`.
* `/page2/`–`/page8/` were self-canonical, indexable, in the sitemap, and
  identical in title and description to the homepage.

Google's own verdict on the pages it did fetch is `Crawled - currently not
indexed`, and its verdict on everything else is `URL is unknown to Google`. A
site whose indexable surface is 56% near-empty self-duplicates presents exactly
the shape that gets crawled shallowly.

There is no crawl-budget *scarcity* here in the ordinary sense — 204 URLs is
trivial. The problem is that the crawl frontier is dominated by duplicates, so
the crawl terminates after the navigation shell.

## R2 — The Google Indexing API was used outside its supported scope

**CONFIRMED** (that it happened, and that it is out of scope).
**HIGH CONFIDENCE** (that it materially harmed this domain).

Evidence:

* Public Actions history: 19 runs, **15 successful**, all on 2026-01-31, against
  `https://indexing.googleapis.com/v3/urlNotifications:publish`, for every
  sitemap URL.
* The trigger `workflow_run` on `pages-build-deployment` refers to a workflow
  that genuinely exists, so the job was armed and would re-fire on the next
  deploy.
* The URLs notified were SANS Holiday Hack Challenge write-ups: ordinary blog
  posts, not job postings or live-blog broadcast events, which is what Google's
  documentation restricts the Indexing API to.

The causal link to the indexing outcome cannot be proven from the outside — the
Search Console API does not expose manual actions, and a penalty would not be
attributable to a specific API call. What is certain is that this was a
documented policy violation, it was repeated at scale, and it is the only
mechanism in the repository that actively pushed URLs at Google outside of
normal crawl discovery. Removed.

## R3 — Sitemap discovery was misconfigured and never took effect

**CONFIRMED.**

* Three submissions existed. `sitemap.xml?v=2` is a stale cache-buster
  duplicate. `feed.xml` is an **Atom feed submitted as a sitemap** — never a
  valid sitemap submission.
* All three report `isPending: true` after 8–9 months.
* The URL Inspection API returns an empty `sitemaps` field for every URL
  inspected, including the homepage. No sitemap is associated with any URL.

Whatever the reason for `isPending`, the two malformed submissions meant that
two of the three signals pointing Google at this site's URL list were noise.

## R4 — Duplicate `<title>`/`<meta name="description">` across the whole indexable set

**CONFIRMED.**

136 documents shared one description; 15 shared one title; ~59 tag pages reused
a post's title. Every one of these pages is self-canonical and was advertised in
the sitemap, so the site explicitly asked Google to index many near-identical
documents and told it they were each the authoritative version of themselves.
Fixed in the generator, not in the generated output.

## R5 — Build was not reproducible, and the next build would have emitted invalid HTML

**CONFIRMED.**

`Gemfile.lock` was gitignored, so builds floated. Live is chirpy 7.4.1;
`bundle install` today resolves 7.6.0, which under this site's `compress_html`
configuration emits `<html lang="en"data-bs-theme="dark">` — a missing
attribute separator — on every page. Reproduced locally before fixing.

## R6 — Two competing GitHub Pages deployment pipelines

**CONFIRMED** (that both ran). **POSSIBLE** (that this caused a bad deploy).

Eight `github-pages` deployments on 2026-01-31 between `actions/deploy-pages`
and the legacy `pages build and deployment`. The live content is demonstrably the
Actions artifact (its sitemap carries `lastmod` values that only
`_plugins/posts-lastmod-hook.rb` can produce, and the legacy builder does not
run `_plugins/`), so no incorrect content was served. It remains untidy and
wasteful, and the resolution requires a repository-admin change to the Pages
source setting. Left as a documented follow-up.

## R7 — Metadata and markup gaps

**CONFIRMED**, individually small:

| Finding | Evidence |
| --- | --- |
| No `og:image` anywhere | 0 of 210 documents; `social_preview_image` was empty |
| No feed discovery link | 0 of 210 documents had `link rel=alternate` |
| Pinch-zoom disabled | `user-scalable=no` on all pages (WCAG 2.1 SC 1.4.4) |
| Empty copyright link | `social.name` commented out → `<a href="…"></a>` |
| Verification file published as content | in the sitemap, HTTP 200, indexable |
| `/404.html` indexable | HTTP 200, self-canonical, no `noindex` |
| Stray `<html><head><title>` in a post body | 1 of 203 documents; kramdown absorbed a fence into a list item |

None of these individually prevents indexing. Together they are the difference
between a page that is merely acceptable and one that gives a crawler no reason
to keep going.

## What was ruled out

Recording these matters, because they are the usual first hypotheses:

* **robots.txt blocking content** — ruled out. The only `Disallow` is
  `/norobots/`, a directory that has never existed.
* **`noindex` on posts** — ruled out. Zero `meta robots` and zero `X-Robots-Tag`
  on the live site.
* **Canonical conflicts or loops** — ruled out. For all four crawled URLs,
  `userCanonical == googleCanonical`, and no canonical points anywhere but itself.
* **Broken internal links** — ruled out. html-proofer: 898 internal links, 0
  failures.
* **JavaScript-dependent rendering** — ruled out. Posts ship ~20,000 characters
  of content in the initial HTML; no framework, no hydration requirement.
* **Thin content on the posts themselves** — ruled out. The sampled post had
  20,414 characters of main-content text and complete solutions.
* **Sitemap syntax errors** — ruled out. `xmllint --schema` against the official
  sitemaps.org 0.9 XSD: *validates*.
* **A bad `lastmod`** — ruled out. All 78 values parse as W3C-DATETIME.

## Not claimed

* No ranking improvement is promised. This audit addresses crawlability,
  discovery, canonicalisation and index hygiene. Ranking is a separate system.
* "No impressions" is not treated as proof of non-indexing. The conclusions above
  rest on the URL Inspection API's `coverageState` and `lastCrawlTime`, which are
  Google's own record, not on the absence of Search Analytics rows.
* The URL Inspection API returns Google's **most recent stored** index state. It
  is not a live re-crawl, and the API exposes no "request indexing" operation.
  The remediation is expected to change Google's state only on Google's own
  schedule.
