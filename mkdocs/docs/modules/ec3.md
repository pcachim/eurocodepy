# Eurocode 3 module: `ec3`

## Overview

The `ec3` module provides tools for the design of steel structures according to
EN 1993-1-1: material properties, standard rolled profiles, bolted and welded connections,
section classification and the ULS section and member checks.

Profile properties are those of the catalogue: **dimensions in cm, areas in cm², inertia in cm⁴**.
The checks take strengths in N/mm², forces in kN and moments in kNm, and read the geometry of a
profile converting cm to mm.

---

## Materials

### `Steel`

```python
from eurocodepy.ec3 import Steel

steel = Steel('S355')
steel.fyk        # yield strength [MPa] (t ≤ 40 mm)
steel.fuk        # ultimate tensile strength [MPa]
steel.fyk40      # yield strength, 40 mm < t ≤ 80 mm
steel.Es         # elastic modulus [MPa]
steel.fyd        # design yield strength fyk/γM0
steel.gamma_M0, steel.gamma_M1, steel.gamma_M2
```

Grades (enum `SteelEnum`): S235, S275, S355, S450, and the others of the database.

### Bolts

```python
from eurocodepy.ec3 import Bolt, BoltGrade

bolt = Bolt(20, '8.8')             # M20, grade 8.8
bolt.fub, bolt.fyb                 # ultimate and yield strength [MPa]
bolt.d, bolt.d0                    # nominal and hole diameter [mm]
bolt.A, bolt.Athread               # gross and tensile stress area As [cm²]
```

Grades: 4.6, 5.6, 6.6, 6.8, 8.8, 9.8, 10.9, 12.9 (`BoltGrades`, `BoltsEnum`). `Bolt('M20', '8.8')` reads the areas of the
database; `Bolt(20, '8.8')` uses those of the standard size when it exists, `0,78·A` otherwise, or the `athread=` you give.

### `Weld`

```python
from eurocodepy.ec3 import Weld, WeldConnection, WeldTypeEnum

weld = Weld(a=5.0, length=200.0, steel_grade='S355')     # throat thickness a, length
group = WeldConnection()
group.add(weld)
group.total_length()
group.area, group.xg, group.yg                      # throat area and centroid [mm², mm]
group.inertia_xx, group.inertia_yy, group.inertia_xy  # about the centroid [mm⁴]
group.w_el_xx_sup, group.w_el_xx_inf                  # elastic moduli to the extreme welds [mm³]
```

`WeldTypeEnum`: `SLIDE`, `SHEAR`, `NORMAL`, `SHEARNORMAL`, `SLIDENORMAL`, `SLIDESHEAR`, `SLINESHEARNORMAL`.

---

## Steel profiles

`ProfilesI`, `ProfilesCHS`, `ProfilesRHS` and `ProfilesSHS` are dictionaries of the rolled profiles of the
database, keyed by name; the profile classes hold the catalogue values.

```python
from eurocodepy.ec3 import ProfilesI, ProfilesCHS, ProfilesRHS, ProfilesSHS

section = ProfilesI['IPE300']
section.h, section.b, section.tw, section.tf        # [cm]
section.A, section.Iy, section.Iz                   # [cm², cm⁴]
section.Wel_y, section.Wpl_y, section.Wel_z, section.Wpl_z    # [cm³]
section.IT, section.Iw, section.Av_z                # torsion, warping, shear area
section.Npl_Rd, section.Mpl_Rd_y, section.Vpl_Rd_z  # S235 resistances of the catalogue

list(ProfilesI)[:3]                                  # 'HEA100', 'HEA1000', 'HEA120'
```

I profiles: IPE, HEA, HEB, HEM; hollow sections: circular (CHS), rectangular (RHS) and square (SHS), with the
enums `ProfilesIEnum`, `ProfilesCHSEnum`, `ProfilesRHSEnum`, `ProfilesSHSEnum`.

### `SteelPlate`

```python
from eurocodepy.ec3 import SteelPlate

plate = SteelPlate(thickness=10.0, steel=steel, width=200.0)     # mm
```

---

## Connections

### Bolted connections

```python
import numpy as np
from eurocodepy.ec3 import BoltedConnection

conn = BoltedConnection(bolt, outer_plate=plate)
conn.Fv_Rd(), conn.Ft_Rd(), conn.Bp_Rd()           # shear, tension and punching resistance per bolt [kN]
r = conn.check(Fv_Ed=np.array([100.0]), Ft_Ed=np.array([0.0]))
r['ShearRatio'], r['BearingRatio'], r['TensileRatio'], r['PunchingRatio']
```

`PinnedConnection` and `PinnedConnectionDouble` add the bending of the pin (`gap`, `M_Rd`).

---

## ULS checks — `ec3`

### Classification (EN 1993-1-1, 5.5)

```python
from eurocodepy.ec3 import classify_section

c = classify_section(section, fy=355.0, n_ed=0.0, m_ed=100.0)     # kN, kNm
c.section_class
```

### Section resistance (6.2)

```python
from eurocodepy.ec3 import section_check_profile, SectionForces

r = section_check_profile(section, 355.0, SectionForces(n_ed=0.0, my_ed=100.0, vz_ed=80.0))
r.utilization
```

`eurocode3_section_check(SectionResistanceInput(...), SectionForces(...))` is the same check for
a section described by its dimensions instead of a profile.

### Member buckling (6.3, Eqs. 6.61 and 6.62)

```python
from eurocodepy.ec3 import member_check_profile

r = member_check_profile(section, 355.0, n_ed=-200.0, my_ed=80.0,
                         lcr_y=4000.0, lcr_z=4000.0, l_lt=4000.0)      # buckling lengths [mm]
r.utilization
```

`eurocode3_member_check(MemberInput(...))` takes the section properties directly. All the checks accept
`trace=` (a `CalcReport`) to record the steps.

---

## Compliance

Calculations follow EN 1993-1-1:2005 and EN 1993-1-8 (connections).

## Further reading

- [EN 1993-1-1 — Design of steel structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-3-design-steel-structures)
