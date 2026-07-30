# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Bending + axial checks — **EN 1995-1-1:2025** (§8).

The combined bending-and-axial unity checks use the second-generation §8 forms
(Eqs. 8.24-8.27 / 8.39 / 8.44-8.45) with the reduction factor ``k_red`` and the
stability factors ``k_c`` (Eq. 8.40) and ``k_m`` (Eq. 8.46). The EN 1995-1-1:2004
(§6) versions live in :mod:`eurocodepy.ec5.uls.bending`; the function names match
so the two editions are drop-in swappable.
"""
import numpy as np

import eurocodepy as ec
from eurocodepy.ec5.materials import TimberForcesType
from eurocodepy.ec5.materials import LoadDuration, ServiceClass, Timber
from eurocodepy.utils import CrossSection

LAMBDA_REL_LIM = 0.3
LAMBDA_M_REL = 0.55
EPSILON_TIMBER: float = 1.0 / 400.0
EPSILON_GLULAM: float = 1.0 / 1000.0
THETA_TWIST_BASE: float = 1.0 / 1500.0


def get_safety_factor(timber_type: str) -> float:
    """Get the safety factor for a given timber type, load duration, and service class.

    Args:
        timber_type (str): Type of timber ('timber', 'glulam', 'lvl').

    Returns:
        float: Safety factor gamma_M

    """
    return ec.TimberParams["safety"][timber_type]


def calc_k_red(section: CrossSection) -> float:
    """Calculate the reduction factor k_red for bending according to Eurocode 5.

    According to 8.1.8.1.(2) from EN 1995-1-1:2025

    Args:
        section (CrossSection): Cross-section object.

    Returns:
        float: Reduction factor k_red

    """
    return 0.7 if section.shape == "rectangular" else 1.0


def calc_k_c(l_0y: float, l_0z: float, section: CrossSection,  # noqa: PLR0914
                timber: Timber) -> tuple[float, float]:
    """Calculate the k_c factor for compression instability according to Eurocode 5.

    k_c is calculated using equation 8.40 from EN 1995-1-1:2025.

    Args:
        l_0y (float): Effective length about the y-axis in mm.
        l_0z (float): Effective length about the z-axis in mm.
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.

    Returns:
        k_c_y (float): k_c factor about the y-axis.
        k_c_z (float): k_c factor about the z-axis.

    """
    E0k: float = timber.E0k  # noqa: N806
    fc0k: float = timber.fc0k
    k_hy = timber.k_h(section.height, TimberForcesType.Bending)
    fmky: float = timber.fmk * k_hy  # calc_k_h(section.height, timber.type)
    k_hz = timber.k_h(section.width, TimberForcesType.Bending)
    fmkz: float = timber.fmk * k_hz  # calc_k_h(section.width, timber.type)
    # Relative slenderness λ_rel = (l_ef / i) / π · √(f_c,0,k / E_0,05), with the
    # radius of gyration i (m) and the effective length converted from mm to m.
    # (N_cr = π²·E·I/l² with I = A·i², so λ_rel = √(f_c,0,k·A/N_cr) reduces to
    # this closed form — the earlier version used i as if it were I and mixed
    # mm/m units.)
    l0y_m: float = l_0y / 1e3
    l0z_m: float = l_0z / 1e3
    i_y: float = section.radius_y
    i_z: float = section.radius_z
    lambda_rely: float = (l0y_m / i_y / np.pi * np.sqrt(fc0k / E0k)
                          if (l0y_m > 0.0 and i_y > 0.0) else 0.0)
    lambda_relz: float = (l0z_m / i_z / np.pi * np.sqrt(fc0k / E0k)
                          if (l0z_m > 0.0 and i_z > 0.0) else 0.0)

    epsilon: float = EPSILON_TIMBER if (timber.type ==
                            "timber") else EPSILON_GLULAM
    beta_c: float = epsilon * np.pi * np.sqrt(3.0 *
                        E0k / fc0k) * fc0k  # Table 8.2
    beta_cy: float = beta_c / fmky  # Table 8.2
    beta_cz: float = beta_c / fmkz  # Table 8.2

    if lambda_rely <= LAMBDA_REL_LIM:
        k_c_y = 1.0
    else:
        phi: float = 0.5 * (1 + beta_cy * (lambda_rely -
                                LAMBDA_REL_LIM) + lambda_rely**2)
        k_c_y: float = 1.0 / (phi + np.sqrt(phi**2 - lambda_rely**2))

    if lambda_relz <= LAMBDA_REL_LIM:
        k_c_z = 1.0
    else:
        phi: float = 0.5 * (1 + beta_cz * (lambda_relz -
                                LAMBDA_REL_LIM) + lambda_relz**2)
        k_c_z: float = 1.0 / (phi + np.sqrt(phi**2 - lambda_relz**2))

    return (k_c_y, k_c_z)


def calc_mcr(l_0m: float, section: CrossSection, timber: Timber) -> float:
    """Calculate the critical bending moment m_cr according to Eurocode 5.

    ``M_y,crit = (π / l_ef)·√(E_0,05·I_z·G_0,05·I_tor)`` (the lateral-torsional
    buckling moment).

    Args:
        l_0m (float): Effective length for lateral-torsional buckling in mm.
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.

    Returns:
        m_cr (float): Critical bending moment (∞ when l_0m ≤ 0 → no LTB).

    """
    lef: float = l_0m / 1e3                      # mm → m
    if lef <= 0.0:
        return float("inf")
    E0k: float = timber.E0k  # noqa: N806
    G0k: float = timber.Gk  # noqa: N806
    Itor: float = section.torsional_inertia  # noqa: N806
    Iz: float = section.inertia_z  # noqa: N806
    m_cr: float = np.pi * np.sqrt(E0k * G0k * Itor * Iz) / lef

    return m_cr


def calc_k_m(l_0m: float, section: CrossSection, timber: Timber) -> float:
    """Calculate the k_m factor for bending instability according to Eurocode 5.

    k_m is calculated using equation 8.46 from EN 1995-1-1:2025.

    Args:
        l_0m (float): Effective length about the major axis in mm.
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.

    Returns:
        k_m (float): k_m factor.

    """
    E0k: float = timber.E0k  # noqa: N806
    G0k: float = timber.Gk  # noqa: N806
    m_cr_y: float = calc_mcr(l_0m, section, timber)
    lambda_relm: float = np.sqrt(timber.fmk *
                                section.bend_mod_y / m_cr_y)  # equation (8.43)
    ratio: float = section.height / section.width

    epsilon: float = EPSILON_TIMBER if (timber.type
                            == "timber") else EPSILON_GLULAM  # Table 8.2
    beta_m: float = epsilon * ratio * np.pi / 2.0 * np.sqrt(3.0 *
                                        E0k / G0k)  # Table 8.2
    beta_twist: float = THETA_TWIST_BASE / section.height * ratio  # Table 8.2

    if lambda_relm <= LAMBDA_REL_LIM:
        k_m = 1.0
    else:
        phi: float = 0.5 * (1 + beta_m * beta_twist * (lambda_relm - LAMBDA_M_REL)
                            + lambda_relm**2)  # equation (8.47)
        k_m: float = 1.0 / (phi + np.sqrt(phi**2 - lambda_relm**2))  # equation (8.46)

    return k_m


def check_bending_with_normal(n_ed: float, m_ed_y: float, m_ed_z: float,  # noqa: PLR0913, PLR0914, PLR0917
                    section: CrossSection, timber: Timber,
                    l_0y: float, l_0z: float, l_0m: float,
                    service_class: ServiceClass, load_duration: LoadDuration) -> dict:
    """Check bending according to Eurocode 5.

    This function checks if the design bending stresses in both principal directions
    are within the design bending strength of the timber member.
    Uses equation 6.1 from Eurocode 5.

    Args:
        n_ed (float): Design axial force in N.
        m_ed_y (float): Design bending moment about the y-axis in Nm.
        m_ed_z (float): Design bending moment about the z-axis in Nm.
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.
        l_0y (float): Effective length about the y-axis in mm.
        l_0z (float): Effective length about the z-axis in mm.
        l_0m (float): Effective length about the major axis in mm.
        service_class (ServiceClass): Service class category.
        load_duration (LoadDuration): Load duration category.

    Returns:
        bool: True if the bending check is satisfied, False otherwise.

    """
    # calculate design strengths
    timber.design_values(service_class=service_class, load_duration=load_duration)
    # kmod: float = calc_k_mod(timber.type,
    #                         load_duration,
    #                         service_class)
    kred: float = calc_k_red(section)
    fc0d: float = (timber.fc0d)
    ft0d: float = (timber.ft0d)
    k_hy = timber.k_h(section.height, TimberForcesType.Bending)
    fmdy: float = (timber.fmd) * k_hy  # calc_k_h(section.height, timber.type)
    k_hz = timber.k_h(section.width, TimberForcesType.Bending)
    fmdz: float = (timber.fmd) * k_hz  # calc_k_h(section.width, timber.type)

    # calculate stresses
    sig_n: float = n_ed / section.area / 1e3  # convert to MPa
    sig_my: float = m_ed_y / section.bend_mod_y / 1e3  # convert to MPa
    sig_mz: float = m_ed_z / section.bend_mod_z / 1e3  # convert to MPa

    # calculate k_c and k_m
    k_c: tuple[float, float] = calc_k_c(l_0y=l_0y, l_0z=l_0z,
                                        section=section, timber=timber)
    k_m: float = calc_k_m(l_0m=l_0m, section=section, timber=timber)

    # check for bending
    if n_ed < 0.0:  # compression
        p: float = 2.0 if section.shape == "rectangular" else 1.0
        check1: float = (  # equation (8.26) EN1995-1-1:2025
                            (sig_n / fc0d)**p +
                            (sig_my / fmdy) +
                            kred * (sig_mz / fmdz)
                        )
        check2: float = (  # equation (8.27) EN1995-1-1:2025
                            (sig_n / fc0d)**p +
                            kred * (sig_my / fmdy) +
                            (sig_mz / fmdz)
                        )
        check3: float = (  # equation (8.39) EN1995-1-1:2025
                            (sig_n / (k_c[0] * fc0d)) +
                            (sig_my / fmdy) +
                            kred * (sig_mz / fmdz)
                        )
        check4: float = (  # equation (8.44) EN1995-1-1:2025
                            (sig_n / (k_c[1] * fc0d)) +
                            (sig_my / (k_m * fmdy))**2 +
                            kred * (sig_mz / fmdz)
                        )
    else:  # tension
        check1: float = (  # equation (8.24) EN1995-1-1:2025
                            (sig_n / ft0d) +
                            (sig_my / fmdy) +
                            kred * (sig_mz / fmdz)
                        )
        check2: float = (  # equation (8.25) EN1995-1-1:2025
                            (sig_n / ft0d) +
                            kred * (sig_my / fmdy) +
                            (sig_mz / fmdz)
                        )
        check3: float = True  # Not applicable in tension
        check4: float = (  # equation (8.45) EN1995-1-1:2025
                            (sig_n / (k_c[1] * ft0d)) +
                            (sig_my / (k_m * fmdy)) +
                            kred * (sig_mz / fmdz)
                        )

    check: bool = check1 <= 1.0 and check2 <= 1.0 and check3 <= 1.0 and check4 <= 1.0
    # Governing utilisation (largest of the applicable unity checks). check3 in
    # tension is the sentinel True (not applicable) → coerce to 0.0.
    _c3 = 0.0 if check3 is True else float(check3)
    utilization: float = max(float(check1), float(check2), _c3, float(check4))

    s = (
        f"Bending check results:\n"
        f"  Cross-section: {section}\n"
        f"    width = {section.width} m\n"
        f"    height = {section.height} m\n"
        f"    A = {section.area:.4f} m²\n"
        f"    W_y = {section.bend_mod_y:.6f} m³\n"
        f"    W_z = {section.bend_mod_z:.6f} m³\n"
        f"  Design forces:\n"
        f"    N_ed = {n_ed:.2f} kN\n"
        f"    M_ed_y = {m_ed_y:.2f} kNm\n"
        f"    M_ed_z = {m_ed_z:.2f} kNm\n"
        f"  Design strengths:\n"
        f"    kmod = {timber.kmod:.2f}\n"
        f"    gamma_M = {timber.safety:.2f}\n"
        f"    fc0d = {fc0d:.2f} MPa\n"
        f"    ft0d = {ft0d:.2f} MPa\n"
        f"    kred = {kred:.2f}\n"
        f".   khy = {k_hy:.2f}\n"
        f".   khz = {k_hz:.2f}\n"
        f"    fmdy = {fmdy:.2f} MPa\n"
        f"    fmdz = {fmdz:.2f} MPa\n"
        f"  Stresses:\n"
        f"    sigma_n = {sig_n:.2f} MPa\n"
        f"    sigma_my = {sig_my:.2f} MPa\n"
        f"    sigma_mz = {sig_mz:.2f} MPa\n"
        f"  Stability factors:\n"
        f"    k_cy = {k_c[0]:.2f}\n"
        f"    k_cz = {k_c[1]:.2f}\n"
        f"    k_m = {k_m:.2f}\n"
    )
    if n_ed < 0.0:  # compression
        s += (
            f"  Bending with compression checks (n_ed < 0):\n"
            f"    Check 1 (Eq. 8.26): {check1:.3f} <= 1.0 -> "
            f"{'OK' if check1 <= 1.0 else 'NOT OK'}\n"
            f"    Check 2 (Eq. 8.27): {check2:.3f} <= 1.0 -> "
            f"{'OK' if check2 <= 1.0 else 'NOT OK'}\n"
            f"    Check 3 (Eq. 8.39): {check3:.3f} <= 1.0 -> "
            f"{'OK' if check3 <= 1.0 else 'NOT OK'}\n"
            f"    Check 4 (Eq. 8.44): {check4:.3f} <= 1.0 -> "
            f"{'OK' if check4 <= 1.0 else 'NOT OK'}\n"
        )
    else:  # tension
        s += (
            f"  Bending with tension checks (n_ed >= 0):\n"
            f"    Check 1 (Eq. 8.24): {check1:.3f} <= 1.0 -> "
            f"{'OK' if check1 <= 1.0 else 'NOT OK'}\n"
            f"    Check 2 (Eq. 8.25): {check2:.3f} <= 1.0 -> "
            f"{'OK' if check2 <= 1.0 else 'NOT OK'}\n"
            f"    Check 4 (Eq. 8.45): {check4:.3f} <= 1.0 -> "
            f"{'OK' if check4 <= 1.0 else 'NOT OK'}\n"
        )

    return {
        "report": s,
        "is_ok": check,
        "utilization": utilization,
        "checks": {"check1": float(check1), "check2": float(check2),
                   "check3": _c3, "check4": float(check4)},
        "k_c": (float(k_c[0]), float(k_c[1])),
        "k_m": float(k_m),
    }
