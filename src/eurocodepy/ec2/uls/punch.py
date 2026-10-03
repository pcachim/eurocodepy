# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See the project's LICENSE file for details.

"""Punching shear — **EN 1992-1-1:2004** (§6.4).

The basic control perimeter ``u1`` is taken at **2·d** from the loaded area, the
load-eccentricity factor ``β`` follows §6.4.3 (the biaxial expression 6.43 for
internal columns, the recommended values 1.4 / 1.5 for edge / corner) and the
concrete resistance is ``vRd,c = CRd,c·k·(100·ρl·fck)^(1/3) ≥ vmin`` with
``CRd,c = 0.18/γc`` (§6.4.4).

The function names match the EN 1992-1-1:2023 module
(:mod:`eurocodepy.ec2.uls2023.punch`) so the two editions are drop-in
swappable, but the signatures differ (2004 uses ``γc``; there is no ``d_dg`` /
``γv`` / ``η_sys``).
"""

import numpy as np


def calc_perimeters(
    dv: float,
    bxord: float,
    by: float | object = None,
    position: str = "center",
    dx: float = 0.0,
    dy: float = 0.0,
) -> tuple[float, float, float]:
    """Return (u0, u1, bb) — EN 1992-1-1:2004 §6.4.2.

    ``u0`` is the loaded-area perimeter (at the column face) and ``u1`` the basic
    control perimeter at **2·d** from it. ``bb`` is the size (column dimension +
    4·d) used by the eccentricity factor β. Edge/corner cases use the reduced
    perimeter of §6.4.2(4).

    Args:
        dv: Effective depth d [mm].
        bxord: Column / loaded-area dimension in x (or the diameter) [mm].
        by: Column dimension in y [mm]; None → circular/square from ``bxord``.
        position: 'center' | 'edgex' | 'edgey' | 'corner'.
        dx: Distance to the x border [mm] (edge/corner).
        dy: Distance to the y border [mm] (edge/corner).

    Returns:
        (u0, u1, bb) in mm.

    """
    two_d = 2.0 * dv
    if by is None:
        # Circular column, diameter d0.
        d0 = bxord
        if position == "edgex":
            u0 = np.pi * d0 / 2.0 + d0 + dx
            u1 = np.pi * (d0 / 2.0 + two_d) + d0 + dx
        elif position == "edgey":
            u0 = np.pi * d0 / 2.0 + d0 + dy
            u1 = np.pi * (d0 / 2.0 + two_d) + d0 + dy
        elif position == "corner":
            u0 = np.pi * d0 / 4.0 + d0 + (dx + dy) / 2.0
            u1 = np.pi * (d0 / 2.0 + two_d) / 2.0 + d0 + (dx + dy) / 2.0
        else:
            u0 = np.pi * d0
            u1 = np.pi * (d0 + two_d)
        bb = d0 + 2.0 * two_d
        return u0, u1, bb

    # Rectangular column cx × cy.
    cx, cy = bxord, by
    if position == "edgex":
        u0 = 2.0 * cx + cy
        u1 = u0 + np.pi * two_d + 2.0 * dx
    elif position == "edgey":
        u0 = cx + 2.0 * cy
        u1 = u0 + np.pi * two_d + 2.0 * dy
    elif position == "corner":
        u0 = cx + cy
        u1 = u0 + np.pi * two_d / 2.0 + (dx + dy)
    else:
        u0 = 2.0 * (cx + cy)
        u1 = u0 + 2.0 * np.pi * two_d
    bb = np.sqrt((cx + 2.0 * two_d) * (cy + 2.0 * two_d))
    return u0, u1, bb


def calc_vedp(  # ruff: ignore[too-many-arguments, too-many-positional-arguments]
    ned: float | np.ndarray,
    medx: float | np.ndarray,
    medy: float | np.ndarray,
    dv: float,
    bxord: float,
    by: float | object = None,
    position: str = "center",
    dx: float = 0.0,
    dy: float = 0.0,
) -> float | np.ndarray:
    """Design punching shear stress ``vEd = β·VEd/(u1·d)`` [MPa] — §6.4.3.

    β follows the code: for an internal column the biaxial expression (6.43)
    ``β = 1 + 1.8·√((ey/bz)² + (ez/by)²)`` ( e = M/V, bz/by = column + 4·d), and
    the recommended constants 1.4 (edge) / 1.5 (corner) otherwise.

    Args:
        ned: Design axial (punching) force VEd [kN].
        medx: Design moment about x [kNm].
        medy: Design moment about y [kNm].
        dv: Effective depth d [mm].
        bxord, by, position, dx, dy: see :func:`calc_perimeters`.

    Returns:
        Design punching shear stress [MPa].

    """
    position = position.lower()
    if position in {"internal", "centre"}:
        position = "center"
    u0, u1, _bb = calc_perimeters(dv, bxord, by, position=position, dx=dx, dy=dy)

    if position == "center":
        cx = bxord
        cy = bxord if by is None else by
        bz = cx + 4.0 * dv
        byy = cy + 4.0 * dv
        with np.errstate(divide="ignore", invalid="ignore"):
            ex = np.where(ned != 0.0, medx / ned * 1e3, 0.0)   # [mm]
            ey = np.where(ned != 0.0, medy / ned * 1e3, 0.0)
        beta = 1.0 + 1.8 * np.sqrt((ey / bz) ** 2 + (ex / byy) ** 2)
    elif position in {"edgex", "edgey", "edge"}:
        beta = 1.4
    elif position == "corner":
        beta = 1.5
    else:
        msg = 'Position must be "center", "edge" or "corner".'
        raise ValueError(msg)

    ved = ned / u1 / dv          # [kN/mm²]
    return beta * ved * 1e3      # [N/mm²] = [MPa]


def calc_vrdcp(rhol: float, fck: float,
               dv: float,
               gamma_c: float = 1.5,
               ) -> float | np.ndarray:
    """Concrete punching resistance ``vRd,c`` [MPa] — EN 1992-1-1:2004 §6.4.4.

    ``vRd,c = CRd,c·k·(100·ρl·fck)^(1/3) ≥ vmin`` with ``CRd,c = 0.18/γc``,
    ``k = 1 + √(200/d) ≤ 2`` and ``vmin = 0.035·k^1.5·√fck``.

    Args:
        rhol: Longitudinal reinforcement ratio ρl (≤ 0.02).
        fck: Characteristic concrete strength [MPa].
        dv: Effective depth d [mm].
        gamma_c: Partial factor for concrete (default 1.5).

    Returns:
        vRd,c [MPa].

    """
    k = min(1.0 + np.sqrt(200.0 / dv), 2.0)
    rho = min(rhol, 0.02)
    crdc = 0.18 / gamma_c
    vrdc = crdc * k * (100.0 * rho * fck) ** (1.0 / 3.0)
    vmin = calc_vrdcminp(fck, dv)
    return max(float(vrdc), float(vmin))


def calc_vrdcminp(fck: float,
                  dv: float,
                  ) -> float | np.ndarray:
    """Minimum concrete punching resistance ``vmin = 0.035·k^1.5·√fck`` [MPa]
    (EN 1992-1-1:2004 §6.4.4 / Eq. 6.3N).

    Args:
        fck: Characteristic concrete strength [MPa].
        dv: Effective depth d [mm].

    Returns:
        vmin [MPa].

    """
    k = min(1.0 + np.sqrt(200.0 / dv), 2.0)
    return 0.035 * k ** 1.5 * np.sqrt(fck)
