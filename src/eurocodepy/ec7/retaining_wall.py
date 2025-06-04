"""
Concrete Retaining Wall Design Module using Eurocode 7

This module provides functions to design and verify reinforced concrete cantilever retaining walls
in accordance with the European standard EN 1997-1:2004 (Eurocode 7 - Geotechnical design - Part 1: General rules).

Main Features:

- Calculation of earth pressures using Rankine, Coulomb, and EC7 methods
- Overturning, sliding, and bearing capacity checks
- Reinforcement design for stem and base slab
- Stability verification under various load cases

References:

- EN 1997-1:2004 - Eurocode 7: Geotechnical design – Part 1: General rules
- EN 1992-1-1:2004 - Eurocode 2: Design of concrete structures
"""

from . import pressure_coefficients, bearing_resistance
from .. import ec2
from .. import db
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class SeismicParameters():
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

    ag = db["Loads"]["Seismic"]["Locale"][code]["a_gR"][spec][zone]
    smax = db["Loads"]["Seismic"]["Locale"][code]["Spectrum"][spec][soil]["S_max"]
    impcoef = db["Loads"]["Seismic"]["Locale"][code]["ImportanceCoef"][spec][imp_coef]
    agvagh = db["Loads"]["Seismic"]["Locale"][code]["avg_ahg"][spec]

    return SeismicParameters(spec, ag, smax, impcoef, agvagh)


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


seismic0 = SeismicParameters("None", 0.0, 0.0, 0.0, 0.0)
seismic1_1 = SeismicParameters("Tipo 1.1", 2.5, 1.0, 1.0, 0.75)
seismic1_2 = SeismicParameters("Tipo 1.2", 2.0, 1.0, 1.0, 0.75)
seismic1_5 = SeismicParameters("Tipo 1.5", 0.8, 1.0, 1.0, 0.75)
seismic1_6 = SeismicParameters("Tipo 1.6", 0.35, 1.0, 1.0, 0.75)
seismic2_1 = SeismicParameters("Tipo 2.1", 2.5, 1.0, 1.0, 0.95)
seismic2_2 = SeismicParameters("Tipo 2.2", 2.0, 1.0, 1.0, 0.95)
seismic2_5 = SeismicParameters("Tipo 2.5", 0.8, 1.0, 1.0, 0.95)

slsstrgeo = SoilSafetyFactors("STR/GEO", "SLS", "STR/GEO", 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)
strgeo1 = SoilSafetyFactors("STR/GEO 1", "ULS", "STR/GEO", 1.0, 1.0, 1.35, 1.0, 1.5, 0.0, 1.0, 1.0)
strgeo2 = SoilSafetyFactors("STR/GEO 2", "ULS", "STR/GEO", 1.0, 1.25, 1.0, 1.0, 1.3, 0.0, 1.0, 1.0)
equ = SoilSafetyFactors("EQU", "ULS", "EQU", 1.0, 1.25, 1.1, 0.9, 1.5, 0.0, 1.0, 1.0)
accequ = SoilSafetyFactors("ACC EQU", "ACC", "EQU", 1.0, 1.25, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)   
accstrgeo = SoilSafetyFactors("ACC STR/GEO", "ACC", "STR/GEO", 1.0, 1.1, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)   

backfill_soil = Soil(20.0, 30.0, 20.0, 300.0)
foundation_soil = Soil(20.0, 30.0, 20.0, 300.0)

surcharge = {    
    "q": 10.0,
    "psi0": 0.6,
    "psi1": 0.4,
    "psi2": 0.2
}


class RetainingWall():
    def __init__(self, height, width, beta=0.0, theta=0.0):
        self.height = height
        self.width = width
        self.beta = np.radians(beta)
        self.theta = np.radians(theta)

        self.overturn_ok = False
        self.slide_ok = False
        self.bearing_ok = False
        self.check = False
        self.as_stem = np.Infinity
        self.as_heel = np.Infinity
        self.as_toe = np.Infinity


