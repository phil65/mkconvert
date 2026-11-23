"""Parser using [mistune](https://github.com/lepture/mistune) (pure Python, fast)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from collections.abc import Sequence

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


def _slugify(token: dict[str, Any], index: int) -> str:
    slug = re.sub(r"[^\w\- ]+", "", token["text"]).strip().lower()
    return re.sub(r"\s+", "-", slug) or f"heading-{index + 1}"


class MistuneParser(MarkdownParser):
    """Mistune: fast pure-Python parser (not fully CommonMark compliant).

    Not supported: `alerts`, `smart_punctuation`. `autolinks` links bare `https://`
    URLs only, not `www.` ones.
    """

    name = "mistune"
    requires = ("mistune",)
    extra = "mistune"
    supported_options: ClassVar[frozenset[str]] = frozenset({
        "tables",
        "strikethrough",
        "autolinks",
        "task_lists",
        "footnotes",
        "heading_ids",
        "math",
        "definition_lists",
        "hard_breaks",
        "raw_html",
        "front_matter",
    })

    def __init__(
        self,
        options: MarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        plugins: Sequence[str] = (),
    ) -> None:
        """Create a mistune parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            plugins: Further mistune plugins, e.g. `"abbr"`, `"mark"`, `"superscript"`.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import mistune
        from mistune.toc import add_toc_hook

        o = self.options
        selected = {
            "table": o.tables,
            "strikethrough": o.strikethrough,
            "url": o.autolinks,
            "task_lists": o.task_lists,
            "footnotes": o.footnotes,
            "math": o.math,
            "def_list": o.definition_lists,
        }
        names = [name for name, enabled in selected.items() if enabled]
        names += [p for p in plugins if p not in names]
        self._md = mistune.create_markdown(
            escape=not o.raw_html,
            hard_wrap=o.hard_breaks,
            plugins=names,  # type: ignore[arg-type]
        )
        if o.heading_ids:
            add_toc_hook(self._md, max_level=6, heading_id=_slugify)

    def _render(self, text: str) -> str:
        return str(self._md(text))
