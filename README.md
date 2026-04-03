# eurocodepy

[![PyPI version](https://img.shields.io/pypi/v/eurocodepy)](https://pypi.org/project/eurocodepy/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

A Python library for structural design calculations according to the **Eurocode** standards.
`eurocodepy` provides composable, engineering-focused building blocks — material databases,
load combinations, section utilities, and code-compliant design checks — that you can drop
into scripts, notebooks, or larger analysis tools.

> **Documentation:** <https://pcachim.github.io/eurocodepy/>  
> **Source:** <https://github.com/pcachim/eurocodepy>  
> **PyPI:** <https://pypi.org/project/eurocodepy/>

---

## What's included

### Material databases

Characteristic and design values are stored in a bundled database and surfaced through
typed Python classes. Variable names follow standard Eurocode notation (`fck`, `fyd`,
`E0mean`, …) so calculations trace directly back to the clauses that define them.

| Material | Available grades |
|----------|-----------------|
| Concrete | C20/25 · C25/30 · C30/37 · C35/45 · C40/50 · C45/55 · C50/60 · C55/67 · C60/75 · C70/85 · C80/95 · C90/105 |
| Reinforcement | B400A/B/C · B500A/B/C · B600A/B/C · B700A/B/C · A400NR · A500NR · A500EL · A400NRSD · A500NRSD |
| Prestressing steel | Y1770 · Y1860 and others |
| Structural steel | S235 · S275 · S355 · S450 |
| Timber (solid) | Softwood C14–C50 · Hardwood D18–D70 |
| Timber (engineered) | Glulam GL24h–GL32h/c · CLT · LVL |
| Bolts | Grades 4.6 · 5.6 · 6.8 · 8.8 · 10.9 |

### Steel profiles

Standard European hot-rolled profiles are available as named dataclasses exposing all
geometric properties (`A`, `Iy`, `Iz`, `Wpl_y`, `it`, `Iw`, …):

- **I-profiles:** IPE, HEA, HEB, HEM
- **Hollow sections:** CHS (circular), RHS (rectangular), SHS (square)

### Eurocode modules

| Module | Standard | Key functionality |
|--------|----------|------------------|
| `ec1` | EN 1991 / EN 1990 | Load types, force resultants, ULS / SLS / ALS load combinations |
| `ec2` | EN 1992-1-1 | Concrete & reinforcement materials; ULS beam bending, shear, shell/membrane reinforcement, punching; SLS crack width, creep, shrinkage; fire |
| `ec3` | EN 1993-1-1 | Steel materials; I, CHS, RHS, SHS profiles; bolted and welded connections |
| `ec5` | EN 1995-1-1 | Timber materials (solid, glulam, CLT, LVL); `kmod`; ULS bending & shear; SLS floor vibration |
| `ec7` | EN 1997-1 | Soil materials; shallow foundation bearing resistance; seismic bearing resistance; active/passive earth pressure coefficients |
| `ec8` | EN 1998-1 | Elastic and design response spectra; Portuguese and standard CEN national annexes; spectrum plotting and CSV export |
| `utils` | — | Section properties, principal stresses, stress invariants |

### National Annex support

Portuguese municipal seismic and wind data is bundled and accessible through
`NationalParams`, `seismic_get_params`, and `wind_get_params`.

---

## Quick start

```python
import eurocodepy as ec

# ── Concrete (EN 1992) ─────────────────────────────────────────────────────
c = ec.Concrete('C30/37')
print(c.fck, c.fcd, c.Ecm)          # 30 MPa, ~20 MPa, ~32 800 MPa

# ── Reinforcement ──────────────────────────────────────────────────────────
r = ec.Reinforcement('B500B')
print(r.fyk, r.fyd)                  # 500 MPa, ~434.8 MPa

# ── Structural steel (EN 1993) ─────────────────────────────────────────────
steel   = ec.Steel('S355')
profile = ec.ec3.materials.ProfileI('IPE300')
print(steel.fy, profile.A, profile.Iy)

# ── Timber (EN 1995) ───────────────────────────────────────────────────────
from eurocodepy.ec5 import SolidTimber, ServiceClass, LoadDuration
timber = SolidTimber('C24')
kmod   = timber.k_mod(ServiceClass.SC1, LoadDuration.Medium)
print(timber.fmk, kmod)              # 24 MPa, 0.8

# ── Load combinations (EN 1990) ────────────────────────────────────────────
from eurocodepy.ec1 import Load, LoadType, LoadCombinations, CombinationType
combos = LoadCombinations([
    Load('G', LoadType.PERMANENT, gk=10.0),
    Load('Q', LoadType.LIVE,      qk=5.0),
    Load('W', LoadType.WIND,      qk=3.0),
])
for c in combos.get(CombinationType.ULS):
    print(c)

# ── Seismic spectrum (EN 1998, Portuguese NA) ──────────────────────────────
spec = ec.spectrum.get_spectrum_ec8(
    locale='PT', code='PT-1', imp_class='II',
    soil='C', zone='1_2', behaviour=3.0,
)
ec.spectrum.draw_spectrum_ec8(spec, show=True)
ec.spectrum.write_spectrum_ec8(spec, filename='spectrum.csv')

# ── Concrete shear check (EN 1992) ─────────────────────────────────────────
from eurocodepy.ec2.uls.shear import calc_vrdc
VRd_c = calc_vrdc(b_w=300, d=460, As=1608, fck=30)
print(f"VRd,c = {VRd_c/1e3:.1f} kN")

# ── Shallow foundation bearing resistance (EN 1997) ────────────────────────
from eurocodepy.ec7 import bearing_resistance
Rd = bearing_resistance(Bx=1.5, By=2.0, Hx=20, Hy=0, N=200,
                        phi=30.0, gamma=18.0, q=0.0, c=0.0)
print(f"Rd = {Rd:.1f} kN")

# ── Creep coefficient (EN 1992-1-1:2025) ──────────────────────────────────
from eurocodepy.ec2.sls.creep import creep_coef
phi = creep_coef(fck=30, RH=60, h0=200, t0=28, t=18250)
print(f"φ(∞,28) = {phi:.2f}")
```

---

## Installation

```shell
# Stable release from PyPI
pip install eurocodepy

# With uv (recommended)
uv add eurocodepy

# Latest development version from GitHub
pip install git+https://github.com/pcachim/eurocodepy.git
```

Requires **Python ≥ 3.12**.

---

## Documentation

Full documentation — API reference, worked tutorials, and how-to guides — is at:

**<https://pcachim.github.io/eurocodepy/>**

---

## Contributing

Contributions are welcome. For significant changes please open an issue first to
discuss the approach.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push and open a Pull Request

Please follow the existing code style (enforced by `ruff`) and include tests where
applicable. See `CONTRIBUTING_GUIDELINES.md` for more detail.

---

## License

MIT — see [LICENSE.md](LICENSE.md) for the full text.

---

## Disclaimer

This software is intended for **educational, research, and preliminary design** purposes
only. It is not a certified engineering tool. Always verify critical calculations against
the official Eurocode standards and applicable national annexes before use in final
designs. The authors assume no liability for design decisions made using this library.

---

## Acknowledgements

Eurocodes and National Annexes are published by CEN and the respective national
standards bodies. This project is not affiliated with CEN or any national standards
organization.
