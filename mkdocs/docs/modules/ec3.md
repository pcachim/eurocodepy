# Eurocode 3 module: `ec3`

## Overview

The `ec3` module provides tools for the design of steel structures according to
EN 1993-1-1. It covers material properties, standard steel profiles, bolted and
welded connections, and ULS member checks.

---

## Materials

### `Steel`

```python
from eurocodepy.ec3 import Steel

steel = Steel('S355')
steel.fy   # yield strength [MPa]
steel.fu   # ultimate tensile strength [MPa]
steel.E    # elastic modulus [MPa]
steel.G    # shear modulus [MPa]
steel.nu   # Poisson's ratio
```

Available grades (enum `SteelEnum`): S235, S275, S355, S450.

### `Weld`

```python
from eurocodepy.ec3 import Weld, WeldTypeEnum

weld = Weld(grade='S355', weld_type=WeldTypeEnum.fillet)
```

### Bolts

```python
from eurocodepy.ec3 import Bolt, BoltGrade, BoltGrades, BoltsEnum

bolt = Bolt(diameter=20, grade=BoltGrade('8.8'))
bolt.fub    # ultimate tensile strength [MPa]
bolt.fyb    # yield strength [MPa]
```

Available bolt grades (enum `BoltsEnum`): 4.6, 5.6, 6.8, 8.8, 10.9.

---

## Steel profiles

All profile classes expose standard geometric properties (`A`, `Iy`, `Iz`,
`Wely`, `Welz`, `Wply`, `Wplz`, `iy`, `iz`, `It`, `Iw`, …).

### I-profiles — `ProfileI`

```python
from eurocodepy.ec3 import ProfileI, ProfilesIEnum

section = ProfileI('IPE300')
section.A    # cross-sectional area [mm²]
section.Iy   # second moment of area about y-axis [mm⁴]
section.h    # total height [mm]
section.bf   # flange width [mm]
section.tf   # flange thickness [mm]
section.tw   # web thickness [mm]
```

Available profiles (enum `ProfilesIEnum`): IPE80 to IPE600; HEA100 to HEA1000;
HEB100 to HEB1000; HEM100 to HEM1000.

### Hollow sections

```python
from eurocodepy.ec3 import ProfileCHS, ProfileRHS, ProfileSHS

chs = ProfileCHS('CHS114.3x6')    # circular hollow section
rhs = ProfileRHS('RHS200x100x8')  # rectangular hollow section
shs = ProfileSHS('SHS150x150x8')  # square hollow section
```

Enums: `ProfilesCHSEnum`, `ProfilesRHSEnum`, `ProfilesSHSEnum`.

### `SteelSection` and `SteelPlate`

```python
from eurocodepy.ec3 import SteelSection, SteelPlate

# Generic section combining a profile and a steel grade
sec = SteelSection(profile=ProfileI('IPE300'), steel=Steel('S355'))

# Flat plate
plate = SteelPlate(b=200, t=12, steel=Steel('S275'))
```

---

## Connections

### Bolted connections

```python
from eurocodepy.ec3 import BoltedConnection, PinnedConnection, PinnedConnectionDouble

conn = BoltedConnection(bolt=bolt, n_bolts=4, t=10.0, steel=steel)
```

### Welded connections

```python
from eurocodepy.ec3 import WeldConnection, WeldTypeEnum

weld_conn = WeldConnection(
    weld=weld,
    length=200.0,  # weld length [mm]
    throat=8.0,    # throat thickness [mm]
)
```

---

## ULS checks — `ec3.uls`

The `ec3.uls` sub-module exposes cross-section and member-level resistance checks.
Import directly from `eurocodepy.ec3.uls`.

---

## Compliance

Calculations follow EN 1993-1-1:2005 and EN 1993-1-8 (connections).

## Further reading

- [EN 1993-1-1 — Design of steel structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-3-design-steel-structures)

