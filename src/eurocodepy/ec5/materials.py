# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
from enum import Enum
from functools import lru_cache

from eurocodepy import dbase
from eurocodepy._compat import StrEnum
from eurocodepy.ec1 import LoadCombination, LoadCombinations, CombinationType, LoadType

RiskClass = Enum("RiskClasses", dbase.TimberMaterial["RiskClasses"])


def _all_service_classes() -> list:
    """Service classes of every edition (the base list plus those that an
    edition adds, e.g. SC4 in EN 1995-1-1:2025), in order, without repeats."""
    out = list(dbase.TimberMaterial["ServiceClasses"])
    for ed in dbase.db.get("Editions", {}).get("ec5", {}).values():
        for sc in ed.get("overrides", {}).get("Timber.ServiceClasses", []):
            if sc not in out:
                out.append(sc)
    return out


ServiceClass = Enum("ServiceClass", _all_service_classes())
LoadDuration = Enum("LoadDuration", dbase.TimberMaterial["LoadDuration"])
TimberForcesType = Enum("TimberForcesType",
                names=("Bending", "Compression", "Tension", "Shear", "Torsion"))
TimberClasses = Enum("TimberClass", list(dbase.TimberGrades.keys()))


@lru_cache(maxsize=None)
def _edition_timber_db(edition: str) -> dict:
    """The ``Timber`` section of the database resolved for *edition* (cached;
    treat as read-only)."""
    return dbase.get_edition_data("ec5", edition)["Timber"]


def _timber_db(edition: str | None) -> dict:
    """The ``Timber`` database section of *edition*; ``None`` is the module-level
    default edition (EN 1995-1-1:2004), exactly as before editions existed."""
    return dbase.TimberMaterial if edition is None else _edition_timber_db(edition)


