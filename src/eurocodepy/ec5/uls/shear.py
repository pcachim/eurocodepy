# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Shear + torsion checks — **EN 1995-1-1:2004** (§6.1.7 / §6.1.8).

Baseline (first-generation) Eurocode 5:

* **shear** (§6.1.7, Eq. 6.13): ``τ_d = 1.5·V / A ≤ f_v,d`` for a rectangular
  section, checked in each direction — there is **no** biaxial shear interaction
  in the 2004 edition;
* **torsion** (§6.1.8, Eqs. 6.14/6.15): ``τ_tor,d ≤ k_shape·f_v,d`` with
  ``k_shape = 1.2`` (circular) or ``min(1 + 0.15·h/b ; 2.0)`` (rectangular).
  Shear and torsion are checked **separately** (no combined interaction — that
  is a :2025 addition).

The EN 1995-1-1:2025 (§8) versions live in
:mod:`eurocodepy.ec5.uls2025.shear`; the function names match so the two
editions are drop-in swappable.
"""
import numpy as np

from eurocodepy.ec5.materials import LoadDuration, ServiceClass, Timber
from eurocodepy.utils import CrossSection, CrossSectionShape


def check_shear_with_torsion(v_ed_y: float, v_ed_z: float, t_ed: float,  # noqa: PLR0913, PLR0914, PLR0917
                    section: CrossSection, timber: Timber,
                    service_class: ServiceClass, load_duration: LoadDuration) -> dict:
    """Shear + torsion check (EN 1995-1-1:2004 §6.1.7 / §6.1.8).

    Args:
        v_ed_y, v_ed_z (float): Design shear forces [kN].
        t_ed (float): Design torsion moment [kNm].
        section, timber: Cross-section / material objects.
        service_class, load_duration: EN 1995-1-1 design conditions.

    Returns:
        dict with ``report``, ``is_ok``, ``utilization``, ``util_shear``,
        ``util_torsion`` and the individual ``checks``.

    """
    timber.design_values(service_class=service_class, load_duration=load_duration)
    fvd = timber.fvd

    # Shear stresses [MPa]: τ = 1.5·V/A for a rectangular section (§6.1.7).
    tau_v_y = 1.5 * abs(v_ed_y) / section.area / 1e3
    tau_v_z = 1.5 * abs(v_ed_z) / section.area / 1e3

    # Torsional shear stress [MPa] (same section convention as the codebase).
    ratio = section.height / section.width
    alpha = (1.0 / 3.0) * (1.0 - 0.672 * ratio + 0.3 * ratio**2)
    tau_tor = alpha * abs(t_ed) / section.area / 1e3

    # k_shape (§6.1.8, Eq. 6.15).
    if section.shape is CrossSectionShape.CIRCULAR:
        k_shape = 1.2
    else:
        k_shape = min(1.0 + 0.15 * ratio, 2.0)
    fvdt = k_shape * fvd

    # Shear — each direction separately (no 2004 interaction), Eq. 6.13.
    check_vy = tau_v_y / fvd if fvd > 0 else 0.0
    check_vz = tau_v_z / fvd if fvd > 0 else 0.0
    # Torsion — Eq. 6.14.
    check_t = tau_tor / fvdt if fvdt > 0 else 0.0

    util_shear = max(float(check_vy), float(check_vz))
    util_torsion = float(check_t)
    check = util_shear <= 1.0 and util_torsion <= 1.0

    s = (
        f"EC5:2004 shear + torsion check\n"
        f"  A = {section.area:.4f} m²  k_shape = {k_shape:.2f}\n"
        f"  V_y = {v_ed_y:.2f} kN  V_z = {v_ed_z:.2f} kN  T = {t_ed:.2f} kNm\n"
        f"  τvy = {tau_v_y:.3f}  τvz = {tau_v_z:.3f}  τtor = {tau_tor:.3f} MPa\n"
        f"  fvd = {fvd:.2f}  fvdt = {fvdt:.2f} MPa\n"
        f"  shear util = {util_shear:.3f}  torsion util = {util_torsion:.3f} "
        f"({'OK' if check else 'NOT OK'})\n"
    )

    return {
        "report": s,
        "is_ok": check,
        "utilization": max(util_shear, util_torsion),
        "util_shear": util_shear,
        "util_torsion": util_torsion,
        "checks": {"check_vy": float(check_vy), "check_vz": float(check_vz),
                   "check_t": float(check_t)},
    }
