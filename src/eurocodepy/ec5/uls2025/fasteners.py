# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Axial resistance of dowel-type fasteners -- **EN 1995-1-1:2025** §11.2.2.

Only what the reinforcement of timber beams needs (§8.3.2(8): fully threaded
screws, rods with wood screw thread and bonded-in rods, resistance from §11.2.2
with the reinforced length ``l_r`` as withdrawal length):

* withdrawal strength ``f_w,k`` of screws and rods with wood screw thread
  (Table 11.2 B.1, Eqs. 4-7) and of bonded-in rods (C, Eq. 9);
* ``F_w,k = π·d·l_w·f_w,k`` (Eq. 11.3) and ``F_t,k = 0.9·A_s·f_u,k``
  (Eq. 11.4);
* ``F_ax,t,d = min{k_mod/γ_R·F_w,k ; F_t,k/γ_M2}`` (Eq. 11.1, without the head
  pull-through: an embedded reinforcement has no head to pull through).

The partial factors ``γ_R`` and ``γ_M2`` are Table 4.4 of the standard, which is
not reproduced here: the caller supplies them. Units: mm, N/mm² (MPa), kg/m³;
forces in kN. Angles in degrees.
"""
from __future__ import annotations

import math

K_SCREW = 8.2                    # Table 11.2 B.1, unless a technical
#                                  specification gives another value
F_W_K_BONDED_IN_ROD = 4.0        # MPa, Table 11.2 C (Eq. 9), 30° ≤ ε ≤ 90°
D_MIN, D_MAX = 3.5, 22.0         # mm, Table 11.2 B
D1_OVER_D = (0.55, 0.76)
L_W_MIN_OVER_D = 5.0
RHO_K_MAX = 700.0                # kg/m³


def calc_k_w(eps: float) -> float:
    """Eq. 5: ``1.0`` for ``30° ≤ ε ≤ 90°``, else ``0.3 + 0.7·ε/30°``."""
    return 1.0 if eps >= 30.0 else 0.3 + 0.7 * eps / 30.0


def calc_k_mat(n_p: float | None, parallel_laminated: bool = True) -> float:
    """Eq. 6: ``1`` for products other than PL and CL; for PL and CL
    ``1 + ln(n_p)/12 ≤ 1.15`` (``n_p`` = number of penetrated laminations, taken
    as at least 1)."""
    if not parallel_laminated or not n_p:
        return 1.0
    return min(1.0 + math.log(max(n_p, 1.0)) / 12.0, 1.15)


def calc_k_rho(eps: float, softwood: bool = True) -> float:
    """Eq. 7: exponent of the density term (0.7 / 1.1 softwoods, 1.6 hardwoods)."""
    if not softwood:
        return 1.6
    return 0.7 if eps <= 5.0 else 1.1


def withdrawal_strength_screw(d: float, rho_k: float, eps: float = 90.0,
                              n_p: float | None = None,
                              k_screw: float = K_SCREW, softwood: bool = True,
                              parallel_laminated: bool = True) -> float:
    """``f_w,k`` of screws and rods with wood screw thread, in MPa
    (Table 11.2 B.1, Eq. 4): ``k_screw·k_w·k_mat·d^-0.33·(ρ_k/350)^k_ρ``."""
    return (k_screw * calc_k_w(eps) * calc_k_mat(n_p, parallel_laminated)
            * d ** -0.33 * (rho_k / 350.0) ** calc_k_rho(eps, softwood))


def screw_validity(d: float, d1: float, l_w: float, rho_k: float) -> list:
    """Limits of Table 11.2 B.1 that are not met, as short messages."""
    out = []
    if not D_MIN <= d <= D_MAX:
        out.append(f"d = {d:g} mm is outside {D_MIN:g}-{D_MAX:g} mm")
    if d > 0 and not D1_OVER_D[0] * d <= d1 <= D1_OVER_D[1] * d:
        out.append(f"d1/d = {d1 / d:.2f} is outside {D1_OVER_D[0]}-{D1_OVER_D[1]}")
    if d > 0 and l_w < L_W_MIN_OVER_D * d:
        out.append(f"l_w = {l_w:g} mm is below 5d")
    if rho_k > RHO_K_MAX:
        out.append(f"ρ_k = {rho_k:g} kg/m³ exceeds {RHO_K_MAX:g}")
    return out


def withdrawal_resistance(d: float, l_w: float, f_wk: float) -> float:
    """``F_w,k = π·d·l_w·f_w,k`` (Eq. 11.3), in kN (d, l_w in mm)."""
    return math.pi * d * l_w * f_wk / 1e3


def steel_tensile_resistance(a_s: float, f_uk: float) -> float:
    """``F_t,k = 0.9·A_s·f_u,k`` (Eq. 11.4), in kN (A_s in mm², f_u,k in MPa)."""
    return 0.9 * a_s * f_uk / 1e3


def axial_tensile_resistance(f_wk_force: float, f_tk_force: float,
                             k_mod: float, gamma_r: float,
                             gamma_m2: float) -> tuple[float, str]:
    """``F_ax,t,d = min{k_mod/γ_R·F_w,k ; F_t,k/γ_M2}`` (Eq. 11.1, no head
    pull-through), in kN, and which of the two governs (``"withdrawal"`` /
    ``"steel"``)."""
    timber = k_mod / gamma_r * f_wk_force
    steel = f_tk_force / gamma_m2
    return (timber, "withdrawal") if timber <= steel else (steel, "steel")
