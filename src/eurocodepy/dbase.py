# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

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

Reinforcement = db["Materials"]["Reinforcement"]
ReinforcementGrades = Reinforcement["Grade"]
ReinforcementBars = Reinforcement["Rebars"]
ReinforcementParams = Reinforcement["Parameters"]

Concrete = db["Materials"]["Concrete"]
ConcreteGrades = Concrete["Grade"]
ConcreteParams = Concrete["Parameters"]

Prestress = db["Materials"]["Prestress"]
PrestressGrades = Prestress["Grade"]
PrestressParams = Prestress["Parameters"]

Timber = db["Materials"]["Timber"]
TimberGrades = Timber["Grade"]
TimberParams = Timber["Parameters"]
TimberLoadDuration = Timber["LoadDuration"]
TimberServiceClasses = Timber["ServiceClasses"]

Steel = db["Materials"]["Steel"]
SteelGrades = Steel["Grade"]
SteelParams = Steel["Parameters"]

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
