"""Speed and fidelity of the Markdown parsers on documentation corpora, per dialect.

The corpus is a folder with one subfolder per Markdown flavour (`github`, `material`,
`mdbook`, `myst`), e.g. the mknodes manual generated per flavour:

    mknodes generate --engine markdown --flavor <flavour> --generated-dir <corpus>/<flavour>

Synthetic stress documents (big table, deep nesting, long text, many code blocks,
pathological emphasis, small chat messages) are always added as the `stress` corpus.

Usage:

    uv run python -m benchmark.bench_parsers --corpus <corpus> [--repeat 5] [--json out.json]
    uv run python -m benchmark.bench_parsers --corpus <corpus> --markdown results.md

Each parser runs in two kinds of configuration:

- `<parser>`: the same common options everywhere (GFM + footnotes, heading ids, alerts;
  options a parser lacks are ignored). Used for the speed comparison.
- `<parser>+<dialect>`: the parser with its own extensions for a dialect (Python-Markdown
  with pymdown-extensions for Material, markdown-it-py with mdit-py-plugins, mistune with
  its fenced directives for MyST). Shows what a parser can do with the right setup.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import gc
import html as htmllib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any

from mkconvert import MarkdownOptions, get_parser, list_parsers


if TYPE_CHECKING:
    from collections.abc import Callable

    from mkconvert import MarkdownParser


FLAVOURS = ("github", "mdbook", "material", "myst")
OPTIONS = MarkdownOptions.gfm(footnotes=True, heading_ids=True, alerts=True)


# --- parser configurations ------------------------------------------------------------


def _material_extensions() -> tuple[list[str], dict[str, Any]]:
    """Python-Markdown extensions roughly matching what Material / Zensical sites use."""
    exts = [
        "admonition",
        "attr_list",
        "md_in_html",
        "pymdownx.details",
        "pymdownx.superfences",
        "pymdownx.tabbed",
        "pymdownx.blocks.admonition",
        "pymdownx.blocks.details",
        "pymdownx.blocks.html",
        "pymdownx.blocks.tab",
    ]
    configs: dict[str, Any] = {"pymdownx.tabbed": {"alternate_style": True}}
    if importlib.util.find_spec("mknodes"):  # the icon index mknodes pages use
        from mknodes.utils import icons

        exts.append("pymdownx.emoji")
        configs["pymdownx.emoji"] = {
            "emoji_index": icons.twemoji,
            "emoji_generator": icons.to_svg,
        }
    return exts, configs


def _mdit_material() -> dict[str, Any]:
    from mdit_py_plugins.admon import admon_plugin
    from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin

    return {"plugins": [admon_plugin, attrs_plugin, attrs_block_plugin]}


def _mdit_myst() -> dict[str, Any]:
    from mdit_py_plugins.colon_fence import colon_fence_plugin
    from mdit_py_plugins.myst_blocks import myst_block_plugin
    from mdit_py_plugins.myst_role import myst_role_plugin

    return {"plugins": [colon_fence_plugin, myst_block_plugin, myst_role_plugin]}


def _mistune_myst() -> dict[str, Any]:
    from mistune.directives import Admonition, FencedDirective

    return {"plugins": [FencedDirective([Admonition()], markers="`:")]}


def _pymd_material() -> dict[str, Any]:
    exts, configs = _material_extensions()
    return {"extensions": exts, "extension_configs": configs}


@dataclass(frozen=True)
class Config:
    """A parser with options and parser-specific keyword arguments."""

    name: str
    parser: str
    kwargs: Callable[[], dict[str, Any]] = dict
    dialects: tuple[str, ...] = FLAVOURS
    """Flavours this configuration is meant for."""

    def create(self) -> MarkdownParser:
        return get_parser(self.parser, OPTIONS, on_unsupported="ignore", **self.kwargs())


NATIVE_CONFIGS = [
    Config("python-markdown+material", "python-markdown", _pymd_material, ("material",)),
    Config("markdown-it-py+material", "markdown-it-py", _mdit_material, ("material",)),
    Config("markdown-it-py+myst", "markdown-it-py", _mdit_myst, ("myst",)),
    Config("mistune+myst", "mistune", _mistune_myst, ("myst",)),
]


def available_configs() -> list[Config]:
    configs = [Config(name, name) for name in list_parsers(available_only=True)]
    names = {c.name for c in configs}
    return configs + [c for c in NATIVE_CONFIGS if c.parser in names]


# --- corpora ------------------------------------------------------------------------


def load_corpus(folder: Path) -> list[tuple[str, str]]:
    """All Markdown files below `folder` as (relative path, text)."""
    return [
        (p.relative_to(folder).as_posix(), p.read_text(encoding="utf-8"))
        for p in sorted(folder.rglob("*.md"))
        if p.is_file()
    ]


def stress_corpus() -> list[tuple[str, str]]:
    """Synthetic documents that stress specific parts of a parser."""
    row = "| `cell` | **bold** text | [link](https://example.org) | 12345 |\n"
    table = "| A | B | C | D |\n|---|---|---|---|\n" + row * 2000
    nested = "".join("  " * i + f"- item {i}\n" for i in range(60))
    nested += "".join(">" * i + f" quote {i}\n" for i in range(1, 40))
    para = "Lorem *ipsum* dolor sit **amet**, `consectetur` adipiscing [elit](https://x.org). " * 8
    long_text = "\n\n".join(f"## Section {i}\n\n{para}" for i in range(400))
    code = "\n".join(f"```python\ndef f{i}(x):\n    return x * {i}\n```\n" for i in range(800))
    emphasis = "*a **b " * 4000 + "\n\n" + "[" * 3000 + "x" + "]" * 3000 + "\n"
    footnotes = "".join(f"Text[^{i}] " for i in range(500)) + "\n\n"
    footnotes += "".join(f"[^{i}]: Note {i}.\n" for i in range(500))
    return [
        ("table-2000-rows", table),
        ("nesting", nested),
        ("long-text-400-sections", long_text),
        ("code-800-blocks", code),
        ("pathological-emphasis", emphasis),
        ("footnotes-500", footnotes),
    ]


def chat_messages() -> list[str]:
    """Small chat-style messages (an LLM answer each)."""
    parts = [
        "Sure! Here is how to **sort** a list:\n\n```python\nitems.sort(key=len)\n```\n",
        "1. Open the *settings*\n2. Pick `Theme`\n3. Done\n\n> [!TIP]\n> Restart afterwards.\n",
        "| Option | Default |\n|---|---|\n| `x` | 1 |\n| `y` | 2 |\n\nSee https://example.org.\n",
        "The answer is ~~42~~ **43**, see the [docs](https://example.org/docs#a).\n",
    ]
    return [parts[i % len(parts)] * (1 + i % 3) for i in range(200)]


# --- speed --------------------------------------------------------------------------


@dataclass
class Speed:
    pages: int
    size: int
    total_ms: float
    p95_ms: float
    max_ms: float

    @property
    def pages_per_s(self) -> float:
        return self.pages / self.total_ms * 1000

    @property
    def mb_per_s(self) -> float:
        return self.size / 1e6 / (self.total_ms / 1000)


def measure(parser: MarkdownParser, docs: list[str], repeat: int) -> Speed:
    """Best-of-`repeat` total time; per page the best time over the repeats."""
    for text in docs:  # warm up
        parser.convert(text)
    best = [float("inf")] * len(docs)
    totals = []
    for _ in range(repeat):
        gc.collect()
        total = 0.0
        for i, text in enumerate(docs):
            start = time.perf_counter()
            parser.convert(text)
            elapsed = time.perf_counter() - start
            total += elapsed
            best[i] = min(best[i], elapsed)
        totals.append(total)
    per_page = sorted(t * 1000 for t in best)
    p95 = per_page[max(0, round(0.95 * len(per_page)) - 1)]
    size = sum(len(t.encode()) for t in docs)
    return Speed(len(docs), size, min(totals) * 1000, p95, per_page[-1])


STREAM_DOC = "".join(chat_messages()[:12])
"""A ~2 KB chat answer, streamed in 16 character chunks."""


def measure_stream(parser: MarkdownParser, text: str, chunk: int = 16) -> float:
    """Re-render the growing prefix of `text` every `chunk` characters (ms in total).

    This is what a chat view does when it shows a streamed answer as rendered HTML.
    """
    start = time.perf_counter()
    for end in range(chunk, len(text) + chunk, chunk):
        parser.convert(text[:end])
    return (time.perf_counter() - start) * 1000


_SETUP_SCRIPT = """
import sys, time
t0 = time.perf_counter()
from benchmark.bench_parsers import available_configs
configs = {c.name: c for c in available_configs()}
t1 = time.perf_counter()
parser = configs[sys.argv[1]].create()
t2 = time.perf_counter()
parser.convert("# Title\\n\\nSome *text* and a [link](x).\\n")
t3 = time.perf_counter()
print((t1 - t0) * 1000, (t2 - t1) * 1000, (t3 - t2) * 1000)
"""


def measure_setup(config: Config) -> tuple[float, float]:
    """Cold start in a fresh interpreter: (create incl. imports, first render) in ms."""
    root = Path(__file__).parent.parent
    out = subprocess.run(
        [sys.executable, "-c", _SETUP_SCRIPT, config.name],
        capture_output=True,
        text=True,
        check=True,
        cwd=root,
    ).stdout.split()
    _, create, first = map(float, out)
    return create, first


# --- fidelity -----------------------------------------------------------------------

_PRE_RE = re.compile(r"<pre\b.*?</pre>|<code\b.*?</code>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def visible_text(html: str) -> str:
    """Text a reader sees outside code blocks / code spans."""
    return htmllib.unescape(_TAG_RE.sub("", _PRE_RE.sub("", html)))


def has_bold_body(h: str) -> bool:
    return "<strong>b</strong>" in h


@dataclass(frozen=True)
class Probe:
    """A construct as a flavour writes it, with checks on the rendered HTML."""

    construct: str
    source: str
    correct: Callable[[str], bool]
    degraded: Callable[[str], bool] = lambda h: False
    note: str = ""


def _alert_ok(h: str) -> bool:
    return "[!WARNING]" not in visible_text(h) and "warning" in h.lower() and has_bold_body(h)


def _shared_probes() -> list[Probe]:
    return [
        Probe(
            "table (inline HTML in cells)",
            "| Name | Info |\n| --- | --- |\n"
            "| **<font size='4'>[A](x.md)</font>**<br>*m* | <ul><li>[B](y.md)</li></ul> |\n",
            lambda h: "<table" in h and "<font" in h and 'href="x.md"' in h and "<li>" in h,
            lambda h: "<table" in h,
        ),
        Probe(
            "footnotes",
            "Text[^1].\n\n[^1]: The **b** note.\n",
            lambda h: "[^1]" not in visible_text(h) and 'href="#' in h and has_bold_body(h),
        ),
        Probe(
            "heading ids",
            "## Get started\n",
            lambda h: 'id="get-started"' in h,
            lambda h: "<h2" in h,
        ),
    ]


def _github_probes() -> list[Probe]:
    return [
        Probe(
            "GitHub alerts",
            "> [!WARNING]\n> **Careful**\n>\n> Body **b**.\n",
            _alert_ok,
            lambda h: "<blockquote" in h and has_bold_body(h),
            "degraded: a plain quote starting with [!WARNING]",
        ),
        Probe(
            "`<details>` with Markdown inside (collapsibles, tabs)",
            "<details open>\n<summary>Config</summary>\n\nSome **b**\n\n"
            "```toml\nx = 1\n```\n\n</details>\n",
            lambda h: "<details" in h and has_bold_body(h) and "```" not in visible_text(h),
        ),
        Probe(
            "task lists",
            "- [x] done\n- [ ] todo\n",
            lambda h: 'type="checkbox"' in h,
        ),
        Probe(
            "API anchors in headings",
            '## <a id="mknodes.rendering.use"></a>`mknodes.rendering.use`\n',
            lambda h: 'id="mknodes.rendering.use"' in h and "<h2" in h,
        ),
        Probe(
            "icons (Iconify `<img>`)",
            '[<img src="https://api.iconify.design/mdi/github.svg" alt=""> Source](x)\n',
            lambda h: "<img" in h and 'href="x"' in h,
        ),
        Probe(
            "fenced code (mermaid)",
            "```mermaid\ngraph TD\n  A-->B\n```\n",
            lambda h: "language-mermaid" in h or 'class="mermaid' in h,
            lambda h: "<pre" in h,
        ),
        Probe(
            "autolinks",
            "See https://example.org.\n",
            lambda h: 'href="https://example.org"' in h,
            lambda h: "https://example.org" in h,
        ),
        *_shared_probes(),
    ]


def _material_probes() -> list[Probe]:
    return [
        Probe(
            "admonitions (`!!!`)",
            '!!! info "Filter blocks"\n    Body **b**.\n\n    ```py\n    x = 1\n    ```\n',
            lambda h: "admonition" in h and "Filter blocks" in h and has_bold_body(h),
        ),
        Probe(
            "collapsible admonitions (`???`)",
            '??? quote "Config"\n    Body **b**.\n',
            lambda h: "<details" in h and has_bold_body(h),
            lambda h: "admonition" in h and has_bold_body(h),
            "degraded: an always open admonition",
        ),
        Probe(
            "content tabs (`===`)",
            '=== "Tab A"\n    Content **b**\n\n=== "Tab B"\n    Content c\n',
            lambda h: "tabbed" in h and has_bold_body(h) and "===" not in visible_text(h),
        ),
        Probe(
            "PyMdown blocks (`///`)",
            '/// details | "Why?"\n\nBody **b**.\n\n///\n',
            lambda h: "<details" in h and has_bold_body(h) and "///" not in visible_text(h),
        ),
        Probe(
            "fence attributes (`{.toml}`)",
            "``` {.toml }\nx = 1\n```\n",
            lambda h: "toml" in h and "{" not in h,
            lambda h: "<pre" in h,
            "degraded: a code block with a mangled language class",
        ),
        Probe(
            "fence titles (`title=`)",
            "``` {.py  title='Example'}\nx = 1\n```\n",
            lambda h: "Example" in visible_text(h) and "<pre" in h,
            lambda h: "<pre" in h,
            "degraded: the title is lost",
        ),
        Probe(
            "attribute lists (`{ .md-button }`)",
            "[Button](x.md){ .md-button }\n",
            lambda h: 'class="md-button"' in h,
        ),
        Probe(
            "heading ids (`{#custom}`)",
            "## Heading {#custom-id}\n",
            lambda h: 'id="custom-id"' in h and "{#" not in h,
        ),
        Probe(
            "Markdown in HTML (`markdown` attribute)",
            '<div class="grid" markdown>\n\nSome **b**\n\n</div>\n',
            lambda h: 'class="grid"' in h and has_bold_body(h),
        ),
        Probe(
            "icons / emoji (`:fa-brands-github:`)",
            ":fa-brands-github: Source\n",
            lambda h: ":fa-brands-github:" not in visible_text(h),
        ),
        *_shared_probes(),
    ]


def _myst_probes() -> list[Probe]:
    return [
        Probe(
            "admonition directives (`{note}`)",
            "```{note}\n\nBody **b**.\n```\n",
            lambda h: "admonition" in h and has_bold_body(h),
        ),
        Probe(
            "titled admonitions (`{admonition}`)",
            ":::{admonition} Directory tree\n:class: note\n\nBody **b**.\n:::\n",
            lambda h: "Directory tree" in h and has_bold_body(h) and ":class:" not in h,
        ),
        Probe(
            "dropdowns (`{dropdown}`)",
            ":::{dropdown} Config\n:color: info\n\nBody **b**.\n:::\n",
            lambda h: "<details" in h and has_bold_body(h),
            lambda h: has_bold_body(h) and ":::" not in visible_text(h),
        ),
        Probe(
            "tab sets (`{tab-set}`)",
            "::::{tab-set}\n\n:::{tab-item} Rendered\n:selected:\n\nContent **b**\n:::\n\n"
            ":::{tab-item} Markdown\nContent c\n:::\n\n::::\n",
            lambda h: "tab" in h and has_bold_body(h) and ":::" not in visible_text(h),
            lambda h: has_bold_body(h) and ":::" not in visible_text(h),
        ),
        Probe(
            "code-block directives (`:caption:`)",
            "```{code-block} py\n:caption: Example\nimport x\n```\n",
            lambda h: "Example" in visible_text(h) and ":caption:" not in h,
            lambda h: "<pre" in h and "import x" in h,
            "degraded: a code block with the options as code lines",
        ),
        Probe(
            "targets (`(label)=`)",
            "(mknodes.rendering.use)=\n### use\n",
            lambda h: 'id="mknodes.rendering.use"' in h and ")=" not in visible_text(h),
        ),
        Probe(
            "task lists",
            "- [x] done\n- [ ] todo\n",
            lambda h: 'type="checkbox"' in h,
        ),
        *_shared_probes(),
    ]


PROBES: dict[str, list[Probe]] = {
    "github": _github_probes(),
    "mdbook": _github_probes(),  # mknodes' mdbook flavour (no mdbook-admonish) = github
    "material": _material_probes(),
    "myst": _myst_probes(),
}

# Raw syntax a reader would see in the rendered page (outside code), per flavour.
LEAKS: dict[str, dict[str, str]] = {
    "github": {
        "alert markers": r"\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]",
        "footnote refs": r"\[\^\w+\]",
        "code fences": r"```",
    },
    "material": {
        "block markers": r"(?m)^\s*(!!!|\?\?\?\+?|===|///)[ \n]",
        "attribute lists": r"\{\s*[.#:][\w-]+[^}]*\}",
        "icon shortcodes": r":(fa|mdi|octicons?|simple|material|fontawesome)-[\w-]+:",
        "footnote refs": r"\[\^\w+\]",
    },
    "myst": {
        "directive fences": r":::+\{|```\{",
        "directive options": r"(?m)^:(class|color|caption|selected|open|name|linenos):",
        "targets": r"(?m)^\([\w.\-]+\)=\s*$",
        "footnote refs": r"\[\^\w+\]",
    },
}
LEAKS["mdbook"] = LEAKS["github"]
# Syntax that ends up as a code block instead of being rendered (checked on the HTML).
CODE_LEAKS: dict[str, dict[str, str]] = {
    "myst": {
        "directives as code blocks": r'class="(?:language|block)-\{',
        "directives as error blocks": r'<div class="error">',  # mistune: unknown directive
    },
}


def grade(probe: Probe, html: str) -> str:
    if probe.correct(html):
        return "ok"
    return "degraded" if probe.degraded(html) else "broken"


def count_leaks(flavour: str, pages: list[str]) -> dict[str, int]:
    texts = [visible_text(h) for h in pages]
    counts = {
        label: sum(len(re.findall(pattern, t)) for t in texts)
        for label, pattern in LEAKS[flavour].items()
    }
    for label, pattern in CODE_LEAKS.get(flavour, {}).items():
        counts[label] = sum(len(re.findall(pattern, h)) for h in pages)
    return counts


# --- driver -------------------------------------------------------------------------


@dataclass
class Results:
    speed: dict[str, dict[str, dict[str, float]]] = field(default_factory=dict)
    setup: dict[str, dict[str, float]] = field(default_factory=dict)
    stream: dict[str, float] = field(default_factory=dict)
    fidelity: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)
    leaks: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)
    corpus: dict[str, dict[str, int]] = field(default_factory=dict)


def run(corpus_dir: Path | None, flavours: list[str], repeat: int) -> Results:
    res = Results()
    configs = available_configs()
    corpora: dict[str, list[str]] = {}
    for flavour in flavours:
        if corpus_dir and (corpus_dir / flavour).is_dir():
            corpora[flavour] = [t for _, t in load_corpus(corpus_dir / flavour)]
    corpora["stress"] = [t for _, t in stress_corpus()]
    corpora["chat"] = chat_messages()
    for name, docs in corpora.items():
        res.corpus[name] = {"pages": len(docs), "bytes": sum(len(t.encode()) for t in docs)}

    for config in configs:
        print(f"== {config.name}", file=sys.stderr)
        create, first = measure_setup(config)
        res.setup[config.name] = {"create_ms": create, "first_render_ms": first}
        parser = config.create()
        res.speed[config.name] = {}
        for name, docs in corpora.items():
            if name in FLAVOURS and name not in config.dialects:
                continue
            s = measure(parser, docs, repeat)
            res.speed[config.name][name] = {
                "total_ms": s.total_ms,
                "pages_per_s": s.pages_per_s,
                "mb_per_s": s.mb_per_s,
                "p95_ms": s.p95_ms,
                "max_ms": s.max_ms,
            }
        res.stream[config.name] = measure_stream(parser, STREAM_DOC)
        for flavour in flavours:
            if flavour not in config.dialects:
                continue
            res.fidelity.setdefault(flavour, {})[config.name] = {
                p.construct: grade(p, parser.convert(p.source)) for p in PROBES[flavour]
            }
            if flavour in corpora:
                pages = [parser.convert(t) for t in corpora[flavour]]
                res.leaks.setdefault(flavour, {})[config.name] = count_leaks(flavour, pages)
    return res


# --- report -------------------------------------------------------------------------

SYMBOLS = {"ok": "✓", "degraded": "~", "broken": "✗"}


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def to_markdown(res: Results) -> str:
    out: list[str] = []
    corpora = list(res.corpus)
    out.append("### Corpora\n")
    out.append(
        _table(
            ["Corpus", "Pages", "Size"],
            [[c, str(v["pages"]), f"{v['bytes'] / 1e6:.2f} MB"] for c, v in res.corpus.items()],
        )
    )
    out.append("\n### Speed (pages/s; MB/s; p95 ms per page)\n")
    plain = [c for c in res.speed if "+" not in c]
    for corpus in corpora:
        rows = []
        ranked = sorted(
            (c for c in res.speed if corpus in res.speed[c]),
            key=lambda c: res.speed[c][corpus]["total_ms"],
        )
        if not ranked:
            continue
        fastest = res.speed[ranked[0]][corpus]["total_ms"]
        for c in ranked:
            s = res.speed[c][corpus]
            rows.append([
                c,
                f"{s['total_ms']:.1f}",
                f"{s['total_ms'] / fastest:.1f}x",
                f"{s['pages_per_s']:.0f}",
                f"{s['mb_per_s']:.2f}",
                f"{s['p95_ms']:.2f}",
                f"{s['max_ms']:.1f}",
            ])
        out.append(f"\n#### {corpus}\n")
        header = ["Parser", "Total ms", "Relative", "Pages/s", "MB/s", "p95 ms", "Max ms"]
        out.append(_table(header, rows))
    out.append("\n### Setup and streaming\n")
    rows = [
        [
            c,
            f"{res.setup[c]['create_ms']:.0f}",
            f"{res.setup[c]['first_render_ms']:.1f}",
            f"{res.stream[c]:.0f}",
        ]
        for c in sorted(res.setup, key=lambda c: res.stream[c])
    ]
    out.append(
        _table(["Parser", "Import + create ms", "First render ms", "Streaming re-render ms"], rows)
    )
    out.append("\n### Fidelity (✓ correct, ~ degraded, ✗ broken)\n")
    for flavour, by_config in res.fidelity.items():
        configs = [c for c in by_config if c in plain] + [c for c in by_config if "+" in c]
        constructs = list(next(iter(by_config.values())))
        rows = [
            [construct, *(SYMBOLS[by_config[c][construct]] for c in configs)]
            for construct in constructs
        ]
        out.append(f"\n#### {flavour}\n")
        out.append(_table(["Construct", *configs], rows))
        if flavour in res.leaks:
            leaks = res.leaks[flavour]
            labels = list(next(iter(leaks.values())))
            rows = [[label, *(str(leaks[c][label]) for c in configs)] for label in labels]
            out.append(f"\nRaw syntax visible in the rendered {flavour} corpus (count):\n")
            out.append(_table(["Leak", *configs], rows))
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--corpus", type=Path, help="folder with one subfolder per flavour")
    ap.add_argument("--flavours", default=",".join(FLAVOURS))
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--json", type=Path, help="write raw results as JSON")
    ap.add_argument("--markdown", type=Path, help="write result tables as Markdown")
    args = ap.parse_args()
    res = run(args.corpus, args.flavours.split(","), args.repeat)
    report = to_markdown(res)
    print(report)
    if args.markdown:
        args.markdown.write_text(report, encoding="utf-8")
    if args.json:
        args.json.write_text(json.dumps(res.__dict__, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
