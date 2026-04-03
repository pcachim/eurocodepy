# Utilities module: `utils`

## Overview

The `utils` module provides cross-cutting helper functions for geometric, mechanical,
and mathematical operations commonly needed in structural calculations. It is used
internally throughout EurocodePy and is also part of the public API.

---

## Section properties — `utils.crosssection`

```python
from eurocodepy.utils import crosssection, section_properties

# section_properties: properties of a rectangular section (uncracked)
props = section_properties(b=300, h=600)
# Returns a dict with keys:
# 'A'     — cross-sectional area [mm²]
# 'Iy'    — second moment of area about y-axis [mm⁴]
# 'Iz'    — second moment of area about z-axis [mm⁴]
# 'Wel_y' — elastic section modulus about y-axis [mm³]
# 'Wel_z' — elastic section modulus about z-axis [mm³]
# 'iy'    — radius of gyration about y-axis [mm]
# 'iz'    — radius of gyration about z-axis [mm]

# crosssection: general polygon section from vertex coordinates
cs = crosssection([(0, 0), (300, 0), (300, 600), (0, 600)])
```

---

## Stress calculations — `utils.stress`

```python
from eurocodepy.utils import stress

# Principal stresses and invariants from a 2-D or 3-D stress state
result = stress.principal(sigma_x, sigma_y, tau_xy)
# Returns (sigma_1, sigma_2, theta_p)

result = stress.invariants(sigma_x, sigma_y, sigma_z, tau_xy, tau_yz, tau_xz)
# Returns (I1, J2, J3) — stress invariants
```

---

## Usage in other modules

The `utils` module is re-exported at the top-level `eurocodepy` namespace:

```python
import eurocodepy as ec

ec.crosssection        # alias for utils.crosssection
ec.section_properties  # alias for utils.section_properties
ec.stress              # alias for utils.stress
```

---

## Further reading

- [eurocodepy Documentation](../index.md)

