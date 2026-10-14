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
print(steel.fyk, steel.fuk)

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
from eurocodepy import NationalParams, get_national_params, seismic_get_params, wind_get_params

# Data of a municipality (seismic zones, accelerations, snow and wind zones, temperatures)
data = get_national_params(concelho='Coimbra')
print(data['ZonaSismica1'], data['Acel1'], data['ZonaVento'])

# Spectrum parameters of the Portuguese NA: code, type, soil, importance class
seismic = seismic_get_params('PT', 'PT1', 'C', 'ii')
print(seismic)           # S_max, S_min, a_g1, a_g2, T_B, T_C, T_D, ImportanceCoef

# Wind: vb,0, z_min, z_0 and z_0,II of a zone and terrain category
vb0, z_min, z0, z0_ii = wind_get_params('PT', 'ZonaA', 'II')

# NationalParams holds the locale and the municipality (default: Lisboa)
params = NationalParams(concelho='Braga')
print(params.local, params.concelho)
```

---

## How to define a unit system

```python
from eurocodepy.units import SI, kN_mm, N_mm, UnitType

# Each system gives the SI value of its units
print(SI.force, SI.distance, SI.pressure)              # N, m, Pa
print(kN_mm.force, kN_mm.distance, kN_mm.pressure)     # kN, mm, kN/mm²
print(N_mm.force, N_mm.distance, N_mm.pressure)        # N, mm, N/mm²

# Factor that converts a value from one system to another
f = SI.convert_to(kN_mm, UnitType.FORCE)               # newtons -> kilonewtons: 0.001
```

---

## How to build load combinations

```python
from eurocodepy.ec1 import Load, LoadType, Loads

