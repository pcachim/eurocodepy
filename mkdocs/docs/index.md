# EurocodePy

**EurocodePy** is a Python library for structural design calculations according to the
[Eurocode standards](https://eurocodes.jrc.ec.europa.eu/). It provides composable,
engineering-focused building blocks — reusable calculations, material databases, load
combinations, and section utilities — that you can drop into your own scripts and notebooks.

> Source code: <https://github.com/pcachim/eurocodepy>  
> Current version: **2026.2.1**

---

## What's included

### Material databases

Material characteristic and design values are stored in a bundled database and exposed
through typed Python classes. Supported materials:

| Material | Grades / Types |
|----------|---------------|
| Concrete | C20/25 to C90/105 |
| Reinforcement | B400A/B/C, B500A/B/C, B600–B700, A400NR, A500NR, A500EL |
| Prestressing steel | Y1770, Y1860, and others |
| Structural steel | S235, S275, S355, S450 |
| Timber | Softwood (C), Hardwood (D), Glulam (GL), CLT, LVL |
| Bolts | Grades 4.6 through 10.9 |

### Steel section profiles

European hot-rolled profiles are available as named enumerations and dataclasses:

- **I-profiles:** IPE, HEA, HEB, HEM
- **Hollow sections:** CHS (circular), RHS (rectangular), SHS (square)

### Eurocode modules

| Module | Standard | Coverage |
|--------|----------|----------|
| `ec1` | EN 1991 | Load combinations (ULS, SLS, ALS), wind, snow, load types |
| `ec2` | EN 1992 | Concrete materials, ULS beam/shear/shell/punching, SLS crack/creep/shrinkage, fire |
| `ec3` | EN 1993 | Steel materials, profiles, bolted and welded connections, ULS checks |
| `ec5` | EN 1995 | Timber materials, ULS bending/shear, SLS vibration/deformation |
| `ec7` | EN 1997 | Bearing resistance, earth pressures, soil materials |
| `ec8` | EN 1998 | Design response spectra, national annex parameters (EU, PT) |
| `utils` | — | Section properties, principal stresses, stress invariants |

### National Annex support

Portuguese municipal data (seismic zones, wind zones) is bundled and accessible via the
`NationalParams` class and helper functions `seismic_get_params` / `wind_get_params`.

---

## Quick start

```python
import eurocodepy as ec

# --- Concrete material (EN 1992) ---
concrete = ec.Concrete('C30/37')
print(concrete.fck)   # characteristic compressive strength [MPa]
print(concrete.fcd)   # design compressive strength [MPa]

# --- Steel material (EN 1993) ---
steel = ec.Steel('S355')
print(steel.fy)   # yield strength [MPa]

# --- Timber material (EN 1995) ---
timber = ec.Timber('C24')
print(timber.fmk)  # characteristic bending strength [MPa]

# --- Design response spectrum (EN 1998, Portuguese NA) ---
spec = ec.spectrum.get_spectrum_ec8(
    locale='PT', code='PT-1', imp_class='II',
    soil='C', zone='1_2', behaviour=3.0
)
ec.spectrum.draw_spectrum_ec8(spec, show=True)

# --- Load combinations (EN 1990) ---
from eurocodepy.ec1 import Load, LoadType, LoadCombinations, CombinationType
loads = [
    Load('G1', LoadType.PERMANENT, 10.0),
    Load('Q1', LoadType.LIVE, 5.0),
    Load('W1', LoadType.WIND, 3.0),
]
combos = LoadCombinations(loads)
uls = combos.get(CombinationType.ULS)
```

---

## Installation

```bash
# From PyPI
pip install eurocodepy

# With uv
uv add eurocodepy

# Latest development version from GitHub
pip install git+https://github.com/pcachim/eurocodepy.git
```

Requires **Python ≥ 3.12**.

---

## Navigation

- [Tutorials](tutorials.md) — step-by-step worked examples
- [How-to guides](how-to-guides.md) — recipes for common tasks
- [Modules](modules/ec1.md) — module-by-module feature reference
- [Code Reference](reference/) — auto-generated API documentation
- [Background](explanation.md) — design decisions and architecture
- [License & Contributing](copyright.md)

---

## Support

Open an issue or start a discussion on GitHub:
<https://github.com/pcachim/eurocodepy/issues>

## Disclaimer

This software is intended for **educational, research, and preliminary design** purposes only.
It is not a certified engineering tool. Always verify critical calculations against the
official Eurocode standards and applicable national annexes before use in final designs.
The authors assume no liability for design decisions made using this library.

## Acknowledgements

Eurocodes and National Annexes are published by their respective standards bodies (CEN and
national SDOs). This project is not affiliated with CEN or any national standards organization.