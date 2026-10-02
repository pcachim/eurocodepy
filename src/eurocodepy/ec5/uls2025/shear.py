# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Shear + torsion checks — **EN 1995-1-1:2025** (§8).

Uses the second-generation §8 forms: the biaxial shear interaction (Eqs.
8.28/8.29) and the torsion + shear interaction (Eq. 8.34), with ``k_shape``
from Eq. 8.35. The EN 1995-1-1:2004 (§6.1.7/6.1.8) versions live in
:mod:`eurocodepy.ec5.uls.shear`; the function names match so the two editions
are drop-in swappable.
"""
import numpy as np

from eurocodepy.ec5.materials import (
    LoadDuration,
    ServiceClass,
    Timber,
    TimberForcesType,
    TimberType,
)
from eurocodepy.utils import CrossSection, CrossSectionShape

K_VAR = 1.0
F_V_REF_K_TIMBER = 2.30  # MPa
F_V_REF_K_GLULAM = 2.75  # MPa


def check_shear_with_torsion(v_ed_y: float, v_ed_z: float, t_ed: float,  # noqa: PLR0913, PLR0914, PLR0917
                    section: CrossSection, timber: Timber,
                    service_class: ServiceClass, load_duration: LoadDuration) -> dict:
    """Check shear and torsion according to Eurocode 5.

    This function checks if the design shear and torsion stresses are within
    the design strengths.
    Uses equation 6.1 from Eurocode 5.

    Args:
        v_ed_y (float): Design shear force about the y-axis in N.
        v_ed_z (float): Design shear force about the z-axis in N.
        t_ed (float): Design torsion moment in Nm.
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.
        service_class (ServiceClass): Service class category.
        load_duration (LoadDuration): Load duration category.

    Returns:
        bool: True if the shear and torsion check is satisfied, False otherwise.

    """
    # calculate design strengths
    timber.design_values(service_class=service_class, load_duration=load_duration)
    fvd: float = timber.fvd

    # calculate stresses
    # Unsigned magnitudes, same reasoning as check_bending_with_normal(): the
    # torsion check (check2 = tau_tor/fvdt) and, for CLT (a=1), the shear
    # terms in check3 are never squared, so a negative v_ed/t_ed would
    # otherwise *reduce* the reported utilisation instead of adding to it.
    tau_v_y: float = 1.5 * abs(v_ed_y) / section.area / 1e3  # convert to MPa
    tau_v_z: float = 1.5 * abs(v_ed_z) / section.area / 1e3  # convert to MPa
    # τ_tor from the torsional section modulus (§8.1.12(1)); h = larger and
    # b = smaller side for the rectangular k_shape (Eq. 8.35).
    ratio: float = 1.0
    if section.shape is not CrossSectionShape.CIRCULAR:
        small, large = sorted((section.width, section.height))
        ratio = large / small
    tau_tor: float = abs(t_ed) / section.torsion_modulus / 1e3  # convert to MPa

    # calculate strengths

    if (timber.material is TimberType.CLT or
        timber.material is TimberType.LVL or
        timber.material is TimberType.GLVL):
        k_vy = 1.0
        k_vz = 1.0
    elif timber.material is TimberType.TIMBER:
        k_hvy = timber.k_h(section.height, TimberForcesType.Shear)
        k_hvz = timber.k_h(section.width, TimberForcesType.Shear)
        k_vy = min(k_hvy * K_VAR * F_V_REF_K_TIMBER / timber.fvk, 1.0)
        k_vz = min(k_hvz * K_VAR * F_V_REF_K_TIMBER / timber.fvk, 1.0)
    elif timber.material is TimberType.GLULAM:
        k_hvy = timber.k_h(section.height, TimberForcesType.Shear)
        k_hvz = timber.k_h(section.width, TimberForcesType.Shear)
        k_vy = min(k_hvy * K_VAR * F_V_REF_K_GLULAM / timber.fvk, 1.0)
        k_vz = min(k_hvz * K_VAR * F_V_REF_K_GLULAM / timber.fvk, 1.0)
    else:
        k_vy = 1.0
        k_vz = 1.0

    fvdy: float = k_vy * fvd
    fvdz: float = k_vz * fvd

    if section.shape is CrossSectionShape.CIRCULAR:  # equation (8.35)
        k_shape = 1.2
    elif (section.shape is CrossSectionShape.RECTANGULAR and
            timber.material is TimberType.CLT):
        k_shape = 1.0
    else:
        k_shape = min(1.0 + 0.05 * ratio, 1.3)
    fvdt: float = k_shape * fvd

    # check for shear and torsion
    a: float = 1.0 if timber.material is TimberType.CLT else 2.0
    check1: float = (  # equation (8.29) EN1995-1-1:2025
                        (tau_v_y / fvdy)**2 + (tau_v_z / fvdz)**2
                    )
    check2: float = (  # equation (8.34) EN1995-1-1:2025
                        tau_tor / fvdt
                    )
    check3: float = (  # equation (8.34) EN1995-1-1:2025
                        check2 + (tau_v_y / fvdy)**a + (tau_v_z / fvdz)**a
                    )
    check4: float = (  # equation (8.28) EN1995-1-1:2025
                        np.sqrt(check1)
                    )

    check: bool = check1 <= 1.0 and check2 <= 1.0 and check3 <= 1.0 and check4 <= 1.0
    # Split the governing utilisation into a "shear" part (the combined-shear
    # unity check, Eq. 8.28/8.29) and a "torsion" part (Eq. 8.34a/b).
    util_shear: float = max(float(check1), float(check4))
    util_torsion: float = max(float(check2), float(check3))

    s = (
        f"Bending check results:\n"
        f"  Cross-section: {section}\n"
        f"    width = {section.width} m\n"
        f"    height = {section.height} m\n"
        f"    A = {section.area:.4f} m²\n"
        f"    W_t = {section.torsion_modulus:.6f} m³\n"
        f"  Design forces:\n"
        f"    T_ed = {t_ed:.2f} kNm\n"
        f"    V_ed_y = {v_ed_y:.2f} kN\n"
        f"    V_ed_z = {v_ed_z:.2f} kN\n"
        f"  Design strengths:\n"
        f"    kmod = {timber.kmod:.2f}\n"
        f"    gamma_M = {timber.safety:.2f}\n"
        f"    k_vy = {k_vy:.2f}\n"
        f"    k_vy = {k_vz:.2f}\n"
        f"    fvd = {fvd:.2f} MPa\n"
        f"    fvdy = {fvdy:.2f} MPa\n"
        f"    fvdz = {fvdz:.2f} MPa\n"
        f"    fvdt = {fvdt:.2f} MPa\n"
        f"  Shear and torsion checks (n_ed < 0):\n"
        f"    Check shear (Eq. 8.28): {check4:.3f} <= 1.0 -> "
        f"{'OK' if check4 <= 1.0 else 'NOT OK'}\n"
        f"    Check shear (Eq. 8.29): {check1:.3f} <= 1.0 -> "
        f"{'OK' if check1 <= 1.0 else 'NOT OK'}\n"
        f"    Check torsion (Eq. 8.34a): {check2:.3f} <= 1.0 -> "
        f"{'OK' if check2 <= 1.0 else 'NOT OK'}\n"
        f"    Check shear + torsion (Eq. 8.34b): {check3:.3f} <= 1.0 -> "
        f"{'OK' if check3 <= 1.0 else 'NOT OK'}\n"
    )

    return {
        "report": s,
        "is_ok": check,
        "utilization": max(util_shear, util_torsion),
        "util_shear": util_shear,
        "util_torsion": util_torsion,
        "checks": {"check1": float(check1), "check2": float(check2),
                   "check3": float(check3), "check4": float(check4)},
    }
