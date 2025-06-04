# Eurocode 7: ec7 module

## Overview

Welcome to the ec7 module off *eurocodepy* package. This module is a toolkit designed to assist engineers and geotechnical professionals in calculating and analyzing earth pressure coefficients and soil bearing capacity based on the Eurocode 7 (EC7) standards.

## Features

1. Active Earth Pressure Analysis
Perform active earth pressure calculations according to Eurocode 7 standards.
Input parameters include soil properties, wall geometry, and external loads.
Output results include the magnitude and distribution of active earth pressure on the retaining structure.
2. Soil Bearing Capacity Analysis
Calculate soil bearing capacity based on the Eurocode 7 guidelines.
Input parameters include soil properties, foundation geometry, and relevant loadings.
Output results include the ultimate and allowable bearing capacities for shallow foundations.
3. Compliance with Eurocode 7
The package adheres to the Eurocode 7 standards, ensuring accurate and reliable calculations.
Regular updates will be provided to align with any changes or amendments to the Eurocode 7 specifications.
Installation

## Usage

Import the *eurocodepy* package 
Initialize the active earth pressure or soil bearing capacity calculation objects.
Set the input parameters such as soil properties, wall/foundation geometry, and loads.
Run the calculation method to obtain the results.
Access the output data and analyze the results.

```python
# Import the EC7Package module
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
Contribution Guidelines
```

