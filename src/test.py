import eurocodepy as eurocode
from eurocodepy import ec_base as ec
import json, os
import pandas as pd

def test_database():
    print ("Testing database\n")

    df = pd.DataFrame.from_dict(ec.PrestressClasses)
    print(df)
    print("\n")
    df = pd.DataFrame.from_dict(ec.ReinforcementClasses)
    print(df)
    print("\n")

    print(ec.ConcreteClasses)
    print("\n")
    
    print(ec.Materials)
    print("\n")
    
if __name__ == "__main__":
    print ("Testing 'eurocodepy'\n")
    test_database()