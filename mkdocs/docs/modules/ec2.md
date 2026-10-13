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

### EN 1992-1-1:2023

```python
c = Concrete('C30/37', edition='2023')                  # k_tc = 1.0 (late loading)
c = Concrete('C50/60', edition='2023', loading='other') # k_tc = 0.85
c.eta_cc, c.k_tc, c.fcd   # fcd = eta_cc * k_tc * fck / gamma_c  (Eq. 5.3)
Concrete('C30/37', edition='2023', situation='accidental').gamma_c   # 1.15 (Table 4.3)
Concrete('C30/37', edition='2023', k_cip=1.1)           # cast in the ground (4.3.3(4))

from eurocodepy.ec2 import material_partial_factors, prestress_partial_factors
material_partial_factors('2023', 'fatigue')   # gamma_s, gamma_c, gamma_ce, gamma_v
prestress_partial_factors('2023')             # Tables 4.1 and 4.2
```

`loading='late'` is `t_ref` ≤ 28 d (CN/CR) or 56 d (CS) with the design loading not expected for 3 months
after casting; `'other'` is every other case, including `fck(t)`. `Reinforcement` and `Prestress` take
`edition` and `situation` as well. The `edition=None` default is 2004.

The check inputs (`PunchInput`, `ShearInput`, `SlabInput`, `MembraneInput`, `ShearTorsionInput`) take the
partial factors of a design situation with `from_partial_factors`:

```python
from eurocodepy.ec2.uls.punch_check import PunchInput
inp = PunchInput.from_partial_factors("2023", "accidental", d=0.25, bx=0.4, by=0.4, fck=30, fyk=500)
inp.gamma_v, inp.gamma_c, inp.gamma_s, inp.edition   # 1.15, 1.15, 1.0, '2023'
```

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

### Shear, EN 1992-1-1:2023 (Clause 8.2)

```python
from eurocodepy.ec2 import uls2023

inp = uls2023.ShearInput(b=0.3, d=0.5, fck=30, fyk=500, as_long=0.0015)   # m, MPa, m²
r = uls2023.eurocode2_shear_check(inp, v_ed=150.0)                          # kN
r.mode, r.asw_s, r.cot, r.vrd_c, r.vrd_max   # 'stirrups', Asw/s [m²/m], cot θ, ...

uls2023.shear.calc_taurdc(rho_l=0.01, fck=30, d=0.5, fyd=434.8)   # τRd,c, Eq. (8.27)
uls2023.shear.calc_tau_rdi(30, 1.5, 20, "rough", sigma_n=1.0)     # interface, Eq. (8.76)
```

The check follows 8.2.1: `τEd ≤ τRdc,min` (verification omitted), `τEd ≤ τRd,c` (no calculated
reinforcement), otherwise the compression field with `ν = 0,5` and the flattest strut that does not
crush (`cot θ ≤ cot θmin`). `ShearInput` takes `gamma_v` (Table 4.3), `n_ed`/`m_ed` (shear span and axial
force, 8.2.2(3)-(4)) and `asw_min_s`, the minimum `Asw/s` (default `ρw,min` of Eq. 12.4; `0.0` omits it). The
formulae for the other parts of 8.2 (planar members, strain-based `ν`, chord forces, web-flange shear,
interfaces) are in `uls2023.shear`.

### Torsion and shear + torsion, EN 1992-1-1:2023 (Clause 8.3)

```python
from eurocodepy.ec2 import uls2023

t = uls2023.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0, cover=0.05)
t["Asw_tor_s"], t["Asl_tor"], t["TRd_max"]      # Eqs. (8.82), (8.83), (8.84)

inp = uls2023.ShearTorsionInput(b=0.3, h=0.5, cover=0.05, fck=30, fyk=500, as_long=0.0015)
r = uls2023.eurocode2_shear_torsion_check(inp, v_ed=150.0, t_ed=30.0)
r.asw_total_s, r.asl_tor_total, r.interaction   # interaction: Eq. (8.86)
```

`cot θ` is shared by shear and torsion; `1/2,5 ≤ cot θ ≤ 2,5` (Eq. 8.85). `ν` of Eq. (8.84) comes from
Annex G: 0,60 at `cot θ = 1`, otherwise Eq. (G.9) with `ε1 = max(G.10, G.11)` and the steel strain `fyd/Es`
(0,38 at `cot θ = 2`, 0,29 at `cot θ = 2,5`); `nu=` overrides it. For a squat section (`bmax/bmin < 1,5`) the cover is reduced to `0,07·bmin`
(8.3.4(5)).

### Membrane, shell and slab elements, EN 1992-1-1:2023 (Annex G)

