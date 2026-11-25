"""mkconvert: one API over many Markdown parsers, plus HTML -> Markdown conversion."""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("mkconvert")
__title__ = "mkconvert"

__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2024 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/mkconvert"

from mkconvert._core import (
    MissingDependencyError,
    OnUnsupported,
    UnsupportedOptionError,
    UnsupportedOptionWarning,
)
from mkconvert.parsers import (
    CmarkgfmParser,
    ComrakParser,
    Markdown2Parser,
    MarkdownItPyParser,
    MarkdownItPyrsParser,
    MarkdownOptions,
    MarkdownParser,
    MarkoParser,
    MistuneParser,
    PyromarkParser,
    PythonMarkdownParser,
)
from mkconvert.converters import (
    HtmdConverter,
    HtmlToMarkdownConverter,
    HtmlToMarkdownOptions,
    MarkdownifyConverter,
)
from mkconvert.api import (
    get_converter,
    get_converter_class,
    get_parser,
    get_parser_class,
    list_converters,
    list_parsers,
    register_converter,
    register_parser,
    to_html,
    to_markdown,
)
from mkconvert.utils import extract_title, sanitize, split_front_matter

__all__ = [
    "CmarkgfmParser",
    "ComrakParser",
    "HtmdConverter",
    "HtmlToMarkdownConverter",
    "HtmlToMarkdownOptions",
    "Markdown2Parser",
    "MarkdownItPyParser",
    "MarkdownItPyrsParser",
    "MarkdownOptions",
    "MarkdownParser",
    "MarkdownifyConverter",
    "MarkoParser",
    "MissingDependencyError",
    "MistuneParser",
    "OnUnsupported",
    "PyromarkParser",
    "PythonMarkdownParser",
    "UnsupportedOptionError",
    "UnsupportedOptionWarning",
    "__version__",
    "extract_title",
    "get_converter",
    "get_converter_class",
    "get_parser",
    "get_parser_class",
    "list_converters",
    "list_parsers",
    "register_converter",
    "register_parser",
    "sanitize",
    "split_front_matter",
    "to_html",
    "to_markdown",
]
