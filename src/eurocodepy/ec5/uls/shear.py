# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
import numpy as np

from eurocodepy.ec5 import (
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
                    service_class: ServiceClass, load_duration: LoadDuration) -> bool:
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
    tau_v_y: float = 1.5 * v_ed_y / section.area / 1e3  # convert to MPa
    tau_v_z: float = 1.5 * v_ed_z / section.area / 1e3  # convert to MPa
    ratio: float = section.height / section.width
    alpha: float = (1.0 / 3.0) * (1.0 - 0.672 * ratio + 0.3 * ratio**2)
    tau_tor: float = alpha * t_ed / section.area / 1e3  # convert to MPa

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
        k_vy = min(k_hvz * K_VAR * F_V_REF_K_TIMBER / timber.fvk, 1.0)
    elif timber.material is TimberType.GLULAM:
        k_hvy = timber.k_h(section.height, TimberForcesType.Shear)
        k_hvz = timber.k_h(section.width, TimberForcesType.Shear)
        k_vy = min(k_hvy * K_VAR * F_V_REF_K_GLULAM / timber.fvk, 1.0)
        k_vy = min(k_hvz * K_VAR * F_V_REF_K_GLULAM / timber.fvk, 1.0)
    else:
        k_vy = 1.0
        k_vz = 1.0

    fvdy: float = k_vy * fvd
    fvdz: float = k_vz * fvd

    if section.shape is CrossSectionShape.CIRCULAR:  # equation (8.35)
        k_shape = 1.2
    elif (section.shape is CrossSectionShape.RECTANGULAR and
            timber.material is TimberType.CLT):
        k_shape: 1.0
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

    s = (
        f"Bending check results:\n"
        f"  Cross-section: {section}\n"
        f"    width = {section.width} m\n"
        f"    height = {section.height} m\n"
        f"    A = {section.area:.4f} m²\n"
        f"    alpha = {alpha:.4f} m²\n"
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
    }
