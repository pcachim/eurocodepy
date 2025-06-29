import numpy as np


def calc_vrd(bw: float, d: float, fck: float, g_c: float, fyk: float, g_s: float,
            cott: float, asw_s: float) -> float:
    """Calculate the design shear strength Vrds and Vrd.max.

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        fyk (float): steel strength
        g_s (float): steel partial safety coefficient
        cott (float): truss inclination (cot)
        asw_s (float): steel transverse area (Asw/s)
        alpha (float): coefficient

    Returns:
        float: (shear reinforcement max(Asw/s), Vrd.max)

    """
    z = 0.9 * d
    vrd_s = asw_s * z * fyk / g_s * cott * 1000.0
    niu = 0.6 * (1.0 - fck / 250)
    vrd_max = bw * z * niu * fck / g_c * 100.0 / (cott + 1.0 / cott)
    return max(vrd_s, vrd_max)


def calc_vrdmax(bw: float, d: float, fck: float, g_c: float, cott: float) -> float:
    """Calculate the design shear strength Vrd.max.

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        cott (float): truss inclination (cot)

    Returns:
        float: Vrd.max

    """
    return bw * 0.9 * d * 0.6 * (1.0 -
                            fck / 250) * fck / g_c * 100.0 / (cott + 1.0 / cott)


def calc_asws(bw: float, d: float, fck: float, g_c: float, fyk: float, g_s: float,
            cott: float, ved: float) -> tuple[float, float]:
    """Calculate the design shear reinforcement.

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        fyk (float): steel strength
        g_s (float): steel partial safety coefficient
        cott (float): truss inclination (cot)
        ved (float): design shear force
        alpha (float): coefficient

    Returns:
        Tuple[float, float]: (shear reinforcement (Asw/s), maximum shear force Vrd.max)

    """
    z = 0.9 * d
    niu = 0.6 * (1.0 - fck / 250)
    vrd_max = bw * z * niu * fck / g_c * 1000.0 / (cott + 1.0 / cott)

    asw_s = ved / z / fyk * g_s / cott / 1000.0 if vrd_max >= ved else np.nan
    return asw_s, vrd_max


def calc_vrdc(bw: float, d: float, fck: float, g_c: float,
        rho_l: float) -> tuple[float, float, float]:
    """Shear strength without shear reinforcement.

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        rho_l (float): longitudinal reinforcement ratio (As/bd)

    Returns:
        Tuple[float, float, float]: (vrd.min, vrd.c, vrd [min(vrd.mmin, vrd.c])

    """
    k = min(2.0, 1.0 + np.sqrt(0.2 / d))
    vrd_min = 35.0 * np.pow(k, 1.5) * np.sqrt(fck) * bw * d
    vrd_c = 180.0 / g_c * k * (100.0 * rho_l * fck)**(1.0 / 3.0) * bw * d
    vrd = max(vrd_min, vrd_c)
    return vrd_min, vrd_c, vrd
