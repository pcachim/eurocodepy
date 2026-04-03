# Eurocode 2 module: `ec2`

## Overview

The `ec2` module provides tools for the design of reinforced and prestressed concrete
structures according to EN 1992-1-1. It supports both the 2004 and 2025 editions of
the code where functions have been updated.

---

## Materials

### `Concrete`

```python
from eurocodepy.ec2 import Concrete

c = Concrete('C30/37')
c.fck      # characteristic compressive strength [MPa]
c.fcd      # design compressive strength (fck / γc)
c.fctm     # mean tensile strength
c.Ecm      # secant modulus of elasticity [MPa]
```

Available grades: C20/25, C25/30, C30/37, C35/45, C40/50, C45/55, C50/60,
C55/67, C60/75, C70/85, C80/95, C90/105.

Convenience instances are pre-created: `C20_25`, `C25_30`, `C30_37`, …, `C90_105`.

### `Reinforcement`

```python
from eurocodepy.ec2 import Reinforcement

r = Reinforcement('B500B')
r.fyk     # characteristic yield strength [MPa]
r.fyd     # design yield strength (fyk / γs)
r.Es      # elastic modulus [MPa]
```

Available grades: B400A/B/C, B500A/B/C, B600A/B/C, B700A/B/C, A400NR, A500NR,
A400NRSD, A500NRSD, A500EL.

### `Prestress`

```python
from eurocodepy.ec2 import Prestress
p = Prestress('Y1860S7')
p.fpk     # characteristic tensile strength [MPa]
p.fp0_1k  # 0.1% proof strength [MPa]
```

### Helper functions

```python
# Partial safety factors
from eurocodepy.ec2 import GammaC, GammaS, GammaCT, GammaP

# Time-dependent concrete strength factor
from eurocodepy.ec2 import beta_cc
s = beta_cc(fck=30, t=28, cement='N')   # = 1.0 at 28 days

# Creep and shrinkage (EN 1992-1-1:2004)
from eurocodepy.ec2 import calc_creep_coef, calc_shrink_strain

# Creep and shrinkage (EN 1992-1-1:2025)
from eurocodepy.ec2 import creep_coef, shrink_strain
```

---

## ULS checks

### Bending — `ec2.uls.beam`

```python
from eurocodepy.ec2.uls.beam import calc_mrd, calc_asl, get_bend_params

# Design bending resistance of a rectangular section
MRd = calc_mrd(b, d, As, concrete, reinforcement)  # [Nmm]

# Required tensile reinforcement for a given design moment
Asl = calc_asl(b, d, MEd, concrete, reinforcement)

# Full set of bending design parameters (x, z, ε, …)
params = get_bend_params(b, d, As, concrete, reinforcement)
```

### Shear — `ec2.uls.shear`

```python
from eurocodepy.ec2.uls.shear import calc_vrdc, calc_vrd, calc_vrdmax, calc_asws

VRd_c   = calc_vrdc(b_w, d, As, fck)          # without shear reinforcement [N]
VRd_max = calc_vrdmax(b_w, d, fck, angle=45)  # max strut resistance [N]
VRd_s   = calc_vrd(b_w, d, Asw_s, fyk)        # with shear links [N]
Asw_s   = calc_asws(b_w, d, VEd, fyk)         # required Asw/s [mm²/mm]
```

### Shell / plane reinforcement — `ec2.uls.shell`

```python
from eurocodepy.ec2.uls.shell import calc_reinf_plane, calc_reinf_shell

# In-plane (membrane) reinforcement
asx, asy = calc_reinf_plane(Nx, Ny, Nxy, fyd)

# Shell (plate + membrane) reinforcement
asx_bot, asy_bot, asx_top, asy_top = calc_reinf_shell(
    Nx, Ny, Nxy, Mx, My, Mxy, h, fyd
)
```

### Punching shear — `ec2.uls.punch`

```python
from eurocodepy.ec2.uls.punch import calc_perimeters, calc_vedp, calc_vrdcminp, calc_vrdcp
```

---

## SLS checks

### Crack width — `ec2.sls.crack`

```python
from eurocodepy.ec2.sls.crack import (
    calc_crack_width, calc_sr_max, calc_eps_sm_cm
)
```

### Creep — `ec2.sls.creep`

```python
from eurocodepy.ec2.sls.creep import creep_coef   # EN 1992-1-1:2025
phi = creep_coef(fck=30, RH=60, h0=200, t0=28, t=18250)
```

### Shrinkage — `ec2.sls.shrinkage`

```python
from eurocodepy.ec2.sls.shrinkage import shrink_strain  # EN 1992-1-1:2025
eps_sh = shrink_strain(fck=30, RH=60, h0=200, t=18250, t_s=7)
```

---

## Fire — `ec2.fire`

```python
from eurocodepy.ec2.fire import fire_base
```

---

## Compliance

Calculations follow EN 1992-1-1:2004 and, where indicated, EN 1992-1-1:2025 (second
generation Eurocode 2).

## Further reading

- [EN 1992-1-1 — Design of concrete structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-2-design-concrete-structures)

