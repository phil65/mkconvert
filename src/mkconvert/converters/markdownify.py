"""Converter using [markdownify](https://github.com/matthewwithanm/python-markdownify)."""

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from mkconvert.converters.base import HtmlToMarkdownConverter


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from mkconvert._core import OnUnsupported
    from mkconvert.converters.base import HtmlToMarkdownOptions


class MarkdownifyConverter(HtmlToMarkdownConverter):
    """markdownify: pure-Python converter on top of BeautifulSoup, highly configurable.

    Not supported: `code_block_style="indented"`, `code_fence="~~~"`,
    `link_style="reference"`.
    """

    name = "markdownify"
    requires = ("markdownify",)
    extra = "markdownify"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "heading_style",
        "bullet_marker",
        "emphasis_marker",
        "line_break",
        "skip_tags",
    })

    def __init__(
        self,
        options: HtmlToMarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        bullets: str | None = None,
        strip: Sequence[str] | None = None,
        convert: Sequence[str] | None = None,
        autolinks: bool = True,
        default_title: bool = False,
        code_language: str = "",
        code_language_callback: Callable[[Any], str | None] | None = None,
        escape_asterisks: bool = True,
        escape_underscores: bool = True,
        escape_misc: bool = False,
        sub_symbol: str = "",
        sup_symbol: str = "",
        table_infer_header: bool = False,
        wrap: bool = False,
        wrap_width: int = 80,
        strip_document: Literal["strip", "lstrip", "rstrip"] | None = "strip",
    ) -> None:
        """Create a markdownify converter.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            bullets: Bullet markers per nesting level, e.g. `"*+-"`; overrides
                `bullet_marker`.
            strip: Tags to drop while keeping their content.
            convert: Only convert these tags (keeping the text of all others).
            autolinks: `<https://...>` for links whose text is their URL.
            default_title: Use the URL as title of links without one.
            code_language: Language for fenced code blocks.
            code_language_callback: Derive the language from the `<pre>` element.
            escape_asterisks: Escape `*` in text.
            escape_underscores: Escape `_` in text.
            escape_misc: Escape other Markdown characters in text.
            sub_symbol: Wrap `<sub>` text in this symbol.
            sup_symbol: Wrap `<sup>` text in this symbol.
            table_infer_header: Use the first row as table header if there is no `<th>`.
            wrap: Wrap paragraphs at `wrap_width`.
            wrap_width: Line width for `wrap`.
            strip_document: Strip whitespace around the result.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        from markdownify import MarkdownConverter

        o = self.options
        skip = frozenset(tag.lower() for tag in o.skip_tags)

        class _Converter(MarkdownConverter):
            def get_conv_fn(self, tag_name: str) -> Any:
                if tag_name.lower() in skip:
                    return lambda *_args, **_kwargs: ""
                return super().get_conv_fn(tag_name)  # ty: ignore[missing-attribute]

        self._converter = _Converter(
            heading_style="atx" if o.heading_style == "atx" else "underlined",
            bullets=bullets or o.bullet_marker,
            strong_em_symbol=o.emphasis_marker,
            newline_style=o.line_break,
            strip=list(strip) if strip is not None else None,
            convert=list(convert) if convert is not None else None,
            autolinks=autolinks,
            default_title=default_title,
            code_language=code_language,
            code_language_callback=code_language_callback,
            escape_asterisks=escape_asterisks,
            escape_underscores=escape_underscores,
            escape_misc=escape_misc,
            sub_symbol=sub_symbol,
            sup_symbol=sup_symbol,
            table_infer_header=table_infer_header,
            wrap=wrap,
            wrap_width=wrap_width,
            strip_document=strip_document,
        )

    def convert(self, text: str) -> str:
        """Convert HTML `text` to Markdown."""
        return self._converter.convert(text)
