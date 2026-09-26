# frozen_string_literal: true

source "https://rubygems.org"

# Pinned to the 7.4.x line on purpose.
#
# `~> 7.4` means ">= 7.4, < 8.0" in RubyGems, so it had been silently tracking
# new minor releases. The published site was built with 7.4.1, and 7.6.0 emits
# `<html lang="en"data-bs-theme="dark">` - a missing attribute separator -
# when combined with the `compress_html` settings in _config.yml. Pinning the
# minor line plus committing Gemfile.lock makes the build reproducible.
gem "jekyll-theme-chirpy", "~> 7.4.1"

# The theme calls `include_cached` in its default layout; it used to be loaded
# only as a transitive dependency. Declared explicitly so the Liquid tag it
# provides cannot disappear on a dependency change.
gem "jekyll-include-cache", "~> 0.2"

# Drives sitemap/canonical/index-directive generation in _plugins/seo-indexing.rb
# and the deliberate sitemap.xml template.
gem "jekyll-archives", "~> 2.2"
gem "jekyll-seo-tag", "~> 2.8"
gem "jekyll-paginate", "~> 1.1"

# Asset pipeline used by the theme for its Sass.
gem "jekyll-sass-converter", "~> 3.0"

gem "html-proofer", "~> 5.0", group: :test

platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

gem "wdm", "~> 0.2.0", :platforms => [:mingw, :x64_mingw, :mswin]
