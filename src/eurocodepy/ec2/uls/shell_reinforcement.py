import math
import numpy as np


def as_plan(n_xx: float, n_yy:float, n_xy: float)->list:
    """_summary_

    Args:
        n_xx (float): _description_
        n_yy (float): _description_
        n_xy (float): _description_

    Returns:
        list: _description_
    """
    abs_n_xy = abs(n_xy)
    n_xx_n_yy = n_xx * n_yy
    n_xy_2 = n_xy * n_xy
    if n_xx >= -abs_n_xy and n_yy >= -abs_n_xy:
        theta = 1.0
        asx = n_xx + abs_n_xy
        asy = n_yy + abs_n_xy
        asc = 2.0 * abs_n_xy
    elif n_xx < -abs_n_xy and n_xx <= n_yy and n_xx_n_yy <= n_xy_2:
        theta = 0 if abs_n_xy < 1.0e-12 else -n_xx / abs_n_xy
        asx = 0.0
        asy = n_yy + n_xy_2 / abs(n_xx)
        asc = abs(n_xx) * (1.0 + (abs_n_xy/n_xx)**2)
    elif n_yy < -abs_n_xy and n_xx >= n_yy and n_xx_n_yy <= n_xy_2:
        theta = -abs_n_xy / n_yy
        asx = n_xx + n_xy_2 / abs(n_yy)
        asy = 0.0
        asc = abs(n_yy) * (1.0 + (abs_n_xy/n_yy)**2)
    else:
        cen = (n_xx + n_yy) * 0.5
        rad = math.sqrt(n_xy_2+0.25*(n_xx-n_yy)**2)
        theta = math.atan2(n_xx-n_yy, 2*n_xy) / 2.0
        theta = 0 if theta == 0 else 1.0/math.tan(theta)
        asx = 0.0
        asy = 0.0
        asc = abs(cen - rad)
        
    return [asx, asy, asc, theta]


def as_shell_plan(n_t_xx: float, n_t_yy: float, n_t_xy: float, 
                  n_b_xx: float, n_b_yy: float, n_b_xy: float)->np.ndarray:

    return np.array(as_plan(n_t_xx, n_t_yy, n_t_xy) + as_plan(n_b_xx, n_b_yy, n_b_xy))


def as_shell(n_xx: float, n_yy: float, n_xy: float, m_xx: float, m_yy: float, m_xy: float,
            rec: float, h: float) -> np.ndarray:
    """_summary_

    Args:
        n_xx (float): _description_
        n_yy (float): _description_
        n_xy (float): _description_
        m_xx (float): _description_
        m_yy (float): _description_
        m_xy (float): _description_
        rec (float): _description_
        h (float): _description_

    Returns:
        np.array: the reinforecment in both diretions in top and bottom layer and concrete stresses
    """

    t = 2 * rec
    z = h - t
    if h - 4 * rec < 0: return np.array([math.nan,math.nan,math.nan,math.nan,math.nan,math.nan])
    
    n_t_xx = (0.5*n_xx + m_xx/z) / t
    n_t_yy = (0.5*n_yy + m_yy/z) / t
    n_t_xy = (0.5*n_xy - m_xy/z) / t

    n_b_xx = (0.5*n_xx - m_xx/z) / t
    n_b_yy = (0.5*n_yy - m_yy/z) / t
    n_b_xy = (0.5*n_xy + m_xy/z) / t

    as_vect = np.vectorize(as_shell_plan, otypes=[np.ndarray])
    as_total = as_vect(n_t_xx, n_t_yy, n_t_xy, n_b_xx, n_b_yy, n_b_xy)
    return as_total
