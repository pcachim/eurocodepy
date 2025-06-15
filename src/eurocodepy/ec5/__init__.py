# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 5 Timber Module.

This module provides classes and functions for Eurocode 5 timber design.
It includes properties for different timber grades and types, as well as calculations
for serviceability and ultimate limit states.
it also includes vibration and deformation calculations.
"""

from eurocodepy.ec5.materials import (
    CLT,
    GL,
    LVL,
    ST,
    Glulam,
    Hardwood,
    LoadDuration,
    RiskClass,
    ServiceClass,
    Softwood,
    SolidTimber,
    Timber,
    TimberClass,
)
from eurocodepy.ec5 import sls
from eurocodepy.ec5.sls import deformation, vibration
from eurocodepy.ec5.sls.vibration import a_from_b, b_from_a, floor_freq, vel, vlim
