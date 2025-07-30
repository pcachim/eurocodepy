# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from enum import Enum

import numpy as np

from eurocodepy import dbase

cemprops = {
    "Type S": [3, 0.13],
    "Type N": [4, 0.12],
    "Type R": [6, 0.11],
}

MAX_BUNDLE_BARS = 4
MIN_BUNDLE_BARS = 2
REF_FCK = 50.0
REF_FCM = 35.0


GammaC = dbase.ConcreteParams["gamma_cc"]
GammaCT = dbase.ConcreteParams["gamma_ct"]
ConcreteClass = Enum(
    "ConcreteClass",
    {item: item.replace("_", "/") for item in dbase.ConcreteGrades},
)
ReinforcementClass = Enum("ReinforcementClass", list(dbase.ReinforcementGrades.keys()))
GammaS = dbase.ReinforcementParams["gamma_s"]
PrestressClass = Enum("PrestressClass", list(dbase.PrestressGrades.keys()))
GammaP = dbase.PrestressParams["gamma_p"]


class Bar:
    """Represents a reinforcement bar with a given diameter and number of bars.

    Attributes
    ----------
    diameter : float
        Diameter of the bar.
    area : float
        Area of the bar cross-section.
    number : int
        Number of bars in the bundle.

    Methods
    -------
    total_area
        Returns the total area of all bars.

    """

    def __init__(self, diameter: float | str, n: int = 1) -> None:
        if isinstance(diameter, str):
            self.bar = dbase.ReinforcementBars[diameter]
            self.diameter = self.bar["d"]
            self.area = self.bar["A"]
        else:
            self.diameter = diameter
            self.area = round(np.pi * diameter**2 / 400.0, 2)

        self.number = n

    def total_area(self) -> float:
        """Return the total area of all bars in the bundle.

        Returns
        -------
        float
            The total area of all bars in the bundle.

        """
        return self.number * self.area

    def __eq__(self, other: object) -> bool:
        """Compara barras com base no diâmetro e área.

        Returns
        -------
        bool
            True se as barras têm o mesmo diâmetro, False caso contrário.

        """
        return (
            isinstance(other, Bar) and
            self.diameter == other.diameter
        )

    def __hash__(self) -> int:
        """Make Bar hashable based on diameter.

        Returns
        -------
        int
            Hash value based on the bar's diameter.

        """
        return hash(self.diameter)

    def __repr__(self) -> str:
        """Return a string representation of the Bar object.

        Returns
        -------
        str
            String representation of the Bar object.

        """
        return f"Bar(diameter={self.diameter}, area={self.area})"


class Bundle:
    """Represents a bundle of reinforcement bars for concrete design.

    Attributes
    ----------
    bars : list[Bar]
        List of Bar objects included in the bundle.
    diameter : float
        Equivalent diameter of the bundle.
    area : float
        Total area of all bars in the bundle.
    number : int
        Number of bundles.

    Methods
    -------
    total_area
        Returns the total area of all bars in the bundle.
    equiv_diameter
        Calculates and returns the equivalent diameter of the bundle.

    """

    def __init__(self, bars: list[Bar]) -> None:
        """Initialize a Bundle with a list of Bar objects.

        Args:
            bars (list[Bar]): List of Bar objects to be included in the bundle.

        Raises:
            ValueError: If the number of bars in the bundle is less than 2 or
                greater than 4.

        """
        if len(bars) > MAX_BUNDLE_BARS:
            msg = "Number of bars in a bundle must be less or equal 4"
            raise ValueError(msg)
        if len(bars) < MIN_BUNDLE_BARS:
            msg = "Number of bars in a bundle must be more than 1"
            raise ValueError(msg)
        self.bars = bars
        self.diameter = np.sqrt(sum(x.diameter**2 for x in bars))
        self.area = sum(bar.area for bar in self.bars)
        self.number = 1

    @property
    def total_area(self) -> float:
        """Return the total area of all bars in the bundle."""
        return self.number * self.area

    @property
    def equiv_diameter(self) -> float:
        """Calculate and return the equivalent diameter of the bundle of bars.

        Returns
        -------
        float
            The equivalent diameter calculated as the sum of squared
            diameters divided by the sum of diameters.

        """
        num = sum(bar.diameter**2 for bar in self.bars)
        den = sum(bar.diameter for bar in self.bars)
        return num / den


