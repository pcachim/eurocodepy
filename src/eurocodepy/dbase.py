# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

import copy
import json
import warnings
from pathlib import Path

from eurocodepy import annex as _annex

"""eurocodepy.dbase.
====================

This module provides access to a structured database of Eurocode-related materials,
profiles, and loads. It loads data from JSON files and exposes them as both dictionaries
and custom objects for convenient access.

Features:
---------
- Loads Eurocode data from JSON files located in the 'data' directory.
- Provides access to materials (Concrete, Steel, Timber, Reinforcement, Prestress, Bolts) and their grades, parameters, and profiles.
- Loads steel profile data (I, SHS, RHS, CHS) from separate JSON files and integrates them into the main database.
- Exposes both dictionary-based and attribute-based (object) access to the database.
- Offers convenience variables for direct access to common sub-databases (e.g., ConcreteGrades, SteelParams).

Usage Examples:
---------------
- Dictionary access:
    db["Materials"]["Timber"]["Grade"]["C24"]["fcd"]

Available Variables:
--------------------
- db: Main Eurocodes database as a dictionary.
- dbobj: deprecated, a snapshot of ``db`` with attribute access (built when asked for, not at import).
- Materials, Concrete, Steel, Timber, Reinforcement, Prestress, Bolts: Material sub-databases.
- ConcreteGrades, SteelGrades, TimberGrades, ReinforcementGrades, PrestressGrades, BoltGrades: Grade sub-databases.
- ConcreteParams, SteelParams, TimberParams, ReinforcementParams, PrestressParams: Parameter sub-databases.
- SteelIProfiles, SteelSHSProfiles, SteelRHSProfiles, SteelCHSProfiles: Steel profile databases.
- Loads, WindLoads, DeadLoads, SeismicLoads: Load sub-databases.

Note:
----
This module is intended for internal use within the eurocodepy package and assumes the presence of the required JSON data files.
"""


def __dict2obj(base_dict: dict) -> str:
    class Obj:
        """Custom object class used as the object_hook."""

        def __init__(self, base_dict: dict) -> None:
            """Update the object's __dict__ with the dictionary."""
            self.__dict__.update(base_dict)

    return json.loads(json.dumps(base_dict), object_hook=Obj)


base_path = Path(__file__).parent / "data"
base_name = base_path / "eurocodes.json"
with base_name.open(encoding="utf-8") as f:
    db = json.loads(f.read())["Eurocodes"]
prof_name = base_path / "i_profiles_euro.json"
with prof_name.open(encoding="utf-8") as f:
    db["SteelProfiles"]["EuroI"] = json.loads(f.read())
prof_name = base_path / "shs_profiles_euro.json"
with prof_name.open(encoding="utf-8") as f:
    db["SteelProfiles"]["EuroSHS"] = json.loads(f.read())
prof_name = base_path / "rhs_profiles_euro.json"
with prof_name.open(encoding="utf-8") as f:
    db["SteelProfiles"]["EuroRHS"] = json.loads(f.read())
prof_name = base_path / "chs_profiles_euro.json"
with prof_name.open(encoding="utf-8") as f:
    db["SteelProfiles"]["EuroCHS"] = json.loads(f.read())


# The country data of the actions lives in the national annex files
# (data/national_annexes/<COUNTRY>.json); it is merged here, next to the EU data,
# so that ``db["Loads"][...]["Locale"][country]`` keeps working for every reader.
_LOADS_PATH = {"live": ("Live", "Locale"), "seismic": ("Seismic", "Locale"),
               "wind": ("Wind", "locale")}


def _merge_annex_loads(country: str, loads: dict) -> None:
    for kind, data in loads.items():
        parent, key = _LOADS_PATH[kind]
        db["Loads"][parent][key][country] = copy.deepcopy(data)


def _remove_annex_loads(country: str) -> None:
    for parent, key in _LOADS_PATH.values():
        db["Loads"][parent][key].pop(country, None)


for _country in _annex.available_annexes():
    _merge_annex_loads(_country, _annex.get_annex(_country).get("loads", {}))


def __getattr__(name: str) -> object:
    """Build the deprecated ``dbobj`` only when it is asked for (PEP 562)."""
    if name == "dbobj":
        warnings.warn(
            "eurocodepy.dbobj is deprecated and will be removed in 2028; "
            "use dictionary access on eurocodepy.db instead, "
            'e.g. db["Materials"]["Timber"]["Grade"]["C24"]["fcd"]. '
            "It is a snapshot of the database at the time it is requested.",
            DeprecationWarning, stacklevel=2)
        return __dict2obj(db)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


Materials = db["Materials"]

