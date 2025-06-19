# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

import json
from pathlib import Path

"""This module contains the database of the Eurocodes

For convenience, the database is loaded as a dictionary and as a class.
It allows to access the database in two ways:
1. Using the dictionary db (e.g. db["Materials"]["Timber"]["Grade"]["C24"]["fcd"])
2. Using the class dbase (e.g. dbase.Materials.Timber.Grades.C24.fcd)

There are also some functions to access the database:
- get_eurocodes(): returns the whole database
- get_materials(): returns the materials database
- get_timber(): returns the timber database
- get_timber_Grades(): returns the timber Grades database
- get_concrete(): returns the concrete database
- get_prestress(): returns the prestress database
- get_reinforcement(): returns the reinforcement database
- get_steel(): returns the steel database

And some variables:
- Eurocodes: the eurocodes database
- Concrete: the concrete database
- ConcreteGrades: the concrete Grades database
- ConcreteParams: the concrete parameters database
- Reinforcement: the reinforcement database
- ReinforcementGrades: the reinforcement Grades database
- ReinforcementBars: the reinforcement bars database
- ReinforcementParams: the reinforcement parameters database
- Steel: the steel database
- SteelParams: the steel parameters database
- SteelProfiles: the steel profiles database
- Bolts: the bolts database
- BoltGrades: the bolts Grades database
- BoltDiameters: the bolts diameters database
- Prestress: the prestress database
- PrestressGrades: the prestress Grades database
- PrestressParams: the prestress parameters database
- Timber: the timber database
- TimberGrades: the timber Grades database
- TimberParams: the timber parameters database
- Materials: the materials database

"""


def dict2obj(dict1: dict) -> str:
    """Convert a dictionary to a custom object using json.loads and object_hook.

    Args:
        dict1: The input dictionary.

    Returns:
        A custom object representing the dictionary.

    """

    class Obj:
        """Custom object class used as the object_hook."""

        def __init__(self, dict1: dict) -> None:
            """Update the object's __dict__ with the dictionary."""
            self.__dict__.update(dict1)

    return json.loads(json.dumps(dict1), object_hook=Obj)


# db = {}
base_path = Path(__file__).parent / "data"
base_name = base_path / "eurocodes.json"
with base_name.open(encoding="utf-8") as f:
    db = json.loads(f.read())["Eurocodes"]
prof_name = base_path / "prof_euro.json"
with prof_name.open(encoding="utf-8") as f:
    db["SteelProfiles"]["Euro"] = json.loads(f.read())
prof_name = base_path / "i_profiles_euro.json"
with prof_name.open(encoding="utf-8") as f:
    db["SteelProfiles"]["EuroI"] = json.loads(f.read())

dbobj = dict2obj(db)

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

Steel = db["Materials"]["Steel"]
SteelGrades = Steel["Grade"]
SteelParams = Steel["Parameters"]

Bolts = db["Materials"]["Bolts"]
BoltGrades = Bolts["Grade"]
BoltDiameters = Bolts["Diameters"]

SteelProfiles = db["SteelProfiles"]["Euro"]
SteelIProfiles = db["SteelProfiles"]["EuroI"]

Loads = db["Loads"]
WindLoads = Loads["Wind"]
DeadLoads = Loads["Dead"]
SeismicLoads = Loads["Seismic"]


def wind_get_params(code: str = "PT", zone: str = "ZonaA",
                    terrain: str = "II") -> tuple:
    """Return the wind parameters for the specified code.

    Returns:
        tuple: A tuple containing (vb0, zmin, z0), where vb0 is the base wind velocity,
        zmin is the minimum height, and z0 is the terrain roughness length.

    """
    wind = WindLoads["locale"][code]
    vb0 = wind["base_velocity"][zone]["vb0"]
    z0 = wind["terrain"][terrain]["z0"]
    zmin = wind["terrain"][terrain]["zmin"]
    return vb0, zmin, z0
