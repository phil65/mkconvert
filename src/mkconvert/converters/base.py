"""Common options and base class for HTML -> Markdown converters."""

from __future__ import annotations

from typing import ClassVar, Literal

from mkconvert._core import Backend, Options


class HtmlToMarkdownOptions(Options):
    """Common HTML -> Markdown options, mapped onto every converter.

    Check `HtmlToMarkdownConverter.supported_options` for what a converter can change.
    """

    heading_style: Literal["atx", "setext"] = "atx"
    """`# Heading` (atx) or underlined headings (setext, h1 / h2 only)."""
    bullet_marker: Literal["-", "*"] = "-"
    """Marker for unordered list items."""
    emphasis_marker: Literal["*", "_"] = "*"
    """Marker for `*emphasis*` and `**strong**`."""
    code_block_style: Literal["fenced", "indented"] = "fenced"
    """Fenced or indented code blocks."""
    code_fence: Literal["```", "~~~"] = "```"
    """Fence for fenced code blocks."""
    line_break: Literal["spaces", "backslash"] = "spaces"
    """`<br>` as two trailing spaces or a trailing backslash."""
    link_style: Literal["inline", "reference"] = "inline"
    """`[text](url)` or `[text][1]` with the URLs collected at the end."""
    skip_tags: tuple[str, ...] = ()
    """Tags to drop together with their content, e.g. `("script", "style")`."""


class HtmlToMarkdownConverter(Backend[HtmlToMarkdownOptions]):
    """Base class for HTML -> Markdown converters."""

    options_class: ClassVar[type[HtmlToMarkdownOptions]] = HtmlToMarkdownOptions
