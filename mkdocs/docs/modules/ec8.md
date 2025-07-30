# Eurocode 8 module: `ec8`

## Overview

The `ec8` module of the *eurocodepy* package provides tools for seismic analysis and design in accordance with Eurocode 8 (EN 1998-1). It enables engineers and researchers to generate design response spectra, retrieve national annex parameters, and visualize or export spectra for use in structural analysis.

## Features

- **Design Spectrum Generation**  
  Compute elastic response spectra for different countries, codes, soil types, seismic zones, and importance classes.
- **National Annex Support**  
  Includes standard Eurocode and Portuguese National Annex parameters.
- **Parameter Retrieval**  
  Functions to obtain soil amplification, reference acceleration, and spectrum shape parameters.
- **Custom/User-Defined Spectra**  
  Generate spectra for user-specified parameters.
- **Visualization and Export**  
  Plot spectra using matplotlib and export to CSV for use in structural software.

## Typical Usage

```python
from eurocodepy.ec8.spectrum import get_spectrum_ec8, draw_spectrum_ec8

# Generate a spectrum for Portugal, standard code, importance class II, soil C, zone 1_2, q=3.0
spec = get_spectrum_ec8(
    locale='PT',
    code='PT-1',
    imp_class='II',
    soil='C',
    zone='1_2',
    behaviour=3.0
)

# Plot the spectrum
draw_spectrum_ec8(spec, show=True)

# Export the spectrum to CSV
from eurocodepy.ec8.spectrum import write_spectrum_ec8
write_spectrum_ec8(spec, filename='spectrum_PT1_II_C_1_2.csv')
```

## Compliance

All calculations and checks are based on the requirements and recommendations of Eurocode 8 (EN 1998-1), including support for national annexes.

## Further Reading

- [Eurocode 8: Design of structures for earthquake resistance (EN 1998-1)](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-8-design-structures-earthquake-resistance)
