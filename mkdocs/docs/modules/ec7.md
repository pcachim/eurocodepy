# Eurocode 7 module: `ec7`

## Overview

The `ec7` module provides tools for geotechnical design according to EN 1997-1:
soil definitions, partial factors of the design approaches, bearing resistance of shallow
foundations (static and seismic, EN 1998-5) and earth pressure coefficients.

**Angles are in radians** in the calculation functions (`bearing_resistance`, `seismic_bearing_resistance`,
`pressure_coefficients`). `Soil(friction_angle=30.0)` takes degrees and stores radians.

---

## Soil materials

### `Soil` and `SoilEnum`

```python
from eurocodepy.ec7 import Soil, SoilEnum

soil = Soil("Dense sand", unit_weight=19.0, friction_angle=34.0, cohesion=0.0)   # degrees, kN/m³, kPa
soil.unit_weight, soil.friction_angle, soil.cohesion          # friction_angle in radians
soil.is_drained, soil.is_coherent, soil.young, soil.poiss, soil.ks, soil.sig_adm

SoilEnum.Sand, SoilEnum.Clay, SoilEnum.Gravel, SoilEnum.Rock   # typical soils
```

### `SoilSafetyFactors` and `SoilSafetyFactorsEnum`

Partial factors of the geotechnical design approaches (EN 1997-1).

```python
from eurocodepy.ec7 import SoilSafetyFactorsEnum

sf = SoilSafetyFactorsEnum.STRGEO_A2
sf.phi, sf.c, sf.cu, sf.gamma                  # on tan φ', c', cu and γ
sf.perm_unfav, sf.var_unfav                    # on actions
sf.bearing, sf.slide                           # on resistances
```

Members (each is a `SoilSafetyFactors`): `EQU`, `EQU_ACC`, `STRGEO_A1`, `STRGEO_A2`, `STRGEO_B`, `STRGEO_C`, `STRGEO_ACC`, `STRGEO_SLS`.

### Seismic parameters

```python
from eurocodepy.ec7 import get_soil_seismic_parameters, soil_gamma_rd

params = get_soil_seismic_parameters("S1", "PT", "C", "ii", "PT1", "1_2")   # name, code, soil, class, spectrum, zone
params.alpha, params.smax, params.avg_ahg, params.r
params.kh, params.kv                             # horizontal and vertical seismic coefficients

soil_gamma_rd["compact sand"]                    # γRd by soil type: 1.0, 1.15, 1.5 …
```

### `SoilSurcharge`

`SoilSurcharge(q=10.0, psi0=0.6, psi1=0.4, psi2=0.2)`: a surcharge on the soil surface with its combination coefficients.

---

## Bearing resistance — `ec7.bearing_capacity`

```python
import numpy as np
from eurocodepy.ec7 import bearing_resistance, seismic_bearing_resistance

phi = np.radians(30.0)

# EN 1997-1: effective width Bx, length By, horizontal loads Hx, Hy and vertical load N
# [m, kN], effective friction angle, unit weight [kN/m³], surcharge beside the footing q [kPa], cohesion c
q = 0.8 * 18.0
r = bearing_resistance(Bx=1.5, By=2.0, Hx=20.0, Hy=0.0, N=200.0, phi=phi, gamma=18.0, q=q, c=0.0)

# EN 1998-5: True where the verification is satisfied (two vertical directions)
ok = seismic_bearing_resistance(ag=0.2, avg_ahg=0.5, S=1.4, B=1.5, H=20.0, N=200.0, M=10.0,
                                phi=phi, gamma_s=18.0)            # cu=..., soil_type="coherent" for clays
```

`bearing_resistance` also takes arrays (one value per combination).

---

## Earth pressures — `ec7.earth_pressures`

```python
import numpy as np
from eurocodepy.ec7 import pressure_coefficients, EarthPressureModels

phi, delta = np.radians(30.0), np.radians(15.0)      # soil and wall friction angles
theta, beta = 0.0, 0.0                                # backfill slope and wall inclination
Ka, Kp, Kaq, Kpq, dkas1, dkps1, dkas2, dkps2 = pressure_coefficients(
    phi, delta, theta, beta, method=EarthPressureModels.COULOMB)
```

Methods (`EarthPressureModels`): `RANKINE`, `COULOMB`, `EC7` (the default) and
`INREST`. `Kaq` and `Kpq` are the coefficients at rest; `dkas*` and `dkps*` the seismic increments of EN 1998-5
when `seismic=` (a `SoilSeismicParameters`) is given.

---

## Compliance

Calculations follow EN 1997-1:2004. Seismic bearing resistance follows EN 1998-5.

## Further reading

- [EN 1997-1 — Geotechnical design](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-7-geotechnical-design)
