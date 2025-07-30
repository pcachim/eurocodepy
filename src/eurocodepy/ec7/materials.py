# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

import numpy as np

from eurocodepy import dbase


@dataclass
class SoilSafetyFactors:
    """Soil safety factors for geotechnical design.

    Attributes:
        name (str): name of the soil safety factor set ("STR/GEO", "EQU", "ACC STR/GEO")
        casetype (str): type of case (e.g., "SLS", "ULS", "ACC")
        case (str): specific case description (e.g., "STR/GEO", "EQU", "ACC")
        gamma (float): partial safety factor for weight
        phi (float): partial safety factor for angle of internal friction
        c (float): partial safety factor for effective cohesion
        cu (float): partial safety factor for undrained shear strength
        perm_unfav (float): unfavourable permanent load factor
        perm_fav (float): favourable permanent load factor
        var_unfav (float): unfavourable variable load factor
        var_fav (float): favourable variable load factor
        slide (float): sliding resistance factor
        bearing (float): bearing resistance factor

    """

    name: str
    casetype: str
    case: str
    gamma: float
    phi: float
    c: float
    cu: float
    perm_unfav: float
    perm_fav: float
    var_unfav: float
    var_fav: float
    slide: float
    bearing: float


class SoilSafetyFactorsEnum:
    """Enum for soil safety factors based on Eurocode 7."""

    STRGEO_SLS = SoilSafetyFactors("STR/GEO", "SLS", "STR/GEO",
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)
    STRGEO_A1 = SoilSafetyFactors("STR/GEO A1", "ULS", "STR/GEO",
        1.0, 1.0, 1.0, 1.0, 1.35, 1.0, 1.5, 0.0, 1.0, 1.0)
    STRGEO_A2 = SoilSafetyFactors("STR/GEO A2", "ULS", "STR/GEO",
        1.0, 1.25, 1.25, 1.4, 1.0, 1.0, 1.3, 0.0, 1.0, 1.0)
    STRGEO_B = SoilSafetyFactors("STR/GEO B", "ULS", "STR/GEO",
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 0.0, 1.1, 1.4)
    STRGEO_C = SoilSafetyFactors("STR/GEO C", "ULS", "STR/GEO",
        1.0, 1.25, 1.25, 1.4, 1.0, 1.0, 1.5, 0.0, 1.0, 1.0)
    STRGEO_ACC = SoilSafetyFactors("ACC STR/GEO", "ACC", "STR/GEO",
        1.0, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)
    EQU = SoilSafetyFactors("EQU", "ULS", "EQU",
        1.0, 1.25, 1.25, 1.4, 1.1, 0.9, 1.5, 0.0, 1.0, 1.0)
    EQU_ACC = SoilSafetyFactors("ACC EQU", "ACC", "EQU",
        1.0, 1.0, 1.0, 1.25, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)


