"""Eurocode 2: Design of concrete structures.
This module provides classes and functions for Eurocode 2 concrete design.
It includes properties for different concrete grades and types, as well as calculations for serviceability and ultimate limit states.
"""
from enum import Enum
from typing import Union, List
import numpy as np
from .. import db

from .. import utils

gamma_C = db.ConcreteParams["gamma_cc"]
gamma_CT = db.ConcreteParams["gamma_ct"]
ConcreteClass = Enum("ConcreteClass", {item: item.replace("_", "/") for item in db.ConcreteGrades.keys()})
ReinforcementClass = Enum("ReinforcementClass", list(db.ReinforcementGrades.keys()))
gamma_S = db.ReinforcementParams["gamma_s"]
PrestressClass = Enum("PrestressClass", list(db.PrestressGrades.keys()))

class Bar:
    def __init__(self, diameter: float, number: int = 1):
        self.diameter = diameter
        self.area = np.round(np.pi * diameter**2 / 4.0, 2)
        self.number = number

    def __eq__(self, other):
        """Compara barras com base no diâmetro e área."""
        return (
            isinstance(other, Bar) and
            self.diameter == other.diameter
        )

    def __repr__(self):
        return f"Bar(diameter={self.diameter}, area={self.area})"

class Bundle:
    def __init__(self, bars: List[Bar]):
        if len(bars) > 4:
            raise ValueError("Number of bars in a bundle must be less or equal 4")
        self.bars = bars
        self.diameter = np.sqrt(sum(x**2 for x in bars))
        self.area = sum(bar.area for bar in self.bars)

class BarLayout:
    def __init__(self, bars: List[Bar] = None):
        self.bars = bars if bars is not None else []

    def add_bar(self, item: Union[Bar, Bundle], n: int = 1):
        """
        Adiciona uma barra ou um bundle de barras ao layout.
        
        Args:
            item (Bar or Bundle): objeto Bar individual ou Bundle de barras.
            n (int): número de vezes que o item será adicionado (aplicado ao número de barras).
        """
        if isinstance(item, Bar):
            self._add_or_merge_bar(item, n)
        elif isinstance(item, Bundle):
            for bar in item.bars:
                self._add_or_merge_bar(bar, n)
        else:
            raise TypeError("Item deve ser do tipo Bar ou Bundle")

    def _add_or_merge_bar(self, bar: Bar, n: int):
        for existing_bar in self.bars:
            if existing_bar == bar:
                existing_bar.number += bar.number * n
                return
        # Não encontrou igual, adiciona nova entrada
        self.bars.append(Bar(bar.diameter, bar.area, bar.number * n))

    def total_area(self) -> float:
        """Retorna a área total considerando todas as barras."""
        return sum(bar.area * bar.number for bar in self.bars)

