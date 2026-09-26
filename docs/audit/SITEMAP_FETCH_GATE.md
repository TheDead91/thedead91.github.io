# Sitemap fetch recovery gate

Question under investigation: Google Search Console reports
`https://thedead91.github.io/sitemap.xml` as **"Couldn't fetch"**, while the
file is publicly reachable and, on inspection, technically correct.

Date of investigation: 2026-09-26, 18:35Z – 19:25Z.
Scope: this gate only. No content, metadata, theme or accessibility work was
reopened, and the Indexing API was not used. No URL was manually requested for
indexing.

## A. Identity

| Item | Value |
| --- | --- |
| Repository | `https://github.com/TheDead91/thedead91.github.io` |
| Branch | `main` |
| Starting HEAD | `c5a188552aea78e678021c0a20f51f05cc540334` |
| Intermediate HEAD | `2966f05` (temporary diagnostic sitemap) |
| Final HEAD | the commit that adds this file (see `git log -1`; its hash cannot be written inside itself) |
| Tree before this gate | clean |
| Tree after this gate | clean |
| Property queried | `https://thedead91.github.io/` (URL-prefix, `siteOwner`) |
| Deployment | push to `main` → `.github/workflows/pages-deploy.yml` |

The three properties on the account are `https://thedead91.github.io/`,
`https://holidayhackchallenge.thedead91.com/` and `sc-domain:thedead91.com`.
Only the first was touched. `sc-domain:thedead91.com` does not cover
`thedead91.github.io`, so there is no property overlap.

## B. Search Console state

`sitemaps.list` for `https://thedead91.github.io/`, read at 18:35Z, i.e. 5h20m
after the last submission:

```json
{"path": "https://thedead91.github.io/sitemap.xml",
 "lastSubmitted": "2026-09-26T13:14:41.252Z",
 "isPending": true, "isSitemapsIndex": false,
 "warnings": "0", "errors": "0"}
```

The single most informative detail is what is **absent**: there is no
`lastDownloaded` and no `contents`. Those two fields only appear once Google
has actually fetched and parsed a sitemap.

The same field was read by the previous engagement at 14:59 local
(12:59:17.655Z) and was identical apart from the timestamp, so the state has
been static across the whole window. Two prior submissions are on record and
both were of this exact canonical path: `2026-09-26T12:59:17.655Z` and
`2026-09-26T13:14:41.252Z`. Stale submissions (`/feed.xml` submitted
2026-01-05, `/sitemap.xml?v=2` submitted 2025-12-24) had already been deleted
before this gate. No HTTP/HTTPS duplicate, no `?v=` variant, no feed, no
sitemap index and no old path is registered.

`errors: "0"` and `warnings: "0"` must not be read as a clean bill of health.
They are the documented default for an unprocessed sitemap; they are only
meaningful once `contents` is present.

### Account-level control

The sibling property makes the capability explicit. Its sitemap was submitted
at `2025-01-04T23:06:03.183Z` and:

```json
{"path": "https://holidayhackchallenge.thedead91.com/sitemap.xml",
 "lastSubmitted": "2025-01-04T23:06:03.183Z", "isPending": false,
 "type": "sitemap",
 "lastDownloaded": "2025-01-04T23:06:04.269Z",
 "warnings": "0", "errors": "0",
 "contents": [{"type": "web", "submitted": "69", "indexed": "0"}]}
```

Google downloaded that sitemap **1.086 seconds** after submission and the API
reports `lastDownloaded`, `type` and `contents` for it. The same API, on the
same account, therefore does report successful sitemap fetches. Note also
`indexed: "0"` of 69: that property's sitemap is fetched correctly and still
indexes nothing, which is a useful reminder that a fetched sitemap and an
indexed site are different things.

## C. Live HTTP evidence for /sitemap.xml

```text
HTTP/2 200
content-type: application/xml
content-length: 11860
last-modified: Sat, 26 Sep 2026 18:44:31 GMT
etag: "6ab8128f-2e54"
cache-control: max-age=600
vary: Accept-Encoding
server: GitHub.com
x-cache: MISS
x-github-request-id: 6D9662:...   (varies per request, normal)
x-fastly-request-id: ...           (varies per request, normal)
```

