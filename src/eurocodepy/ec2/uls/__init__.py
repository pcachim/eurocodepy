# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2 ULS (Ultimate Limit State) design.

Bending, shear, punching and shell reinforcement design according to
EN 1992-1-1.
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
)
from eurocodepy.ec2.uls.beam import (
    RCBeam as RCBeam,
    calc_asl as calc_asl,
    calc_mrd as calc_mrd,
    get_bend_params as get_bend_params,
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
from eurocodepy.ec2.uls.punch import (
    calc_perimeters as calc_perimeters,
    calc_vedp as calc_vedp,
    calc_vrdcminp as calc_vrdcminp,
    calc_vrdcp as calc_vrdcp,
)
from eurocodepy.ec2.uls.shell import (
    calc_reinf_plane as calc_reinf_plane,
    calc_reinf_shell as calc_reinf_shell,
)

__all__ = [
    # submodules
    "beam", "punch", "shear", "shell",
    # materials (re-exported for convenience)
    "Concrete", "ConcreteClass", "Prestress", "PrestressClass",
    "Reinforcement", "ReinforcementClass",
    # bending design
    "RCBeam", "calc_asl", "calc_mrd", "get_bend_params",
    # shear / torsion
    "calc_asws", "calc_vrd", "calc_vrdc", "calc_vrdmax",
    # punching shear
    "calc_perimeters", "calc_vedp", "calc_vrdcminp", "calc_vrdcp",
    # shell reinforcement
    "calc_reinf_plane", "calc_reinf_shell",
]
