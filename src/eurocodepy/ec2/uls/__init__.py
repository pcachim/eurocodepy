# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2 ULS (Ultimate Limit State) design — **EN 1992-1-1:2004**.

Bending, shear, punching and shell reinforcement design according to the 2004
generation of EC2. The prEN 1992-1-1:2023 punching model (same function names,
different formulas) lives in :mod:`eurocodepy.ec2.uls2023`.
"""
from eurocodepy import dbase as dbase
from eurocodepy.ec2.materials import (
    Concrete as Concrete,
    ConcreteClass as ConcreteClass,
    Prestress as Prestress,
    PrestressClass as PrestressClass,
    Reinforcement as Reinforcement,
    ReinforcementClass as ReinforcementClass,
)
from eurocodepy.ec2.uls import (
    beam as beam,
    column as column,
    punch as punch,
    shear as shear,
    shear_torsion as shear_torsion,
    shell as shell,
    torsion as torsion,
)
from eurocodepy.ec2.uls.beam import (
    RCBeam as RCBeam,
    calc_asl as calc_asl,
    calc_mrd as calc_mrd,
    get_bend_params as get_bend_params,
)
from eurocodepy.ec2.uls.bend_axial import (
    calc_asl_nm as calc_asl_nm,
    design_rcbeam_nm as design_rcbeam_nm,
)
# Shear/torsion checks come from `shear` (their canonical home). `beam` also
# defines identical copies; importing from one place avoids an ambiguous
# re-export where the last import silently wins.
from eurocodepy.ec2.uls.shear import (
    calc_asws as calc_asws,
    calc_vrd as calc_vrd,
    calc_vrdc as calc_vrdc,
    calc_vrdmax as calc_vrdmax,
)
from eurocodepy.ec2.uls.shear_check import (
    ShearInput as ShearInput,
    ShearResult as ShearResult,
    eurocode2_shear_check as eurocode2_shear_check,
)
from eurocodepy.ec2.uls.punch import (
    calc_perimeters as calc_perimeters,
    calc_vedp as calc_vedp,
    calc_vrdcminp as calc_vrdcminp,
    calc_vrdcp as calc_vrdcp,
)
from eurocodepy.ec2.uls.punch_check import (
    PunchInput as PunchInput,
    PunchResult as PunchResult,
    eurocode2_punching_check as eurocode2_punching_check,
)
from eurocodepy.ec2.uls.shell import (
    calc_reinf_plane as calc_reinf_plane,
    calc_reinf_shell as calc_reinf_shell,
)
from eurocodepy.ec2.uls.membrane_check import (
    MembraneInput as MembraneInput,
    MembraneResult as MembraneResult,
    eurocode2_membrane_check as eurocode2_membrane_check,
)
from eurocodepy.ec2.uls.slab_check import (
    SlabInput as SlabInput,
    SlabResult as SlabResult,
    eurocode2_slab_check as eurocode2_slab_check,
)
from eurocodepy.ec2.uls.torsion import (
    calc_torsion as calc_torsion,
)
from eurocodepy.ec2.uls.shear_torsion import (
    ShearTorsionInput as ShearTorsionInput,
    ShearTorsionResult as ShearTorsionResult,
    distribute_torsion_longitudinal as distribute_torsion_longitudinal,
    eurocode2_shear_torsion_check as eurocode2_shear_torsion_check,
)
from eurocodepy.ec2.uls.column import (
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

__all__ = [
    # submodules
    "beam", "column", "punch", "shear", "shear_torsion", "shell", "torsion",
    # materials (re-exported for convenience)
    "Concrete", "ConcreteClass", "Prestress", "PrestressClass",
    "Reinforcement", "ReinforcementClass",
    # bending design
    "RCBeam", "calc_asl", "calc_mrd", "get_bend_params",
    # combined bending + axial (M-N) design
    "calc_asl_nm", "design_rcbeam_nm",
    # shear / torsion
    "calc_asws", "calc_vrd", "calc_vrdc", "calc_vrdmax", "calc_torsion",
    # composite column check (§5.8 / §6.1)
    "eurocode2_column_check", "ColumnInput", "ColumnResult", "RebarLayout",
    "slenderness_limit", "effective_length", "biaxial_interaction_exponent",
    "nominal_curvature_e2", "nominal_stiffness_moment",
    "uniaxial_moment_resistance",
    # automatic column reinforcement design (Fase 4)
    "design_column_reinforcement", "minimum_column_reinforcement_m2",
    "maximum_column_reinforcement_m2",
    # composite shear check (§6.2)
    "eurocode2_shear_check", "ShearInput", "ShearResult",
    # punching shear
    "calc_perimeters", "calc_vedp", "calc_vrdcminp", "calc_vrdcp",
    # composite punching check (§6.4 / :2023 §8.4)
    "eurocode2_punching_check", "PunchInput", "PunchResult",
    # shell reinforcement
    "calc_reinf_plane", "calc_reinf_shell",
    # composite membrane check (§6.109)
    "eurocode2_membrane_check", "MembraneInput", "MembraneResult",
    # composite slab flexural check (§6.1 / §9.3.1.1)
    "eurocode2_slab_check", "SlabInput", "SlabResult",
    # composite shear + torsion check (§6.2 + §6.3, Eq. 6.29)
    "eurocode2_shear_torsion_check", "ShearTorsionInput", "ShearTorsionResult",
    "distribute_torsion_longitudinal",
]
