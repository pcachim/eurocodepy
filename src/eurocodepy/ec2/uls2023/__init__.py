# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2 ULS — **EN 1992-1-1:2023** flavour.

This package mirrors :mod:`eurocodepy.ec2.uls`, exposing the same names, and
overrides only the calculations for which the 2023 generation of EC2 is already
implemented — currently **punching shear**. Every other check (bending, shear,
torsion, shell) is re-used from the shared EN 1992-1-1:2004 modules until a 2023
version exists, so ``ec2.uls`` and ``ec2.uls2023`` are drop-in swappable.

    from eurocodepy.ec2 import uls2023 as uls
    uls.calc_vrdcp(...)        # 2023 punching
    uls.calc_vrd(...)          # shared 2004 shear (no 2023 version yet)
"""

# Re-export the whole EN 1992-1-1:2004 ULS surface…
from eurocodepy.ec2.uls import *  # ruff: ignore[undefined-local-with-import-star]
from eurocodepy.ec2.uls import __all__ as _uls_all

# …then override the punching submodule and its functions with the 2023 model.
from eurocodepy.ec2.uls2023 import punch as punch
from eurocodepy.ec2.uls2023.punch import (
    calc_perimeters as calc_perimeters,
)
from eurocodepy.ec2.uls2023.punch import (
    calc_vedp as calc_vedp,
)
from eurocodepy.ec2.uls2023.punch import (
    calc_vrdcminp as calc_vrdcminp,
)
from eurocodepy.ec2.uls2023.punch import (
    calc_vrdcp as calc_vrdcp,
)

# …and the column check (no override yet -- see column.py's own docstring).
from eurocodepy.ec2.uls2023 import column as column
from eurocodepy.ec2.uls2023.column import (
    ColumnInput as ColumnInput,
    ColumnResult as ColumnResult,
    RebarLayout as RebarLayout,
    biaxial_interaction_exponent as biaxial_interaction_exponent,
    design_column_reinforcement as design_column_reinforcement,
    effective_length as effective_length,
    eurocode2_column_check as eurocode2_column_check,
    maximum_column_reinforcement_m2 as maximum_column_reinforcement_m2,
    minimum_column_reinforcement_m2 as minimum_column_reinforcement_m2,
    nominal_curvature_e2 as nominal_curvature_e2,
    nominal_stiffness_moment as nominal_stiffness_moment,
    slenderness_limit as slenderness_limit,
    uniaxial_moment_resistance as uniaxial_moment_resistance,
)

# …and the combined shear+torsion check (no override yet -- see
# shear_torsion.py's own docstring).
from eurocodepy.ec2.uls2023 import shear_torsion as shear_torsion
from eurocodepy.ec2.uls2023.shear_torsion import (
    ShearTorsionInput as ShearTorsionInput,
    ShearTorsionResult as ShearTorsionResult,
    distribute_torsion_longitudinal as distribute_torsion_longitudinal,
    eurocode2_shear_torsion_check as eurocode2_shear_torsion_check,
)

__all__ = list(_uls_all)
