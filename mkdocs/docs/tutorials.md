# Tutorials

Step-by-step worked examples that take you from zero to a working calculation.
Each tutorial is self-contained — copy, paste, and run.

---

## Tutorial 1 — Concrete beam bending check (EN 1992)

This tutorial shows how to define concrete and reinforcement materials, then
check the bending resistance of a rectangular section.

```python
import eurocodepy as ec

# 1. Define materials
concrete = ec.Concrete('C30/37')   # fck = 30 MPa
reinf    = ec.Reinforcement('B500B')  # fyk = 500 MPa

print(f"fck  = {concrete.fck} MPa")
print(f"fcd  = {concrete.fcd:.2f} MPa")   # design value (fck / γc)
print(f"fyk  = {reinf.fyk} MPa")
print(f"fyd  = {reinf.fyd:.2f} MPa")      # design value (fyk / γs)

# 2. Section geometry
b   = 300   # width [mm]
h   = 500   # total depth [mm]
c   = 30    # nominal cover [mm]
phi = 16    # bar diameter [mm]
n   = 4     # number of bars

d   = h - c - phi / 2   # effective depth [mm]
As  = n * 3.14159 * (phi / 2) ** 2   # reinforcement area [mm²]
print(f"d    = {d:.1f} mm")
print(f"As   = {As:.1f} mm²")

# 3. Calculate design bending resistance (simplified rectangular stress block)
Mrd = ec.ec2.calc_mrd(b, d, As, concrete, reinf)
print(f"MRd  = {Mrd / 1e6:.2f} kNm")
```

---

## Tutorial 2 — Design response spectrum (EN 1998, Portuguese NA)

This tutorial generates and plots the horizontal elastic design spectrum for a
building in Lisbon using the Portuguese National Annex.

```python
import eurocodepy as ec

# Spectrum parameters
# locale   : 'PT'  — Portuguese national annex
# code     : 'PT-1' — type 1 spectrum (continental Portugal)
# imp_class: 'II'   — importance class II (ordinary buildings)
# soil     : 'C'    — medium-dense soil (Vs,30 = 180–360 m/s)
# zone     : '1_2'  — seismic zone 1.2
# behaviour: 3.0    — behaviour factor q for ductile frame

spec = ec.spectrum.get_spectrum_ec8(
    locale='PT',
    code='PT-1',
    imp_class='II',
    soil='C',
    zone='1_2',
    behaviour=3.0,
)

# Print a few values
print("ag   =", spec['ag'], "g")     # reference peak ground acceleration
print("S    =", spec['S'])           # soil factor
print("T_B  =", spec['TB'], "s")
print("T_C  =", spec['TC'], "s")
print("T_D  =", spec['TD'], "s")

# Plot
ec.spectrum.draw_spectrum_ec8(spec, show=True)

# Export to CSV for use in structural analysis software
ec.spectrum.write_spectrum_ec8(spec, filename='spectrum_PT1_II_C_1_2.csv')
```

---

## Tutorial 3 — Load combinations (EN 1990)

This tutorial builds a set of ULS and SLS load combinations from individual loads.

```python
from eurocodepy.ec1 import (
    Load, LoadType, LoadCombinations, CombinationType
)

# Define individual characteristic loads
G1 = Load('Self-weight', LoadType.PERMANENT, gk=10.0)   # [kN/m²]
Q1 = Load('Live load',   LoadType.LIVE,      qk=5.0)
W1 = Load('Wind',        LoadType.WIND,      qk=3.0)
S1 = Load('Snow',        LoadType.SNOW,      qk=1.5)

# Build all combinations
combos = LoadCombinations([G1, Q1, W1, S1])

# Retrieve ULS combinations (EN 1990 expression 6.10)
for combo in combos.get(CombinationType.ULS):
    print(combo)

# Retrieve SLS quasi-permanent combinations
for combo in combos.get(CombinationType.SLS_QP):
    print(combo)
```

---

## Tutorial 4 — Timber bending check (EN 1995)

```python
from eurocodepy.ec5.materials import SolidTimber, ServiceClass, LoadDuration

# Define timber grade
timber = SolidTimber('C24')

# Material properties
print(f"fm,k  = {timber.fmk} MPa")        # characteristic bending strength
print(f"E0,mean = {timber.E0mean} MPa")   # mean modulus of elasticity

# Modification factor for Service Class 1, Medium-term loading
kmod = timber.k_mod(
    service_class=ServiceClass.SC1,
    load_duration=LoadDuration.Medium,
)
print(f"kmod  = {kmod}")

# Design bending strength
gamma_m = 1.3   # partial factor for solid timber (Table 2.3 EN 1995)
fm_d = kmod * timber.fmk / gamma_m
print(f"fm,d  = {fm_d:.2f} MPa")
```

---

## Tutorial 5 — Steel section and bearing capacity (EN 1993 / EN 1997)

```python
import eurocodepy as ec

# Steel section
steel   = ec.Steel('S355')
profile = ec.ec3.materials.ProfileI('IPE300')

print(f"fy   = {steel.fy} MPa")
print(f"A    = {profile.A} mm²")
print(f"Iy   = {profile.Iy:.0f} mm⁴")

# Shallow foundation bearing capacity (EN 1997)
soil = ec.ec7.Soil('Sand-medium')
bc   = ec.ec7.bearing_resistance(
    B=1.5, L=2.0, D=0.8,
    phi=30.0, c=0.0, gamma=18.0,
    Vd=200.0, Hd=20.0,
)
print(f"R/A  = {bc:.1f} kPa")
```

