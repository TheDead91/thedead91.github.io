# frozen_string_literal: true

# Central crawl/index policy for the site.
#
# Every decision here is driven by evidence from the indexing audit recorded in
# docs/audit/ROOT_CAUSE.md and docs/audit/URL_MATRIX.csv:
#
#   * The auto-generated sitemap listed 203 URLs. 106 were per-post tag archive
#     pages; 105 of those 106 rendered fewer than 1200 characters of text
#     (median 59 characters) and each reused the exact <title> of the single
#     post it listed, because the tags are named after post titles. Another 7
#     were paginated listings that shared the homepage's title, meta
#     description and self-canonical. 136 pages in total carried the identical
#     meta description "Yet another blog".
#   * Search Console reported the homepage as "Crawled - currently not indexed"
#     and every one of the 73 posts as "URL is unknown to Google", so the goal
#     is an unambiguous indexable set, not a larger one.
#
# Policy:
#
#   per-post tag pages    -> noindex, follow, unique title + description.
#                            Still crawlable, because following their links is
#                            how the posts stay reachable.
#   category pages        -> indexable, unique title + description.
#   /tags/, /categories/  -> indexable navigation hubs, unique descriptions.
#   paginated listings    -> indexable (they are the only crawl path to the
#                            older posts) with unique titles, but excluded from
#                            the sitemap.
#   /404.html, /robots.txt-> the theme's copies are dropped so the repository
#                            versions are the only writers. Jekyll otherwise
#                            reports a destination conflict and writes an
#                            empty file.
#   compiled CSS/JS, the web manifest, the feed -> not indexable documents.
#
# This generator is the single source of truth for the indexable URL set. It
# publishes that set to `site.data["seo_sitemap"]`, and sitemap.xml does nothing
# but format it, so the sitemap and the on-page index directives cannot drift
# apart. tools/seo_check.py asserts the rendered result.
#
# `page.title` is set rather than a separate override so that <title>, og:title
# and the visible <h1> can never disagree.
#
# Priority is :lowest so this runs after jekyll-archives (:normal) and
# jekyll-paginate (:lowest) have created their pages; jekyll-paginate stores its
# Pager on Page#pager. generate() warns loudly if that stops being true, and
# tools/seo_check.py asserts the built HTML, so a plugin upgrade cannot silently
# regress the policy.