class BarLayout:
    """Manages a layout of reinforcement bars or bundles for concrete design.

    Attributes
    ----------
    bars : list[Bar]
        List of Bar objects representing the reinforcement layout.

    Methods
    -------
    add_bar(item: Union[Bar, Bundle], n: int = 1)
        Adds a bar or bundle of bars to the layout.
    total_area
        Returns the total area of all bars in the layout.
    diameter
        Returns the diameter (to be implemented).

    """

    def __init__(self, bars: list[Bar]) -> None:
        """Initialize a BarLayout with a list of Bar objects.

        Args:
            bars (list[Bar]): List of Bar objects representing the reinforcement layout.

        """
        self.bars = bars if bars is not None else []

    def add_bar(self, item: Bar | Bundle, n: int = 1) -> None:
        """Adiciona uma barra ou um bundle de barras ao layout.

        Args:
            item (Bar or Bundle): objeto Bar individual ou Bundle de barras.
            n (int): número de vezes que o item será adicionado
                (aplicado ao número de barras).

        Raises:
            TypeError: Se o item não for do tipo Bar ou Bundle.

        """
        if isinstance(item, Bar):
            self._add_or_merge_bar(item, n)
        elif isinstance(item, Bundle):
            for bar in item.bars:
                self._add_or_merge_bar(bar, n)
        else:
            msg = "Item deve ser do tipo Bar ou Bundle"
            raise TypeError(msg)

    def _add_or_merge_bar(self, bar: Bar, n: int) -> None:
        for existing_bar in self.bars:
            if existing_bar == bar:
                existing_bar.number += bar.number * n
                return
        # Não encontrou igual, adiciona nova entrada
        self.bars.append(Bar(bar.diameter, bar.number * n))

    @property
    def total_area(self) -> float:
        """Retorna a área total considerando todas as barras."""
        return sum(bar.area * bar.number for bar in self.bars)

    @property
    def diameter(self) -> float:
        """Returns the diameter (to be implemented)."""
        return self.diameter


BarSizes = dbase.ReinforcementBars.keys()


