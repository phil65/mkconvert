# mkconvert

[![PyPI License](https://img.shields.io/pypi/l/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Package status](https://img.shields.io/pypi/status/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Monthly downloads](https://img.shields.io/pypi/dm/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Distribution format](https://img.shields.io/pypi/format/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Wheel availability](https://img.shields.io/pypi/wheel/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Python version](https://img.shields.io/pypi/pyversions/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Implementation](https://img.shields.io/pypi/implementation/mkconvert.svg)](https://pypi.org/project/mkconvert/)
[![Releases](https://img.shields.io/github/downloads/phil65/mkconvert/total.svg)](https://github.com/phil65/mkconvert/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/mkconvert)](https://github.com/phil65/mkconvert/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/mkconvert)](https://github.com/phil65/mkconvert/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/mkconvert)](https://github.com/phil65/mkconvert/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/mkconvert)](https://github.com/phil65/mkconvert/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/mkconvert)](https://github.com/phil65/mkconvert/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/mkconvert)](https://github.com/phil65/mkconvert/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/mkconvert)](https://github.com/phil65/mkconvert)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/mkconvert)](https://github.com/phil65/mkconvert/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/mkconvert)](https://github.com/phil65/mkconvert/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/mkconvert)](https://github.com/phil65/mkconvert)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/mkconvert)](https://github.com/phil65/mkconvert)
[![Package status](https://codecov.io/gh/phil65/mkconvert/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/mkconvert/)
[![PyUp](https://pyup.io/repos/github/phil65/mkconvert/shield.svg)](https://pyup.io/repos/github/phil65/mkconvert/)

[Read the documentation!](https://phil65.github.io/mkconvert/)

One API for many Markdown parsers. `mkconvert` wraps Python and Rust Markdown → HTML
libraries behind a common `BaseParser` interface, adds an optional processing pipeline
(pre-processors, HTML tree processors, post-processors such as sanitizing), and offers
HTML → Markdown conversion. Every backend is an optional extra, so you only install what you use.

## Installation

```bash
pip install "mkconvert[comrak]"           # Rust-based Comrak parser
pip install "mkconvert[markdown]"         # Python-Markdown + pymdown-extensions
pip install "mkconvert[comrak,lxml,nh3]"  # pipeline with lxml tree processing and sanitizing
```

Parser extras: `comrak`, `pyromark`, `markdown_it_pyrs`, `markdown`, `markdown2`, `mistune`,
`marko`, `cmarkgfm`, `httpx2` (GitHub API parser; `httpx` is an alias).
Other extras: `lxml`, `nh3`, `bleach`, `beautifulsoup4`, `htmd-py`, `markdownify`.
`comrak`, `pyromark` and `lxml` are currently only installed on Python < 3.14.

## Quickstart

Use a backend directly:

```python
from mkconvert import ComrakParser

parser = ComrakParser(header_ids=True)
html = parser.convert("# Hello\n\n~~old~~ **new**")
print(parser.name, sorted(parser.features))
```

All parsers share the same interface (`convert()`, `name`, `features`):
`ComrakParser`, `PyroMarkParser`, `MarkdownItPyRSParser`, `PythonMarkdownParser`,
`Markdown2Parser`, `MistuneParser`, `MarkoParser`, `GithubApiParser`
and `mkconvert.parsers.cmarkgfm_parser.CMarkGfmParser`.

Build a pipeline with processors:

```python
from mkconvert import ExtractTitleETProcessor, MarkdownParser, MkDocsToGFMAdmonitionProcessor

pipeline = MarkdownParser(rust_parser="comrak")  # or "pyromark", "markdown-it-pyrs"
pipeline.pre_processors.register_processor(MkDocsToGFMAdmonitionProcessor())
title = ExtractTitleETProcessor()
pipeline.tree_processors.register_et_processor(title)

html = pipeline.convert('# Guide\n\n!!! note "Heads up"\n    Read this first.\n')
print(title.title)  # "Guide"
```

Convert HTML back to Markdown, or sanitize HTML:

```python
from mkconvert.html_to_md.factory import create_html_to_markdown
from mkconvert.sanitizers.factory import create_sanitizer

markdown = create_html_to_markdown().convert("<h1>Title</h1><p><b>bold</b></p>")
safe_html = create_sanitizer().sanitize("<p>hi<script>bad()</script></p>")
```

## Features

- Uniform `BaseParser` API over nine Markdown backends, with per-backend feature sets.
- `MarkdownParser` pipeline: pre-processors (e.g. MkDocs admonitions → GitHub alerts),
  ElementTree or lxml tree processors (e.g. title extraction), post-processors
  (`SanitizeHTMLProcessor`, `Prettify`).
- HTML → Markdown via htmd (Rust) or markdownify, with shared style options.
- HTML sanitizing via nh3 (Rust) or bleach.

## Backend feature comparison

| Feature | Python-Markdown | Markdown2 | Mistune | Comrak (Rust) | PyroMark (Rust) | Markdown-It-PyRS (Rust) |
|---------|----------------|-----------|---------|---------------|-----------------|-------------------------|
| **Core CommonMark** | ✅ | ✅ | ✅ | ✅ (100% compliant) | ✅ | ✅ (100% compliant) |
| Fenced code blocks | ✅ | ✅ (with ext) | ✅ | ✅ | ✅ | ✅ |
| **GitHub Flavored Markdown** |||||||
| Tables | ✅ (with ext) | ✅ (with ext) | ✅ (with plugin) | ✅ (with `.table`) | ✅ (optional) | ✅ (with GFM or `.table`) |
| Task lists | ✅ (with pymdownx.tasklist) | ✅ (with ext) | ✅ (with plugin) | ✅ (with `.tasklist`) | ✅ (optional) | ✅ (with `.tasklist`) |
| Strikethrough | ✅ (with pymdownx.tilde) | ✅ (with ext) | ✅ (with plugin) | ✅ (with `.strikethrough`) | ✅ (optional) | ✅ (with GFM or `.strikethrough`) |
| Autolinks | ✅ (with pymdownx.magiclink) | ❌ | ✅ (with plugin) | ✅ (with `.autolink`) | ✅ (with GFM) | ✅ (with `.autolink_ext`) |
| GFM Alerts | ❌ | ❌ | ❌ | ✅ (with `.alerts`) | ✅ (with GFM) | ❌ |
| **Extended Features** |||||||
| Footnotes | ✅ (with ext) | ✅ (with ext) | ✅ (with plugin) | ✅ (with `.footnotes`) | ✅ (optional) | ✅ (with `.footnote`) |
| Definition lists | ✅ (with ext) | ✅ (with ext) | ❌ | ✅ (with `.description_lists`) | ✅ (optional) | ✅ (with `.deflist`) |
| Admonitions | ✅ (with ext) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Math notation | ✅ (with pymdownx.arithmatex) | ❌ | ✅ (with plugin) | ✅ (with `.math_dollars`/`.math_code`) | ✅ (optional) | ❌ |
| Superscript | ✅ (with ext) | ❌ | ❌ | ✅ (with `.superscript`) | ✅ (optional) | ❌ |
| Subscript | ✅ (with ext) | ❌ | ❌ | ✅ (with `.subscript`) | ✅ (optional) | ❌ |
| Table of Contents | ✅ (with ext) | ✅ (with ext) | ❌ | ❌ | ❌ | ❌ |
| Front matter | ✅ (with ext) | ✅ (with ext) | ❌ | ✅ (with `.front_matter_delimiter`) | ✅ (optional) | ✅ (with `.front_matter`) |
| Wikilinks | ✅ (with ext) | ❌ | ❌ | ✅ (with `.wikilinks_*`) | ✅ (optional) | ❌ |
| Header IDs | ✅ (with ext) | ✅ (with ext) | ❌ | ✅ (with `.header_ids`) | ✅ (optional) | ✅ (with `.heading_anchors`) |
| Multiline blockquotes | ❌ | ❌ | ❌ | ✅ (with `.multiline_block_quotes`) | ❌ | ❌ |
| Syntax highlighting | ✅ (with ext) | ✅ (with ext) | ✅ (with plugin) | ✅ (with plugins) | ❌ | ❌ |
| Special features | Admonitions | Smart quotes | Custom renderers | Spoiler, Greentext | Definition lists | Tree structure, very fast (20x faster than Python-Markdown) |
