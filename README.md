<!-- docs:skip-start -->
<p align="center">
  <img src="https://raw.githubusercontent.com/pcachim/eurocodepy/master/mkdocs/docs/assets/logo.svg?v=2" alt="eurocodepy" width="360">
</p>

<!-- docs:skip-end -->
# eurocodepy

[![PyPI version](https://img.shields.io/pypi/v/eurocodepy)](https://pypi.org/project/eurocodepy/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](LICENSE.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23371032.svg)](https://doi.org/10.5281/zenodo.23371032)

A Python library for structural design calculations according to the **Eurocode** standards.
`eurocodepy` provides composable, engineering-focused building blocks — material databases,
load combinations, section utilities, and code-compliant design checks — that you can drop
into scripts, notebooks, or larger analysis tools.

> **Documentation:** <https://pcachim.github.io/eurocodepy/>  
> **Source:** <https://github.com/pcachim/eurocodepy>  
> **PyPI:** <https://pypi.org/project/eurocodepy/>  
> **Changelog:** <https://github.com/pcachim/eurocodepy/blob/master/CHANGELOG.md>

---

## What's included

### Material databases

Characteristic and design values are stored in a bundled database and surfaced through
typed Python classes. Variable names follow standard Eurocode notation (`fck`, `fyd`,
`E0mean`, …) so calculations trace directly back to the clauses that define them.

| Material | Available grades |
|----------|-----------------|
| Concrete | C12/15 to C90/105 (EN 1992-1-1:2004) · C12/15 to C100/115 (EN 1992-1-1:2023, Table 5.1) |
| Reinforcement | B400A/B/C · B450A/B/C · B500A/B/C · B550A/B/C · B600A/B/C · B700A/B/C · A400NR · A500NR · A500EL · A400NRSD · A500NRSD |
| Prestressing steel | Y1570 to Y2160: wires, strands and bars (class and diameter, e.g. `Y1860S7 12.5`) |
| Structural steel | S235 · S275 · S355 · S420 · S450 · S460 and their qualities (JR, N, NL, M, ML, W, Q, QL) |
| Timber (solid) | C16 · C18 · C24 · C30 · D24 · D30 · D40 · D50 · D60 · D70 |
| Timber (glulam) | GL20h to GL32h · GL20c to GL32c |
| Bolts | Grades 4.6 · 5.6 · 6.6 · 6.8 · 8.8 · 9.8 · 10.9 · 12.9 |

### Steel profiles

Standard European hot-rolled profiles are available as dictionaries of dataclasses exposing the
catalogue properties (`A`, `Iy`, `Iz`, `Wpl_y`, `IT`, `Iw`, … in cm):

- **I-profiles:** IPE, HEA, HEB, HEM
- **Hollow sections:** CHS (circular), RHS (rectangular), SHS (square)

### Eurocode modules

| Module | Standard | Key functionality |
|--------|----------|------------------|
| `ec1` | EN 1991 / EN 1990 | Load types, force resultants, ULS / SLS / ALS load combinations, wind (EN 1991-1-4) |
| `ec2` | EN 1992-1-1 (2004 and 2023), EN 1992-2 | Concrete, reinforcement and prestress; ULS bending, shear, torsion, punching, detailing; membranes, slabs and shells (Annex G, Annex LL, sandwich model); SLS crack width; creep, shrinkage and relaxation (Annex B); fire |
| `ec3` | EN 1993-1-1, 1-8 | Steel materials; I, CHS, RHS, SHS profiles; section classification, section and member checks; bolted and pinned connections, weld groups |
| `ec5` | EN 1995-1-1 (2004 and 2025) | Timber materials (solid, glulam); `kmod`; ULS bending, shear, tapered and curved beams; SLS floor vibration |
| `ec7` | EN 1997-1, EN 1998-5 | Soil materials; shallow foundation bearing resistance; seismic bearing resistance; earth pressure coefficients |
| `ec8` | EN 1998-1 | Elastic and design response spectra; Portuguese and standard CEN national annexes; spectrum plotting and export |
| `utils` | — | Cross sections, section properties of reinforced sections, principal stresses, stress invariants |

### Editions and National Annexes

Functions take `edition=` (the 2004 default, or `"2023"` for the second-generation Eurocode 2) and
`annex=` (a country code). A National Annex is one JSON file of patches over the recommended values, and
`register_annex` adds your own. Portuguese data (seismic and wind zones, live loads) is bundled; the Portuguese
parameters of EN 1992-1-1:2023 are **not** there yet, so `annex="PT"` gives the recommended values for concrete.
Seismic and wind data of Portuguese municipalities are available through `NationalParams`, `seismic_get_params`
and `wind_get_params`.

### Calculation reports and units

Most checks take `trace=` with a `CalcReport` that records every step with its clause and formula, and exports
it as a dictionary or Markdown. `eurocodepy.units` has unit systems (`SI`, `kN_m`, `kN_mm`, `N_mm`) used by the
force and stress containers of `ec1`; the calculation functions work in the fixed units given in their documentation.

---

## Quick start

```python
import eurocodepy as ec

# ── Concrete and reinforcement (EN 1992) ───────────────────────────────────
c = ec.Concrete('C30/37')
r = ec.Reinforcement('B500B')
print(c.fck, c.fcd, c.Ecm)           # 30 MPa, 20 MPa, 33 000 MPa
print(r.fyk, r.fyd)                  # 500 MPa, ~434.8 MPa

# The same concrete with the second-generation code: fcd = ηcc·ktc·fck/γc
c23 = ec.ec2.get_concrete('C50/60', edition='2023', loading='other')
print(c23.eta_cc, c23.k_tc, c23.fcd)

# ── Bending and shear of a rectangular beam (EN 1992-1-1:2004) ─────────────
# m, cm², kNm, MPa (see the documentation of each function for its units)
MRd, eps_s, x = ec.ec2.calc_mrd(b=0.30, d=0.46, ast=8.04, fcd=c.fcd, fyd=r.fyd)
from eurocodepy.ec2.uls.shear import calc_vrdc
vrd_min, vrd_c, vrd = calc_vrdc(bw=0.30, d=0.46, fck=30, g_c=1.5, rho_l=0.0117)
print(f"MRd = {MRd:.1f} kNm, VRd,c = {vrd:.1f} kN")

# ── Shear check of EN 1992-1-1:2023, clause 8.2 ─────────────────────────────
from eurocodepy.ec2 import uls2023
shear = uls2023.eurocode2_shear_check(
    uls2023.ShearInput(b=0.3, d=0.5, fck=30, fyk=500, as_long=0.0015), v_ed=150.0)
print(shear.mode, shear.asw_s)       # 'stirrups', Asw/s [m²/m]

# ── Structural steel (EN 1993) ─────────────────────────────────────────────
steel = ec.Steel('S355')
profile = ec.ec3.ProfilesI['IPE300']
print(steel.fyk, profile.A, profile.Iy)      # 355 MPa, cm², cm⁴
check = ec.ec3.section_check_profile(
    profile, steel.fyk, ec.ec3.SectionForces(my_ed=100.0, vz_ed=80.0))
print(f"utilization = {check.utilization:.2f}")

# ── Timber (EN 1995) ───────────────────────────────────────────────────────
from eurocodepy.ec5.materials import SolidTimber, ServiceClass, LoadDuration
timber = SolidTimber('C24')
kmod = timber.k_mod(ServiceClass.SC1, LoadDuration.MediumDuration)
print(timber.fmk, kmod, timber.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)['fmd'])

# ── Load combinations (EN 1990) ────────────────────────────────────────────
from eurocodepy.ec1 import Load, LoadType, Loads
loads = Loads()                      # γ favourable, γ unfavourable, ψ0, ψ1, ψ2
loads.add(Load('G', LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
loads.add(Load('Q', LoadType.LIVE,      0.0, 1.50, 0.7, 0.5, 0.3))
loads.add(Load('W', LoadType.WIND,      0.0, 1.50, 0.6, 0.2, 0.0))
for name in loads.get_ULS_combos():
    print(name)

# ── Seismic spectrum (EN 1998, Portuguese NA) ──────────────────────────────
spec = ec.spectrum.get_spectrum_ec8(
    locale='PT', code='PT1', imp_class='II',
    soil='C', zone='1_2', behaviour=3.0,
)
ec.spectrum.draw_spectrum_ec8(spec, show=False)       # show=True opens the window
ec.spectrum.write_spectrum_ec8(spec, filename='spectrum.csv')

# ── Shallow foundation bearing resistance (EN 1997): angles in radians ─────
import numpy as np
from eurocodepy.ec7 import bearing_resistance
Rd = bearing_resistance(Bx=1.5, By=2.0, Hx=20, Hy=0, N=200,
                        phi=np.radians(30.0), gamma=18.0, q=0.0, c=0.0)
print(f"Rd = {Rd:.1f} kPa")                            # bearing stress

# ── Creep coefficient (EN 1992-1-1:2023, Annex B) ──────────────────────────
from eurocodepy.ec2.sls.creep import creep_coef
phi_t = creep_coef(t=18278, t0=28, fcm28=38.0, RH=60, hn=200, t0_T=28, concrete_class='CN')
print(f"φ(50 y, 28 d) = {phi_t:.2f}")
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

<!-- docs:skip-start -->
## Documentation

Full documentation — worked tutorials, how-to guides, a page per module and the API reference — is at:

**<https://pcachim.github.io/eurocodepy/>**
<!-- docs:skip-end -->

---

## Contributing

Contributions are welcome. For significant changes please open an issue first to
discuss the approach.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push and open a Pull Request

Please follow the existing code style (enforced by `ruff`) and include tests where
applicable. See [CONTRIBUTING_GUIDELINES.md](CONTRIBUTING_GUIDELINES.md) for more detail.

---

## License

GNU Lesser General Public License v3.0 (LGPLv3) — see [LICENSE.md](LICENSE.md) and [COPYING](COPYING) for the full text.

---

## Disclaimer

This software is intended for **educational and research** purposes only. It is not a
certified engineering tool and must not be used for final structural designs. Always
verify calculations against the official Eurocode standards and applicable national
annexes, and have final designs reviewed and approved by a qualified structural
engineer. The authors assume no liability for design decisions made using this library.

This disclaimer is in addition to, and does not limit, the warranty disclaimer in the
LGPLv3 license (see [LICENSE.md](LICENSE.md)).

---

## Acknowledgements

Eurocodes and National Annexes are published by CEN and the respective national
standards bodies. This project is not affiliated with CEN or any national standards
organization.
