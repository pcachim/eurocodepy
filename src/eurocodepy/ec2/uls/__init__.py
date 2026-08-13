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
    punch as punch,
    shear as shear,
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

__all__ = [
    # submodules
    "beam", "punch", "shear", "shell", "torsion",
    # materials (re-exported for convenience)
    "Concrete", "ConcreteClass", "Prestress", "PrestressClass",
    "Reinforcement", "ReinforcementClass",
    # bending design
    "RCBeam", "calc_asl", "calc_mrd", "get_bend_params",
    # combined bending + axial (M-N) design
    "calc_asl_nm", "design_rcbeam_nm",
    # shear / torsion
    "calc_asws", "calc_vrd", "calc_vrdc", "calc_vrdmax", "calc_torsion",
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
]
