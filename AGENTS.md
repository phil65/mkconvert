# AGENTS.md

## Overview

`mkconvert` is one API over many Markdown -> HTML parsers (Rust: comrak, pyromark,
markdown-it-pyrs (deprecated); C: cmarkgfm; Python: mistune, markdown-it-py, marko, markdown2,
Python-Markdown) and two
HTML -> Markdown converters (htmd, markdownify). A common, typed option model maps onto every
backend; each backend adds its own keyword-only options. Every backend is an optional extra.

## Architecture

- `src/mkconvert/__init__.py`: public API re-exports. Must stay importable with **no extras
  installed**: backends import their library inside `__init__`/`convert`.
- `src/mkconvert/_core.py`: `Options` (frozen pydantic base; `changed()` = non-default fields),
  `Backend[O]` ABC (`name`, `requires`, `extra`, `supported_options`, `is_available()`,
  `unsupported()`, option check with `on_unsupported` = warn/raise/ignore), `Registry`, errors
  (`MissingDependencyError`, `UnsupportedOptionError`, `UnsupportedOptionWarning`).
- `src/mkconvert/parsers/base.py`: `MarkdownOptions` (defaults = plain CommonMark, raw HTML on)
  and `MarkdownParser` (`convert()` strips front matter generically, then calls `_render()`).
- `src/mkconvert/parsers/<backend>.py`: one `MarkdownParser` subclass per backend. It maps the
  common options onto the library once in `__init__`; `supported_options` lists the common
  options it can set to a non-default value. `parsers/__init__.py` holds the registry; its
  order is the preference when no parser is named.
- `src/mkconvert/converters/`: same pattern for HTML -> Markdown (`HtmlToMarkdownOptions`,
  `HtmlToMarkdownConverter`, `htmd.py`, `markdownify.py`).
- `src/mkconvert/api.py`: `to_html`, `to_markdown`, `get_parser`, `get_converter`,
  `get_*_class`, `list_*`, `register_*`.
- `src/mkconvert/utils.py`: `split_front_matter`, `extract_title` (stdlib `HTMLParser`),
  `sanitize` (nh3).
- `benchmark/bench.py` + `benchmark/cases/*.txt`: parser speed comparison (not shipped).
- `benchmark/bench_parsers.py`: speed + fidelity per Markdown dialect on a documentation
  corpus (mknodes manual per flavour) and synthetic stress docs; results in `docs/parsers.md`.

## Where to look

| Task | Location |
|------|----------|
| Add a Markdown backend | new `src/mkconvert/parsers/<name>.py`, register in `parsers/__init__.py`, export in `__init__.py`, add an extra in `pyproject.toml`, README table |
| Add a common option | field on `MarkdownOptions`, map it in every parser that can, add to their `supported_options`, add a case to `tests/test_parsers.py::CASES` |
| HTML -> Markdown | `src/mkconvert/converters/` |
| Tests | `tests/` (`conftest.py` parametrizes over all registered backends, skipping missing ones) |
| CI | `.github/workflows/build.yml`, `.github/workflows/documentation.yml` |

## Commands

```bash
uv sync --all-extras                 # setup
uv run pytest                        # tests
uv run ruff check . && uv run ruff format --check .
uv run ty check                      # type check (src only); warnings fail too
uv run deptry src                    # undeclared / unused dependencies
uv run mkdocs-mknodes build          # docs (README is the index page)
uvx duty lint                        # ruff fix + format + ty (tasks in duties.py)
uv build
```

CI (`build.yml`) runs ruff, ty and pytest on Python 3.14, 3.15 and 3.16 (3.16 is `continue-on-error`)
across Linux/macOS/Windows with `uv sync --all-extras --no-group docs`.

## Conventions

- `from __future__ import annotations` everywhere; ruff line length 100, Google docstrings.
- Optional libraries are imported inside methods, never at module level of anything imported by
  `mkconvert/__init__.py`. Availability flags use `importlib.util.find_spec(...)`.
- Tests for optional backends must skip (fixtures in `conftest.py` or `pytest.importorskip`).
- Typing via ty; use targeted `# ty: ignore[rule]` only for stub-less compiled modules (htmd)
  or stubs that miss members (markdownify).

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `copier-phil65`). Don't hand-edit
  template-owned files/sections; add dependencies below the `# Only add below (Copier)` markers.
  ruff/ty versions are pinned in the `lint` group by the template, don't bump them here.
- `markdown_it_pyrs` is deprecated (remove in 3.0): 0.4.0 is unmaintained, has wheels only up
  to cp312 and segfaults when built for 3.14+, so its extra is limited to
  `python_version < '3.14'` (ty is told via `[tool.ty.analysis] allowed-unresolved-imports`).
  The parser warns (`DeprecationWarning`) and comes last in the registry.
- comrak >= 0.0.16 and pyromark >= 0.10.6 have wheels for 3.14 and 3.15 (incl. free-threaded).
- markdown-it-py needs >= 4.1 (built-in task lists / alerts); autolinks, footnotes, heading
  ids, math and definition lists come from mdit-py-plugins.
- `comrak>=0.0.15` is required: heading ids are set via `header_id_prefix` (string prefix).
- pyromark cannot escape raw HTML, autolink or add heading ids; markdown-it-pyrs has no
  `disable()`, so the parser starts from the `zero` preset and enables CommonMark rules.
- `schemez` is an intentionally kept (unused) dependency; deptry ignores it.
