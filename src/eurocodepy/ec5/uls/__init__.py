# Copyright (c) 2024. Paulo Cachim.
# SPDX-License-Identifier: MIT
"""Ultimate Limit State (ULS) calculations for Eurocode 5.

This module provides functions for calculating various factors and checks
in timber structures according to Eurocode 5.
"""

from . import bending as bending
from . import cross_section as cross_section
from . import shear as shear
from . import special_beams as special_beams
from .bending import (
    calc_k_c,
    calc_k_m,
    calc_k_red,
    calc_mcr,
    check_bending_with_normal,
    get_safety_factor,
)
from .cross_section import (
    TimberForces,
    TimberSectionInput,
    TimberSectionResult,
    eurocode5_section_check,
)
from .shear import (
    check_shear_with_torsion,
)
from .special_beams import (
    ApexInput,
    ApexResult,
    TaperedEdgeResult,
    apex_volume,
    calc_k_l,
    calc_k_m_alpha,
    calc_k_p,
    calc_k_r,
    calc_k_vol,
    check_apex_zone,
    check_tapered_edge,
)

__all__ = [
    "ApexInput",
    "ApexResult",
    "TaperedEdgeResult",
    "apex_volume",
    "calc_k_l",
    "calc_k_m_alpha",
    "calc_k_p",
    "calc_k_r",
    "calc_k_vol",
    "check_apex_zone",
    "check_tapered_edge",
    "TimberForces",
    "TimberSectionInput",
    "TimberSectionResult",
    "calc_k_c",
    "calc_k_m",
    "calc_k_red",
    "calc_mcr",
    "check_bending_with_normal",
    "check_shear_with_torsion",
    "eurocode5_section_check",
    "get_safety_factor",
]
