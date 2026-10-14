# EN 1992-1-1:2004

Units differ between functions: see the [conventions](index.md#conventions). Slabs, membranes and shells are in
[Membranes, slabs and shells](shells.md).

## ULS checks

### Bending — `ec2.uls.beam`

*Code reference:* [`uls.beam`][eurocodepy.ec2.uls.beam]

```python
from eurocodepy.ec2 import Concrete, Reinforcement
from eurocodepy.ec2.uls.beam import calc_mrd, calc_asl, get_bend_params

c, s = Concrete("C30/37"), Reinforcement("B500B")
b, d = 0.30, 0.46                                  # m

# Design bending resistance of a rectangular section: As in cm²
mrd, eps_s, x = calc_mrd(b, d, 8.04, c.fcd, s.fyd)     # kNm, steel strain [‰], x/d
# Required tensile reinforcement for MEd = 150 kNm
asl, eps_s, x = calc_asl(b, d, 150.0, c.fcd, s.fyd)      # cm², steel strain [‰], x/d
# Stress-block parameters of a concrete class
get_bend_params("C30/37")
```

### Shear — `ec2.uls.shear`

*Code reference:* [`uls.shear`][eurocodepy.ec2.uls.shear]

```python
from eurocodepy.ec2.uls.shear import calc_vrdc, calc_vrd, calc_vrdmax, calc_asws

bw, d, fck, gc, fyk, gs, cot = 0.30, 0.46, 30.0, 1.5, 500.0, 1.15, 2.0       # m, MPa

vrd_min, vrd_c, vrd = calc_vrdc(bw, d, fck, gc, rho_l=0.006)  # without shear reinforcement [kN]
vrd_max = calc_vrdmax(bw, d, fck, gc, cot)                    # strut resistance [kN]
vrd_s = calc_vrd(bw, d, fck, gc, fyk, gs, cot, asw_s=5e-4)    # min(VRd,s, VRd,max) [kN]
asw_s, vrd_max = calc_asws(bw, d, fck, gc, fyk, gs, cot, ved=150.0)   # Asw/s [m²/m], nan if VEd > VRd,max
```

### Shell / plane reinforcement — `ec2.uls.shell`

*Code reference:* [`uls.shell`][eurocodepy.ec2.uls.shell]

```python
from eurocodepy.ec2.uls.shell import calc_reinf_plane, calc_reinf_shell

# In-plane (membrane) forces for nxx, nyy, nxy in kN/m: the reinforcement is returned as forces
asx, asy, asc, cot = calc_reinf_plane(100.0, 50.0, 20.0)     # kN/m, kN/m, concrete, cot θ

# Sandwich layers of a shell (Annex LL): n in kN/m, m in kNm/m, cover and h in m
top = calc_reinf_shell(100.0, 50.0, 20.0, 20.0, 10.0, 5.0, 0.04, 0.2)
top_asx, top_asy, top_asc, top_cot, bot_asx, bot_asy, bot_asc, bot_cot = top   # per unit layer thickness
```

### Anchorage and lap lengths — `ec2.uls.anchorage`

*Code reference:* [`uls.anchorage`][eurocodepy.ec2.uls.anchorage]

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

*Code reference:* [`uls.punch`][eurocodepy.ec2.uls.punch], [`uls.punch_check.eurocode2_punching_check`][eurocodepy.ec2.uls.punch_check.eurocode2_punching_check]

```python
from eurocodepy.ec2.uls.punch import calc_perimeters, calc_vedp, calc_vrdcminp, calc_vrdcp
```

---

## SLS checks

### Crack width — `ec2.sls.crack`

*Code reference:* [`sls.crack`][eurocodepy.ec2.sls.crack]

```python
import numpy as np
from eurocodepy.ec2 import Concrete, Reinforcement
from eurocodepy.ec2.sls.crack import crack_opening, is_cracked, sr_max

c, s = Concrete("C30/37"), Reinforcement("B500B")
# b, h, bar diameter in m; areas in m²; M in kNm (quasi-permanent: k_t = 0.4)
sec = (np.array([8.04e-4]), np.array([0.46]), np.array([0.0]), np.array([0.04]), c, s)   # As, ds, Asc, dsc
cracked = is_cracked(0.30, 0.50, *sec, np.array([150.0]))
wk = crack_opening(0.30, 0.50, 0.016, *sec, np.array([150.0]), k_t=0.4)   # mm
sr = sr_max(c=0.04, phi=0.016, rho_p_eff=0.02)             # same units as c and phi
```

### Creep — `ec2.sls.creep`

```python
from eurocodepy.ec2.sls.creep import creep_coef   # EN 1992-1-1:2023, Annex B
# fcm,28 = 38 MPa (C30/37), hn = 2Ac/u in mm, class CS, CN or CR; loaded at 28 d, t = 50 years
phi = creep_coef(t=18278, t0=28, fcm28=38.0, RH=60, hn=200, t0_T=28, concrete_class="CN")
```

### Shrinkage — `ec2.sls.shrinkage`

```python
from eurocodepy.ec2.sls.shrinkage import shrink_strain  # EN 1992-1-1:2023, Annex B
eps_cs = shrink_strain(t=18251, ts=1, fcm28=38.0, RH=60, hn=200, concrete_class="CN",
                       alpha_NDP_b=1.0, alpha_NDP_d=1.0)
```

---

## Fire — `ec2.fire`

Simplified and tabulated methods (EN 1992-1-2) in `ec2.fire`: reduction factors `sig_kc`, `sig_ks` and
temperatures `stemp` are tables (arrays), `delta_a` gives the axis-distance correction and `beam_*`,
`wall_*` the tabulated minimum dimensions.

```python
from eurocodepy.ec2.fire import delta_a, sig_kc, sig_ks, stemp
delta_a(0.7, 1.15, 500.0, 1.0)      # eta_fi, gamma_s, fyk, As,req/As,prov
```
