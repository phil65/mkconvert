"""Front matter, title extraction and sanitizing."""

from __future__ import annotations

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