module Jekyll
  module SiteIndexingPolicy
    # Pages whose on-page copy is owned by this repository rather than the theme.
    OWNED_PATHS = ["/robots.txt", "/404.html"].freeze

    # Generated documents that must never be advertised as indexable pages.
    NON_INDEXABLE = ["/404.html", "/robots.txt", "/feed.xml"].freeze

    # Tab pages that are pure navigation indexes of generated archives.
    INDEX_PAGES = {
      "/tags/" => "Every tag used across the SANS Holiday Hack Challenge " \
                  "write-ups on this site.",
      "/categories/" => "All SANS Holiday Hack Challenge write-ups on this " \
                        "site, grouped by year and by act of the challenge.",
      "/archives/" => "Every SANS Holiday Hack Challenge write-up on this " \
                      "site in reverse chronological order, by year."
    }.freeze

    class Generator < ::Jekyll::Generator
      safe true
      priority :lowest

      def generate(site)
        drop_theme_owned_pages(site)

        # 1. defaults first, so the specific policies below can only narrow them
        apply_defaults(site)

        tag_pages = site.pages.select { |p| p.url.start_with?("/tags/") }
        pagination = site.pages.select { |p| p.respond_to?(:pager) && p.pager }

        if tag_pages.empty?
          Jekyll.logger.warn("IndexingPolicy:",
                             "no tag archive pages found; taxonomy titles not set")
        end
        if pagination.empty? && site.config["paginate"].to_i.positive?
          Jekyll.logger.warn("IndexingPolicy:",
                             "no paginated pages found; pagination titles not set")
        end

        # 2. then the specific policies
        tag_pages.each { |page| apply_tag_policy(site, page) }
        pagination.each { |page| apply_pagination_policy(site, page) }
        each_document(site) { |doc| apply_named_page_policy(doc) }

        # 3. finally publish the indexable set for sitemap.xml
        publish_sitemap_entries(site)
      end

      private

      def drop_theme_owned_pages(site)
        site.pages.reject! do |page|
          next false unless OWNED_PATHS.include?(page.url)

          source =
            begin
              page.relative_path.to_s
            rescue StandardError
              ""
            end
          # Only remove the copy inherited from the theme gem.
          if source.start_with?("assets/")
            Jekyll.logger.info("IndexingPolicy:", "dropped theme page #{page.url}")
            true
          else
            false
          end
        end
      end

      # Indexable by default; every exclusion is explicit and reasoned.
      def apply_defaults(site)
        site.posts.docs.each { |post| post.data["seo_indexable"] = true }

        each_document(site) do |doc|
          doc.data["seo_indexable"] = true
          doc.data["seo_indexable"] = false if NON_INDEXABLE.include?(doc.url)
          # Compiled assets, the web manifest and the feed are Jekyll pages but
          # are not indexable documents.
          doc.data["seo_indexable"] = false unless doc.output_ext == ".html"
        end
      end

      # A per-post tag page is a navigation surface, not an independent document.
      #
      # jekyll-archives::Archive exposes `title` and `posts` as Ruby readers and
      # hides them behind a PageDrop in Liquid, so `page.data["title"]` is
      # shadowed and cannot be used to rename the page. The <title> is therefore
      # rewritten from `seo_title` in the post_render pass below, while the
      # description and the index directive - which the metadata hook reads from
      # page data - are set directly.
      def apply_tag_policy(site, page)
        name = archive_name(page)
        count = page.posts&.size
        site_title = site.config["title"].to_s

        page.data["seo_indexable"] = false # keep out of the sitemap
        page.data["seo_noindex"] = true    # keep out of the index
        page.data["seo_title"] = "Tag: #{name} | #{site_title}"
        page.data["seo_og_title"] = "Tag: #{name}"
        page.data["description"] =
          if count
            "All #{count} write-up#{"s" unless count == 1} tagged #{name} in the " \
              "SANS Holiday Hack Challenge series."
          else
            "All write-ups tagged #{name} in the SANS Holiday Hack Challenge series."
          end
      end

      def apply_pagination_policy(site, page)
        pager = page.pager
        number = pager.page
        total = pager.total_pages
        oldest = pager.posts&.last&.date
        site_title = site.config["title"].to_s

        # jekyll-paginate assigns a Pager to the *first* page as well
        # (`page.pager = pager` when num_page == 1), so the site index arrives
        # here too. It is the homepage, not a paginated duplicate of itself: it
        # stays indexable, keeps the bare site title the theme renders, and gets
        # a real description instead of inheriting a generic one.
        if number == 1 || page.url == "/"
          page.data["seo_indexable"] = true
          page.data["seo_noindex"] = false
          page.data["description"] =
            "Write-ups and solutions for the SANS Holiday Hack Challenge, " \
            "covering web, network, cloud, mobile and hardware challenges."
          return
        end

        # Paginated listings carry unique post sets, so they stay indexable -
        # they are the only crawl path to the older posts. They are kept out of
        # the sitemap because a sitemap is not the right way to advertise a
        # sequence of duplicates of the index.
        page.data["seo_indexable"] = false
        page.data["seo_noindex"] = false
        # The theme's <head> omits the page title whenever `page.layout` is
        # "home", and jekyll-paginate clones index.html, so every /pageN/ was
        # emitted as a byte-identical `<title>TheDead91</title>` with a
        # self-referencing canonical. seo_title fixes that in post_render.
        page.data["seo_title"] = "Page #{number} of #{total} | #{site_title}"
        page.data["seo_og_title"] = "Page #{number} of #{total}"
        page.data["description"] =
          "Page #{number} of #{total} of the #{site_title} archive: older SANS " \
          "Holiday Hack Challenge write-ups" \
          "#{oldest ? " down to #{oldest.strftime('%B %Y')}" : ""}."
      end

      def apply_named_page_policy(doc)
        desc = INDEX_PAGES[doc.url]
        doc.data["description"] = desc if desc

        return unless doc.url.start_with?("/categories/")
        return unless doc.respond_to?(:posts)

        posts = doc.posts
        return if posts.nil? || posts.empty?

        # A category archive has no date of its own, so its lastmod is the most
        # recent post it lists. jekyll-archives hands them over newest first.
        doc.data["seo_lastmod"] = posts.first.date
        # Without this, every category page inherited the site-wide
        # "Yet another blog" description.
        name = archive_name(doc)
        count = posts.size
        doc.data["description"] =
          "All #{count} write-up#{"s" unless count == 1} in #{name} from the " \
          "SANS Holiday Hack Challenge series."
      end

      # jekyll-archives::Archive#title is the unslugified tag/category name.
      def archive_name(page)
        if page.respond_to?(:title) && page.title.is_a?(String)
          page.title
        else
          page.data["title"].to_s
        end
      end

      # Every renderable document except posts: site pages (which include the
      # jekyll-archives tag/category pages and the jekyll-paginate listings) plus
      # the documents of every output collection (the `tabs` collection).
      def each_document(site, &block)
        site.pages.each(&block)
        site.collections.each_value do |collection|
          collection.docs.each(&block)
        end
      end

      def publish_sitemap_entries(site)
        entries = []
        seen = {}

        add = lambda do |doc, lastmod|
          next if doc.data["seo_indexable"] == false
          next if doc.data["sitemap"] == false
          next if seen.key?(doc.url)

          seen[doc.url] = true
          entries << { "url" => doc.url, "lastmod" => lastmod }
        end

        site.pages.each do |page|
          # The homepage changes on every build, so site.time is the honest
          # lastmod. Jekyll::Page has no #date, so other pages rely on whatever
          # a plugin has recorded.
          lastmod = page.url == "/" ? site.time : page.data["last_modified_at"]
          add.call(page, lastmod)
        end

        each_document(site) do |doc|
          # Jekyll::Page has no #date; only documents and posts do.
          lastmod = doc.data["seo_lastmod"] || doc.data["last_modified_at"]
          lastmod ||= doc.date if doc.respond_to?(:date)
          add.call(doc, lastmod)
        end

        site.posts.docs.each do |post|
          next if seen.key?(post.url)

          seen[post.url] = true
          entries << { "url" => post.url, "lastmod" => post.data["last_modified_at"] || post.date }
        end

        site.data["seo_sitemap"] = entries
        Jekyll.logger.info("IndexingPolicy:", "#{entries.size} indexable URLs")
      end
    end
  end