class TimberType(StrEnum):
    """Enumeration of timber product types."""

    TIMBER = "timber"
    GLULAM = "glulam"
    CLT = "clt"
    LVL = "lvl"
    GLVL = "glvl"
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
    LVL = "LVL"  # "Laminated veneer lumber"
    GLVL_P = "Glued laminated veneer lumber with parallel veneers"
    GLVL_C = "Glued laminated veneer lumber with crossband veneers"
    GLVL = "GLVL"  # "Glued laminated veneer lumber"
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
        edition (str, optional): Edition of EN 1995-1-1 whose parameters
        (``k_mod``, ``k_def``, ``k_h``, ``γ_M``, service classes) are used,
        e.g. ``"2025"``. ``None`` (default) is the 2004 edition.

    Raises:
        ValueError: If the type_label is not found in the database.

    """

    def __init__(self, type_label: str = "C24",  # noqa: D107
                 edition: str | None = None) -> None:
        tdb = _timber_db(edition)
        self.edition = edition
        self._params = tdb["Parameters"]
        try:
            timber = tdb["Grade"][type_label]
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
        self.timber_product = TimberProduct.ST

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

        params = self._params
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

    def __post_init__(self,  # noqa: D105
                    service_class: ServiceClass,
                    load_duration: LoadDuration) -> None:
        self.design_values(ServiceClass.SC3, LoadDuration.Permanent)

    @property
    def kcr(self) -> float:
        """Crack factor for shear, ``b_ef = k_cr·b`` (EN 1995-1-1:2004 §6.1.7(2)).

        Defaults to 0.67 for solid timber and glued laminated timber and 1.0
        for the other products; assign a value to override it (e.g. a National
        Annex value). Not used by the 2025 edition, which has no ``b_ef``
        (the cracking effect is in ``k_v``, §8.1.11.1).
        """
        override = getattr(self, "_kcr", None)
        if override is not None:
            return override
        if self.material in (TimberType.TIMBER, TimberType.GLULAM):
            return 0.67
        return 1.0

    @kcr.setter
    def kcr(self, value: float | None) -> None:
        self._kcr = value

    def set_product(self, product: TimberProduct) -> None:
        """Set product type.

        Args:
            product (TimberProduct): The type of timber product.

        """
        self.timber_product = product

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
            "Perm", "Long", "Medium", "Short", "Inst", "Permanent", "LongDuration",
            "MediumDuration", "ShortDuration", "Instantaneous",
        }:
            load_duration = 0
        if isinstance(load_duration, LoadDuration):
            load_duration = load_duration.value

        if (isinstance(service_class, str) and
            service_class not in {"SC1", "SC2", "SC3", "SC4"}):
            service_class = "SC3"
        if isinstance(service_class, ServiceClass):
            service_class = service_class.name

        try:
            kmod = self.kmods[service_class][load_duration]
        except KeyError:
            msg = (f"No k_mod for {self.type_label} ({self.type}) in "
                   f"{service_class} in EN 1995-1-1"
                   f"{':' + self.edition if self.edition else ''}.")
            raise KeyError(msg) from None
        if kmod is None:
            msg = (f"No k_mod for {self.type_label} ({self.type}) in "
                   f"{service_class} for this load duration.")
            raise KeyError(msg)
        self.kmod = kmod

        return self.kmod

    def design_values(
        self,
        service_class: ServiceClass | str = ServiceClass.SC1,
        load_duration: LoadDuration | str = LoadDuration.MediumDuration,
    ) -> dict:
        """Calculate the design values of the properties and returns them as a dict.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.
            load_duration (LoadDuration, optional): Load duration (Perm, Long,
            Medium, Short, Inst).
                Defaults to LoadDuration.Medium.

        Returns:
            A dict with the design values

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
        return {
            "fmd": self.fmd,
            "ft0d": self.ft0d,
            "fc0d": self.fc0d,
            "fvd": self.fvd,
            "fc90d": self.fc90d,
            "ft90d": self.ft90d,
            "kmod": kmod,
            "safety": self.safety,
        }

    def k_def(self, service_class: ServiceClass = ServiceClass.SC1) -> float:
        """Return the kdef value for serviceability limit state.

        Args:
            service_class (ServiceClass, optional): Service class (SC1, SC2, or SC3).
                Defaults to ServiceClass.SC1.

        Returns:
            float: kdef value for the specified service class.

        """
        return self.kdef[service_class.name]

    def fc0k_factor(self, service_class: ServiceClass | str = ServiceClass.SC1,
                    optional: bool = False) -> float:
        """Factor on ``f_c,0,k`` for the service class (EN 1995-1-1:2025 5.2.1(3)-(4)):
        ``0.83`` for LVL in SC2/SC3 and GLVL in SC2 (a requirement), and ``1.2``
        for ST, FST, GST and GL in SC1 (*optional*, returned only with
        ``optional=True``). ``1.0`` when none applies or the edition has none.
        It is **not** applied automatically by :meth:`design_values`."""
        if isinstance(service_class, ServiceClass):
            service_class = service_class.name
        f = (self._params.get("fc0k_sc_factor", {}).get(self.type, {})
             .get(service_class, 1.0))
        return f if (f < 1.0 or optional) else 1.0

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
                if "st" in self.kh:          # EN 1995-1-1:2025 Table 5.6
                    aref = self.kh["atref"]
                    sm = self.kh["st"]
                    kmin = self.kh["khtmin"]
                    kmax = self.kh["khtmax"]
                else:
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

    def __init__(self, type_label: str = "C24",  # noqa: D107
                 edition: str | None = None) -> None:
        grades_list = [item for item in dbase.TimberGrades
                    if (item.startswith(("C", "D")))]
        if type_label not in grades_list:
            msg = (
                f"Softwood type '{type_label}' not found in database. "
                f"Softwood type must be one of {grades_list}"
            )
            raise ValueError(msg)

        super().__init__(type_label, edition)

        if type_label.startswith("D"):
            self.Gk = 0.83 * self.Gmean
        else:
            self.Gk = 0.67 * self.Gmean
        self.fvrefk = self._params["fvrefk"][self.type]
        self.theta_twist = self._params["theta_twist"][self.type]
        self.kred = self._params["kred"][self.type]
        self.material = TimberType.TIMBER
        self.timber_product = TimberProduct.ST


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

    def __init__(self, type_label: str = "GL24h",  # noqa: D107
                 edition: str | None = None) -> None:
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

        super().__init__(type_label, edition)

        timber = dbase.TimberGrades[type_label]
        self.frk = timber["frk"]  # Characteristic rolling shear strength (MPa)
        self.Gk = timber["Gk"]  # Characteristic shear modulus in MPa
        self.Grk = timber["Grk"]  # Charact. rolling shear modulus in
        self.Grmean = timber["Grmean"]  # Mean rolling shear modulus in MPa
        self.G90k = timber["Gk"]  # Charact. shear modulus perp. to grain (MPa)
        self.fvrefk = self._params["fvrefk"][self.type]
        self.theta_twist = self._params["theta_twist"][self.type]
        self.kred = self._params["kred"][self.type]
        self.material = TimberType.GLULAM
        self.timber_product = TimberProduct.GL

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

    def __init__(self, type_label: str = "CLT30",  # noqa: D107
                 edition: str | None = None) -> None:
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

        super().__init__(type_label, edition)
        self.material = TimberType.CLT
        self.timber_product = TimberProduct.CLT


