"""Parser using [comrak](https://github.com/kivikakk/comrak) (Rust, CommonMark + GFM)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class ComrakParser(MarkdownParser):
    """Comrak: fast, CommonMark / GFM compliant, supports every common option."""

    name = "comrak"
    requires = ("comrak",)
    extra = "comrak"
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
        header_id_prefix: str = "",
        tagfilter: bool = False,
        superscript: bool = False,
        subscript: bool = False,
        underline: bool = False,
        spoiler: bool = False,
        greentext: bool = False,
        wikilinks: bool = False,
        multiline_block_quotes: bool = False,
        math_code: bool = False,
        relaxed_autolinks: bool = False,
        relaxed_tasklist_matching: bool = False,
        default_info_string: str | None = None,
        github_pre_lang: bool = False,
        full_info_string: bool = False,
        sourcepos: bool = False,
    ) -> None:
        """Create a comrak parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            header_id_prefix: Prefix for heading ids (with `heading_ids`).
            tagfilter: GFM tag filter: escape `<script>`, `<iframe>`, ... in raw HTML.
            superscript: `^sup^`.
            subscript: `~sub~`.
            underline: `__underline__`.
            spoiler: `||spoiler||`.
            greentext: `> greentext` lines without blockquote nesting.
            wikilinks: `[[url|title]]` wikilinks.
            multiline_block_quotes: `>>>` fenced block quotes.
            math_code: `` $`math`$ `` math syntax.
            relaxed_autolinks: Looser autolink detection (with `autolinks`).
            relaxed_tasklist_matching: Any character as task list checkmark.
            default_info_string: Language for fenced code blocks without one.
            github_pre_lang: GitHub-style `<pre lang="...">` code blocks.
            full_info_string: Keep the full info string as `data-meta`.
            sourcepos: Add `data-sourcepos` attributes.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import comrak

        o = self.options
        ext = comrak.ExtensionOptions()
        ext.table = o.tables
        ext.strikethrough = o.strikethrough
        ext.autolink = o.autolinks
        ext.tasklist = o.task_lists
        ext.footnotes = o.footnotes
        ext.header_id_prefix = header_id_prefix if o.heading_ids else None
        ext.alerts = o.alerts
        ext.math_dollars = o.math
        ext.description_lists = o.definition_lists
        ext.tagfilter = tagfilter
        ext.superscript = superscript
        ext.subscript = subscript
        ext.underline = underline
        ext.spoiler = spoiler
        ext.greentext = greentext
        ext.wikilinks_title_after_pipe = wikilinks
        ext.multiline_block_quotes = multiline_block_quotes
        ext.math_code = math_code
        parse = comrak.ParseOptions()
        parse.smart = o.smart_punctuation
        parse.relaxed_autolinks = relaxed_autolinks
        parse.relaxed_tasklist_matching = relaxed_tasklist_matching
        parse.default_info_string = default_info_string
        render = comrak.RenderOptions()
        render.hardbreaks = o.hard_breaks
        render.unsafe_ = o.raw_html
        render.escape = not o.raw_html
        render.github_pre_lang = github_pre_lang
        render.full_info_string = full_info_string
        render.sourcepos = sourcepos
        self._options = (ext, parse, render)

    def _render(self, text: str) -> str:
        import comrak

        ext, parse, render = self._options
        return comrak.render_markdown(
            text, extension_options=ext, parse_options=parse, render_options=render
        )
