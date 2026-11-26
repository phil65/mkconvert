"""Benchmark the installed Markdown parsers on the files in `cases/`.

Usage: `uv run python -m benchmark.bench [case ...]`
"""

from pathlib import Path
import sys
import time
from typing import TYPE_CHECKING

from mkconvert import MarkdownOptions, get_parser, list_parsers


if TYPE_CHECKING:
    from collections.abc import Callable


CASES_DIR = Path(__file__).parent / "cases"
OPTIONS = MarkdownOptions.gfm(footnotes=True)


def load_cases(names: list[str] | None = None) -> dict[str, str]:
    """Load the benchmark cases, optionally only those named in `names`."""
    cases = {p.stem: p.read_text(encoding="utf-8") for p in sorted(CASES_DIR.glob("*.txt"))}
    return {k: v for k, v in cases.items() if not names or k in names}


def time_ms(convert: Callable[[str], str], text: str, iterations: int) -> float:
    """Average time of `convert(text)` in milliseconds."""
    convert(text)  # warm up
    start = time.perf_counter()
    for _ in range(iterations):
        convert(text)
    return (time.perf_counter() - start) * 1000 / iterations


def main() -> None:
    """Benchmark every installed parser on every case and print a summary."""
    cases = load_cases(sys.argv[1:])
    iterations = 20
    totals: dict[str, float] = {}
    for name in list_parsers(available_only=True):
        # Same options everywhere; parsers lacking some (e.g. autolinks) just skip them.
        parser = get_parser(name, OPTIONS, on_unsupported="ignore")
        totals[name] = 0.0
        for case, text in cases.items():
            ms = time_ms(parser.convert, text, iterations)
            totals[name] += ms
            print(f"{name:<18} {case:<22} {ms:8.3f} ms")

    fastest = min(totals.values())
    print(f"\n{'Parser':<18} | {'Total (ms)':>10} | Relative")
    print("-" * 42)
    for name, total in sorted(totals.items(), key=lambda kv: kv[1]):
        print(f"{name:<18} | {total:10.3f} | {total / fastest:6.1f}x")


if __name__ == "__main__":
    main()
