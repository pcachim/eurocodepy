import pandas as pd
import numpy as np
import timeit

from src import eurocodepy as ec
SteelProfiles = ec.SteelProfiles
db = ec.db
# import eurocodepy as ec
# from eurocodepy.db import SteelProfiles


def test_database():
    """[summary]
    """
    print ("Testing database\n")
    db = ec.db

    print ("\nPrestress classes\n")
    df = pd.DataFrame.from_dict(ec.PrestressClasses)
    print(df)
    print("\nReinforccement classes\n")
    df = pd.DataFrame.from_dict(ec.ReinforcementClasses)
    print(df)
    
    print("\nConcrete classes\n")
    print(ec.ConcreteClasses)

    print("\nReinforcement classes\n")    
    print(pd.DataFrame.from_dict(db["Materials"]["Reinforcement"]["Classes"]))
    
    print("\nConcrete C20/25")
    fck = ec.ConcreteClasses['C20/25']
    print(fck)

    print("\nSteel profile IPE200\n")    
    print(SteelProfiles["I_SECTION"]["IPE200"])
    # print(pd.DataFrame.from_dict(SteelProofiles["I_SECTION"]["IPE200"]))
    print("\nConcrete classes")
    db2 = ec.dbase.Materials.Concrete.Classes
    print (db2)
    print("\nEnd testing databasde\n\n")


def test_modules():
    print("Testing modules\n")
    asws = ec.ec2.uls.shear.calc_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    asws = ec.ec2.uls.calc_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    asws = ec.ec2.calc_asws(0.3, 0.5, 25, 1.5, 500, 1.15, 2.5, 300, 1.0)
    print (asws)
    param = ec.ec2.get_bend_params()
    print (param)


def test_ec2_uls_biaxial():
    nxx = np.random.randint(-100, 100, 30000)
    nyy = np.random.randint(-100, 100, 30000)
    nxy = np.random.randint(-100, 100, 30000)
    mxx = np.random.randint(-100, 100, 30000)
    myy = np.random.randint(-100, 100, 30000)
    mxy = np.random.randint(-100, 100, 30000)
    asx = ec.ec2.calc_reinf_shell(nxx, nyy, nxy, mxx, myy, mxy, 0.04, 0.3)
    #asx = ec.ec2.uls.biaxial.as_shell(100, -100, 0, 0, 100, 0, 0.04, 0.3)
    asx = np.stack( asx, axis=0 )
    print("Testing forces in shell elements for reinforcement")
    print(asx)
    print("a single element")
    print(asx[6, 2])


def test_utils_stress():
    # test stress module
    print("\nTest stress module: principals:\n")
    eval, evec = ec.utils.stress.principals(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
    print(eval)
    print(evec)
    print("\nTest stress module: principal_vectors:\n")
    evec = ec.utils.stress.principal_vectors(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
    print(evec)
    
    print("\nTest stress module: stress invariants:\n")
    u = ec.stress.invariants(3.0, 2.0, -1.0, 0.3, -0.4, 0.5)
    print (u)


def test_rcbeam():
    # test RCBeam class
    print("\nTest RCBeam:\n")
    beam = ec.ec2.uls.RCBeam(0.3, 0.5, at=0.05, ac=0.05, conc="C30/37", reinf="A500NR")
    asl, asc, a, epst, epsc = beam.calcBending(100.0)
    print (f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}\n")
    asl, asc, a, epst, epsc = beam.calcBending(500.0)
    print (f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}\n")
    beam = ec.ec2.uls.RCBeam(0.3, 0.5, at=0.05, ac=0.05, conc="C90/105", reinf="A500NR")
    asl, asc, a, epst, epsc = beam.calcBending(700.0)
    print (f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}\n")
    return


def test_wind():
    print("Testing wind")
    c0 = ec.ec1.wind.c_0(10.0, 0.0, 10.0, 10.0, 1000.0)
    print(f"c_0 = {c0}")
    

def test_seismic():
    print("Testing seismic")
    params = ec.ec8.spectrum.get_spec_params("PT", "PT-1", "ii", "A", "1.3")
    print(f"params = {params}")

if __name__ == "__main__":

    import requests
    def get_altitude_OSM(latitude: float, longitude: float)->int:
        # Make a request to the Open-Elevation API
        url = f'https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}'
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract the altitude (elevation) from the response
            altitude = data['results'][0]['elevation']
            
            # st.write(f'Altitude at ({latitude}, {longitude}): {altitude} meters')
        else:
            print(f"Error: Unable to fetch data from Open-Elevation API. Status code: {response.reason}")
            
        return altitude

    print ("Testing 'eurocodepy'\n")
    starttime = timeit.default_timer()
    alti = get_altitude_OSM(45.0, 7.0)
    print(f"Altitude at (45.0, 7.0): {alti} meters")

    # test_database()
    # # test_modules()
    # print("\n")
    # #print(ec.ec2.uls.db)
    # test_ec2_uls_biaxial()
    # print("\n")
    # test_utils_stress()
    
    # cr = ec.ec2.crack.iscracked_annexLL(2.2, 25.0, 2.201, 0.0, 0.0, 0.0, 0.0, 0.0)
    # print(f"Is cracked: {cr}")
    
    # test_rcbeam()
    test_wind()
    test_seismic()

    print("\nTotal execution time is :", timeit.default_timer() - starttime)
    print("\n")
    
