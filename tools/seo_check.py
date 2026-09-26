#!/usr/bin/env python3
"""Regression checks for the site's crawl / index architecture.

Standard library only, so it runs unchanged in CI (ubuntu-latest ships Python 3)
and locally.

    python3 tools/seo_check.py _site

Every assertion here corresponds to a defect found during the indexing audit and
documented in docs/audit/ROOT_CAUSE.md. The intent is to protect *intent*
("a post must be discoverable and indexable", "the sitemap must only advertise
indexable canonical URLs") rather than to pin implementation details such as
exact wording, so the checks survive ordinary copy edits.

Exit status is 0 when everything passes, 1 otherwise.
"""
import argparse
import collections
import html
import json
import os
import posixpath
import re
import sys
import urllib.parse as up
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class Failures:
    def __init__(self):
        self.items = []

    def check(self, ok, label, detail=""):
        if not ok:
            self.items.append((label, detail))
        return ok


class HeadParser(HTMLParser):
    """Extracts just the head signals we assert on."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self.canonicals = []
        self.robots = []
        self.descriptions = []
        self.viewport = None
        self.og_titles = []
        self.og_images = []
        self.alt_feeds = []
        self.jsonld = []
        self.h1_count = 0
        self._in_h1 = False
        self._in_jsonld = False
        self._buf = []
        self.links = []
        self.imgs_without_alt = 0
        self.lang = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self._in_title, self._buf = True, []
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta":
            name = a.get("name", "").lower()
            prop = a.get("property", "").lower()
            if name == "description":
                self.descriptions.append(a.get("content", ""))
            elif name == "robots":
                self.robots.append(a.get("content", ""))
            elif name == "viewport":
                self.viewport = a.get("content", "")
            elif prop == "og:title":
                self.og_titles.append(a.get("content", ""))
            elif prop == "og:image":
                self.og_images.append(a.get("content", ""))
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if rel == "canonical":
                self.canonicals.append(a.get("href", ""))
            elif "alternate" in rel and "xml" in a.get("type", ""):
                self.alt_feeds.append(a)
        elif tag == "script":
            if a.get("type", "").lower() == "application/ld+json":
                self._in_jsonld, self._buf = True, []
        elif tag == "a" and "href" in a:
            self.links.append(a["href"])
        elif tag == "img" and "alt" not in a:
            self.imgs_without_alt += 1

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self.title = "".join(self._buf).strip()
            self._in_title = False
        elif tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._buf))
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_title or self._in_jsonld:
            self._buf.append(data)


def walk_html(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".html"):
                yield os.path.join(dirpath, fn)


def url_of(root, path):
    """Map a built file to the URL a crawler would use for it."""
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    if rel == "index.html":
        return "/"
    # Strip only "index.html" so that "about/index.html" becomes "/about/"
    # rather than "/about".
    if rel.endswith("index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def to_disk(root, url_path):
    """Map a URL path to the file that serves it inside the build directory.

    URL paths are percent-encoded (`%C3%B6`), file names on disk are not.
    """
    decoded = up.unquote(url_path)
    local = os.path.join(root, decoded.lstrip("/"))
    if decoded.endswith("/"):
        local = os.path.join(local, "index.html")
    return local


# The tag/category *index* pages are deliberate navigation hubs and stay
# indexable; only the per-post tag archive pages are excluded.
TAXONOMY_INDEXES = ("/tags/", "/categories/")


def kind(u):
    p = up.urlsplit(u).path
    if p in TAXONOMY_INDEXES:
        return "taxonomy_index"
    if p.startswith("/posts/"):
        return "post"
    if p.startswith("/tags/"):
        return "tag"
    if p.startswith("/categories/"):
        return "category"
    if re.fullmatch(r"/page\d+/?", p):
        return "pagination"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", default="_site")
    ap.add_argument("--base-url", default=None,
                    help="expected canonical origin, e.g. https://example.com")
    a = ap.parse_args()
    root = a.site
    F = Failures()

    if not os.path.isdir(root):
        print(f"ERROR: build directory {root!r} does not exist; build the site first")
        return 1

    # ---------------------------------------------------------------- sitemap
    sm_path = os.path.join(root, "sitemap.xml")
    if not F.check(os.path.exists(sm_path), "sitemap.xml exists"):
        print("FATAL: no sitemap.xml"); return 1

    sm_raw = open(sm_path, encoding="utf-8").read()
    try:
        sm = ET.fromstring(sm_raw)
    except ET.ParseError as e:
        F.check(False, "sitemap.xml is well-formed XML", str(e))
        print("FATAL: sitemap.xml does not parse"); return 1

    locs = [html.unescape(e.text or "") for e in sm.iter(f"{SITEMAP_NS}loc")]
    F.check(bool(locs), "sitemap.xml has at least one <loc>")
    F.check(len(locs) == len(set(locs)), "sitemap.xml has no duplicate URLs",
            str([u for u, n in collections.Counter(locs).items() if n > 1]))

    base = a.base_url
    if base:
        wrong = [u for u in locs if not u.startswith(base)]
        F.check(not wrong, f"every sitemap URL is on the canonical origin {base}",
                str(wrong[:5]))

    for u in locs:
        F.check(u == u.strip(), "sitemap URL has no surrounding whitespace", u)
        F.check(" " not in u, "sitemap URL is percent-encoded (no raw spaces)", u)
        F.check(up.urlsplit(u).scheme == "https", "sitemap URL is https", u)
        k = kind(u)
        F.check(k != "tag", "sitemap contains no thin tag archive page", u)
        F.check(k != "pagination", "sitemap contains no paginated listing", u)
        F.check(u.rstrip("/").rsplit("/", 1)[-1] not in ("404.html",),
                "sitemap does not advertise the 404 document", u)
        F.check("/robots.txt" not in u, "sitemap does not advertise robots.txt", u)
        F.check("/feed.xml" not in u, "sitemap does not advertise the feed", u)
        F.check("/assets/" not in u, "sitemap does not advertise assets", u)
        F.check("google-site-verification" not in u and "google18a" not in u,
                "sitemap does not advertise the site-verification file", u)

    # every sitemap URL must resolve to a real file in the build
    for u in locs:
        local = to_disk(root, up.urlsplit(u).path)
        F.check(os.path.exists(local), "sitemap URL exists in the build", u)

    # ----------------------------------------------------------- page signals
    pages = {}
    skipped = []
    for path in walk_html(root):
        u = url_of(root, path)
        raw = open(path, encoding="utf-8", errors="replace").read()
        if "<html" not in raw.lower():
            # e.g. the Google site-verification file, which is a bare text
            # fragment with an .html extension and no document structure.
            skipped.append(u)
            continue
        parser = HeadParser()
        try:
            parser.feed(raw)
        except Exception as e:  # noqa: BLE001
            F.check(False, "HTML parses", f"{u}: {e}")
            continue
        pages[u] = parser

    post_urls = {u for u in pages if kind(u) == "post"}
    F.check(bool(post_urls), "site has posts")

    # every post must be in the sitemap
    in_sm = {up.unquote(up.urlsplit(u).path) for u in locs}
    missing = sorted(p for p in post_urls if p not in in_sm)
    F.check(not missing, "every post appears in sitemap.xml", str(missing[:5]))

    # ------------------------------------------------------- index directives
    for u, p in sorted(pages.items()):
        k = kind(u)
        robots = " ".join(p.robots).lower()
        noindex = "noindex" in robots
        if k == "post":
            F.check(not noindex, "post is not accidentally noindex", u)
            F.check(p.h1_count >= 1, "post has an <h1>", u)
        elif k == "category":
            F.check(not noindex, "category page is not accidentally noindex", u)
        elif k == "other" and u in in_sm:
            F.check(not noindex, "sitemap URL is not noindex", u)
        if k == "tag":
            F.check(noindex, "thin tag archive page is noindex", u)
            F.check("follow" in robots or not robots,
                    "noindexed tag page still allows following links", u)

    # the 404 document must not be indexable
    if "/404.html" in pages:
        F.check("noindex" in " ".join(pages["/404.html"].robots).lower(),
                "404 document is noindex")

    # -------------------------------------------------------------- canonicals
    if base:
        for u, p in sorted(pages.items()):
            if not p.canonicals:
                continue
            F.check(len(p.canonicals) == 1, "exactly one canonical link", u)
            c = p.canonicals[0]
            F.check(c.startswith(base), "canonical is on the canonical origin", f"{u} -> {c}")
            # Compare decoded paths: the canonical is percent-encoded while the
            # on-disk path is not.
            F.check(up.unquote(up.urlsplit(c).path) == u,
                    "canonical points at the page itself", f"{u} -> {c}")

    # ------------------------------------------------- unique titles/descriptions
    #
    # Scoped to *generated* pages. Posts are excluded on purpose: this author
    # publishes one write-up per challenge per year, so "Holiday Hack
    # Orientation" legitimately titles three different posts. Rewriting those
    # would be editing content to satisfy a metric, which is not a technical
    # fix. Collisions among posts are reported as information instead.
    generated = [u for u, p in pages.items() if kind(u) in ("category", "taxonomy_index", "other")]
    for label, getter in (("title", lambda p: p.title),
                          ("description", lambda p: (p.descriptions or [""])[0])):
        groups = collections.defaultdict(list)
        for u in generated:
            v = (getter(pages[u]) or "").strip()
            if v:
                groups[v].append(u)
        dups = {v: us for v, us in groups.items() if len(us) > 1}
        F.check(not dups, f"no duplicate <{label}> among generated pages",
                json.dumps({v: us[:4] for v, us in list(dups.items())[:5]}, indent=1))

    # the placeholder site description must not be spread across indexable pages
    generic = []
    for u, p in pages.items():
        d = (p.descriptions or [""])[0].strip()
        if d.lower() not in ("yet another blog", "thedead91"):
            continue
        if any("noindex" in r.lower() for r in p.robots):
            continue  # noindexed, so the description is never evaluated
        generic.append((u, d))
    F.check(not generic, "no indexable page carries the placeholder site description",
            str([u for u, _ in generic][:8]))

    # ------------------------------------------------------------- head basics
    for u, p in sorted(pages.items()):
        if p.viewport:
            F.check("user-scalable=no" not in p.viewport.replace(" ", ""),
                    "viewport does not disable pinch-zoom", f"{u}: {p.viewport}")
        F.check(bool(p.alt_feeds), "page advertises its feed (link rel=alternate)", u)
        F.check(bool(p.og_images), "page has an og:image", u)
        F.check(bool(p.lang), "document declares a lang attribute", u)

    # --------------------------------------------------------- structured data
    for u, p in sorted(pages.items()):
        for block in p.jsonld:
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                F.check(False, "JSON-LD block is valid JSON", f"{u}: {e}")

    post_types = {}
    for u, p in pages.items():
        if kind(u) != "post":
            continue
        types = set()
        for block in p.jsonld:
            try:
                d = json.loads(block)
            except json.JSONDecodeError:
                continue
            for item in (d if isinstance(d, list) else [d]):
                if isinstance(item, dict) and "@type" in item:
                    types.add(str(item["@type"]))
        post_types[u] = types
    missing_ld = sorted(u for u, t in post_types.items() if "BlogPosting" not in t)
    F.check(not missing_ld, "every post carries BlogPosting structured data",
            str(missing_ld[:5]))

    # ------------------------------------------------------------ internal links
    for u, p in sorted(pages.items()):
        for href in p.links:
            if href.startswith(("http://", "https://", "mailto:", "javascript:", "#")):
                if href.startswith("http") and base and up.urlsplit(href).netloc == up.urlsplit(base).netloc:
                    path = up.urlsplit(href).path or "/"
                    if path == u:
                        continue
                    F.check(os.path.exists(to_disk(root, path)),
                            "absolute internal link resolves", f"{u} -> {href}")
                continue
            if href.startswith("/"):
                path = href.split("#")[0].split("?")[0] or "/"
                F.check(os.path.exists(to_disk(root, path)) or os.path.isdir(to_disk(root, path)),
                        "internal link resolves", f"{u} -> {href}")

    # ----------------------------------------------------------------- robots
    rb = os.path.join(root, "robots.txt")
    if F.check(os.path.exists(rb), "robots.txt exists"):
        txt = open(rb, encoding="utf-8").read()
        F.check("Sitemap:" in txt, "robots.txt declares a Sitemap")
        sm_dirs = re.findall(r"^Disallow:\s*(\S*)", txt, re.M | re.I)
        for d in sm_dirs:
            F.check(d in ("", "/norobots/"),
                    "robots.txt does not block content or the posts", d)
        F.check("norobots" not in txt or "norobots/" in txt,
                "robots.txt does not reference a non-existent directory")

    # ------------------------------------------- document structure / markdown
    # A fenced code block that kramdown fails to recognise is emitted as literal
    # "```" prose, and any raw markup inside it then leaks into <body>. That
    # produced a second <html><head><title> on /posts/2024-09-PowerShell/.
    for path in walk_html(root):
        raw = open(path, encoding="utf-8", errors="replace").read()
        if "<html" not in raw.lower():
            continue
        u = url_of(root, path)
        bm = re.search(r"<body[^>]*>", raw, re.I)
        if not bm:
            F.check(False, "document has a <body>", u)
            continue
        # slice *after* the opening <body> tag, otherwise the check counts the
        # document's own body element
        body = raw[bm.end():]
        for m in re.finditer(r"```", body):
            if m.start() > 0 and body[m.start() - 1] == "`":
                continue  # part of the same run
            inside_pre = body.rfind("<pre", 0, m.start()) > body.rfind("</pre>", 0, m.start())
            if inside_pre:
                continue  # legitimate: the post is showing ``` as content
            F.check(False, "no unrendered code fence leaks into the body text", u)
            break
        for tag in ("html", "head", "body"):
            n = len(re.findall(rf"<{tag}[\s>]", body, re.I))
            F.check(n == 0, f"no stray <{tag}> element inside <body>", f"{u} ({n})")
        # `</head>` and `</body>` are optional end tags in HTML5 and the theme's
        # compress_html strips them; only a *duplicate opening* tag is a defect,
        # which the check above covers.

    # ------------------------------------------------------------------ report
    # Information only: identical titles/descriptions across *posts* are a
    # content choice (one write-up per challenge per year), not a technical
    # defect, and are deliberately not "fixed".
    post_dup_titles = collections.defaultdict(list)
    for u in sorted(post_urls):
        t = (pages[u].title or "").strip()
        if t:
            post_dup_titles[t].append(u)
    repeated = {t: us for t, us in post_dup_titles.items() if len(us) > 1}
    if repeated:
        print("INFO  repeated post titles (content, not a technical defect):")
        for t, us in list(repeated.items())[:10]:
            print(f"        {len(us)}x {t!r}")
    if skipped:
        print(f"INFO  non-document .html files skipped: {skipped}")

    if F.items:
        print(f"FAILED {len(F.items)} check(s):\n")
        for label, detail in F.items:
            print(f"  x {label}")
            if detail:
                for line in str(detail).splitlines()[:12]:
                    print(f"      {line}")
        return 1

    print(f"OK  all checks passed")
    print(f"    build dir            {root}")
    print(f"    html documents       {len(pages)}")
    print(f"    sitemap URLs         {len(locs)}")
    print(f"      posts              {sum(1 for u in locs if kind(u) == 'post')}")
    print(f"      categories         {sum(1 for u in locs if kind(u) == 'category')}")
    print(f"      other              {sum(1 for u in locs if kind(u) == 'other')}")
    print(f"    noindex pages        {sum(1 for p in pages.values() if any('noindex' in r.lower() for r in p.robots))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