class Concrete:
    """Represents EC2 concrete properties and provides access to parameters.

    Attributes
    ----------
    grade : str
        The concrete grade (e.g., 'C30/37').
    name : str
        The normalized name of the concrete grade.
    fck : float
        Characteristic compressive strength (MPa).
    fcm : float
        Mean compressive strength (MPa).
    fctm : float
        Mean tensile strength (MPa).
    fctk_05 : float
        5% fractile tensile strength (MPa).
    fctk_95 : float
        95% fractile tensile strength (MPa).
    Ecm : float
        Modulus of elasticity (MPa).
    eps_c2 : float
        Strain at peak stress.
    eps_cu2 : float
        Ultimate compressive strain.
    n : float
        Parameter n for stress-strain curve.
    gamma_c : float
        Partial safety factor for concrete.
    fcd : float
        Design compressive strength (MPa).
    fctd : float
        Design tensile strength (MPa).

    Methods
    -------
    __repr__()
        Returns a string representation of the Concrete object.
    __str__()
        Returns a user-friendly string representation of the Concrete object.
    from_fck(f_ck: int, name: object = None)
        Class method to create a Concrete instance from characteristic
        compressive strength.

    """

    def __init__(self, class_name: str = "C30/37") -> None:
        self.grade = class_name

        class_name = class_name.replace("/", "_").upper()
        if class_name not in dbase.ConcreteGrades:
            grades_list = [item.replace("_", "/") for item in dbase.ConcreteGrades]
            msg = (
                f"Concrete class '{class_name}' not found in database. "
                f"Concrete type must be one of {grades_list}"
            )
            raise ValueError(msg)

        conc = dbase.ConcreteGrades[class_name]
        self.name = class_name
        self.fck = conc["fck"]  # MPa
        self.fcm = conc["fcm"]  # Mean compressive strength (MPa)
        self.fctm = conc["fctm"]  # Mean tensile strength (MPa)
        self.fctk_05 = conc["fctk05"] * self.fctm  # 5% fractile (MPa)
        self.fctk_95 = round(1.3 * self.fctm, 1)  # 95% fractile (MPa)
        self.Ecm = conc["Ecm"]  # Modulus of elasticity (MPa)
        self.eps_c2 = conc["epsc2"]  # Strain at peak stress
        self.eps_cu2 = conc["epscu2"]  # Ultimate compressive strain
        self.n = conc["n"]  # Ultimate compressive strain

        self.gamma_c = GammaC
        self.fcd = round(self.fck / GammaC, 1)  # Design yield strength (MPa)
        self.fctd = round(self.fctk_05 / GammaCT, 1)  # Design yield strength (MPa)

    def __repr__(self) -> str:
        """Return a string representation of the Concrete object.

        Returns
        -------
        str
            String representation of the Concrete object.

        """
        return (
            f"Concrete(grade='{self.grade}', fck={self.fck}, fcm={self.fcm}, "
            f"fctm={self.fctm}, fctk_05={self.fctk_05}, fctk_95={self.fctk_95}, "
            f"Ecm={self.Ecm}, eps_c2={self.eps_c2}, eps_cu2={self.eps_cu2}, "
            f"n={self.n}, fcd={self.fcd}, fctd={self.fctd})"
        )

    def __str__(self) -> str:
        """Return a string representation of the Concrete object.

        Returns
        -------
        str
            String representation of the Concrete object.

        """
        return (
            f"Concrete {self.grade} ("
            f"fck={self.fck} MPa, "
            f"fcm={self.fcm} MPa, "
            f"fctm={self.fctm} MPa, "
            f"fctk_05={self.fctk_05} MPa, "
            f"fctk_95={self.fctk_95} MPa, "
            f"Ecm={self.Ecm} MPa, "
            f"eps_c2={self.eps_c2}, "
            f"eps_cu2={self.eps_cu2}, "
            f"n={self.n}, "
            f"fcd={self.fcd} MPa, "
            f"fctd={self.fctd} MPa)"
        )

    @classmethod
    def from_fck(cls, f_ck: int, name: object = None) -> "Concrete":
        """Create a Concrete instance from characteristic compressive strength.

        Args:
            f_ck (int): Characteristic compressive strength of concrete (MPa)
            name (str, optional): Name for the concrete grade.

        Returns:
            Concrete: Concrete instance.

        """
        fck = float(f_ck)
        cls.fck = round(fck, 1)  # MPa
        cls.fcm = round(fck + 8, 1)  # Mean compressive strength (MPa)
        cls.fctm = round(0.30 * fck**(2 / 3), 1)  # Mean tensile strength (MPa)
        cls.fctk_005 = round(0.7 * cls.fctm, 1)  # 5% fractile
        cls.fctk_095 = round(1.3 * cls.fctm, 1)  # 95% fractile
        cls.Ecm = round(22000 * (cls.fcm / 10)**0.3, 1)  # Modulus of elasticity (MPa)
        cls.eps_c2 = 2.0 if fck <= REF_FCK else 2.0 + 0.085 * (fck - 50) ** 0.53
        # Strain at peak stress
        cls.eps_cu2 = (
            3.5 if fck <= REF_FCK
            else round(2.6 + 35 * ((90.0 - fck) / 100.0) ** 4, 1)
        )
        cls.n = (
            2.0
            if fck <= REF_FCK
            else round(1.4 + 23.4 * ((90.0 - fck) / 100.0) ** 4, 1)
        )
        if name is not None:
            cls.name = name
            cls.grade = name
        else:
            cls.name = f"C{f_ck}"
            cls.grade = f"C{f_ck}"

        cls.gamma_c = GammaC
        cls.fcd = round(cls.fck / GammaC, 1)  # Design yield strength (MPa)
        cls.fctd = round(cls.fctk_05 / GammaCT, 1)  # Design yield strength (MPa)

        return cls


