"""Tree processors for HTML DOM manipulation."""

from mkconvert.tree_processors.base import (
    LXML_AVAILABLE as HAS_LXML,
    ETTreeProcessor,
    LXMLTreeProcessor,
    TreeProcessor,
)
from mkconvert.tree_processors.extract_title import ExtractTitleETProcessor
from mkconvert.tree_processors.extract_title_lxml import ExtractTitleLXMLProcessor
from mkconvert.tree_processors.registry import TreeProcessorRegistry

# The lxml processors raise ImportError on instantiation if lxml is not installed.

__all__ = [
    "HAS_LXML",
    "ETTreeProcessor",
    "ExtractTitleETProcessor",
    "ExtractTitleLXMLProcessor",
    "LXMLTreeProcessor",
    "TreeProcessor",
    "TreeProcessorRegistry",
]
