"""Front matter, title extraction and sanitizing."""

import pytest

from mkconvert import extract_title, sanitize, split_front_matter


@pytest.mark.parametrize(
    ("html", "title"),
    [
        ("<h1>Simple Title</h1><p>Some content</p>", "Simple Title"),
        ("<h2>Secondary</h2><p>Some content</p>", None),
        ("<h1>First</h1><p>Content</p><h1>Second</h1>", "First"),
        ("<h1>With <em>italic</em> and <strong>bold</strong></h1>", "With italic and bold"),
        ('<h1 id="t">Anchored<a href="#t" class="anchor"></a></h1>', "Anchored"),
        ("<h1></h1><p>Content</p>", ""),
        ("<h1>$pecial &amp; &lt;chars&gt;</h1>", "$pecial & <chars>"),
        ("<p>Intro<br></p><h1>Spans\n  lines</h1>", "Spans lines"),
    ],
)
def test_extract_title(html: str, title: str | None) -> None:
    assert extract_title(html) == title


@pytest.mark.parametrize(
    ("html", "title"),
    [
        ('<h1><img src="logo.png" alt="logo"> Title</h1><p>Body</p>', "Title"),
        ("<h1>Hello<br>World</h1><p>Body</p>", "Hello World"),
        ("<h1>Title<wbr>More</h1><p>Body</p>", "TitleMore"),
        ("<h1><span>Unclosed</h1><p>Body</p>", "Unclosed"),
    ],
)
def test_extract_title_void_and_unclosed_nested_tags(html: str, title: str) -> None:
    assert extract_title(html) == title


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("---\ntitle: x\n---\n# Hi\n", ("title: x\n", "# Hi\n")),
        ("---\ntitle: x\n...\nbody", ("title: x\n", "body")),
        ("---\n---\nbody", ("", "body")),
        ("# No front matter\n---\n", (None, "# No front matter\n---\n")),
        ("---\nunterminated\n", (None, "---\nunterminated\n")),
    ],
)
def test_split_front_matter(text: str, expected: tuple[str | None, str]) -> None:
    assert split_front_matter(text) == expected


def test_sanitize() -> None:
    pytest.importorskip("nh3")
    html = '<h1 id="t">T</h1><a href="javascript:x()">l</a><script>bad()</script>'
    clean = sanitize(html)
    assert "<script" not in clean
    assert "javascript" not in clean
    assert 'id="t"' not in clean
    assert 'id="t"' in sanitize(html, extra_attributes={"*": {"id"}})
    assert sanitize("<b>x</b><i>y</i>", tags={"b"}) == "<b>x</b>y"


def test_sanitize_extra_attributes_with_none_attributes() -> None:
    pytest.importorskip("nh3")
    html = '<h1 id="t">T</h1><a href="https://example.org">l</a>'
    clean = sanitize(html, attributes=None, extra_attributes={"*": {"id"}})
    assert 'id="t"' in clean
    assert 'href="https://example.org"' in clean
    strict = sanitize(html, attributes={}, extra_attributes={"*": {"id"}})
    assert 'id="t"' in strict
    assert "href=" not in strict
