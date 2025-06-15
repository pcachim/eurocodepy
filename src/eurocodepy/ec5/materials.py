# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
from enum import Enum

from eurocodepy import dbase

RiskClass = Enum("RiskClasses", dbase.Timber["RiskClasses"])
ServiceClass = Enum("ServiceClasses", dbase.Timber["ServiceClasses"])
LoadDuration = Enum("LoadDuration", dbase.Timber["LoadDuration"])
TimberClass = Enum("TimberClass", list(dbase.TimberGrades.keys()))


class Timber:
    """Eurocode 5 timber properties."""

    def __init__(self, type_label: str = "C24") -> None:
        """Initialize Timber object.

        Properties are derived from the database for the given type_label.

        Args:
            type_label (str, optional): Timber grade label (e.g., 'C24').
            Defaults to 'C24'.

        Raises:
            ValueError: If the type_label is not found in the database.

        """
        if type_label not in dbase.TimberGrades:
            msg = (
                f"Timber type '{type_label}' not found in database. "
                f"Timber type must be one of {list(dbase.TimberGrades)}"
            )
            raise ValueError(msg)

        timber = dbase.TimberGrades[type_label]
        self.fmk = timber["fmk"]  # Characteristic strength in MPa
        self.ft0k = timber["ft0k"]  # Charact. strength in tension // to grain (MPa)
        self.ft90k = timber["ft90k"]  # Charact. strength in tensio perp. to grain (MPa)
        self.fc0k = timber["fc0k"]  # Charact. strength in compression // to grain (MPa)
        self.fc90k = timber["fc90k"]  # Charact. strength in compr. perp. to grain (MPa)
        self.fvk = timber["fvk"]  # Characteristic shear strength (MPa)
        self.E0mean = timber["E0mean"]  # Mean modulus elasticity in MPa
        self.E0k = timber["E0k"]  # Characteristic modulus elasticity in MPa
        self.E90k = timber["E90k"]  # Charact. modulus elasticity perp. to grain (MPa)
        self.Gmean = timber["Gmean"]  # Mean shear modulus in MPa
        self.rhok = timber["rhok"]  # Characteristic density in kg/m³
        self.rhom = timber["rhom"]  # Mean density in kg/m³
        self.type_label = type_label
        self.type = timber["Type"]

        self.safety = dbase.TimberParams["safety"][self.type]  # Partial safety factor
        self.kmod = dbase.TimberParams["kmod"][self.type]
        self.kdef = dbase.TimberParams["kmod"][self.type]
        self.kh = dbase.TimberParams["kh"][self.type]

    def k_mod(
        self,
        service_class: ServiceClass = ServiceClass.SC1,
        load_duratiom: LoadDuration = LoadDuration.Medium,
    ) -> float:
        """Return the kmod value for serviceability limit state.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.
            load_duratiom (LoadDuration, optional): Load duration (Perm, Long,
            Medium, Short, Inst).
                Defaults to LoadDuration.Medium.

        Returns:
            float: kmod value for the specified service class and load duration.

        """
        return self.kmod[service_class.name][load_duratiom.value]

    def k_def(self, service_class: ServiceClass = ServiceClass.SC1) -> float:
        """Return the kdef value for serviceability limit state.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.

        Returns:
            float: kmod value for the specified service class.

        """
        return self.kdef[service_class.name]


class SolidTimber(Timber):
    """Class represents Eurocode 5 solid timber properties.

    It includes both softwood and hardwood types.

    Args:
        type_label (str): Timber grade label (e.g., 'C24', 'D30'). Defaults to 'C24'.

    """

    def __init__(self, type_label: str = "C24") -> None:
        """Initialize a SolidTimber object.

        Properties read from the database for the given type_label.

        Args:
            type_label (str, optional): Timber grade label (e.g., 'C24', 'D30').
            Defaults to 'C24'.

        Raises:
            ValueError: If the type_label is not found in the database.

        """
        grades_list = [item for item in dbase.TimberGrades
                    if (item.startswith(("C", "D")))]
        if type_label not in grades_list:
            msg = (
                f"Softwood type '{type_label}' not found in database. "
                f"Softwood type must be one of {grades_list}"
            )
            raise ValueError(msg)

        super().__init__(type_label)

        self.fvrefk = dbase.TimberParams["fvrefk"][self.type]
        self.theta_twist = dbase.TimberParams["theta_twist"][self.type]
        self.kred = dbase.TimberParams["kred"][self.type]


class Glulam(Timber):
    """Eurocode 5 glulam properties.

    :param type_label: Glulam type label (e.g., 'GL24h', 'GL28c')
    """

    def __init__(self, type_label: str = "GL24h") -> None:
        """Initialize a Glulam object.

        Properties read from the database for the given type_label.

        Args:
            type_label (str, optional): Glulam type label (e.g., 'GL24h', 'GL28c').
            Defaults to 'GL24h'.

        Raises:
            ValueError: If the type_label does not start with 'GL' or
            is not found in the database.

        """
        grades_list = [item for item in dbase.TimberGrades if item.startswith("GL")]

        if not type_label.startswith("GL"):
            msg = (
                f"Glulam type '{type_label}' must start with 'GL'. "
                f"Glulam type must be one of {grades_list}"
            )
            raise ValueError(msg)
        if type_label not in grades_list:
            msg = (
                f"Glulam type '{type_label}' not found in database. "
                f"Glulam type must be one of {grades_list}"
            )
            raise ValueError(msg)

        super().__init__(type_label)

        self.fvrefk = dbase.TimberParams["fvrefk"][self.type]
        self.theta_twist = dbase.TimberParams["theta_twist"][self.type]
        self.kred = dbase.TimberParams["kred"][self.type]


class CLT(Timber):
    """Eurocode 5 Cross-Laminated Timber (CLT) properties. Not implemented."""


class LVL(Timber):
    """Eurocode 5 Laminated Veneer Lumber (LVL) properties. Not implemented."""


class WoodBasedPanels(Timber):
    """Eurocode 5 Wood-Based Panels properties. Not implemented."""


# Alias for SolidTimber, as it is commonly referred to as Softwood in Eurocode 5
Softwood = SolidTimber
# Alias for SolidTimber, as it is commonly referred to as HArdwood in Eurocode 5
Hardwood = SolidTimber
# Alias for SolidTimber, as it is commonly referred to as ST in Eurocode 5
ST = SolidTimber
# Alias for Glulam, as it is commonly referred to as Glulam in Eurocode 5
GL = Glulam
