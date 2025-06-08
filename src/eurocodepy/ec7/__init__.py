"""Eurocode 7 - Geotechnical design module
This module provides functions and classes for geotechnical design according to Eurocode 7 (EN 1997-1:2004).
It includes calculations for bearing capacity, earth pressures, and other geotechnical parameters.
"""
import numpy as np
from dataclasses import dataclass

class SoilSafetyFactors():
    """Soil safety factors for geotechnical design
    Attributes:
        name (str): name of the soil safety factor set ("STR/GEO", "EQU", "ACC STR/GEO", ...)
        casetype (str): type of case (e.g., "SLS", "ULS", "ACC)
        case (str): specific case description (e.g., "STR/GEO", "EQU", "ACC")
        gamma (float): partial safety factor for weight
        phi (float): partial safety factor for angle of internal friction
        perm_unfav (float): unfavourable permanent load factor
        perm_fav (float): favourable permanent load factor
        var_unfav (float): unfavourable variable load factor
        var_fav (float): favourable variable load factor
        slide (float): sliding resistance factor
        bearing (float): bearing resistance factor
    """
    def  __init__(self, name, casetype, case, gamma, phi, perm_unfav, perm_fav, var_unfav, var_fav, slide, bearing):
        self.name = name
        self.casetype = casetype
        self.case = case
        self.gamma = gamma
        self.phi = phi
        self.perm_fav = perm_fav
        self.perm_unfav = perm_unfav
        self.var_fa = var_fav
        self.var_unfav = var_unfav
        self.slide = slide
        self.bearing = bearing

class Soil():
    """Soil class to hold soil properties for geotechnical calculations
    Attributes:
        unit_weight (float): unit weight of the soil in kN/m³
        phi (float): effective angle of internal friction in radians
        delta (float): angle of wall friction in radians
        sig_adm (float): admissible stress in kPa
    """
    def __init__(self, unit_weight, phi, delta, sig_adm):
        self.unit_weight = unit_weight
        self.phi = np.radians(phi)
        self.delta = np.radians(delta)
        self.sig_adm = sig_adm

class SoilSeismicParameters():
    """Seismic parameters for soil based on Eurocode 8

    Args:
        spectrum (str): name of the seismic spectrum (e.g., "PT1", "PT2", "CEN1", "CEN2")
        agR (float): ground acceleration in m/s²
        s_max (float): maximum spectral acceleration
        importance_coeff (float): importance coefficient for the structure
        avg_ahg (float): ratio vertical/horizontal acceleration
        r (float, optional): response reduction factor. Defaults to 1.0.
    
    Notes:
        r=2.0 - Free gravity walls that can accept a displacement up to dr = 300 α⋅S (mm)
        r=1.5 - Free gravity walls that can accept a displacement up to dr = 200 α⋅S (mm)
        r=1.0 - Flexural reinforced concrete walls, anchored or braced walls, reinforced
        concrete walls founded on vertical piles, restrained basement walls and bridge
        abutments

    Attributes:
        name (str): name of the seismic spectrum
        r (float): response reduction factor
        ag (float): ground acceleration in m/s²
        S (float): soil spectral scale factor
        alpha (float): normalized ground acceleration (ag / 9.80665)
        smax (float): maximum spectral acceleration
        importance_coeff (float): importance coefficient
        avg_ahg (float): ratio of vertical to horizontal acceleration
        kh (float): horizontal seismic coefficient
        kv (float): vertical seismic coefficient
    """
    def __init__(self, name, agR, s_max, importance_coeff, avg_ahg, r=1.0):
        self.name = name
        self.r = r
        self._ag = agR * importance_coeff
        self.smax = s_max
        self.importance_coeff = importance_coeff
        self.avg_ahg = avg_ahg
        self.alpha = agR / 9.80665
        self._S =  np.maximum(1,np.minimum(s_max,s_max-(s_max-1)*(agR * importance_coeff - 1)/3))
        self._kh = self.alpha * self.S / self.r
        self._kv = 0.5*self.kh if self.avg_ahg > 0.6 else 0.33*self._kh

    @property
    def kh(self):
        return self._kh
    
    @property
    def kv(self):
        return self._kv
    
    @property
    def ag(self):
        return self._ag
    
    @property
    def S(self):
        return self._S

def get_soil_seismic_parameters(name: str, code: str, soil: str, imp_class: str, 
            spectrum: str, zone: str, r: float=1.0) -> SoilSeismicParameters:
    """Sets the parameters for the seismic action 1 and 2

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
        r=2.0 - Free gravity walls that can accept a displacement up to dr = 300 α⋅S (mm)
        r=1.5 - Free gravity walls that can accept a displacement up to dr = 200 α⋅S (mm)
        r=1.0 - Flexural reinforced concrete walls, anchored or braced walls, reinforced
        concrete walls founded on vertical piles, restrained basement walls and bridge
        abutments
    """

    ag = db.Loads["Seismic"]["Locale"][code]["a_gR"][spectrum][zone]
    smax = db.Loads["Seismic"]["Locale"][code]["Spectrum"][spectrum][soil]["S_max"]
    impcoef = db.Loads["Seismic"]["Locale"][code]["ImportanceCoef"][spectrum][imp_class]
    agvagh = db.Loads["Seismic"]["Locale"][code]["avg_ahg"][spectrum]

    return SoilSeismicParameters(name, ag, smax, impcoef, agvagh)

@dataclass
class SoilSurcharge:
    """Soil surcharge load parameters
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

from .. import db
from .. import utils

from . import bearing_capacity
from .bearing_capacity import bearing_resistance
from .bearing_capacity import seismic_bearing_resistance

from . import earth_pressures
from .earth_pressures import rankine_coefficient
from .earth_pressures import coulomb_coefficient
from .earth_pressures import inrest_coefficient
from .earth_pressures import ec7_coefficient
from .earth_pressures import pressure_coefficients
from .earth_pressures import earthquake_coefficient

