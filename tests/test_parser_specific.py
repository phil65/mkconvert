"""Parser-specific options."""

from __future__ import annotations

import pytest

from mkconvert import MarkdownOptions, to_html


def _need(module: str) -> None:
    pytest.importorskip(module)


def test_comrak_specific() -> None:
    _need("comrak")
    html = to_html(
        "x^sup^ ~sub~ ||spoiler||", parser="comrak", superscript=True, subscript=True, spoiler=True
    )
    assert "<sup>sup</sup>" in html
    assert "<sub>sub</sub>" in html
    assert "spoiler" in html
    html = to_html(
        "# Title", parser="comrak", options=MarkdownOptions(heading_ids=True), header_id_prefix="h-"
    )
    assert 'id="h-title"' in html


def test_comrak_tagfilter() -> None:
    _need("comrak")
    assert "&lt;script" in to_html("<script>x</script>\n", parser="comrak", tagfilter=True)


def test_pyromark_heading_attributes() -> None:
    _need("pyromark")
    assert 'id="custom"' in to_html(
        "# Title {#custom}\n", parser="pyromark", heading_attributes=True
    )
    assert "{#custom}" in to_html("# Title {#custom}\n", parser="pyromark")


def test_markdown_it_pyrs_xhtml() -> None:
    _need("markdown_it_pyrs")
    assert "<hr />" in to_html("---\n", parser="markdown-it-pyrs")
    assert "<hr>" in to_html("---\n", parser="markdown-it-pyrs", xhtml=False)


def test_cmarkgfm_tagfilter() -> None:
    _need("cmarkgfm")
    assert "&lt;script" in to_html("<script>x</script>\n", parser="cmarkgfm", tagfilter=True)


def test_marko_extensions() -> None:
    _need("marko")
    # pangu inserts spaces between CJK and latin characters
    html = to_html("中文English", parser="marko", extensions=["pangu"])
    assert "中文" in html
    assert html != to_html("中文English", parser="marko")


def test_mistune_plugins() -> None:
    _need("mistune")
    assert "<mark>hit</mark>" in to_html("==hit==", parser="mistune", plugins=["mark"])


def test_markdown2_extras() -> None:
    _need("markdown2")
    html = to_html("[[spoiler]]\n\n>! hidden\n", parser="markdown2", extras={"spoiler": None})
    assert "spoiler" in html


def test_python_markdown_extensions() -> None:
    _need("markdown")
    html = to_html(
        '!!! note "Heads up"\n    Text\n', parser="python-markdown", extensions=["admonition"]
    )
    assert 'class="admonition note"' in html
