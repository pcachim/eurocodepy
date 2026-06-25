# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
from __future__ import annotations

import numpy as np

from eurocodepy import utils
from eurocodepy.ec2.materials import (
    Concrete,
    ConcreteClass,
    Reinforcement,
    ReinforcementClass,
    get_concrete,
    get_reinforcement,
)
from eurocodepy.utils import calc_section_rectangular

# Constants for sr_max
k1 = 0.8  # ribbed bars
k2 = 0.5  # bending
k3 = 3.4  # Eurocode 2 Table 7.1, for high bond bars
k4 = 0.425


def sr_max(c: float, phi: float, rho_p_eff: float,
            k1: float = 0.8, k2: float = 0.5) -> float:
    """Calculate maximum crack spacing sr_max according to EN 1992-1-1, 7.3.4.

    Args:
        c (float): Concrete cover to the centroid of the tensile reinforcement [mm]
        phi (float): Bar diameter [mm]
        rho_p_eff (float): Effective reinforcement ratio (As,eff / (Ac,eff * rho))
        k1 (float): Coefficient for bond properties (0.8 for high bond bars,
            1.6 for plain bars)
        k2 (float): Coefficient for strain distribution (0.5 for bending,
            1.0 for pure tension)

    Returns:
        float: Maximum crack spacing sr_max [mm].

    """
    return k3 * c + k1 * k2 * k4 * phi / rho_p_eff


def eps_sm(sigma_s: float, Es: float, rho_p_eff: float, fct_eff: float,
            alpha_e: float, k_t: float = 0.6) -> float:
    """Calculate mean strain in reinforcement (eps_sm) according to EN 1992-1-1, 7.3.4.

    Args:
        sigma_s (float): Stress in reinforcement under relevant load [MPa]
        Es (float): Modulus of elasticity of steel [MPa]
        rho_p_eff (float): Effective reinforcement ratio
        fct_eff (float): Effective tensile strength of concrete [MPa]
        alpha_e (float): Modular ratio (Es/Ecm)
        k_t (float): Coefficient for duration of load
            (0.6 for short-term, 0.4 for long-term)

    Returns:
        float: Mean strain in reinforcement (eps_sm).

    """
    sig1 = (sigma_s - k_t * fct_eff * (1.0 + alpha_e * rho_p_eff) / rho_p_eff)
    sig2 = 0.6 * sigma_s
    return np.where(sig1 > sig2, sig1, sig2) / Es


def Ac_eff(b: float, d: float, x: float, h: float) -> float:
    """Calculate the effective height of the tension zone (h_eff).

    Calculation is made according to EN 1992-1-1, 7.3.2.

    Args:
        b (float): Bredth of the beam
        d (float): Effective depth to tension reinforcement
        x (float): Depth of the neutral axis
        h (float): Total section height

    Returns:
        float: Effective height of the tension zone (h_eff) [mm].

    """
    return min(2.5 * (h - d), (h - x) / 3, h / 2) * b


def crack_opening(b: float, h: float, phi: float,
            As: np.ndarray, ds: np.ndarray, Asc: np.ndarray, dsc: np.ndarray,
            conc: str | Concrete | ConcreteClass,
            reinf: str | Reinforcement | ReinforcementClass,
            M: np.ndarray, N: np.ndarray | float | None = None,
            k_t: float = 0.4) -> float:
    """Calculate the crack opening of a reinforced concrete beam.

    EN 1992-1-1 §7.3.4. The cracked-section steel stress accounts for a combined
    bending moment and axial force.

    Args:
        b (float): Bredth of the beam
        h (float): Total section height
        phi (float): bar diameter
        As (np.ndarray): Tension reinforcement areas
        ds (np.ndarray): Effective depths to tension reinforcement
        Asc (np.ndarray): Compression reinforcement areas
        dsc (np.ndarray): Effective depths to compression reinforcement
        conc (Concrete): Concrete
        reinf (Reinforcement): Reinforcement
        M (np.ndarray): Bending moments
        N (np.ndarray | float | None): Axial force, **compression positive**.
            ``None`` (default) keeps the pure-bending behaviour. When supplied,
            the steel stress includes the axial term.
        k_t (float): Load-duration factor for ``eps_sm`` — 0.6 for short-term
            (characteristic/frequent) and 0.4 for long-term (quasi-permanent)
            loading.

    Returns:
        float: the crack opening [mm].

    """
    conc = get_concrete(conc)
    reinf = get_reinforcement(reinf)
    Ap = np.array([0.0])
    dp = np.array([h])
    alpha_Es = 15.0
    alpha_Ep = 15.0
    Es = reinf.Es * 1000.0
    fctm = conc.fctm * 1000.0

    # Effective depth uses the *tension* reinforcement only (the compression
    # steel must not pull the centroid towards the compression face).
    d = np.sum(As * ds) / np.sum(As)

    if N is None:
        # Pure bending — preserve the original formulation exactly.
        Ndummy = np.full_like(M, 0.001)
        _uncrk, crack = calc_section_rectangular(h, b, As,
            Asc, Ap, ds, dsc, dp, alpha_Es, alpha_Ep, M, Ndummy)
        x = crack["NeutralAxis"]
        sig_s = alpha_Es * M / crack["Inertia"] * (ds - x)
    else:
        # Combined M + N. The section solver expresses the axial force as an
        # equivalent normal force at an eccentricity (es = -M/N), so it divides
        # by N — guard a (near-)zero axial against that singularity.
        # The axial force is referenced to the section centroid (≈ h/2), not the
        # bottom fibre, so it does not introduce a spurious eccentricity moment.
        Nv = np.asarray(N, dtype=float)
        Nv = np.where(np.abs(Nv) < 1e-3, 1e-3, Nv)
        dp_axial = np.array([h / 2.0])
        _uncrk, crack = calc_section_rectangular(h, b, As,
            Asc, Ap, ds, dsc, dp_axial, alpha_Es, alpha_Ep, M, Nv)
        x = crack["NeutralAxis"]
        e_p = crack["e_p"]
        sig_s = alpha_Es * (-Nv / crack["Area"]
                            + (M - Nv * e_p) / crack["Inertia"] * (ds - crack["zGs"]))

    rho_p_eff = np.sum(As) / Ac_eff(b, d, x, h)
    epssm = eps_sm(sig_s, Es, rho_p_eff, fctm, alpha_Es, k_t=k_t)
    srmax = sr_max(h - d, phi, rho_p_eff, k1, k2)
    wk = epssm * srmax * 1000.0
    return wk  # noqa: RET504


