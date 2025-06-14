# Copyright Paulo Cachim 2025
from dataclasses import dataclass

import numpy as np

cemprops = {
    "Type S": [3, 0.13],
    "Type N": [4, 0.12],
    "Type R": [6, 0.11],
}

VALUE_FCM = 35.0


def beta_cc(t: float, s: float = 0.25) -> float:
    """Calculate the strength hardening coefficient.

    Args:
        t (float): time (days)
        s (float): cement type parameter. Optional, defaults to 0.25 (Type N cement)

        s = 0.20, fast hardening R: CEM42,5R, CEM52,5N e CEM52,5R
        s = 0.25, normal hardening N: CEM32,5R, CEM42,5N
        s = 0.38, slow hardening S: CEM32,5N

    Returns:
        float: strength hardening coefficient

    """
    return np.exp(s * (1 - np.sqrt(28.0 / t)))


def beta_ce(t: float, s: float = 0.25) -> float:
    """Calculate the modulus of elasticity hardening coefficient.

    Args:
        t (float): time (days)
        s (float): cement type parameter. Optional, defaults to 0.25 (Type N cement)

        s = 0.20, fast hardening R: CEM42,5R, CEM52,5N e CEM52,5R
        s = 0.25, normal hardening N: CEM32,5R, CEM42,5N
        s = 0.38, slow hardening S: CEM32,5N

    Returns:
        float: modulus of elasticity hardening coefficient

    """
    return (np.exp(s * (1 - np.sqrt(28.0 / t))))**0.3


@dataclass
class CreepParams:
    """Data class for storing parameters used in creep coefficient calculations.

    Attributes:
        t (int): Time in days.
        h0 (int): Effective height in mm.
        rh (int): Relative humidity in percent.
        t0 (int): Initial time in days.
        fck (float): Concrete compressive strength in MPa.
        cem (float): Cement parameter.

    """

    t: int = 1000000
    h0: int = 100
    rh: int = 65
    t0: int = 10
    fck: float = 20.0
    cem: float = 0.0


def _calc_fcm(fck: float) -> float:
    return fck + 8


def _calc_alphas(fcm: float) -> tuple:
    alpha1 = (35 / fcm)**0.7
    alpha2 = (35 / fcm)**0.2
    alpha3 = min(1.0, (3 / fcm)**0.5)
    return alpha1, alpha2, alpha3


def _calc_tt0(t0: float, cem: float) -> float:
    return t0 * ((1.0 + 9.0 / (2.0 + t0**1.2))**cem)


def _calc_phi_rh(rh: float, h0: float, fcm: float,
                alpha1: float, alpha2: float) -> float:
    phi_rh = (1.0 - rh / 100) / (0.1 * (h0**0.33333333))
    if fcm <= VALUE_FCM:
        return 1.0 + phi_rh
    return (1.0 + phi_rh * alpha1) * alpha2


def _calc_beta_fcm(fcm: float) -> float:
    return 16.8 / np.sqrt(fcm)


def _calc_beta_t0(tt0: float) -> float:
    return 1.0 / (0.1 + tt0**0.2)


def _calc_betah(alpha3: float, rh: float, h0: float) -> float:
    return min(
        1500 * alpha3,
        1.5 * (1.0 + np.power(0.012 * rh, 18)) * h0 + 250 * alpha3,
    )


def _calc_betacc(t: float, t0: float, betah: float) -> float:
    return np.power((t - t0) / (betah + t - t0), 0.3)


def calc_creep_coef(params: CreepParams) -> float:
    """Calculate the creep coefficient using EN1992-1:2004.

    This function calculates the creep coefficient of concrete based on the time,
    effective height, relative humidity, initial time, concrete compressive strength,
    and cement parameter. The creep coefficient is a measure of the time-dependent
    deformation of concrete under sustained load. It is calculated using the
    coefficients defined for different concrete compressive strengths and the effects
    of relative humidity and time.

    Args:
        params (CreepParams): Parameters for the creep coefficient calculation.

    Returns:
        float: the creep coeficient

    """
    t = params.t
    h0 = params.h0
    rh = params.rh
    t0 = params.t0
    fck = params.fck
    cem = params.cem

    fcm = _calc_fcm(fck)
    alpha1, alpha2, alpha3 = _calc_alphas(fcm)
    tt0 = _calc_tt0(t0, cem)
    phi_rh = _calc_phi_rh(rh, h0, fcm, alpha1, alpha2)
    beta_fcm = _calc_beta_fcm(fcm)
    beta_t0 = _calc_beta_t0(tt0)
    phi_0 = beta_fcm * beta_t0 * phi_rh

    try:
        betah = _calc_betah(alpha3, rh, h0)
        betacc = _calc_betacc(t, t0, betah)
        phi = betacc * phi_0
    except (ZeroDivisionError, ValueError, OverflowError):
        phi = 0.0

    return phi


@dataclass
class ShrinkStrainParams:
    """Data class for storing parameters used in shrinkage strain calculations.

    Attributes:
        t (int): Time in days.
        h0 (int): Effective height in mm.
        ts (int): Time of shrinkage start in days.
        rh (int): Relative humidity in percent.
        fck (float): Concrete compressive strength in MPa.
        cem (str): Cement type.

    """

    t: int = 1000000
    h0: int = 100
    ts: int = 3
    rh: int = 65
    fck: float = 20.0
    cem: str = "Type N"


def calc_shrink_strain(params: ShrinkStrainParams) -> float:
    """Calculate the total shrinkage strain. Uses EN1992-1:2004.

    This function calculates the total shrinkage strain of concrete based on the time,
    effective height, time of shrinkage start, relative humidity, concrete compressive
    strength, and cement type. The shrinkage strain is calculated using the coefficients
    defined for different cement types and the concrete compressive strength.

    Args:
        params (ShrinkStrainParams): Parameters for shrinkage strain calculation.

    Returns:
        float: the total shrinkage strain

    """
    t = params.t
    h0 = params.h0
    ts = params.ts
    rh = params.rh
    fck = params.fck
    cem = params.cem

    fcm = fck + 8
    alpha1 = cemprops[cem][0]
    alpha2 = cemprops[cem][1]

    eps_ca = 25.0e-6 * (fck - 10)
    beta_as = 1.0 - np.exp(-0.2 * (t**0.5))

    beta_rh = 1.55 * (1.0 - (rh / 100)**3)
    eps_cd = beta_rh * 0.85e-6 * ((220 + 110 * alpha1) * np.exp(-alpha2 * fcm / 10.0))
    beta_ds = (t - ts) / ((t - ts) + 0.4 * h0**1.5)

    return beta_as * eps_ca + beta_ds * eps_cd
