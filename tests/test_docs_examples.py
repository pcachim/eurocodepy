"""Run the Python blocks of the documentation (``mkdocs/docs``) so the examples cannot drift from the code.

The blocks of a page run in order and share one namespace, as a reader would run them, and every page must run
clean. If an example cannot run yet, list its page and block number (1-based, in page order) in ``KNOWN_BROKEN``;
the test then fails as soon as the block starts working, so the list only shrinks.
"""
import re
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "mkdocs" / "docs"
README = ROOT / "README.md"          # also the home page of the site (mkdocs/scripts/gen_index.py)
BLOCK = re.compile(r"```python\n(.*?)```", re.S)

KNOWN_BROKEN: dict[str, set[int]] = {}


def _pages() -> list[Path]:
    pages = sorted(p for p in DOCS.rglob("*.md") if p.name not in {"STYLE_GUIDE.md", "clauses.md"})
    return ([README] if README.is_file() else []) + pages


def _name(page: Path) -> str:
    return page.name if page == README else str(page.relative_to(DOCS))


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
@pytest.mark.parametrize("page", _pages(), ids=_name)
def test_documentation_examples_run(page, tmp_path, monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    monkeypatch.chdir(tmp_path)        # the examples write files
    failed = _run(page)
    expected = KNOWN_BROKEN.get(_name(page), set())
    assert failed == expected, (
        f"{_name(page)}: blocks that fail {sorted(failed)}, expected {sorted(expected)} "
        "(update KNOWN_BROKEN if a block was fixed)")


@pytest.mark.parametrize("page", _pages(), ids=_name)
def test_code_fences_are_balanced(page):
    """An unclosed or stray fence turns the prose into code (and the code into prose) without any block failing."""
    fences = [(n, line.strip()) for n, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1)
              if line.lstrip().startswith("```")]
    for i, (n, text) in enumerate(fences):
        if text != "```":                       # a fence with a language can only open a block
            assert i % 2 == 0, f"{_name(page)}:{n}: {text!r} where a block is still open"
    assert len(fences) % 2 == 0, f"{_name(page)}: unclosed code fence"


def test_home_page_is_built_from_the_readme():
    """``gen_index.py`` turns the README into ``index.md``: what is only for GitHub goes, the navigation comes."""
    import importlib.util
    import sys
    import types

    script = ROOT / "mkdocs" / "scripts" / "gen_index.py"
    if not script.is_file():
        pytest.skip("the documentation scripts are not in this checkout")

    class FakeFile:
        written = ""

        def __init__(self, *args):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def write(self, text):
            FakeFile.written = text

    fake = types.ModuleType("mkdocs_gen_files")
    fake.open = FakeFile
    sys.modules["mkdocs_gen_files"] = fake              # the script writes the page through this module
    try:
        spec = importlib.util.spec_from_file_location("gen_index_under_test", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        del sys.modules["mkdocs_gen_files"]
    assert FakeFile.written.startswith("# eurocodepy") and "## Navigation" in FakeFile.written   # the real README
    readme = (
        "# Title\n\nSee [the license](LICENSE.md) and [Python](https://python.org).\n\n"
        "<!-- docs:skip-start -->\n## Documentation\n\nonly for GitHub\n<!-- docs:skip-end -->\n"
        "## Contributing\n\nText.\n")
    page = module.build_index(readme)
    assert "only for GitHub" not in page and "docs:skip" not in page
    assert "](https://github.com/pcachim/eurocodepy/blob/master/LICENSE.md)" in page
    assert "](https://python.org)" in page
    assert page.index("## Navigation") < page.index("## Contributing")
    assert "(tutorials.md)" in page
    assert page.startswith("# Title")
    # a README without a heading (its logo carries the name) gets one on the site
    assert module.build_index("Text\n\n## Contributing\n").startswith("# eurocodepy\n")
    assert module.build_index("# Own title\n\n## Contributing\n").startswith("# Own title")
    with pytest.raises(ValueError, match="Contributing"):
        module.build_index("# no contributing section")
    assert "docs:skip-start" in README.read_text(encoding="utf-8")    # the markers the script relies on exist
