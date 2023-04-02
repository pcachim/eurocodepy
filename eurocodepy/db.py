import json
import os
import pandas as pd
import importlib.resources as pkg_resources

"""This module contains the database of the Eurocodes

For convenience, the database is loaded as a dictionary and as a class. It allows to access the database in two ways:
1. Using the dictionary db (e.g. db["Materials"]["Timber"]["Classes"]["C24"]["fcd"])
2. Using the class dbase (e.g. dbase.Materials.Timber.Classes.C24.fcd)

There are also some functions to access the database:
- get_eurocodes(): returns the whole database
- get_materials(): returns the materials database
- get_timber(): returns the timber database
- get_timber_classes(): returns the timber classes database
- get_concrete(): returns the concrete database
- get_prestress(): returns the prestress database
- get_reinforcement(): returns the reinforcement database
- get_steel(): returns the steel database

And some variables:
- Eurocodes: the eurocodes database
- Concrete: the concrete database
- ConcreteClasses: the concrete classes database
- ConcreteParams: the concrete parameters database
- Reinforcement: the reinforcement database
- ReinforcementClasses: the reinforcement classes database
- ReinforcementBars: the reinforcement bars database
- ReinforcementParams: the reinforcement parameters database
- Steel: the steel database
- SteelParams: the steel parameters database
- SteelProfiles: the steel profiles database
- Bolts: the bolts database
- BoltClasses: the bolts classes database
- BoltDiameters: the bolts diameters database
- Prestress: the prestress database
- PrestressClasses: the prestress classes database
- PrestressParams: the prestress parameters database
- Timber: the timber database
- TimberClasses: the timber classes database
- TimberParams: the timber parameters database
- Materials: the materials database

"""

# Turns a dictionary into a class
# declaringa a class
class obj:
    # constructor
    def __init__(self, dict1):
        self.__dict__.update(dict1)


def dict2obj(dict1):
    # using json.loads method and passing json.dumps
    # method and custom object hook as arguments
    return json.loads(json.dumps(dict1), object_hook=obj)


database = {}
dirname = os.path.dirname(__file__)
db = json.loads(open(os.path.join(dirname,'eurocodes.json'),'r').read())["Eurocodes"]
db["SteelProfiles"]["Euro"] = json.loads(open(os.path.join(dirname,'prof_euro.json'),'r').read())

dbase = dict2obj(db)

Materials = db["Materials"]

Reinforcement = db["Materials"]["Reinforcement"]
ReinforcementClasses = Reinforcement["Classes"]
ReinforcementBars = Reinforcement["Rebars"]
ReinforcementParams = Reinforcement["Parameters"]
#ReinforcementClasses = db["Materials"]["Reinforcement"]["Classes"]

Concrete = db["Materials"]["Concrete"]
ConcreteClasses = Concrete["Classes"]
ConcreteParams = Concrete["Parameters"]

Prestress = db["Materials"]["Prestress"]
PrestressClasses = Prestress["Classes"]
PrestressParams = Prestress["Parameters"]

Timber = db["Materials"]["Timber"]
TimberClasses = Timber["Classes"]
TimberParams = Timber["Parameters"]
TimberLoadDuration = Timber["LoadDuration"]

Steel = db["Materials"]["Steel"]
SteelClasses = Steel["Classes"]
SteelParams = Steel["Parameters"]

Bolts = db["Materials"]["Bolts"]
BoltClasses = Bolts["Classes"]
BoltDiameters = Bolts["Diameters"]

SteelProfiles = db["SteelProfiles"]["Euro"]