class LVL(Timber):
    """Eurocode 5 Laminated Veneer Lumber (LVL) properties. Not implemented."""

    def __init__(self, type_label: str = "LVL30P",  # noqa: D107
                 edition: str | None = None) -> None:
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

        super().__init__(type_label, edition)
        self.material = TimberType.LVL
        self.timber_product = TimberProduct.LVL_P


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


def TimberClass(timber: str = "C24", edition: str | None = None) -> Timber:  # noqa: N802
    """Return a Timber object of the appropriate subclass based on timber grade.

    Args:
        timber (str, optional): Timber grade label (e.g., 'C24', 'GL24h').
            Defaults to 'C24'.
        edition (str, optional): Edition of EN 1995-1-1 for ``k_mod``,
            ``k_def``, ``k_h``, ``γ_M`` and the service classes (e.g. ``"2025"``);
            ``None`` is the 2004 edition.

    Returns:
        Timber: A SolidTimber instance for C/D grades, Glulam instance for GL grades,
            or generic Timber instance for other grades.

    """
    if timber.startswith(("C", "D")):
        return SolidTimber(timber, edition)

    if timber.startswith("GL"):
        return Glulam(timber, edition)

    if timber.startswith("LVL"):
        return LVL(timber, edition)

    if timber.startswith("CLT"):
        return CLT(timber, edition)

    return Timber(timber, edition)


def GetTimberDesignValues(timber: Timber, combos: LoadCombinations,  # noqa: N802
                          service_class: ServiceClass | str = ServiceClass.SC1) -> dict:
    """Get the design values of a timber for each load combination.

    ``kmod`` of a combination is that of the action of shortest duration in it
    (EN 1995-1-1, 3.1.3(2)); the durations of the load types are those of
    :func:`GetLoadDurations`. A combination whose ``attributes`` have ``"loadduration"``
    (a :class:`LoadDuration` or its name) uses that value instead. Serviceability
    combinations have no design strengths: they give ``{"design": False}``.

    Args:
        timber (Timber): the timber class (C18, GL24c, ...)
        combos (LoadCombinations): the collection of load combinations, or any
            iterable of :class:`~eurocodepy.ec1.LoadCombination`
        service_class (ServiceClass | str): service class of the member. Defaults to SC1.

    Returns:
        dict: ``{combination name: design values}``, see :meth:`Timber.design_values`

    Raises:
        ValueError: if the load duration of a combination cannot be determined.

    """
    durations = GetLoadDurations()
    design_values: dict = {}
    for combo in combos:
        if combo.type in {CombinationType.SLS_K, CombinationType.SLS_FR, CombinationType.SLS_QP}:
            design_values[combo.name] = {"design": False}
            continue
        duration = combo.attributes.get("loadduration")
        if isinstance(duration, str):
            duration = LoadDuration[duration]
        if duration is None:
            found = [durations[entry[0].load_type] for entry in combo.factors.values()
                     if isinstance(entry, tuple)]
            if not found:
                msg = (f"combination '{combo.name}': no load types to take the load duration from; "
                       "give attributes['loadduration']")
                raise ValueError(msg)
            duration = max(found, key=lambda d: d.value)       # the shortest action governs
        values = timber.design_values(service_class, duration)
        values["design"] = True
        values["loadduration"] = duration
        design_values[combo.name] = values
    return design_values


def GetLoadDurations() -> dict:  # noqa: D103, N802
    return {
        LoadType.ACCIDENTAL: LoadDuration.Instantaneous,
        LoadType.EARTHQUAKE: LoadDuration.Instantaneous,
        LoadType.FIRE: LoadDuration.Instantaneous,
        LoadType.LIVE: LoadDuration.MediumDuration,
        LoadType.OTHER: LoadDuration.Instantaneous,
        LoadType.PERMANENT: LoadDuration.Permanent,
        LoadType.SNOW: LoadDuration.ShortDuration,
        LoadType.TEMPERATURE: LoadDuration.ShortDuration,
        LoadType.WIND: LoadDuration.ShortDuration,
    }
