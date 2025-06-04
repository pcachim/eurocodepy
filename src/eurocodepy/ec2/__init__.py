from enum import Enum
from .. import db

from .. import utils

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

ConcreteClass = Enum("ConcreteClass", {item: item.replace("_", "/") for item in db.ConcreteGrades.keys()})
ReinforcementClass = Enum("ReinforcementClass", list(db.ReinforcementGrades.keys()))
PrestressClass = Enum("PrestressClass", list(db.PrestressGrades.keys()))

class Concrete:
    def __init__(self, class_name: str | ConcreteClass = "C30/37"):
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
        
        gamma_cc = db.ConcreteParams["gamma_cc"]  # Partial safety factor
        self.fcd = round(self.fck / gamma_cc, 1)  # Design yield strength (MPa)
        gamma_ct = db.ConcreteParams["gamma_ct"]  # Partial safety factor
        self.fctd = round(self.fctk_05 / gamma_ct, 1)  # Design yield strength (MPa)

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

        gamma_cc = db.ConcreteParams["gamma_cc"]  # Partial safety factor
        cls.fcd = round(cls.fck / gamma_cc, 1)  # Design yield strength (MPa)
        gamma_ct = db.ConcreteParams["gamma_ct"]  # Partial safety factor
        cls.fctd = round(cls.fctk_05 / gamma_ct, 1)  # Design yield strength (MPa)

        return cls  

ConcreteGrade = Enum("ConcreteGrade", {item: Concrete(item) for item in db.ConcreteGrades.keys()})

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
