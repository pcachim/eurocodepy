# EN 1992-1-1:2023

Second-generation Eurocode 2. Materials, partial factors and `get_concrete(edition="2023")` are on the
[main page](index.md); membranes, slabs and shells (Annex G) are in [Membranes, slabs and shells](shells.md).
Units: kN, m, MPa.

### Shear, EN 1992-1-1:2023 (Clause 8.2)

*Code reference:* [`uls2023.shear`][eurocodepy.ec2.uls2023.shear], [`uls2023.shear_check.eurocode2_shear_check`][eurocodepy.ec2.uls2023.shear_check.eurocode2_shear_check], [`uls2023.shear_check.ShearInput`][eurocodepy.ec2.uls2023.shear_check.ShearInput]

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

*Code reference:* [`uls2023.torsion`][eurocodepy.ec2.uls2023.torsion], [`uls2023.shear_torsion.eurocode2_shear_torsion_check`][eurocodepy.ec2.uls2023.shear_torsion.eurocode2_shear_torsion_check]

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

### Creep, shrinkage and relaxation, EN 1992-1-1:2023 (Annex B)

*Code reference:* [`time_dependent2023`][eurocodepy.ec2.time_dependent2023], [`sls.creep.creep_coef`][eurocodepy.ec2.sls.creep.creep_coef], [`sls.shrinkage.shrink_strain`][eurocodepy.ec2.sls.shrinkage.shrink_strain]

```python
from eurocodepy.ec2 import time_dependent2023 as td

fcm = 38.0                                                      # C30/37, fcm,28
td.creep_coefficient(18250 + 28, 28, fcm, rh=50, hn=200, cls="CN")   # φ(50 y, 28 d) ≈ 2,46
td.shrinkage_total(18251, 1, fcm, rh=50, hn=200, cls="CN")           # εcs after 50 years of drying
td.fcm_t(7, fcm, 30.0, "CN"); td.ecm_t(7, 33000.0, 30.0, "CN")       # strength and stiffness at 7 days
td.creep_coefficient_50y(28, "CN", 50, 200, 30.0)                    # Table 5.2, any fck by (35/fck)^A
td.relaxation_loss(18250, 1000.0, td.relaxation_rho1000(0.7, "wire"))  # Eq. (B.43), MPa
```

Ages in days, `hn = 2Ac/u` in mm, `RH` in %. `cls` is the strength development class CS, CN or CR (Table B.1).
`ec2.sls.creep.creep_coef` and `ec2.sls.shrinkage.shrink_strain` are this model (same results, arrays accepted).

### Detailing, EN 1992-1-1:2023 (Clause 12)

*Code reference:* [`uls2023.detailing`][eurocodepy.ec2.uls2023.detailing]

```python
from eurocodepy.ec2.uls2023 import detailing as dt

dt.calc_asw_min_s(f_ck=30, f_yk=500, b_w=0.3, ductility="B")   # Eq. (12.4), m²/m
dt.beam_max_spacings(d=0.5)                                  # Table 12.1: s_l_max, s_bu_max, s_tr_max
dt.column_min_longitudinal(n_ed=2000, f_yd=434.8, a_c=0.09)   # Table 12.3, m²
dt.wall_min_vertical(a_c=0.2, f_ctm=2.9, f_yk=500)            # Table 12.4, m²
dt.calc_vrd_int(a_s_int=1e-3, f_yd=434.8, ductility="B")      # Eq. (12.10), kN
```

The tables of Clause 12 are NDPs; the functions return the values of the Eurocode.
