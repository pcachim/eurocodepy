from math import log10, log, exp


# z0 = {"EU": {"0": 0.003, "I": 0.01, "II": 0.05, "III": 0.3, "IV": 1},
#       "PT": {"I": 0.005, "II": 0.05, "III": 0.3, "IV": 1}}
# zmin = {"EU": {"0": 1, "I": 1, "II": 2, "III": 5, "IV": 10},
#         "PT": {"I": 1, "II": 3, "III": 8, "IV": 15}}

# zz0 = z0["EU"]
# zzmin = zmin["EU"]


def s_coef(x: float, z: float, H: float, Lu: float, Ld: float=1000) -> float:
    """_summary_

    Args:
        x (float): horizontal distance
        z (float): vertical distance
        H (float): height of the hill/cliff
        Lu (float): length of the hill/cliff
        Ld (float, optional): length of the cliff. Defaults to 1000, meaning it's a cliff.
    Returns:
        float: _description_
    """
    phi0 = H/Ld
    phi = H/Lu
    
    if phi < 0.05: return 0.0
    orography_type = 'hill' if phi0 > 0.05 else 'cliff'

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

def c_o(z: float, x: float=0, H: float=0, Lu: float=10, Ld: float=1000) -> float:
    """Calculates the orography factor.
    Args:
        z (float): vertical distance
        x (float, optional): horizontal distance. Defaults to 0.
        H (float, optional): height of the hill/cliff. Defaults to 0.
        Lu (float, optional): length of the hill/cliff. Defaults to 10.
        Ld (float, optional): length of the cliff. Defaults to 1000, meaning it's a cliff.

    Returns:
        float: orography factor
    """
    phi = H/Lu
    if phi < 0.05: return 1.0
    s = s_coef(x, z, H, Lu, Ld)
    return 1.0+2.0*s*phi if phi < 0.3 else 1.0+0.6*s

def c_r(z: float, z_min: float, z_0: float, z_0II: float) -> float:
    """ Calculate the roughness factor

    Args:
        z (float): vertical distance.
        z_min (float, optional): minimum height.
        z_0 (float, optional): roughness length.
        z_OII (float, optional): roughness length for terrain II.

    Returns:
        float: the roughness factor
    """
    k_r = 0.19*((z_0/z_0II)**0.07)
    zeff = z if z >= z_min else z_min
    return k_r * log(zeff/z_0)

def v_b(vb_0: float, c_season: float=1.0, c_dir: float=1.0) -> float:
    """Calculates the basic wind velocity 

    Args:
        vb_0 (float): fundamental value of the basic wind velocity
        c_season (float, optional): seasonal factor. Defaults to 1.0.
        c_dir (float, optional): directional factor. Defaults to 1.0.

    Returns:
        float: basic wind velocity 
    """
    return c_season * c_dir * vb_0

def v_m(z: float, vb: float, cr: float, co: float) -> float:
    """ Calculates the mean wind velocity, vm(z), at a height z above the terrain.
    Depends on the terrain roughness and orography and on the basic wind velocity.

    Args:
        z (float): vertical distance
        vb (float): basic wind velocity
        cr (float): terrain roughness factor.
        co (float): orography factor.

    Returns:
        float: mean wind velocity, vm(z) 
    """
    return cr * co * vb

def I_v(z: float, z_min: float, z_0: float, co: float, k_I:float=1) -> float:
    """Calculates the turbulence intensity, Iv(z), at height z.
    It is defined as the standard deviation of the turbulence divided by the mean wind velocity.

    Args:
        z (float): vertical distance
        z_min (float, optional): minimum height.
        z_0 (float, optional): roughness length.
        co (float): orography factor.
        k_I (float, optional): turbulence intensity factor. Defaults to 1.

    Returns:
        float: turbulence intensity
    """
    zeff = z if z >= z_min else z_min
    Iv = k_I / co / log(zeff/z_0)
    return Iv

def v_p(z: float, vb: float, z_min: float, z_0: float, cr: float, co: float, k_I:float=1) -> float:
    """Calculates the peak velocity, vp(z), at height z, 
    which includes mean and short-term velocity fluctuations.

    Args:
        z (float): vertical distance
        vb (float): fundamental value of the basic wind velocity
        z_min (float, optional): minimum height.
        z_0 (float, optional): roughness length.
        cr (float): terrain roughness factor.
        co (float): orography factor.
        k_I (float, optional): turbulence intensity factor. Defaults to 1.

    Returns:
        float: peak velocity pressure
    """
    v = cr * co * vb
    zeff = z if z >= z_min else z_min
    Iv = k_I / co / log(zeff/z_0)
    vp = (1.0 + 7*Iv) * v
    return vp

def q_p(z: float, vb: float, z_min: float, z_0: float, cr: float, co: float, rho: float=1.25, k_I:float=1) -> float:
    """Calculates the peak velocity pressure, qp(z), at height z, 
    which includes mean and short-term velocity fluctuations.

    Args:
        z (float): vertical distance.
        vb (float): fundamental value of the basic wind velocity.
        z_min (float, optional): minimum height.
        z_0 (float, optional): roughness length.
        cr (float): terrain roughness factor.
        co (float): orography factor.
        rho (float, optional): air density. Defaults to 1.25 kg/m3.
        k_I (float, optional): turbulence intensity factor. Defaults to 1.

    Returns:
        float: peak velocity pressure
    """
    v = cr * co * vb
    zeff = z if z >= z_min else z_min
    Iv = k_I / co / log(zeff/z_0)
    qp = 0.5 * (1.0 + 7*Iv) * v**2 * rho
    return qp
