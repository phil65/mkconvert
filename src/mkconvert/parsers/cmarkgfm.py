"""Parser using [cmarkgfm](https://github.com/theacodes/cmarkgfm) (GitHub's cmark-gfm, C)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class CmarkgfmParser(MarkdownParser):
    """cmarkgfm: bindings to cmark-gfm, the reference GFM implementation.

    Not supported: `heading_ids`, `alerts`, `math`, `definition_lists`.
    With `raw_html=False`, raw HTML is replaced by `<!-- raw HTML omitted -->`.
    """

    name = "cmarkgfm"
    requires = ("cmarkgfm",)
    extra = "cmarkgfm"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "autolinks",
        "task_lists",
        "footnotes",
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
        tagfilter: bool = False,
        github_pre_lang: bool = False,
        sourcepos: bool = False,
    ) -> None:
        """Create a cmarkgfm parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            tagfilter: GFM tag filter: escape `<script>`, `<iframe>`, ... in raw HTML.
            github_pre_lang: GitHub-style `<pre lang="...">` code blocks.
            sourcepos: Add `data-sourcepos` attributes.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        from cmarkgfm.cmark import Options as Flags

        o = self.options
        selected = {
            "table": o.tables,
            "strikethrough": o.strikethrough,
            "autolink": o.autolinks,
            "tasklist": o.task_lists,
            "tagfilter": tagfilter,
        }
        self._extensions = [ext for ext, enabled in selected.items() if enabled]
        flags = {
            Flags.CMARK_OPT_FOOTNOTES: o.footnotes,
            Flags.CMARK_OPT_HARDBREAKS: o.hard_breaks,
            Flags.CMARK_OPT_SMART: o.smart_punctuation,
            Flags.CMARK_OPT_UNSAFE: o.raw_html,
            Flags.CMARK_OPT_GITHUB_PRE_LANG: github_pre_lang,
            Flags.CMARK_OPT_SOURCEPOS: sourcepos,
        }
        self._flags = sum(flag for flag, enabled in flags.items() if enabled)

    def _render(self, text: str) -> str:
        from cmarkgfm.cmark import markdown_to_html_with_extensions

        return markdown_to_html_with_extensions(
            text, options=self._flags, extensions=self._extensions
        )
