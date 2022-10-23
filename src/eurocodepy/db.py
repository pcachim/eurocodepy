import json
import os
import pandas as pd
import importlib.resources as pkg_resources


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

def _get_database() -> dict:
    """[summary]
    Returns:
        dict: [description]
    """
    global database
    f = pkg_resources.open_text(__package__, 'eurocodes.json')
    #f = open(filename, "r")
    database = json.loads(f.read())
    return database


def _get_database2() -> dict:
    """[summary]
    Returns:
        dict: [description]
    """
    global database
    f = open(os.path.join(os.path.dirname(__file__),'eurocodes.json'),'r')
    #f = open(filename, "r")
    database = json.loads(f.read())
    return database


def get_eurocodes() -> dict:
    """Gets the euroocodes database
    Returns:
        dict: eurocodes database
    """
    return db["Eurocodes"]


def get_materials() -> dict:
    """Gets all the materials in the database
    Returns:
        dict: all the materials in the database
    """
    return db["Eurocodes"]["Materials"]


def get_timber() -> dict:
    """Gets the timber (solid and glulam) classes
    Returns:
        dict: the timber (solid and glulam) classes
    """
    return db["Eurocodes"]["Materials"]["Timber"]


def get_concrete() -> dict:
    """Gets the concrete classes
    Returns:
        dict: the concrete classes
    """
    return db["Materials"]["Concrete"]["Classes"]


def get_prestress() -> dict:
    """Gets the prestrress steel classes
    Returns:
        dict: the prestrress steel classes
    """
    return db["Eurocodes"]["Materials"]["Prestress"]


def get_reinforcement() -> dict:
    """Gets the reinforcement steel classes
    Returns:
        dict: the reinforcement steel classes
    """
    return db["Eurocodes"]["Materials"]["Reinforcement"]

ConcreteClasses = db["Materials"]["Concrete"]["Classes"]
PrestressClasses = db["Materials"]["Prestress"]["Classes"]
ReinforcementClasses = db["Materials"]["Reinforcement"]["Classes"]
ReinforcementBars = db["Materials"]["Reinforcement"]["Rebars"]
SteelProfiles = db["SteelProfiles"]["Euro"]