# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

import math

import numpy as np

TOLER = 1.0e-12


def calc_reinf_plane(n_xx: float, n_yy: float, n_xy: float) -> list:
    """Calculate the reinforcement in a plane element.

    Args:
        n_xx (float): axial force in x direction
        n_yy (float): axial force in y direction
        n_xy (float): shear force in xy direction

    Returns:
        list: ``[asx, asy, asc, cot θ]``, the reinforcement in both directions, the
            concrete stress and the strut inclination. ``cot θ`` is ``math.inf`` for
            ``n_xy = 0`` with compression in x (the strut is parallel to x) and
            ``math.nan`` when no reinforcement is required (both compressive and
            ``n_xx·n_yy > n_xy²``): the angle is undefined there.

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
        theta = math.inf if abs_n_xy < TOLER else -n_xx / abs_n_xy
        asx = 0.0
        asy = n_yy + n_xy_2 / abs(n_xx)
        asc = abs(n_xx) * (1.0 + (abs_n_xy / n_xx)**2)
    elif n_yy < -abs_n_xy and n_xx >= n_yy and n_xx_n_yy <= n_xy_2:
        theta = -abs_n_xy / n_yy
        asx = n_xx + n_xy_2 / abs(n_yy)
        asy = 0.0
        asc = abs(n_yy) * (1.0 + (abs_n_xy / n_yy)**2)
    else:
        cen = (n_xx + n_yy) * 0.5
        rad = math.sqrt(n_xy_2 + 0.25 * (n_xx - n_yy)**2)
        theta = math.nan                      # no reinforcement: θ undefined
        asx = 0.0
        asy = 0.0
        asc = abs(cen - rad)

    return [asx, asy, asc, theta]


def cal_reinf_shell_plan(top_forces: tuple, bottom_forces: tuple) -> np.ndarray:
    """Calculate reinforcement for shell plane given top and bottom force tuples.

    Args:
        top_forces (tuple): (n_t_xx, n_t_yy, n_t_xy)
        bottom_forces (tuple): (n_b_xx, n_b_yy, n_b_xy)

    Returns:
        np.ndarray: Reinforcement and concrete stresses for both layers.

    """
    return np.array(
        calc_reinf_plane(*top_forces) + calc_reinf_plane(*bottom_forces),
    )


def calc_reinf_shell(n_xx: float, n_yy: float, n_xy: float,
                    m_xx: float, m_yy: float, m_xy: float,
                    rec: float, h: float) -> np.ndarray:
    """Calculate the forces to ccalculate the reinforcement in a shell element.

    Args:
        n_xx (float): axial force in x direction
        n_yy (float): axial force in y direction
        n_xy (float): shear force in xy direction
        m_xx (float): moment in x direction (bending)
        m_yy (float): moment in y direction (bending)
        m_xy (float): moment in xy direction (torsion)
        rec (float): cover to reinforcement
        h (float): height of the shell

    Returns:
        np.ndarray: 8 values, ``[asx, asy, asc, cot θ]`` of the "top" layer followed
            by the same four of the "bottom" layer (``calc_reinf_plane`` of each
            layer). They are per unit of layer thickness ``t = 2·rec`` — stresses in
            the unit of ``n/t`` (kN/m² for n in kN/m) — so multiply ``asx`` and
            ``asy`` by ``t`` for the force per unit length. All ``nan`` if the two
            layers overlap (``h < 4·rec``).

    The "top" layer is the one in tension for a positive ``m_xx`` and ``m_yy``; the
    sandwich model of EN 1992-1-1:2023 Annex G labels the layers the other way and
    has its own sign of the torsion (see
    :func:`eurocodepy.ec2.uls2023.annex_g.sandwich_stresses`).

    """
    t = 2 * rec
    z = h - t
    if h - 4 * rec < 0:
        return np.full(8, math.nan)

    n_t_xx = (0.5 * n_xx + m_xx / z) / t
    n_t_yy = (0.5 * n_yy + m_yy / z) / t
    n_t_xy = (0.5 * n_xy - m_xy / z) / t

    n_b_xx = (0.5 * n_xx - m_xx / z) / t
    n_b_yy = (0.5 * n_yy - m_yy / z) / t
    n_b_xy = (0.5 * n_xy + m_xy / z) / t

    return cal_reinf_shell_plan((n_t_xx, n_t_yy, n_t_xy), (n_b_xx, n_b_yy, n_b_xy))
