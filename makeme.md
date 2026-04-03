# Build & Release Procedures for EurocodePy

This file documents all procedures for developing, building, testing, and publishing
the **EurocodePy** package, as well as building and deploying its documentation.

All commands assume you are at the **root of the repository** (the folder containing
`pyproject.toml`) unless otherwise noted.

---

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/) | Fast Python package manager & build tool | `pip install uv` or `curl -Lsf https://astral.sh/uv/install.sh \| sh` |
| Python ≥ 3.12 | Required runtime | Via `uv python install 3.12` or system installer |
| Git | Version control and GitHub deployment | System package manager |
| MkDocs + plugins | Documentation site generation | Installed automatically via `uv` (see below) |

---

## 1. Development Setup

### 1.1 Create and activate a virtual environment

```bash
# Create a project-local virtual environment using uv
uv venv

# Activate it (Linux / macOS)
source .venv/bin/activate

# Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### 1.2 Install the package in editable (development) mode

```bash
# Install the package itself plus all runtime dependencies
# The -e flag makes changes to src/ immediately visible without re-installing
uv pip install -e .
```

### 1.3 Install dev-only extras (linting, type-checking, pre-commit hooks)

```bash
# Installs ruff (linter/formatter), ty (type checker), and pre-commit
uv pip install -e ".[dev]"
```

### 1.4 Set up pre-commit hooks (optional but recommended)

```bash
# Installs hooks into .git/hooks so they run automatically on each commit
pre-commit install
```

---

## 2. Code Quality

### 2.1 Lint and format with Ruff

```bash
# Check for linting issues (does not modify files)
uv run ruff check src/

# Auto-fix safe issues
uv run ruff check --fix src/

# Format all source files (like Black, but faster)
uv run ruff format src/

# Show all available rules (useful when editing pyproject.toml [tool.ruff])
uv run ruff rules
```

### 2.2 Type-check with ty

```bash
# Run the type checker over the source tree
uv run ty check src/
```

---

## 3. Testing

### 3.1 Run the test file

```bash
# The project currently uses a standalone test script at the repo root
python test.py
```

> **Note:** Migrating to `pytest` is recommended for future growth.
> When ready, install it with `uv add --dev pytest` and run `uv run pytest`.

---

## 4. Build the Package

### 4.1 Build source distribution and wheel

```bash
# Produces dist/eurocodepy-<version>.tar.gz  (sdist)
#       and dist/eurocodepy-<version>-py3-none-any.whl  (wheel)
uv build
```

### 4.2 Verify the build artefacts

```bash
# List what was produced
ls dist/

# Optional: check the wheel contents
uv run python -c "import zipfile, glob; [print(n) for z in glob.glob('dist/*.whl') for n in zipfile.ZipFile(z).namelist()]"
```

---

## 5. Publish to PyPI

### 5.1 Publish to the real PyPI

```bash
# You will be prompted for your PyPI API token unless PYPI_TOKEN is set
uv publish

# Or pass the token explicitly:
uv publish --token $PYPI_TOKEN
```

### 5.2 Publish to TestPyPI first (recommended before a real release)

```bash
# Upload to the test index so you can verify the package before going live
uv publish --index-url https://test.pypi.org/legacy/ --token $TEST_PYPI_TOKEN

# Install from TestPyPI to verify the upload looks correct
pip install --index-url https://test.pypi.org/simple/ eurocodepy
```

### 5.3 Version bumping

The version lives in **two places** — keep them in sync:

| File | Location |
|------|----------|
| `pyproject.toml` | `[project] version = "YYYY.M.PATCH"` |
| `src/eurocodepy/__init__.py` | `__version__ = "YYYY.M.PATCH"` |

The project uses a **calendar versioning** scheme: `YYYY.M.PATCH`
(e.g. `2026.2.1` → `2026.2.2` for a patch, `2026.3.0` for a new month release).

---

## 6. Documentation

The documentation is built with [MkDocs](https://www.mkdocs.org/) using the
**Material** theme and **mkdocstrings** for auto-generated API reference pages.
All documentation source files live under `mkdocs/`.

### 6.1 Install documentation dependencies

```bash
# These packages are already listed in pyproject.toml [project.dependencies]
# so they are installed automatically in step 1.2 above.
# If you need to install them standalone:
uv add mkdocs mkdocs-material mkdocstrings mkdocstrings-python \
        mkdocs-gen-files mkdocs-literate-nav mkdocs-section-index
