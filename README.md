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

One API for many Markdown → HTML parsers (Rust and Python), with a common set of options
that maps onto every parser, parser-specific options on top, and the same pattern for
HTML → Markdown. Every backend is an optional extra: install only what you use.

## Installation

```bash
pip install "mkconvert[comrak]"            # Rust-based comrak (recommended)
pip install "mkconvert[pyromark,htmd-py]"  # pulldown-cmark parser + Rust HTML -> Markdown
```

Parser extras: `comrak`, `pyromark`, `cmarkgfm`, `mistune`, `markdown-it-py`
(markdown-it-py + mdit-py-plugins), `marko`, `markdown2`, `markdown` (Python-Markdown +
pymdown-extensions), and the deprecated `markdown_it_pyrs`.
HTML → Markdown: `htmd-py`, `markdownify`. Sanitizing: `nh3`.

| Parser | Python 3.14 | Python 3.15 | Notes |
|---|:-:|:-:|---|
| comrak (≥ 0.0.16) | ✓ wheels | ✓ abi3 wheels | also free-threaded (3.14t / 3.15t) |
| pyromark (≥ 0.10.6) | ✓ wheels | ✓ wheels | also free-threaded |
| cmarkgfm | ✓ wheels | sdist (needs a C compiler) | |
| mistune, markdown-it-py, marko, markdown2, Python-Markdown | ✓ | ✓ | pure Python |
| markdown-it-pyrs | ✗ | ✗ | **Deprecated**, removed in 3.0: unmaintained, wheels only up to 3.12, segfaults when built for 3.14+; the extra installs nothing there |

