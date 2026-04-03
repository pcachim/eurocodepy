# Eurocode 7 module: `ec7`

## Overview

The `ec7` module provides tools for geotechnical design according to EN 1997-1.
It covers soil material definitions, bearing resistance of shallow foundations,
seismic bearing capacity, and earth pressure coefficients.

---

## Soil materials

### `Soil`

```python
from eurocodepy.ec7 import Soil, SoilEnum

soil = Soil('Sand-medium')
soil.phi     # friction angle [°]
soil.c       # cohesion [kPa]
soil.gamma   # unit weight [kN/m³]
```

Available soil types are accessible via `SoilEnum`.

### `SoilSafetyFactors` and `SoilSafetyFactorsEnum`

Partial factors for soil strength parameters (Design Approaches 1, 2, 3).

```python
from eurocodepy.ec7 import SoilSafetyFactors, SoilSafetyFactorsEnum

sf = SoilSafetyFactors(SoilSafetyFactorsEnum.DA1_C2)
sf.gamma_phi   # partial factor on tan(φ)
sf.gamma_c     # partial factor on cohesion c
```

### `SoilSeismicParameters` and `get_soil_seismic_parameters`

```python
from eurocodepy.ec7 import SoilSeismicParameters, get_soil_seismic_parameters

params = get_soil_seismic_parameters(soil_type='C')
params.S       # soil amplification factor
params.Vs30    # shear wave velocity [m/s]
```

### `SoilSurcharge`

Represents a surcharge load applied to the soil surface.

---

## Bearing resistance — `ec7.bearing_capacity`

```python
from eurocodepy.ec7 import bearing_resistance, seismic_bearing_resistance, soil_gamma_rd

# Bearing resistance of a shallow foundation (EN 1997-1 Annex D)
R_d = bearing_resistance(
    B=1.5,      # foundation width [m]
    L=2.0,      # foundation length [m]
    D=0.8,      # embedment depth [m]
    phi=30.0,   # friction angle [°]
    c=0.0,      # cohesion [kPa]
    gamma=18.0, # unit weight of soil [kN/m³]
    Vd=200.0,   # design vertical load [kN]
    Hd=20.0,    # design horizontal load [kN]
)
print(f"Rd = {R_d:.1f} kN")

# Seismic bearing resistance (EN 1998-5)
R_seismic = seismic_bearing_resistance(...)

# Partial resistance factor
gamma_Rd = soil_gamma_rd(design_approach=SoilSafetyFactorsEnum.DA2)
```

---

## Earth pressures — `ec7.earth_pressures`

```python
from eurocodepy.ec7 import pressure_coefficients, EarthPressureModels

# Compute active and passive pressure coefficients
Ka, Kp = pressure_coefficients(
    phi=30.0,    # soil friction angle [°]
    delta=15.0,  # wall friction angle [°]
    beta=0.0,    # slope angle behind wall [°]
    alpha=90.0,  # wall inclination from horizontal [°]
    model=EarthPressureModels.Rankine,
)
print(f"Ka = {Ka:.3f},  Kp = {Kp:.3f}")
```

Available models (`EarthPressureModels`): `Rankine`, `Coulomb`.

---

## Compliance

Calculations follow EN 1997-1:2004. Seismic bearing resistance follows EN 1998-5.

## Further reading

- [EN 1997-1 — Geotechnical design](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-7-geotechnical-design)

