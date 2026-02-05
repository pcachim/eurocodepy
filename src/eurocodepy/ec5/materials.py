# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
from enum import Enum, StrEnum

from eurocodepy import dbase

RiskClass = Enum("RiskClasses", dbase.TimberMaterial["RiskClasses"])
ServiceClass = Enum("ServiceClass", dbase.TimberMaterial["ServiceClasses"])
LoadDuration = Enum("LoadDuration", dbase.TimberMaterial["LoadDuration"])
TimberForcesType = Enum("TimberForcesType",
                names=("Bending", "Compression", "Tension", "Shear", "Torsion"))
TimberClasses = Enum("TimberClass", list(dbase.TimberGrades.keys()))


class TimberType(StrEnum):
    """Enumeration of timber product types."""

    TIMBER = "timber"
    GLULAM = "glulam"
    CLT = "clt"
    LVL = "lvl"
    PANEL = "board"


class TimberProduct(StrEnum):
    """Enumeration of timber product types."""

    ST = "Structural timber"
    FST = "Structural finger-jointed timber"
    GL = "Glued laminated timber"
    BGL = "Block glued glulam"
    GST = "Glued solid timber"
    CLT = "CLT"  # "Cross laminated timber"
    LVL_P = "Laminated veneer lumber with parallel veneers"
    LVL_C = "Laminated veneer lumber with crossband veneers"
    LVL = "LVL"
    GLVL_P = "Glued laminated veneer lumber with parallel veneers"
    GLVL_C = "Glued laminated veneer lumber with crossband veneers"
    GLVL = "GLVL"
    SWP_P = "Single layer solid wood panel"
    SWP_C = "Multi-layered solid wood panel"
    PW = "Plywood"
    OSB = "Oriented strand board"
    MDF = "Dry process fibreboard"
    SB = "Softboard"
    MB = "Medium fibreboard"
    HB = "Hard fibreboard"
    RPB = "Resin-bonded particleboard"
    CPB = "Cement-bonded particleboard"
    GFB = "Gypsum fibreboard"
    GPB = "Gypsum plasterboard"