class ConcreteCantiliverWall(RetainingWall):
    def __init__(self, height, width, front_toe, back_heel, beta, theta, foot_height, concrete, steel, c_cover, backfill_soil, 
                foundation_soil, surcharge, seismic_load_1=None, seismic_load_2=None, length=1000.0):
        super().__init__(height, width, beta, theta)
        self.foot_height = foot_height
        self.front_toe = front_toe
        self.back_heel = back_heel
        self.concrete = concrete
        self.steel = steel
        self.c_cover = c_cover
        self.backfill_soil = backfill_soil
        self.foundation_soil = foundation_soil
        self.surcharge = surcharge
        self.base = self.front_toe + self.back_heel + self.width
        self.length = length

        self._set_materials(concrete, steel)

        self.seismic_1 = seismic1_1 if seismic_load_1 is None else seismic_load_1
        self.seismic_2 = seismic2_1 if seismic_load_2 is None else seismic_load_2

        area1 = self.foot_height * self.base
        x1 = self.base / 2
        y1 = self.foot_height / 2
        area2 = self.height * self.width
        x2 = self.front_toe + self.width / 2
        y2 = self.foot_height + self.height / 2
        self.area = area1 + area2
        self.xG = (area1 * x1 + area2 * x2) / self.area
        self.yG = (area1 * y1 + area2 * y2) / self.area
        self.weight = self.area * self.c_weight

    def __str__(self):
        return self.write_results()

    def check_wall(self):
        self.results = []
        self.results += self.check_overturning(equ, None)
        self.results += self.check_overturning(accequ, self.seismic_1)
        self.results += self.check_overturning(accequ, self.seismic_2)
        self.results += self.check_sliding(strgeo1, None)
        self.results += self.check_sliding(strgeo2, None)
        self.results += self.check_sliding(accstrgeo, self.seismic_1)
        self.results += self.check_sliding(accstrgeo, self.seismic_2)
        self.results += self.check_bearing(strgeo1, None)
        self.results += self.check_bearing(strgeo2, None)
        self.results += self.check_bearing(accstrgeo, self.seismic_1)
        self.results += self.check_bearing(accstrgeo, self.seismic_2)

        self.check = True
        self.as_stem = 0.0
        self.as_heel = 0.0
        self.as_toe = 0.0
        for r in self.results:
            if not r["status"]:
                self.check = False
            if r["type"] == "bearing":
                if not r["design"]["vstem_status"] or not r["design"]["vheel_status"] or not r["design"]["vtoe_status"]:
                    self.check = False
                if r["design"]["as_stem"] > self.as_stem: self.as_stem = r["design"]["as_stem"]
                if r["design"]["as_heel"] > self.as_heel: self.as_heel = r["design"]["as_heel"]
                if r["design"]["as_toe"] > self.as_toe: self.as_toe = r["design"]["as_toe"]
        
        self.check_cracking(slsstrgeo)

        return self.results

    def write_results(self, filename: str=None):
        s = f"""
    Overall check of the wall:
        Stability check: {self.check}
        As stem = {self.as_stem:.2f} cm²/m (max space = {self.space_stem:.0f} mm)
        As heel = {self.as_heel:.2f} cm²/m (max space = {self.space_heel:.0f} mm)
        As toe = {self.as_toe:.2f} cm²/m (max space = {self.space_toe:.0f} mm)

    Wall dimensions:
        Height = {self.height:.2f} m
        Width = {self.width:.2f} m
        Front toe = {self.front_toe:.2f} m
        Back heel = {self.back_heel:.2f} m
        Footing height = {self.foot_height:.2f} m
        Base length = {self.base:.2f} m
        Total height = {self.height + self.foot_height:.2f} m
        Backfill slope angle (beta) = {np.degrees(self.beta):.1f}°

    Concrete parameters:
        Concrete class = {self.concrete}
        Concrete characteristic strength (fck) = {self.c_fck:.0f} MPa
        Concrete design strength (fcd) = {self.c_fcd:.1f} MPa
        Concrete unit weight = {self.c_weight:.1f} kN/m³
        Concrete mechanical cover = {self.c_cover*1000:.0f} mm
        
    Reinforcement parameters:
        Reinforcement class = {self.steel}
        Reinforcement characteristic strength (fyk) = {self.s_fyk:.0f} MPa
        Reinforcement design strength (fyd) = {self.s_fyd:.1f} MPa

    Backfill soil parameters:
        Unit weight = {self.backfill_soil.unit_weight:.1f} kN/m³
        Internal friction angle (phi) = {np.degrees(self.backfill_soil.phi):.1f}°
        Friction angle on footing base (delta) = {np.degrees(self.backfill_soil.delta):.1f}°
        Admissible bearing capacity (sigma_adm) = {self.backfill_soil.sig_adm:.0f} kPa

    Foundation soil parameters:
        Unit weight = {self.foundation_soil.unit_weight:.1f} kN/m³
        Internal friction angle (phi) = {np.degrees(self.foundation_soil.phi):.1f}°
        Friction angle on footing base (delta) = {np.degrees(self.foundation_soil.delta):.1f}°
        Admissible bearing capacity (sigma_adm) = {self.foundation_soil.sig_adm:.0f} kPa

    Seismic parameters:
        Seismic 1: {self.seismic_1.name}
            ag = {self.seismic_1.ag:.2f} m/s²
            S = {self.seismic_1.S:.2f}
            kh = {self.seismic_1.kh:.2f}
            kv = {self.seismic_1.kv:.2f}
        Seismic 2: {self.seismic_2.name}
            ag = {self.seismic_2.ag:.2f} m/s²
            S = {self.seismic_2.S:.2f}
            kh = {self.seismic_2.kh:.2f}
            kv = {self.seismic_2.kv:.2f}

    Weights: 
        Wall = {self.weight:.1f} kN/m
        Earth = {self.forces["weight"][0]:.1f} kN/m
        """

        for r in self.results:
            if r["type"] == "overturning":
                s += f'''
    Overturning stability check:
        safety = {r["safety"].case + "_" + r["safety"].casetype}
        seismic = {r["seismic"].name}
        direction = {r["direction"]} 
        M_stb = {r["med_stb"]:.1f} kNm/m
        M_dstb = {r["med_dstb"]:.1f} kNm/m
        SF = {r["med_stb"]/r["med_dstb"]:.2f}
        status = {r["status"]}
                    '''

            if r["type"] == "sliding":
                s += f'''
    Sliding stability check:
        safety = {r["safety"].case + "_" + r["safety"].casetype}
        seismic = {r["seismic"].name}
        direction = {r["direction"]} 
        F_stb = {r["fed_stb"]:.1f} kN/m
        F_dstb = {r["fed_dstb"]:.1f} kN/m
        SF = {r["fed_stb"]/r["fed_dstb"]:.2f}
        status = {r["status"]}
                '''

            if r["type"] == "bearing":
                s += f'''
    Bearing capacity check:
        safety = {r["safety"].case + "_" + r["safety"].casetype}
        seismic = {r["seismic"].name}
        direction = {r["direction"]}
        med = {r["med"]:.1f} kNm/m
        ned = {r["ned"]:.1f} kN/m
        exc = {r["exc"]:.2f} m
        sig_act = {r["sig_act"]:.0f} kPa
        sig_adm = {r["sig_adm"]:.0f} kPa
        SF = {r["sig_adm"]/r["sig_act"]:.2f}
        status = {r["status"]}

        Reinforcement bending design:
            stem:
                Med = {r["design"]["med_stem"]:.1f} kNm/m
                As = {r["design"]["as_stem"]:.2f} cm²/m
                Asmin = {r["design"]["asmin_stem"]:.2f} cm²/m
                Ved = {r["design"]["ved_stem"]:.1f} kN/m
                Vrd = {r["design"]["vrd_stem"]:.1f} kN/m
                status (V) = {r["design"]["vstem_status"]}
            heel: 
                Med = {r["design"]["med_heel"]:.1f} kNm/m
                As = {r["design"]["as_heel"]:.2f} cm²/m
                Asmin = {r["design"]["asmin_heel"]:.2f} cm²/m
                Ved = {r["design"]["ved_heel"]:.1f} kN/m
                Vrd = {r["design"]["vrd_heel"]:.1f} kN/m
                status (V) = {r["design"]["vheel_status"]}
            toe: 
                Med = {r["design"]["med_toe"]:.1f} kNm/m
                As = {r["design"]["as_toe"]:.2f} cm²/m
                Asmin = {r["design"]["asmin_heel"]:.2f} cm²/m
                Ved = {r["design"]["ved_toe"]:.1f} kN/m
                Vrd = {r["design"]["vrd_toe"]:.1f} kN/m
                status (V) = {r["design"]["vtoe_status"]}
            '''

        if filename is not None:
            # Open the file in write mode
            with open(filename, 'w') as file:
                file.write(s)
        return s

    def check_sliding(self, safety: SoilSafetyFactors, seismic: SeismicParameters = None) -> bool:
        self._earth_forces(safety, seismic)
        f = 0
        tan_delta_b = np.tan(self.foundation_soil.delta)/safety.phi
        if seismic is None:
            kv = 0.0
            kh = 0.0
        else:
            kv = seismic.kv
            kh = seismic.kh
        self.f_stb_asc = (self.weight + self.forces["weight"][f]) * (tan_delta_b * (1.0+kv) - kh)
        self.f_stb_dsc = (self.weight + self.forces["weight"][f]) * (tan_delta_b * (1.0-kv) - kh)

        delta = np.arctan(np.tan(self.backfill_soil.phi)/safety.phi)
        cos_delta = np.cos(delta)
        sin_delta = np.sin(delta)
        ka = self.forces["coef_back"][0]
        kas = self.forces["coef_back"][4]
        Ia = self.forces["impulse_back"][f] * (ka + kas)
        self.f_dstb_asc = Ia * (cos_delta - sin_delta * tan_delta_b) / safety.slide

        kas = self.forces["coef_back"][6]
        Ia = self.forces["impulse_back"][f] * (ka + kas)
        self.f_dstb_dsc = Ia * (cos_delta - sin_delta * tan_delta_b) / safety.slide
        
        self.slide_ok = True if self.f_stb_asc > self.f_dstb_asc and self.f_stb_dsc > self.f_dstb_dsc else False

        if seismic is None: seismic = seismic0
        
        results = [{
            "type": "sliding",
            "safety": safety,
            "seismic": seismic,
            "direction": "None",
            "fed_stb": self.f_stb_asc,
            "fed_dstb": self.f_dstb_asc,
            "status": self.overturn_ok
        }]

        if safety.casetype == "ACC":
            results[0]["direction"] = "asc"
            results.append({
                "type": "sliding",
                "safety": safety,
                "seismic": seismic,
                "direction": "dsc",
                "fed_stb": self.f_stb_dsc,
                "fed_dstb": self.f_dstb_dsc,
                "status": self.overturn_ok
            })

        return results

    def check_overturning(self, safety: SoilSafetyFactors, seismic: SeismicParameters = None) -> list:
        self._earth_forces(safety, seismic)
        f = 0
        x = 1
        y = 2

        if seismic is None:
            kv = 0.0
            kh = 0.0
        else:
            kv = seismic.kv
            kh = seismic.kh

        self.m_stb_asc = (1.0+kv)*(self.weight*self.xG + self.forces["weight"][f]*
            self.forces["weight"][x])-kh*(self.weight*self.yG + self.forces["weight"][f]*self.forces["weight"][y])
        self.m_stb_dsc = (1.0-kv)*(self.weight*self.xG + self.forces["weight"][f]*
            self.forces["weight"][x])-kh*(self.weight*self.yG + self.forces["weight"][f]*self.forces["weight"][y])

        delta = np.arctan(np.tan(self.backfill_soil.phi)/safety.phi)
        cos_delta = np.cos(delta)
        sin_delta = np.sin(delta)

        ka = self.forces["coef_back"][0]
        kas = self.forces["coef_back"][4]
        xa = self.forces["impulse_back"][x]
        ya = self.forces["impulse_back"][y]
        yas = self.forces["impulse_back"][y+1]
        Ia = self.forces["impulse_back"][f] * ka
        Ias = self.forces["impulse_back"][f] * kas     
        self.m_dstb_asc = (Ia * ya + Ias * yas) * cos_delta - (Ia  + Ias) * xa * sin_delta

        kas = self.forces["coef_back"][6]
        Ias = self.forces["impulse_back"][f] * kas
        self.m_dstb_dsc = (Ia * ya + Ias * yas) * cos_delta - (Ia  + Ias) * xa * sin_delta
        
        self.overturn_ok = True if self.m_stb_asc > self.m_dstb_asc and self.m_stb_dsc > self.m_dstb_dsc else False

        if seismic is None: seismic = seismic0
        
        results = [{
            "type": "overturning",
            "safety": safety,
            "seismic": seismic,
            "direction": "None",
            "med_stb": self.m_stb_asc,
            "med_dstb": self.m_dstb_asc,
            "status": self.overturn_ok
        }]

        if safety.casetype == "ACC":
            results[0]["direction"] = "asc"
            results.append({
                "type": "overturning",
                "safety": safety,
                "seismic": seismic,
                "direction": "dsc",
                "med_stb": self.m_stb_dsc,
                "med_dstb": self.m_dstb_dsc,
                "status": self.overturn_ok
            })

        return results

    def check_bearing(self, safety: SoilSafetyFactors, seismic: SeismicParameters = None) -> list:
        self._earth_forces(safety, seismic)
        f = 0
        x = 1
        y = 2
        if seismic is None:
            kv = 0.0
            kh = 0.0
            seismic = seismic0
        else:
            kv = seismic.kv
            kh = seismic.kh

        deltax = self.base/2.0

        Wg = self.weight
        xWg = deltax - self.xG
        yWg = self.yG
        Ws = self.forces["weight"][f]
        xWs = deltax - self.forces["weight"][x]
        yWs = self.forces["weight"][y]

        major = 1.0+kv
        minor = 1.0-kv
        ka = self.forces["coef_back"][0]
        kas = self.forces["coef_back"][4]
        xIa = deltax - self.forces["impulse_back"][x]
        ya = self.forces["impulse_back"][y]
        yas = self.forces["impulse_back"][y+1]
        Ia = self.forces["impulse_back"][f] * ka
        Ias = self.forces["impulse_back"][f] * kas

        delta = np.arctan(np.tan(self.backfill_soil.phi)/safety.phi)
        cos_delta = np.cos(delta)
        sin_delta = np.sin(delta)

        self.n_asc = major*(Wg + Ws) + (Ia  + Ias)*sin_delta
        self.m_asc = (Ia*ya+Ias*yas)*cos_delta + (Ia*xIa+Ias*xIa)*sin_delta + \
                    major*(Wg*xWg+Ws*xWs) + kh*(Wg*yWg + Ws*yWs)
        self.exc_asc = self.m_asc/self.n_asc
        self.sig_asc = self.n_asc/(self.base-2*self.exc_asc)
        
        B = self.base-2*self.exc_asc
        Hx = major*(Ia+Ias)+kh*(Wg+Ws)
        phi = self.foundation_soil.phi
        gamma = self.foundation_soil.unit_weight
        sig_adm = bearing_resistance(phi, gamma, gamma*self.foot_height, B, self.length, Hx, 0.0, self.n_asc) / safety.bearing
        # ????
        sig_adm = np.where(sig_adm < self.foundation_soil.sig_adm, self.foundation_soil.sig_adm, sig_adm)

        # self.bearing_ok = True if   self.sig_asc <= self.foundation_soil.sig_adm else False
        self.bearing_ok = True if   self.sig_asc <= sig_adm else False

        results = [{
            "type": "bearing",
            "safety": safety,
            "seismic": seismic,
            "direction": "None",
            "med": self.m_asc,
            "ned": self.n_asc,
            "exc": self.exc_asc,
            "sig_act": self.sig_asc,
            "sig_adm": sig_adm,
            "status": self.bearing_ok
        }]

        results[0]["design"] = self._check_bending_shear(major, self.forces["coef_stem"][4], safety.phi, results[0])

        if safety.casetype == "ACC":
            kas = self.forces["coef_back"][6]
            Ias = self.forces["impulse_back"][f] * kas

            self.n_dsc = minor*(self.weight + Ws) + (Ia  + Ias)*sin_delta
            self.m_dsc = (Ia*ya+Ias*yas)*cos_delta + (Ia*xIa+Ias*xIa)*sin_delta + \
                        minor*(Wg*xWg+Ws*xWs) + kh*(Wg*yWg + Ws*yWs)
            self.exc_dsc = self.m_dsc/self.n_dsc
            self.sig_dsc = self.n_dsc/(self.base-2*self.exc_dsc)

            B = self.base-2*self.exc_asc
            Hx = major*(Ia+Ias)+kh*(Wg+Ws)
            phi = self.foundation_soil.phi
            gamma = self.foundation_soil.unit_weight
            sig_adm = bearing_resistance(phi, gamma, gamma*self.foot_height, B, self.length, Hx, 0.0, self.n_dsc) / safety.bearing
            # ????
            sig_adm = np.where(sig_adm < self.foundation_soil.sig_adm, self.foundation_soil.sig_adm, sig_adm)

            results[0]["direction"] = "asc"
            results.append({
                "type": "bearing",
                "safety": safety,
                "seismic": seismic,
                "direction": "dsc",
                "med": self.m_dsc,
                "ned": self.n_dsc,
                "exc": self.exc_dsc,
                "sig_act": self.sig_dsc,
                "sig_adm": sig_adm,
                "status": self.bearing_ok
            })
            
            results[1]["design"] = self._check_bending_shear(minor, self.forces["coef_stem"][6], safety.phi, results[1])

            if self.sig_dsc > self.foundation_soil.sig_adm: 
                self.bearing_ok = False

        return results

    def _set_materials(self, concrete, steel):
        self.c_fck = db.ConcreteClasses[concrete]["fck"]
        self.c_fctm = db.ConcreteClasses[concrete]["fctm"]
        self.c_gc = db.ConcreteParams["gamma-cc"]
        self.c_weight = db.ConcreteParams["weigh"]
        self.c_fcd = round(self.c_fck / self.c_gc, 1)
        self.s_fyk = db.ReinforcementClasses[steel]["fyk"]
        self.s_gs = db.ReinforcementParams["gamma-s"]
        self.s_fyd = round(self.s_fyk / self.s_gs, 1)

    def _earth_forces(self, safety: SoilSafetyFactors, seismic = None):
        beta_height = self.back_heel * np.tan(self.beta)
        weight_soil = self.backfill_soil.unit_weight / safety.gamma

        # Calculate the weight of the backfill and their location
        w1 = self.height*self.back_heel
        w2 = self.back_heel*beta_height*0.5
        weight = w1 + w2
        weight_x = self.front_toe+self.width+self.back_heel*(0.5 * w1 + 2.0/3.0 * w2)/weight
        weight_y = self.foot_height + (self.height/2.0*w1 + (self.height+beta_height/3.0)*w2)/weight
        weight = weight_soil * weight

        # Calculate the active pressure coefficient on back of the stem 
        phi = np.arctan(np.tan(self.backfill_soil.phi)/safety.phi)
        delta = np.arctan(np.tan(self.backfill_soil.delta)/safety.phi)
        ka_stem = pressure_coefficients(phi, delta, self.theta, self.beta, seismic=seismic)

        # Calculate the force on back of the stem
        stem_force = 0.5 * weight_soil * self.height**2
        stem_force_x = self.front_toe + self.width
        stem_force_y = self.foot_height + self.height/3.0
        stem_force_ys = self.foot_height + self.height/2.0

        # Calculate the active pressure coefficient of the backfill
        phi = np.arctan(np.tan(self.backfill_soil.phi)/safety.phi)
        delta = phi
        ka_back = pressure_coefficients(phi, delta, self.theta, self.beta, seismic=seismic)

        # Calculate the force on the back of the footing
        back_height = self.height + self.foot_height + beta_height
        back_force =  0.5 * weight_soil * back_height**2
        back_force_x = self.base
        back_force_y = back_height/3.0
        back_force_ys = back_height/2.0

        self.forces = {"weight": [weight, weight_x, weight_y], 
                "impulse_back": [back_force, back_force_x, back_force_y, back_force_ys],
                "impulse_stem": [stem_force, stem_force_x, stem_force_y, stem_force_ys],
                "coef_back": ka_back,
                "coef_stem": ka_stem }

        return self.forces

    def _check_bending_shear(self, major: float, delta_kas: float, safetyphi: float, result: dict) -> list:
        f = 0
        x = 1
        y = 2

        delta = np.arctan(np.tan(self.backfill_soil.delta)/safetyphi)
        cos_delta = np.cos(delta)

        Wg = self.weight
        xWg = self.xG
        yWg = self.yG
        Ws = self.forces["weight"][f]
        xWs = self.forces["weight"][x]
        yWs = self.forces["weight"][y] - self.foot_height

        ka = self.forces["coef_stem"][0]
        kas = delta_kas
        yIa = self.forces["impulse_stem"][y] - self.foot_height
        yas = self.forces["impulse_stem"][y+1] - self.foot_height
        Ia = self.forces["impulse_stem"][f] * ka
        Ias = self.forces["impulse_stem"][f] * kas

        sigma = result["sig_act"]
        exct = result["exc"]
        b_heel = self.back_heel - 2.0*exct

        fcd = self.c_fcd
        fyd = self.s_fyd
        # fctm = self.c_fctm*1000.0
        # fyk = self.s_fyk*1000.0
    
        asmin = max(0.26*self.c_fctm/self.s_fyk, 0.0013)*10000
        dutil = self.width - self.c_cover
        asmin_stem = asmin * dutil

        ved_stem = (Ia+Ias)*cos_delta #+ kh*(Wg + Ws)
        med_stem = (Ia*yIa+Ias*yas)*cos_delta #+ kh*(Wg*yWg + Ws*yWs)
        as_stem = round(max(ec2.calc_asl(1.0, dutil, med_stem, fcd, fyd)[0], asmin_stem), 2)
        vrd_stem = ec2.calc_vrdc(1.0, dutil, self.c_fck, self.c_gc, as_stem/dutil/10000.0)[2]

        dutil = self.foot_height - self.c_cover
        asmin_heel =  asmin * dutil

        ved_heel = major*(Wg + Ws) - sigma*b_heel
        med_heel = Wg*(xWg-self.front_toe-self.width) + Ws*(xWs-self.front_toe-self.width) - sigma*b_heel**2/2.0
        as_heel = round(max(ec2.calc_asl(1.0, dutil, med_heel, fcd, fyd)[0], asmin_heel), 2)
        vrd_heel = ec2.calc_vrdc(1.0, dutil, self.c_fck, self.c_gc, as_heel/dutil/10000.0)[2]

        ved_toe = sigma*self.front_toe**2/2.0
        med_toe = sigma*self.front_toe
        as_toe = round(max(ec2.calc_asl(1.0, dutil, med_toe, fcd, fyd)[0], asmin_heel), 2)
        vrd_toe = ec2.calc_vrdc(1.0, dutil, self.c_fck, self.c_gc, as_toe/dutil/10000.0)[2]

        design = {
            "type": "bending",
            "as_min=:": asmin,
            "med_toe": med_toe,
            "as_toe": as_toe,
            "asmin_toe": asmin_heel,
            "ved_toe": ved_toe,
            "vrd_toe": vrd_toe,
            "vtoe_status": vrd_toe > ved_toe,
            "med_heel": med_heel,
            "as_heel": as_heel,
            "asmin_heel": asmin_heel,
            "ved_heel": ved_heel,
            "vrd_heel": vrd_heel,
            "vheel_status": vrd_heel > ved_heel,
            "med_stem": med_stem,
            "as_stem": as_stem,
            "asmin_stem": asmin_stem,
            "ved_stem": ved_stem,
            "vrd_stem": vrd_stem,
            "vstem_status": vrd_stem > ved_stem
        }

        return design

    def check_cracking(self, safety: SoilSafetyFactors) -> list:
        self._earth_forces(safety, None)
        f = 0
        x = 1
        y = 2

        deltax = self.base/2.0

        Wg = self.weight
        xWg = deltax - self.xG
        yWg = self.yG
        Ws = self.forces["weight"][f]
        xWs = deltax - self.forces["weight"][x]
        yWs = self.forces["weight"][y]

        ka = self.forces["coef_back"][0]
        kas = self.forces["coef_back"][4]
        xIa = deltax - self.forces["impulse_back"][x]
        ya = self.forces["impulse_back"][y]
        yas = self.forces["impulse_back"][y+1]
        Ia = self.forces["impulse_back"][f] * ka
        Ias = self.forces["impulse_back"][f] * kas

        delta = np.arctan(np.tan(self.backfill_soil.phi)/safety.phi)
        cos_delta = np.cos(delta)
        sin_delta = np.sin(delta)

        self.n_asc = (Wg + Ws) + (Ia  + Ias)*sin_delta
        self.m_asc = (Ia*ya+Ias*yas)*cos_delta + (Ia*xIa+Ias*xIa)*sin_delta + (Wg*xWg+Ws*xWs) 
        self.exc_asc = self.m_asc/self.n_asc
        self.sig_asc = self.n_asc/(self.base-2*self.exc_asc)

        delta = np.arctan(np.tan(self.backfill_soil.delta)/safety.phi)
        cos_delta = np.cos(delta)

        Wg = self.weight
        xWg = self.xG
        yWg = self.yG
        Ws = self.forces["weight"][f]
        xWs = self.forces["weight"][x]
        yWs = self.forces["weight"][y] - self.foot_height

        ka = self.forces["coef_stem"][0]
        kas = self.forces["coef_stem"][4]
        yIa = self.forces["impulse_stem"][y] - self.foot_height
        yas = self.forces["impulse_stem"][y+1] - self.foot_height
        Ia = self.forces["impulse_stem"][f] * ka
        Ias = self.forces["impulse_stem"][f] * kas

        sigma = self.sig_asc
        exct = self.exc_asc
        b_heel = self.back_heel - 2.0*exct

        dutil = self.width - self.c_cover
        med_stem = (Ia*yIa+Ias*yas)*cos_delta #+ kh*(Wg*yWg + Ws*yWs)
        as_stem = self.as_stem/10000.0
        sig_stem = med_stem/0.9/dutil/as_stem/1000.0

        dutil = self.foot_height - self.c_cover
        med_heel = Wg*(xWg-self.front_toe-self.width) + Ws*(xWs-self.front_toe-self.width) - sigma*b_heel**2/2.0
        as_heel = self.as_heel/10000.0
        sig_heel = med_heel/0.9/dutil/as_heel/1000.0

        med_toe = sigma*self.front_toe
        as_toe = self.as_toe/10000.0
        sig_toe = med_toe/0.9/dutil/as_toe/1000.0

        crack_stress = np.array([160.0, 200.0, 240.0, 280.0, 320.0, 360.0])
        crack_spaces = np.array([300.0, 250.0, 200.0, 150.0, 100.0,  50.0])
        self.space_stem = np.interp(np.array([sig_stem]), crack_stress, crack_spaces)[0]
        self.space_heel = np.interp(np.array([sig_heel]), crack_stress, crack_spaces)[0]
        self.space_toe = np.interp(np.array([sig_toe]), crack_stress, crack_spaces)[0]

        return


class ConcreteCounterfortWall(RetainingWall):
    pass


class GravityWall(RetainingWall):
    pass