class ConcreteGrade(Enum):
    """Enumeration of standard Eurocode 2 concrete grades.

    Each member represents a concrete grade with its associated properties.
    """

    C20_25 = Concrete("C20/25")
    C25_30 = Concrete("C25/30")
    C30_37 = Concrete("C30/37")
    C35_45 = Concrete("C35/45")
    C40_50 = Concrete("C40/50")
    C45_55 = Concrete("C45/55")
    C50_60 = Concrete("C50/60")
    C55_67 = Concrete("C55/67")
    C60_75 = Concrete("C60/75")
    C70_85 = Concrete("C70/85")
    C80_95 = Concrete("C80/95")
    C90_105 = Concrete("C90/105")


ConcreteGrades = {item.replace("_", "/"): Concrete(item.replace("_", "/"))
            for item in dbase.ConcreteGrades}


def get_concrete(concrete: str | Concrete | ConcreteGrade) -> Concrete:
    """Return a Concrete instance from a string, Concrete, or ConcreteGrade input.

    Parameters
    ----------
    concrete : str, Concrete, or ConcreteGrade
        The concrete specification as a string (e.g., 'C30/37'), a Concrete object,
        or a ConcreteGrade enum.

    Returns
    -------
    Concrete
        A Concrete instance corresponding to the input.

    Raises
    ------
    TypeError
        If the input is not a str, Concrete, or ConcreteGrade.

    """
    if isinstance(concrete, Concrete):
        return concrete
    if isinstance(concrete, ConcreteGrade):
        return concrete.value
    if isinstance(concrete, str):
        return Concrete(concrete)

    msg = "Input must be a str, Concrete, or ConcreteGrade"
    raise TypeError(msg)


class Reinforcement:
    """Represents Eurocode 2 steel reinforcement properties.

    Attributes
    ----------
    grade : str
        Steel type label (e.g., 'B500B', 'B500C').
    name : str
        Name of the reinforcement type.
    fyk : float
        Characteristic yield strength (MPa).
    epsilon_uk : float
        Ultimate strain (‰).
    ftk : float
        Characteristic tensile strength (MPa).
    Es : float
        Modulus of elasticity (MPa).
    ClassType : str
        Class type ('A', 'B', or 'C').
    gamma_s : float
        Partial safety factor for reinforcement.
    fyd : float
        Design yield strength (MPa).

    Methods
    -------
    __repr__()
        Returns a string representation of the Reinforcement object.
    __str__()
        Returns a user-friendly string representation of the Reinforcement object.

    """

    def __init__(self, type_label: str | ReinforcementClass = "B500B") -> None:
        if isinstance(type_label, ReinforcementClass):
            type_label = type_label.name
        self.grade = type_label
        self.name = type_label

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
        self.gamma_s = GammaS
        self.fyd = round(self.fyk / gamma_s, 1)  # Design yield strength (MPa)

    def __repr__(self) -> str:
        """Return a string representation of the Reinforcement object.

        Returns
        -------
        str
            String representation of the Reinforcement object.

        """
        return (
            f"Reinforcement(grade='{self.grade}', fyk={self.fyk}, "
            f"epsilon_uk={self.epsilon_uk}, ftk={self.ftk}, Es={self.Es}, "
            f"ClassType='{self.ClassType}', fyd={self.fyd})"
        )

    def __str__(self) -> str:
        """Return a string representation of the Reinforcement object.

        Returns
        -------
        str
            String representation of the Reinforcement object.

        """
        return (
            f"Reinforcement {self.grade} ("
            f"fyk={self.fyk} MPa, "
            f"epsilon_uk={self.epsilon_uk} ‰, "
            f"ftk={self.ftk} MPa, "
            f"Es={self.Es} MPa, "
            f"ClassType='{self.ClassType}', "
            f"fyd={self.fyd} MPa)"
        )


