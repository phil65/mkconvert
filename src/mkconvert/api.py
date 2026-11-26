"""Top-level functions: convert, look up and register backends by name."""

from typing import TYPE_CHECKING, Any

from mkconvert import converters, parsers


if TYPE_CHECKING:
    from mkconvert._core import OnUnsupported
    from mkconvert.converters import HtmlToMarkdownConverter, HtmlToMarkdownOptions
    from mkconvert.parsers import MarkdownOptions, MarkdownParser


def to_html(
    text: str,
    *,
    parser: str | None = None,
    options: MarkdownOptions | None = None,
    on_unsupported: OnUnsupported = "warn",
    **parser_options: Any,
) -> str:
    """Convert Markdown to HTML.

    For many conversions with the same settings, create the parser once with
    `get_parser` and call its `convert` method.

    Args:
        text: Markdown source.
        parser: Parser name (see `list_parsers`); `None` uses the first installed one.
        options: Common options; `None` for plain CommonMark.
        on_unsupported: What to do with options the parser cannot honour:
            `"warn"`, `"raise"` or `"ignore"`.
        parser_options: Parser-specific options, see the parser class.
    """
    md = get_parser(parser, options, on_unsupported=on_unsupported, **parser_options)
    return md.convert(text)


def to_markdown(
    html: str,
    *,
    converter: str | None = None,
    options: HtmlToMarkdownOptions | None = None,
    on_unsupported: OnUnsupported = "warn",
    **converter_options: Any,
) -> str:
    """Convert HTML to Markdown.

    Args:
        html: HTML source.
        converter: Converter name (see `list_converters`); `None` uses the first
            installed one.
        options: Common options; `None` for the defaults.
        on_unsupported: What to do with options the converter cannot honour:
            `"warn"`, `"raise"` or `"ignore"`.
        converter_options: Converter-specific options, see the converter class.
    """
    conv = get_converter(converter, options, on_unsupported=on_unsupported, **converter_options)
    return conv.convert(html)


def get_parser(
    name: str | None = None,
    options: MarkdownOptions | None = None,
    *,
    on_unsupported: OnUnsupported = "warn",
    **parser_options: Any,
) -> MarkdownParser:
    """Create the parser registered as `name` (`None`: the first installed one).

    Raises:
        ValueError: Unknown parser name.
        MissingDependencyError: The parser's package is not installed.
        UnsupportedOptionError: See `on_unsupported`.
    """
    cls = parsers.registry.get(name)
    return cls(options, on_unsupported=on_unsupported, **parser_options)


def get_converter(
    name: str | None = None,
    options: HtmlToMarkdownOptions | None = None,
    *,
    on_unsupported: OnUnsupported = "warn",
    **converter_options: Any,
) -> HtmlToMarkdownConverter:
    """Create the converter registered as `name` (`None`: the first installed one).

    Raises:
        ValueError: Unknown converter name.
        MissingDependencyError: The converter's package is not installed.
        UnsupportedOptionError: See `on_unsupported`.
    """
    cls = converters.registry.get(name)
    return cls(options, on_unsupported=on_unsupported, **converter_options)


def get_parser_class(name: str) -> type[MarkdownParser]:
    """Return the parser class registered as `name`, e.g. to check `supported_options`."""
    return parsers.registry.get(name)


def get_converter_class(name: str) -> type[HtmlToMarkdownConverter]:
    """Return the converter class registered as `name`."""
    return converters.registry.get(name)


def list_parsers(*, available_only: bool = False) -> list[str]:
    """Names of the registered parsers, in order of preference.

    Args:
        available_only: Only parsers whose package is installed.
    """
    return parsers.registry.names(available_only=available_only)


def list_converters(*, available_only: bool = False) -> list[str]:
    """Names of the registered HTML -> Markdown converters, in order of preference.

    Args:
        available_only: Only converters whose package is installed.
    """
    return converters.registry.names(available_only=available_only)


def register_parser[T: type[MarkdownParser]](cls: T) -> T:
    """Register a `MarkdownParser` subclass under its `name` (usable as decorator)."""
    parsers.registry.register(cls)
    return cls


def register_converter[T: type[HtmlToMarkdownConverter]](cls: T) -> T:
    """Register an `HtmlToMarkdownConverter` subclass under its `name`."""
    converters.registry.register(cls)
    return cls
