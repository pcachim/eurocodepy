import json
import importlib.resources as pkg_resources

database = {}

def get_database() -> dict:
    global database
    f = pkg_resources.open_text(__package__, 'eurocodes.json')
    #f = open(filename, "r")
    database = json.loads(f.read())
    return database

def get_timber() -> dict:
    global database
    database = get_database()
    return database["Eurocodes"]["Materials"]["Timber"]

def get_concrete() -> dict:
    global database
    database = get_database()
    return database["Eurocodes"]["Materials"]["Concrete"]

