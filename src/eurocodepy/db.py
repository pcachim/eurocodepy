import json
import os
import pandas as pd
import importlib.resources as pkg_resources

database = {}
db = json.loads(open(os.path.join(os.path.dirname(__file__),'eurocodes.json'),'r').read())["Eurocodes"]
db["SteelProfiles"]["Euro"] = json.loads(open(os.path.join(os.path.dirname(__file__),'euro.prof.json'),'r').read())

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
    """
    """
    return _get_database2()["Eurocodes"]


def get_materials() -> dict:
    """[summary]

    Returns:
        dict: [description]
    """
    global database
    database = _get_database2()
    return database["Eurocodes"]["Materials"]


def get_timber() -> dict:
    """[summary]

    Returns:
        dict: [description]
    """
    global database
    database = _get_database2()
    return database["Eurocodes"]["Materials"]["Timber"]


def get_concrete() -> dict:
    """[summary]

    Returns:
        dict: [description]
    """
    global database
    database = _get_database2()
    return database["Eurocodes"]["Materials"]["Concrete"]


def get_prestress() -> dict:
    """[summary]

    Returns:
        dict: [description]
    """
    global database
    database = _get_database2()
    return database["Eurocodes"]["Materials"]["Prestress"]


def get_reinforcement() -> dict:
    """[summary]

    Returns:
        dict: [description]
    """
    global database
    database = _get_database2()
    return database["Eurocodes"]["Materials"]["Reinforcement"]

ConcreteClasses = db["Materials"]["Concrete"]["Classes"]
PrestressClasses = db["Materials"]["Prestress"]["Classes"]
ReinforcementClasses = db["Materials"]["Reinforcement"]["Classes"]
ReinforcementBars = db["Materials"]["Reinforcement"]["Rebars"]
SteelProofiles = db["SteelProfiles"]["Euro"]