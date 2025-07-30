# Eurocode 3 module: `ec3`

## Overview

The `ec3` module of the *eurocodepy* package provides a toolkit for the analysis and design of steel structures in accordance with Eurocode 3 (EN 1993-1-1). It is intended for engineers and researchers who require reliable and efficient tools for structural calculations, checks, and code compliance for steel members and connections.

## Features

- **Section Analysis**  
  Calculate section properties for common steel profiles (I, H, channel, angle, etc.).
- **Material Models**  
  Access and use steel grades and material properties as per Eurocode 3.
- **Member Checks**  
  Functions for cross-section classification, axial, bending, shear, and combined checks.
- **Buckling and Stability**  
  Tools for flexural, lateral-torsional, and local buckling checks.
- **Connection Design**  
  Utilities for bolted and welded connection design and verification.
- **Serviceability Limit States (SLS)**  
  Deflection and vibration checks for steel members.
- **Utilities**  
  Helper functions for geometric and mechanical properties, slenderness, and more.

## Typical Usage

```python
from eurocodepy.ec3 import Steel, Section, member_buckling_check, cross_section_class

# Define material and section
steel = Steel('S355')
section = Section('IPE300')

# Section properties
area = section.area
Iy = section.Iy

# Cross-section classification
cls = cross_section_class(section, steel)

# Member buckling check
N_Ed = 500e3  # Applied axial force [N]
L = 6.0       # Member length [m]
buckling_ok = member_buckling_check(section, steel, N_Ed, L)
```

## Compliance

All calculations and checks are based on the requirements and recommendations of Eurocode 3 (EN 1993-1-1).

## Further Reading

- [Eurocode 3: Design of steel structures (EN 1993-1-1)](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-3-design-steel-structures)
- [eurocodepy Documentation](../index.md)
