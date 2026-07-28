# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 - Design of steel structures.

This module provides classes and functions for Eurocode 3 steel design.
It includes properties for different steel grades and types, profile classes
(I, CHS, RHS, SHS), bolts, welds, and connection checks.
"""

from eurocodepy import dbase as dbase
from eurocodepy.ec3 import (
    classification as classification,
    materials as materials,
    uls as uls,
)
from eurocodepy.ec3.classification import (
    SectionClass as SectionClass,
    ClassificationResult as ClassificationResult,
    EffectiveProperties as EffectiveProperties,
    epsilon as epsilon,
    classify_section as classify_section,
    classify_internal_part as classify_internal_part,
    classify_outstand_part as classify_outstand_part,
    classify_chs_part as classify_chs_part,
    effective_properties as effective_properties,
)
from eurocodepy.ec3.materials import (
    BoltGrade as BoltGrade,
    Bolt as Bolt,
    BoltGrades as BoltGrades,
    BoltsEnum as BoltsEnum,
    Steel as Steel,
    SteelEnum as SteelEnum,
    SteelSection as SteelSection,
    SteelPlate as SteelPlate,
    BoltedConnection as BoltedConnection,
    PinnedConnection as PinnedConnection,
    PinnedConnectionDouble as PinnedConnectionDouble,
    ProfileCHS as ProfileCHS,
    ProfileI as ProfileI,
    ProfileRHS as ProfileRHS,
    ProfileSHS as ProfileSHS,
    ProfilesI as ProfilesI,
    ProfilesCHS as ProfilesCHS,
    ProfilesRHS as ProfilesRHS,
    ProfilesSHS as ProfilesSHS,
    ProfilesCHSEnum as ProfilesCHSEnum,
    ProfilesIEnum as ProfilesIEnum,
    ProfilesRHSEnum as ProfilesRHSEnum,
    ProfilesSHSEnum as ProfilesSHSEnum,
    Weld as Weld,
    WeldConnection as WeldConnection,
    WeldTypeEnum as WeldTypeEnum,
)

__all__ = [
    "dbase",
    "classification",
    "materials",
    "uls",
    "SectionClass",
    "ClassificationResult",
    "EffectiveProperties",
    "epsilon",
    "classify_section",
    "classify_internal_part",
    "classify_outstand_part",
    "classify_chs_part",
    "effective_properties",
    "BoltGrade",
    "Bolt",
    "BoltGrades",
    "BoltsEnum",
    "Steel",
    "SteelEnum",
    "SteelSection",
    "SteelPlate",
    "BoltedConnection",
    "PinnedConnection",
    "PinnedConnectionDouble",
    "ProfileCHS",
    "ProfileI",
    "ProfileRHS",
    "ProfileSHS",
    "ProfilesI",
    "ProfilesCHS",
    "ProfilesRHS",
    "ProfilesSHS",
    "ProfilesCHSEnum",
    "ProfilesIEnum",
    "ProfilesRHSEnum",
    "ProfilesSHSEnum",
    "Weld",
    "WeldConnection",
    "WeldTypeEnum",
]
