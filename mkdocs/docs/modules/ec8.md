# Eurocode 8 module: `ec8`

## Overview

The `ec8` module provides tools for seismic design according to EN 1998-1. It generates
elastic and design response spectra, retrieves national annex parameters for both the
standard Eurocode and the Portuguese National Annex, and exports spectra to CSV.

---

## Response spectra — `ec8.spectrum`

### `get_spec_params`

Returns the raw spectrum shape parameters for a given locale, code, importance class,
soil type, and seismic zone.

```python
from eurocodepy.ec8 import get_spec_params

S, ag, TB, TC, TD = get_spec_params(
    locale='PT',        # 'EU' (standard CEN) or 'PT' (Portuguese NA)
    code='PT-1',        # see table below
    class_imp='II',     # importance class: 'i', 'ii', 'iii', 'iv'
    soil='C',           # soil type: A, B, C, D, E
    zone='1_2',         # seismic zone (code-dependent)
)
```

#### Available codes

| `locale` | `code` | Description |
|----------|--------|-------------|
| `EU` | `CEN-1` | Standard Eurocode type 1 spectrum |
| `EU` | `CEN-2` | Standard Eurocode type 2 spectrum |
| `PT` | `PT-1` | Portuguese NA — continental Portugal (type 1) |
| `PT` | `PT-2` | Portuguese NA — continental Portugal + Madeira (type 2) |
| `PT` | `PT-A` | Portuguese NA — Azores |

#### Seismic zones

- `PT-1`: `1_1`, `1_2`, `1_3`, `1_4`, `1_5`, `1_6`
- `PT-2` / `PT-A`: `2_1`, `2_2`, `2_3`, `2_4`, `2_5`
- `CEN-1` / `CEN-2`: `.1g`, `.2g`, `.3g`, `.4g`, `.5g`, `.6g`, `.7g`, `.8g`, `.9g`, `1_0g`

---

### `get_spectrum_ec8`

Builds the full horizontal design spectrum as a dict of arrays.

```python
from eurocodepy.ec8 import get_spectrum_ec8   # also: ec8.spectrum.get_spectrum_ec8

spec = get_spectrum_ec8(
    locale='PT',
    code='PT-1',
    imp_class='II',
    soil='C',
    zone='1_2',
    behaviour=3.0,   # behaviour factor q (1.0 for elastic spectrum)
)

# Keys in the returned dict:
# 'T'   — period array [s]
# 'Sd'  — design spectral acceleration [g]
# 'Se'  — elastic spectral acceleration [g]
# 'ag'  — reference peak ground acceleration [g]
# 'S'   — soil factor
# 'TB', 'TC', 'TD' — corner periods [s]
```

---

### `get_spectrum_user`

Generate a spectrum from arbitrary user-supplied parameters without needing a
national annex entry.

```python
from eurocodepy.ec8.spectrum import get_spectrum_user

spec = get_spectrum_user(ag=0.2, S=1.15, TB=0.1, TC=0.6, TD=2.0, behaviour=4.0)
```

---

### `get_spectrum_parameters`

Low-level function; returns the parameter dict for a given combination.

---

### `calc_spectrum`

Computes the spectral ordinates from already-extracted parameters.

---

### `draw_spectrum_ec8`

Plots the spectrum using matplotlib.

```python
from eurocodepy.ec8 import draw_spectrum_ec8

draw_spectrum_ec8(spec, show=True, title='Design spectrum — Lisbon')
```

---

### `write_spectrum_ec8`

Exports the spectrum to a CSV file (two columns: `T [s]`, `Sd [g]`).

```python
from eurocodepy.ec8 import write_spectrum_ec8

write_spectrum_ec8(spec, filename='spectrum_PT1_II_C_1_2.csv')
```

---

## Compliance

Calculations follow EN 1998-1:2004 and the Portuguese National Annex (NP EN 1998-1).

## Further reading

- [EN 1998-1 — Design for earthquake resistance](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-8-design-structures-earthquake-resistance)