@dataclass
class Soil:
    """Soil class to hold soil properties for geotechnical calculations.

    Attributes:
        unit_weight (float): Unit weight of the soil in kN/m³.
        friction_angle (float): Effective angle of internal friction in degrees
        (converted to radians).
        conc_friction_angle (float): Angle of soil/concrete friction in degrees
        (converted to radians).
        sig_adm (float): Admissible stress in kPa. Defaults to 200 kPa.
        c (int or numpy.ndarray): effective cohesion. Defaults to 0.
        drained (bool, optional): drained or undrained conditions.
        if undrained c = cu. Defaults to True.

    """

    name: str = "Soil"
    unit_weight: float = 18.0  # Unit weight in kN/m³, default is 18 kN/m³
    friction_angle: float = 30.0  # Input in degrees, default is 30 degrees
    conc_friction_angle: float = 20.0  # Input in degrees, default is 20 degrees
    sig_adm: float = 200.0  # Admissible stress in kPa, default is 200 kPa
    sig_rd: float = 300.0  # Maximum design resistance stress in kPa, default is 300 kPa
    cohesion: float = 0.0  # Effective cohesion in kPa, default is 0
    is_drained: bool = True  # Drained condition, default is True
    is_coherent: bool = False  # Whether the soil is cohesive, default is False
    young: float = 30.0  # Young modulus in MPa
    poiss: float = 0.3  # Poisson coefficient
    ks: float = 30000  # modulus of subgrade reaction kN/m3

    def __post_init__(self) -> None:
        self.friction_angle = np.radians(self.friction_angle)
        self.conc_friction_angle = np.radians(self.conc_friction_angle)
        if self.cohesion > 0:
            self.is_coherent = True

    @staticmethod
    def get_es_from_spt(nspt: float) -> float:
        """Estimate Young's modulus (Es) from SPT value.

        Parameters
        ----------
        nspt : float
            Standard Penetration Test (SPT) value.

        Returns
        -------
        float
            Estimated Young's modulus (Es).

        """
        return nspt

    @staticmethod
    def get_sigadm_from_spt(nspt: float) -> float:
        """Estimate admissible stress from SPT (Standard Penetration Test) value.

        Parameters
        ----------
        nspt : float
            Standard Penetration Test (SPT) value.

        Returns
        -------
        float
            Estimated admissible stress in kPa.

        """
        return nspt

    @staticmethod
    def get_sigadm_from_cpt(nspt: float) -> float:
        """Estimate admissible stress from CPT (Cone Penetration Test) value.

        Parameters
        ----------
        nspt : float
            CPT value.

        Returns
        -------
        float
            Estimated admissible stress in kPa.

        """
        return nspt

    @staticmethod
    def get_ks_from_spt(nspt: float) -> float:
        """Estimate modulus of subgrade reaction (ks) from SPT value.

        Parameters
        ----------
        nspt : float
            Standard Penetration Test (SPT) value.

        Returns
        -------
        float
            Estimated modulus of subgrade reaction in kN/m³.

        """
        return nspt

    @staticmethod
    def get_ks_from_es(es: float) -> float:
        """Estimate modulus of subgrade reaction (ks) from Young's modulus (Es).

        Parameters
        ----------
        es : float
            Young's modulus in MPa.

        Returns
        -------
        float
            Estimated modulus of subgrade reaction in kN/m³.

        """
        return es


class SoilEnum:
    """Enumeration of typical soil types with predefined properties.

    Attributes:
        Sand (Soil): Typical sand soil properties.
        Clay (Soil): Typical clay soil properties.
        Gravel (Soil): Typical gravel soil properties.
        Rock (Soil): Typical rock soil properties.

    """

    Sand = Soil(name="Sand", unit_weight=18.0, friction_angle=30.0,
                conc_friction_angle=20.0, sig_adm=200.0, cohesion=0.0, is_drained=True)
    Clay = Soil(name="Clay", unit_weight=18.0, friction_angle=20.0,
                conc_friction_angle=15.0, sig_adm=200., cohesion=50.0, is_drained=False)
    Gravel = Soil(name="Gravel", unit_weight=20.0, friction_angle=35.0,
                conc_friction_angle=25.0, sig_adm=250.0, cohesion=0.0, is_drained=True)
    Rock = Soil(name="Rock", unit_weight=25.0, friction_angle=40.0,
                conc_friction_angle=30.0, sig_adm=500., cohesion=100.0, is_drained=True)


