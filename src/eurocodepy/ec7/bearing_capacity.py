# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Soil Bearing Resistance Module.

This module provides functions to calculate the ultimate bearing capacity and factor of safety
for shallow foundations based on classical geotechnical engineering methods such as Terzaghi's theory.

Currently supported:

- Ultimate bearing capacity using EC7 method
- Ultimate bearing capacity for seismic loads using EC7 method
"""

import numpy as np

soil_gamma_rd = {
    "compact sand": 1.0,
    "dry loose sand": 1.15,
    "saturated loose sand": 1.5,
    "non sensitive clay": 1.0,
    "sensitive clay": 1.15,
}


def bearing_resistance(Bx: float, By: float, Hx: int | float | np.ndarray, Hy: int | float | np.ndarray,
            N:  int | float | np.ndarray,
            phi: float, gamma: float, q: float, c: float = 0,
            drained: bool = True) -> float:
    """Calculate the bearing capacity of a shallow foundation (EN 1997-1:2004).

    Args:
        Bx (float or numpy.ndarray): effective width of the foundation
        By (float or numpy.ndarray): effective length of the foundation
        Hx (float or numpy.ndarray): horizontal load in X direction on the foundation
        Hy (float or numpy.ndarray): horizontal load in Y direction on the foundation
        q (float or numpy.ndarray): vertical load outside the foundation
        phi (float or numpy.ndarray): effective soil friction angle
        gamma (float or numpy.ndarray): unit weight of the soil
        N (float or numpy.ndarray): vertical load on the foundation
        c (int or numpy.ndarray, optional): effective cohesion. Defaults to 0.
        drained (bool, optional): drained or undrained conditions. if undrained c = cu. Defaults to True.

    Returns:
        float or numpy.ndarray: the bearing capacity of the foundation 

    """
    bearing = 0.0
    area = Bx * By

    B = np.where(Bx <= By, Bx, By)
    L = np.where(Bx <= By, By, Bx)
    theta = np.where(Bx <= By, np.arctan2(Hx, Hy), np.arctan2(Hy, Hx))
    H = np.sqrt(Hx**2 + Hy**2)

    if drained:
        mb = (2 + B / L) / (1 + B / L)
        ml = (2 + L / B) / (1 + L / B)
        m = ml * np.cos(theta)**2 + mb * np.sin(theta)**2

        tanphi = np.tan(phi)
        sinphi = np.sin(phi)

        Nq = np.exp(np.pi * tanphi) * np.tan(np.pi / 4 + phi / 2)**2
        Nc = (Nq - 1.0) / tanphi
        Ng = 2.0 * (Nq - 1.0) * tanphi

        sq = 1.0 + (B / L) * sinphi
        sg = 1.0 - 0.3 * (B / L)
        sc = (sq * Nq - 1.0) / (Nq - 1.0)

        aux = (1.0 - H / (N + area * c / tanphi))
        iq = aux ** m
        ig = aux**(m + 1)
        ic = iq - (1.0 - iq) / (Nc * tanphi)

        bearing = c * Nc * sc * ic + q * Nq * sq * iq + 0.5 * gamma * B * Ng * sg * ig

    else:
        sc = 1.0 + 0.2 * (B / L)
        aux = H / (area * c)
        aux = min(1.0, aux)
        ic = 0.5 * (1.0 + np.sqrt(1.0 - aux))
        bearing = (np.pi + 2.0) * c * sc * ic + q

    return bearing


def seismic_bearing_resistance(ag: float, avg_ahg: float, S: float, B: float, H: float, N: float, M: float,
        phi: float, gamma_s: float, cu: float = 0.0, gamma_c: float = 1.0, 
        gamma_rd: float = 1.5, soil_type: str = "incoherent") -> np.ndarray:
    """Calculate the bearing capacity of a shallow foundation under seismic conditioons.

    According with Eurocode 7 (EN 1997-5:2004).

    Args:
        ag (float or numpy.ndarray): soil acceleration
        avg_ahg (float or numpy.ndarray): ratio between the vertical and horizontal accelerations
        S (float or numpy.ndarray): seismic soil coefficient
        B (float or numpy.ndarray): width of the foundation
        H (float or numpy.ndarray): horizontal load in Y direction on the foundation
        N (float or numpy.ndarray): vertical load on the foundation
        M (float or numpy.ndarray): moment on the foundation
        phi (float or numpy.ndarray): effective soil friction angle
        gamma_s (float or numpy.ndarray): unit weight of the soil
        cu (float or numpy.ndarray, optional): effective cohesion. Defaults to 0.
        gamma_c (float or numpy.ndarray, optional): safety coefficient for coehesion. Defaults to 1.0
        gamma_rd (float or numpy.ndarray, optional): safety coefficient for bearing capacity. Defaults to 1.5
        soil_type (str, optional): type of soil.

    Returns:
        np.ndarray: values of the bearing capacity ratio

    """
    g = 9.80665
    tanphi = np.tan(phi)
    Nmax = np.array([0.0, 0.0])
    F_ = 0.0

    if soil_type == "coherent":
        a = 0.7
        b = 1.29
        c = 2.14
        d = 1.81
        e = 0.21
        f = 0.44
        m = 0.21
        k = 1.22
        k_ = 1.0
        ct = 2.0
        cm = 2.0
        c_m = 1.0
        beta = 2.57
        gamma = 1.87

        F_ = gamma_s * ag * S * B / cu
        Nq = np.exp(np.pi*tanphi)*np.tan(np.pi/4 + phi/2)**2
        Ng = 2.0*(Nq-1.0)*tanphi
        Nmax = np.array([(np.pi+2.0) * c * B / gamma_c])

    elif soil_type == "incoherent":
        a = 0.92
        b = 1.25
        c = 0.92
        d = 1.25
        e = 0.41
        f = 0.32
        m = 0.96
        k = 1.0
        k_ = 0.39
        ct = 1.14
        cm = 1.01
        c_m = 1.01
        beta = 2.9
        gamma = 2.8

        F_ = ag / (g * tanphi)
        Nq = np.exp(np.pi*tanphi)*np.tan(np.pi/4 + phi/2)**2
        Ng = 2.0*(Nq-1.0)*tanphi
        Nmax = np.array([   0.5 * gamma_s * g * (1.0 + avg_ahg * ag / g) * B**2 * Ng,
                            0.5 * gamma_s * g * (1.0 - avg_ahg * ag / g) * B**2 * Ng])

    ratio = np.array([])
    for n in Nmax:
        N_ = gamma_rd * N / n
        V_ = gamma_rd * H / n
        M_ = gamma_rd * M / n

        if (N_ < 0.0 or (
            (soil_type == "incoherent" and (1.0 - m * F_)**k_ <= N_) or
            (soil_type == "coherent" and N_ >= 1.0))):
            ratio.append(-1)
            continue

        val1 = (1.0 - e * F_)**ct * (beta * V_)**ct
        val2 = N_**a * ((1.0 - m * F_**k)**k_ - N_)**b
        val3 = (1.0 - f * F_)**c_m * (gamma * M_)**cm
        val4 = N_**c * ((1.0 - m * F_**k)**k_ - N_)**d

        ratio.append(val1 / val2 + val3 / val4 - 1.0)

    return np.where(ratio < 0.0, True, False)  # noqa: FBT003


if __name__ == "__main__":
    fhi = np.radians(np.array([32.5, 27, 32.5]))
    B = np.array([2.05, 2.63, 3.06])
    d = 0.8
    gamma = 19
    q = d*gamma
    H = np.array([74.6, 74.7, 20.0])
    V = np.array([716.4, 557.0, 530.5])
    bearing = bearing_resistance(B, B, H, H, V, 
                                fhi, gamma, q, 0, True)  # noqa: FBT003
    print(f"Bearing capacity: {np.round(bearing, 1)} kN/m²")  # noqa: T201
    print(f"Bearing capacity: {np.round(bearing*B, 1)} kN")  # noqa: T201
