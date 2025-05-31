from enum import Enum

from .. import db
from .. import utils

from . import sls
from .sls import vibration
from .sls.vibration import floor_freq, vel, b_from_a, a_from_b, vlim
from .sls import deformation

RiskClass = Enum("RiskClasses", db.Timber["RiskClasses"])
ServiceClass = Enum("ServiceClasses", db.Timber["ServiceClasses"])
LoadDuration = Enum("LoadDuration", db.Timber["LoadDuration"])
TimberClass = Enum("TimberClass", list(db.TimberGrades.keys()))

class Timber:
    def __init__(self, type_label: str = "C24"):
        """
        Eurocode 5 timber properties.
        """
        
        if type_label not in db.TimberGrades.keys():
            raise ValueError(f"Steel type '{type_label}' not found in database. Steel type must be one of {list(db.TimberGrades.keys())}")

        timber = db.TimberGrades[type_label]
        self.fmk = timber["fmk"]  # Characteristic strength in MPa
        self.ft0k = timber["ft0k"] # Characteristic strength in tension parallel to grain (MPa)
        self.ft90k = timber["ft90k"]  # Characteristic strength in tension perpendicular to grain (MPa)
        self.fc0k = timber["fc0k"]  # Characteristic strength in compression parallel to grain (MPa)
        self.fc90k = timber["fc90k"]  # Characteristic strength in compression perpendicular to grain (MPa)
        self.fvk = timber["fvk"]  # Characteristic shear strength (MPa)
        self.E0mean = timber["E0mean"]  # Mean modulus of elasticity in MPa
        self.E0k = timber["E0k"]  # Characteristic modulus of elasticity in MPa
        self.E90k = timber["E90k"]  # Characteristic modulus of elasticity perpendicular to grain (MPa)
        self.Gmean = timber["Gmean"]  # Mean shear modulus in MPa
        self.rhok = timber["rhok"] # Characteristic density in kg/m³
        self.rhom = timber["rhom"] # Mean density in kg/m³
        self.type_label = type_label
        self.type = timber["Type"]

        self.safety = db.TimberParams["safety"][self.type]  # Partial safety factor
        self.kmod = db.TimberParams["kmod"][self.type]
        self.kdef = db.TimberParams["kmod"][self.type]
        self.kh = db.TimberParams["kh"][self.type]
    
    def k_mod(self, service_class: ServiceClass = ServiceClass.SC1, load_duratiom: LoadDuration = LoadDuration.Medium) -> float:
        """
        Returns the kmod value for serviceability limit state.
        :param service_class: Service class (1, 2, or 3)
        :return: kmod value
        """

        return self.kmod[service_class.name][load_duratiom.value]

    def k_def(self, service_class: ServiceClass = ServiceClass.SC1) -> float:
        """
        Returns the kdef value for serviceability limit state.
        :param service_class: Service class (1, 2, or 3)
        :return: kdef value
        """
        return self.kdef[service_class.name]

class SolidTimber(Timber):
    def __init__(self, type_label: str = "C24"):
        """
        Eurocode 5 solid timber properties.
        :param type_label: Solid timber type label (e.g., 'C24', 'C30')
        """

        grades_list = [item for item in db.TimberGrades.keys() if (item.startswith("C") or item.startswith("D"))]
        if type_label not in grades_list:
            raise ValueError(f"Softwood type '{type_label}' not found in database. Softwood type must be one of {grades_list}")

        super().__init__(type_label)

        self.fvrefk = db.TimberParams["fvrefk"][self.type]
        self.theta_twist = db.TimberParams["theta_twist"][self.type]
        self.kred = db.TimberParams["kred"][self.type]

Softwood = SolidTimber # Alias for SolidTimber, as it is commonly referred to as Softwood in Eurocode 5
Hardwood = SolidTimber # Alias for SolidTimber, as it is commonly referred to as Hardwood in Eurocode 5
ST = SolidTimber # Alias for SolidTimber, as it is commonly referred to as ST in Eurocode 5

class Glulam(Timber):
    def __init__(self, type_label: str = "GL24h"):
        """
        Eurocode 5 glulam properties.
        :param type_label: Glulam type label (e.g., 'GL24h', 'GL28c')
        """

        grades_list = [item for item in db.TimberGrades.keys() if item.startswith("GL")]

        if not type_label.startswith("GL"):
            raise ValueError(f"Glulam type '{type_label}' must start with 'GL'. Glulam type must be one of {grades_list}")
        if type_label not in grades_list:
            raise ValueError(f"Glulam type '{type_label}' not found in database. Glulam type must be one of {grades_list}")

        super().__init__(type_label)

        self.fvrefk = db.TimberParams["fvrefk"][self.type]
        self.theta_twist = db.TimberParams["theta_twist"][self.type]
        self.kred = db.TimberParams["kred"][self.type]

GL = Glulam # Alias for Glulam, as it is commonly referred to as Glulam in Eurocode 5

class CLT(Timber):
    pass

class LVL(Timber):
    pass

class WoodBasedPanels(Timber):
    pass
