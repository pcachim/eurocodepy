from math import log

c_season = 1.0
c_dir = 1.0
k_1 = 1.0 # coeficiente de turbulência
rho = 1.25 # kg/m3
z0 = {"0": 0.003, "I": 0.01, "II": 0.05, "III": 0.3, "IV": 1}
zmin = {"0": 1, "I": 1, "II": 2, "III": 5, "IV": 10}

def v_b(vb_0: float) -> float:
    return c_season * c_dir * vb_0

def c_r(z: float, zone: str) -> float:
    k_r = 0.19*((z0[zone]/z0["II"])**0.07)
    zeff = z if z >= zmin[zone] else zmin[zone]
    return k_r * log(zeff/z0[zone])

def c_0(z: float) -> float:
    return 1.0

def v_m(z: float, vb: float, zone: str) -> float:
    return c_r(z, zone) * c_0(z) * vb

def I_v(z: float, zone: str) -> float:
    zeff = z if z >= zmin[zone] else zmin[zone]
    Iv = k_1 / c_0(z) / log(zeff/z0[zone])
    return Iv

def q_p(z: float, vb0: float, zone: str) -> float:
    zone = str.upper(zone)
    # v = v_m(z, v_b(vb0), zone)
    v = c_r(z, zone) * c_0(z) * vb0
    qp = 0.5 * (1.0 + 7*I_v(z, zone)) * v**2 * rho
    return qp