class Concrete:
    def __init__(self, class_name: Union[str] = "C30/37"):
        """
        Eurocode 2 concrete properties.
        :param fck: Characteristic compressive strength of concrete (MPa)
        """
        if isinstance(class_name, ConcreteClass):
            self.grade = class_name.value
            class_name = class_name.value
        elif isinstance(class_name, str):
            self.grade = class_name
        else:
            raise TypeError("class_name must be a string or ConcreteClass enum")

        class_name = class_name.replace("/", "_").upper()
        if class_name not in db.ConcreteGrades.keys():
            grades_list = [item.replace("_", "/") for item in db.ConcreteGrades.keys()]
            raise ValueError(f"Concrete class '{class_name}' not found in database. Concrete type must be one of {grades_list}")

        conc = db.ConcreteGrades[class_name]
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
        
        self.fcd = round(self.fck / gamma_C, 1)  # Design yield strength (MPa)
        self.fctd = round(self.fctk_05 / gamma_CT, 1)  # Design yield strength (MPa)
        
    def __repr__(self):
        return f"Concrete(grade='{self.grade}', fck={self.fck}, fcm={self.fcm}, fctm={self.fctm}, " \
            f"fctk_05={self.fctk_05}, fctk_95={self.fctk_95}, Ecm={self.Ecm}, eps_c2={self.eps_c2}, " \
            f"eps_cu2={self.eps_cu2}, n={self.n}, fcd={self.fcd}, fctd={self.fctd})"
    
    def __str__(self):
        return f"Concrete {self.grade} (fck={self.fck} MPa, fcm={self.fcm} MPa, fctm={self.fctm} MPa, " \
            f"fctk_05={self.fctk_05} MPa, fctk_95={self.fctk_95} MPa, Ecm={self.Ecm} MPa, " \
            f"eps_c2={self.eps_c2}, eps_cu2={self.eps_cu2}, n={self.n}, fcd={self.fcd} MPa, " \
            f"fctd={self.fctd} MPa)"

    @property
    def C25_30(self):
        return Concrete("C25/30")  # Default concrete class

    @classmethod
    def from_fck(cls, f_ck: int, name=None) -> 'Concrete':
        """
        Create a Concrete instance from characteristic compressive strength, using EC2 relations.
        :param f_ck: Characteristic compressive strength of concrete (MPa)
        :type f_ck: int
        :return: Concrete instance
        """
        fck = float(f_ck)
        cls.fck = round(fck, 1)  # MPa
        cls.fcm = round(fck + 8, 1)  # Mean compressive strength (MPa)
        cls.fctm = round(0.30 * fck**(2/3), 1)  # Mean tensile strength (MPa)
        cls.fctk_005 = round(0.7 * cls.fctm, 1)  # 5% fractile
        cls.fctk_095 = round(1.3 * cls.fctm, 1)  # 95% fractile
        cls.Ecm = round(22000 * (cls.fcm / 10)**0.3, 1)  # Modulus of elasticity (MPa)
        cls.eps_c2 = 2.0 if fck <= 50 else 2.0 + 0.085 * (fck - 50) ** 0.53  # Strain at peak stress
        cls.eps_cu2 = 3.5 if fck <= 50 else round(2.6+35*((90.0-fck)/100.0)**4, 1)
        cls.n = 2.0 if fck <= 50 else round(1.4+23.4*((90.0-fck)/100.0)**4, 1)
        if name is not None:
            cls.name = name
            cls.grade = name
        else:
            cls.name = f"C{f_ck}"
            cls.grade = f"C{f_ck}"

        cls.fcd = round(cls.fck / gamma_C, 1)  # Design yield strength (MPa)
        cls.fctd = round(cls.fctk_05 / gamma_CT, 1)  # Design yield strength (MPa)

        return cls  

class ConcreteGrade(Enum):
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

def get_concrete(concrete: Union[str, Concrete, ConcreteGrade]) -> Concrete:
    if isinstance(concrete, Concrete):
        return concrete
    elif isinstance(concrete, ConcreteGrade):
        return concrete.value
    elif isinstance(concrete, str):
        return Concrete(concrete)
    else:
        raise TypeError("Input must be a str, Concrete, or ConcreteGrade")

class Reinforcement:
    def __init__(self, type_label: str | ReinforcementClass = "B500B"):
        """
        Eurocode 2 steel reinforcement properties.
        :param type_label: Steel type label (e.g., 'B500B', 'B500C')
        """
        
        if isinstance(type_label, ReinforcementClass):
            type_label = type_label.name
        self.grade = type_label
        self.name = type_label
        
        if type_label not in db.ReinforcementGrades.keys():
            raise ValueError(f"Steel type '{type_label}' not found in database. Steel type must be one of {list(db.ReinforcementGrades.keys())}")

        reinf = db.ReinforcementGrades[type_label]
        self.fyk = reinf["fyk"] # Characteristic yield strength (MPa)
        self.epsilon_uk = reinf["epsuk"] # Ultimate strain (‰)
        self.ftk = reinf["ftk"] # Characteristic tensile strength (MPa)
        self.Es = reinf["Es"] # Modulus of elasticity (MPa)
        self.ClassType = reinf["T"] # 'A', 'B', or 'C'
        
        gamma_s = db.ReinforcementParams["gamma_s"]  # Partial safety factor
        self.fyd = round(self.fyk / gamma_s, 1)  # Design yield strength (MPa)
    
    def __repr__(self):
        return f"Reinforcement(grade='{self.grade}', fyk={self.fyk}, epsilon_uk={self.epsilon_uk}, " \
            f"ftk={self.ftk}, Es={self.Es}, ClassType='{self.ClassType}', fyd={self.fyd})"
    def __str__(self):
        return f"Reinforcement {self.grade} (fyk={self.fyk} MPa, epsilon_uk={self.epsilon_uk} ‰, " \
            f"ftk={self.ftk} MPa, Es={self.Es} MPa, ClassType='{self.ClassType}', fyd={self.fyd} MPa)"