Which parser fits which Markdown dialect, and how fast they are on real documentation:
see [Parsers by dialect](https://phil65.github.io/mkconvert/parsers/).

## Quickstart

```python
import mkconvert
from mkconvert import MarkdownOptions

html = mkconvert.to_html("# Hello\n\n~~old~~ **new**", options=MarkdownOptions.gfm())

# Pick a parser, add common options and parser-specific ones:
html = mkconvert.to_html(
    "# Title\n\nx^2^",
    parser="comrak",
    options=MarkdownOptions(heading_ids=True, footnotes=True),
    superscript=True,  # comrak-specific
)

# Reuse a configured parser for many documents:
parser = mkconvert.get_parser("comrak", MarkdownOptions.gfm(math=True))
pages = [parser.convert(text) for text in ["# A", "# B"]]

# Or use the classes directly (typed, documented parameters):
from mkconvert import ComrakParser

html = ComrakParser(MarkdownOptions(tables=True), header_id_prefix="h-").convert("| a |\n|---|")
```

Without `parser=`, the first installed parser is used, in this order: comrak, pyromark,
cmarkgfm, mistune, markdown-it-py, marko, markdown2, python-markdown, markdown-it-pyrs.
`mkconvert.list_parsers(available_only=True)` lists the installed ones. A missing package
raises `MissingDependencyError` naming the extra to install.

## Common options

`MarkdownOptions()` is plain CommonMark (all extensions off, raw HTML passed through),
except that a leading `---` front matter block is dropped (`front_matter=False` renders it).
`MarkdownOptions.gfm(**changes)` turns on tables, strikethrough, autolinks and task lists.

| Option | comrak | pyromark | markdown-it-pyrs | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `tables` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `strikethrough` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `autolinks` | ✓ | – | ✓ | ✓ | ✓¹ | ✓ | ✓ | – | ✓ |
| `task_lists` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `footnotes` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `heading_ids` | ✓ | – | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| `alerts` | ✓ | ✓ | – | – | – | ✓ | ✓ | ✓ | – |
| `math` | ✓ | ✓ | – | – | ✓ | ✓ | – | – | ✓ |
| `definition_lists` | ✓ | ✓ | ✓ | – | ✓ | ✓ | – | – | ✓ |
| `hard_breaks` | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `smart_punctuation` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ |
| `raw_html=False` | ✓ | – | ✓ | ✓² | ✓ | ✓ | ✓ | ✓ | ✓ |
| `front_matter` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

¹ bare `https://` URLs only, not `www.` ² raw HTML is omitted instead of escaped.

Each option is documented on `MarkdownOptions`. A parser's `supported_options` tells what it
can do (`mkconvert.get_parser_class("pyromark").supported_options`). Setting an option the
parser can't honour warns (`UnsupportedOptionWarning`) and is ignored;
`on_unsupported="raise"` raises `UnsupportedOptionError` instead, `"ignore"` stays quiet.

`raw_html=False` keeps raw HTML out of the output, but it is no sanitizer. For untrusted input
run the result through `mkconvert.sanitize(html)` (nh3).

## Parser-specific options

Passed as keyword arguments to `to_html` / `get_parser` or the parser class:

| Parser | Options |
|---|---|
| `comrak` | `header_id_prefix`, `tagfilter`, `superscript`, `subscript`, `underline`, `spoiler`, `greentext`, `wikilinks`, `multiline_block_quotes`, `math_code`, `relaxed_autolinks`, `relaxed_tasklist_matching`, `default_info_string`, `github_pre_lang`, `full_info_string`, `sourcepos` |
| `pyromark` | `heading_attributes`, `superscript`, `subscript`, `wikilinks`, `old_footnotes`, `highlight` |
| `markdown-it-pyrs` | `xhtml`, `sourcepos`, `plugins` (deprecated parser) |
| `markdown-it-py` | `plugins` (mdit-py-plugins, e.g. `admon_plugin`), `xhtml`, `heading_levels` |
| `cmarkgfm` | `tagfilter`, `github_pre_lang`, `sourcepos` |
| `mistune` | `plugins` (names like `["abbr", "mark"]` or plugin objects such as directives) |
| `marko` | `extensions` (e.g. `["codehilite", "pangu"]`) |
| `markdown2` | `extras`, `highlight`, `html4tags` |
| `python-markdown` | `extensions`, `extension_configs`, `output_format` |

## HTML → Markdown

```python
from mkconvert import HtmlToMarkdownOptions, to_markdown

md = to_markdown("<h1>Title</h1><p><b>bold</b></p>")
md = to_markdown(
    html,
    converter="markdownify",
    options=HtmlToMarkdownOptions(heading_style="setext", skip_tags=("script", "style")),
    code_language="python",  # markdownify-specific
)
```

| Option | htmd | markdownify |
|---|:-:|:-:|
| `heading_style` (`"atx"`, `"setext"`) | ✓ | ✓ |
| `bullet_marker` (`"-"`, `"*"`) | ✓ | ✓ |
| `emphasis_marker` (`"*"`, `"_"`) | – | ✓ |
| `code_block_style` (`"fenced"`, `"indented"`) | ✓ | – |
| `code_fence` (`` "```" ``, `"~~~"`) | ✓ | – |
| `line_break` (`"spaces"`, `"backslash"`) | ✓ | ✓ |
| `link_style` (`"inline"`, `"reference"`) | ✓ | – |
| `skip_tags` | ✓ | ✓ |

Converter-specific options: htmd: `hr_style`, `link_reference_style`, `preformatted_code`,
`ul_bullet_spacing`, `ol_number_spacing`, `translation_mode`; markdownify: `bullets`,
`strip`, `convert`, `autolinks`, `default_title`, `code_language`, `code_language_callback`,
`escape_asterisks`, `escape_underscores`, `escape_misc`, `sub_symbol`, `sup_symbol`,
`table_infer_header`, `wrap`, `wrap_width`, `strip_document`.

## Helpers

- `sanitize(html, extra_attributes=None, **nh3_options)`: clean HTML with nh3, e.g.
  `sanitize(html, extra_attributes={"*": {"id", "class"}})` to keep heading ids and code classes.
- `extract_title(html)`: text of the first `<h1>`, or `None`.
- `split_front_matter(text)`: `(front_matter, body)` for a leading `---` block.

## Custom parsers

Subclass `MarkdownParser` (set `name`, `requires`, `extra`, `supported_options`, implement
`_render`) and register it with `mkconvert.register_parser`; likewise
`HtmlToMarkdownConverter` and `register_converter`.
