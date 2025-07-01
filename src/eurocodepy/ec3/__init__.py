# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 Steel Reinforcement Module.

This module provides classes and functions for Eurocode 3 steel reinforcement design.
It includes properties for different steel grades and types, as well as profile classes.
"""
from dataclasses import dataclass
from enum import Enum

import numpy as np

from eurocodepy import dbase
from eurocodepy.ec3 import uls  # noqa: F401

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
        if type_label not in dbase.SteelGrades:
            msg = (
                f"Steel type '{type_label}' not found in database. "
                f"Steel type must be one of {list(dbase.SteelGrades.keys())}"
            )
            raise ValueError(msg)

        reinf = dbase.SteelGrades[type_label]
        self.fyk = reinf["fyk"]  # Characteristic yield strength (MPa)
        self.fuk = reinf["fuk"]  # Characteristic ultimate strength (MPa)
        self.fyk40 = reinf["fyk40"]  # Characteristic yield strength for 40 mm bar (MPa)
        self.fuk40 = reinf["fuk40"]  # Charac. ultimate strength for 40 mm bar (MPa)
        self.Es = reinf["Es"]  # Modulus of elasticity (MPa)
        self.ClassType = ""

        gamma_s = dbase.SteelParams["gamma_M0"]  # Partial safety factor
        self.gamma_M0 = dbase.SteelParams["gamma_M0"]  # Partial safety factor
        self.gamma_M1 = dbase.SteelParams["gamma_M1"]  # Partial safety factor
        self.gamma_M2 = dbase.SteelParams["gamma_M2"]  # Partial safety factor
        self.fyd = round(self.fyk / gamma_s, 1)  # Design yield strength (MPa)
        self.fyd40 = round(self.fyk40 / gamma_s, 1)  # Design yield strength (MPa)

    def __str__(self) -> str:
        """Return a string representation of the Steel instance.

        Returns:
            str: A string describing the steel properties.

        """
        return (
            f"Steel Type: {self.fyk}\n"
            f"Characteristic Yield Strength (fyk): {self.fyk} MPa\n"
            f"Characteristic Ultimate Strength (fuk): {self.fuk} MPa\n"
            f"Design Yield Strength (fyd): {self.fyd} MPa\n"
            f"Modulus of Elasticity (Es): {self.Es} MPa\n"
            f"Partial Safety Factor (gamma_M0): {self.gamma_M0}\n"
        )

    def __repr__(self) -> str:
        """Return a string representation of the Steel instance for debugging.

        Returns:
            str: A string representation of the Steel instance.

        """
        return (
            f"Steel(type_label={self.fyk}, "
            f"fyk={self.fyk}, fuk={self.fuk}, "
            f"fyd={self.fyd}, Es={self.Es})"
        )


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
    r: float = 0.0  # Fillet radius, default is 0.0
    m: float = 0.0
    P: float = 0.0
    A: float = 0.0
    Av_z: float = 0.0
    Av_y: float = 0.0
    Iy: float = 0.0
    iy: float = 0.0
    Wel_y: float = 0.0
    Wpl_y: float = 0.0
    Iz: float = 0.0
    iz: float = 0.0
    Wel_z: float = 0.0
    Wpl_z: float = 0.0
    IT: float = 0.0
    WT: float = 0.0
    Iw: float = 0.0
    Ww: float = 0.0
    Npl_Rd: float = 0.0
    Vpl_Rd_z: float = 0.0
    Vpl_Rd_y: float = 0.0
    Mel_Rd_y: float = 0.0
    Mpl_Rd_y: float = 0.0
    Mel_Rd_z: float = 0.0
    Mpl_Rd_z: float = 0.0
    CurveA: str = "a"
    CurveB: str = "b"
    UserDefined: bool = False
    fyd: float = 235.0  # Design yield strength (MPa)

    def __post_init__(self) -> None:
        """Post-initialization to ensure the section type is set correctly.

        Raises:
            ValueError: If the section type is not 'I'.

        """
        if self.type != "I":
            msg = f"Invalid section type: {self.type}. Expected 'I'."
            raise ValueError(msg)

        if self.UserDefined:
            self._initialize_user_defined_properties()

    def _initialize_user_defined_properties(self) -> None:
        """Initialize properties for user-defined sections."""
        self.A = self.tf * self.b * 2 + (self.h - 2 * self.tf) * self.tw
        self.Av_z = self.tw * self.h
        self.Av_y = 2.0 * self.tf * self.b
        self.Iy = (self.b * self.h**3 - (self.tw * (self.h - 2 * self.tf)**3)) / 12.0
        self.Wel_y = self.Iy / (self.h / 2.0)
        self.Wpl_y = self.Iy / (self.h / 2.0)
        self.iy = np.sqrt(self.Iy / self.A)
        self.Iz = (
            (self.h * self.b**3) / 12.0 -
            (self.tf * (self.b - 2 * self.tw)**3) / 12.0)
        self.Wel_z = self.Iz / (self.b / 2.0)
        self.Wpl_z = self.Iz / (self.b / 2.0)
        self.iz = np.sqrt(self.Iz / self.A)
        self.IT = (
            (2.0 * self.hf**3 * self.b +
            self.tw**3 * (self.h - 2.0 * self.hf)) / 3.0
            )
        self.WT = 0.0
        self.Iw = (
            self.h**2 / 2.0 *
            (self.b**3 * self.tf / 12.0))
        self.Ww = 0.0
        self.Npl_Rd = self.A * 235.0 * 0.1
        self.Vpl_Rd_z = self.Av_z * 235.0 * 0.1
        self.Vpl_Rd_y = self.Av_y * 235.0 * 0.1
        self.Mel_Rd_y = self.Wel_y * 235.0 * 1.0e-3
        self.Mpl_Rd_y = self.Wpl_y * 235.0 * 1.0e-3
        self.Mel_Rd_z = self.Wel_z * 235.0 * 1.0e-3
        self.Mpl_Rd_z = self.Wpl_z * 235.0 * 1.0e-3

    def update_strength(self, fyd: float, gamma_M0: float = 1.0) -> None:  # noqa: D417, N803
        """Update the design strength based on a new yield strength.

        Args:
            fyk (float): New characteristic yield strength (MPa).
            gamma_M0 (float, optional): Partial safety factor for material strength.
            Defaults to 1.0.

        """
        conversion_factor: float = fyd / self.fyd / gamma_M0
        self.Npl_Rd *= conversion_factor
        self.Mel_Rd_y *= conversion_factor
        self.Mpl_Rd_y *= conversion_factor
        self.Mel_Rd_z *= conversion_factor
        self.Mpl_Rd_z *= conversion_factor
        self.Vpl_Rd_y *= conversion_factor
        self.Vpl_Rd_z *= conversion_factor
        self.fyd = fyd

    def __str__(self) -> str:
        """Return a string representation of the ProfileI instance.

        Returns:
            str: A string describing the ProfileI instance.

        """
        return (
            f"Geometry: {self.Section}\n"
            f"User Defined: {self.UserDefined}\n"
            f"Type: {self.type}\n"
            f"GEOMETRY:\n"
            f"Height (h): {self.h} cm\n"
            f"Width (b): {self.b} cm\n"
            f"Web thickness (tw): {self.tw} cm\n"
            f"Flange thickness (tf): {self.tf} cm\n"
            f"Fillet radius (r): {self.r} cm\n"
            f"PROPERTIES:\n"
            f"Mass per unit length (m): {self.m} kg/m\n"
            f"Perimeter (P): {self.P} m\n"
            f"Cross-sectional area (A): {self.A} cm²\n"
            f"Shear area in z-direction (Av_z): {self.Av_z} cm²\n"
            f"Shear area in y-direction (Av_y): {self.Av_y} cm²\n"
            f"Moment of inertia about y-axis (Iy): {self.Iy} cm⁴\n"
            f"Radius of gyration about y-axis (iy): {self.iy} cm\n"
            f"Elastic section modulus about y-axis (Wel_y): {self.Wel_y} cm³\n"
            f"Plastic section modulus about y-axis (Wpl_y): {self.Wpl_y} cm³\n"
            f"Moment of inertia about z-axis (Iz): {self.Iz} cm⁴\n"
            f"Radius of gyration about z-axis (iz): {self.iz} cm\n"
            f"Elastic section modulus about z-axis (Wel_z): {self.Wel_z} cm³\n"
            f"Plastic section modulus about z-axis (Wpl_z): {self.Wpl_z} cm³\n"
            f"Torsional moment of inertia (IT): {self.IT} cm⁴\n"
            f"Torsional section modulus (WT): {self.WT} cm³\n"
            f"Warping constant (Iw): {self.Iw} cm⁶\n"
            f"Warping section modulus (Ww): {self.Ww} cm³\n"
            f"STRENGTH:\n"
            f"Design yield strength (fyd): {self.fyd} MPa\n"
            f"Design axial strength (Npl_Rd): {self.Npl_Rd:.2f} kN\n"
            f"Design shear strength in z-direction (Vpl_Rd_z): {self.Vpl_Rd_z:.2f} kN\n"
            f"Design shear strength in y-direction (Vpl_Rd_y): {self.Vpl_Rd_y:.2f} kN\n"
            f"Design elastic moment about y-axis (Mel_Rd_y): {self.Mel_Rd_y:.2f} kNm\n"
            f"Design plastic moment about y-axis (Mpl_Rd_y): {self.Mpl_Rd_y:.2f} kNm\n"
            f"Design elastic moment about z-axis (Mel_Rd_z): {self.Mel_Rd_z:.2f} kNm\n"
            f"Design plastic moment about z-axis (Mpl_Rd_z): {self.Mpl_Rd_z:.2f} kNm\n"
            f"OTHER DATA:\n"
            f"Curve A: {self.CurveA}\n"
            f"Curve B: {self.CurveB}\n"
        )


@dataclass
class ProfileSHS(SteelSection):
    """SHS-shaped steel profile according to Eurocode 3.

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


