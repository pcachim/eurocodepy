# Eurocode 5 module: `ec5`

## Overview

The `ec5` module provides tools for the design of timber structures according to
EN 1995-1-1. It covers material classes for all common timber products, modification
factors, and ULS / SLS checks.

---

## Materials

### `Timber` (base class)

```python
from eurocodepy.ec5 import Timber
t = Timber('C24')
t.fmk      # characteristic bending strength [MPa]
t.ft0k     # tension parallel to grain [MPa]
t.fc0k     # compression parallel to grain [MPa]
t.fvk      # shear strength [MPa]
t.E0mean   # mean modulus of elasticity parallel to grain [MPa]
t.E0_05    # 5th percentile modulus [MPa]
t.Gmean    # mean shear modulus [MPa]
t.rhok     # characteristic density [kg/m³]
t.rhomean  # mean density [kg/m³]
```

### `SolidTimber`

For sawn structural timber (strength classes C and D).

```python
from eurocodepy.ec5 import SolidTimber, Softwood, Hardwood

c24 = SolidTimber('C24')   # softwood C class
d30 = SolidTimber('D30')   # hardwood D class
```

### `Glulam`

For glued laminated timber (GL classes).

```python
from eurocodepy.ec5 import Glulam

gl28h = Glulam('GL28h')   # homogeneous
gl28c = Glulam('GL28c')   # combined
```

### Other product classes

| Class | Product |
|-------|---------|
| `CLT` | Cross-laminated timber |
| `LVL` | Laminated veneer lumber |
| `ST`  | Structural timber (alias for SolidTimber) |

### `ServiceClass` (enum)

| Member | Description |
|--------|-------------|
| `SC1` | Indoor, dry conditions (MC ≤ 12%) |
| `SC2` | Covered, outdoor (MC ≤ 20%) |
| `SC3` | Exposed to weather |

### `LoadDuration` (enum)

`Permanent`, `LongTerm`, `MediumTerm` (= `Medium`), `ShortTerm`, `Instantaneous`

### `k_mod` — modification factor

```python
kmod = timber.k_mod(
    service_class=ServiceClass.SC1,
    load_duration=LoadDuration.Medium,
)
```

### `GetTimberDesignValues`

Convenience function that returns design strengths for a given timber grade,
service class, and load duration in a single call.

---

## ULS checks — `ec5.uls`

### Bending — `ec5.uls.bending`

```python
from eurocodepy.ec5.uls.bending import (
    calc_mrd,        # design bending resistance
    calc_lateral_torsional_buckling,
    check_biaxial_bending,
)
```

### Shear — `ec5.uls.shear`

```python
from eurocodepy.ec5.uls.shear import (
    calc_vrd,     # design shear resistance
    calc_torsion, # torsion capacity
)
```

---

## SLS checks — `ec5.sls`

### Vibration — `ec5.sls.vibration`

```python
from eurocodepy.ec5.sls.vibration import floor_freq, vel, vlim, a_from_b, b_from_a

f1 = floor_freq(l=5.0, EI=1.2e10, m=300.0)   # fundamental frequency [Hz]
v  = vel(...)         # unit impulse velocity response [m/s per N]
vl = vlim(...)        # velocity limit [m/s per N]
```

### Deformation — `ec5.sls.deformation`

```python
from eurocodepy.ec5.sls import deformation
```

---

## Compliance

Calculations follow EN 1995-1-1:2004+A2:2014.

## Further reading

- [EN 1995-1-1 — Design of timber structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-5-design-timber-structures)

