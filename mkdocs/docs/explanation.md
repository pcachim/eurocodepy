# Background & Design Philosophy

This section explains the *why* behind EurocodePy — its goals, design decisions, and
how the pieces fit together. Read this if you want to understand the library deeply
rather than just use it.

---

## Why EurocodePy was created

Structural engineers working in Python face a recurring problem: Eurocode calculations
are well-defined in the standards, but translating them into reliable, readable code is
repetitive and error-prone. Each project reinvents the same material property look-ups,
the same load combination logic, the same unit conversions.

EurocodePy aims to provide the missing layer of shared building blocks — small, composable
functions and classes that can be dropped into any project, notebook, or parametric model
without pulling in a large framework.

The design philosophy is:

- **Pragmatic over complete.** Not every clause of every part needs to be implemented.
  What matters is that the implemented parts are correct, well-tested, and easy to use.
- **Transparent.** Formulas follow the code clauses directly. Variable names mirror the
  standard notation (e.g. `fck`, `fyd`, `VRd_c`) so it is straightforward to trace a
  computation back to its source equation.
- **Composable.** Each module is independently useful. You can use `ec2` alone without
  importing `ec7`, or mix `ec1` load combinations with a custom section analysis.

---

## Architecture overview

```
eurocodepy/
├── dbase       ← JSON-backed material & section database
├── units       ← Unit system abstractions (SI, kN/mm, N/mm)
├── national_parameters  ← Portuguese / EU national annex data
├── ec1         ← EN 1991: load types, forces, combinations (ULS/SLS/ALS)
├── ec2         ← EN 1992: concrete, reinforcement, prestress; ULS + SLS
├── ec3         ← EN 1993: steel materials, profiles, connections
├── ec5         ← EN 1995: timber materials, ULS checks, SLS vibration
├── ec7         ← EN 1997: soils, bearing resistance, earth pressures
├── ec8         ← EN 1998: response spectra, national annex parameters
└── utils       ← Section properties, stress calculations
```

Each Eurocode module follows a consistent internal layout where it makes sense:

```
ecN/
├── __init__.py   ← public exports
├── materials.py  ← material classes and grade enumerations
├── uls/          ← Ultimate Limit State check functions
└── sls/          ← Serviceability Limit State check functions
```

---

## Material database

Material properties are stored in a JSON file bundled with the package. The `dbase`
module loads this file at import time and exposes the data through typed pandas
DataFrames and Python dataclasses. This approach means:

- Properties are easy to inspect and update without changing code.
- The same data is accessible both via the high-level material classes (e.g. `Concrete('C30/37')`)
  and directly via `dbase.db` for custom queries.

---

## Unit systems

Structural engineering practice uses several different unit systems. The `units` module
provides three pre-defined `UnitSystem` objects:

| Name | Force | Length | Pressure |
|------|-------|--------|----------|
| `SI` | N | m | Pa |
| `kN_mm` | kN | mm | kN/mm² = GPa |
| `N_mm` | N | mm | N/mm² = MPa |

Functions throughout the library accept numeric inputs; the caller is responsible for
passing values in a consistent unit system. The `UnitSystem` objects are provided as
a reference — they are not yet used to automatically convert inputs.

---

## Load combinations (EC1)

The `ec1.combos` module implements EN 1990 load combination logic using Python dataclasses
and enumerations. A `LoadCombinations` object takes a list of `Load` objects (each tagged
with a `LoadType`) and generates all required combinations for the requested limit state
(`CombinationType.ULS`, `SLS_K`, `SLS_FR`, `SLS_QP`, `ALS`, or `FLS`).

The combination factors (ψ₀, ψ₁, ψ₂) are looked up from a built-in table keyed on
`LoadType`. Custom ψ values are not yet supported.

---

## Seismic spectra (EC8)

The `ec8.spectrum` module supports both the standard Eurocode horizontal spectrum and
the Portuguese National Annex (two continental zones and Azores). Spectra are returned
as dictionaries of period–acceleration pairs that can be plotted with `draw_spectrum_ec8`
or exported to CSV with `write_spectrum_ec8`.

Key parameters follow the standard notation: `ag` (reference peak ground acceleration),
`S` (soil factor), `T_B`, `T_C`, `T_D` (corner periods). The behaviour factor `q` is
applied when generating a design (inelastic) spectrum.

---

## Status and roadmap

EurocodePy is **early-stage**. The APIs are functional but may change between releases
as the library matures. Contributions are welcome — see
[CONTRIBUTING_GUIDELINES.md](copyright.md) for how to get involved.

Areas actively being developed:

- EN 1992-1-1:2025 (second generation Eurocode 2) compatibility
- EN 1993 cross-section classification and member buckling
- EN 1995 connection design
- Expanded national annex support (Spain, France, Germany)