class SoilSeismicParameters:
    """Seismic parameters for soil based on Eurocode 8.

    Args:
        spectrum (str): name of the seismic spectrum (e.g., "PT1", "PT2", "CEN1", ...)
        agR (float): ground acceleration in m/s²
        s_max (float): maximum spectral acceleration
        importance_coeff (float): importance coefficient for the structure
        avg_ahg (float): ratio vertical/horizontal acceleration
        r (float, optional): response reduction factor. Defaults to 1.0.

    Notes:
        r=2.0 - Free gravity walls that can accept a displacement dr = 300 a⋅S (mm)
        r=1.5 - Free gravity walls that can accept a displacement dr = 200 a⋅S (mm)
        r=1.0 - Flexural reinforced concrete walls, anchored or braced walls, reinforced
        concrete walls founded on vertical piles, restrained basement walls and bridge
        abutments

    Attributes:
        name (str): name of the seismic spectrum
        r (float): response reduction factor
        agr (float): ground acceleration in m/s²
        s_max (float): Maximum spectral acceleration.
        alpha (float): normalized ground acceleration (ag / 9.80665)
        smax (float): maximum spectral acceleration
        importance_coeff (float): importance coefficient
        avg_ahg (float): ratio of vertical to horizontal acceleration
        kh (float): horizontal seismic coefficient
        kv (float): vertical seismic coefficient
        r (float, optional): Response reduction factor. Defaults to 1.0.

    """

    def __init__(self, name: str, agr: float, s_max: float,
                avg_ahg: float, r: float = 1.0) -> None:
        self.name = name
        self.r = r
        self._ag = agr
        self.smax = s_max
        self.avg_ahg = avg_ahg
        self.alpha = agr / 9.80665
        self._S = np.maximum(1, np.minimum(s_max, s_max - (s_max - 1) * (agr - 1) / 3))
        self._kh = self.alpha * self.smax / self.r
        self._kv = 0.5 * self.kh if self.avg_ahg > 0.6 else 0.33 * self._kh

    @property
    def kh(self) -> float:
        """Return the horizontal seismic coefficient (kh)."""
        return self._kh

    @property
    def kv(self) -> float:
        """Return the vertical seismic coefficient (kv)."""
        return self._kv

    @property
    def ag(self) -> float:
        """Return the ground acceleration (ag) in m/s²."""
        return self._ag

    @property
    def s(self) -> float:
        """Return the soil spectral scale factor (S)."""
        return self._S


def get_soil_seismic_parameters(name: str, code: str, soil: str, imp_class: str,
            spectrum: str, zone: str) -> SoilSeismicParameters:
    """Set the parameters for the seismic action 1 and 2.

    Args:
        name (str): name of the seismic action (e.g., "S1", "S2")
        code (str): country (EU, PT)
        soil (str): type of soil (A, B, C, D, E)
        imp_class (str): importance class (i, ii, iii, iv)
        spectrum (str): spectrum name (for PT: PT1, PT2, PTA)
                                    (for EU: CEN1, CEN2)
        zone (str): seismic zone 1 (for PT: 1_1, 1_2, 1_3, 2_4, 2_5, 2_6, ...)
                                    (for EU: _1g, _2g ...)
        r (float, optional): response reduction factor. Defaults to 1.0.

    Returns:
        SoilSeismicParameters: object containing seismic parameters

    Notes:
        r=2.0 - Free gravity walls that can accept a displacement dr = 300 a⋅S (mm)
    return SoilSeismicParameters(
        name=name,
        agR=ag,
        s_max=smax,
        importance_coeff=impcoef,
        avg_ahg=agvagh
    )
        r=1.0 - Flexural reinforced concrete walls, anchored or braced walls, reinforced
        concrete walls founded on vertical piles, restrained basement walls and bridge
        abutments

    """
    ag = dbase.Loads["Seismic"]["Locale"][code]["a_gR"][spectrum][zone]
    smax = dbase.Loads["Seismic"]["Locale"][code]["Spectrum"][spectrum][soil]["S_max"]
    impcoef = dbase.Loads["Seismic"]["Locale"][code]["ImportanceCoef"][spectrum][imp_class]
    agvagh = dbase.Loads["Seismic"]["Locale"][code]["avg_ahg"][spectrum]

    return SoilSeismicParameters(name, ag, smax, impcoef, agvagh)


@dataclass
class SoilSurcharge:
    """Soil surcharge load parameters.

    Attributes:
        q (float): surcharge load in kN/m²
        psi0 (float): coefficient for vertical stress at depth z=0
        psi1 (float): coefficient for vertical stress at depth z=1
        psi2 (float): coefficient for vertical stress at depth z=2

    """

    q: float = 10.0
    psi0: float = 0.6
    psi1: float = 0.4
    psi2: float = 0.2
