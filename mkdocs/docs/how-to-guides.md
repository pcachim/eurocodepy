# How-to Guides

Practical recipes for common tasks. Unlike tutorials, each guide assumes you already
have EurocodePy installed and focuses on getting one specific thing done.

---

## How to look up a material

```python
import eurocodepy as ec

# Concrete — access all grades via the enum
concrete = ec.Concrete('C25/30')
print(concrete.fck, concrete.fcd, concrete.Ecm)

# Steel
steel = ec.Steel('S275')
print(steel.fy, steel.fu)

# Timber
timber = ec.Timber('GL28h')
print(timber.fmk, timber.E0mean)
```

Alternatively browse the raw database:

```python
# List all available concrete grades
print(list(ec.ConcreteGrades))

# List all reinforcement grades
print(list(ec.ReinforcementGrades))

# List all timber grades
print(list(ec.TimberGrades))
```

---

## How to access Portuguese national annex parameters

```python
from eurocodepy.national_parameters import NationalParams, seismic_get_params, wind_get_params

# Seismic parameters for a municipality
seismic = seismic_get_params('Coimbra')
print(seismic)   # peak ground acceleration, seismic zone, etc.

# Wind parameters
wind = wind_get_params('Porto')
print(wind)

# Or use the NationalParams dataclass (defaults to Lisboa)
params = NationalParams(concelho='Braga')
print(params.data)
```

---

## How to define a unit system

```python
from eurocodepy.units import SI, kN_mm, N_mm, UnitSystem

# SI units (N, m, Pa) — the default
print(SI.force, SI.length, SI.pressure)

# kN / mm system — common in structural engineering practice
print(kN_mm.force, kN_mm.length, kN_mm.pressure)

# N / mm system
print(N_mm.force, N_mm.length, N_mm.pressure)
```

---

## How to build load combinations

```python
from eurocodepy.ec1 import Load, LoadType, LoadCombinations, CombinationType

loads = [
    Load('G',  LoadType.PERMANENT, gk=20.0),
    Load('Q',  LoadType.LIVE,      qk=8.0),
    Load('W',  LoadType.WIND,      qk=4.0),
]
combos = LoadCombinations(loads)

# All ULS combinations
for c in combos.get(CombinationType.ULS):
    print(c)

# SLS characteristic combinations
for c in combos.get(CombinationType.SLS_K):
    print(c)
```

---

## How to calculate creep and shrinkage (EN 1992-1-1:2025)

```python
from eurocodepy.ec2.sls.creep import creep_coef
from eurocodepy.ec2.sls.shrinkage import shrink_strain

# Creep coefficient φ(t, t₀)
# fck=30 MPa, RH=60%, h0=200mm (notional size), t0=28 days, t=18250 days (~50yr)
phi = creep_coef(fck=30, RH=60, h0=200, t0=28, t=18250)
print(f"φ = {phi:.2f}")

# Total shrinkage strain
eps_sh = shrink_strain(fck=30, RH=60, h0=200, t=18250, t_s=7)
print(f"εsh = {eps_sh:.6f}")
```

---

## How to check shear resistance of a concrete beam (EN 1992)

```python
from eurocodepy.ec2.uls.shear import calc_vrdc, calc_vrd, calc_vrdmax, calc_asws

# Section and material
b_w = 300    # web width [mm]
d   = 460    # effective depth [mm]
As  = 1608   # tensile reinforcement area [mm²]
fck = 30     # characteristic compressive strength [MPa]
fyk = 500    # characteristic yield strength of shear reinforcement [MPa]

# Design shear resistance without shear reinforcement
VRd_c = calc_vrdc(b_w, d, As, fck)
print(f"VRd,c = {VRd_c/1e3:.1f} kN")

# Required shear reinforcement for VEd = 180 kN
VEd   = 180e3   # [N]
Asw_s = calc_asws(b_w, d, VEd, fyk)
print(f"Asw/s = {Asw_s:.2f} mm²/mm")
```

---

## How to compute earth pressures (EN 1997)

```python
from eurocodepy.ec7 import pressure_coefficients, EarthPressureModels

phi   = 30.0   # friction angle [°]
delta = 15.0   # wall friction angle [°]
beta  = 0.0    # slope angle [°]
alpha = 90.0   # wall inclination from horizontal [°]

Ka, Kp = pressure_coefficients(
    phi, delta, beta, alpha,
    model=EarthPressureModels.Rankine,
)
print(f"Ka = {Ka:.3f},  Kp = {Kp:.3f}")
```

---

## How to plot and export a seismic spectrum

```python
from eurocodepy.ec8.spectrum import get_spectrum_ec8, draw_spectrum_ec8, write_spectrum_ec8

spec = get_spectrum_ec8(
    locale='EU', code='CEN-1',
    imp_class='II', soil='B',
    zone='.3g', behaviour=4.0,
)

# Display the plot interactively
draw_spectrum_ec8(spec, show=True)

# Save a CSV for import into SAP2000, ETABS, etc.
write_spectrum_ec8(spec, filename='spectrum_EU_CEN1_II_B_03g_q4.csv')
```

---

## How to calculate section properties

```python
from eurocodepy.utils import section_properties, crosssection

# Rectangular uncracked section
props = section_properties(b=300, h=600)
print(props['A'], props['Iy'], props['Wel_y'])

# Or use the lower-level crosssection helper for custom shapes
cs = crosssection([(0, 0), (300, 0), (300, 600), (0, 600)])
print(cs)
```

