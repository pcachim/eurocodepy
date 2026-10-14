"""Run the Python blocks of the documentation (``mkdocs/docs``) so the examples cannot drift from the code.

The blocks of a page run in order and share one namespace, as a reader would run them, and every page must run
clean. If an example cannot run yet, list its page and block number (1-based, in page order) in ``KNOWN_BROKEN``;
the test then fails as soon as the block starts working, so the list only shrinks.
"""
import re
import warnings
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "mkdocs" / "docs"
BLOCK = re.compile(r"```python\n(.*?)```", re.S)

KNOWN_BROKEN: dict[str, set[int]] = {}


def _pages() -> list[Path]:
    return sorted(p for p in DOCS.rglob("*.md") if p.name not in {"STYLE_GUIDE.md", "clauses.md"})


def _run(page: Path) -> set[int]:
    namespace: dict = {"__name__": "docblock"}
    failed: set[int] = set()
    text = page.read_text(encoding="utf-8")
    for n, match in enumerate(BLOCK.finditer(text), start=1):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                exec(compile(match.group(1), f"{page.name}[{n}]", "exec"), namespace)  # noqa: S102
        except Exception:  # noqa: BLE001
            failed.add(n)
    return failed


@pytest.fixture(autouse=True)
def _clean_annexes():
    import eurocodepy as ec

    before = set(ec.available_annexes())
    yield
    for code in set(ec.available_annexes()) - before:
        ec.unregister_annex(code)


@pytest.mark.skipif(not DOCS.is_dir(), reason="the documentation is not in this checkout")
@pytest.mark.parametrize("page", _pages(), ids=lambda p: str(p.relative_to(DOCS)))
def test_documentation_examples_run(page, tmp_path, monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    monkeypatch.chdir(tmp_path)        # the examples write files
    failed = _run(page)
    expected = KNOWN_BROKEN.get(str(page.relative_to(DOCS)), set())
    assert failed == expected, (
        f"{page.relative_to(DOCS)}: blocks that fail {sorted(failed)}, expected {sorted(expected)} "
        "(update KNOWN_BROKEN if a block was fixed)")


@pytest.mark.parametrize("page", _pages(), ids=lambda p: str(p.relative_to(DOCS)))
def test_code_fences_are_balanced(page):
    """An unclosed or stray fence turns the prose into code (and the code into prose) without any block failing."""
    fences = [(n, line.strip()) for n, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1)
              if line.lstrip().startswith("```")]
    for i, (n, text) in enumerate(fences):
        if text != "```":                       # a fence with a language can only open a block
            assert i % 2 == 0, f"{page.relative_to(DOCS)}:{n}: {text!r} where a block is still open"
    assert len(fences) % 2 == 0, f"{page.relative_to(DOCS)}: unclosed code fence"
