"""Parser using [markdown-it-py](https://github.com/executablebooks/markdown-it-py) (Python)."""

from typing import TYPE_CHECKING, Any, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from markdown_it import MarkdownIt

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class MarkdownItPyParser(MarkdownParser):
    """markdown-it-py + mdit-py-plugins: pure Python, CommonMark compliant, pluggable.

    Supports every common option. Further syntax (MkDocs-style `!!!` admonitions, MyST
    directives, attributes, ...) comes from mdit-py-plugins via `plugins`.
    """

    name = "markdown-it-py"
    requires = ("markdown_it", "mdit_py_plugins")
    extra = "markdown-it-py"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "autolinks",
        "task_lists",
        "footnotes",
        "heading_ids",
        "alerts",
        "math",
        "definition_lists",
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
        plugins: Sequence[Callable[..., None] | tuple[Callable[..., None], dict[str, Any]]] = (),
        xhtml: bool = True,
        heading_levels: tuple[int, int] = (1, 6),
    ) -> None:
        """Create a markdown-it-py parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            plugins: Further plugins, each a plugin function or a `(function, kwargs)`
                pair, e.g. `[mdit_py_plugins.admon.admon_plugin]`.
            xhtml: Self-closing tags with a trailing slash (`<br />`).
            heading_levels: Lowest and highest heading level that get ids
                (with `heading_ids`).
        """
        super().__init__(options, on_unsupported=on_unsupported)
        from markdown_it import MarkdownIt

        o = self.options
        md = MarkdownIt(
            "commonmark",
            {
                "html": o.raw_html,
                "xhtmlOut": xhtml,
                "breaks": o.hard_breaks,
                "typographer": o.smart_punctuation,
                "tasklists": o.task_lists,
                "alerts": o.alerts,
            },
        )
        if not o.raw_html:
            md.disable(["html_block", "html_inline"])
        if o.tables:
            md.enable("table")
        if o.strikethrough:
            md.enable("strikethrough")
        if o.smart_punctuation:
            md.enable(["replacements", "smartquotes"])
        if o.autolinks:
            from mdit_py_plugins.gfm_autolink import gfm_autolink_plugin

            md.use(gfm_autolink_plugin)
        if o.footnotes:
            from mdit_py_plugins.footnote import footnote_plugin

            md.use(footnote_plugin, inline=False)
        if o.heading_ids:
            from mdit_py_plugins.anchors import anchors_plugin

            md.use(anchors_plugin, min_level=heading_levels[0], max_level=heading_levels[1])
        if o.math:
            from mdit_py_plugins.dollarmath import dollarmath_plugin

            md.use(dollarmath_plugin)
        if o.definition_lists:
            from mdit_py_plugins.deflist import deflist_plugin

            md.use(deflist_plugin)
        for plugin in plugins:
            func, kwargs = plugin if isinstance(plugin, tuple) else (plugin, {})
            md.use(func, **kwargs)
        self._md: MarkdownIt = md

    def _render(self, text: str) -> str:
        return self._md.render(text)