class ReinforcementGrade(Enum):
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

def get_reinforcement(reinforcement: Union[str, Reinforcement, ReinforcementGrade]) -> Reinforcement:
    if isinstance(reinforcement, Reinforcement):
        return reinforcement
    elif isinstance(reinforcement, ReinforcementGrade):
        return reinforcement.value
    elif isinstance(reinforcement, str):
        return Reinforcement(reinforcement)
    else:
        raise TypeError("Input must be a str, Reinforcement, or ReinforcementGrade")

class Prestress:
    def __init__(self, type_label: str | PrestressClass = "Y1860S7 12.5"):
        """
        Eurocode 2 steel reinforcement properties.
        :param type_label: Steel type label (e.g., 'Y1860S7 12.5', 'Y1860S7 15.2')
        """

        if isinstance(type_label, PrestressClass):
            class_name = type_label.name
            self.name = class_name.replace("_", " ", 1).replace("_", ".", 1)
        elif isinstance(type_label, str):
            self.name = type_label
            class_name = type_label.replace(" ", "_")
            class_name = class_name.replace(".", "_")
        else:
            raise TypeError("type_label must be a string or PrestressClass enum")

        if class_name not in db.PrestressGrades.keys():
            grades_list = [item.replace("_", " ", 1).replace("_", ".", 1) for item in db.PrestressGrades.keys()]
            raise ValueError(f"Prestress steel class '{class_name}' not found in database. Prestress type must be one of {grades_list}")

        reinf = db.PrestressGrades[class_name]
        self.pType = reinf["T"] # 'strand', 'bar', or 'wire'
        self.zone = reinf["zone"]
        self.fpk = reinf["fpk"] # Characteristic prestress force (MPa)
        self.fp0_1k = reinf["fp0_1k"] # Characteristic prestress force at 0.1% strain (MPa)
        self.Ep = reinf["Ep"] # Modulus of elasticity (MPa)
        self.d = reinf["d"] # Diameter (mm)
        self.Ap = reinf["Ap"] # Cross-sectional area (cm²)

        gamma_p = db.PrestressParams["gamma_p"]  # Partial safety factor
        self.fpd = round(self.fp0_1k / gamma_p, 0)  # Design yield strength (MPa)
    
    def __repr__(self):
        return f"Prestress(name='{self.name}', pType='{self.pType}', zone='{self.zone}', " \
            f"fpk={self.fpk}, fp0_1k={self.fp0_1k}, Ep={self.Ep}, d={self.d}, Ap={self.Ap}, fpd={self.fpd})"
    def __str__(self):
        return f"Prestress {self.name} (pType='{self.pType}', zone='{self.zone}', " \
            f"fpk={self.fpk} MPa, fp0_1k={self.fp0_1k} MPa, Ep={self.Ep} MPa, d={self.d} mm, " \
            f"Ap={self.Ap} cm², fpd={self.fpd} MPa)"

from . import material
from .material import beta_cc
from .material import beta_ce
from .material import cemprops
from .material import calc_creep_coef # EN1992-1:2004
from .material import calc_shrink_strain # EN1992-1:2004

from . import fire
from . import crack
from .crack import iscracked_annexLL

from . import uls
from .uls import beam
from .uls.beam import get_bend_params
from .uls.beam import calc_mrd
from .uls.beam import calc_asl
from .uls import shear
from .uls.shear import calc_asws
from .uls.shear import calc_vrd 
from .uls.shear import calc_vrdc
from .uls.shear import calc_vrdmax
from .uls import shell
from .uls.shell import calc_reinf_shell
from .uls.shell import calc_reinf_plane

from . import sls
from .sls import shrinkage
from .sls.shrinkage import shrink_strain # EN1992-1:2025
from .sls import creep
from .sls.creep import creep_coef # EN1992-1:2025

