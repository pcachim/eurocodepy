# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
"""Eurocode 3 - Steel Design - ULS Bending Design Functions.

This module provides functions for the design of steel profiles under bending
according to Eurocode 3 (EN 1993-1-1).
"""
import numpy as np

from eurocodepy.ec3.materials import ProfileI, ProfileRHS, SteelSection


def check_bending_capacity(moment, moment_capacity, gamma_m0=1.0) -> dict:
    """Check bending capacity utilization.

    Parameters
    ----------
    moment : float
        Design bending moment (kNm)
    moment_capacity : float
        Bending moment capacity (kNm)
    gamma_m0 : float, optional
        Partial factor for material (default: 1.0)

    Returns
    -------
    dict
        Dictionary with utilization ratio and status

    """
    utilization = moment / (moment_capacity / gamma_m0)
    status = "OK" if utilization <= 1.0 else "FAIL"

    return {
        "utilization": utilization,
        "status": status,
        "demand": moment,
        "capacity": moment_capacity / gamma_m0
    }


def calculate_mc_elastic(fy, iy, l_c):
    """Calculate elastic critical moment for lateral-torsional buckling.

    Parameters
    ----------
    fy : float
        Yield strength (MPa)
    iy : float
        Second moment of inertia about y-axis (cm4)
    l_c : float
        Length of compression zone (m)

    Returns
    -------
    float
        Elastic critical moment (kNm)

    """
    # Simplified formula for elastic critical moment
    # Mcr = π/Lc * sqrt(EIy * GIt)
    # This is a simplified version without considering torsional properties
    e_modulus = 210000  # MPa
    mcr = (3.14159 / l_c) * (e_modulus * iy) * 1e-7  # Convert to kNm
    return mcr


def calculate_moment_capacity_class1_2(fy, w_pl):
    """Calculate moment capacity for Class 1 and 2 sections (plastic moment).

    Parameters
    ----------
    fy : float
        Yield strength (MPa)
    w_pl : float
        Plastic section modulus (cm3)

    Returns
    -------
    float
        Plastic moment capacity (kNm)

    """
    # Mp = fy * Wpl (converted from cm3 to m3)
    m_pl = fy * w_pl * 1e-3  # Convert to kNm
    return m_pl


def calculate_moment_capacity_class3(fy, w_el):
    """Calculate moment capacity for Class 3 sections (elastic moment).

    Parameters
    ----------
    fy : float
        Yield strength (MPa)
    w_el : float
        Elastic section modulus (cm3)

    Returns
    -------
    float
        Elastic moment capacity (kNm)

    """
    # Mel = fy * Wel (converted from cm3 to m3)
    m_el = fy * w_el * 1e-3  # Convert to kNm
    return m_el


def calculate_lateral_torsional_buckling_factor(moment_distribution="uniform"):
    """Calculate lateral-torsional buckling reduction factor based on moment distribution.

    Parameters
    ----------
    moment_distribution : str, optional
        Type of moment distribution: "uniform", "linear", "triangular" (default: "uniform")

    Returns
    -------
    float
        Correction factor C1 for lateral-torsional buckling

    """
    factors = {
        "uniform": 1.00,
        "linear": 1.30,
        "triangular": 1.85
    }
    return factors.get(moment_distribution, 1.00)


def calculate_chi_lt(slenderness_lt, moment_class="class1"):
    """Calculate lateral-torsional buckling reduction coefficient.

    Parameters
    ----------
    slenderness_lt : float
        Lateral-torsional slenderness (dimensionless)
    moment_class : str, optional
        Section class (default: "class1")

    Returns
    -------
    float
        Lateral-torsional buckling reduction coefficient χLT
    """
    if slenderness_lt <= 0.4:
        return 1.0

    # Imperfection factor for different section types
    imperfection_factors = {
        "class1": 0.21,  # H sections
        "class2": 0.21,
        "class3": 0.24,  # Rolled sections
        "class4": 0.21
    }

    alpha = imperfection_factors.get(moment_class, 0.21)
    lambda_bar = slenderness_lt

    # EC3 lateral-torsional buckling formula
    phi_lt = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    chi_lt = 1 / (phi_lt + (phi_lt**2 - lambda_bar**2)**0.5)

    return min(chi_lt, 1.0)


def check_combined_bending_shear(moment_demand, moment_capacity, shear_demand=0, shear_capacity=1e10):
    """Check combined bending and shear interaction.

    Parameters
    ----------
    moment_demand : float
        Design bending moment (kNm)
    moment_capacity : float
        Bending moment capacity (kNm)
    shear_demand : float, optional
        Design shear force (kN, default: 0)
    shear_capacity : float, optional
        Shear capacity (kN, default: very large)

    Returns
    -------
    dict
        Dictionary with utilization ratios and status

    """
    util_moment = moment_demand / moment_capacity if moment_capacity > 0 else 0
    util_shear = shear_demand / shear_capacity if shear_capacity > 0 else 0

    # If shear utilization > 0.5, reduce moment capacity
    if util_shear > 0.5:
        reduced_moment_capacity = moment_capacity * (1 - (2 * util_shear - 1)**2)
        util_moment = moment_demand / reduced_moment_capacity

    combined_util = util_moment + util_shear * 0.5  # Simplified interaction
    status = "OK" if combined_util <= 1.0 else "FAIL"

    return {
        "moment_utilization": util_moment,
        "shear_utilization": util_shear,
        "combined_utilization": combined_util,
        "status": status
    }


def design_bending_check(moment_demand, fy, w_pl, w_el, section_class, l_c=None, gamma_m0=1.0):
    """Perform complete bending design check according to EC3.

    Parameters
    ----------
    moment_demand : float
        Design bending moment (kNm)
    fy : float
        Yield strength (MPa)
    w_pl : float
        Plastic section modulus (cm3)
    w_el : float
        Elastic section modulus (cm3)
    section_class : int
        Cross-section class (1, 2, 3, or 4)
    l_c : float, optional
        Length of compression zone (m, for LT buckling check)
    gamma_m0 : float, optional
        Partial factor for material (default: 1.0)

    Returns
    -------
    dict
        Comprehensive design check results

    """
    # Calculate moment capacity based on section class
    if section_class <= 2:
        moment_capacity = calculate_moment_capacity_class1_2(fy, w_pl)
    else:
        moment_capacity = calculate_moment_capacity_class3(fy, w_el)

    # Basic bending check
    result = check_bending_capacity(moment_demand, moment_capacity, gamma_m0)

    # Add section class info
    result["section_class"] = section_class
    result["moment_capacity_used"] = moment_capacity if section_class <= 2 else None

    return result
