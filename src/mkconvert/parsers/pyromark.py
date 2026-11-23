"""Parser using [pyromark](https://github.com/monosans/pyromark) (Rust, pulldown-cmark)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    import pyromark

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class PyromarkParser(MarkdownParser):
    """Pyromark: bindings to pulldown-cmark, very fast.

    Not supported: `autolinks`, `heading_ids` (only explicit `# Title {#id}` via
    `heading_attributes`), `hard_breaks` and `raw_html=False`.
    """

    name = "pyromark"
    requires = ("pyromark",)
    extra = "pyromark"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "task_lists",
        "footnotes",
        "alerts",
        "math",
        "definition_lists",
        "smart_punctuation",
        "front_matter",
    })

    def __init__(
        self,
        options: MarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        heading_attributes: bool = False,
        superscript: bool = False,
        subscript: bool = False,
        wikilinks: bool = False,
        old_footnotes: bool = False,
        highlight: pyromark.Theme | None = None,
    ) -> None:
        """Create a pyromark parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            heading_attributes: `# Heading {#id .class}` attributes.
            superscript: `^sup^`.
            subscript: `~sub~`.
            wikilinks: `[[wikilinks]]`.
            old_footnotes: Footnotes with the older, looser pulldown-cmark syntax.
            highlight: Syntax-highlight code blocks with this theme.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import pyromark

        flags = pyromark.Options
        o = self.options
        selected = {
            flags.ENABLE_TABLES: o.tables,
            flags.ENABLE_STRIKETHROUGH: o.strikethrough,
            flags.ENABLE_TASKLISTS: o.task_lists,
            flags.ENABLE_FOOTNOTES: o.footnotes,
            flags.ENABLE_GFM: o.alerts,
            flags.ENABLE_MATH: o.math,
            flags.ENABLE_DEFINITION_LIST: o.definition_lists,
            flags.ENABLE_SMART_PUNCTUATION: o.smart_punctuation,
            flags.ENABLE_HEADING_ATTRIBUTES: heading_attributes,
            flags.ENABLE_SUPERSCRIPT: superscript,
            flags.ENABLE_SUBSCRIPT: subscript,
            flags.ENABLE_WIKILINKS: wikilinks,
            flags.ENABLE_OLD_FOOTNOTES: old_footnotes,
        }
        value = flags(0)
        for flag, enabled in selected.items():
            if enabled:
                value |= flag
        self._md = pyromark.Markdown(options=value, highlight=highlight)

    def _render(self, text: str) -> str:
        return self._md.html(text)
