# Parsers by dialect

Which Markdown parser renders which Markdown dialect, and how fast, measured on real
documentation: the [mknodes](https://phil65.github.io/mknodes/) manual (131 pages, 2-3 MB)
generated in each of its flavours (`github`, `mdbook`, `material`, `myst`), plus synthetic
stress documents and small chat messages. The benchmark script is
`benchmark/bench_parsers.py` in the repository (see "Reproduce" below).

## Summary

| Dialect | Best fidelity | Fast and good enough | Avoid |
|---|---|---|---|
| GitHub (GFM + alerts), mknodes `github` / `mdbook` | **comrak**, markdown-it-py (everything correct) | comrak (~6000 pages/s); pyromark is 3x faster but has no heading ids / autolinks | Python-Markdown: a raw `<details>` block swallows the Markdown inside it (538 raw code fences in the manual); cmarkgfm, mistune, Python-Markdown: no alerts |
| Material for MkDocs / Zensical, mknodes `material` | **Python-Markdown + pymdown-extensions** (the engine Zensical runs; the only one that renders tabs, `///` blocks, icons) | markdown-it-py + `admon` / `attrs` plugins (admonitions, attribute lists; no tabs, blocks, icons; 3.4x faster) | every CommonMark parser alone: admonition / tab bodies become code blocks (~500 visible block markers in the manual) |
| MyST, mknodes `myst` | none: directives need myst-parser + docutils (Sphinx) | mistune + `FencedDirective`: admonition directives (`{note}`, `{warning}`, ...) only; markdown-it-py + MyST plugins parses every directive without leaking syntax, but renders them as code blocks | treating MyST as CommonMark: 245 directives end up as code blocks |
| Chat / LLM answers (small GFM documents) | comrak, markdown-it-py | comrak: 35 µs per re-render of a 2 KB answer | markdown2 (1000x slower than pyromark), marko |

Speed in short (warm, same GFM options for every parser, Python 3.14, one core):
pyromark ≈ 300 MB/s, comrak / cmarkgfm ≈ 80-200 MB/s, mistune / markdown-it-py /
Python-Markdown ≈ 3.5-11 MB/s, marko ≈ 1.5-3 MB/s, markdown2 ≈ 0.2-0.4 MB/s. The Rust and C
parsers are 30-100x faster than the pure Python ones; Python-Markdown with the full Material
extension set is another 2.5x slower than plain Python-Markdown and needs 0.7 s to set up
(icon index).

## Availability on Python 3.14 / 3.15

| Parser | Version | Python 3.14 | Python 3.15 | Notes |
|---|---|:-:|:-:|---|
| comrak | 0.0.16 | ✓ (cp314, cp314-abi3, cp311-abi3 macOS) | ✓ (cp315-abi3, cp39-abi3) | also 3.14t / 3.15t |
| pyromark | 0.10.6 | ✓ (cp314) | ✓ (cp315) | also 3.14t / 3.15t |
| cmarkgfm | 2025.10.22 | ✓ (cp314, no macOS x86_64) | builds from the sdist (C compiler) | |
| mistune, markdown-it-py, marko, markdown2, Python-Markdown | | ✓ | ✓ | pure Python |
| markdown-it-pyrs | 0.4.0 (2024) | ✗ segfaults | ✗ segfaults | **Deprecated**, removed in mkconvert 3.0: unmaintained, wheels only up to cp312; a source build imports, but creating a parser crashes. Use comrak / pyromark (Rust) or markdown-it-py (markdown-it compatible) |

Tested on Linux x86_64 with CPython 3.14.10, 3.15.2 and their free-threaded builds: import
and a GFM render (tables, task lists, alerts, footnotes) for comrak, pyromark and cmarkgfm.

## Recommendations

### mknodes: fast HTML previews and render checks per flavour

- **`github` / `mdbook`**: comrak with `MarkdownOptions.gfm(footnotes=True,
  heading_ids=True, alerts=True)`. It renders everything these flavours produce (alerts,
  `<details>` with Markdown inside, tables with inline HTML, footnotes, heading ids, raw
  `<a id>` anchors, Iconify `<img>` icons) and renders the whole manual in ~23 ms. A render
  check can then scan the visible text for leaked syntax (`[!NOTE]`, code fences, `[^1]`) as
  the benchmark does.
- **`material`**: only Python-Markdown with the site's extension list is faithful (~2 s for
  the manual, 30 ms p95 per page). Use it for checks that must match the real site. For a
  quick "nothing is badly broken" pass, comrak plus a leak scan is 100x faster but cannot
  validate pymdown syntax.
