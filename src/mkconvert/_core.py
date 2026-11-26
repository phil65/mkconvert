"""Shared machinery for parsers and converters: options, errors, registry."""

from abc import ABC, abstractmethod
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast
import warnings

from pydantic import BaseModel, ConfigDict


if TYPE_CHECKING:
    from collections.abc import Iterator


_PACKAGE_DIR = str(Path(__file__).parent)

OnUnsupported = Literal["warn", "raise", "ignore"]
"""What to do when options are set that a backend cannot honour."""


class MissingDependencyError(ImportError):
    """The package a backend needs is not installed."""


class UnsupportedOptionError(ValueError):
    """Options were set that the chosen backend cannot honour."""


class UnsupportedOptionWarning(UserWarning):
    """Options were set that the chosen backend cannot honour; they are ignored."""


class Options(BaseModel):
    """Base class for the common option models.

    Every default is the baseline behaviour all backends can produce. Setting an option
    to a non-default value requires the backend to support it, see
    `Backend.supported_options`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", use_attribute_docstrings=True)

    def changed(self) -> set[str]:
        """Names of the options whose value differs from the default."""
        return {
            name
            for name, field in type(self).model_fields.items()
            if getattr(self, name) != field.default
        }


class Backend[O: Options](ABC):
    """Base class for Markdown parsers and HTML-to-Markdown converters."""

    name: ClassVar[str]
    """Registry name of the backend."""
    requires: ClassVar[tuple[str, ...]]
    """Import names of the packages the backend needs."""
    extra: ClassVar[str]
    """The mkconvert extra that installs these packages."""
    supported_options: ClassVar[frozenset[str]]
    """Common options this backend can set to a non-default value."""
    options_class: ClassVar[type[Options]]

    def __init__(self, options: O | None = None, *, on_unsupported: OnUnsupported = "warn"):
        """Check dependencies and options.

        Args:
            options: Common options; `None` for the defaults.
            on_unsupported: What to do with options this backend cannot honour:
                `"warn"` (ignore them with an `UnsupportedOptionWarning`), `"raise"`
                (`UnsupportedOptionError`) or `"ignore"` (silently).

        Raises:
            MissingDependencyError: A required package is not installed.
            UnsupportedOptionError: Unsupported options are set and
                `on_unsupported="raise"`.
        """
        self.require()
        self.options: O = options if options is not None else cast("O", self.options_class())
        if unsupported := self.unsupported(self.options):
            names = ", ".join(sorted(unsupported))
            msg = f"{self.name!r} does not support option(s): {names}"
            match on_unsupported:
                case "raise":
                    raise UnsupportedOptionError(msg)
                case "warn":
                    warnings.warn(
                        f"{msg}; ignoring them",
                        UnsupportedOptionWarning,
                        skip_file_prefixes=(_PACKAGE_DIR,),
                    )

    @classmethod
    def unsupported(cls, options: Options) -> set[str]:
        """Names of the options in `options` this backend cannot honour."""
        return options.changed() - cls.supported_options

    @classmethod
    def is_available(cls) -> bool:
        """Whether the packages this backend needs are installed."""
        return all(importlib.util.find_spec(pkg) is not None for pkg in cls.requires)

    @classmethod
    def require(cls) -> None:
        """Raise `MissingDependencyError` if a required package is missing."""
        if not cls.is_available():
            pkgs = ", ".join(repr(p) for p in cls.requires)
            msg = (
                f"{cls.name!r} needs the package(s) {pkgs}. "
                f"Install them with: pip install 'mkconvert[{cls.extra}]'"
            )
            raise MissingDependencyError(msg)

    @abstractmethod
    def convert(self, text: str) -> str:
        """Convert `text` and return the result."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.options!r})"


class Registry[B: Backend[Any]]:
    """Name -> backend class mapping, in order of preference."""

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._classes: dict[str, type[B]] = {}

    def register(self, cls: type[B]) -> type[B]:
        """Register a backend class under `cls.name` (usable as a decorator)."""
        self._classes[cls.name] = cls
        return cls

    def get(self, name: str | None = None) -> type[B]:
        """Return the class registered as `name`, or the first available one for `None`.

        Raises:
            ValueError: `name` is not registered.
            MissingDependencyError: `name` is `None` and no backend is installed.
        """
        if name is None:
            for cls in self:
                if cls.is_available():
                    return cls
            extras = ", ".join(sorted({c.extra for c in self}))
            msg = f"No {self._kind} is installed. Install one of the extras: {extras}"
            raise MissingDependencyError(msg)
        try:
            return self._classes[name]
        except KeyError:
            known = ", ".join(self._classes)
            msg = f"Unknown {self._kind} {name!r}. Known: {known}"
            raise ValueError(msg) from None

    def names(self, *, available_only: bool = False) -> list[str]:
        """Registered names, optionally only those whose packages are installed."""
        return [c.name for c in self if not available_only or c.is_available()]

    def __iter__(self) -> Iterator[type[B]]:
        return iter(self._classes.values())
