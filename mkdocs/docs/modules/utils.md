# Utilities module: `utils`

## Overview

The `utils` module provides cross-cutting helper functions for geometric, mechanical,
and mathematical operations commonly needed in structural calculations. It is used
internally throughout EurocodePy and is also part of the public API.

---

## Cross sections — `utils.crosssection`

`RectangularCrossSection(width, height)` and `CircularCrossSection(diameter)` give the geometric
properties of a section (lengths in the unit of the arguments).

```python
from eurocodepy.utils import RectangularCrossSection, CircularCrossSection

r = RectangularCrossSection(0.30, 0.60)       # m
r.area, r.inertia_y, r.inertia_z               # A, Iy, Iz
r.bend_mod_y, r.bend_mod_z                     # Wy, Wz
r.radius_y, r.radius_z                         # radii of gyration
r.torsional_inertia, r.torsion_modulus, r.polar_inertia
r.shape                                        # CrossSectionShape member

CircularCrossSection(0.40).area
```

These objects are what the EC5 checks (`ec5.uls`) take as `section`.

---

## Reinforced and prestressed sections — `utils.section_properties`

`calc_section_rectangular` and `calc_section_T` return the uncracked and the cracked
properties (area, centroid, inertia, section moduli, neutral axis) of a section with passive and
prestressed reinforcement, with the steel homogenised by `alpha_Es` and `alpha_Ep`. The arguments
are consistent units (here m, m², kNm and kN). `calc_section_T_uncrack` and `calc_section_T_crack`
give each of them separately.

```python
import numpy as np
from eurocodepy.utils import calc_section_rectangular

arr = lambda *v: np.array(v)
uncracked, cracked = calc_section_rectangular(
    h=0.50, b=0.30,
    A_s=arr(8.0e-4), A_sc=arr(0.0), A_p=arr(0.0),      # tension, compression, prestressing steel
    ds=arr(0.46), dsc=arr(0.04), dp=arr(0.50),        # their distances to the top fibre
    alpha_Es=15.0, alpha_Ep=15.0,
    M=arr(150.0), P=arr(0.001),
)
uncracked["Area"], uncracked["Inertia"]
cracked["NeutralAxis"], cracked["Inertia"], cracked["zGs"], cracked["zGi"]
```

---

## Stress calculations — `utils.stress`

The six components of the stress tensor are `sigxx, sigyy, sigzz, sigxy, sigyz, sigzx`.

```python
from eurocodepy.utils import stress

# Principal stresses (ascending) and the normalised principal directions (columns)
values, vectors = stress.principals(10.0, 5.0, 0.0, 2.0, 0.0, 0.0)

# Principal vectors scaled by the principal stresses
stress.principal_vectors(10.0, 5.0, 0.0, 2.0, 0.0, 0.0)

# Invariants: I1, J2, J3, mean stress, equivalent (von Mises) stress, Lode r, z, θ, cos 3θ, triaxiality
i1, j2, j3, mean, eqv, lode_r, lode_z, lode_theta, cos3t, triax = stress.invariants(
    10.0, 5.0, 0.0, 2.0, 0.0, 0.0)
```

`FailureCriteria` is an enum of the criteria available (`VON_MISES`, `MOHR_COULOMB`, `RANKINE`,
`CONCRETE`, …).

---

## Usage in other modules

The `utils` module is re-exported at the top level of `eurocodepy`:

```python
import eurocodepy as ec

ec.crosssection          # the module utils.crosssection
ec.section_properties    # the module utils.section_properties
ec.stress                # the module utils.stress
```

---

## Further reading

- [eurocodepy Documentation](../index.md)

