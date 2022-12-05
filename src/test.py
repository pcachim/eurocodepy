import eurocodepy as ec
import json, os
import pandas as pd
import numpy as np
import timeit

from eurocodepy.db import SteelProfiles


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

    print(SteelProfiles["I_SECTION"]["IPE200"]["S22POS"])
    # print(pd.DataFrame.from_dict(SteelProofiles["I_SECTION"]["IPE200"]))
    print("\n")
    db2 = ec.db2.Materials.Concrete
    print (db2)


def test_modules():
    asws = ec.ec2.uls.shear.shear_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    asws = ec.ec2.uls.shear_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    asws = ec.ec2.shear_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    param = ec.ec2.bend_params()
    print (param)


def test_ec2_uls_biaxial():
    nxx = np.random.randint(-100, 100, 30000)
    nyy = np.random.randint(-100, 100, 30000)
    nxy = np.random.randint(-100, 100, 30000)
    mxx = np.random.randint(-100, 100, 30000)
    myy = np.random.randint(-100, 100, 30000)
    mxy = np.random.randint(-100, 100, 30000)
    asx = ec.ec2.as_shell(nxx, nyy, nxy, mxx, myy, mxy, 0.04, 0.3)
    #asx = ec.ec2.uls.biaxial.as_shell(100, -100, 0, 0, 100, 0, 0.04, 0.3)
    asx = np.stack( asx, axis=0 )
    print(asx)
    print(asx[6, 2])


def test_utils_stress():
    # test stress module
    print("\nTest stress module: principals:")
    eval, evec = ec.utils.stress.principals(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
    print(eval)
    print(evec)
    print("\nTest stress module: principal_vectors:")
    evec = ec.utils.stress.principal_vectors(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
    print(evec)
    
    print("\nTest stress module: stress invariants:")
    u = ec.stress.invariants(3.0, 2.0, -1.0, 0.3, -0.4, 0.5)
    print (u)

if __name__ == "__main__":
    print ("Testing 'eurocodepy'\n")
    starttime = timeit.default_timer()
    test_database()
    test_modules()
    print("\n")
    #print(ec.ec2.uls.db)
    test_ec2_uls_biaxial()
    print("\n")
    test_utils_stress()
    print("\nTotal execution time is :", timeit.default_timer() - starttime)
    print("\n")
    