- **`myst`**: no fast parser renders MyST; checks need Sphinx / myst-parser. markdown-it-py
  with `colon_fence`, `myst_block` and `myst_role` plugins tokenizes every directive and
  target, so it can check the nesting of directives cheaply (no HTML preview).
- The "Html" example tabs in the generated manual show unrendered dialect syntax for the
  non-Material flavours (`<p>[!WARNING]` in `github`, `<p>:::{warning}</p>` in `myst`): the
  preview HTML comes from a parser that does not know the flavour. For `github` / `mdbook`,
  comrak (or markdown-it-py) with alerts renders it correctly.

### Agent chat dock (streamed Markdown -> HTML for Qt's `QTextBrowser`)

Use **comrak**: `mkconvert.get_parser("comrak", MarkdownOptions.gfm(footnotes=True,
alerts=True, raw_html=False))`.

- Streaming means re-rendering the growing answer for every chunk. For a 2 KB answer in
  16-character chunks (115 renders) comrak needs 4 ms in total, mistune 102 ms,
  markdown-it-py 128 ms, Python-Markdown 156 ms, marko 476 ms, markdown2 1.9 s. Every parser
  but markdown2 is fast enough for short answers; for long answers (20 KB+) the pure Python
  ones cost 4-10 ms per re-render, so they need throttling and comrak does not.
- comrak supports all of GFM plus alerts, ships wheels (incl. abi3 and free-threaded) for
  3.14 and 3.15 and has no dependencies. Turn `raw_html` off: LLM output is untrusted, and
  `QTextBrowser` would otherwise display any HTML the model writes.
- `QTextBrowser` supports only a subset of HTML / CSS (no `<details>`, no form controls,
  class selectors via `setDefaultStyleSheet`), so post-processing the HTML matters more than
  the parser: style `.markdown-alert-*`, `pre`, `table`; task list checkboxes need a
  replacement (e.g. ☐ / ☑).
- **markdown-it-py** is the pick if a pure Python dependency is required or the dock wants
  to work on the token stream (custom renderer emitting Qt-friendly HTML, render only the
  last block while streaming). It renders every common option correctly.
- **mistune** is the fastest pure Python parser here, but has no GitHub alerts and its
  autolinks skip `www.` URLs.

## How the benchmark works

- **Corpus**: `mknodes generate --engine markdown --flavor <flavour>` (mknodes 4.3.0) for
  `github`, `mdbook`, `material` and `myst`; `mdbook` without mdbook-admonish is the same
  Markdown as `github`. Stress documents: a 2000-row table, deep list / quote nesting,
  400 sections of inline markup, 800 code blocks, pathological emphasis and brackets, 500
  footnotes. Chat: 200 small answers (lists, code, a table, an alert).
- **Speed**: each parser runs with the same common options (GFM, footnotes, heading ids,
  alerts; options a parser lacks are ignored, which favours pyromark: no heading ids, no
  autolinks). One warm-up pass, then the best of 5 passes; per page the best of the 5 runs
  for p95 / max. Setup = import + creating the parser in a fresh interpreter. Streaming =
  re-rendering a 2 KB answer every 16 characters.