class ReinforcementGrade(Enum):
    """Enumeration of standard Eurocode 2 reinforcement steel grades.

    Each member represents a reinforcement grade with its associated properties.
    """

    A400NR = Reinforcement("A400NR")
    A500NR = Reinforcement("A500NR")
    A500EL = Reinforcement("A500EL")
    A400NRSD = Reinforcement("A400NRSD")
    A500NRSD = Reinforcement("A500NRSD")
    B400A = Reinforcement("B400A")
    B400B = Reinforcement("B400B")
    B400C = Reinforcement("B400C")
    B500A = Reinforcement("B500A")
    B500B = Reinforcement("B500B")
    B500C = Reinforcement("B500C")
    B600A = Reinforcement("B600A")
    B600B = Reinforcement("B600B")
    B600C = Reinforcement("B600C")
    B700A = Reinforcement("B700A")
    B700B = Reinforcement("B700B")
    B700C = Reinforcement("B700C")


ReinforcementGrades = {item: Reinforcement(item)
            for item in dbase.ReinforcementGrades}


def get_reinforcement(
    reinforcement: str | Reinforcement | ReinforcementGrade,
) -> Reinforcement:
    """Return a Reinforcement object from string, Reinforcement, or ReinforcementGrade.

    Parameters
    ----------
    reinforcement : str, Reinforcement, or ReinforcementGrade
        The reinforcement specification as a string (e.g., 'B500B'), a
        Reinforcement object, or a ReinforcementGrade enum.

    Returns
    -------
    Reinforcement
        A Reinforcement instance corresponding to the input.

    Raises
    ------
    TypeError
        If the input is not a str, Reinforcement, or ReinforcementGrade.

    """
    if isinstance(reinforcement, Reinforcement):
        return reinforcement
    if isinstance(reinforcement, ReinforcementGrade):
        return reinforcement.value
    if isinstance(reinforcement, str):
        return Reinforcement(reinforcement)

    msg = "Input must be a str, Reinforcement, or ReinforcementGrade"
    raise TypeError(msg)


class Prestress:
    """Represents Eurocode 2 prestressing steel properties.

    Attributes
    ----------
    name : str
        Name of the prestressing steel type.
    pType : str
        Type of prestressing steel ('strand', 'bar', or 'wire').
    zone : str
        Zone classification.
    fpk : float
        Characteristic prestress force (MPa).
    fp0_1k : float
        Characteristic prestress force at 0.1% strain (MPa).
    Ep : float
        Modulus of elasticity (MPa).
    d : float
        Diameter (mm).
    Ap : float
        Cross-sectional area (cm²).
    gamma_P : float
        Partial safety factor for prestressing steel.
    fpd : float
        Design yield strength (MPa).

    Methods
    -------
    __repr__()
        Returns a string representation of the Prestress object.
    __str__()
        Returns a user-friendly string representation of the Prestress object.

    """

    def __init__(self, type_label: str | PrestressClass = "Y1860S7 12.5") -> None:  # noqa: D107
        if isinstance(type_label, PrestressClass):
            class_name = type_label.name
            self.name = class_name.replace("_", " ", 1).replace("_", ".", 1)
        elif isinstance(type_label, str):
            self.name = type_label
            class_name = type_label.replace(" ", "_")
            class_name = class_name.replace(".", "_")
        else:
            msg = "type_label must be a string or PrestressClass enum"
            raise TypeError(msg)

        if class_name not in dbase.PrestressGrades:
            grades_list = [
                item.replace("_", " ", 1).replace("_", ".", 1)
                for item in dbase.PrestressGrades
            ]
            msg = (
                f"Prestress steel class '{class_name}' not found in database. "
                f"Prestress type must be one of {grades_list}"
            )
            raise ValueError(msg)

        reinf = dbase.PrestressGrades[class_name]
        self.pType = reinf["T"]  # 'strand', 'bar', or 'wire'
        self.zone = reinf["zone"]
        self.fpk = reinf["fpk"]  # Characteristic prestress force (MPa)
        # Characteristic prestress force at 0.1% strain (MPa)
        self.fp0_1k = reinf["fp0_1k"]
        self.Ep = reinf["Ep"]  # Modulus of elasticity (MPa)
        self.d = reinf["d"]  # Diameter (mm)
        self.Ap = reinf["Ap"]  # Cross-sectional area (cm²)

        gamma_p = dbase.PrestressParams["gamma_p"]  # Partial safety factor
        self.gamma_P = gamma_p
        self.fpd = round(self.fp0_1k / gamma_p, 0)  # Design yield strength (MPa)

    def __repr__(self) -> str:
        """Return a string representation of the Prestress object.

        Returns
        -------
        str
            String representation of the Prestress object.

        """
        return (
            f"Prestress(name='{self.name}', pType='{self.pType}', zone='{self.zone}', "
            f"fpk={self.fpk}, fp0_1k={self.fp0_1k}, Ep={self.Ep}, d={self.d}, "
            f"Ap={self.Ap}, fpd={self.fpd})"
        )

    def __str__(self) -> str:
        """Return a string representation of the Prestress object.

        Returns
        -------
        str
            String representation of the Prestress object.

        """
        return (
            f"Prestress {self.name} (pType='{self.pType}', zone='{self.zone}', "
            f"fpk={self.fpk} MPa, fp0_1k={self.fp0_1k} MPa, Ep={self.Ep} MPa, "
            f"d={self.d} mm, Ap={self.Ap} cm², fpd={self.fpd} MPa)"
        )


