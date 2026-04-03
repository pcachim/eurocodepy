# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2: Design of concrete structures.

This module provides classes and functions for Eurocode 2 concrete design.
It includes properties for different concrete grades and types, as well as calculations
for serviceability and ultimate limit states.
"""

from eurocodepy.ec2.materials import (
    A400NR,
    A500NR,
    A500EL,
    A400NRSD,
    A500NRSD,
    B400A,
    B400B,
    B400C,
    B500A,
    B500B,
    B500C,
    B600A,
    B600B,
    B600C,
    B700A,
    B700B,
    B700C,
    Bar,
    BarLayout,
    BarSizes,
    Bundle,
    C20_25,
    C25_30,
    C30_37,
    C35_45,
    C40_50,
    C45_55,
    C50_60,
    C55_67,
    C60_75,
    C70_85,
    C80_95,
    C90_105,
    Concrete,
    ConcreteClass,
    ConcreteGrades,
    CreepParams,
    GammaC,
    GammaCT,
    GammaP,
    GammaS,
    Prestress,
    PrestressClass,
    Reinforcement,  # noqa: F401
    ReinforcementClass,
    ReinforcementGrades,
    ShrinkStrainParams,
    beta_cc,
    beta_ce,
    calc_creep_coef,  # EN1992-1:2004
    calc_shrink_strain,  # EN1992-1:2004
    cemprops,  # noqa: F401
    get_concrete,
    get_reinforcement,
)
from eurocodepy.ec2 import fire, sls, uls
from eurocodepy.ec2.sls import creep, shrinkage
from eurocodepy.ec2.sls.creep import creep_coef  # EN1992-1:2025
from eurocodepy.ec2.sls.shrinkage import shrink_strain  # EN1992-1:2025
from eurocodepy.ec2.uls import beam as beam, shear as shear, shell as shell
from eurocodepy.ec2.uls.beam import calc_asl, calc_mrd, get_bend_params
from eurocodepy.ec2.uls.punch import (
    calc_perimeters,
    calc_vedp,
    calc_vrdcminp,
    calc_vrdcp,
)
from eurocodepy.ec2.uls.shear import calc_asws, calc_vrd, calc_vrdc, calc_vrdmax
from eurocodepy.ec2.uls.shell import calc_reinf_plane, calc_reinf_shell
