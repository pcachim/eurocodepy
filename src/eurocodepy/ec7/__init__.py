"""Eurocode 7 - Geotechnical design module
This module provides functions and classes for geotechnical design according to Eurocode 7 (EN 1997-1:2004).
It includes calculations for bearing capacity, earth pressures, and other geotechnical parameters.
"""
import numpy as np

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


class SoilSafetyFactors():
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
    def __init__(self, unit_weight, phi, delta, sig_adm):
        self.unit_weight = unit_weight
        self.phi = np.radians(phi)
        self.delta = np.radians(delta)
        self.sig_adm = sig_adm

class SoilSeismicParameters():
    def __init__(self, name, accel, s_max, importance_coeff, avg_ahg, r=1.0):
        self.name = name
        self.r = r
        self._ag = accel * importance_coeff
        self.smax = s_max
        self.importance_coeff = importance_coeff
        self.avg_ahg = avg_ahg
        self._S =  np.maximum(1,np.minimum(s_max,s_max-(s_max-1)*(accel * importance_coeff - 1)/3))
        self.alpha = accel / 9.80665
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

def set_seismic(code: str, soil: str, imp_coef: str, spec: str, zone: str):
    """Sets the parameters for the seismic action 1 and 2

    Args:
        code (str): country (EU, PT)
        soil (str): type of soil (A, B, C, D, E)
        imp_coef (str): importance coeficient (i, ii, iii, iv)
        spec1 (str): spectrum name (for PT: PT-1, PT-2, PT-A)
                                    (for EU: CEN-1, CECN-2)
        zone1 (str): seismic zone 1 (for PT: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6)
                                    (for EU: .1g, .2g ...)
    """

    ag = db.Loads["Seismic"]["Locale"][code]["a_gR"][spec][zone]
    smax = db.Loads["Seismic"]["Locale"][code]["Spectrum"][spec][soil]["S_max"]
    impcoef = db.Loads["Seismic"]["Locale"][code]["ImportanceCoef"][spec][imp_coef]
    agvagh = db.Loads["Seismic"]["Locale"][code]["avg_ahg"][spec]

    return SoilSeismicParameters(spec, ag, smax, impcoef, agvagh)

SoilSurchargeLoad = {    
    "q": 10.0,
    "psi0": 0.6,
    "psi1": 0.4,
    "psi2": 0.2
}