def is_cracked(b: float, h: float, As: np.ndarray, ds: np.ndarray,
            Asc: np.ndarray, dsc: np.ndarray,
            conc: str | Concrete | ConcreteClass,
            reinf: str | Reinforcement | ReinforcementClass,
            M: np.ndarray, N: np.ndarray | float | None = None) -> bool:
    """Return whether the section is cracked under the given M (and N).

    The section is cracked when the extreme-fibre tensile stress of the
    uncracked (transformed) section reaches the mean tensile strength fctm
    (EN 1992-1-1 §7.1). Both faces are checked, so the test is valid for sagging
    and hogging as well as combined bending and axial force.

    Args:
        b (float): Bredth of the beam
        h (float): Total section height
        As (np.ndarray): Tension reinforcement areas
        Asc (np.ndarray): Compression reinforcement areas
        ds (np.ndarray): Effective depths to tension reinforcement
        dsc (np.ndarray): Effective depths to compression reinforcement
        conc (Concrete): Concrete
        reinf (Reinforcement): Reinforcement
        M (np.ndarray): Bending moments
        N (np.ndarray | float | None): Axial force, **compression positive**.
            ``None`` (default) treats the section in pure bending.

    Returns:
        bool: True if cracked, otherwise False

    """
    conc = get_concrete(conc)
    reinf = get_reinforcement(reinf)
    Ap = np.array([0.0])
    dp = np.array([h])
    alpha_Es = 15.0
    alpha_Ep = 15.0
    fctm = conc.fctm * 1000.0

    if N is None:
        Nv = np.full_like(M, 0.001)
    else:
        Nv = np.asarray(N, dtype=float)
        Nv = np.where(np.abs(Nv) < 1e-3, 1e-3, Nv)
        # Reference the axial force to the section centroid (see crack_opening).
        dp = np.array([h / 2.0])

    uncrk, _crack = calc_section_rectangular(h, b, As, Asc, Ap,
                                ds, dsc, dp, alpha_Es, alpha_Ep, M, Nv)
    e_p = uncrk["e_p"]
    axial = -Nv / uncrk["Area"]
    bend = (M - Nv * e_p)
    # Tension is positive; check the most-tensioned fibre (bottom or top).
    sig_bot = axial + bend / uncrk["Wi"]
    sig_top = axial - bend / uncrk["Ws"]
    sig_max = np.maximum(sig_bot, sig_top)

    return bool(np.any(sig_max >= fctm))


def iscracked_annexLL(fctm: float, fcm: float,
                sigxx: float, sigyy: float, sigzz: float,
                sigxy: float, sigyz: float, sigzx: float) -> bool:
    """Check if the point is cracked.

    Calculation using expression (LL.101) of Annex LL of EN 1992-2:2005.

    Args:
        fctm (float): mean tensile strength of concrete
        fcm (float): mean comprerssive strength of concrete
        sigxx (float): stress xx
        sigyy (float): stress yy
        sigzz (float): stress zz
        sigxy (float): stress xy
        sigyz (float): stress yz
        sigzx (float): stress zx

    Returns:
        bool: True if cracked, False otherwise

    """
    # Calculate stress invariants
    invar = utils.stress.invariants(sigxx, sigyy, sigzz, sigxy, sigyz, sigzx)
    I1 = invar[0] / fcm  # noqa: N806
    J2 = invar[1] / fcm / fcm  # noqa: N806
    cos3t = invar[8]

    # Calculate auxiliary parameters
    k = fctm / fcm
    c1 = 1.0 / (0.7 * k**0.9)
    c2 = 1.0 - 6.8 * (k - 0.07)**2
    alpha = 1.0 / (9.0 * k**1.4)
    beta = 1.0 / (3.7 * k**1.1)
    ang = np.acos(abs(c2 * cos3t)) / 3.0
    lamb = c1 * np.cos(ang) if cos3t >= 0 else c1 * (np.pi / 3.0 - ang)

    # Calculate cracking condition (>0 cracked; <0 uncracked)
    crack = alpha * J2 + lamb * np.sqrt(J2) + beta * I1 - 1.0

    # Return cracked stated (True: cracked: False: uncracked)
    return crack > 0


if __name__ == "__main__":
    b = 0.3
    h = 0.5
    phi = 20  # mm
    As = np.array([8.0e-4])
    ds = np.array([h - 0.05])
    Asc = np.array([0.0e-4])
    dsc = np.array([0.05])
    M = np.array([80.0, 50.0, 40.0, 100.0])

    wk = crack_opening(b, h, phi / 1000.0, As, ds, Asc, dsc, "C30/37", "A500NR", M)
    wk_max = np.max(wk)
    print(f"{wk}")
    print(f"w_cr_max = {wk_max}")
