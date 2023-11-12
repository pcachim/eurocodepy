from math import log

c_season = 1.0
c_dir = 1.0
k_1 = 1.0 # coeficiente de turbulência
rho = 1.25 # kg/m3
z0 = {"0": 0.003, "I": 0.01, "II": 0.05, "III": 0.3, "IV": 1}
zmin = {"0": 1, "I": 1, "II": 2, "III": 5, "IV": 10}


def s_coef(x: float, z: float, H: float, Lu: float, Ld: float=-1) -> float:
    orography_type = 'hill' if Ld > 0 else 'cliff'
    phi = H/Lu
    Le = H/0.3 if phi >= 0.3 else Lu
    x_Lu = x/Lu
    z_Le = z/Le

    s = 0.0
    if x_Lu <= 0:
        if -1.5 < x_Lu and z_Le < 2:
            A = 0.1552*z_Le**4 -0.8575*z_Le**3 +1.8133*z_Le**2 -1.9115*z_Le +1.0124
            B = 0.3542*z_Le**2 -1.0577*z_Le+2.6456
            s = A*exp(B*x_Lu)
        elif x_Lu < -1.5 or z_Le >= 2:
            s = 0.0
    else:
        if orography_type == 'hill':
            x_Ld = x/Ld
            if x_Ld < 2 and z_Le < 2:
                A = 0.1552*z_Le**4 -0.8575*z_Le**3 +1.8133*z_Le**2 -1.9115*z_Le +1.0124
                B = -0.3056*z_Le**2 +1.0212*z_Le -1.7637
                s = A*exp(B*x_Lu)
            elif x_Ld >= 2 or z_Le >= 2:
                s = 0.0
        else: # orography_type == 'cliff'
            x_Le = x/Le
            if z_Le < 0.1: z_Le = 0.1
            if (0.1 < x_Le < 3.5) and (z_Le < 2):
                logzle = log10(z_Le)
                A = -1.3420*logzle**3 -0.8222*logzle**2 +0.4609*logzle -0.0791
                B = -1.0196*logzle**3 -0.8910*logzle**2 +0.5343*logzle -0.1156
                C =  0.8030*logzle**3 +0.4236*logzle**2 -0.5738*logzle +0.1606
                logxle = log10(x/Le)
                s = A*logxle**2 + B*logxle + C
            elif (0.1 >= x_Le) and (z_Le < 2):
                s1 = 0.1552*z_Le**4 -0.8575*z_Le**3 +1.8133*z_Le**2 -1.9115*z_Le +1.0124
                logzle = log10(z_Le)
                A = -1.3420*logzle**3 -0.8222*logzle**2 +0.4609*logzle -0.0791
                B = -1.0196*logzle**3 -0.8910*logzle**2 +0.5343*logzle -0.1156
                C =  0.8030*logzle**3 +0.4236*logzle**2 -0.5738*logzle +0.1606
                logxle = log10(0.1/Le)
                s2 = A*logxle**2 + B*logxle + C
                s = s1 + x_Le*(s2-s1)/0.1           
            elif x_Le >= 3.5 or z_Le >= 2:
                s = 0.0
    return s


def c_0(z: float, x: float=0, H: float=0, Lu: float=10, Ld: float=10) -> float:
    """Calculates the orography factor, taken as 1,0
    Args:
        z (float): vertical distance

    Returns:
        float: orography factor
    """
    phi = H/Lu
    if phi < 0.05: return 1.0
    s = s_coef(x, z, H, Lu, Ld)
    return 1.0+2.0*s*phi if phi < 0.3 else 1.0+0.6*s


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
