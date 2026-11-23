"""Common options, parametrized over every installed parser."""

from __future__ import annotations

from html import unescape
from typing import TYPE_CHECKING, Any

import pytest

from mkconvert import (
    MarkdownOptions,
    UnsupportedOptionError,
    UnsupportedOptionWarning,
    get_parser,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from mkconvert import MarkdownParser

# option -> (non-default value, Markdown source, check that holds only with the option)
CASES: dict[str, tuple[Any, str, Callable[[str], bool]]] = {
    "tables": (True, "| a | b |\n|---|---|\n| 1 | 2 |\n", lambda h: "<table" in h),
    "strikethrough": (True, "~~gone~~\n", lambda h: "<del>" in h or "<s>" in h),
    "autolinks": (
        True,
        "Visit https://example.org now.\n",
        lambda h: 'href="https://example.org"' in h,
    ),
    "task_lists": (True, "- [x] done\n- [ ] todo\n", lambda h: 'type="checkbox"' in h),
    "footnotes": (True, "Text[^1]\n\n[^1]: Note.\n", lambda h: 'href="#' in h),
    "heading_ids": (True, "# Hello World\n", lambda h: 'id="hello-world"' in h),
    "alerts": (True, "> [!NOTE]\n> Careful\n", lambda h: "[!NOTE]" not in h),
    "math": (True, "Inline $x^2$ math\n", lambda h: "$x^2$" not in h),
    "definition_lists": (True, "Term\n: Definition\n", lambda h: "<dl>" in h),
    "hard_breaks": (True, "a\nb\n", lambda h: "<br" in h),
    "smart_punctuation": (True, '"quoted"\n', lambda h: "“" in unescape(h)),
    "raw_html": (
        False,
        "<div>hi</div>\n\nx <b>y</b>\n",
        lambda h: "<div>" not in h and "<b>" not in h,
    ),
    "front_matter": (True, "---\ntitle: x\n---\n\n# Hi\n", lambda h: "title" not in h),
}


def test_cases_cover_all_options() -> None:
    assert set(CASES) == set(MarkdownOptions.model_fields)


def test_supported_options_are_known(parser_cls: type[MarkdownParser]) -> None:
    assert parser_cls.supported_options <= set(MarkdownOptions.model_fields)
    assert "front_matter" in parser_cls.supported_options


def test_commonmark_baseline(parser_cls: type[MarkdownParser]) -> None:
    html = parser_cls().convert("# Title\n\n*em* `code`\n\n```py\nx = 1\n```\n")
    assert "<h1" in html
    assert "<em>em</em>" in html
    assert "<code>code</code>" in html
    assert 'class="language-py"' in html or 'class="py language-py"' in html


@pytest.mark.parametrize("option", CASES)
def test_common_option(parser_cls: type[MarkdownParser], option: str) -> None:
    value, source, check = CASES[option]
    options = MarkdownOptions(**{option: value})
    if option not in parser_cls.supported_options:
        with pytest.raises(UnsupportedOptionError, match=option):
            parser_cls(options, on_unsupported="raise")
        with pytest.warns(UnsupportedOptionWarning, match=option):
            parser_cls(options)
        parser_cls(options, on_unsupported="ignore").convert(source)
        return
    enabled = parser_cls(options, on_unsupported="raise").convert(source)
    baseline = parser_cls().convert(source)
    assert check(enabled), enabled
    assert not check(baseline), baseline


def test_gfm_preset() -> None:
    opts = MarkdownOptions.gfm(footnotes=True)
    assert opts.changed() == {"tables", "strikethrough", "autolinks", "task_lists", "footnotes"}


def test_options_are_validated() -> None:
    with pytest.raises(ValueError, match="tabels"):
        MarkdownOptions(tabels=True)  # type: ignore[call-arg]


def test_parser_is_reusable(parser_cls: type[MarkdownParser]) -> None:
    md = get_parser(
        parser_cls.name, MarkdownOptions(footnotes="footnotes" in parser_cls.supported_options)
    )
    first = md.convert("# One\n")
    assert md.convert("# Two\n") != first
    assert md.convert("# One\n") == first
