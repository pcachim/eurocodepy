# Eurocode 8 module: `ec8`

## Overview

The `ec8` module provides tools for seismic design according to EN 1998-1. It generates
elastic and design response spectra, retrieves national annex parameters for both the
standard Eurocode and the Portuguese National Annex, and exports spectra to CSV.

---

## Response spectra — `ec8.spectrum`

Accelerations are in m/s² (`a_g`, and the ordinates of the spectra); periods in s.

### `get_spec_params`

Returns the spectrum parameters `(S, a_g, T_B, T_C, T_D)` for a locale, code, importance class,
soil type and seismic zone. `a_g = a_gR·γI`; `S` is interpolated between `S_max` and `S_min`
with `a_g`.

```python
from eurocodepy.ec8 import get_spec_params

s_val, a_g, t_b, t_c, t_d = get_spec_params(
    locale="PT",        # "EU" (CEN) or "PT" (Portuguese National Annex)
    code="PT1",         # see the table below
    class_imp="II",     # importance class: I, II, III, IV
    soil="C",           # soil type: A, B, C, D, E
    zone="1_2",         # seismic zone (code-dependent)
)
```

#### Available codes

| `locale` | `code` | Description |
|----------|--------|-------------|
| `EU` | `CEN_1` | Standard Eurocode type 1 spectrum |
| `EU` | `CEN_2` | Standard Eurocode type 2 spectrum |
| `PT` | `PT1` | Portuguese NA — type 1 (continental Portugal) |
| `PT` | `PT2` | Portuguese NA — type 2 |
| `PT` | `PTA` | Portuguese NA — Azores |

#### Seismic zones

- `PT1`: `1_1`, `1_2`, `1_3`, `1_4`, `1_5`, `1_6`
- `PT2` / `PTA`: `2_1`, `2_2`, `2_3`, `2_4`, `2_5`
- `CEN_1` / `CEN_2`: `.1g`, `.2g`, … `.9g`, `1_0g` (the reference acceleration as a fraction of g)

---

### `get_spectrum_ec8`

Builds the horizontal design spectrum as a `pandas.DataFrame` with columns `period` and `value`.

```python
from eurocodepy.ec8 import get_spectrum_ec8

spec = get_spectrum_ec8(
    locale="PT",
    code="PT1",
    imp_class="II",
    soil="C",
    zone="1_2",
    behaviour=3.0,   # behaviour factor q
)
spec.columns.tolist()       # ['period', 'value']
spec["value"].max()         # largest design ordinate [m/s²]
```

---

### `get_spectrum_user` and `get_elastic_spectrum_user`

Spectra from arbitrary parameters, without a National Annex entry.

```python
from eurocodepy.ec8 import get_spectrum_user, get_elastic_spectrum_user

# a_g [m/s²], S, q, T_B, T_C, T_D
design = get_spectrum_user(a_g=2.0, s_val=1.15, q=4.0, t_b=0.1, t_c=0.6, t_d=2.0)
elastic = get_elastic_spectrum_user(a_g=2.0, s_val=1.15, t_b=0.1, t_c=0.6, t_d=2.0, damping=5.0)
```

---

### `calc_spectrum`, `calc_elastic_spectrum`, `damping_correction`

Ordinates of one period, from already-extracted parameters (EN 1998-1, Eqs. 3.2 to 3.5 and 3.13 to 3.16).

```python
from eurocodepy.ec8 import calc_spectrum, calc_elastic_spectrum, damping_correction

sd = calc_spectrum(0.3, a_g=2.0, s_val=1.15, q=3.0, t_b=0.1, t_c=0.6, t_d=2.0)   # design
se = calc_elastic_spectrum(0.3, 2.0, 1.15, 0.1, 0.6, 2.0)                       # elastic, 5 % damping
eta = damping_correction(5.0)                                                    # 1.0
```

`get_spectrum_parameters(code, coef_imp, soil, zone)` is the same lookup as `get_spec_params` with the
tables inside the function (codes `CEN-1`, `CEN-2`, `PT-1`, `PT-2`, `PT-A`, hyphenated); prefer `get_spec_params`.

---

### `draw_spectrum_ec8`

Plots the spectrum with matplotlib.

```python
from eurocodepy.ec8 import draw_spectrum_ec8

draw_spectrum_ec8(spec, show=False, save=True, filename="spectrum.png")
```

---

### `write_spectrum_ec8`

Exports the spectrum to a text file (two columns, `period` and `value`).

```python
from eurocodepy.ec8 import write_spectrum_ec8

write_spectrum_ec8(spec, filename="spectrum_PT1_II_C_1_2.csv", separator=",")
```

---

## Compliance

Calculations follow EN 1998-1:2004 and the Portuguese National Annex (NP EN 1998-1).

## Further reading

- [EN 1998-1 — Design for earthquake resistance](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-8-design-structures-earthquake-resistance)

