# Membranes, slabs and shells

Units: kN, m, MPa. See the [conventions](index.md#conventions) for signs.

## EN 1992-1-1:2023, Annex G

*Code reference:* [`uls2023.annex_g`][eurocodepy.ec2.uls2023.annex_g], [`uls2023.membrane_check.eurocode2_membrane_check`][eurocodepy.ec2.uls2023.membrane_check.eurocode2_membrane_check], [`uls2023.slab_design.eurocode2_slab_check`][eurocodepy.ec2.uls2023.slab_design.eurocode2_slab_check], [`uls2023.shell_check.eurocode2_shell_check`][eurocodepy.ec2.uls2023.shell_check.eurocode2_shell_check]

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

## EN 1992-1-1:2004 and EN 1992-2 (Annex F, 6.109, Annex LL)

### Slabs and membranes

*Code reference:* [`uls.slab_check.eurocode2_slab_check`][eurocodepy.ec2.uls.slab_check.eurocode2_slab_check], [`uls.membrane_check.eurocode2_membrane_check`][eurocodepy.ec2.uls.membrane_check.eurocode2_membrane_check], [`uls.shell.strut_limit`][eurocodepy.ec2.uls.shell.strut_limit]

`uls.slab_check` takes Wood-Armer moments (`SlabInput.min_reinf="demand"` by default: a face with no
tension gets zero reinforcement). `strip_reinforcement` is the underlying strip design. The 2004 code does not
limit `mxy`; the Wood-Armer tables of EN 1992-1-1:2023 (G.4(5)) are valid for `|mxy| ≤ 0,07·d²·fcd`.

`uls.eurocode2_membrane_check` limits the concrete strut with `MembraneInput.strut_model`:

```python
from eurocodepy.ec2.uls import shell

sx, sy, txy, fck, fcd, cot = -10.0, -5.0, 2.0, 30.0, 20.0, 2.0      # MPa
shell.strut_limit("annex_f", sx, sy, txy, fck, fcd, cot)     # F.1(3)-(4): σ ≤ fcd, or ν·fcd, ν = 0,6(1 − fck/250)
shell.strut_limit("6.109", sx, sy, txy, fck, fcd, cot)       # EN 1992-2 6.109(103): Eqs. 6.110 and 6.112
shell.principal_stresses(sx, sy, txy); shell.elastic_compression_angle(sx, sy, txy)
shell.deformation_capacity_ok_2004(1.0, 1.0, sx, sy, txy)  # 6.109(105) check of the reinforcement ductility
```

### Shell elements (sandwich model, both editions)

*Code reference:* [`uls.shell_check.eurocode2_shell_check`][eurocodepy.ec2.uls.shell_check.eurocode2_shell_check], [`uls2023.shell_check.eurocode2_shell_check`][eurocodepy.ec2.uls2023.shell_check.eurocode2_shell_check], [`uls.shell.calc_reinf_shell`][eurocodepy.ec2.uls.shell.calc_reinf_shell]

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
bottom layer in tension (EN 1992-2 Annex LL: the "top" layer of `calc_reinf_shell` is the upper one, +m/z).

Cracking (EN 1992-2 Annex LL (102)–(104), (107)): with `check_cracking=True` (default) the principal stresses of the
uncracked section are evaluated through the thickness (`shell_stresses_at_level`) and the element is cracked where the Ottosen
criterion (`ottosen_phi`, LL.101; `fctm` or Table 3.1) is exceeded. An element that is not cracked gets zero areas and only
`σmin ≤ fcd` is checked: `details["cracked"]` is `False`. `check_cracking=False` designs it as cracked. `shell_cracking(n, m, h,
fck, v, f_ctm)` returns the check on its own.

Out-of-plane shear: pass `v_x`, `v_y` (kN/m) to `ShellInput` (and to `SlabInput` in `uls2023`). The principal shear
`vEd0 = √(vx² + vy²)` is verified as a beam of unit width — 2004: inner layer of Annex LL (109)–(111) with
`ρl = ρx·cos²φ0 + ρy·sin²φ0`; 2023: clause 8.2 (G.4(4)). Where stirrups are needed (`r.asw_s`, m²/m²), the chord force
`vEd0·cot θ` of the truss is added to the outer layers and the shell is redesigned; `r.details["shear"]` has the checks and
a crushed shear strut sets `r.crushing`. `check_shear=False` skips it. `uls.slab_check` returns `asw_s` too, but the chord
force is not added to the Wood-Armer bars.
