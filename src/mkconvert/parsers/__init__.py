"""Markdown -> HTML parsers.

Importing this package does not import any parser library: each parser imports its
library when instantiated.
"""

from mkconvert._core import Registry
from mkconvert.parsers.base import MarkdownOptions, MarkdownParser
from mkconvert.parsers.cmarkgfm import CmarkgfmParser
from mkconvert.parsers.comrak import ComrakParser
from mkconvert.parsers.markdown2 import Markdown2Parser
from mkconvert.parsers.markdown_it_py import MarkdownItPyParser
from mkconvert.parsers.markdown_it_pyrs import MarkdownItPyrsParser
from mkconvert.parsers.marko import MarkoParser
from mkconvert.parsers.mistune import MistuneParser
from mkconvert.parsers.pyromark import PyromarkParser
from mkconvert.parsers.python_markdown import PythonMarkdownParser

registry: Registry[MarkdownParser] = Registry("Markdown parser")
"""Parsers by name. Order is the preference when no parser is named."""

for _cls in (
    ComrakParser,
    PyromarkParser,
    CmarkgfmParser,
    MistuneParser,
    MarkdownItPyParser,
    MarkoParser,
    Markdown2Parser,
    PythonMarkdownParser,
    MarkdownItPyrsParser,  # deprecated
):
    registry.register(_cls)

__all__ = [
    "CmarkgfmParser",
    "ComrakParser",
    "Markdown2Parser",
    "MarkdownItPyParser",
    "MarkdownItPyrsParser",
    "MarkdownOptions",
    "MarkdownParser",
    "MarkoParser",
    "MistuneParser",
    "PyromarkParser",
    "PythonMarkdownParser",
    "registry",
]