class Timber:
    """Initialize Timber object.

    Properties are derived from the database for the given type_label.

    Args:
        type_label (str, optional): Timber grade label (e.g., 'C24').
        Defaults to 'C24'.

    Raises:
        ValueError: If the type_label is not found in the database.

    """

    def __init__(self, type_label: str = "C24") -> None:  # noqa: D107
        try:
            timber = dbase.TimberGrades[type_label]
        except KeyError:
            msg = (
                f"Timber type '{type_label}' not found. "
                f"Available types: {list(dbase.TimberGrades)}"
            )
            raise ValueError(
                msg,
            ) from None

        self.type_label = type_label
        self.type = timber["Type"]
        self.material = TimberType.TIMBER

        self.fmk = timber["fmk"]
        self.ft0k = timber["ft0k"]
        self.ft90k = timber["ft90k"]
        self.fc0k = timber["fc0k"]
        self.fc90k = timber["fc90k"]
        self.fvk = timber["fvk"]

        self.E0mean = timber["E0mean"]
        self.E0k = timber["E0k"]
        self.E90mean = timber["E90mean"]
        self.E90k = 0.0
        self.Gmean = timber["Gmean"]
        self.Gk = self.E0k / self.E0mean * self.Gmean

        self.rhok = timber["rhok"]
        self.rhom = timber["rhom"]

        params = dbase.TimberParams
        self.safety = params["safety"][self.type]
        self.kmods = params["kmod"][self.type]
        self.kh = params["kh"][self.type]
        self.kdef = params["kdef"][self.type]
        self.kmod = 0.0

        self.fmd = 0.0
        self.ft0d = 0.0
        self.fc0d = 0.0
        self.fvd = 0.0
        self.fc90d = 0.0
        self.ft90d = 0.0

    def k_mod(
        self,
        service_class: ServiceClass | str = ServiceClass.SC1,
        load_duration: LoadDuration | str = LoadDuration.MediumDuration,
    ) -> float:
        """Return the kmod value for serviceability limit state.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.
            load_duration (LoadDuration, optional): Load duration (Perm, Long,
            Medium, Short, Inst).
                Defaults to LoadDuration.Medium.

        Returns:
            float: kmod value for the specified service class and load duration.

        """
        if isinstance(load_duration, str) and load_duration not in {
            "Perm", "Long", "Medium", "Short", "Inst", "Permanent", "LongTerm",
            "MediumTerm", "ShortTerm", "Instantaneous",
        }:
            load_duration = 0
        if isinstance(load_duration, LoadDuration):
            load_duration = load_duration.value

        if (isinstance(service_class, str) and
            service_class not in {"SC1", "SC2", "SC3"}):
            service_class = "SC3"
        if isinstance(service_class, ServiceClass):
            service_class = service_class.name

        self.kmod = self.kmods[service_class][load_duration]

        return self.kmod

    def design_values(
        self,
        service_class: ServiceClass | str = ServiceClass.SC1,
        load_duration: LoadDuration | str = LoadDuration.MediumDuration,
    ) -> None:
        """Calculate the design values of the strengh properties.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.
            load_duration (LoadDuration, optional): Load duration (Perm, Long,
            Medium, Short, Inst).
                Defaults to LoadDuration.Medium.

        """
        kmod = self.k_mod(service_class, load_duration)
        safety = self.safety
        ratio = kmod / safety
        self.fmd = self.fmk * ratio
        self.ft0d = self.ft0k * ratio
        self.fc0d = self.fc0k * ratio
        self.fvd = self.fvk * ratio
        self.fc90d = self.fc90k * ratio
        self.ft90d = self.ft90k * ratio

    def k_def(self, service_class: ServiceClass = ServiceClass.SC1) -> float:
        """Return the kdef value for serviceability limit state.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.

        Returns:
            float: kdef value for the specified service class.

        """
        return self.kdef[service_class.name]

    def k_h(self, size: float,
            forcetype: TimberForcesType = TimberForcesType.Bending) -> float:
        """Return the kh value for serviceability limit state.

        Returns:
            float: kh value.

        """
        match forcetype:
            case TimberForcesType.Bending:
                aref = self.kh["aref"]
                sm = self.kh["sm"]
                kmin = self.kh["khmmin"]
                kmax = self.kh["khmmax"]
            case TimberForcesType.Shear:
                aref = self.kh["aref"]
                sm = self.kh["sv"]
                kmin = self.kh["khvmin"]
                kmax = self.kh["khvmax"]
            case TimberForcesType.Tension:
                aref = self.kh["aref"]
                sm = self.kh["sm"]
                kmin = self.kh["khmmin"]
                kmax = self.kh["khmmax"]
            case _:
                return 1.0

        kh = (aref / size)**sm
        return max(kmin, min(kh, kmax))

    def __str__(self) -> str:  # noqa: D105
        return (
            f"Timber class: {self.type_label}\n"
            f"  type: {self.type}\n"
            f"  fmk: {self.fmk} MPa\n"
            f"  ft0k: {self.ft0k} MPa\n"
            f"  fc0k: {self.fc0k} MPa\n"
            f"  fvk: {self.fvk} MPa\n"
            f"  fc90k: {self.fc90k} MPa\n"
            f"  ft90k: {self.ft90k} MPa\n"
            f"  E0k: {self.E0k} MPa\n"
            f"  E90mean: {self.E90mean} MPa\n"
            f"  E0mean: {self.E0mean} MPa\n"
            f"  Gmean: {self.Gmean} MPa\n"
            f"  rhok: {self.rhok} kg/m³\n"
            f"  rhom: {self.rhom} kg/m³\n"
        )


class SolidTimber(Timber):
    """Class represents Eurocode 5 solid timber properties.

    It includes both softwood and hardwood types.
    Properties read from the database for the given type_label.

    Args:
        type_label (str, optional): Timber grade label (e.g., 'C24', 'D30').
        Defaults to 'C24'.

    Raises:
        ValueError: If the type_label is not found in the database.

    """

    def __init__(self, type_label: str = "C24") -> None:  # noqa: D107
        grades_list = [item for item in dbase.TimberGrades
                    if (item.startswith(("C", "D")))]
        if type_label not in grades_list:
            msg = (
                f"Softwood type '{type_label}' not found in database. "
                f"Softwood type must be one of {grades_list}"
            )
            raise ValueError(msg)

        super().__init__(type_label)

        if type_label.startswith("D"):
            self.Gk = 0.83 * self.Gmean
        else:
            self.Gk = 0.67 * self.Gmean
        self.fvrefk = dbase.TimberParams["fvrefk"][self.type]
        self.theta_twist = dbase.TimberParams["theta_twist"][self.type]
        self.kred = dbase.TimberParams["kred"][self.type]
        self.material = "Solid"


