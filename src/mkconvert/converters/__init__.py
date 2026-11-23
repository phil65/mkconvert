"""HTML -> Markdown converters.

Importing this package does not import any converter library: each converter imports
its library when instantiated.
"""

from __future__ import annotations

from mkconvert._core import Registry
from mkconvert.converters.base import HtmlToMarkdownConverter, HtmlToMarkdownOptions
from mkconvert.converters.htmd import HtmdConverter
from mkconvert.converters.markdownify import MarkdownifyConverter

registry: Registry[HtmlToMarkdownConverter] = Registry("HTML to Markdown converter")
"""Converters by name. Order is the preference when no converter is named."""

registry.register(HtmdConverter)
registry.register(MarkdownifyConverter)

__all__ = [
    "HtmdConverter",
    "HtmlToMarkdownConverter",
    "HtmlToMarkdownOptions",
    "MarkdownifyConverter",
    "registry",
]
