# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
import numpy as np


def k_h(height: float, timber_type: str = "timber") -> float:
    """Calculate the height factor k_h for bending according to Eurocode 5.

    Args:
        height (float): Height of the timber member in mm.
        timber_type (str): Type of timber ('timber' or 'glulam').

    Returns:
        float: Height factor k_h

    """
    if timber_type not in {"timber", "glulam"}:
        return 1.0

    if timber_type == "timber":
        return 1.0 if height > 0.150 else np.minimum((0.150 / height)**0.2, 1.3)

    if timber_type == "glulam":
        return 1.0 if height > 0.6 else np.minimum((0.60 / height)**0.1, 1.1)

    if timber_type == "lvl":
        return 1.0 if height > 0.3 else np.minimum((0.3 / height)**0.15, 1.2)

    return 1.0


def k_l(length: float, timber_type: str = "lvl") -> float:
    """Calculate the height factor k_l for tension according to Eurocode 5.

    Args:
        length (float): Length of the timber member in mm.
        timber_type (str): Type of timber ('lvl').

    Returns:
        float: Height factor k_h

    """
    if timber_type != "lvl":
        return 1.0

    if timber_type == "lvl":
        return 1.0 if length > 3.0 else np.minimum((3.0 / length)**0.075, 1.1)

    return 1.0


def calc_k_c(n_ed: float, a_eff: float, f_mk: float, k_mod: float,
                k_h_val: float, k_l_val: float) -> float:
    """Calculate the k_c factor for compression instability according to Eurocode 5.

    Args:
        n_ed (float): Design axial force in N.
        a_eff (float): Effective cross-sectional area in mm².
        f_mk (float): Characteristic bending strength in N/mm².
        k_mod (float): Modification factor for load duration and moisture content.
        k_h_val (float): Height factor.
        k_l_val (float): Length factor.

    Returns:
        float: k_c factor.

    """
    f_md = (k_mod * f_mk) / (k_h_val * k_l_val)
    if n_ed <= 0:
        return 1.0
    else:
        return np.maximum(1.0 - (n_ed / (a_eff * f_md)), 0.0)


def calc_k_crit(eff_length: float, i_y: float, i_z: float, e_mod: float) -> float:
    """Calculate the critical load factor k_crit for compression instability according to Eurocode 5.

    Args:
        eff_length (float): Effective length of the timber member in mm.
        i_y (float): Second moment of area about the y-axis in mm^4.
        i_z (float): Second moment of area about the z-axis in mm^4.
        e_mod (float): Modulus of elasticity in N/mm².

    Returns:
        float: k_crit factor.

    """
    lambda_y = eff_length / np.pi * np.sqrt(e_mod * i_y)
    lambda_z = eff_length / np.pi * np.sqrt(e_mod * i_z)
    lambda_rel = np.maximum(lambda_y, lambda_z)

    if lambda_rel <= 0.4:
        return 1.0
    else:
        return 0.5 + (0.82 / lambda_rel**2)


def check_bending(n_ed: float, m_ed_y: float, m_ed_z: float, k_mod: float, f_mk: float,
                k_h_val: float, k_l_val: float, w_y: float, w_z: float) -> bool:
    """Check bending according to Eurocode 5.

    This function checks if the design bending stresses in both principal directions
    are within the design bending strength of the timber member.
    Uses equation 6.1 from Eurocode 5.

    Args:
        n_ed (float): Design axial force in N.
        m_ed_y (float): Design bending moment about the y-axis in Nm.
        m_ed_z (float): Design bending moment about the z-axis in Nm.
        k_mod (float): Modification factor for load duration and moisture content.
        f_mk (float): Characteristic bending strength in N/mm².
        k_h_val (float): Height factor.
        k_l_val (float): Length factor.
        w_y (float): Section modulus about the y-axis in mm³.
        w_z (float): Section modulus about the z-axis in mm³.

    Returns:
        bool: True if the bending check is satisfied, False otherwise.

    """
    f_md = (k_mod * f_mk) / (k_h_val * k_l_val)

    bending_stress_y = m_ed_y / w_y
    bending_stress_z = m_ed_z / w_z

    return bending_stress_y <= f_md and bending_stress_z <= f_md