class Glulam(Timber):
    """Eurocode 5 glulam properties.

    Properties read from the database for the given type_label.

    Args:
        type_label (str, optional): Glulam type label (e.g., 'GL24h', 'GL28c').
        Defaults to 'GL24h'.

    Raises:
        ValueError: If the type_label does not start with 'GL' or
        is not found in the database.

    """

    def __init__(self, type_label: str = "GL24h") -> None:  # noqa: D107
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

        timber = dbase.TimberGrades[type_label]
        self.frk = timber["frk"]  # Characteristic rolling shear strength (MPa)
        self.Gk = timber["Gk"]  # Characteristic shear modulus in MPa
        self.Grk = timber["Grk"]  # Charact. rolling shear modulus in
        self.Grmean = timber["Grmean"]  # Mean rolling shear modulus in MPa
        self.G90k = timber["Gk"]  # Charact. shear modulus perp. to grain (MPa)
        self.fvrefk = dbase.TimberParams["fvrefk"][self.type]
        self.theta_twist = dbase.TimberParams["theta_twist"][self.type]
        self.kred = dbase.TimberParams["kred"][self.type]
        self.material = TimberType.GLULAM

    def __str__(self) -> str:  # noqa: D105
        return (
            f"Timber class: {self.type_label}\n"
            f"  type: {self.type}\n"
            f"  fmk: {self.fmk} MPa\n"
            f"  ft0k: {self.ft0k} MPa\n"
            f"  fc0k: {self.fc0k} MPa\n"
            f"  fvk: {self.fvk} MPa\n"
            f"  fc90k: {self.fc90k} MPa\n"
            f"  ft90k: {self.ft90k} MPa\n"
            f"  frk: {self.frk} MPa\n"
            f"  E0mean: {self.E0mean} MPa\n"
            f"  E0k: {self.E0k} MPa\n"
            f"  E90mean: {self.E90mean} MPa\n"
            f"  E90k: {self.E90k} MPa\n"
            f"  Gmean: {self.Gmean} MPa\n"
            f"  Gk: {self.Gk} MPa\n"
            f"  Grmean: {self.Grmean} MPa\n"
            f"  Grk: {self.Grk} MPa\n"
            f"  rhok: {self.rhok} kg/m³\n"
            f"  rhom: {self.rhom} kg/m³\n"
        )


class CLT(Timber):
    """Eurocode 5 Cross-Laminated Timber (CLT) properties. Not implemented."""

    def __init__(self, type_label: str = "CLT30") -> None:  # noqa: D107
        grades_list = [item for item in dbase.TimberGrades if item.startswith("GL")]

        if not type_label.startswith("CLT"):
            msg = (
                f"CLT type '{type_label}' must start with 'CLT'. "
                f"CLT type must be one of {grades_list}"
            )
            raise ValueError(msg)
        if type_label not in grades_list:
            msg = (
                f"CLT type '{type_label}' not found in database. "
                f"CLT type must be one of {grades_list}"
            )
            raise ValueError(msg)

        super().__init__(type_label)
        self.material = TimberType.CLT


class LVL(Timber):
    """Eurocode 5 Laminated Veneer Lumber (LVL) properties. Not implemented."""

    def __init__(self, type_label: str = "LVL30P") -> None:  # noqa: D107
        grades_list = [item for item in dbase.TimberGrades if item.startswith("GL")]

        if not type_label.startswith("LVL"):
            msg = (
                f"LVL type '{type_label}' must start with 'LVL'. "
                f"LVL type must be one of {grades_list}"
            )
            raise ValueError(msg)
        if type_label not in grades_list:
            msg = (
                f"LVL type '{type_label}' not found in database. "
                f"LVL type must be one of {grades_list}"
            )
            raise ValueError(msg)

        super().__init__(type_label)
        self.material = TimberType.LVL


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

TimberGrades = {item: Timber(item)
            for item in dbase.TimberGrades}


def TimberClass(timber: str = "C24") -> Timber:  # noqa: N802
    """Return a Timber object of the appropriate subclass based on timber grade.

    Args:
        timber (str, optional): Timber grade label (e.g., 'C24', 'GL24h').
            Defaults to 'C24'.

    Returns:
        Timber: A SolidTimber instance for C/D grades, Glulam instance for GL grades,
            or generic Timber instance for other grades.

    """
    if timber.startswith(("C", "D")):
        return SolidTimber(timber)

    if timber.startswith("GL"):
        return Glulam(timber)

    if timber.startswith("LVL"):
        return LVL(timber)

    if timber.startswith("CLT"):
        return CLT(timber)

    return Timber(timber)
