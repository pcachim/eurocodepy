# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2: Design of concrete structures.

This module provides classes and functions for Eurocode 2 concrete design.
It includes properties for different concrete grades and types, as well as calculations
for serviceability and ultimate limit states.
"""

from eurocodepy.ec2.materials import (
    Bar,
    BarLayout,
    Bundle,
    Concrete,
    ConcreteClass,
    ConcreteGrade,
    CreepParams,
    GammaC,
    GammaCT,
    GammaP,
    GammaS,
    Prestress,
    PrestressClass,
    Reinforcement,
    ReinforcementClass,
    ReinforcementGrade,
    ShrinkStrainParams,
    beta_cc,
    beta_ce,
    calc_creep_coef,  # EN1992-1:2004
    calc_shrink_strain,  # EN1992-1:2004
    cemprops,
    get_concrete,
    get_reinforcement,
)
from eurocodepy.ec2 import fire, sls, uls
from eurocodepy.ec2.sls import creep, shrinkage
from eurocodepy.ec2.sls.creep import creep_coef  # EN1992-1:2025
from eurocodepy.ec2.sls.shrinkage import shrink_strain  # EN1992-1:2025
from eurocodepy.ec2.uls import beam, shear, shell
from eurocodepy.ec2.uls.beam import calc_asl, calc_mrd, get_bend_params
from eurocodepy.ec2.uls.shear import calc_asws, calc_vrd, calc_vrdc, calc_vrdmax
from eurocodepy.ec2.uls.shell import calc_reinf_plane, calc_reinf_shell
