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
Mrd, eps_s, x = ec.ec2.calc_mrd(b / 1000, d / 1000, As / 100, concrete.fcd, reinf.fyd)   # m, cm²
print(f"MRd  = {Mrd:.1f} kNm")

# 4. The same section with the second-generation code (EN 1992-1-1:2023)
concrete23 = ec.ec2.get_concrete('C30/37', edition='2023')   # fcd = η_cc·k_tc·fck/γc, Eq. 5.3
reinf23 = ec.ec2.Reinforcement('B500B', edition='2023')
print(f"fcd (2023) = {concrete23.fcd:.2f} MPa,  fyd (2023) = {reinf23.fyd:.2f} MPa")
Mrd23, eps_s, x = ec.ec2.calc_mrd(b / 1000, d / 1000, As / 100, concrete23.fcd, reinf23.fyd)
print(f"MRd (2023) = {Mrd23:.1f} kNm")

# For fck > 40 MPa the 2023 design strength is reduced by η_cc, and k_tc depends on the loading
c50 = ec.ec2.get_concrete('C50/60', edition='2023', loading='other')
print(f"C50/60: η_cc = {c50.eta_cc:.3f}, k_tc = {c50.k_tc}, fcd = {c50.fcd:.2f} MPa")
```

---

## Tutorial 2 — Design response spectrum (EN 1998, Portuguese NA)

This tutorial generates and plots the horizontal elastic design spectrum for a
building in Lisbon using the Portuguese National Annex.

```python
import eurocodepy as ec

# Spectrum parameters
# locale   : 'PT'  — Portuguese national annex
# code     : 'PT1' — type 1 spectrum (continental Portugal)
# imp_class: 'II'   — importance class II (ordinary buildings)
# soil     : 'C'    — medium-dense soil (Vs,30 = 180–360 m/s)
# zone     : '1_2'  — seismic zone 1.2
# behaviour: 3.0    — behaviour factor q for ductile frame

spec = ec.spectrum.get_spectrum_ec8(
    locale='PT',
    code='PT1',
    imp_class='II',
    soil='C',
    zone='1_2',
    behaviour=3.0,
)

# Print a few values
print("ag   =", spec.attrs['a_g'], "m/s2")   # design ground acceleration
print("S    =", spec.attrs['S'])             # soil factor
print("peak =", spec['value'].max(), "m/s2") # largest ordinate of the design spectrum

# Plot (show=True opens the window)
ec.spectrum.draw_spectrum_ec8(spec, show=False)

# Export to CSV for use in structural analysis software
ec.spectrum.write_spectrum_ec8(spec, filename='spectrum_PT1_II_C_1_2.csv')
```

---

## Tutorial 3 — Load combinations (EN 1990)

This tutorial builds a set of ULS and SLS load combinations from individual loads.

```python
from eurocodepy.ec1 import Load, LoadType, Loads

