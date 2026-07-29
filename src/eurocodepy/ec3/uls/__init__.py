# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 ULS (Ultimate Limit State) verifications.

Two modules carry the design checks, organised by EN 1993-1-1 clause:

* :mod:`cross_section` — §6.2 resistance of cross-sections (N, My, Mz, Vy, Vz,
  T and their interactions);
* :mod:`member_buckling` — §6.3 buckling resistance of members (flexural and
  lateral-torsional buckling, the interaction equations 6.61/6.62, and the
  elastic critical forces Ncr / Mcr).

The older :mod:`checks` and :mod:`bending` modules are kept for backward
compatibility.
"""

from eurocodepy.ec3.uls.checks import (
    SectionCheckResult as SectionCheckResult,
    SectionProperties as SectionProperties,
    eurocode3_combined_check as eurocode3_combined_check,
    BucklingParameters as BucklingParameters,
    eurocode3_buckling_check as eurocode3_buckling_check,
    check_ltb_resistance as check_ltb_resistance,
)
from eurocodepy.ec3.uls.member_buckling import (
    MemberInput as MemberInput,
    MemberCheckResult as MemberCheckResult,
    eurocode3_member_check as eurocode3_member_check,
    member_check_profile as member_check_profile,
    reduction_chi as reduction_chi,
    reduction_chi_lt as reduction_chi_lt,
    elastic_critical_moment as elastic_critical_moment,
    cm_factor as cm_factor,
    calc_Ncr as calc_Ncr,
    calc_Ncr_T as calc_Ncr_T,
    calc_Ncr_TF as calc_Ncr_TF,
)
from eurocodepy.ec3.uls.cross_section import (
    SectionForces as SectionForces,
    SectionResistanceInput as SectionResistanceInput,
    SectionResistanceResult as SectionResistanceResult,
    eurocode3_section_check as eurocode3_section_check,
    section_check_profile as section_check_profile,
    shear_resistance as shear_resistance,
    torsion_resistance as torsion_resistance,
    reduced_shear_resistance_torsion as reduced_shear_resistance_torsion,
)

__all__ = [
    "SectionCheckResult",
    "SectionProperties",
    "eurocode3_combined_check",
    "BucklingParameters",
    "eurocode3_buckling_check",
    "check_ltb_resistance",
    "calc_Ncr",
    "calc_Ncr_T",
    "calc_Ncr_TF",
    "MemberInput",
    "MemberCheckResult",
    "eurocode3_member_check",
    "member_check_profile",
    "reduction_chi",
    "reduction_chi_lt",
    "elastic_critical_moment",
    "cm_factor",
    "SectionForces",
    "SectionResistanceInput",
    "SectionResistanceResult",
    "eurocode3_section_check",
    "section_check_profile",
    "shear_resistance",
    "torsion_resistance",
    "reduced_shear_resistance_torsion",
]