- **Configurations**: `<parser>` is the common options only; `<parser>+<dialect>` adds the
  parser's own extensions for the dialect: Python-Markdown with admonition, attr_list,
  md_in_html, pymdownx details / superfences / tabbed / blocks / emoji (mknodes' icon index);
  markdown-it-py with mdit-py-plugins `admon` + `attrs` (Material) or `colon_fence` +
  `myst_block` + `myst_role` (MyST); mistune with `FencedDirective([Admonition()])` (MyST).
- **Fidelity**: per flavour, each construct as mknodes writes it is rendered and checked
  with structural assertions on the HTML: ✓ rendered correctly, ~ degraded (content renders
  as normal Markdown but the wrapper's meaning is lost, e.g. an alert as a plain quote
  starting with `[!NOTE]`, a code block without its language or title), ✗ broken (raw
  syntax visible, or the content ends up in a code block). In addition the whole rendered
  corpus is scanned for syntax a reader would see outside code (block markers, attribute
  lists, icon shortcodes, directive fences and options, ...).
- Spot checks of rendered pages in a browser confirmed the matrix (e.g. Python-Markdown
  showing a whole `github` page as run-on raw text inside `<details>`, CommonMark parsers
  showing Material tabs as `=== "Examples"` followed by code blocks).

Other findings:

- markdown2 is pathologically slow on large pages: 4.3 s for one 856 KB changelog page.
- marko does not support footnote definitions whose text starts on the next line
  (`[^1]:` + indented text); they stay visible.
- mistune renders unknown fenced directives (`{admonition}`, `{dropdown}`, `{tab-set}`) as
  error blocks.

### Reproduce

```bash
uv sync --all-extras
# corpus from a mknodes checkout:
mknodes generate --engine markdown --flavor github --generated-dir /tmp/corpus/github
# ... same for mdbook, material, myst
uv run python -m benchmark.bench_parsers --corpus /tmp/corpus --markdown results.md
```

## Results

Python 3.14.10, Linux x86_64 (AMD Ryzen 7 PRO 7840U), comrak 0.0.16, pyromark 0.10.6,
cmarkgfm 2025.10.22, mistune 3.4.0, markdown-it-py 4.3.0 + mdit-py-plugins 0.7.0,
marko 2.2.5, markdown2 2.5.5, Markdown 3.11.3 + pymdown-extensions 13.1.2.

### Corpora

| Corpus | Pages | Size |
|---|---|---|
| github | 131 | 2.09 MB |
| mdbook | 131 | 2.09 MB |
| material | 131 | 2.81 MB |
| myst | 131 | 2.10 MB |
| stress | 6 | 0.49 MB |
| chat | 200 | 0.03 MB |

### Speed (pages/s; MB/s; p95 ms per page)


#### github

| Parser | Total ms | Relative | Pages/s | MB/s | p95 ms | Max ms |
|---|---|---|---|---|---|---|
| pyromark | 7.4 | 1.0x | 17675 | 282.65 | 0.12 | 2.2 |
| comrak | 23.2 | 3.1x | 5655 | 90.43 | 0.27 | 9.1 |
| cmarkgfm | 26.5 | 3.6x | 4949 | 79.14 | 0.38 | 9.0 |
| python-markdown | 386.1 | 52.1x | 339 | 5.43 | 7.02 | 77.1 |
| mistune | 406.5 | 54.8x | 322 | 5.15 | 6.38 | 135.2 |
| markdown-it-py | 426.9 | 57.6x | 307 | 4.91 | 5.42 | 138.3 |
| marko | 1398.1 | 188.6x | 94 | 1.50 | 19.40 | 446.7 |
| markdown2 | 9272.0 | 1251.0x | 14 | 0.23 | 112.74 | 4332.8 |

#### mdbook

| Parser | Total ms | Relative | Pages/s | MB/s | p95 ms | Max ms |
|---|---|---|---|---|---|---|
| pyromark | 6.3 | 1.0x | 20914 | 334.40 | 0.10 | 1.9 |
| comrak | 20.8 | 3.3x | 6310 | 100.90 | 0.29 | 7.0 |
| cmarkgfm | 24.6 | 3.9x | 5318 | 85.04 | 0.40 | 8.5 |
| python-markdown | 398.0 | 63.5x | 329 | 5.26 | 6.98 | 78.8 |
| markdown-it-py | 442.1 | 70.6x | 296 | 4.74 | 5.58 | 145.0 |
| mistune | 445.6 | 71.1x | 294 | 4.70 | 6.73 | 139.9 |
| marko | 1301.3 | 207.8x | 101 | 1.61 | 18.41 | 415.2 |
| markdown2 | 10294.5 | 1643.5x | 13 | 0.20 | 118.03 | 4690.8 |

#### material

| Parser | Total ms | Relative | Pages/s | MB/s | p95 ms | Max ms |
|---|---|---|---|---|---|---|
| pyromark | 8.5 | 1.0x | 15389 | 330.18 | 0.13 | 1.8 |
| comrak | 21.4 | 2.5x | 6134 | 131.61 | 0.25 | 4.8 |
| cmarkgfm | 21.8 | 2.6x | 6022 | 129.20 | 0.30 | 6.3 |
| markdown-it-py | 294.0 | 34.5x | 446 | 9.56 | 3.76 | 54.0 |
| mistune | 302.1 | 35.5x | 434 | 9.30 | 3.85 | 45.0 |
| markdown-it-py+material | 592.5 | 69.6x | 221 | 4.74 | 7.81 | 112.0 |
| python-markdown | 809.9 | 95.1x | 162 | 3.47 | 8.79 | 234.0 |
| marko | 880.9 | 103.5x | 149 | 3.19 | 10.59 | 155.4 |
| python-markdown+material | 2029.5 | 238.4x | 65 | 1.38 | 29.82 | 466.4 |
| markdown2 | 6625.1 | 778.3x | 20 | 0.42 | 116.10 | 1118.1 |

#### myst

| Parser | Total ms | Relative | Pages/s | MB/s | p95 ms | Max ms |
|---|---|---|---|---|---|---|
| pyromark | 3.9 | 1.0x | 33384 | 535.23 | 0.07 | 0.9 |
| comrak | 10.8 | 2.7x | 12162 | 195.00 | 0.16 | 1.9 |
| cmarkgfm | 16.5 | 4.2x | 7924 | 127.05 | 0.24 | 5.3 |
| mistune | 182.8 | 46.6x | 717 | 11.49 | 3.62 | 37.2 |
| mistune+myst | 183.0 | 46.6x | 716 | 11.48 | 3.72 | 39.5 |
| markdown-it-py | 204.0 | 52.0x | 642 | 10.30 | 3.46 | 47.2 |
| markdown-it-py+myst | 209.7 | 53.4x | 625 | 10.02 | 3.57 | 53.5 |
| python-markdown | 359.2 | 91.5x | 365 | 5.85 | 8.51 | 76.2 |
| marko | 642.4 | 163.7x | 204 | 3.27 | 13.78 | 157.6 |
| markdown2 | 10781.2 | 2747.5x | 12 | 0.19 | 123.09 | 4978.3 |

#### stress

| Parser | Total ms | Relative | Pages/s | MB/s | p95 ms | Max ms |
|---|---|---|---|---|---|---|
| pyromark | 5.7 | 1.0x | 1050 | 85.82 | 2.31 | 2.3 |
| comrak | 18.6 | 3.2x | 323 | 26.43 | 10.69 | 10.7 |
| cmarkgfm | 23.0 | 4.0x | 261 | 21.37 | 12.10 | 12.1 |
| mistune+myst | 333.0 | 58.3x | 18 | 1.47 | 148.51 | 148.5 |
| mistune | 343.1 | 60.0x | 17 | 1.43 | 166.74 | 166.7 |
| markdown-it-py | 495.9 | 86.8x | 12 | 0.99 | 233.98 | 234.0 |
| markdown-it-py+material | 637.6 | 111.6x | 9 | 0.77 | 353.04 | 353.0 |
| markdown-it-py+myst | 679.7 | 119.0x | 9 | 0.72 | 372.45 | 372.4 |
| marko | 1488.1 | 260.4x | 4 | 0.33 | 629.48 | 629.5 |
| python-markdown | 1989.7 | 348.2x | 3 | 0.25 | 1341.21 | 1341.2 |
| python-markdown+material | 2297.0 | 402.0x | 3 | 0.21 | 1310.91 | 1310.9 |
| markdown2 | 7665.0 | 1341.4x | 1 | 0.06 | 3126.93 | 3126.9 |

#### chat

| Parser | Total ms | Relative | Pages/s | MB/s | p95 ms | Max ms |
|---|---|---|---|---|---|---|
| pyromark | 0.7 | 1.0x | 304105 | 46.43 | 0.01 | 0.0 |
| comrak | 1.4 | 2.1x | 145042 | 22.14 | 0.01 | 0.0 |
| cmarkgfm | 3.1 | 4.7x | 65144 | 9.95 | 0.02 | 0.1 |
| mistune | 24.2 | 36.8x | 8265 | 1.26 | 0.28 | 0.3 |
| mistune+myst | 27.9 | 42.4x | 7178 | 1.10 | 0.31 | 0.4 |
| markdown-it-py+material | 36.7 | 55.8x | 5445 | 0.83 | 0.34 | 0.4 |
| markdown-it-py+myst | 36.9 | 56.1x | 5420 | 0.83 | 0.36 | 0.5 |
| markdown-it-py | 37.6 | 57.1x | 5323 | 0.81 | 0.36 | 0.4 |
| python-markdown | 52.7 | 80.1x | 3797 | 0.58 | 0.40 | 0.5 |
| marko | 128.7 | 195.6x | 1554 | 0.24 | 1.74 | 2.0 |
| python-markdown+material | 148.7 | 226.1x | 1345 | 0.21 | 1.66 | 2.1 |
| markdown2 | 674.0 | 1024.8x | 297 | 0.05 | 7.04 | 8.2 |

### Setup and streaming

| Parser | Import + create ms | First render ms | Streaming re-render ms |
|---|---|---|---|
| pyromark | 1 | 0.0 | 1 |
| comrak | 1 | 0.0 | 4 |
| cmarkgfm | 1 | 0.1 | 7 |
| mistune | 6 | 1.6 | 102 |
| mistune+myst | 9 | 1.9 | 112 |
| markdown-it-py | 14 | 1.2 | 128 |
| markdown-it-py+material | 65 | 4.8 | 136 |
| markdown-it-py+myst | 17 | 1.5 | 141 |
| python-markdown | 33 | 0.7 | 156 |
| python-markdown+material | 703 | 1.1 | 360 |
| marko | 8 | 1.7 | 476 |
| markdown2 | 6 | 2.0 | 1928 |

### Fidelity (✓ correct, ~ degraded, ✗ broken)


#### github

| Construct | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown |
|---|---|---|---|---|---|---|---|---|
| GitHub alerts | ✓ | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ~ |
| `<details>` with Markdown inside (collapsibles, tabs) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| task lists | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| API anchors in headings | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| icons (Iconify `<img>`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| fenced code (mermaid) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| autolinks | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ |
| table (inline HTML in cells) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| footnotes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| heading ids | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ |

Raw syntax visible in the rendered github corpus (count):

| Leak | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown |
|---|---|---|---|---|---|---|---|---|
| alert markers | 0 | 0 | 321 | 320 | 0 | 1 | 6 | 321 |
| footnote refs | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| code fences | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 538 |

#### mdbook

| Construct | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown |
|---|---|---|---|---|---|---|---|---|
| GitHub alerts | ✓ | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ~ |
| `<details>` with Markdown inside (collapsibles, tabs) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| task lists | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| API anchors in headings | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| icons (Iconify `<img>`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| fenced code (mermaid) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| autolinks | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ |
| table (inline HTML in cells) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| footnotes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| heading ids | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ |

Raw syntax visible in the rendered mdbook corpus (count):

| Leak | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown |
|---|---|---|---|---|---|---|---|---|
| alert markers | 0 | 0 | 321 | 320 | 0 | 1 | 6 | 321 |
| footnote refs | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| code fences | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 538 |

#### material

| Construct | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown | python-markdown+material | markdown-it-py+material |
|---|---|---|---|---|---|---|---|---|---|---|
| admonitions (`!!!`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| collapsible admonitions (`???`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ~ |
| content tabs (`===`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| PyMdown blocks (`///`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| fence attributes (`{.toml}`) | ~ | ~ | ~ | ~ | ~ | ~ | ✗ | ✓ | ~ | ~ |
| fence titles (`title=`) | ~ | ~ | ~ | ~ | ~ | ~ | ✗ | ~ | ✓ | ~ |
| attribute lists (`{ .md-button }`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| heading ids (`{#custom}`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Markdown in HTML (`markdown` attribute) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| icons / emoji (`:fa-brands-github:`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| table (inline HTML in cells) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| footnotes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| heading ids | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Raw syntax visible in the rendered material corpus (count):

| Leak | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown | python-markdown+material | markdown-it-py+material |
|---|---|---|---|---|---|---|---|---|---|---|
| block markers | 498 | 498 | 498 | 497 | 498 | 498 | 436 | 496 | 0 | 423 |
| attribute lists | 179 | 179 | 179 | 179 | 179 | 179 | 153 | 178 | 0 | 171 |
| icon shortcodes | 139 | 139 | 139 | 139 | 139 | 139 | 141 | 139 | 1 | 139 |
| footnote refs | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |

#### myst

| Construct | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown | markdown-it-py+myst | mistune+myst |
|---|---|---|---|---|---|---|---|---|---|---|
| admonition directives (`{note}`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| titled admonitions (`{admonition}`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| dropdowns (`{dropdown}`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| tab sets (`{tab-set}`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| code-block directives (`:caption:`) | ~ | ~ | ~ | ~ | ~ | ~ | ✗ | ✗ | ~ | ~ |
| targets (`(label)=`) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| task lists | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| table (inline HTML in cells) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| footnotes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| heading ids | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Raw syntax visible in the rendered myst corpus (count):

| Leak | comrak | pyromark | cmarkgfm | mistune | markdown-it-py | marko | markdown2 | python-markdown | markdown-it-py+myst | mistune+myst |
|---|---|---|---|---|---|---|---|---|---|---|
| directive fences | 62 | 62 | 62 | 61 | 62 | 62 | 1559 | 89 | 0 | 0 |
| directive options | 41 | 41 | 41 | 41 | 41 | 41 | 784 | 71 | 0 | 0 |
| targets | 187 | 187 | 187 | 187 | 187 | 187 | 245 | 181 | 186 | 186 |
| footnote refs | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| directives as code blocks | 245 | 245 | 245 | 245 | 245 | 245 | 0 | 0 | 291 | 5 |
| directives as error blocks | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 273 |