| Property | Value |
| --- | --- |
| Status | `200`, no redirect, `num_redirects: 0` |
| Final URL | `https://thedead91.github.io/sitemap.xml` |
| `Content-Type` | `application/xml` (Google's documented accepted type) |
| Body length | 11860 bytes identity, 1613 bytes gzipped |
| Transfer/content encoding | `gzip` negotiated, `identity`, `deflate` and `br` all decode to the identical body |
| BOM | none; first bytes are `3c 3f 78 6d` = `<?xm` |
| XML declaration | `<?xml version="1.0" encoding="UTF-8"?>` |
| Namespace | `http://www.sitemaps.org/schemas/sitemap/0.9` |
| Well-formedness | passes `xmllint --noout` |
| Schema validity | **validates against the sitemaps.org 0.9 XSD**, fetched live during this gate |
| Trailing bytes | exactly one `\n` after `</urlset>`; no NUL, no non-ASCII |
| Accidental HTML / Jekyll output | none; the single `&` in the set is correctly escaped as `&amp;` in `.../2025-20-Snowcat-RCE-&amp;-Priv-Esc/` |
| Duplicate URLs | none (89 unique) |
| Query strings / fragments in `<loc>` | none |
| Non-HTTPS or off-origin `<loc>` | none; all 89 are `https://thedead91.github.io` |
| Redirects inside the sitemap | none |
| Future-dated `<lastmod>` | none; max `2026-09-26T15:02:22+02:00` is in the past |

Hashes:

| Artefact | sha256 |
| --- | --- |
| Live, 18:36Z (pre-gate deploy) | `151fea5a978e90a28a1befef93d61c93daa2a27ef587193d67d0a85ca2bc7994` |
| Local `_site` build, 14:53 local | `7500a6980d23c3203b157c0b413e2a99981f318ea0c35808b6b45e74f4295360` |
| Live, 18:44Z (after this gate's deploy) | `45b8bf8c2129bad3e1897c4a267d4f8bfd151d1d1e614bc4bd3d89994452ec66` |

The three differ only in `<lastmod>` values. The URL membership is byte-for-byte
identical across all three, and the live document validates after each
deployment. The non-post `<lastmod>` values are the build clock, so they move
on every deploy by design. **This is not a deployment mismatch and not a stale
artefact.**

`"Couldn't fetch"` is a *retrieval* verdict, not a validation verdict. A
document that is schema-valid, publicly reachable and self-consistent cannot
cause a retrieval failure, which is why the document contents were treated as
exonerated early and the remaining effort went to the delivery path and to a
controlled experiment.

## D. Sitemap population

All 89 `<loc>` values were fetched with a Googlebot user agent and parsed.

| Check | Result |
| --- | --- |
| Total URLs | 89 |
| HTTP 200 | **89 / 89** |
| Redirects (`final != loc`) | 0 |
| Blocked by robots.txt | 0 |
| `noindex` while in the sitemap | 0 |
| Canonical mismatch | 0 |
| Missing canonical | 0 |
| `sitemap.xml` itself in the sitemap | no |

Composition: 73 posts, 11 category archives, `/categories/`, `/tags/`,
`/archives/`, `/about/` and the homepage.

## E. robots.txt

```text
HTTP/2 200
content-type: text/plain; charset=utf-8
content-length: 264

User-agent: *

Allow: /

Sitemap: https://thedead91.github.io/sitemap.xml
```

- Plain ASCII, LF line endings, no BOM.
- `User-agent: *` with `Allow: /`. No `Disallow` anywhere, so nothing relevant
  is blocked.
- Exactly one `Sitemap:` directive and it is character-for-character the
  submitted sitemap URL, https and all.
- The sitemap is reachable independently of the declaration: it is fetched
  directly and by URL, and it is advertised in no `<link rel="sitemap">`
  (the site emits none; the feed is correctly advertised as
  `rel="alternate" type="application/atom+xml"`).

## F. Fetch-path tests

| Test | Result |
| --- | --- |
| Normal GET (`curl/8.5.0`) | 200, 11860 bytes |
| Browser UA | 200, identical body |
| `Googlebot/2.1` | 200, identical body |
| `Googlebot-Smartphone/2.1` | 200, identical body |
| `Googlebot-Image/1.0` | 200, identical body |
| No `User-Agent` header at all | 200, identical body |
| `HEAD` | 200, `content-length: 11860`, `application/xml` |
| HTTP/2 vs HTTP/1.1 | both 200, identical body |
| HTTP/1.0, no `Accept`, no UA | 200, identical body |
| `Connection: close` | 200, identical body |
| `Accept-Encoding`: identity / gzip / deflate / br | all 200, all decode to the identical body |
| `If-None-Match` (current ETag) | `304` |
| `If-Modified-Since` | `304` |
| `Range: bytes=0-99` | `206`, 100 bytes |
| IPv4 (`-4`, `185.199.111.153`) | 200, identical body |
| IPv6 (`-6`, `2606:50c0:8002::153`) | 200, identical body |
| Case-varied host | 200, identical body |
| `:443` explicit | 200, identical body |
| Query-string cache bust | 200, identical body |
| Repeated requests | 30 normal + 10 Googlebot + 60 concurrent at 20-way parallelism: **every one 200 with one single body hash**, no 404, no 5xx, no 429, no rate limiting |
| Throttled to 1 kB/s | 200 after 10.4s, no truncation |
| `http://` scheme | 301 to HTTPS, as expected |

DNS: four `A` (185.199.108–111.153) and four `AAAA` records, no CNAME, all
reachable. TLS: `CN=*.github.io`, issuer Let's Encrypt `YR1`, valid
2026-08-02 → 2026-10-31, SAN covers `*.github.io`; TLS 1.2 and 1.3 both
negotiate, chain verifies.

GitHub Pages status was checked during the window: `All Systems Operational`,
zero incidents, zero scheduled maintenances. The submission at 13:14:41Z
coincided with a fully healthy Pages.

**Conclusion: no UA-dependent behaviour, no anti-bot behaviour, no IPv6 fault,
no CDN or cache anomaly, no intermittent failure, no malformed compression and
no content-negotiation difference was found. The delivery path is sound.**

## G. Controlled sitemap experiment

A deliberately minimal second sitemap was deployed and submitted to the same
property, so that a single pair of submissions on the same host, at the same
moment, through the same delivery path, would separate a document-level cause
from a property-level one.

- File: `sitemap-test.xml` → `https://thedead91.github.io/sitemap-test.xml`
- Contents: homepage + 2 canonical posts, 3 URLs, 329 bytes
- Deliberate differences from `sitemap.xml`: 3 URLs instead of 89; no
  `<lastmod>` at all; no `xsi:schemaLocation`; no indentation or inter-element
  newlines; no URL containing an ampersand
- Everything required for validity retained: XML declaration, UTF-8,
  canonical namespace, HTTPS absolute URLs, and all 3 URLs are HTTP 200,
  self-canonical, indexable and unblocked
- `sitemap: false` kept it out of the canonical sitemap, so the diagnostic
  could not contaminate the document it was diagnosing. Verified: the
  canonical sitemap still reported 89 `<loc>` after the deploy
- Deployed: pushed 18:42:39Z, live `last-modified: 18:44:31 GMT`
- Live verification: 200, `application/xml`, 329 bytes, sha256
  `585c6b478e57b14a48ed366b1cf663dbf1e5215bea75ea5a7dae79f59405dc55`,
  byte-identical to the built artefact, **validates against the sitemaps.org
  0.9 XSD**, 10/10 Googlebot-like requests identical
- Submitted: `2026-09-26T18:44:55.314Z`
- CI on that commit: `tools/seo_check.py` reported *OK all checks passed*, 89
  sitemap URLs; `htmlproofer` finished successfully on 204 files

Deliberately, the canonical sitemap was **not** re-submitted, so its
`13:14:41.252Z` timer and its 5h20m of accumulated pending state were left
intact as evidence.

Result: both sitemaps behaved identically.

| Time (UTC) | `sitemap.xml` | `sitemap-test.xml` |
| --- | --- | --- |
| submitted | 13:14:41.252Z | 18:44:55.314Z |
| last observed state | 19:21:15Z | 19:21:15Z |
| `isPending` | true | true |
| `lastDownloaded` | absent | absent |
| `contents` | absent | absent |
| `errors` / `warnings` | 0 / 0 | 0 / 0 |

19 samples at 2-minute intervals over 36 minutes produced **exactly one
distinct state**. Nothing changed.

**This is CASE B.** A 3-URL, 329-byte, byte-minimal document at a different
filename, containing none of the canonical document's optional or awkward
constructs, is not fetched either. Population size, `<lastmod>` presence and
timezone format, `xsi:schemaLocation`, indentation, entity escaping and
filename are therefore all eliminated as causes, because removing every one of
them changed nothing.

## H. Root-cause analysis

| Hypothesis | Verdict | Basis |
| --- | --- | --- |
| Live sitemap is malformed, mis-encoded or truncated | **RULED OUT** | XSD-valid, no BOM, no trailing garbage, byte-identical across every fetch mode |
| Sitemap is not publicly reachable | **RULED OUT** | 200 from ~100 probes, 4 A + 4 AAAA, two external networks, `no User-Agent` included |
| `Content-Type` unacceptable | **RULED OUT** | `application/xml`, the type Google documents |
| robots.txt blocks or misdeclares | **RULED OUT** | 200, `text/plain`, no `Disallow`, exact canonical `Sitemap:` line, sitemap reachable independently |
| A sitemap URL is broken (404/5xx/redirect/noindex/canonical drift) | **RULED OUT** | 89/89 at 200, 0 redirects, 0 noindex, 0 canonical mismatches, 0 robots blocks |
| Googlebot-specific blocking or cloaking | **RULED OUT** | Googlebot, Googlebot-Smartphone, Googlebot-Image and no-UA all 200 with one body. This does not prove real Googlebot access; it only shows no UA-dependent behaviour |
| IPv6 / CDN / edge / geo anomaly | **RULED OUT** | v4 and v6 identical, 60 concurrent requests identical, several Fastly POPs, no 429 |
| Compression or content-negotiation corruption | **RULED OUT** | identity/gzip/deflate/br all decode identically; `Range` honoured |
| Intermittent GitHub Pages failure during Google's fetch window | **RULED OUT** | `All Systems Operational`, 0 incidents, 0 maintenance at the submission time |
| Stale or duplicate submissions confusing the fetch | **RULED OUT** | exactly one registered sitemap before the experiment; no `?v=`, no http, no feed, no index |
| Deployment mismatch / stale generated artefact | **RULED OUT** | live body matches the local build; only build-clock `<lastmod>` differs; URL membership identical |
| Feed or another artefact advertised as a sitemap | **RULED OUT** | no `rel="sitemap"` in the build or on any live page; 10 other sitemap-ish paths all 404 |
| Document complexity (89 URLs, `<lastmod>`, entity, `schemaLocation`) | **RULED OUT** | CASE B: a 329-byte document with none of those behaves identically |
| Google's fetch is queued but not yet executed for this property | **HIGH CONFIDENCE** | `isPending: true` with `lastDownloaded` and `contents` absent, unchanged across 5h48m and 19 samples; the sibling property on the same account shows the API reporting a download in 1.086s when one happens |
| Google-side reporting condition: the UI verdict predates the current submission | **POSSIBLE** | the canonical was submitted twice (12:59:17Z, 13:14:41Z) and a re-submission resets the displayed status; the API has reported pending, not an error, since 12:59Z. The API cannot distinguish a stale UI row from a live one, so this cannot be confirmed from here |
| Google's fetch fails for a network or anti-bot reason invisible to this host | **POSSIBLE** | cannot be tested from a single vantage point; would be an edge/Google-side fault, and the sibling control shows the account is capable of a logged fetch |
| Low crawl priority for a property Google has barely crawled | **POSSIBLE** | homepage `lastCrawlTime` 2026-06-11, 73 posts "URL is unknown to Google", 3 impressions in 90 days, `site:` returns no results, sibling property 0/69 indexed. This is consistent with the pending state but is a contributing condition, not a demonstrated mechanism |

A note on over-reading the evidence: Search Console API state is not a live
Googlebot request, not a URL Inspection test and not a guarantee of indexing. A
Googlebot-like `User-Agent` is not Googlebot. The absence of `lastDownloaded`
means this API has not recorded a fetch; it cannot exclude that Google fetched
something outside the state the API exposes.

## I. Remediation

**No defect under our control was found, so no corrective change was made.**

The sitemap, its generation, its population, its robots declaration and its
delivery path are all correct. The only repository change made was the
temporary diagnostic sitemap, which has been removed again. No speculative
change was made:

- `lastmod` was **not** normalised to `Z`, even though the offsets are unusual.
  It cannot cause a *fetch* failure and the test sitemap already proved that
  removing `lastmod` entirely changes nothing.
- The sitemap was **not** re-submitted, because that would have reset the
  canonical's pending timer and destroyed the evidence.
- No second sitemap was left behind, so the site's one-sitemap architecture
  established by the previous engagement is intact.

One unrelated local issue was fixed in the tooling rather than the site:
`/root/gsc/gsc.py` requested two OAuth scopes while the stored grant covers
one, so every API call died with `invalid_scope` before reaching the network.
It now honours the scope recorded in the token, and gained a
`delete-sitemap` subcommand.

## J. Post-remediation Search Console state

Final read of `sitemaps.list` for `https://thedead91.github.io/`:

```json
{"path": "https://thedead91.github.io/sitemap.xml",
 "lastSubmitted": "2026-09-26T13:14:41.252Z",
 "isPending": true, "isSitemapsIndex": false,
 "warnings": "0", "errors": "0"}
```

Exactly one sitemap, still pending, still no `lastDownloaded`, still no
`contents`, 0 errors, 0 warnings. Nothing was reset by this gate and no new
submission of the canonical sitemap was made.

## K. Cleanup

- The `sitemap-test.xml` submission was removed from Search Console at
  19:23:21Z, **before** the file was deleted, so that Google can never be left
  attempting a fetch of a path this investigation removed. GSC therefore never
  learns of a URL that no longer exists.
- `sitemap-test.xml` was deleted from the repository and redeployed.
- No temporary sitemap, file or submission remains.
- No credentials, tokens or secrets were written to the repository. All
  diagnostic evidence lives under `/root/gsc/out/gate/`, outside every git
  repository. `/root/gsc/gsc.py`, `crawl.py`, `popcheck.py`, `fetchpath.sh` and
  `poll.sh` are all outside the repository.

## L. What would constitute meaningful new evidence

- `sitemaps.list` for this property returning a `contents` array, a
  `lastDownloaded` timestamp, `isPending: false`, or a non-zero `errors` /
  `warnings` count. Any of these is a real state transition and would end the
  ambiguity. Polling that endpoint is the single decisive observation, and it
  needs no change on the site.
- A non-zero `errors` value with a message. That would convert this from
  "not yet processed" into a diagnosed failure, and the error text would name
  the cause.
- A change in the `sitemaps` field of `indexStatusResult` for any URL. The
  inspection response is currently flat and contains no `sitemaps` key at all;
  its appearance means the sitemap has been processed and associated.
- A `lastCrawlTime` later than `2026-06-11T11:21:17Z` for the homepage. That
  would show crawl activity resuming, which is a precondition for sitemap
  processing being visible.
- Evidence from Google's side that its fetcher reached the URL, for example a
  logged 200 from Google's infrastructure. Nothing available to this
  investigation can substitute for that, and it is the one thing still not
  directly observable from here.

Absent one of the above, further changes to the sitemap would be
unfalsifiable. There is nothing left on the site to test.
