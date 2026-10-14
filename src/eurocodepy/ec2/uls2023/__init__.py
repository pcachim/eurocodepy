# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2 ULS — **EN 1992-1-1:2023** flavour.

This package mirrors :mod:`eurocodepy.ec2.uls`, exposing the same names, and
overrides only the calculations for which the 2023 generation of EC2 is already
implemented — currently **punching shear**, **shear** (8.2), **torsion** (8.3, with
the combined shear+torsion check), **membrane/slab design** (Annex G) and the **detailing rules** (Clause 12,
``uls2023.detailing``). Every
other check (bending) is re-used from the shared EN 1992-1-1:2004
modules until a 2023 version exists, so ``ec2.uls`` and ``ec2.uls2023`` are
drop-in swappable.

    from eurocodepy.ec2 import uls2023 as uls
    uls.calc_vrdcp(...)                  # 2023 punching
    uls.shear.calc_taurdc(...)           # 2023 shear formulae (8.2)
    uls.eurocode2_shear_check(...)       # 2023 shear check (new ShearInput)
    uls.calc_vrd(...)                    # 2004 shear functions (``calc_vrdc`` ...)
"""

# Re-export the whole EN 1992-1-1:2004 ULS surface…
from eurocodepy.ec2.uls import (  # the whole EN 1992-1-1:2004 ULS surface, listed so that it is visible to tools
    Concrete as Concrete,
    ConcreteClass as ConcreteClass,
    Prestress as Prestress,
    PrestressClass as PrestressClass,
    Reinforcement as Reinforcement,
    ReinforcementClass as ReinforcementClass,
    RCBeam as RCBeam,
    calc_asl as calc_asl,
    calc_mrd as calc_mrd,
    get_bend_params as get_bend_params,
    calc_asl_nm as calc_asl_nm,
    calc_asl_nm_strain as calc_asl_nm_strain,
    design_rcbeam_nm as design_rcbeam_nm,
    anchorage_coefficients as anchorage_coefficients,
    basic_anchorage_length as basic_anchorage_length,
    beam_cover_distance as beam_cover_distance,
    bond_conditions_beam as bond_conditions_beam,
    bond_strength as bond_strength,
    design_anchorage_length as design_anchorage_length,
    lap_coefficient_alpha6 as lap_coefficient_alpha6,
    lap_length as lap_length,
    calc_asws as calc_asws,
    calc_vrd as calc_vrd,
    calc_vrdc as calc_vrdc,
    calc_vrdmax as calc_vrdmax,
    calc_torsion as calc_torsion,
    eurocode2_column_check as eurocode2_column_check,
    ColumnInput as ColumnInput,
    ColumnResult as ColumnResult,
    RebarLayout as RebarLayout,
    slenderness_limit as slenderness_limit,
    effective_length as effective_length,
    biaxial_interaction_exponent as biaxial_interaction_exponent,
    nominal_curvature_e2 as nominal_curvature_e2,
    nominal_stiffness_moment as nominal_stiffness_moment,
    uniaxial_moment_resistance as uniaxial_moment_resistance,
    design_column_reinforcement as design_column_reinforcement,
    minimum_column_reinforcement_m2 as minimum_column_reinforcement_m2,
    maximum_column_reinforcement_m2 as maximum_column_reinforcement_m2,
    eurocode2_shear_check as eurocode2_shear_check,
    ShearInput as ShearInput,
    ShearResult as ShearResult,
    calc_perimeters as calc_perimeters,
    calc_vedp as calc_vedp,
    calc_vrdcminp as calc_vrdcminp,
    calc_vrdcp as calc_vrdcp,
    eurocode2_punching_check as eurocode2_punching_check,
    PunchInput as PunchInput,
    PunchResult as PunchResult,
    calc_reinf_plane as calc_reinf_plane,
    calc_reinf_shell as calc_reinf_shell,
    eurocode2_membrane_check as eurocode2_membrane_check,
    MembraneInput as MembraneInput,
    MembraneResult as MembraneResult,
    eurocode2_shell_check as eurocode2_shell_check,
    ShellInput as ShellInput,
    ShellResult as ShellResult,
    eurocode2_slab_check as eurocode2_slab_check,
    SlabInput as SlabInput,
    SlabResult as SlabResult,
    eurocode2_shear_torsion_check as eurocode2_shear_torsion_check,
    ShearTorsionInput as ShearTorsionInput,
    ShearTorsionResult as ShearTorsionResult,
    distribute_torsion_longitudinal as distribute_torsion_longitudinal,
)
from eurocodepy.ec2.uls import __all__ as _uls_all
from eurocodepy.ec2.uls import (  # modules that have no 2023 counterpart
    anchorage as anchorage,
    beam as beam,
    shell as shell,
)

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

# …the shear formulae and the shear check (EN 1992-1-1:2023 Clause 8.2), and the detailing rules (Clause 12)…
from eurocodepy.ec2.uls2023 import detailing as detailing
from eurocodepy.ec2.uls2023 import shear as shear
from eurocodepy.ec2.uls2023 import shear_check as shear_check
from eurocodepy.ec2.uls2023.shear_check import (
    ShearInput as ShearInput,
    ShearResult as ShearResult,
    eurocode2_shear_check as eurocode2_shear_check,
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

# …the Annex G design of membrane, shell and slab elements (``slab_design`` is not a drop-in
# for ``slab_check``: it takes the design moments of the element, not Wood-Armer moments,
# so it keeps its own module and names)…
from eurocodepy.ec2.uls2023 import annex_g as annex_g
from eurocodepy.ec2.uls2023 import membrane_check as membrane_check
from eurocodepy.ec2.uls2023 import shell_check as shell_check
from eurocodepy.ec2.uls2023 import slab_design as slab_design
from eurocodepy.ec2.uls2023.shell_check import (
    ShellInput as ShellInput,
    ShellResult as ShellResult,
    eurocode2_shell_check as eurocode2_shell_check,
)
from eurocodepy.ec2.uls2023.membrane_check import (
    MembraneInput as MembraneInput,
    MembraneResult as MembraneResult,
    eurocode2_membrane_check as eurocode2_membrane_check,
)

# …the torsion design (EN 1992-1-1:2023 8.3) and the combined shear+torsion check.
from eurocodepy.ec2.uls2023 import shear_torsion as shear_torsion
from eurocodepy.ec2.uls2023 import torsion as torsion
from eurocodepy.ec2.uls2023.torsion import calc_torsion as calc_torsion
from eurocodepy.ec2.uls2023.shear_torsion import (
    ShearTorsionInput as ShearTorsionInput,
    ShearTorsionResult as ShearTorsionResult,
    distribute_torsion_longitudinal as distribute_torsion_longitudinal,
    eurocode2_shear_torsion_check as eurocode2_shear_torsion_check,
)

__all__ = list(_uls_all)
