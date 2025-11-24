"""CMarkGfm parser implementation."""

from __future__ import annotations

import functools
import operator
from typing import Any, Literal

from mkconvert.parsers.base_parser import BaseParser


class CMarkGfmParser(BaseParser):
    """Parser implementation using PyroMark."""

    def __init__(
        self,
        # Feature options
        mode: Literal["markdown", "gfm"] = "markdown",
        enable_footnotes: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the PyroMark parser.

        Args:
            enable_tables: Enable tables extension
            enable_footnotes: Enable footnotes extension
        """
        from cmarkgfm.cmark import Options as cmarkgfmOptions

        self._mode = mode
        options = []
        if enable_footnotes:
            options.append(cmarkgfmOptions.CMARK_OPT_FOOTNOTES)
        self._options = functools.reduce(operator.or_, options) if options else None
        self._feature_options = {"footnotes": enable_footnotes}
        self._kwargs = kwargs

    def convert(self, markdown_text: str) -> str:
        """Convert markdown to HTML."""
        import cmarkgfm

        if self._mode == "markdown":
            return cmarkgfm.markdown_to_html(markdown_text)
        return cmarkgfm.github_flavored_markdown_to_html(markdown_text, options=self._options or 0)

    @property
    def name(self) -> str:
        """Get the name of the parser."""
        return "cmarkgfm"

    @property
    def features(self) -> set[str]:
        """Get the set of supported features."""
        features = {"basic_markdown", "fenced_code"}

        if self._feature_options["footnotes"]:
            features.add("footnotes")
        return features


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)

    parser = CMarkGfmParser()
    print(parser.convert("# Test"))
