"""Converter using [htmd-py](https://github.com/lmmx/htmd-py) (Rust, port of turndown)."""

from typing import TYPE_CHECKING, ClassVar, Literal

from mkconvert.converters.base import HtmlToMarkdownConverter


if TYPE_CHECKING:
    from mkconvert._core import OnUnsupported
    from mkconvert.converters.base import HtmlToMarkdownOptions


class HtmdConverter(HtmlToMarkdownConverter):
    """htmd: fast Rust converter.

    Not supported: `emphasis_marker="_"`.
    """

    name = "htmd"
    requires = ("htmd",)
    extra = "htmd-py"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "heading_style",
        "bullet_marker",
        "code_block_style",
        "code_fence",
        "line_break",
        "link_style",
        "skip_tags",
    })

    def __init__(
        self,
        options: HtmlToMarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        hr_style: Literal["dashes", "asterisks", "underscores"] = "dashes",
        link_reference_style: Literal["full", "collapsed", "shortcut"] = "full",
        preformatted_code: bool = False,
        ul_bullet_spacing: int = 1,
        ol_number_spacing: int = 1,
        translation_mode: Literal["pure", "faithful"] = "pure",
    ) -> None:
        """Create an htmd converter.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            hr_style: `- - -`, `* * *` or `_ _ _` for `<hr>`.
            link_reference_style: Reference link form (with `link_style="reference"`).
            preformatted_code: Keep whitespace of inline `<code>` as is.
            ul_bullet_spacing: Spaces after a bullet list marker.
            ol_number_spacing: Spaces after an ordered list number.
            translation_mode: `"faithful"` keeps HTML that has no Markdown equivalent.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import htmd

        o = self.options
        opts = htmd.Options()  # ty: ignore[missing-attribute]
        opts.heading_style = "setex" if o.heading_style == "setext" else "atx"
        opts.bullet_list_marker = "dash" if o.bullet_marker == "-" else "asterisk"
        opts.code_block_style = o.code_block_style
        opts.code_block_fence = "tildes" if o.code_fence == "~~~" else "backticks"
        opts.br_style = "backslash" if o.line_break == "backslash" else "two_spaces"
        opts.link_style = "referenced" if o.link_style == "reference" else "inlined"
        opts.skip_tags = [tag.lower() for tag in o.skip_tags]
        opts.hr_style = hr_style
        opts.link_reference_style = link_reference_style
        opts.preformatted_code = preformatted_code
        opts.ul_bullet_spacing = ul_bullet_spacing
        opts.ol_number_spacing = ol_number_spacing
        opts.translation_mode = translation_mode
        self._opts = opts

    def convert(self, text: str) -> str:
        """Convert HTML `text` to Markdown."""
        import htmd

        return htmd.convert_html(text, self._opts)  # ty: ignore[missing-attribute]
