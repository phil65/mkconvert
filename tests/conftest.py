import pytest

from mkconvert import converters, parsers


def _params(registry):
    return [
        pytest.param(
            cls,
            id=cls.name,
            marks=pytest.mark.skipif(not cls.is_available(), reason=f"needs [{cls.extra}]"),
        )
        for cls in registry
    ]


@pytest.fixture(params=_params(parsers.registry))
def parser_cls(request: pytest.FixtureRequest) -> type[parsers.MarkdownParser]:
    """Each registered parser class (skipped if its package is not installed)."""
    return request.param


@pytest.fixture(params=_params(converters.registry))
def converter_cls(request: pytest.FixtureRequest) -> type[converters.HtmlToMarkdownConverter]:
    """Each registered converter class (skipped if its package is not installed)."""
    return request.param
