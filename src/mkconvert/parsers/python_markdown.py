"""Parser using [Python-Markdown](https://python-markdown.github.io/) (pure Python)."""

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from mkconvert.parsers.base import MarkdownParser


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from markdown import Extension

    from mkconvert._core import OnUnsupported
    from mkconvert.parsers.base import MarkdownOptions


class PythonMarkdownParser(MarkdownParser):
    """Python-Markdown with pymdown-extensions (not CommonMark compliant).

    Fenced code blocks are always on. Strikethrough, task lists, autolinks and math
    come from pymdown-extensions. Not supported: `alerts`.
    """

    name = "python-markdown"
    requires = ("markdown", "pymdownx")
    extra = "markdown"
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
        "smart_punctuation",
        "raw_html",
        "front_matter",
    })

    def __init__(
        self,
        options: MarkdownOptions | None = None,
        *,
        on_unsupported: OnUnsupported = "warn",
        extensions: Sequence[str | Extension] = (),
        extension_configs: Mapping[str, Mapping[str, Any]] | None = None,
        output_format: Literal["html", "xhtml"] = "html",
    ) -> None:
        """Create a Python-Markdown parser.

        Args:
            options: Common options.
            on_unsupported: See `Backend`.
            extensions: Further extensions, e.g. `"admonition"` or `"pymdownx.superfences"`.
            extension_configs: Settings per extension name; merged over the ones mkconvert
                uses for the common options.
            output_format: `"html"` or `"xhtml"`.
        """
        super().__init__(options, on_unsupported=on_unsupported)
        import markdown

        o = self.options
        selected = {
            "tables": o.tables,
            "pymdownx.tilde": o.strikethrough,
            "pymdownx.magiclink": o.autolinks,
            "pymdownx.tasklist": o.task_lists,
            "footnotes": o.footnotes,
            "toc": o.heading_ids,
            "pymdownx.arithmatex": o.math,
            "def_list": o.definition_lists,
            "nl2br": o.hard_breaks,
            "smarty": o.smart_punctuation,
        }
        exts: list[str | Extension] = ["fenced_code"]
        exts += [name for name, enabled in selected.items() if enabled]
        exts += list(extensions)
        configs: dict[str, Any] = {
            "pymdownx.tilde": {"subscript": False},
            "pymdownx.arithmatex": {"generic": True},
        }
        configs.update(extension_configs or {})
        self._md = markdown.Markdown(
            extensions=exts, extension_configs=configs, output_format=output_format
        )
        if not o.raw_html:
            self._md.preprocessors.deregister("html_block")
            self._md.inlinePatterns.deregister("html")

    def _render(self, text: str) -> str:
        return self._md.reset().convert(text)
