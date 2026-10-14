# Eurocode 5 module: `ec5`

## Overview

The `ec5` module provides tools for the design of timber structures according to
EN 1995-1-1: material classes, modification factors, ULS checks and floor vibration. The ULS checks
exist for the 2004 edition (`ec5.uls`) and for the second generation (`ec5.uls2025`, EN 1995-1-1:2025,
clause 8); both have the same functions and can be swapped.

Units: forces in kN, moments in kNm, section dimensions in m, **effective lengths in mm**, strengths in MPa.

---

## Materials

### `Timber` and its products

```python
from eurocodepy.ec5.materials import SolidTimber, Glulam

t = SolidTimber("C24")
t.fmk      # characteristic bending strength [MPa]
t.ft0k     # tension parallel to grain
t.fc0k     # compression parallel to grain
t.fvk      # shear
t.E0mean   # mean modulus parallel to grain [MPa]
t.E0k      # 5th percentile modulus [MPa]
t.Gmean    # mean shear modulus [MPa]
t.rhok     # characteristic density [kg/m³]
t.rhom     # mean density [kg/m³]
t.safety   # γM (Table 2.3)

g = Glulam("GL28h")        # GL20h … GL32h (homogeneous) and GL20c … GL32c (combined)
```

| Class | Product |
|-------|---------|
| `SolidTimber` (alias `ST`, `Softwood`, `Hardwood`) | sawn timber, strength classes C and D |
| `Glulam` (alias `GL`) | glued laminated timber |
| `CLT`, `LVL` | not implemented (the grade tables are missing) |

### `ServiceClass` and `LoadDuration`

`ServiceClass`: `SC1`, `SC2`, `SC3`, `SC4`. `LoadDuration`: `Permanent`, `LongDuration`,
`MediumDuration`, `ShortDuration`, `Instantaneous`.

### `k_mod` and design values

```python
from eurocodepy.ec5.materials import ServiceClass, LoadDuration

kmod = t.k_mod(ServiceClass.SC1, LoadDuration.MediumDuration)       # 0.8 (Table 3.1)
d = t.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)   # fmd, ft0d, fc0d, fvd, fc90d, ft90d, kmod, safety
d["fmd"]                                                            # kmod·fmk/γM [MPa]
```

`GetTimberDesignValues(timber, combos, service_class=ServiceClass.SC1)` returns the design values of each
combination of a `Loads`: `kmod` is that of the shortest action in the combination (EN 1995-1-1, 3.1.3(2)),
`attributes["loadduration"]` of a `LoadCombination` overrides it, and serviceability combinations give
`{"design": False}`.

```python
from eurocodepy.ec1 import Load, LoadType, Loads
from eurocodepy.ec5.materials import GetTimberDesignValues

loads = Loads()
loads.add(Load("G", LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
loads.add(Load("W", LoadType.WIND, 0.0, 1.5, 0.6, 0.2, 0.0))
values = GetTimberDesignValues(t, loads.get_ULS_combos().values(), ServiceClass.SC2)
{name: v["kmod"] for name, v in values.items()}          # short-term kmod in the combinations with wind
```

---

## ULS checks — `ec5.uls`

### Section check (N, My, Mz, Vy, Vz, T)

```python
from eurocodepy.ec5.materials import SolidTimber, ServiceClass, LoadDuration
from eurocodepy.ec5.uls import TimberSectionInput, TimberForces, eurocode5_section_check
from eurocodepy.utils import RectangularCrossSection

section = RectangularCrossSection(0.10, 0.20)                       # b, h [m]
inp = TimberSectionInput(section, SolidTimber("C24"), ServiceClass.SC1, LoadDuration.MediumDuration,
                         l_0y=3000.0, l_0z=3000.0, l_0m=3000.0)     # effective lengths [mm]
r = eurocode5_section_check(inp, TimberForces(n_ed=-20.0, my_ed=5.0, vz_ed=8.0))   # n_ed < 0: compression
r.utilization, r.passed
r.util_bending_axial, r.util_shear, r.util_torsion
r.k_c, r.k_m
```

### Single checks

```python
from eurocodepy.ec5.uls import calc_k_c, calc_k_m, calc_k_red, calc_mcr

kc_y, kc_z = calc_k_c(3000.0, 3000.0, section, SolidTimber("C24"))   # column instability, §6.3.2
km = calc_k_m(3000.0, section, SolidTimber("C24"))                    # lateral-torsional buckling, §6.3.3
```

`check_bending_with_normal` (bending with axial force, §6.2.3 and §6.2.4) and `check_shear_with_torsion`
(§6.1.7) are the two parts of the section check and return a dictionary.
`get_safety_factor("timber")` gives γM for a product (`timber`, `glulam`, `lvl`, `clt`, …).

### Tapered and curved beams

`check_tapered_edge(m_ed, b, h, alpha, tension_on_cut_edge, timber)` (§6.4.2) and
`check_apex_zone(ApexInput(...), timber)` (§6.4.3) with the factors `calc_k_l`, `calc_k_p`, `calc_k_r`,
`calc_k_vol`, `calc_k_m_alpha`.

```python
from eurocodepy.ec5.materials import Glulam
from eurocodepy.ec5.uls import check_tapered_edge

r = check_tapered_edge(10.0, 0.10, 0.30, 0.10, True, Glulam("GL28h"))   # m_ed, b, h, α [rad]
r.util
```

---

## SLS checks — `ec5.sls`

### Vibration — `ec5.sls.vibration`

```python
from eurocodepy.ec5.sls.vibration import floor_freq, vel, vlim, a_from_b, b_from_a

f1 = floor_freq(l=5.0, EI=1.2e5, m=50.0)                          # fundamental frequency [Hz]
v = vel(f1, b=3.0, l=5.0, m=50.0, EIl=1.2e5, EIt=1.0e3)          # unit impulse velocity response [m/(N·s)]
a_from_b(100.0), b_from_a(1.0)                                    # Figure 7.2 coefficients a and b
```

`vlim(f1, b, damp)` is the limit of the velocity response. `ec5.sls.deformation` is a placeholder.

---

## Compliance

Calculations follow EN 1995-1-1:2004+A2:2014 and, in `uls2025`, EN 1995-1-1:2025.

## Further reading

- [EN 1995-1-1 — Design of timber structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-5-design-timber-structures)
