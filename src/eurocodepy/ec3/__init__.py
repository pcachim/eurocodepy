# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 Steel Reinforcement Module.

This module provides classes and functions for Eurocode 3 steel reinforcement design.
It includes properties for different steel grades and types, as well as profile classes.
"""
from dataclasses import dataclass
from enum import Enum
import re

import numpy as np

from eurocodepy import dbase
from eurocodepy.ec3 import uls  # noqa: F401

"""
Eurocode 3 steel classes existing in the databse.
"""

def extract_steel(s):
    match = re.search(r'S\d+', s)
    return match.group(0) if match else None

MIN_E1: float = 1.2
MIN_E2: float = 1.2
MIN_P1: float = 2.2
MIN_P2: float = 2.4
REC_E1: float = 3.0
REC_E2: float = 1.5
REC_P1: float = 3.75
REC_P2: float = 3.0
MIN_E1_PIN: float = 1.6
MIN_E2_PIN: float = 1.25

class Bolt:
    """Represents a steel bolt according to Eurocode 3.

    Attributes:
        diameter (str | float): Bolt diameter designation (e.g., 'M16' or 16.0).
        grade (str): Bolt steel grade (e.g., '8.8').
        athread (float, optional): Area of the thread (cm^2). Defaults to None.
        dnut (float, optional): Diameter of the nut (mm). Defaults to None.
        name (str): Bolt diameter designation (e.g., 'M16').
        steel (str): Bolt steel grade (e.g., '8.8').
        d (float): Diameter of the bolt (mm).
        A (float): Area of the bolt (cm^2).
        Athread (float): Area of the thread (cm^2).
        fub (float): Characteristic ultimate strength (MPa).
        fyb (float): Characteristic yield strength (MPa).

    Methods:
        __str__(): Returns a string representation of the bolt properties.

        Raises:
            ValueError: If the grade or diameter is not found in the database.

    """

    def __init__(self, diameter: str | float | object, grade: str, athread = None, dnut = None) -> None:  # noqa: D107
        if grade.replace(".", "_") not in dbase.BoltGrades:
            msg = (
                f"Bolt grade '{grade}' not found in database. "
                f"Bolt grade must be one of {list(dbase.BoltGrades.keys())}"
            )
            raise ValueError(msg)

        if isinstance(diameter, float) or isinstance(diameter, int):
            self.name = f"U{diameter}"  # U = universal diameter
            self.d = diameter
            folga = 1 if diameter <= 12 else 2 if diameter <= 27 else 3
            self.d0 = diameter + folga
            self.dnut = dnut if dnut is not None else self.d0  # Optional nut diameter
            self.A = np.pi * diameter**2 / 4 / 100.0
            self.Athread = athread if athread is not None else self.A
        else:
            if diameter not in dbase.BoltDiameters:
                msg = (
                    f"Bolt diameter '{diameter}' not found in database. "
                    f"Bolt diameter must be one of {list(dbase.BoltDiameters.keys())}"
                )
                raise ValueError(msg)

            bolt = dbase.BoltDiameters[diameter]
            self.name = diameter
            self.d = bolt["d"]
            self.d0 = bolt["d0"]
            self.dnut = bolt.get("dnut", None)  # Optional nut diameter
            self.A = bolt["A"]
            self.Athread = bolt["Athread"]

        bolt_grade = dbase.BoltGrades[grade.replace(".", "_")]
        self.steel = grade.replace("_", ".").upper()
        self.fub = bolt_grade["fub"]
        self.fyb = bolt_grade["fyb"]
        self.gamma_M0 = dbase.SteelParams["gamma_M0"]  # Partial safety factor
        self.gamma_M1 = dbase.SteelParams["gamma_M1"]  # Partial safety factor
        self.gamma_M2 = dbase.SteelParams["gamma_M2"]  # Partial safety factor

    def __str__(self) -> str:
        """Return a string representation of the Bolt instance.

        Returns:
            str: A string describing the bolt properties.

        """
        return (
            f"Bolt Type: {self.name}\n"
            f"Bolt steel grade: {self.steel}\n"
            f"Characteristic Yield Strength (fyb): {self.fyb} MPa\n"
            f"Characteristic Ultimate Strength (fub): {self.fub} MPa\n"
            f"Diameter (d): {self.d} mm\n"
            f"Area of the bolt (A): {self.A} cm^2\n"
            f"Area of the thread (Athread): {self.Athread} cm^2\n"
        )

    @staticmethod
    def M20(grade: str = "8.8") -> "Bolt":
        """
        Convenience method to create a Bolt instance with M20 diameter.

        Args:
            grade (str): Bolt steel grade (e.g., '8.8', '10.9'). Defaults to '8.8'.

        Returns:
            Bolt: A Bolt instance with M20 diameter and the specified grade.
        """
        return Bolt("M20", grade)

    @staticmethod
    def M22(grade: str = "8.8") -> "Bolt":
        """
        Convenience method to create a Bolt instance with M22 diameter.

        Args:
            grade (str): Bolt steel grade (e.g., '8.8', '10.9'). Defaults to '8.8'.

        Returns:
            Bolt: A Bolt instance with M22 diameter and the specified grade.
        """
        return Bolt("M22", grade)

    @staticmethod
    def M24(grade: str = "8.8") -> "Bolt":
        """
        Convenience method to create a Bolt instance with M24 diameter.

        Args:
            grade (str): Bolt steel grade (e.g., '8.8', '10.9'). Defaults to '8.8'.

        Returns:
            Bolt: A Bolt instance with M24 diameter and the specified grade.
        """
        return Bolt("M24", grade)

    @staticmethod
    def M27(grade: str = "8.8") -> "Bolt":
        """
        Convenience method to create a Bolt instance with M27 diameter.

        Args:
            grade (str): Bolt steel grade (e.g., '8.8', '10.9'). Defaults to '8.8'.

        Returns:
            Bolt: A Bolt instance with M27 diameter and the specified grade.
        """
        return Bolt("M27", grade)

    def M30(grade: str = "8.8") -> "Bolt":
        """
        Convenience method to create a Bolt instance with M30 diameter.

        Args:
            grade (str): Bolt steel grade (e.g., '8.8', '10.9'). Defaults to '8.8'.

        Returns:
            Bolt: A Bolt instance with M30 diameter and the specified grade.
        """
        return Bolt("M30", grade)


BoltsEnum = Enum("BoltsEnum", {b: Bolt(b, "8_8") for b in dbase.BoltDiameters})  


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
        self.ClassType = type_label

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
            f"Partial Safety Factor (gamma_M1): {self.gamma_M1}\n"
            f"Partial Safety Factor (gamma_M2): {self.gamma_M2}\n"
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


SteelEnum = Enum("SteelEnum", {s: Steel(s) for s in dbase.SteelGrades})


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


@dataclass
class SteelPlate:
    """Represents a steel plate with specified thickness, width, and steel grade.

    Attributes
    ----------
    thickness : float
        Plate thickness in mm.
    width : float
        Plate width in mm.
    steel : ec.ec3.Steel
        Steel grade of the plate.

    """

    thickness: float
    steel: Steel
    width: float = 1000.0
    Length: float = 1000.0


class BoltedConnection:
    """Represents a bolted connection in a steel structure.

    Attributes
    ----------
    d0 : float
        Hole diameter (d0 = d + 1) in mm.
    e1 : float
        End distance (>= 1.2d0) in mm.
    p1 : float
        Spacing parallel to force (>= 2.2d0) in mm.
    e2 : float
        Edge distance (>= 1.2d0) in mm.
    p2 : float
        Spacing perpendicular to force (>= 2.4d0) in mm.
    n1 : int
        Number of bolts in parallel.
    n2 : int
        Number of bolts in series.
    steel_plate : SteelPlate
        Steel plate used in the connection.
    steel : ec.ec3.Steel
        Steel grade of the connection.
    bolt : ec.ec3.Bolt
        Bolt used in the connection.

    """

    _e1: float = 0.0  # end distance >= 1.2d0
    _p1: float = 0.0  # spacing parallel >= 2.2d0
    _e2: float = 0.0  # edge distance >= 1.5d0
    _p2: float = 0.0  # spacing perpendicular >= 2.5d0
    _n1: int = 1  # number of bolts in parallel
    _n2: int = 1  # number of bolts in series

    def __init__(self,
            bolt: Bolt,
            steel_plate: SteelPlate,
            steel_plate_b: SteelPlate | object = None) -> None:
        """Post-initialization to ensure the bolt is of type Bolt."""
        self._plate_a = steel_plate
        self._plate_b = steel_plate_b if steel_plate_b is not None else steel_plate
        self._bolt = bolt
        self._e1 = REC_E1 * self.bolt.d0
        self._p1 = REC_P2 * self.bolt.d0
        self._e2 = REC_E2 * self.bolt.d0
        self._p2 = REC_P2 * self.bolt.d0
        self._result = None

    @property
    def steel(self) -> Steel:
        """Returns the steel grade of the connection."""
        return self.steel_plate.steel

    @property
    def bolt(self) -> Bolt:
        """Returns the bolt used in the connection."""
        return self._bolt

    @property
    def d0(self) -> float:
        """Returns the hole diameter (d0 = d + 1) in mm."""
        return self.bolt.d0

    @property
    def e1(self) -> float:
        """Returns the end distance (>= 1.2d0) in mm."""
        return self._e1

    @e1.setter
    def e1(self, value: float) -> None:
        """Set the end distance (>= 1.2d0) in mm.

        Raises
        ------
        ValueError
            If the provided value is less than the minimum or exceeds the maximum allowed.

        """
        if value < MIN_E1 * self.d0:
            msg = f"End distance must be at least {MIN_E1} times the hole diameter ({self.d0})."
            raise ValueError(msg)
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        if value > 4.0 * t + 40:
            msg = f"End distance must not exceed 4 times the plate thickness ({t}) plus 40 mm."
            raise ValueError(msg)
        self._e1 = value

    @property
    def p1(self) -> float:
        """Returns the spacing parallel to force (>= 2.2d0) in mm."""
        return self._p1

    @p1.setter
    def p1(self, value: float) -> None:
        """Set the spacing parallel to force (>= 2.2d0) in mm.

        Raises
        ------
        ValueError
            If the provided value is less than the minimum or exceeds the maximum allowed.

        """
        if value < MIN_P1 * self.d0:
            msg = f"Spacing parallel to force must be at least {MIN_P1} times the hole diameter ({self.d0})."
            raise ValueError(msg)
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        if value > 14.0 * t or value > 200:  # noqa: PLR2004
            msg = (
                f"Spacing parallel to force must not exceed 14 "
                f"times the plate thickness ({t}) or 200 mm."
            )
            raise ValueError(msg)
        self._p1 = value

    @property
    def e2(self) -> float:
        """Returns the edge distance (>= 1.2d0) in mm."""
        return self._e2

    @e2.setter
    def e2(self, value: float) -> None:
        """Set the edge distance (>= 1.2d0) in mm.

        Raises
        ------
        ValueError
            If the provided value is less than the minimum or exceeds the maximum allowed.

        """
        if value < MIN_E2 * self.d0:
            msg = f"Edge distance must be at least {MIN_E2} times the hole diameter ({self.d0})."
            raise ValueError(msg)
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        if value > 4.0 * t + 40:
            msg = f"Edge distance must not exceed 4 times the plate thickness ({t}) plus 40 mm."
            raise ValueError(msg)
        self._e2 = value

    @property
    def p2(self) -> float:
        """Returns the spacing perpendicular to force (>= 2.5d0) in mm."""
        return self._p2

    @p2.setter
    def p2(self, value: float) -> None:
        """Set the spacing perpendicular to force (>= 2.5d0) in mm.

        Raises
        ------
        ValueError
            If the provided value is less than the minimum or exceeds the maximum allowed.

        """
        if value < MIN_P2 * self.d0:
            msg = f"Spacing perpendicular to force must be at least {MIN_P2} times the hole diameter ({self.d0})."
            raise ValueError(msg)
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        if value > 14.0 * t or value > 200:  # noqa: PLR2004
            msg = (
                f"Spacing perpendicular to force must not exceed 14 "
                f"times the plate thickness ({t}) or 200 mm."
            )
            raise ValueError(msg)
        self._p2 = value

    @property
    def steel_plate(self) -> SteelPlate:
        """Returns the steel plate used in the connection."""
        return self._plate_a

    @property
    def steel_plate_b(self) -> SteelPlate:
        """Returns the second steel plate used in the connection."""
        return self._plate_b

    @property
    def n1(self) -> int:
        """Returns the number of bolts in parallel."""
        return self._n1

    @n1.setter
    def n1(self, value: int) -> None:
        """Set the number of bolts in parallel."""  # noqa: DOC501
        if value < 1:
            msg = "Number of bolts in parallel must be at least 1."
            raise ValueError(msg)
        self._n1 = value

    @property
    def n2(self) -> int:
        """Returns the number of bolts in series."""
        return self._n2

    @n2.setter
    def n2(self, value: int) -> None:
        """Set the number of bolts in series."""  # noqa: DOC501
        if value < 1:
            msg = "Number of bolts in series must be at least 1."
            raise ValueError(msg)
        self._n2 = value

    @steel_plate.setter
    def steel_plate(self, value: SteelPlate) -> None:
        """Set the steel plate used in the connection."""
        self._plate_a = value

    @steel_plate_b.setter
    def steel_plate_b(self, value: SteelPlate) -> None:
        """Set the steel plate used in the connection."""
        self._plate_b = value

    def Fv_Rd(self, threaded: bool = True) -> float:
        """Return shear strength.

        Args:
            threaded (bool, optional): Shear occurs in threaded part. Defaults to True.

        Returns:
            float: shear strength

        """
        if threaded:
            alpha_v = 0.5 if self.bolt.steel in {"4.6", "5.6", "6.4"} else 0.6
            area = self.bolt.Athread
        else:
            alpha_v = 0.6
            area = self.bolt.A
        return np.round(alpha_v * self.bolt.fub * area / self.bolt.gamma_M2 / 10.0, 2)

    def Fb_Rd(self) -> float:  # noqa: N802
        """Return bearing strength.

        Args:
            thread (bool, optional): Shear occurs in thread. Defaults to True.

        Returns:
            float: bearing strength

        """
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        fu = self.steel_plate.steel.fuk

        ad = min(self.e1 / (3 * self.d0), self.p1 / (3 * self.d0) - 1.0 / 4.0)
        k1 = min(2.8 * self.e2 / self.d0 - 1.7, 1.4 * self.p2 / self.d0 - 1.7, 2.5)
        ab = min(ad, self.bolt.fub / fu, 1.0)

        return np.round(k1 * ab * fu * self.bolt.d * t / self.bolt.gamma_M2 / 1000.0, 2)

    def Ft_Rd(self, countersunk: bool = False) -> float:  # noqa: FBT001, FBT002, N802, PLR6301
        """Return tensile strength.

        Args:
            countersunk (bool, optional): Countersunk bolts. Defaults to False.

        Returns:
            float: tensile strength

        """
        k2 = 0.6 if countersunk else 0.9
        return np.round(k2 * self.bolt.fub * self.bolt.Athread / self.bolt.gamma_M2 / 10.0, 2)

    def Bp_Rd(self) -> float:
        """Return punching strength of the bolt.

        Returns:
            float: punching strength of the plate

        """
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        return np.round(0.6 * np.pi * self.bolt.dnut * self.steel_plate.steel.fuk *
                    t / self.bolt.gamma_M2 / 10.0, 2)

    def check(self, Fv_Ed: np.ndarray, Ft_Ed: np.ndarray,  # noqa: N803
                threaded: bool = True, countersunk: bool = False) -> dict:  # noqa: FBT001, FBT002
        """Perform design checks for the bolted connection.

        Parameters
        ----------
        Fv_Ed : np.ndarray
            Array of applied shear forces.
        Ft_Ed : np.ndarray
            Array of applied tensile forces.
        threaded : bool, optional
            Whether shear occurs in the threaded part of the bolt (default is True).
        countersunk : bool, optional
            Whether the bolts are countersunk (default is False).

        Returns
        -------
        dict
            Dictionary containing the results of the design checks.

        """
        self.Fv_Ed = Fv_Ed
        self.Fb_Ed = Fv_Ed
        self.Ft_Ed = Ft_Ed
        shear_ratio = np.round(self.Fv_Ed / self.Fv_Rd(), 2)
        shear_check = np.all(shear_ratio <= 1)
        bearing_ratio = np.round(self.Fv_Ed / self.Fb_Rd(), 2)
        bearing_check = np.all(bearing_ratio <= 1)
        tensile_ratio = np.round(self.Ft_Ed / self.Ft_Rd(), 2)
        tensile_check = np.all(tensile_ratio <= 1)
        punching_ratio = np.round(self.Ft_Ed / self.Bp_Rd(), 2)
        punching_check = np.all(punching_ratio <= 1)
        combined_ratio = np.round(self.Fv_Ed / self.Fv_Rd() + self.Ft_Ed / 1.4 / self.Ft_Rd(), 2)
        combined_check = np.all(combined_ratio <= 1)

        self._result = {
            "ShearRatios": shear_ratio,
            "ShearRatio": np.max(shear_ratio),
            "ShearCheck": shear_check,
            "BearingRatios": bearing_ratio,
            "BearingRatio": np.max(bearing_ratio),
            "BearingCheck": bearing_check,
            "TensileRatios": tensile_ratio,
            "TensileRatio": np.max(tensile_ratio),
            "TensileCheck": tensile_check,
            "PunchingRatios": punching_ratio,
            "PunchingRatio": np.max(punching_ratio),
            "PunchingCheck": punching_check,
            "CombinedRatios": combined_ratio,
            "CombinedRatio": np.max(combined_ratio),
            "CombinedCheck": combined_check,
            "Check": shear_check & bearing_check & tensile_check & combined_check,
        }

        return self._result

    def __str__(self) -> str:
        """Return a string representation of the bolted connection.

        Returns:
            str: String representation of the bolted connection.

        """
        s: str = (
            f"\nBOLTED CONNECTION\n"
            f"\nGeometry and materials: mm\n"
            f"End distance e1: {self.e1} mm\n"
            f"Spacing parallel p1: {self.p1} mm\n"
            f"Edge distance e2: {self.e2} mm\n"
            f"Spacing perpendicular p2: {self.p2} mm\n"
            f"Number of bolts in parallel n1: {self.n1}\n"
            f"Number of bolts in series n2: {self.n2}\n"
            f"Bolt diameter: {self.bolt.d} mm\n"
            f"Bolt grade: {self.bolt.fub}\n"
            f"Bolt area: {self.bolt.A} cm^2\n"
            f"Bolt area thread: {self.bolt.Athread} cm^2\n"
            f"Bolt hole diameter: {self.bolt.d0} mm\n"
            f"Bolt nut 'diameter': {self.bolt.dnut} mm\n"
            f"Steel plate A thickness: {self.steel_plate.thickness} mm\n"
            f"Steel plate A grade: {self.steel_plate.steel.ClassType}\n"
            f"Steel plate B thickness: {self.steel_plate_b.thickness} mm\n"
            f"Steel plate B grade: {self.steel_plate_b.steel.ClassType}\n"
            f"\nGeometry and materials:\n"
            f"Shear strength: {self.Fv_Rd(threaded=True)} kN\n"
            f"Bearing strength: {self.Fb_Rd()} kN\n"
            f"Tensile strength: {self.Ft_Rd()} kN\n"
            f"Punching strength: {self.Bp_Rd()} kN\n"
            f"\nDesign checks:\n"
        )

        if self._result is not None:
            t: str = (
            f"Shear ratios: {self._result['ShearRatios']}\n"
            f"Bearing ratios: {self._result['BearingRatios']}\n"
            f"Tensile ratios: {self._result['TensileRatios']}\n"
            f"Punching ratios: {self._result['PunchingRatios']}\n"
            f"Combined ratios: {self._result['CombinedRatios']}\n"
            f"Shear ratio: {self._result['ShearRatio']}\n"
            f"Bearing ratio: {self._result['BearingRatio']}\n"
            f"Tensile ratio: {self._result['TensileRatio']}\n"
            f"Punching ratio: {self._result['PunchingRatio']}\n"
            f"Combined ratio: {self._result['CombinedRatio']}\n"
            f"Shear check: {self._result['ShearCheck']}\n"
            f"Bearing check: {self._result['BearingCheck']}\n"
            f"Tensile check: {self._result['TensileCheck']}\n"
            f"Punching check: {self._result['PunchingCheck']}\n"
            f"Combined check: {self._result['CombinedCheck']}\n"
            f"Check: {self._result['Check']}")
        else:
            t: str = "WARNING: No results available. Run 'Check' method first."

        return s + t


class PinnedConnection(BoltedConnection):
    """Represents a pinned connection in a steel structure.

    Inherits from BoltedConnection and uses the same properties and methods.
    Plate A are the outer plates, plate B are the inner plate.

    """

    _g: float = 0.0  # gap between plates in mm
    _pin_type: str = "simple"

    def __init__(self,
            bolt: Bolt,
            steel_plate: SteelPlate,
            steel_plate_b: SteelPlate | object = None,
            gap: float = 0) -> None:
        """Post-initialization to ensure the bolt is of type Bolt."""
        super().__init__(bolt, steel_plate, steel_plate_b)
        self._g = gap  # default gap
        self._p1 = 0.0
        self._p2 = 0.0
        self._e1 = MIN_E1_PIN * self.bolt.d0
        self._e2 = MIN_E2_PIN * self.bolt.d0

    @property
    def g(self) -> float:
        """Returns the gap between plates in mm."""
        return self._g

    @g.setter
    def g(self, value: float) -> None:
        """Set the gap between plates in mm."""  # noqa: DOC501
        if value < 0:
            msg = "Gap between plates must be >= 0."
            raise ValueError(msg)
        self._g = value

    def Fv_Rd(self) -> float:
        """Return shear strength.

        Args:
            threaded (bool, optional): Shear occurs in threaded part. Defaults to True.

        Returns:
            float: shear strength

        """
        self._Fv_Rd = np.round(0.6 * self.bolt.fub * self.bolt.A / self.bolt.gamma_M2 / 10.0, 2)
        return self._Fv_Rd

    def Fb_Rd(self) -> tuple:  # noqa: N802
        """Return bearing strength.

        Args:
            thread (bool, optional): Shear occurs in thread. Defaults to True.

        Returns:
            float: 0.0

        """
        fy: float = min(self.steel_plate.steel.fyk, self.bolt.fyb)
        self._Fb_Rd_A = 1.5 * self.steel_plate.thickness * self.bolt.d * fy / self.bolt.gamma_M0 / 1000.0
        fy: float = min(self.steel_plate_b.steel.fyk, self.bolt.fyb)
        self._Fb_Rd_B = 1.5 * self.steel_plate_b.thickness * self.bolt.d * fy / self.bolt.gamma_M0 / 1000.0
        return (self._Fb_Rd_A, self._Fb_Rd_B)

    def M_Rd(self) -> float:
        """Return the moment resistant of the pin.

        Returns:
            float: resitant moment

        """
        w_ell = (self.bolt.d / 1000.0)**3 * np.pi / 32.0
        self._M_Rd = np.round(1.5 * self.bolt.fyb * 1000.0 * w_ell / self.bolt.gamma_M0, 2)
        return self._M_Rd

    def Ft_Rd(self) -> float:
        """Return tensile strength of the pin (0.0).

        Returns:
            float: 0.0

        """
        return 0.0

    def Bp_Rd(self) -> float:
        """Return punching strength of the pin (0.0).

        Returns:
            float: 0.0

        """
        return 0.0

    def check(self, F_Ed: np.ndarray) -> dict:  # noqa: N803
        """Check the design of the pinned connection.

        Returns:
            dict: Result of the design checks.

        """
        # Calculate design forces
        self.Fv_Ed = F_Ed / 2.0
        self.Fb_Ed_A = F_Ed / 2.0
        self.Fb_Ed_B = F_Ed
        self.M_Ed = F_Ed * (
            2.0 * self.steel_plate.thickness +
            self.steel_plate_b.thickness +
            4.0 * self.g
        ) / 8.0 / 1000.0
        # Perform checks on geometry
        t = min(self.steel_plate.thickness, self.steel_plate_b.thickness)
        fy = min(self.steel_plate.steel.fyk, self.bolt.fyb)
        e1_lim = F_Ed / 2.0 / t * self.bolt.gamma_M0 / fy + 7.0 * self.bolt.d0 / 6.0
        self._e1 = e1_lim
        e2_lim = F_Ed / 2.0 / t * self.bolt.gamma_M0 / fy + 5.0 * self.bolt.d0 / 6.0
        self._e2 = e2_lim
        # Perform checks on stresses
        shear_ratio = np.round(self.Fv_Ed / self.Fv_Rd(), 2)
        shear_check = np.all(shear_ratio < 1)
        moment_ratio = np.round(self.M_Ed / self.M_Rd(), 2)
        moment_check = np.all(moment_ratio <= 1)
        self.Fb_Rd()
        bearing_ratio_a = np.round(self.Fb_Ed_A / self._Fb_Rd_A, 2)
        bearing_check_a = np.all(bearing_ratio_a <= 1)
        bearing_ratio_b = np.round(self.Fb_Ed_B / self._Fb_Rd_B, 2)
        bearing_check_b = np.all(bearing_ratio_b <= 1)
        combined_ratio = np.round(
            (self.Fv_Ed / self._Fv_Rd)**2 + (self.M_Ed / self._M_Rd)**2, 2)
        combined_check = np.all(combined_ratio <= 1)

        self._result = {
            "ShearRatios": shear_ratio,
            "ShearRatio": np.max(shear_ratio),
            "ShearCheck": shear_check,
            "MomentRatios": moment_ratio,
            "MomentRatio": np.max(moment_ratio),
            "MomentCheck": moment_check,
            "BearingRatiosA": bearing_ratio_a,
            "BearingRatioA": np.max(bearing_ratio_a),
            "BearingCheckA": bearing_check_a,
            "BearingRatiosB": bearing_ratio_b,
            "BearingRatioB": np.max(bearing_ratio_b),
            "BearingCheckB": bearing_check_b,
            "CombinedRatios": combined_ratio,
            "CombinedRatio": np.max(combined_ratio),
            "CombinedCheck": combined_check,
            "Check": shear_check & bearing_check_a & bearing_check_b & combined_check,
        }

        return self._result

    def __str__(self) -> str:
        """Return a string representation of the bolted connection.

        Returns:
            str: String representation of the bolted connection.

        """

        base_text: str = (
                "\nPINNED CONNECTION (simple)\n"
                "Pinned connection with one central element and two side elements.\n"
            ) if self._pin_type == "simple" else (
                "\nPINNED CONNECTION (double)\n"
                "Pinned connection with two central elements and two side elements.\n"
            )

        geom_text: str = (
            f"\nGeometry and materials:\n"
            f"End distance e1: {self.e1}\n"
            f"Edge distance e2: {self.e2}\n"
            # f"Number of bolts in parallel n1: {self.n1}\n"
            # f"Number of bolts in series n2: {self.n2}\n"
            f"Pin diameter: {self.bolt.d} mm\n"
            f"Pin grade: {self.bolt.steel}\n"
            f"Pin area: {self.bolt.A:.2f} cm^2\n"
            f"Pin hole diameter: {self.bolt.d0} mm\n"
            f"Steel plate A thickness: {self.steel_plate.thickness} mm\n"
            f"Steel plate A grade: {self.steel_plate.steel.ClassType}\n"
            f"Steel plate B thickness: {self.steel_plate_b.thickness} mm\n"
            f"Steel plate B grade: {self.steel_plate_b.steel.ClassType}\n"
            f"\nStrength:\n"
            f"Shear strength: {self._Fv_Rd} kN\n"
            f"Moment strength: {self._M_Rd} kNm\n"
            f"Bearing strength (side): {self._Fb_Rd_A} kN\n"
            f"Bearing strength (centre): {self._Fb_Rd_B} kN\n"
            f"\nDesign checks:\n"
        )

        if self._result is not None:
            check_text: str = (
            f"Shear ratios: {self._result['ShearRatios']}\n"
            f"Moment ratios: {self._result['MomentRatios']}\n"
            f"Bearing ratios (side): {self._result['BearingRatiosA']}\n"
            f"Bearing ratios (centre): {self._result['BearingRatiosB']}\n"
            f"Combined ratios: {self._result['CombinedRatios']}\n"
            f"Shear ratio: {self._result['ShearRatio']}\n"
            f"Moment ratio: {self._result['MomentRatio']}\n"
            f"Bearing ratio (side): {self._result['BearingRatioA']}\n"
            f"Bearing ratio (centre): {self._result['BearingRatioB']}\n"
            f"Combined ratio: {self._result['CombinedRatio']}\n"
            f"Shear check: {self._result['ShearCheck']}\n"
            f"Moment check: {self._result['MomentCheck']}\n"
            f"Bearing check (side): {self._result['BearingCheckA']}\n"
            f"Bearing check (centre): {self._result['BearingCheckB']}\n"
            f"Combined check: {self._result['CombinedCheck']}\n"
            f"Check: {self._result['Check']}")
        else:
            check_text: str  = "WARNING: No results available. Run 'check' method first."

        return base_text + geom_text + check_text


class PinnedConnectionDouble(PinnedConnection):
    """Represents a double pinned connection in a steel structure.

    Inherits from PinnedConnection and uses the same properties and methods.
    Plate A are the outer plates, plate B are the inner plate.

    """

    _pin_type: str = "double"

    def __init__(self,
            bolt: Bolt,
            steel_plate: SteelPlate,
            steel_plate_b: SteelPlate | object = None,
            gap: float = 0) -> None:
        """Post-initialization to ensure the bolt is of type Bolt."""
        super().__init__(bolt, steel_plate, steel_plate_b, gap)

    def check(self, F_Ed: np.ndarray) -> dict:
        self.Fv_Ed = F_Ed / 2.0
        self.Fb_Ed_A = F_Ed / 2.0
        self.Fb_Ed_B = F_Ed / 2.0
        self.M_Ed = F_Ed * (
            2.0 * self.steel_plate.thickness +
            2.0 * self.steel_plate_b.thickness +
            4.0 * self.g
        ) / 8.0 / 1000.0
        shear_ratio = np.round(self.Fv_Ed / self.Fv_Rd(), 2)
        shear_check = np.all(shear_ratio <= 1)
        moment_ratio = np.round(self.M_Ed / self.M_Rd(), 2)
        moment_check = np.all(moment_ratio <= 1)
        self.Fb_Rd()
        bearing_ratio_a = np.round(self.Fb_Ed_A / self._Fb_Rd_A, 2)
        bearing_check_a = np.all(bearing_ratio_a <= 1)
        bearing_ratio_b = np.round(self.Fb_Ed_B / self._Fb_Rd_B, 2)
        bearing_check_b = np.all(bearing_ratio_b <= 1)
        combined_ratio = np.round(
            (self.Fv_Ed / self._Fv_Rd)**2 + (self.M_Ed / self._M_Rd)**2, 2)
        combined_check = np.all(combined_ratio <= 1)

        self._result = {
            "ShearRatios": shear_ratio,
            "ShearRatio": np.max(shear_ratio),
            "ShearCheck": shear_check,
            "MomentRatios": moment_ratio,
            "MomentRatio": np.max(moment_ratio),
            "MomentCheck": moment_check,
            "BearingRatiosA": bearing_ratio_a,
            "BearingRatioA": np.max(bearing_ratio_a),
            "BearingCheckA": bearing_check_a,
            "BearingRatiosB": bearing_ratio_b,
            "BearingRatioB": np.max(bearing_ratio_b),
            "BearingCheckB": bearing_check_b,
            "CombinedRatios": combined_ratio,
            "CombinedRatio": np.max(combined_ratio),
            "CombinedCheck": combined_check,
            "Check": shear_check & bearing_check_a & bearing_check_b & combined_check,
        }

        return self._result


class WeldTypeEnum(Enum):
    """Enumeration for weld types according to Eurocode 3."""
    SLIDE = 0
    SHEAR = 1
    NORMAL = 2
    SHEARNORMAL = 3
    SLIDENORMAL = 4
    SLIDESHEAR = 4
    SLINESHEARNORMAL = 5

@dataclass
class Weld:
    """Represents a weld according to Eurocode 3.

    Attributes:
        a (float): Weld width (mm).
        length (float): Weld length (mm).
        grade (str): Weld grade (e.g., 'A', 'B', etc.).
    """

    a: float
    length: float
    steel_grade: str
    x: float = 0.0
    y: float = 0.0
    orientation: float = 0.0
    weldtype: WeldTypeEnum = WeldTypeEnum.SLIDENORMAL
    x_max: float = 0.0
    y_max: float = 0.0
    x_min: float = 0.0
    y_min: float = 0.0
    cos: float = 1.0
    sin: float = 0.0
    xg: float = 0.0
    yg: float = 0.0

    def __post_init__(self):
        self.steel_grade = self.steel_grade.upper()
        if self.steel_grade not in dbase.SteelGrades:
            msg = (
                f"Weld grade '{self.steel_grade}' not found in database. "
                f"Weld grade must be one of {list(dbase.SteelGrades.keys())}"
            )
            raise ValueError(msg)

        steel = dbase.SteelGrades[self.steel_grade]
        self.fu = steel["fuk"]
        self.fy = steel["fyk"]
        grade = extract_steel(self.steel_grade)
        self.beta_w = 0.8 if grade == "S235" else 0.85 if grade == "S275" else 0.9 if grade == "S355" else 1.00
        self.gamma_M0 = dbase.SteelParams["gamma_M0"]  # Partial safety factor
        self.gamma_M1 = dbase.SteelParams["gamma_M1"]  # Partial safety factor
        self.gamma_M2 = dbase.SteelParams["gamma_M2"]  # Partial safety factor
        self.fv_wd = self.fu / (np.sqrt(3.0) * self.gamma_M2 * self.beta_w)
        # Fillet width for shear full strength (should be mukltiplied by t)
        self.a_full_shear = 0.7 * self.fy / self.gamma_M0 / self.fv_wd  
        # Fillet width for tension full strength (should be mukltiplied by t)
        self.a_full_tension = 0.5 * self.fy / self.gamma_M0 / self.fv_wd
        self.fw_vrd = self.fu / self.gamma_M2 / self.beta_w
        self.fw_trd = 0.9 * self.fu / self.gamma_M2

        self.cos = np.cos(self.orientation)
        self.sin = np.sin(self.orientation)
        self.x_max = self.x + 0.5 * self.length * self.cos
        self.y_max = self.y + 0.5 * self.length * self.sin
        self.x_min = self.x - 0.5 * self.length * self.cos
        self.y_min = self.y - 0.5 * self.length * self.sin
        i_xx = (self.a**3 * self.length) / 12.0
        i_yy = (self.a * self.length**3) / 12.0
        i_xy = 0.5 * (i_xx + i_yy)
        i_yx = 0.5 * (i_xx - i_yy)
        cos_2a = np.cos(2 * self.orientation)
        sin_2a = np.sin(2 * self.orientation)
        self.inertia_xx = i_xy + i_yx * cos_2a
        self.inertia_yy = i_xy - i_yx * cos_2a
        self.inertia_xy = i_yx * sin_2a
        self.area = self.a * self.length
        self.area_xx = self.area * np.round(self.cos**2, 2)
        self.area_yy = self.area * np.round(self.sin**2, 2)


    def __repr__(self):
        return f"Weld(a='{self.a}', length={self.length}, steel grade='{self.steel_grade}')"


class WeldConnection:

    inertia_xx = 0.0
    inertia_yy = 0.0
    inertia_xy = 0.0
    area_xx = 0.0
    area_yy = 0.0
    area = 0.0
    max_x = -np.inf
    max_y = -np.inf
    min_x = np.inf
    min_y = np.inf  

    def __init__(self, welds: list | None = None):
        self.welds = welds if welds is not None else []

    def add(self, weld: Weld):
        self.__update_weld(weld)
        self.welds.append(weld)

    def __update_weld(self, weld: Weld) -> None:
        self.inertia_xx += weld.inertia_xx
        self.inertia_yy += weld.inertia_yy
        self.inertia_xy += weld.inertia_xy
        self.area_xx += weld.area_xx
        self.area_yy += weld.area_yy
        self.area += weld.area
        if weld.x_max > self.max_x:
            self.max_x = weld.x_max
        if weld.y_max > self.max_y:
            self.max_y = weld.y_max
        if weld.x_min < self.min_x:
            self.min_x = weld.x_min
        if weld.y_min < self.min_y:
            self.min_y = weld.y_min
        self.w_el_xx_sup = self.inertia_xx / self.max_x
        self.w_el_yy_sup = self.inertia_yy / self.max_y
        self.w_el_xx_inf = np.abs(self.inertia_xx / self.min_x)
        self.w_el_yy_inf = np.abs(self.inertia_yy / self.min_y)

    def total_length(self):
        return sum(weld.length for weld in self.welds)

    def __len__(self):
        return len(self.welds)

    def __iter__(self):
        return iter(self.welds)

    def __repr__(self):
        return f"WeldConnection({self.welds})"


