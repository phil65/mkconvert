# AGENTS.md

## Overview

`mkconvert` is a thin, uniform wrapper around many Markdown → HTML parsers (Python-Markdown,
Markdown2, Mistune, Marko, cmarkgfm, and the Rust-backed Comrak, PyroMark, markdown-it-pyrs,
plus GitHub's REST API) and two HTML → Markdown converters (htmd, markdownify). Every backend
is an optional extra. A pipeline class (`MarkdownParser`) adds pre-, tree- and post-processors
around a backend. Downstream users (e.g. chatly) depend on `mkconvert[comrak]` / `ComrakParser`.

## Architecture

- `src/mkconvert/__init__.py`: public API re-exports. Must stay importable with **no extras
  installed**: backends import their library lazily inside `__init__`/`convert`.
- `src/mkconvert/parsers/base_parser.py`: `BaseParser` ABC (`convert(text) -> str`, `name`,
  `features: set[str]`).
- `src/mkconvert/parsers/<backend>_parser/parser.py`: one `BaseParser` subclass per backend
  (`comrak_parser`, `pyromark_parser`, `markdown_it_pyrs_parser`, `python_markdown_parser`,
  `markdown2_parser`, `mistune_parser`, `marko_parser`, `cmarkgfm_parser`, `github_api_parser`).
  Each subpackage `__init__.py` re-exports the class.
- `src/mkconvert/parsers/parser.py`: `MarkdownParser` pipeline:
  pre-processors (markdown text) → Rust backend (`rust_parser` = `comrak` | `pyromark` |
  `markdown-it-pyrs`) → tree processors (lxml if available and registered, else ElementTree)
  → post-processors (HTML string).
- `src/mkconvert/pre_processors/`: `PreProcessor` ABC, `PreProcessorRegistry`,
  `MkDocsToGFMAdmonitionProcessor` (`!!! note` → GFM alerts).
- `src/mkconvert/tree_processors/`: `TreeProcessor[T]` generic base, `ETTreeProcessor`,
  `LXMLTreeProcessor` (raises `ImportError` on init without lxml), `ExtractTitle*Processor`,
  `TreeProcessorRegistry` (separate ET / lxml lists, sorted by priority, higher first).
- `src/mkconvert/post_processors/`: `PostProcessor` ABC, registry, `SanitizeHTMLProcessor`
  (uses `sanitizers.create_sanitizer`), `Prettify` (BeautifulSoup).
- `src/mkconvert/sanitizers/`: `HTMLSanitizer` ABC, `NH3Sanitizer`, `BleachSanitizer`,
  `create_sanitizer()` picks an installed backend.
- `src/mkconvert/html_to_md/`: `BaseHtmlToMarkdown` with shared style literals (`base.py`),
  `HtmdConverter`, `MarkdownifyConverter`, `create_html_to_markdown()` / `HtmlToMarkdownFactory`.
- `src/mkconvert/extensions.py`: Python-Markdown extension config dataclasses and entry-point
  discovery (needs the `markdown` extra; not imported by the package).
- `benchmark/bench.py` + `benchmark/cases/*.txt`: parser speed comparison (not shipped).

## Where to look

| Task | Location |
|------|----------|
| Add a Markdown backend | new `src/mkconvert/parsers/<name>_parser/`, export in `src/mkconvert/__init__.py`, add an extra in `pyproject.toml` |
| Change Comrak options | `src/mkconvert/parsers/comrak_parser/parser.py` |
| Pipeline / processor ordering | `src/mkconvert/parsers/parser.py`, `*/registry.py` |
| HTML sanitizing | `src/mkconvert/sanitizers/`, `src/mkconvert/post_processors/sanitizer.py` |
| HTML → Markdown | `src/mkconvert/html_to_md/` |
| Tests | `tests/` |
| CI | `.github/workflows/build.yml`, `.github/workflows/documentation.yml` |

## Commands

```bash
uv sync --all-extras                 # setup (Python 3.13: all extras resolve)
uv run pytest                        # tests
uv run ruff check . && uv run ruff format --check .
uv run ty check                      # type check (src only); warnings fail too
uv run deptry src                    # undeclared / unused dependencies
uv run mkdocs-mknodes build          # docs (README is the index page)
uvx duty lint                        # ruff fix + format + ty (tasks in duties.py)
uv build
```

CI (`build.yml`) runs ruff, ty and pytest on Python 3.13 and 3.14 (3.14 is `continue-on-error`)
across Linux/macOS/Windows with `uv sync --all-extras --no-group docs`.

## Conventions

- `from __future__ import annotations` everywhere; ruff line length 100, Google docstrings.
- Optional libraries are imported inside methods, never at module level of anything imported by
  `mkconvert/__init__.py`. Availability flags use `importlib.util.find_spec(...)`.
- Tests for optional backends must `pytest.importorskip(...)`, not fail.
- Typing via ty; use targeted `# ty: ignore[rule]` only for stub-less compiled modules (htmd).
  `types-lxml` in the lint group provides lxml stubs.

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `copier-phil65`). Don't hand-edit
  template-owned files/sections; add dependencies below the `# Only add below (Copier)` markers.
  ruff/ty versions are pinned in the `lint` group by the template, don't bump them here.
- `comrak`, `lxml` and `pyromark` extras are limited to `python_version < '3.14'`; on 3.14 they
  are absent (ty is told via `[tool.ty.analysis] allowed-unresolved-imports`).
- `comrak>=0.0.15` is required: `list_style` takes `comrak.ListStyle`, and heading ids are set
  via `header_id_prefix` (string prefix).
- `GithubApiParser` performs a network call to `api.github.com` (needs the `httpx2` extra; `httpx` is an alias).
- `schemez` is an intentionally kept (unused) dependency; deptry ignores it.
