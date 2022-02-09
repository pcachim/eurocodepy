import json
import os
import pandas as pd
import importlib.resources as pkg_resources

database = {}

def get_database() -> dict:
    global database
    f = pkg_resources.open_text(__package__, 'eurocodes.json')
    #f = open(filename, "r")
    database = json.loads(f.read())
    return database


def get_database2() -> dict:
    global database
    f = open(os.path.join(os.path.dirname(__file__),'eurocodes.json'),'r')
    #f = open(filename, "r")
    database = json.loads(f.read())
    return database


def get_materials() -> dict:
    global database
    database = get_database2()
    return database["Eurocodes"]["Materials"]


def get_timber() -> dict:
    global database
    database = get_database2()
    return database["Eurocodes"]["Materials"]["Timber"]


def get_concrete() -> dict:
    global database
    database = get_database2()
    return database["Eurocodes"]["Materials"]["Concrete"]


def get_prestress() -> dict:
    global database
    database = get_database2()
    return database["Eurocodes"]["Materials"]["Prestress"]


def get_reinforcement() -> dict:
    global database
    database = get_database2()
    return database["Eurocodes"]["Materials"]["Reinforcement"]

Materials = get_materials()
ConcreteClasses = pd.DataFrame.from_dict(get_concrete()["Classes"]) 
PrestressClasses = get_prestress()["Classes"]
ReinforcementClasses = get_reinforcement()["Classes"]
ReinforcementBars = get_reinforcement()["Rebars"]