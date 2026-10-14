# Eurocode 2 module: `ec2`

## Overview

The `ec2` module provides tools for the design of reinforced and prestressed concrete
structures according to EN 1992-1-1 and, for slabs and shells, EN 1992-2 Annex LL. It supports the
2004 edition and the 2023 edition (second generation) where functions have been updated; see
[Editions and National Annexes](../editions.md).

| Page | Content |
|------|---------|
| this page | conventions, materials, helper functions, limitations |
| [EN 1992-1-1:2004](edition-2004.md) | beam bending and shear, anchorage, punching, SLS crack, creep, shrinkage, fire |
| [EN 1992-1-1:2023](edition-2023.md) | shear (8.2), torsion (8.3), detailing (12), creep and shrinkage (Annex B) |
| [Membranes, slabs and shells](shells.md) | Annex G (2023), EN 1992-1-1 Annex F and EN 1992-2 6.109 and Annex LL (2004), sandwich model, out-of-plane shear |
| [Clause map](clauses.md) | every function of `uls2023` by clause and equation (generated from the docstrings) |

---

## Conventions

Functions written for the second-generation code (`uls2023`, `time_dependent2023`, and the shell, slab
and membrane checks) use **kN, m and MPa** unless the docstring says otherwise. The older 2004 functions
were written one by one and mix units; the table below is what each family expects.

| Family | Lengths | Areas | Forces / moments | Stresses |
|--------|---------|-------|------------------|----------|
| `uls2023`, `uls.shell_check`, `uls.slab_check`, `uls.membrane_check` | m | m² (per m: m²/m) | kN, kN/m, kNm, kNm/m | MPa |
| `uls.beam` (`calc_mrd`, `calc_asl`) | m | cm² | kN·m | MPa |
| `uls.shear` (`calc_vrd`, `calc_vrdc`, `calc_asws`) | m | m² per m | kN | MPa |
| `uls.shell` (`calc_reinf_plane`, `calc_reinf_shell`) | m | forces, see the docstring | kN/m | — |
| `uls.punch` | mm | — | kN, kNm | MPa |
| `uls.anchorage` | mm | mm² | N | MPa |
| `sls.crack` | m (bar diameter too) | m² | kNm | MPa; `crack_opening` returns mm |
| `time_dependent2023`, `sls.creep`, `sls.shrinkage` | `hn` in mm | — | — | MPa; ages in days |

**Signs.** Tension and sagging bending are positive in the code of 2023 (Annex G): the *bottom* layer of
`uls2023` is in tension for positive `m`. EN 1992-2 Annex LL and `uls.shell.calc_reinf_shell` take positive `m`
as tension on the *top* face. `uls.shell_check` hides this by returning `asx_bot`, `asy_bot`, `asx_top`,
`asy_top` for the physical faces. Axial force is positive in tension, except in `sls.crack.crack_opening`
(compression positive, see its docstring).

---

## Materials

### `Concrete`

*Code reference:* [`materials.Concrete`][eurocodepy.ec2.materials.Concrete], [`materials.get_concrete`][eurocodepy.ec2.materials.get_concrete]

```python
from eurocodepy.ec2 import Concrete

c = Concrete('C30/37')
c.fck      # characteristic compressive strength [MPa]
c.fcd      # design compressive strength (fck / γc)
c.fctm     # mean tensile strength
c.Ecm      # secant modulus of elasticity [MPa]
```

Available grades: 2004, C12/15 to C90/105; 2023 (Table 5.1), C12/15 to C100/115.

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

*Code reference:* [`materials.Reinforcement`][eurocodepy.ec2.materials.Reinforcement]

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

*Code reference:* [`materials.Prestress`][eurocodepy.ec2.materials.Prestress]

```python
from eurocodepy.ec2 import Prestress
p = Prestress('Y1860S7 12.5')   # class and nominal diameter
p.fpk     # characteristic tensile strength [MPa]
p.fp0_1k  # 0.1% proof strength [MPa]
```

---

## Helper functions

```python
# Partial safety factors
from eurocodepy.ec2 import GammaC, GammaS, GammaCT, GammaP   # 1.5, 1.15, 1.5, 1.15 (floats)

# Time-dependent concrete strength factor
from eurocodepy.ec2 import beta_cc
s = beta_cc(t=28, s=0.25)   # βcc(t) of Eq. 3.2: 1.0 at 28 days, s = 0.25 for class N cement

# Creep and shrinkage (EN 1992-1-1:2004, Annex B)
from eurocodepy.ec2 import calc_creep_coef, calc_shrink_strain

# Creep and shrinkage (EN 1992-1-1:2023, Annex B): same model as ec2.time_dependent2023, validated
from eurocodepy.ec2 import creep_coef, shrink_strain
```

---

## Not implemented

- EN 1992-1-1:2023: `uls2023.column` is the 2004 column code with the 2023 `fcd`; SLS crack width
  (`sls.crack`) and anchorage and lap lengths (`uls.anchorage`) are still 2004.
- EN 1992-2 Annex LL: the general eccentric case of (108) (`zn ≠ zt`) and the eccentric reinforcement of (115)c.
- EN 1992-1-1:2004 slabs: the chord force of the shear truss is not added to the Wood-Armer bars
  (the sandwich model adds it).
- Minimum reinforcement is never added to membrane, slab and shell designs unless `min_reinf` asks for it
  (default `"demand"`: a face with no tension gets zero).

## Further reading

- [EN 1992-1-1 — Design of concrete structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-2-design-concrete-structures)