```python
from eurocodepy.ec2 import uls2023
from eurocodepy.ec2.uls2023 import annex_g as g

g.membrane_optimum(5.0, 3.0, 2.0)          # Table G.1: cot θ*, ftdx*, ftdy*, σcd*
r = uls2023.eurocode2_membrane_check(
    uls2023.MembraneInput(n_xx=100, n_yy=50, n_xy=20, fck=30, fyk=500, thickness=0.2))
r.asx, r.asy, r.crushing                    # σcd ≤ ν·fcd (ν = 0,4, or nu_mode="strain")

s = uls2023.slab_design.eurocode2_slab_check(uls2023.slab_design.SlabInput(
    m_x=50, m_y=30, m_xy=10, fck=30, fyk=500, thickness=0.2,
    cover_bot_x=0.03, cover_bot_y=0.04, cover_top_x=0.03, cover_top_y=0.04))
s.asx_bot, s.details["m_rdx"]               # Tables G.2/G.3 optimum capacities
```

Tension and sagging moments are positive. `slab_design` takes the design moments of the element (it
is not a drop-in for `uls.slab_check`, which takes Wood-Armer moments). `SlabInput.method` is `"auto"`
(default): Tables G.2/G.3 where `|mxy| < 0,07·d²·fcd` and `nEd = 0`, the **sandwich model** (G.4(1)) otherwise
— two layers `t = 2·c` apart by `z = h − t`, each designed as a membrane, `σcd ≤ ν·fcd` checked per layer
(`details["crushing"]`); `"optimum"` and `"sandwich"` force one of them. In-plane forces go in `n_x`, `n_y`, `n_xy`.

### Shell elements (sandwich model)

```python
from eurocodepy.ec2 import uls, uls2023

inp = dict(n_xx=100, n_yy=50, n_xy=20, m_xx=20, m_yy=10, m_xy=5,      # kN/m and kNm/m
           fck=30, fyk=500, thickness=0.2, cover=0.04)
r = uls.eurocode2_shell_check(uls.ShellInput(**inp))                  # 2004: strut ≤ ν·fcd, ν = 0,6(1 − fck/250)
r23 = uls2023.eurocode2_shell_check(uls2023.ShellInput(**inp))        # 2023: Annex G.4, ν = 0,4 or G.9
r.asx_bot, r.asy_bot, r.asx_top, r.asy_top, r.crushing               # m²/m
```

Two layers of thickness `t = 2·cover` at `z = h − t` (EN 1992-2 Annex LL); each layer is a membrane (Table G.1 / Annex F);
`ftd·t/fyd` gives the area and the strut of each layer is checked against `ν·fcd`. Sagging moments put the
bottom layer in tension.

### Detailing, EN 1992-1-1:2023 (Clause 12)

```python
from eurocodepy.ec2.uls2023 import detailing as dt

dt.calc_asw_min_s(fck=30, fyk=500, b_w=0.3, ductility="B")   # Eq. (12.4), m²/m
dt.beam_max_spacings(d=0.5)                                  # Table 12.1: s_l_max, s_bu_max, s_tr_max
dt.column_min_longitudinal(n_ed=2000, f_yd=434.8, a_c=0.09)   # Table 12.3, m²
dt.wall_min_vertical(a_c=0.2, f_ctm=2.9, f_yk=500)            # Table 12.4, m²
dt.calc_vrd_int(a_s_int=1e-3, f_yd=434.8, ductility="B")      # Eq. (12.10), kN
```

The tables of Clause 12 are NDPs; the functions return the values of the Eurocode.

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

### Anchorage and lap lengths — `ec2.uls.anchorage`

Ribbed bars, EN 1992-1-1:2004 §8.4 and §8.7. **Units: mm, mm², MPa** (the units of
the bond clauses themselves).

```python
from eurocodepy.ec2.uls import (
    bond_conditions_beam, beam_cover_distance,
    design_anchorage_length, lap_length,
)

bond = bond_conditions_beam(h=500, face="top")            # "poor" (h > 250 mm)
cd = beam_cover_distance(width=300, cover=38, n_bars=4, phi=16)   # Fig. 8.3

a = design_anchorage_length(phi=16, fck=30, fyk=500, cd=cd,
                            good_bond=(bond == "good"))
a["fbd"], a["lb_rqd"], a["lbd"]          # bond stress, basic and design length
l = lap_length(phi=16, fck=30, fyk=500, cd=cd, rho1=50)
l["alpha6"], l["l0"]                     # lap length of Eq. 8.10
```

* `bond_strength` — `f_bd = 2.25·η1·η2·f_ctd` (§8.4.2; `f_ctd` capped at C60/75).
* `basic_anchorage_length` — `l_b,rqd = (φ/4)·σ_sd/f_bd` (Eq. 8.3).
* `anchorage_coefficients` — `α1 … α5` of Table 8.2 (shape, cover, confinement,
  welded bars, transverse pressure; `α2·α3·α5 ≥ 0.7`).
* `design_anchorage_length` — `l_bd = α1·α2·α3·α4·α5·l_b,rqd ≥ l_b,min`
  (Eq. 8.4, 8.6, 8.7); `σ_sd` defaults to `f_yd` (the safe choice for a curtailed bar).
* `lap_length` — `l_0 = α1·α2·α3·α5·α6·l_b,rqd ≥ l_0,min` (Eq. 8.10, 8.11),
  `α6 = √(ρ1/25)` between 1 and 1.5 (Table 8.3).

Every function accepts `trace=` (a `CalcReport`) to record the steps.

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

