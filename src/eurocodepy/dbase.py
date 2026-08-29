# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

import copy
import json
from pathlib import Path

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
- Includes functions for converting dictionaries to objects for attribute-style access.

Usage Examples:
---------------
- Dictionary access:
    db["Materials"]["Timber"]["Grade"]["C24"]["fcd"]
- Attribute access:
    dbobj.Materials.Timber.Grade.C24.fcd

Available Variables:
--------------------
- db: Main Eurocodes database as a dictionary.
- dbobj: Main Eurocodes database as an object (attribute access).
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

dbobj = __dict2obj(db)

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


def get_edition_data(eurocode: str, edition: str | None = None) -> dict:
    """Return the ``Materials`` dict resolved for the requested edition.

    Applies the deltas in ``Editions.<eurocode>.<edition>.overrides`` on top
    of a deep copy of ``db["Materials"]``. Never mutates or returns a
    reference to the shared global ``db`` state.

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

    Returns
    -------
    dict
        A standalone deep copy of ``Materials`` with the requested
        edition's overrides applied (if any).
    """
    base = copy.deepcopy(db["Materials"])
    editions = db.get("Editions", {}).get(eurocode, {})
    if edition is None:
        edition = next((e for e, v in editions.items() if v.get("default")), None)
    if edition is None or edition not in editions:
        return base
    for path, value in editions[edition].get("overrides", {}).items():
        _set_by_dotpath(base, path, value)
    return base


def get_edition_params(eurocode: str, section: str, edition: str | None = None) -> dict:
    """Return a non-material parameter section for one eurocode edition.

    Some edition-specific design parameters are not material properties (so
    they do not belong under ``Materials``) -- e.g. the punching-shear
    ``dmax``/``eta_sys`` factors of prEN 1992-1-1:2023 SS8.4. These live at
    ``db["Editions"][eurocode][edition][section]`` (a sibling of
    ``"overrides"``), and this accessor resolves them the same way as
    :func:`get_edition_data`: same default-edition lookup, and an empty dict
    (never an exception) when the eurocode, edition, or section is absent --
    e.g. calling this for the "2004" edition, which has no ``punch_params``
    section, simply returns ``{}``.

    Returns a shallow copy, so callers cannot mutate the shared ``db`` state.
    """
    editions = db.get("Editions", {}).get(eurocode, {})
    if edition is None:
        edition = next((e for e, v in editions.items() if v.get("default")), None)
    if edition is None or edition not in editions:
        return {}
    return dict(editions[edition].get(section, {}))


class EurocodeMaterials:
    """Thin, optional, read-only wrapper around an edition-resolved dict.

    This does NOT replace the existing module-level convenience variables
    (``ConcreteParams``, ``SteelGrades``, etc.) — those keep working exactly
    as before. Use this only when you explicitly need a specific edition's
    values, e.g.::

        mats = EurocodeMaterials("ec2", "2023")
        mats.Concrete["Parameters"]["alpha_cc"]
    """

    def __init__(self, eurocode: str, edition: str | None = None) -> None:
        self._eurocode = eurocode
        self._edition = edition
        self._data = get_edition_data(eurocode, edition)

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
            f"edition={self._edition!r})"
        )
