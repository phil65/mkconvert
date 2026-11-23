"""Small helpers around conversion: front matter, title extraction, sanitizing."""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import TYPE_CHECKING, Any

from mkconvert._core import MissingDependencyError


if TYPE_CHECKING:
    from collections.abc import Mapping, Set as AbstractSet


_FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?\r?\n)??(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", re.S)


def split_front_matter(text: str) -> tuple[str | None, str]:
    """Split a leading `---`-delimited front matter block off `text`.

    The block may end with `---` or `...`. It is returned unparsed (usually YAML).

    Returns:
        `(front_matter, body)`; `front_matter` is `None` if there is none.
    """
    if match := _FRONT_MATTER.match(text):
        return match.group(1) or "", text[match.end() :]
    return None, text


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.parts: list[str] = []
        self.done = False

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if self.done:
            return
        if tag == "h1" or self.depth:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.depth:
            self.depth -= 1
            self.done = self.depth == 0

    def handle_data(self, data: str) -> None:
        if self.depth and not self.done:
            self.parts.append(data)


def extract_title(html: str) -> str | None:
    """Return the text of the first `<h1>` in `html`, or `None` if there is none.

    Markup inside the heading (emphasis, permalink anchors) is dropped and entities
    are unescaped.
    """
    parser = _TitleParser()
    parser.feed(html)
    parser.close()
    if not parser.done and not parser.depth:
        return None
    return " ".join("".join(parser.parts).split())


def sanitize(
    html: str,
    *,
    extra_attributes: Mapping[str, AbstractSet[str]] | None = None,
    **nh3_options: Any,
) -> str:
    """Sanitize HTML with [nh3](https://github.com/messense/nh3) (needs the `nh3` extra).

    Uses nh3's safe defaults, which drop e.g. `id` and `class` attributes (heading ids,
    code block languages). Allow them again with `extra_attributes`.

    Args:
        html: HTML to clean.
        extra_attributes: Attributes to allow in addition to the allowed ones, per tag;
            the key `"*"` means all tags, e.g. `{"*": {"id", "class"}}`.
        nh3_options: Keyword arguments for `nh3.clean`, e.g. `tags`, `attributes`,
            `url_schemes`, `link_rel`.
    """
    try:
        import nh3
    except ImportError as e:
        msg = "sanitize() needs 'nh3'. Install it with: pip install 'mkconvert[nh3]'"
        raise MissingDependencyError(msg) from e

    if extra_attributes:
        attributes = {
            k: set(v) for k, v in nh3_options.get("attributes", nh3.ALLOWED_ATTRIBUTES).items()
        }
        for tag, names in extra_attributes.items():
            attributes[tag] = attributes.get(tag, set()) | set(names)
        nh3_options["attributes"] = attributes
    return nh3.clean(html, **nh3_options)
