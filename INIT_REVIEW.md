# Review of the `__init__.py` files

Analysis only — no code changed. Overall the package works, but the `__init__`
files are inconsistent and a couple have real problems. Findings below, grouped
by severity.

## 1. Wrong docstrings (correctness — fix first)

Copy-paste left two package docstrings describing the wrong Eurocode:

- `ec1/__init__.py` → docstring says **"Eurocode 5 Timber Module"**. EC1 is
  *Actions on structures* (loads, combinations, snow, wind). The text is wrong.
- `ec3/__init__.py` → docstring says "Eurocode 3 Steel **Reinforcement**
  Module". EC3 is *steel structures*; "reinforcement" belongs to EC2.

These surface in generated docs and IDEs, so they mislead users directly.

## 2. Inconsistent re-export convention (the main "not solid" feeling)

There are three different styles across the files:

- **Explicit re-export** `from x import Y as Y` — top-level, `ec1`, `ec3`, `ec8`.
  This is the PEP 484 idiom type-checkers recognise; it is the good one.
- **Plain import + scattered `# noqa: F401`** — `ec2`, `ec7`, parts of others.
  Relies on a linter suppression to keep "unused" imports; easy to get wrong.
- **Star import** — `ec1/wind/__init__.py` does `from .pressure import *` (plus
  commented-out dead code). Star imports hide the public surface and defeat
  linters.

Recommendation: pick **one** convention (the `as` form) for every `__init__`,
and drop the star import in `ec1/wind`.

## 3. No `__all__` (implicit public API)

Only `ec5/sls/__init__.py` declares `__all__`. Everywhere else the public API is
whatever happens to be imported. Add an explicit `__all__` to each package so
`from eurocodepy.ecX import *` and the documented surface are intentional and
stable.

## 4. `ec3/uls/__init__.py` is a 429-line implementation module

It contains a `@dataclass SectionCheckResult` plus 8 functions (combined/buckling
checks) — real logic living inside `__init__.py`. This slows import, makes the
code hard to find, and is inconsistent with the other `uls` packages (which keep
logic in named modules like `beam.py`, `shear.py`). Move the implementation to
`ec3/uls/checks.py` (or similar) and leave `__init__.py` as a thin re-export.

## 5. `ec2/uls/__init__.py` problems

- `from eurocodepy import dbase` followed by `dbase = dbase` — a pointless
  self-assignment (presumably to silence "unused import"). Use
  `from eurocodepy import dbase as dbase`.
- **Silent name collisions**: `calc_asws`, `calc_vrd`, `calc_vrdc` are imported
  from **both** `shear` and `beam`. Whichever import runs last wins; the other
  is shadowed with no warning. If the two ever differ, callers get the wrong
  one. Import each name from a single, intended module (or alias them).

## 6. Parent ↔ child circular coupling

`ec2/__init__.py` imports from `eurocodepy.ec2.uls`, while `ec2/uls/__init__.py`
imports back from `eurocodepy.ec2` (`Concrete`, `ConcreteClass`, …). This works
only because of import ordering and is fragile — a small reordering or a new
import can produce a circular-import error. Have submodules import from the leaf
modules (`ec2.materials`) rather than from the parent package.

## 7. Heavy eager imports

`import eurocodepy` eagerly pulls in ec1–ec8, all materials, all steel profiles,
units, and national parameters. Consequences:

- A single broken/incompatible module (e.g. the `StrEnum` Python ≥ 3.11
  requirement) breaks the **entire** package import.
- Slower startup and more circular-import exposure.

Consider importing submodules lazily (e.g. PEP 562 module `__getattr__`) or at
least not re-exporting deep symbols at top level unless they are genuinely the
primary API.

## 8. Minor / cosmetic

- Top-level `version = "This is 'EurocodePy' version " + __version__`: a
  human sentence assigned to a `version` variable is surprising. Keep
  `__version__` as the canonical string; drop or rename the sentence.
- Empty `ec1/snow/__init__.py` vs `ec1/wind` doing star imports — pick a
  consistent approach (expose the snow API explicitly, like the others).
- Mixed copyright years across files (2024 / 2025 / 2026).
- `ec1/wind/__init__.py` has commented-out dead code (`# z_0 = …`).

## Suggested order

1. Fix the two wrong docstrings (ec1, ec3). (Trivial, user-facing.) — **DONE**
2. Move `ec3/uls/__init__.py` logic into a named module. — **DONE** (now in
   `ec3/uls/checks.py`; `__init__` re-exports with `__all__`).
3. Fix `ec2/uls` self-assignment + name collisions. — **DONE** (see below).
4. Standardise on the `as`-re-export convention and add `__all__` per package.
   — **DONE**: every re-export `__init__` now uses `import X as X` and declares
   `__all__` (top-level + ec1/ec2/ec3/ec5/ec7/ec8/utils and their sub-packages).
   Only `ec1/wind` (star import) and the empty `ec1/snow` remain — see item 5.
5. Replace the `ec1/wind` star import; remove dead code. — **DONE**: `ec1/wind`
   now imports the 8 `pressure` functions explicitly with `__all__` (the star
   import was also leaking `np`); removed the commented-out dead code. `ec1/snow`
   was an empty stub — gave it a docstring marking it a not-yet-implemented
   placeholder. No `import *` remains anywhere in the package.
6. Address the parent↔child coupling and (optionally) lazy imports.
   — **Decoupling DONE**: the only submodules that imported names from their
   parent package now import from the leaf `materials` modules instead —
   `ec2/uls/beam.py`, `ec5/uls/bending.py` (and `ec2/uls/__init__.py` earlier).
   No parent-package name imports remain in submodules (except the orphaned
   `crack.py`, below).
   — **Lazy imports: deferred.** Converting the eager top-level `__init__`
   (which re-exports many *names*, not just submodules) to PEP 562
   `__getattr__` is a large, error-prone change for the most critical file and
   needs runtime validation on Python ≥ 3.11. Recommended but not done here.

## Follow-up finding: `ec2/sls/crack.py` is orphaned and broken

`crack.py` is **not imported anywhere** (`ec2/sls/__init__.py` only exposes
`shrinkage` and `creep`), and it imports `ConcreteGrade` / `ReinforcementGrade`
from `eurocodepy.ec2` — names that **do not exist anywhere in the package**
(they were likely renamed to `ConcreteClass` / `ReinforcementClass`). So the
module would raise `ImportError` the moment it were imported. — **FIXED**: the
broken type-hint names were `ConcreteClass` / `ReinforcementClass` (renamed in
`ec2.materials`); updated the imports to read from the leaf `ec2.materials`, and
wired `crack` into `ec2/sls/__init__.py` so `crack_opening`, `is_cracked` and
`iscracked_annexLL` are now exposed. Needs runtime validation on Python ≥ 3.11.

## Follow-up finding: duplicated shear functions in `ec2/uls/beam.py`

While fixing the `ec2/uls` name collisions, I confirmed (AST comparison) that
`beam.py` **redefines its own copies** of `calc_vrd`, `calc_asws`, `calc_vrdc`
and `calc_vrdmax` — the executable logic is identical to `shear.py`, only
docstrings/formatting differ. So the collision was behaviourally harmless, but
the duplication is real: `beam.py` should `from .shear import …` those four
functions instead of carrying copies, so a future change to a shear formula
can't silently diverge between the two modules. — **DONE**: `beam.py` now imports
`calc_asws`, `calc_vrd`, `calc_vrdc`, `calc_vrdmax` from `shear` (its ~90 lines
of duplicate definitions removed). `shear.py` is the single source of truth.
Needs runtime validation on Python ≥ 3.11.
