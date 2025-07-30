# Utilities module: `utils`

## Overview

The `utils` module of the *eurocodepy* package provides a set of helper functions and classes to support geometric, mechanical, and mathematical operations commonly needed in structural engineering calculations. These utilities are used throughout the package to simplify section property calculations, conversions, and general-purpose tasks.

## Features

- **Section Geometry Calculations**  
  Functions for calculating properties of rectangular and T, section shapes, cracked and uncracked.
- **Principal stresses**  
  Tools for conversioncalculation of principal stress vectors and values and stress invariants.
- **General Helpers**  
  Functions for modular ratio, centroid, and other common engineering calculations.

## Typical Usage

```python
from eurocodepy.utils import calc_section_rectangular, sqrt_sum_of_squares

# Calculate properties of a rectangular section
b = 300  # mm
h = 500  # mm
section = calc_section_rectangular(b, h)
print("Area:", section['area'])
print("Moment of inertia:", section['Iy'])

# Calculate the square root of the sum of squares of a list
values = [3, 4, 12]
result = sqrt_sum_of_squares(values)
print("sqrt(sum of squares):", result)
```

## Further reading

- [eurocodepy Documentation](../index.md)
