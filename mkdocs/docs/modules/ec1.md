# Eurocode 1 module: `ec1`

## Overview

The `ec1` module provides tools for EN 1991 (Actions on Structures). It covers
load type definitions, force representations, wind and snow sub-modules, and the
full EN 1990 load combination engine.

---

## Load combinations

### `LoadType` (enum)

Classifies an individual load for combination purposes.

| Member | Value | Description |
|--------|-------|-------------|
| `PERMANENT` | 0 | Self-weight, superimposed dead load |
| `LIVE` | 1 | Imposed loads (occupancy) |
| `WIND` | 2 | Wind action |
| `SNOW` | 3 | Snow load |
| `EARTHQUAKE` | 4 | Seismic action |
| `TEMPERATURE` | 5 | Thermal action |
| `FIRE` | 6 | Fire action |
| `ACCIDENTAL` | 7 | Other accidental actions |
| `OTHER` | 8 | — |

### `CombinationType` (enum)

| Member | Description |
|--------|-------------|
| `ULS` | Ultimate Limit State (EN 1990 Eq. 6.10) |
| `ALS` | Accidental Limit State |
| `FLS` | Fatigue Limit State |
| `SLS_K` | SLS characteristic combination |
| `SLS_FR` | SLS frequent combination |
| `SLS_QP` | SLS quasi-permanent combination |

### `Load` (dataclass)

```text
Load(name, load_type, gamma_fav, gamma_unf, psi0, psi1, psi2, incombo=True)
```

A load carries its partial factors (favourable and unfavourable effect, EN 1990 Table A1.2) and its
combination coefficients; it does not carry a value. `incombo=False` leaves it out of the combinations.

### `Loads` and the combinations

```python
from eurocodepy.ec1 import Load, LoadType, Loads

loads = Loads()
#                  name  type                 γ fav  γ unf  ψ0   ψ1   ψ2
loads.add(Load("G", LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
loads.add(Load("Q", LoadType.LIVE,      0.0, 1.50, 0.7, 0.5, 0.3))
loads.add(Load("W", LoadType.WIND,      0.0, 1.50, 0.6, 0.2, 0.0))

values = {"G": 20.0, "Q": 8.0, "W": 4.0}                 # characteristic values [kN/m²]

# ULS (EN 1990 Eq. 6.10): a dict {name: LoadCombination}; factors = {load name: (Load, factor)}
for name, combo in loads.get_ULS_combos().items():
    total = sum(factor * values[k] for k, (_, factor) in combo.factors.items())
    print(f"{name:34s} {total:7.2f}")

# SLS characteristic, frequent and quasi-permanent
for name, combo in loads.get_SLS_combos().items():
    print(name)
```

`get_ULS_combos()` and `get_SLS_combos()` return a dictionary `{name: LoadCombination}`. A
`LoadCombination` has `name`, `type` (a `CombinationType`) and `factors`, a dictionary
`{load name: (Load, factor)}`. `LoadCombinations` is a container of `LoadCombination` objects
(`add`, `remove`, iteration).

---

## Force representations

| Class | Description |
|-------|-------------|
| `BaseForce` | Abstract base class |
| `PlaneForce` | In-plane forces (Nx, Ny, Nxy) |
| `ShellForce` | Shell resultants (`n_xx`, `n_yy`, `n_xy`, `m_xx`, `m_yy`, `m_xy`, `v_xz`, `v_yz`) |
| `SlabForce` | Slab resultants (`m_xx`, `m_yy`, `m_xy`, `v_xz`, `v_yz`) |
| `FrameForce` | 1-D frame member forces (`n_x`, `v_y`, `v_z`, `m_y`, `m_z`, `t_x`) |

```python
from eurocodepy.ec1 import ShellForce
f = ShellForce(n_xx=100.0, m_xx=20.0)     # kN, m by default: the unit system `u`
f.forces.shape, f.n_cases                 # (8, 1), 1
```

---

## Sub-modules

### `ec1.wind`

Functions of EN 1991-1-4 (4.2 to 4.5): `v_b`, `c_r`, `c_o`, `s_coef`, `v_m`, `I_v`, `v_p`, `q_p`.
Heights and roughness lengths in m, velocities in m/s, pressures in N/m².

```python
from eurocodepy.ec1 import wind

vb = wind.v_b(27.0)                                  # vb,0 = 27 m/s, cseason = cdir = 1
cr = wind.c_r(z=10, z_min=2, z_0=0.05, z_0II=0.05)   # terrain category II
co = wind.c_o(z=10)                                  # flat terrain
vm = wind.v_m(10, vb, cr, co)                        # mean wind velocity
qp = wind.q_p(10, vb, 2, 0.05, cr, co)               # peak velocity pressure [N/m²]
```

### `ec1.snow`

Placeholder: the snow loads of EN 1991-1-3 are not implemented yet.

---

## Compliance

All combination logic follows EN 1990:2002 and its amendments.

## Further reading

- [EN 1991 — Actions on structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-1-actions-structures)
- [EN 1990 — Basis of structural design](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-basis-structural-design)

