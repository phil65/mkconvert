"""Parser using [markdown-it-pyrs](https://github.com/chrisjsewell/markdown-it-pyrs) (Rust)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from markdown_it_pyrs.markdown_it_pyrs import _PLUGIN_NAME

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


# The "commonmark" preset without "html_block" / "html_inline".
_COMMONMARK_RULES: list[_PLUGIN_NAME] = [
    "blockquote",
    "code",
    "fence",
    "heading",
    "hr",
    "lheading",
    "list",
    "paragraph",
    "reference",
    "autolink",
    "backticks",
    "emphasis",
    "entity",
    "escape",
    "image",
    "link",
    "newline",
]


class MarkdownItPyrsParser(MarkdownParser):
    """markdown-it-pyrs: Rust port of markdown-it.

    Not supported: `alerts`, `math`, `hard_breaks`.
    """

    name = "markdown-it-pyrs"
    requires = ("markdown_it_pyrs",)
    extra = "markdown_it_pyrs"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "autolinks",
        "task_lists",
        "footnotes",
        "heading_ids",
        "definition_lists",
        "smart_punctuation",
        "raw_html",
        "front_matter",
    })

    def __init__(
        self,
        options: MarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        xhtml: bool = True,
        sourcepos: bool = False,
        plugins: list[_PLUGIN_NAME] | None = None,
    ) -> None:
        """Create a markdown-it-pyrs parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            xhtml: Self-closing tags with a trailing slash (`<br />`).
            sourcepos: Add `data-sourcepos` attributes.
            plugins: Further plugins / rules to enable.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        from markdown_it_pyrs import MarkdownIt

        o = self.options
        rules = list(_COMMONMARK_RULES)
        if o.raw_html:
            rules += ["html_block", "html_inline"]
        selected: dict[_PLUGIN_NAME, bool] = {
            "table": o.tables,
            "strikethrough": o.strikethrough,
            "autolink_ext": o.autolinks,
            "tasklist": o.task_lists,
            "footnote": o.footnotes,
            "heading_anchors": o.heading_ids,
            "deflist": o.definition_lists,
            "smartquotes": o.smart_punctuation,
            "replacements": o.smart_punctuation,
            "sourcepos": sourcepos,
        }
        rules += [rule for rule, enabled in selected.items() if enabled]
        rules += plugins or []
        self._md = MarkdownIt("zero").enable_many(rules)
        self._xhtml = xhtml

    def _render(self, text: str) -> str:
        return self._md.render(text, xhtml=self._xhtml)
