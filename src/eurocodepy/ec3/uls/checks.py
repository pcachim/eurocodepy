# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 ULS check functions — **deprecated**.

These early, simplified checks have been superseded by the two canonical
modules and are kept only for backward compatibility:

* cross-section resistance (N, My, Mz, Vy, Vz, T) →
  :mod:`eurocodepy.ec3.uls.cross_section` (``eurocode3_section_check``);
* member flexural / lateral-torsional buckling →
  :mod:`eurocodepy.ec3.uls.member_buckling` (``eurocode3_member_check``).

The elastic critical forces ``calc_Ncr`` / ``calc_Ncr_T`` / ``calc_Ncr_TF`` now
live in :mod:`member_buckling` and are re-exported here. Calling the deprecated
check functions emits a :class:`DeprecationWarning`.
"""

import warnings
from dataclasses import dataclass

import numpy as np


def _deprecated(old: str, new: str) -> None:
    """Emit a DeprecationWarning pointing from *old* to *new*."""
    warnings.warn(
        f"eurocodepy.ec3.uls.checks.{old} is deprecated; use {new} instead.",
        DeprecationWarning, stacklevel=3)


@dataclass
class SectionCheckResult:
    """Result of Eurocode 3 combined check for a section.

    Attributes
    ----------
    N_Ed: float                     # Design axial force (kN)
    M_Ed: float                     # Design bending moment (kNm)
    V_Ed: float                     # Design shear force (kN)
    N_Rd: float                     # Design axial resistance (kN)
    M_Rd: float                     # Design bending resistance (kNm)
    V_pl_Rd: float                  # Design shear resistance (kN)
    axial_utilization: float        # Utilization ratio for axial force
    bending_utilization: float      # Utilization ratio for bending moment
    shear_utilization: float        # Utilization ratio for shear force
    interaction_utilization: float  # Combined interaction ratio
    shear_reduction_applied: bool   # True if shear reduction was applied
    passed: bool                    # True if all checks pass

    """

    N_Ed: float                     # Axial force (kN)
    M_Ed: float                     # Bending moment (kNm)
    V_Ed: float                     # Shear force (kN)
    N_Rd: float                     # Axial resistance (kN)
    M_Rd: float                     # Bending resistance (kNm)
    V_pl_Rd: float                  # Shear resistance (kN)
    axial_utilization: float        # Utilization ratio for axial force
    bending_utilization: float      # Utilization ratio for bending
    shear_utilization: float        # Utilization ratio for shear
    interaction_utilization: float  # Combined interaction ratio
    shear_reduction_applied: bool   # True if shear reduction was applied
    passed: bool                    # True if all checks pass

    def __str__(self) -> str:
        """Return a string representation of the SectionCheckResult object.

        Returns
        -------
        str
            String representation of the SectionCheckResult object.

        """
        return (
            f"Forces:\n"
            f"  Axial (N_Ed): {self.N_Ed:.2f} kN\n"
            f"  Bending (M_Ed): {self.M_Ed:.2f} kNm\n"
            f"  Shear (V_Ed): {self.V_Ed:.2f} kN\n"
            f"Design Resistances:\n"
            f"  Axial (N_Rd): {self.N_Rd:.2f} kN\n"
            f"  Bending (M_Rd): {self.M_Rd:.2f} kNm\n"
            f"  Shear (V_pl_Rd): {self.V_pl_Rd:.2f} kN\n"
            f"Utilization Ratios:\n"
            f"  Axial: {self.axial_utilization:.3f}\n"
            f"  Bending: {self.bending_utilization:.3f}\n"
            f"  Shear: {self.shear_utilization:.3f}\n"
            f"  Interaction: {self.interaction_utilization:.3f}\n"
            f"Shear Reduction Applied: {self.shear_reduction_applied}\n"
            f"Pass: {'✅' if self.passed else '❌'}"
        )


@dataclass
class SectionProperties:
    """Section properties for Eurocode 3 combined check."""

    A: float        # Cross-sectional area [mm^2]
    W_el: float     # Elastic section modulus [mm^3]
    fy: float       # Yield strength [MPa]


def eurocode3_combined_check(  # ruff: ignore[undocumented-param, too-many-arguments, too-many-positional-arguments]
    N_Ed: float,
    M_Ed: float,
    V_Ed: float,
    area: float,
    area_v: float,
    W_el: float,
    fy: float,
    gamma_M0: float = 1.0,
    gamma_M1: float = 1.0,
) -> SectionCheckResult:
    """Eurocode 3 combined check for axial force, bending and shear.

    This function performs a Eurocode 3 combined check for axial force, bending and 
    shear.
    It takes the design axial force, bending moment, shear force, and the section 
    properties as input. It returns a dictionary with the utilization ratios
    and a pass/fail status.

    Args:
        N_Ed (float): Axial design force [kN]
        M_Ed (float): Bending moment design value [kNm]
        V_Ed (float): Shear force design value [kN]
        section (SectionProperties): Section properties (A, W_el, fy)
        gamma_M0 (float, optional): Partial safety factor for resistance of
        cross-sections to yielding. Default is 1.0.
        gamma_M1 (float, optional): Partial safety factor for resistance of members to
        instability. Default is 1.0.
        gamma_M2 (float, optional): Partial safety factor for resistance of
        cross-sections to rupture. Default is 1.25.

    Returns:
        dict: Dictionary with utilization ratios and pass/fail status.
        - N_Rd: Axial resistance [kN]
        - M_Rd: Bending resistance [kNm]
        - V_pl_Rd: Shear resistance [kN]
        - axial_utilization: Utilization ratio for axial force
        - bending_utilization: Utilization ratio for bending moment
        - shear_utilization: Utilization ratio for shear force
        - interaction_utilization: Combined utilization ratio
        - shear_reduction_applied: Whether shear reduction was applied
        - pass: True if all checks pass, False otherwise

    """
    _deprecated("eurocode3_combined_check",
                "eurocodepy.ec3.uls.cross_section.eurocode3_section_check")
    # Convert fy to kN/mm^2
    fy_kN = fy * 1000

    # Resistances
    N_Rd = area * fy_kN / gamma_M0  # kN
    M_Rd = W_el * fy_kN / gamma_M1  # kNm
    V_pl_Rd = 0.5 * area_v * fy_kN / gamma_M0  # kN (approx. for I-beams in shear)

    # Checks
    axial_util = N_Ed / N_Rd
    bending_util = M_Ed / M_Rd
    shear_util = V_Ed / V_pl_Rd

    interaction_util = axial_util + bending_util

    shear_reduction = V_Ed / V_pl_Rd > 0.5
    if shear_reduction:
        # Simplified reduction
        M_Rd_red = M_Rd * (1 - 0.5 * (V_Ed / V_pl_Rd - 0.5))
        bending_util = M_Ed / M_Rd_red
        interaction_util = axial_util + bending_util

    return SectionCheckResult(
        N_Ed=N_Ed,
        M_Ed=M_Ed,
        V_Ed=V_Ed,
        N_Rd=N_Rd,
        M_Rd=M_Rd,
        V_pl_Rd=V_pl_Rd,
        axial_utilization=axial_util,
        bending_utilization=bending_util,
        shear_utilization=shear_util,
        interaction_utilization=interaction_util,
        shear_reduction_applied=shear_reduction,
        passed=interaction_util <= 1 and shear_util <= 1)


@dataclass
class BucklingParameters:
    A: float         # Área da seção [mm²]
    fy: float        # Limite de escoamento [MPa]
    L_cr: float      # Comprimento de flambagem [mm]
    i: float         # Raio de giração (sqrt(I/A)) [mm]


def eurocode3_buckling_check(
    *,
    N_Ed: float,
    params: BucklingParameters,
    buckling_curve: str = "b",
    gamma_M1: float = 1.0,
) -> dict[str, float]:
    """Verifica a resistência à flambagem de acordo com o Eurocode 3 (EN 1993-1-1).

    Args:
    N_Ed : força axial de projeto [kN]
    params : BucklingParameters (A, fy, L_cr, i)
    buckling_curve : curva de flambagem ('a', 'b', 'c', 'd')
    gamma_M1 : coeficiente de segurança parcial

    Returns:
        dict: Um dicionário com os resultados da verificação, incluindo lambda_bar, chi, N_pl_Rd, N_b_Rd, utilization e pass.

    """
    _deprecated("eurocode3_buckling_check",
                "eurocodepy.ec3.uls.member_buckling.eurocode3_member_check")
    # Limite de escoamento convertido para kN/mm²
    fy_kN = params.fy / 1000

    # Resistência plástica à compressão (sem flambagem)
    N_pl_Rd = params.A * fy_kN / gamma_M1  # [kN]

    # Esbeltez adimensional (lambda-bar)
    slenderness = params.L_cr / params.i
    lambda_bar = slenderness * np.sqrt(fy_kN / (np.pi**2 * 210e3))  # E = 210000 MPa

    # Parâmetros alfa da curva de flambagem
    alpha_dict = {
        "a": 0.21,
        "b": 0.34,
        "c": 0.49,
        "d": 0.76,
    }
    alpha = alpha_dict.get(buckling_curve, 0.34)

    # Parâmetros de flambagem
    phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    chi = min(1 / (phi + np.sqrt(phi**2 - lambda_bar**2)), 1.0)

    # Resistência de cálculo com flambagem
    N_b_Rd = chi * N_pl_Rd  # [kN]

    # Utilização
    utilization = N_Ed / N_b_Rd

    return {
        "lambda_bar": round(lambda_bar, 3),
        "chi": round(chi, 3),
        "N_pl_Rd [kN]": round(N_pl_Rd, 2),
        "N_b_Rd [kN]": round(N_b_Rd, 2),
        "utilization": round(utilization, 3),
        "pass": utilization <= 1,
    }


def check_ltb_resistance(
    f_y: float,
    E: float,
    G: float,
    gamma_M1: float,
    I_y: float,
    I_z: float,
    W_el_z: float,
    I_w: float,
    I_t: float,
    L: float,
    M_Ed: float,
    C1: float = 1.0,
    alpha_LT: float = 0.34,
) -> dict:
    """Check lateral torsional buckling resistance for an I-section beam.

    Parameters
    ----------
        f_y:     Yield strength [Pa]
        E:       Young’s modulus [Pa]
        G:       Shear modulus [Pa]
        gamma_M1: Partial safety factor (usually 1.0)
        I_y:     Minor axis moment of inertia [m^4]
        I_z:     Major axis moment of inertia [m^4]
        W_el_z:  Elastic section modulus about major axis [m^3]
        I_w:     Warping constant [m^6]
        I_t:     Torsional constant [m^4]
        L:       Buckling length [m]
        M_Ed:    Design moment acting on the beam [Nm]
        C1:      Moment distribution factor (default = 1.0)
        alpha_LT: Imperfection factor (default = 0.34 for rolled sections)

    Returns
    -------
        A dictionary with:
            - M_cr: Critical moment [Nm]
            - lambda_bar_LT: Non-dimensional slenderness
            - chi_LT: Reduction factor
            - M_b_Rd: Design moment resistance [Nm]
            - Utilization: M_Ed / M_b_Rd
            - Status: "PASS" or "FAIL"

    """
    _deprecated("check_ltb_resistance",
                "eurocodepy.ec3.uls.member_buckling (elastic_critical_moment + "
                "reduction_chi_lt, or eurocode3_member_check)")
    # Elastic critical moment (Annex F)
    pi = np.pi
    M_cr = (C1 * pi**2 * E * I_z / (L**2)) * np.sqrt(
        (G * I_t * L**2) / (pi**2 * E * I_z) + (pi**2 * I_w) / (L**2 * I_z),
    )

    # Design resistance without LTB
    M_y_Rd = f_y * W_el_z / gamma_M1

    # Slenderness
    lambda_bar_LT = np.sqrt(W_el_z * f_y / M_cr)

    # Reduction factor chi_LT (EN 1993-1-1, Eq. 6.56)
    phi_LT = 0.5 * (1 + alpha_LT * (lambda_bar_LT - 0.2) + lambda_bar_LT**2)
    chi_LT = min(1.0, 1.0 / (phi_LT + np.sqrt(phi_LT**2 - lambda_bar_LT**2)))

    # LTB design resistance
    M_b_Rd = chi_LT * M_y_Rd

    # Check utilization
    utilization = M_Ed / M_b_Rd
    status = "PASS" if utilization <= 1.0 else "FAIL"

    return {
        "M_cr [kNm]": M_cr / 1e3,
        "λ̄_LT": lambda_bar_LT,
        "χ_LT": chi_LT,
        "M_b,Rd [kNm]": M_b_Rd / 1e3,
        "Utilization": utilization,
        "Status": status,
    }


# The elastic critical buckling forces moved to ``member_buckling`` (they are
# the inputs to the flexural/torsional buckling checks). Re-exported here so
# existing ``from eurocodepy.ec3.uls.checks import calc_Ncr`` imports keep
# working.
from eurocodepy.ec3.uls.member_buckling import (  # ruff: ignore[module-import-not-at-top-of-file]
    calc_Ncr as calc_Ncr,
)
from eurocodepy.ec3.uls.member_buckling import (
    calc_Ncr_T as calc_Ncr_T,
)
from eurocodepy.ec3.uls.member_buckling import (
    calc_Ncr_TF as calc_Ncr_TF,
)
