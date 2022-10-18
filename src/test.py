import eurocodepy as ec
import json, os
import pandas as pd


def test_database():
    """[summary]
    """
    print ("Testing database\n")
    db = ec.db

    df = pd.DataFrame.from_dict(ec.PrestressClasses)
    print(df)
    print("\n")
    df = pd.DataFrame.from_dict(ec.ReinforcementClasses)
    print(df)
    print("\n")

    print(ec.ConcreteClasses)
    print("\n")
    
    print(pd.DataFrame.from_dict(db["Materials"]["Reinforcement"]["Classes"]))
    print("\n")
    
    fck = ec.ConcreteClasses['C20/25']
    print(fck)


def test_modules():
    asws = ec.ec2.uls.shear.shear_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    asws = ec.ec2.uls.shear_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    asws = ec.ec2.shear_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    param = ec.ec2.bend_params()
    print (param)


if __name__ == "__main__":
    print ("Testing 'eurocodepy'\n")
    test_database()
    test_modules()