end

# ---------------------------------------------------------------------------
# Output-level fixes that cannot be expressed as page data.
#
# 1. <title> / og:title.
#
#    Two theme behaviours make page titles impossible to set through page data:
#      * the theme's <head> omits the page title whenever `page.layout` is
#        "home", and jekyll-paginate clones index.html, so all eight /pageN/
#        pages rendered a byte-identical `<title>TheDead91</title>` while
#        declaring a self-referencing canonical;
#      * jekyll-archives::Archive#title is a Ruby reader hidden behind a
#        PageDrop, so `page.data["title"]` is shadowed and a per-tag rename is
#        discarded.
#    Pages that need a distinct title therefore carry `seo_title`, and it is
#    applied here. Only pages that explicitly ask for it are touched.
#
#    This is registered for both :pages and :documents: posts are
#    Jekyll::Document instances, so a :pages-only hook silently skips all 73 of
#    them.
#
# 2. Viewport.
#
#    The theme ships
#      <meta name="viewport" content="width=device-width, user-scalable=no
#                                    initial-scale=1, shrink-to-fit=no, ...">
#    `user-scalable=no` disables pinch-to-zoom, which fails WCAG 2.1 SC 1.4.4
#    (Resize Text) and is surfaced by Google's mobile usability checks. It is a
#    theme default rather than a deliberate site decision, so it is corrected
#    here. Doing it as a post-render pass keeps the change independent of the
#    theme version, which matters because the theme is pinned via Gemfile.lock.
module SiteIndexingPolicy
  module OutputFixes
    module_function

    def apply(page)
      return unless page.output.is_a?(String)

      output = page.output

      if (title = page.data["seo_title"])
        output = output.sub(%r{<title>.*?</title>}m) { "<title>#{title}</title>" }
      end

      if (og = page.data["seo_og_title"])
        output = output.sub(
          %r{(<meta\s+property=["']og:title["']\s+content=["'])[^"']*(["'])}i
        ) { "#{Regexp.last_match(1)}#{og}#{Regexp.last_match(2)}" }
      end

      output = output.gsub(%r{(<meta\s+name=["']viewport["']\s+content=["'])([^"']*)(["'])}i) do
        prefix = Regexp.last_match(1)
        content = Regexp.last_match(2)
        suffix = Regexp.last_match(3)
        cleaned = content
                     .gsub(/\s*,\s*user-scalable\s*=\s*no/i, "")
                     .gsub(/\s*,\s*shrink-to-fit\s*=\s*no/i, "")
                     .gsub(/\buser-scalable\s*=\s*no\s*,?\s*/i, "")
                     .gsub(/\bshrink-to-fit\s*=\s*no\s*,?\s*/i, "")
        next "#{prefix}#{content}#{suffix}" if cleaned == content

        "#{prefix}#{cleaned}#{suffix}"
      end

      page.output = output
    end
  end
end

Jekyll::Hooks.register :pages, :post_render do |page|
  SiteIndexingPolicy::OutputFixes.apply(page)
end

Jekyll::Hooks.register :documents, :post_render do |doc|
  SiteIndexingPolicy::OutputFixes.apply(doc)
end
