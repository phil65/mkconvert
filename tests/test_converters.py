"""HTML -> Markdown converters."""

from typing import TYPE_CHECKING, Any

import pytest

from mkconvert import (
    HtmlToMarkdownOptions,
    UnsupportedOptionError,
    UnsupportedOptionWarning,
    to_markdown,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from mkconvert import HtmlToMarkdownConverter

# option -> (non-default value, HTML, check that holds only with the option)
CASES: dict[str, tuple[Any, str, Callable[[str], bool]]] = {
    "heading_style": ("setext", "<h1>Title</h1>", lambda md: "Title\n=" in md),
    "bullet_marker": ("*", "<ul><li>a</li></ul>", lambda md: md.lstrip().startswith("* a")),
    "emphasis_marker": ("_", "<p><em>e</em></p>", lambda md: "_e_" in md),
    "code_block_style": (
        "indented",
        "<pre><code>x = 1</code></pre>",
        lambda md: "    x = 1" in md and "```" not in md,
    ),
    "code_fence": ("~~~", "<pre><code>x = 1</code></pre>", lambda md: "~~~" in md),
    "line_break": ("backslash", "<p>a<br>b</p>", lambda md: "a\\\nb" in md),
    "link_style": (
        "reference",
        '<p><a href="https://x.org">l</a></p>',
        lambda md: "[l][1]" in md and "[1]: https://x.org" in md,
    ),
    "skip_tags": (
        ("aside",),
        "<p>keep</p><aside>drop</aside>",
        lambda md: "drop" not in md and "keep" in md,
    ),
}


def test_cases_cover_all_options() -> None:
    assert set(CASES) == set(HtmlToMarkdownOptions.model_fields)


def test_defaults(converter_cls: type[HtmlToMarkdownConverter]) -> None:
    html = "<h1>Title</h1><p>a <em>e</em> <strong>s</strong></p><ul><li>i</li></ul>"
    md = converter_cls().convert(html)
    assert "# Title" in md
    assert "*e*" in md
    assert "**s**" in md
    assert "- i" in md


def test_table(converter_cls: type[HtmlToMarkdownConverter]) -> None:
    html = "<table><tr><th>a</th><th>b</th></tr><tr><td>1</td><td>2</td></tr></table>"
    md = converter_cls().convert(html)
    assert "|" in md
    assert "1" in md


@pytest.mark.parametrize("option", CASES)
def test_common_option(converter_cls: type[HtmlToMarkdownConverter], option: str) -> None:
    value, source, check = CASES[option]
    options = HtmlToMarkdownOptions(**{option: value})
    if option not in converter_cls.supported_options:
        with pytest.raises(UnsupportedOptionError, match=option):
            converter_cls(options, on_unsupported="raise")
        with pytest.warns(UnsupportedOptionWarning, match=option):
            converter_cls(options)
        return
    converted = converter_cls(options, on_unsupported="raise").convert(source)
    baseline = converter_cls().convert(source)
    assert check(converted), converted
    assert not check(baseline), baseline


def test_htmd_specific() -> None:
    pytest.importorskip("htmd")
    assert "* * *" in to_markdown("<hr>", converter="htmd", hr_style="asterisks")


def test_markdownify_specific() -> None:
    pytest.importorskip("markdownify")
    md = to_markdown("<pre><code>x</code></pre>", converter="markdownify", code_language="py")
    assert "```py" in md
    md = to_markdown(
        "<ul><li>a<ul><li>b</li></ul></li></ul>", converter="markdownify", bullets="*+"
    )
    assert "* a" in md
    assert "+ b" in md