ReinforcementMaterial = db["Materials"]["Reinforcement"]
ReinforcementGrades = ReinforcementMaterial["Grade"]
ReinforcementBars = ReinforcementMaterial["Rebars"]
ReinforcementParams = ReinforcementMaterial["Parameters"]

ConcreteMaterial = db["Materials"]["Concrete"]
ConcreteGrades = ConcreteMaterial["Grade"]
ConcreteParams = ConcreteMaterial["Parameters"]

PrestressMaterial = db["Materials"]["Prestress"]
PrestressGrades = PrestressMaterial["Grade"]
PrestressParams = PrestressMaterial["Parameters"]

TimberMaterial = db["Materials"]["Timber"]
TimberGrades = TimberMaterial["Grade"]
TimberParams = TimberMaterial["Parameters"]
TimberLoadDuration = TimberMaterial["LoadDuration"]
TimberServiceClasses = TimberMaterial["ServiceClasses"]

SteelMaterial = db["Materials"]["Steel"]
SteelGrades = SteelMaterial["Grade"]
SteelParams = SteelMaterial["Parameters"]

Bolts = db["Materials"]["Bolts"]
BoltGrades = Bolts["Grade"]
BoltDiameters = Bolts["Diameters"]

SteelIProfiles = db["SteelProfiles"]["EuroI"]
SteelSHSProfiles = db["SteelProfiles"]["EuroSHS"]
SteelRHSProfiles = db["SteelProfiles"]["EuroRHS"]
SteelCHSProfiles = db["SteelProfiles"]["EuroCHS"]

Loads = db["Loads"]
WindLoads = Loads["Wind"]
DeadLoads = Loads["Dead"]
SeismicLoads = Loads["Seismic"]


# ---------------------------------------------------------------------------
# Edition-aware access (additive; does not change any of the module-level
# convenience variables above, which keep resolving to the "2004" edition by
# omission, exactly as before this section was added).
# ---------------------------------------------------------------------------


def _deep_merge(existing: dict, value: dict) -> None:
    """Recursively merge ``value`` into ``existing`` (in place, value wins).

    Unlike ``dict.update``, a nested dict in ``value`` patches only the keys
    it contains at every level, instead of replacing the whole nested
    sub-dict -- e.g. ``{"C20_25": {"Ecm": 28847.6}}`` merged into
    ``{"C20_25": {"fck": 20.0, "Ecm": 30000.0, ...}}`` updates only ``Ecm``
    and leaves ``fck`` and every other sibling field untouched.
    """
    for key, val in value.items():
        if isinstance(val, dict) and isinstance(existing.get(key), dict):
            _deep_merge(existing[key], val)
        else:
            existing[key] = val


def _set_by_dotpath(target: dict, path: str, value: object) -> None:
    """Set ``value`` at a dot-notation ``path`` inside ``target`` (in place).

    Intermediate dicts are created if missing. If the existing value at the
    final key is itself a dict and ``value`` is also a dict, they are
    deep-merged (see ``_deep_merge``) instead of replacing the whole
    sub-dict, so an override can patch a single field (e.g. a single grade's
    ``Ecm``) without wiping out sibling fields (e.g. ``fck``) or sibling
    grades that were not meant to change.
    """
    keys = path.split(".")
    node = target
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    last = keys[-1]
    existing = node.get(last)
    if isinstance(existing, dict) and isinstance(value, dict):
        _deep_merge(existing, value)
    else:
        node[last] = value


def resolve_edition(eurocode: str, edition: str | None = None) -> str | None:
    """Return the edition name that ``edition`` resolves to.

    ``None`` resolves to the edition marked ``"default": true`` for that
    eurocode, or to ``None`` when ``Editions`` has no entry for it (the base,
    "2004"-equivalent data). A name that is not registered is returned as
    given, so callers can tell it apart from the default.
    """
    if edition is not None:
        return edition
    editions = db.get("Editions", {}).get(eurocode, {})
    return next((e for e, v in editions.items() if v.get("default")), None)


def register_annex(source: object, *, replace: bool = False) -> str:
    """Register a national annex (a JSON file or a dict, see :mod:`eurocodepy.annex`).

    Its ``loads`` become available next to the EU ones (``wind_get_params``,
    ``seismic_get_params``, EC1/EC7/EC8) and its ``editions`` patches through the
    ``annex=`` argument. Returns the country code.
    """
    country = _annex.register_annex(source, replace=replace)
    _remove_annex_loads(country)
    _merge_annex_loads(country, _annex.get_annex(country).get("loads", {}))
    return country


def unregister_annex(country: str) -> None:
    """Remove a national annex and its loads from the database."""
    _annex.unregister_annex(country)
    _remove_annex_loads(str(country).strip().upper())


