# Eurocode 1 module: `ec1`

## Overview

The `ec1` module of the *eurocodepy* package provides tools for the analysis and design of structures subjected to actions as defined in Eurocode 1 (EN 1991). It is intended for engineers who need to calculate loads such as self-weight, imposed loads, wind, snow, and thermal actions in accordance with Eurocode 1 standards.

## Features

- **Load Calculations**  
  Functions to calculate self-weight, imposed loads, wind loads, snow loads, and thermal actions for buildings and civil engineering works.
- **Parameter Flexibility**  
  Input parameters include geometry, location, exposure, and usage category.

## Typical Usage

```python
from eurocodepy.ec1 import wind_load, snow_load, imposed_load

# Calculate wind load
wind = wind_load(height=15, exposure='B', location='coastal')

# Calculate snow load
snow = snow_load(altitude=500, location='mountain')

# Calculate imposed load for office
imposed = imposed_load(category='B', area=50)
```

## Compliance

All calculations and checks are based on the requirements and recommendations of Eurocode 1 (EN 1991). The module is updated to reflect changes and amendments to the code.

## Further Reading

- [Eurocode 1: Actions on structures (EN 1991)](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-1-actions-structures)