loads = Loads()
#                  name  type                 γ fav  γ unf  ψ0   ψ1   ψ2
loads.add(Load("G", LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
loads.add(Load("Q", LoadType.LIVE,      0.0, 1.50, 0.7, 0.5, 0.3))
loads.add(Load("W", LoadType.WIND,      0.0, 1.50, 0.6, 0.2, 0.0))

values = {"G": 20.0, "Q": 8.0, "W": 4.0}                 # characteristic values [kN/m²]

# ULS (EN 1990 Eq. 6.10): a dict {name: LoadCombination}; factors = {load name: (Load, factor)}
for name, combo in loads.get_ULS_combos().items():
    total = sum(factor * values[k] for k, (_, factor) in combo.factors.items())
    print(f"{name:34s} {total:7.2f}")

# SLS characteristic, frequent and quasi-permanent
for name, combo in loads.get_SLS_combos().items():
    print(name)
```

---

## How to calculate creep and shrinkage (EN 1992-1-1:2023, Annex B)

```python
from eurocodepy.ec2.sls.creep import creep_coef
from eurocodepy.ec2.sls.shrinkage import shrink_strain

# C30/37: fcm,28 = 38 MPa; RH = 60 %; hn = 2Ac/u = 200 mm; class CN
# Creep coefficient φ(t, t0): loaded at t0 = 28 days, t = 50 years
phi = creep_coef(t=18250 + 28, t0=28, fcm28=38.0, RH=60, hn=200, t0_T=28, concrete_class="CN")
print(f"φ = {phi:.2f}")

# Total shrinkage strain, drying from ts = 1 day (alpha_NDP_b = alpha_NDP_d = 1: recommended)
eps_cs = shrink_strain(t=18251, ts=1, fcm28=38.0, RH=60, hn=200, concrete_class="CN",
                       alpha_NDP_b=1.0, alpha_NDP_d=1.0)
print(f"εcs = {eps_cs:.6f}")
```

---

## How to follow the strain history of a concrete member (EN 1992-1-1:2023, Annex B)

```python
from eurocodepy.ec2 import time_dependent2023 as td

fcm, ecm = 38.0, 33000.0          # C30/37: fcm,28 and Ecm,28 [MPa]
common = dict(fcm28=fcm, ecm28=ecm, rh=60.0, hn=200.0, cls="CN")

# Compressive stress of 10 MPa applied at 28 days, 5 MPa more at 90 days: stress-dependent strain at 50 years
eps = td.strain_history(18278, [(28, -10.0), (90, -5.0)], **common)

# Compliance J(t, t0) and the shrinkage at the same age
j = td.creep_compliance(18278, 28, **common)                  # 1/MPa
eps_cs = td.shrinkage_total(18278, 1, fcm, rh=60.0, hn=200.0, cls="CN")
```

---

## How to use the partial factors of another design situation (EN 1992-1-1:2023, Table 4.3)

```python
from eurocodepy.ec2 import Concrete, material_partial_factors

material_partial_factors("2023", "accidental")                 # γs, γc, γce, γv of the situation
accidental = Concrete("C30/37", edition="2023", situation="accidental")
print(accidental.gamma_c, accidental.fcd)
```

The check inputs (`PunchInput`, `ShearInput`, `MembraneInput`, …) have `from_partial_factors(edition, situation, ...)`.

---

## How to produce a calculation report

Most checks accept `trace=` with a `CalcReport`: each step (symbol, value, unit, clause, expression) is recorded
and the report can be written as a dictionary, JSON or Markdown with LaTeX.

```python
from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2.uls import design_anchorage_length

report = CalcReport(title="Anchorage of a ϕ16 bar")
anchorage = design_anchorage_length(phi=16, fck=30, fyk=500, cd=40, good_bond=True, trace=report)

print(report.to_markdown())          # sections with the clause and the formula of each step
data = report.to_dict()              # {'schema_version', 'title', 'meta', 'sections': [...]}
```

The checks of EC2 (`uls`, `uls2023`), EC3 (`section_check_profile`, `member_check_profile`,
`classify_section`) and EC5 take it; with `trace=None` (the default) nothing is recorded.

---

## How to check shear resistance of a concrete beam (EN 1992)

```python
from eurocodepy.ec2.uls.shear import calc_vrdc, calc_vrd, calc_vrdmax, calc_asws

# Section and material
b_w = 0.30   # web width [m]
d   = 0.46   # effective depth [m]
rho = 0.0117 # tensile reinforcement ratio As/(b_w·d)
fck, g_c = 30, 1.5     # [MPa]
fyk, g_s = 500, 1.15   # shear reinforcement [MPa]

# Design shear resistance without shear reinforcement [kN]
vrd_min, vrd_c, vrd = calc_vrdc(b_w, d, fck, g_c, rho)
print(f"VRd,c = {vrd:.1f} kN")

# Required shear reinforcement for VEd = 180 kN, cot θ = 2
asw_s, vrd_max = calc_asws(b_w, d, fck, g_c, fyk, g_s, 2.0, 180.0)
print(f"Asw/s = {asw_s * 1e4:.2f} cm²/m (VRd,max = {vrd_max:.0f} kN)")
```

---

## How to compute earth pressures (EN 1997)

```python
import numpy as np
from eurocodepy.ec7 import pressure_coefficients, EarthPressureModels

phi   = np.radians(30.0)   # soil friction angle
delta = np.radians(15.0)   # wall friction angle
theta = 0.0                # slope of the backfill
beta  = 0.0                # slope of the wall

# Ka, Kp, Kaq, Kpq, dkas1, dkps1, dkas2, dkps2
Ka, Kp, *_ = pressure_coefficients(phi, delta, theta, beta, method=EarthPressureModels.COULOMB)
print(f"Ka = {Ka:.3f},  Kp = {Kp:.3f}")
```

---

## How to plot and export a seismic spectrum

```python
from eurocodepy.ec8.spectrum import get_spectrum_ec8, draw_spectrum_ec8, write_spectrum_ec8

spec = get_spectrum_ec8(
    locale='EU', code='CEN_1',
    imp_class='II', soil='B',
    zone='.3g', behaviour=4.0,
)

# Display the plot interactively
draw_spectrum_ec8(spec, show=False)   # show=True opens the window

# Save a CSV for import into SAP2000, ETABS, etc.
write_spectrum_ec8(spec, filename='spectrum_EU_CEN1_II_B_03g_q4.csv')
```

---

## How to calculate section properties

```python
from eurocodepy.utils import RectangularCrossSection

section = RectangularCrossSection(0.30, 0.60)      # m
print(section.area, section.inertia_y, section.bend_mod_y)
```

For reinforced sections (cracked and uncracked properties) see
`utils.calc_section_rectangular` in the [utils module](modules/utils.md).

---

## How to use a National Annex

The values in `eurocodes.json` are the ones recommended by the Eurocodes. What a National
Annex changes is a patch kept in its own file, `data/national_annexes/<COUNTRY>.json`
(Portugal's is built in: its wind, seismic and live-load data). The functions that depend on
Nationally Determined Parameters take `annex=` with the country code:

```python
from eurocodepy.ec2 import Concrete, material_partial_factors
from eurocodepy.ec2.uls2023 import detailing

Concrete("C30/37", edition="2023", annex="PT")        # the annex's values, if it has any
material_partial_factors("2023", "persistent")         # annex=None: the Eurocode's values
detailing.beam_max_spacings(0.5, annex="PT")
```

An unknown code raises `ValueError` and lists the available ones. Add your own annex (a JSON
file or a dict) with `register_annex`; it has the same shape as the `Editions` entries of
`eurocodes.json`, so it patches one value of a table and leaves the rest as recommended:

```python
import eurocodepy as ec

ec.register_annex({
    "country": "XX",
    "editions": {"ec2": {"2023": {
        "partial_factors": {"materials": {"persistent": {"gamma_c": 1.4}}},
        "detailing": {"beams": {"s_l_max": 0.7}},
    }}},
})
Concrete("C30/37", edition="2023", annex="XX").gamma_c    # 1.4
ec.available_annexes()                                      # ['PT', 'XX']
```

`loads` (`wind`, `seismic`, `live`) in the file add the country next to `EU`, so
`wind_get_params("XX", ...)` and the EC1/EC7/EC8 functions find it. The package only ships the
values it can source; it never invents an annex.
