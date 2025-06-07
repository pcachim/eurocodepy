"""
Eurocode 3 Steel Reinforcement Module.
This module provides classes and functions for Eurocode 3 steel reinforcement design.
It includes properties for different steel grades and types, as well as profile classes."""
from enum import Enum
from .. import db

ProfileType = Enum("ProfileType", db.SteelProfiles)
"""
Eurocode 3 steel classes existing in the databse.
"""

class Steel:
    """
    Eurocode 3 steel reinforcement properties.
    :param type_label: Steel type label (e.g., 'S235', 'S275', 'S355', 'S460')
    :raises ValueError: If the steel type is not found in the database.
    """

    def __init__(self, type_label: str = "S275"):        
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

class SteelProfile:
    pass

class ProfileI(SteelProfile):
    pass

class ProfileH(SteelProfile):
    pass

class ProfileSHS(SteelProfile):
    pass

