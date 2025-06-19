# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 Steel Reinforcement Module.

This module provides classes and functions for Eurocode 3 steel reinforcement design.
It includes properties for different steel grades and types, as well as profile classes.
"""
from dataclasses import dataclass
from enum import Enum

from eurocodepy import dbase
from eurocodepy.ec3 import uls

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


@dataclass
class SteelSection:
    """Represents a Eurocode 3 steel profile with geometric and mechanical properties.

    Attributes:
        type (str): Section type (e.g., 'I', 'L', 'T', etc.).

    """

    type: str        # 'IPE', 'HEA', etc.


@dataclass
class ProfileI(SteelSection):
    """I-shaped steel profile according to Eurocode 3.

    Args:
        SteelSection (SteelSection): geometric and mechanical properties of the section.

    """

    Section: str
    h: float
    b: float
    tw: float
    tf: float
    r: float
    m: float
    P: float
    A: float
    Av_z: float
    Av_y: float
    Iy: float
    iy: float
    Wel_y: float
    Wpl_y: float
    Iz: float
    iz: float
    Wel_z: float
    Wpl_z: float
    IT: float
    WT: float
    Iw: float
    Ww: float
    Npl_Rd: float
    Vpl_Rd_z: float
    Vpl_Rd_y: float
    Mel_Rd_y: float
    Mpl_Rd_y: float
    Mel_Rd_z: float
    Mpl_Rd_z: float
    CurveA: str
    CurveB: str


class ProfileH(SteelSection):
    """Eurocode 3 H-shaped steel profile. Not implemented."""


class ProfileSHS(SteelSection):
    """Eurocode 3 SHS (Square Hollow Section) steel profile. Not implemented."""


def _parse_profiles_I() -> dict[str, ProfileI]:  # noqa: N802
    dados_raw = dbase.SteelIProfiles

    return {d["Section"]: ProfileI(type="I", **d) for d in dados_raw}


ProfilesI = _parse_profiles_I()
"""Dictionary of Eurocode 3 I-shaped steel profiles."""
