# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 5 Timber Module.

This module provides classes and functions for Eurocode 5 timber design.
It includes properties for different timber grades and types, as well as calculations
for serviceability and ultimate limit states.
it also includes vibration and deformation calculations.
"""

from eurocodepy.ec5.materials import (
    CLT as CLT,
    GL as GL,
    LVL as LVL,
    ST as ST,
    Glulam as Glulam,
    Hardwood as Hardwood,
    LoadDuration as LoadDuration,
    RiskClass as RiskClass,
    ServiceClass as ServiceClass,
    Softwood as Softwood,
    SolidTimber as SolidTimber,
    Timber as Timber,
    TimberClass as TimberClass,
    TimberForcesType as TimberForcesType,
    TimberGrades as TimberGrades,
    TimberProduct as TimberProduct,
    TimberType as TimberType,
    GetTimberDesignValues as GetTimberDesignValues,
)
from eurocodepy.ec5 import (
    sls as sls,
    uls as uls,
)
from eurocodepy.ec5.sls import (
    deformation as deformation,
    vibration as vibration,
)
from eurocodepy.ec5.sls.vibration import (
    a_from_b as a_from_b,
    b_from_a as b_from_a,
    floor_freq as floor_freq,
    vel as vel,
    vlim as vlim,
)
from eurocodepy.ec5.uls import bending as bending

__all__ = [
    "CLT",
    "GL",
    "LVL",
    "ST",
    "Glulam",
    "Hardwood",
    "LoadDuration",
    "RiskClass",
    "ServiceClass",
    "Softwood",
    "SolidTimber",
    "Timber",
    "TimberClass",
    "TimberForcesType",
    "TimberGrades",
    "TimberProduct",
    "TimberType",
    "GetTimberDesignValues",
    "sls",
    "uls",
    "deformation",
    "vibration",
    "a_from_b",
    "b_from_a",
    "floor_freq",
    "vel",
    "vlim",
    "bending",
]
