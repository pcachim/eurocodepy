# Eurocode 7 Module: `ec7`

## Overview

The `ec7` module of the *eurocodepy* package is a toolkit designed to assist engineers and geotechnical professionals in calculating and analyzing earth pressure coefficients and soil bearing capacity based on Eurocode 7 (EN 1997) standards.

## Features

- **Active Earth Pressure Analysis**  
  Perform active earth pressure calculations according to Eurocode 7.  
  Input parameters include soil properties, wall geometry, and external loads.  
  Output results include the magnitude and distribution of active earth pressure on the retaining structure.

- **Soil Bearing Capacity Analysis**  
  Calculate soil bearing capacity based on Eurocode 7 guidelines.  
  Input parameters include soil properties, foundation geometry, and relevant loadings.  
  Output results include the ultimate and allowable bearing capacities for shallow foundations.

## Typical Usage

```python
from eurocodepy.ec7 import pressure_coefficients, bearing_resistance

# Example for Active Earth Pressure
active_pressure_calculator = ActiveEarthPressure()
active_pressure_calculator.set_soil_properties(...)
active_pressure_calculator.set_wall_geometry(...)
active_pressure_calculator.set_external_loads(...)
active_pressure_calculator.calculate_active_pressure()
results = active_pressure_calculator.get_results()

# Example for Soil Bearing Capacity
bearing_capacity_calculator = SoilBearingCapacity()
bearing_capacity_calculator.set_soil_properties(...)
bearing_capacity_calculator.set_foundation_geometry(...)
bearing_capacity_calculator.set_loadings(...)
bearing_capacity_calculator.calculate_bearing_capacity()
results = bearing_capacity_calculator.get_results()
```

## Compliance

All calculations and checks are based on the requirements and recommendations of Eurocode 7 (EN 1997). The module is updated to reflect changes and amendments to the code.

## Further Reading

- [Eurocode 7: Geotechnical design (EN 1997)](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-7-geotechnical-design)
- [eurocodepy Documentation](../index
