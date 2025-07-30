# Eurocode 5 Module: `ec5`

## Overview

The `ec5` module of the *eurocodepy* package provides tools for the analysis and design of timber structures in accordance with Eurocode 5 (EN 1995-1-1). It is intended for engineers and researchers who require reliable and efficient tools for structural calculations, checks, and code compliance for timber members and assemblies.

## Features

- **Material Models**  
  Access characteristic and mean properties for solid timber (softwood, hardwood), glulam, and other timber products.
- **Service Classes and Load Duration**  
  Enumerations and functions for risk class, service class, and load duration as per Eurocode 5.
- **Strength and Stiffness Parameters**  
  Retrieve characteristic strengths, moduli of elasticity, shear moduli, and densities for a wide range of timber grades.
- **Modification and Partial Factors**  
  Functions for kmod, kdef, and other modification and safety factors.
- **Extensible Classes**  
  Base and specialized classes for Solid Timber, Glulam, CLT, LVL, and Wood-Based Panels.

## Typical Usage

```python
from eurocodepy.ec5.materials import Timber, SolidTimber, Glulam, ServiceClass, LoadDuration

# Create a solid timber object (e.g., C24)
timber = SolidTimber('C24')

# Access characteristic bending strength
fmk = timber.fmk

# Get kmod for Service Class 1 and Medium load duration
kmod = timber.k_mod(service_class=ServiceClass.SC1, load_duratiom=LoadDuration.Medium)

# Create a glulam object (e.g., GL24h)
glulam = Glulam('GL24h')
E0mean = glulam.E0mean
```

## Compliance

All calculations and checks are based on the requirements and recommendations of Eurocode 5 (EN 1995-1-1). The module is updated to reflect changes and amendments to the code.

## Further Reading

- [Eurocode 5: Design of timber structures (EN 1995-1-1)](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-5-design-timber-structures)