@dataclass
class ProfileRHS(SteelSection):
    """RHS-shaped steel profile according to Eurocode 3.

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


@dataclass
class ProfileCHS(SteelSection):
    """CHS-shaped steel profile according to Eurocode 3.

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


def _parse_profiles_I() -> dict[str, ProfileI]:  # noqa: N802
    dados_raw = dbase.SteelIProfiles

    return {d["Section"]: ProfileI(type="I", **d) for d in dados_raw}


def _parse_profiles_SHS() -> dict[str, ProfileSHS]:  # noqa: N802
    dados_raw = dbase.SteelSHSProfiles

    return {d["Section"]: ProfileSHS(type="SHS", **d) for d in dados_raw}


def _parse_profiles_RHS() -> dict[str, ProfileRHS]:  # noqa: N802
    dados_raw = dbase.SteelRHSProfiles

    return {d["Section"]: ProfileRHS(type="RHS", **d) for d in dados_raw}


def _parse_profiles_CHS() -> dict[str, ProfileCHS]:  # noqa: N802
    dados_raw = dbase.SteelCHSProfiles

    return {d["Section"]: ProfileCHS(type="CHS", **d) for d in dados_raw}


ProfilesI = _parse_profiles_I()
"""Dictionary of Eurocode 3 I-shaped steel profiles."""
ProfilesSHS = _parse_profiles_SHS()
"""Dictionary of Eurocode 3 SHS-shaped steel profiles."""
ProfilesRHS = _parse_profiles_RHS()
"""Dictionary of Eurocode 3 RHS-shaped steel profiles."""
ProfilesCHS = _parse_profiles_CHS()
"""Dictionary of Eurocode 3 CHS-shaped steel profiles."""

ProfilesIEnum = Enum("ProfilesIEnum", ProfilesI)
ProfilesSHSEnum = Enum("ProfilesSHSEnum", ProfilesSHS)
ProfilesRHSEnum = Enum("ProfilesRHSEnum", ProfilesRHS)
ProfilesCHSEnum = Enum("ProfilesCHSEnum", ProfilesCHS)
