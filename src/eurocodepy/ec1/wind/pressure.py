from math import log

c_season = 1.0
c_dir = 1.0
k_1 = 1.0 # coeficiente de turbulência
rho = 1.25 # kg/m3
z0 = {"0": 0.003, "I": 0.01, "II": 0.05, "III": 0.3, "IV": 1}
zmin = {"0": 1, "I": 1, "II": 2, "III": 5, "IV": 10}


def v_b(vb_0: float) -> float:
    """Calculates the basic wind velocity 

    Args:
        vb_0 (float): fundamental value of the basic wind velocity

    Returns:
        float: basic wind velocity 
    """
    return c_season * c_dir * vb_0


def c_r(z: float, zone: str) -> float:
    """ Calculate the roughness factor

    Args:
        z (float): vertical distance
        zone (str): the terrain category

    Returns:
        float: the roughness factor
    """
    k_r = 0.19*((z0[zone]/z0["II"])**0.07)
    zeff = z if z >= zmin[zone] else zmin[zone]
    return k_r * log(zeff/z0[zone])


def c_0(z: float) -> float:
    """Calculates the orography factor, taken as 1,0
    Args:
        z (float): vertical distance

    Returns:
        float: orography factor
    """
    return 1.0


def v_m(z: float, vb: float, zone: str) -> float:
    """ Calculates the mean wind velocity, vm(z), at a height z above the terrain.
    Depends on the terrain roughness and orography and on the basic wind velocity.

    Args:
        z (float): vertical distance
        vb (float): basic wind velocity
        zone (str): the terrain category

    Returns:
        float: mean wind velocity, vm(z) 
    """
    return c_r(z, zone) * c_0(z) * vb


def I_v(z: float, zone: str) -> float:
    """Calculates the turbulence intensity, Iv(z), at height z.
    It is defined as the standard deviation of the turbulence divided by the mean wind velocity.

    Args:
        z (float): vertical distance
        zone (str): the terrain category

    Returns:
        float: turbulence intensity
    """
    zeff = z if z >= zmin[zone] else zmin[zone]
    Iv = k_1 / c_0(z) / log(zeff/z0[zone])
    return Iv


def q_p(z: float, vb0: float, zone: str) -> float:
    """Calcculates the peak velocity pressure, qp(z), at height z, 
    which includes mean and short-term velocity fluctuations.

    Args:
        z (float): vertical distance
        vb0 (float): fundamental value of the basic wind velocity
        zone (str): the terrain category

    Returns:
        float: peak velocity pressure
    """
    zone = str.upper(zone)
    v = v_m(z, v_b(vb0), zone)
    #v = c_r(z, zone) * c_0(z) * vb0
    qp = 0.5 * (1.0 + 7*I_v(z, zone)) * v**2 * rho
    return qp