```

### 6.2 Preview documentation locally

```bash
# Start a live-reloading local server at http://127.0.0.1:8000
# Changes to docs/ or source docstrings reload automatically
cd mkdocs
mkdocs serve
```

### 6.3 Build the static documentation site

```bash
# Generates the static HTML site into mkdocs/site/
cd mkdocs
mkdocs build

# The output directory mkdocs/site/ is ready to be served or deployed
```

### 6.4 Deploy documentation to GitHub Pages

```bash
# Commit any outstanding changes first so the deployed docs match the repo
git add -A && git commit -m "docs: update documentation"
git push

# Then build and push to the gh-pages branch in one step
cd mkdocs
mkdocs gh-deploy

# This command:
#   1. Builds the site (same as mkdocs build)
#   2. Commits the output to the gh-pages branch
#   3. Pushes it to GitHub
#
# After a few seconds the live site is updated at:
#   https://pcachim.github.io/eurocodepy/
```

> **Important:** `mkdocs gh-deploy` must be run from inside the `mkdocs/` directory,
> not the repo root, because `mkdocs.yml` is located there.

---

## 7. Full Release Checklist

A step-by-step checklist for cutting a new release:

```
[ ] 1. Ensure all tests pass:          python test.py
[ ] 2. Run linter with no errors:      uv run ruff check src/
[ ] 3. Bump version in pyproject.toml
[ ] 4. Bump version in src/eurocodepy/__init__.py  (must match)
[ ] 5. Commit version bump:            git commit -m "chore: bump version to X.Y.Z"
[ ] 6. Tag the release:                git tag vX.Y.Z && git push --tags
[ ] 7. Build the package:              uv build
[ ] 8. (Optional) Test on TestPyPI:    uv publish --index-url https://test.pypi.org/legacy/
[ ] 9. Publish to PyPI:                uv publish
[ ] 10. Build & deploy docs:           cd mkdocs && mkdocs gh-deploy
[ ] 11. Create a GitHub Release on the tag with release notes
```

---

## 8. Directory Structure Reference

```
eurocodepy/
├── pyproject.toml            # Package metadata, dependencies, tool config
├── README.md                 # PyPI / GitHub landing page
├── makeme.md                 # This file — build & release procedures
├── CONTRIBUTING_GUIDELINES.md
├── CODE_OF_CONDUCT.md
├── LICENSE.md
├── MANIFEST.in               # Files to include in the source distribution
├── requirements_dev.txt      # Pinned dev dependencies (generated from .in file)
├── test.py                   # Standalone test / example script
├── src/
│   └── eurocodepy/           # Main package source
│       ├── __init__.py       # Public API surface; sets __version__
│       ├── dbase.py          # Material & load databases (JSON-backed)
│       ├── units.py          # Unit system helpers (SI, kN_mm, N_mm, …)
│       ├── national_parameters.py  # Portuguese / EU national annex data
│       ├── ec1/              # EN 1991 — Actions (loads, combinations)
│       ├── ec2/              # EN 1992 — Reinforced concrete design
│       ├── ec3/              # EN 1993 — Steel structure design
│       ├── ec5/              # EN 1995 — Timber structure design
│       ├── ec7/              # EN 1997 — Geotechnical design
│       ├── ec8/              # EN 1998 — Seismic design
│       └── utils/            # Cross-module helpers (section props, stress…)
└── mkdocs/
    ├── mkdocs.yml            # MkDocs configuration
    ├── docs/                 # Markdown source for the documentation site
    │   ├── index.md
    │   ├── tutorials.md
    │   ├── how-to-guides.md
    │   ├── explanation.md
    │   ├── modules/          # One page per Eurocode module
    │   └── reference/        # Auto-generated API reference (via mkdocstrings)
    ├── scripts/
    │   └── gen_ref_pages.py  # MkDocs hook that generates the reference pages
    └── site/                 # Built HTML output (git-ignored, created by mkdocs build)
```
