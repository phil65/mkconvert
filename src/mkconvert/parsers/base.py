"""Common options and base class for Markdown -> HTML parsers."""

from abc import abstractmethod
from typing import Any, ClassVar, Self

from mkconvert._core import Backend, Options
from mkconvert.utils import split_front_matter


class MarkdownOptions(Options):
    """Common Markdown -> HTML options, mapped onto every parser.

    The defaults are plain CommonMark (every extension off, raw HTML passed through),
    except that a leading front matter block is dropped.
    Check `MarkdownParser.supported_options` for what a parser can enable.
    """

    tables: bool = False
    """GFM pipe tables."""
    strikethrough: bool = False
    """`~~text~~` -> `<del>` (or `<s>`)."""
    autolinks: bool = False
    """Link bare URLs (`https://...`, `www.`) like GFM's autolink extension."""
    task_lists: bool = False
    """`- [x] item` -> list items with checkboxes."""
    footnotes: bool = False
    """`text[^1]` references and `[^1]: ...` definitions."""
    heading_ids: bool = False
    """Add slug `id` attributes to headings."""
    alerts: bool = False
    """GitHub alerts: `> [!NOTE]`, `> [!WARNING]`, ..."""
    math: bool = False
    """`$inline$` and `$$display$$` math, rendered as markup for MathJax / KaTeX."""
    definition_lists: bool = False
    """`Term` followed by `: definition` lines -> `<dl>`."""
    hard_breaks: bool = False
    """Render every newline inside a paragraph as `<br>`."""
    smart_punctuation: bool = False
    """Typographic quotes, dashes and ellipses."""
    raw_html: bool = True
    """Pass raw HTML through. `False` escapes or omits it (parser-dependent).

    This is not a sanitizer: use `mkconvert.sanitize` for untrusted input.
    """
    front_matter: bool = True
    """Drop a leading `---`-delimited front matter block instead of rendering it.

    On by default: almost every Markdown file with a leading `---` block means front
    matter, not a horizontal rule followed by a heading.
    """

    @classmethod
    def gfm(cls, **changes: Any) -> Self:
        """GitHub Flavored Markdown: tables, strikethrough, autolinks and task lists.

        Args:
            changes: Further options to set, e.g. `footnotes=True`.
        """
        values: dict[str, Any] = dict(
            tables=True, strikethrough=True, autolinks=True, task_lists=True
        )
        return cls(**(values | changes))


class MarkdownParser(Backend[MarkdownOptions]):
    """Base class for Markdown -> HTML parsers.

    Subclasses take `MarkdownOptions` plus their own keyword-only options, map them onto
    the wrapped library once in `__init__` and implement `_render`.
    """

    options_class: ClassVar[type[MarkdownOptions]] = MarkdownOptions

    def convert(self, text: str) -> str:
        """Convert Markdown `text` to HTML."""
        if self.options.front_matter:
            _, text = split_front_matter(text)
        return self._render(text)

    @abstractmethod
    def _render(self, text: str) -> str:
        """Render Markdown to HTML with the wrapped library."""
