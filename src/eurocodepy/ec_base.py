import json
import os
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


def get_prestress() -> dict:
    global database
    database = get_database()
    return database["Eurocodes"]["Materials"]["Prestress"]


def get_rebars() -> dict:
    global database
    database = get_database()
    return database["Eurocodes"]["Materials"]["Rebars"]


if __name__ == "__main__":
    print ("Executing ec_base\n")
    file=open(os.path.join(os.path.dirname(__file__),'eurocodes.json'),'r')
    db = json.loads(file.read())
    # pststeel = get_prestress()
    pststeel = db["Eurocodes"]["Materials"]["Prestress"]
    print(pststeel)

