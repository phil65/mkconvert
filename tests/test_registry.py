"""Registry, lookup and missing-dependency errors."""

from __future__ import annotations

from typing import ClassVar

import pytest

import mkconvert
from mkconvert import (
    MarkdownOptions,
    MarkdownParser,
    MissingDependencyError,
    get_parser,
    get_parser_class,
    list_converters,
    list_parsers,
    to_html,
)
from mkconvert.parsers import registry


def test_list_parsers() -> None:
    names = list_parsers()
    assert names[0] == "comrak"
    assert set(names) == {
        "comrak",
        "pyromark",
        "markdown-it-pyrs",
        "markdown-it-py",
        "cmarkgfm",
        "mistune",
        "marko",
        "markdown2",
        "python-markdown",
    }
    available = list_parsers(available_only=True)
    assert set(available) <= set(names)
    assert all(get_parser_class(n).is_available() for n in available)


def test_list_converters() -> None:
    assert list_converters() == ["htmd", "markdownify"]


def test_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown Markdown parser 'nope'"):
        to_html("x", parser="nope")
    with pytest.raises(ValueError, match="Unknown HTML to Markdown converter"):
        mkconvert.to_markdown("x", converter="nope")


def test_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    cls = get_parser_class("mistune")
    monkeypatch.setattr(cls, "requires", ("not_installed_pkg_xyz",))
    assert not cls.is_available()
    with pytest.raises(MissingDependencyError, match=r"pip install 'mkconvert\[mistune\]'"):
        to_html("x", parser="mistune")
    assert "mistune" not in list_parsers(available_only=True)


def test_no_parser_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    for cls in registry:
        monkeypatch.setattr(cls, "requires", ("not_installed_pkg_xyz",))
    with pytest.raises(MissingDependencyError, match="No Markdown parser is installed"):
        to_html("x")


def test_default_parser_is_first_available() -> None:
    first = list_parsers(available_only=True)[0]
    assert type(get_parser()).name == first


def test_register_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "_classes", dict(registry._classes))

    @mkconvert.register_parser
    class ShoutParser(MarkdownParser):
        name = "shout"
        requires = ()
        extra = "none"
        supported_options: ClassVar[frozenset[str]] = frozenset({"front_matter"})

        def _render(self, text: str) -> str:
            return f"<p>{text.upper()}</p>"

    assert "shout" in list_parsers()
    assert to_html("hi", parser="shout") == "<p>HI</p>"
    assert (
        to_html("---\na: 1\n---\nhi", parser="shout", options=MarkdownOptions(front_matter=True))
        == "<p>HI</p>"
    )
    assert isinstance(get_parser("shout"), ShoutParser)


def test_unknown_provider_option() -> None:
    pytest.importorskip("mistune")
    with pytest.raises(TypeError, match="bogus"):
        to_html("x", parser="mistune", bogus=True)