def beta_cc(t: float, s: float = 0.25) -> float:
    """Calculate the strength hardening coefficient.

    Args:
        t (float): time (days)
        s (float): cement type parameter. Optional, defaults to 0.25 (Type N cement)

        s = 0.20, fast hardening R: CEM42,5R, CEM52,5N e CEM52,5R
        s = 0.25, normal hardening N: CEM32,5R, CEM42,5N
        s = 0.38, slow hardening S: CEM32,5N

    Returns:
        float: strength hardening coefficient

    """
    return np.exp(s * (1 - np.sqrt(28.0 / t)))


def beta_ce(t: float, s: float = 0.25) -> float:
    """Calculate the modulus of elasticity hardening coefficient.

    Args:
        t (float): time (days)
        s (float): cement type parameter. Optional, defaults to 0.25 (Type N cement)

        s = 0.20, fast hardening R: CEM42,5R, CEM52,5N e CEM52,5R
        s = 0.25, normal hardening N: CEM32,5R, CEM42,5N
        s = 0.38, slow hardening S: CEM32,5N

    Returns:
        float: modulus of elasticity hardening coefficient

    """
    return (np.exp(s * (1 - np.sqrt(28.0 / t))))**0.3


@dataclass
class CreepParams:
    """Data class for storing parameters used in creep coefficient calculations.

    Attributes:
        t (int): Time in days.
        h0 (int): Effective height in mm.
        rh (int): Relative humidity in percent.
        t0 (int): Initial time in days.
        fck (float): Concrete compressive strength in MPa.
        cem (float): Cement parameter.

    """

    t: int = 1000000
    h0: int = 100
    rh: int = 65
    t0: int = 10
    fck: float = 20.0
    cem: float = 0.0


def _calc_fcm(fck: float) -> float:
    return fck + 8


def _calc_alphas(fcm: float) -> tuple:
    alpha1 = (35 / fcm)**0.7
    alpha2 = (35 / fcm)**0.2
    alpha3 = min(1.0, (3 / fcm)**0.5)
    return alpha1, alpha2, alpha3


def _calc_tt0(t0: float, cem: float) -> float:
    return t0 * ((1.0 + 9.0 / (2.0 + t0**1.2))**cem)


def _calc_phi_rh(rh: float, h0: float, fcm: float,
                alpha1: float, alpha2: float) -> float:
    phi_rh = (1.0 - rh / 100) / (0.1 * (h0**0.33333333))
    if fcm <= REF_FCM:
        return 1.0 + phi_rh
    return (1.0 + phi_rh * alpha1) * alpha2


