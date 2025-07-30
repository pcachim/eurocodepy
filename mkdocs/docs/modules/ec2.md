# Eurocode 2 module: `ec2`

## Overview

The `ec2` module of the *eurocodepy* package provides a toolkit for the analysis and design of reinforced concrete structures in accordance with Eurocode 2 (EN 1992-1-1). It is intended for engineers and researchers who require reliable and efficient tools for structural calculations, checks, and code compliance.

## Features

- **Section Analysis**  
  Calculate section properties for rectangular, T, and other common concrete sections.
- **Material Models**  
  Access and use concrete and reinforcement grades as per Eurocode 2.
- **Crack Control**  
  Functions for crack width calculation, reinforcement ratio, and crack spacing.
- **Serviceability Limit States (SLS)**  
  Tools for deflection, crack width, and stress checks.
- **Ultimate Limit States (ULS)**  
  Flexural, shear, and axial capacity checks for reinforced concrete members.
- **Utilities**  
  Helper functions for geometric and mechanical properties, modular ratios, and more.

## Typical Usage

```python
from eurocodepy.ec2 import Concrete, Reinforcement, crack_opening, sr_max

# Define materials
conc = Concrete('C30/37')
reinf = Reinforcement('B500B')

# Section and reinforcement data
b = 300      # mm
h = 500      # mm
phi = 16     # mm
As = 4 * 201 # mm² (4 bars of 16 mm)
c = 25       # mm (cover)

# Calculate effective reinforcement ratio, crack spacing, and crack width
Ac_eff = b * 100  # Example effective area in tension [mm²]
rho_p_eff = As / Ac_eff
s_r_max = sr_max(c, phi, rho_p_eff)
# ... further calculations for crack width, etc.
```

## Compliance

All calculations and checks are based on the requirements and recommendations of Eurocode 2 (EN 1992-1-1).

## Further Reading

- [Eurocode 2: Design of concrete structures (EN 1992-1-1)](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-2-design-concrete-structures)
- [eurocodepy Documentation](../index.md)