available_annexes = _annex.available_annexes
get_annex = _annex.get_annex


def get_edition_data(eurocode: str, edition: str | None = None,
                     annex: str | None = None) -> dict:
    """Return the ``Materials`` dict resolved for the requested edition and annex.

    Applies the deltas in ``Editions.<eurocode>.<edition>.overrides`` on top
    of a deep copy of ``db["Materials"]``, then those of the national annex
    (``editions.<eurocode>.<edition>.overrides`` of its file). Never mutates or
    returns a reference to the shared global ``db`` state.

    Parameters
    ----------
    eurocode:
        Key into ``db["Editions"]``, e.g. ``"ec2"``, ``"ec3"``, ``"ec5"``.
    edition:
        Edition name, e.g. ``"2004"`` or ``"2023"``. If ``None``, the
        edition marked ``"default": true`` for that eurocode is used. If
        there is no ``Editions`` entry for this eurocode at all (e.g. an
        older ``eurocodes.json`` without the ``Editions`` section, or an
        eurocode that has not been given any edition overrides yet), the
        base ``Materials`` dict is returned unchanged — identical to
        today's behaviour before this function existed.
    annex:
        Country code of a national annex (``"PT"``); ``None`` is the values
        recommended by the Eurocode. An unknown code raises ``ValueError``.

    Returns
    -------
    dict
        A standalone deep copy of ``Materials`` with the requested
        edition's overrides (and the annex's) applied (if any).
    """
    base = copy.deepcopy(db["Materials"])
    editions = db.get("Editions", {}).get(eurocode, {})
    edition = resolve_edition(eurocode, edition)
    if edition is not None and edition in editions:
        for path, value in editions[edition].get("overrides", {}).items():
            # a copy: lists and dicts of the override must not be shared with the
            # global database, or editing the result would edit it
            _set_by_dotpath(base, path, copy.deepcopy(value))
    if annex is not None:
        patch = _annex.get_edition_patch(annex, eurocode, edition)
        for path, value in patch.get("overrides", {}).items():
            _set_by_dotpath(base, path, value)
    return base


def get_edition_params(eurocode: str, section: str, edition: str | None = None,
                       annex: str | None = None) -> dict:
    """Return a non-material parameter section for one eurocode edition.

    Some edition-specific design parameters are not material properties (so
    they do not belong under ``Materials``) -- e.g. the punching-shear
    ``dmax``/``eta_sys`` factors of EN 1992-1-1:2023 SS8.4. These live at
    ``db["Editions"][eurocode][edition][section]`` (a sibling of
    ``"overrides"``), and this accessor resolves them the same way as
    :func:`get_edition_data`: same default-edition lookup, and an empty dict
    (never an exception) when the eurocode, edition, or section is absent --
    e.g. calling this for the "2004" edition, which has no ``punch_params``
    section, simply returns ``{}``.

    With ``annex`` the section of the national annex (same name, same edition) is
    deep-merged over it, so an annex can change one value of a table and leave the
    rest as recommended; it can also supply a section the edition does not have.

    Returns a deep copy, so callers cannot mutate the shared ``db`` state.
    """
    editions = db.get("Editions", {}).get(eurocode, {})
    edition = resolve_edition(eurocode, edition)
    out: dict = {}
    if edition is not None and edition in editions:
        out = copy.deepcopy(dict(editions[edition].get(section, {})))
    if annex is not None:
        patch = _annex.get_edition_patch(annex, eurocode, edition).get(section)
        if patch:
            _deep_merge(out, copy.deepcopy(patch))
    return out


class EurocodeMaterials:
    """Thin, optional, read-only wrapper around an edition-resolved dict.

    This does NOT replace the existing module-level convenience variables
    (``ConcreteParams``, ``SteelGrades``, etc.) — those keep working exactly
    as before. Use this only when you explicitly need a specific edition's
    values, e.g.::

        mats = EurocodeMaterials("ec2", "2023")
        mats.Concrete["Parameters"]["alpha_cc"]
    """

    def __init__(self, eurocode: str, edition: str | None = None,
                 annex: str | None = None) -> None:
        self._eurocode = eurocode
        self._edition = edition
        self._annex = annex
        self._data = get_edition_data(eurocode, edition, annex)

    def __getattr__(self, name: str) -> object:
        try:
            return self._data[name]
        except KeyError as exc:
            msg = f"{self.__class__.__name__!r} object has no attribute {name!r}"
            raise AttributeError(msg) from exc

    def __getitem__(self, key: str) -> object:
        return self._data[key]

    def __repr__(self) -> str:
        return (
            f"EurocodeMaterials(eurocode={self._eurocode!r}, "
            f"edition={self._edition!r}, annex={self._annex!r})"
        )
