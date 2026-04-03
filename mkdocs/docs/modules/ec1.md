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

```python
Load(name: str, load_type: LoadType, gk: float = 0.0, qk: float = 0.0)
```

### `LoadCombinations`

```python
from eurocodepy.ec1 import Load, LoadType, LoadCombinations, CombinationType

loads = [
    Load('G', LoadType.PERMANENT, gk=10.0),
    Load('Q', LoadType.LIVE,      qk=5.0),
    Load('W', LoadType.WIND,      qk=3.0),
]
combos = LoadCombinations(loads)
for c in combos.get(CombinationType.ULS):
    print(c)
```

---

## Force representations

| Class | Description |
|-------|-------------|
| `BaseForce` | Abstract base class |
| `PlaneForce` | In-plane forces (Nx, Ny, Nxy) |
| `ShellForce` | Shell resultants (Mx, My, Mxy, Vx, Vy, Nx, Ny, Nxy) |
| `SlabForce` | Slab resultants (Mx, My, Mxy, Vx, Vy) |
| `FrameForce` | 1-D frame member forces (N, Vy, Vz, Mx, My, Mz) |

---

## Sub-modules

### `ec1.wind`

Functions for wind load calculation following EN 1991-1-4. Exposed via
`from eurocodepy.ec1 import wind` or `from eurocodepy import wind`.

### `ec1.snow`

Functions for snow load calculation following EN 1991-1-3.

---

## Compliance

All combination logic follows EN 1990:2002 and its amendments.

## Further reading

- [EN 1991 — Actions on structures](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-1-actions-structures)
- [EN 1990 — Basis of structural design](https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-basis-structural-design)

