# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 Steel Reinforcement Module.

This module provides classes and functions for Eurocode 3 steel reinforcement design.
It includes properties for different steel grades and types, as well as profile classes.
"""
from enum import Enum

from eurocodepy import dbase

ProfileType = Enum("ProfileType", dbase.SteelProfiles)
"""
Eurocode 3 steel classes existing in the databse.
"""


class Steel:
    """Eurocode 3 steel reinforcement properties.

    :param type_label: Steel type label (e.g., 'S235', 'S275', 'S355', 'S460')
    :raises ValueError: If the steel type is not found in the database.
    """

    def __init__(self, type_label: str = "S275") -> None:
        """Initialize a Steel instance with properties from the specified steel label.

        Args:
        type_label (str): Steel type label (e.g., 'S235', 'S275', 'S355', 'S460')

        Raises:
        ValueError: If the steel type is not found in the database.

        """
        if type_label not in dbase.ReinforcementGrades:
            msg = (
                f"Steel type '{type_label}' not found in database. "
                f"Steel type must be one of {list(dbase.ReinforcementGrades.keys())}"
            )
            raise ValueError(msg)

        reinf = dbase.ReinforcementGrades[type_label]
        self.fyk = reinf["fyk"]  # Characteristic yield strength (MPa)
        self.epsilon_uk = reinf["epsuk"]  # Ultimate strain (‰)
        self.ftk = reinf["ftk"]  # Characteristic tensile strength (MPa)
        self.Es = reinf["Es"]  # Modulus of elasticity (MPa)
        self.ClassType = reinf["T"]  # 'A', 'B', or 'C'

        gamma_s = dbase.ReinforcementParams["gamma_s"]  # Partial safety factor
        self.fyd = round(self.fyk / gamma_s, 1)  # Design yield strength (MPa)


class SteelProfile:
    """Base class for Eurocode 3 steel profiles. Not implemented."""


class ProfileI(SteelProfile):
    """Eurocode 3 I-shaped steel profile. Not implemented."""


class ProfileH(SteelProfile):
    """Eurocode 3 H-shaped steel profile. Not implemented."""


class ProfileSHS(SteelProfile):
    """Eurocode 3 SHS (Square Hollow Section) steel profile. Not implemented."""