# Each load carries its partial factors (γ favourable and unfavourable) and ψ0, ψ1, ψ2
loads = Loads()
loads.add(Load("Self-weight", LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
loads.add(Load("Live load",   LoadType.LIVE,      0.0, 1.50, 0.7, 0.5, 0.3))
loads.add(Load("Wind",        LoadType.WIND,      0.0, 1.50, 0.6, 0.2, 0.0))
loads.add(Load("Snow",        LoadType.SNOW,      0.0, 1.50, 0.5, 0.2, 0.0))

# ULS combinations (EN 1990 expression 6.10): {name: LoadCombination}
for name in loads.get_ULS_combos():
    print(name)

# SLS combinations: characteristic (SLS-K), frequent (SLS-FR) and quasi-permanent (SLS-QP)
for name, combo in loads.get_SLS_combos().items():
    if combo.type.value == "SLS-QP":
        print(name)

# Apply a combination to the values of the loads (here kN/m²)
values = {"Self-weight": 10.0, "Live load": 5.0, "Wind": 3.0, "Snow": 1.5}
combo = next(iter(loads.get_ULS_combos().values()))
print(sum(f * values[k] for k, (_, f) in combo.factors.items()))
```

---

## Tutorial 4 — Timber bending check (EN 1995)

This tutorial gets the design bending strength of a solid timber member from its strength class, the
service class and the load duration.

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
    load_duration=LoadDuration.MediumDuration,
)
print(f"kmod  = {kmod}")

# Design bending strength
fm_d = kmod * timber.fmk / timber.safety     # γM = 1.3 for solid timber (Table 2.3 EN 1995)
print(f"fm,d  = {fm_d:.2f} MPa")

# The same, in one call
print(timber.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)["fmd"])
```

---

## Tutorial 5 — Steel section and bearing capacity (EN 1993 / EN 1997)

A rolled I section is checked under bending and shear (EN 1993-1-1) and the bearing resistance of a
shallow foundation is computed (EN 1997-1). Profile properties are in cm, the bearing function takes
angles in radians.

```python
import numpy as np
import eurocodepy as ec

# Steel section (catalogue units: cm, cm², cm⁴)
steel   = ec.Steel('S355')
profile = ec.ec3.ProfilesI['IPE300']

print(f"fy   = {steel.fyk} MPa")
print(f"A    = {profile.A} cm²")
print(f"Iy   = {profile.Iy:.0f} cm⁴")

# Section check under MEd = 100 kNm and VEd = 80 kN
check = ec.ec3.section_check_profile(
    profile, steel.fyk, ec.ec3.SectionForces(my_ed=100.0, vz_ed=80.0))
print(f"utilization = {check.utilization:.2f}")

# Shallow foundation bearing capacity (EN 1997): angles in radians
phi = np.radians(30.0)
R = ec.ec7.bearing_resistance(
    Bx=1.5, By=2.0, Hx=20.0, Hy=0.0, N=200.0,    # m, kN
    phi=phi, gamma=18.0, q=0.8 * 18.0, c=0.0,
)
print(f"Rd   = {R:.1f}")
```

---

## Tutorial 6 — Slab or shell with shear: sandwich model, 2004 and 2023

A 200 mm slab-shell with membrane forces, bending, torsion and out-of-plane shear is designed with the
sandwich model of EN 1992-2 Annex LL (2004) and of EN 1992-1-1:2023, Annex G. Forces are per metre
(kN/m, kNm/m), lengths in m and strengths in MPa.

```python
from eurocodepy.ec2 import uls, uls2023

forces = dict(n_xx=100.0, n_yy=50.0, n_xy=20.0,         # membrane [kN/m]
              m_xx=20.0, m_yy=10.0, m_xy=5.0,           # bending and torsion [kNm/m]
              v_x=250.0, v_y=80.0)                      # out-of-plane shear [kN/m]
section = dict(fck=30.0, fyk=500.0, thickness=0.20, cover=0.04)

r04 = uls.eurocode2_shell_check(uls.ShellInput(**forces, **section))
r23 = uls2023.eurocode2_shell_check(uls2023.ShellInput(**forces, **section))

for name, r in (("2004", r04), ("2023", r23)):
    areas = [r.asx_bot, r.asy_bot, r.asx_top, r.asy_top]
    print(name, [f"{a * 1e4:.2f}" for a in areas], "cm²/m;",
          f"stirrups {r.asw_s * 1e4:.2f} cm²/m²;", "crushing:", r.crushing)
```

The four areas are the bars of the bottom and top faces in each direction; `asw_s` is the shear
reinforcement. Faces without tension give zero: no minimum reinforcement is added.

```python
# What each edition checked
r04.details["cracked"]          # LL (107): is the element cracked? (an uncracked one is not designed)
r04.details["shear"]["mode"]    # inner layer of Annex LL, with the chord force added to the outer layers
r23.details["method"]           # 'sandwich' (G.4(1)); 'optimum' (Tables G.2/G.3) when only moments act
r23.details["shear"]["tau_ed"], r23.details["shear"]["tau_rdc"]    # clause 8.2
```

Where the strut limits differ (`ν`, `fcd`) is where the editions part: try `fck=60.0`, or ask 2004 for the
refined EN 1992-2 6.109 limit with `strut_model="6.109"`. See
[Membranes, slabs and shells](modules/ec2/shells.md) for the clauses.