def _calc_beta_fcm(fcm: float) -> float:
    return 16.8 / np.sqrt(fcm)


def _calc_beta_t0(tt0: float) -> float:
    return 1.0 / (0.1 + tt0**0.2)


def _calc_betah(alpha3: float, rh: float, h0: float) -> float:
    return min(
        1500 * alpha3,
        1.5 * (1.0 + np.power(0.012 * rh, 18)) * h0 + 250 * alpha3,
    )


def _calc_betacc(t: float, t0: float, betah: float) -> float:
    return np.power((t - t0) / (betah + t - t0), 0.3)


def calc_creep_coef(params: CreepParams) -> float:
    """Calculate the creep coefficient using EN1992-1:2004.

    This function calculates the creep coefficient of concrete based on the time,
    effective height, relative humidity, initial time, concrete compressive strength,
    and cement parameter. The creep coefficient is a measure of the time-dependent
    deformation of concrete under sustained load. It is calculated using the
    coefficients defined for different concrete compressive strengths and the effects
    of relative humidity and time.

    Args:
        params (CreepParams): Parameters for the creep coefficient calculation.

    Returns:
        float: the creep coeficient

    """
    t = params.t
    h0 = params.h0
    rh = params.rh
    t0 = params.t0
    fck = params.fck
    cem = params.cem

    fcm = _calc_fcm(fck)
    alpha1, alpha2, alpha3 = _calc_alphas(fcm)
    tt0 = _calc_tt0(t0, cem)
    phi_rh = _calc_phi_rh(rh, h0, fcm, alpha1, alpha2)
    beta_fcm = _calc_beta_fcm(fcm)
    beta_t0 = _calc_beta_t0(tt0)
    phi_0 = beta_fcm * beta_t0 * phi_rh

    try:
        betah = _calc_betah(alpha3, rh, h0)
        betacc = _calc_betacc(t, t0, betah)
        phi = betacc * phi_0
    except (ZeroDivisionError, ValueError, OverflowError):
        phi = 0.0

    return phi


@dataclass
class ShrinkStrainParams:
    """Data class for storing parameters used in shrinkage strain calculations.

    Attributes:
        t (int): Time in days.
        h0 (int): Effective height in mm.
        ts (int): Time of shrinkage start in days.
        rh (int): Relative humidity in percent.
        fck (float): Concrete compressive strength in MPa.
        cem (str): Cement type.

    """

    t: int = 1000000
    h0: int = 100
    ts: int = 3
    rh: int = 65
    fck: float = 20.0
    cem: str = "Type N"


def calc_shrink_strain(params: ShrinkStrainParams) -> float:
    """Calculate the total shrinkage strain. Uses EN1992-1:2004.

    This function calculates the total shrinkage strain of concrete based on the time,
    effective height, time of shrinkage start, relative humidity, concrete compressive
    strength, and cement type. The shrinkage strain is calculated using the coefficients
    defined for different cement types and the concrete compressive strength.

    Args:
        params (ShrinkStrainParams): Parameters for shrinkage strain calculation.

    Returns:
        float: the total shrinkage strain

    """
    t = params.t
    h0 = params.h0
    ts = params.ts
    rh = params.rh
    fck = params.fck
    cem = params.cem

    fcm = fck + 8
    alpha1 = cemprops[cem][0]
    alpha2 = cemprops[cem][1]

    eps_ca = 25.0e-6 * (fck - 10)
    beta_as = 1.0 - np.exp(-0.2 * (t**0.5))

    beta_rh = 1.55 * (1.0 - (rh / 100)**3)
    eps_cd = beta_rh * 0.85e-6 * ((220 + 110 * alpha1) * np.exp(-alpha2 * fcm / 10.0))
    beta_ds = (t - ts) / ((t - ts) + 0.4 * h0**1.5)

    return beta_as * eps_ca + beta_ds * eps_cd
