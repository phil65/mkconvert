"""Parser using [markdown2](https://github.com/trentm/python-markdown2) (pure Python)."""

from typing import TYPE_CHECKING, Any, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from collections.abc import Mapping

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class Markdown2Parser(MarkdownParser):
    """markdown2: pure-Python Markdown (not CommonMark compliant), many "extras".

    Not supported: `autolinks`, `math`, `definition_lists`.
    """

    name = "markdown2"
    requires = ("markdown2",)
    extra = "markdown2"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "task_lists",
        "footnotes",
        "heading_ids",
        "alerts",
        "hard_breaks",
        "smart_punctuation",
        "raw_html",
        "front_matter",
    })

    def __init__(
        self,
        options: MarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        extras: Mapping[str, Any] | None = None,
        highlight: bool = False,
        html4tags: bool = False,
    ) -> None:
        """Create a markdown2 parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            extras: Further markdown2 extras with their settings (`None` for defaults),
                e.g. `{"cuddled-lists": None, "toc": {"depth": 3}}`.
            highlight: Highlight fenced code blocks with Pygments (if installed).
            html4tags: HTML4-style tags (`<br>` instead of `<br />`).
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import markdown2

        o = self.options
        selected: dict[str, tuple[bool, Any]] = {
            "fenced-code-blocks": (True, None),
            "highlightjs-lang": (not highlight, None),
            "tables": (o.tables, None),
            "strike": (o.strikethrough, None),
            "task_list": (o.task_lists, None),
            "footnotes": (o.footnotes, None),
            "header-ids": (o.heading_ids, None),
            "alerts": (o.alerts, None),
            "breaks": (o.hard_breaks, {"on_newline": True}),
            "smarty-pants": (o.smart_punctuation, None),
        }
        all_extras = {name: value for name, (enabled, value) in selected.items() if enabled}
        all_extras.update(extras or {})
        self._md = markdown2.Markdown(
            extras=all_extras,
            safe_mode=None if o.raw_html else "escape",
            html4tags=html4tags,
        )

    def _render(self, text: str) -> str:
        return str(self._md.convert(text))
