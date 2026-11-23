"""Parser using [Marko](https://github.com/frostming/marko) (pure Python, CommonMark)."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from collections.abc import Sequence

    from marko.element import Element
    from marko.helpers import MarkoExtension

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class _EscapeHtmlMixin:
    def render_html_block(self, element: Any) -> str:
        return html.escape(element.body, quote=False)

    def render_inline_html(self, element: Any) -> str:
        return html.escape(element.children, quote=False)


class _HardBreaksMixin:
    def render_line_break(self, element: Any) -> str:
        return "<br />\n"  # soft breaks too


class MarkoParser(MarkdownParser):
    """Marko: pure-Python CommonMark parser, extensible.

    Not supported: `math`, `definition_lists`, `smart_punctuation`.
    """

    name = "marko"
    requires = ("marko",)
    extra = "marko"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "autolinks",
        "task_lists",
        "footnotes",
        "heading_ids",
        "alerts",
        "hard_breaks",
        "raw_html",
        "front_matter",
    })

    def __init__(
        self,
        options: MarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        extensions: Sequence[str | MarkoExtension] = (),
    ) -> None:
        """Create a Marko parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            extensions: Further Marko extensions, e.g. `"codehilite"` or `"pangu"`.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import marko
        from marko.ext.gfm import elements as gfm, renderer as gfm_renderer
        from marko.helpers import MarkoExtension

        o = self.options
        selected = {
            (gfm.Table, gfm.TableRow, gfm.TableCell): o.tables,
            (gfm.Strikethrough,): o.strikethrough,
            (gfm.Url,): o.autolinks,
            (gfm.Paragraph,): o.task_lists,
            (gfm.Alert,): o.alerts,
        }
        elements: list[type[Element]] = [
            e for group, enabled in selected.items() if enabled for e in group
        ]
        exts: list[str | MarkoExtension] = []
        if elements:
            exts.append(
                MarkoExtension(elements=elements, renderer_mixins=[gfm_renderer.GFMRendererMixin])
            )
        if o.footnotes:
            exts.append("footnote")
        if o.heading_ids:
            exts.append("toc")
        mixins: list[type] = [
            mixin
            for mixin, enabled in [
                (_EscapeHtmlMixin, not o.raw_html),
                (_HardBreaksMixin, o.hard_breaks),
            ]
            if enabled
        ]
        if mixins:
            exts.append(MarkoExtension(renderer_mixins=mixins))
        exts.extend(extensions)
        self._md = marko.Markdown(extensions=exts)

    def _render(self, text: str) -> str:
        return self._md.convert(text)
