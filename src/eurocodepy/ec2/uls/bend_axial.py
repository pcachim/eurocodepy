# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Rectangular RC section design for combined bending and axial force (M-N).

EN 1992-1-1 ultimate-limit-state design of the tension (As1) and compression
(As2) reinforcement of a rectangular section subjected to a bending moment and
an axial force, using the simplified rectangular stress block and the
transferred-moment method.

The axial force is referred to the section mid-height (centroid). The applied
moment is transferred to the level of the tension reinforcement,

    M_Eds = M_Ed + N_Ed * (h/2 - d1)            (N_Ed compression positive)

and the section is then designed as in pure bending for ``M_Eds``; the axial
force is finally introduced through axial equilibrium,

    As1 = (Fc + As2*fyd - N_Ed) / fyd ,         As2 from the residual moment.

This reduces exactly to the pure-bending result of :func:`calc_asl` when
``N_Ed = 0`` and ``d1 = d2``, so the two share a single source of truth for the
``omega`` relationship.
"""

import math

from eurocodepy.ec2.materials import GammaC, GammaS
from eurocodepy.ec2.uls.beam import calc_asl


def _alpha_lim(fck: float) -> float:
    """Limiting neutral-axis ratio x/d for a singly reinforced section."""
    return 0.45 if fck <= 50.0 else 0.35


def _mu_lim(fck: float) -> float:
    """Limiting reduced moment for the simplified rectangular stress block.

    Derived from the maximum allowed neutral-axis depth (x/d = ``_alpha_lim``)
    with ``x/d = 1.25*omega`` (rectangular block), i.e. omega_max = alpha/1.25
    and mu_lim = omega_max*(1 - omega_max/2). For fck <= 50 this gives
    ~0.295, consistent with the eurocodepy bending routine.
    """
    omega_max = _alpha_lim(fck) / 1.25
    return omega_max * (1.0 - 0.5 * omega_max)


def calc_asl_nm(
    b: float,
    h: float,
    d1: float,
    d2: float,
    med: float,
    ned: float,
    fck: float,
    fyk: float,
    gamma_c: float = GammaC,
    gamma_s: float = GammaS,
    alpha_cc: float = 1.0,
    iprint: bool = False,
) -> dict:
    """Design a rectangular RC section for combined bending and axial force.

    Args:
        b (float): section width [m].
        h (float): section height [m].
        d1 (float): mechanical cover to the tension reinforcement, measured
            from the tension face [m]. The effective depth is ``d = h - d1``.
        d2 (float): mechanical cover to the compression reinforcement, measured
            from the compression face [m].
        med (float): design bending moment about the section mid-height [kNm].
        ned (float): design axial force [kN], **compression positive**.
        fck (float): characteristic concrete strength [MPa].
        fyk (float): characteristic reinforcement yield strength [MPa].
        gamma_c (float, optional): concrete partial factor. Defaults to GammaC.
        gamma_s (float, optional): steel partial factor. Defaults to GammaS.
        alpha_cc (float, optional): long-term/loading coefficient on fcd.
            Defaults to 1.0 (EN 1992-1-1 recommended / Portuguese NA).
        iprint (bool, optional): print a summary. Defaults to False.

    Returns:
        dict: with keys
            ``As1`` tension reinforcement [cm2],
            ``As2`` compression reinforcement [cm2],
            ``As_min`` minimum tension reinforcement [cm2],
            ``mu`` reduced (transferred) moment,
            ``omega`` mechanical reinforcement ratio,
            ``x_d`` neutral-axis ratio x/d,
            ``med_s`` transferred design moment [kNm],
            ``doubly`` whether compression steel is required,
            ``note`` text flag for special cases (e.g. small eccentricity).

    Notes:
        The simplified method is valid while the section is in the
        tension-/balanced-controlled regime (neutral axis within the section
        and the tension steel able to yield). For members dominated by axial
        compression with small eccentricity it returns ``As1 = As_min`` and a
        ``note`` flag; a full M-N interaction (strain compatibility) is then
        required and should be used instead.

    """
    d = h - d1
    if d <= 0:
        msg = "Effective depth d = h - d1 must be positive."
        raise ValueError(msg)

    fcd = alpha_cc * fck / gamma_c          # [MPa]
    fyd = fyk / gamma_s                       # [MPa]

    # Transfer the moment to the tension-reinforcement level. The applied moment
    # decides which face is in tension; the axial force (compression positive)
    # is referred to that tension steel, which sits (h/2 - d1) from the centroid.
    # Using the magnitude keeps the result symmetric for sagging vs hogging:
    # |M_Eds| = |M_Ed| + N_comp·(h/2 - d1)  (axial tension reduces it).
    zs = h / 2.0 - d1
    med_s_abs = abs(med) + ned * zs            # [kNm]
    if med_s_abs < 0.0:
        med_s_abs = 0.0
    med_s = math.copysign(med_s_abs, med) if med != 0.0 else med_s_abs

    mu = med_s_abs / (b * d * d * fcd) / 1000.0
    mu_lim = _mu_lim(fck)

    note = ""
    if mu <= mu_lim:
        # Singly reinforced for the transferred moment (reuse calc_asl so the
        # omega relationship has a single source of truth).
        if med_s_abs < 1.0e-9:
            ast_bending, x_d = 0.0, 0.0
        else:
            ast_bending, _epss, x_d = calc_asl(b, d, med_s_abs, fcd, fyd)
        as2 = 0.0
        # Axial equilibrium: As1 = Fc/fyd - Ned/fyd  (Fc = ast_bending*fyd).
        # ned is compression-positive and reduces the tension steel regardless
        # of the moment sign (i.e. of which face is in tension).
        as1 = ast_bending - ned / fyd * 10.0   # [cm2]
        omega = 1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * mu))
    else:
        # Doubly reinforced: cap the concrete contribution at mu_lim and carry
        # the residual moment with compression steel.
        omega = 1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * mu_lim))
        x_d = 1.25 * omega
        med_lim = mu_lim * b * d * d * fcd * 1000.0       # [kNm]
        dmed = med_s_abs - med_lim                          # [kNm]
        as2 = dmed / ((d - d2) * fyd) * 10.0                # [cm2]
        # Tension steel = concrete block steel + compression steel - axial.
        as1 = (omega * b * d * fcd / fyd * 10000.0
               + as2
               - ned / fyd * 10.0)                          # [cm2]

    # EN 1992-1-1 9.2.1.1 minimum tension reinforcement, using fctm.
    fctm = _fctm(fck)
    as_min = max(0.26 * fctm / fyk, 0.0013) * b * d * 10000.0   # [cm2]

    if as1 < 0.0:
        # Section dominated by axial compression: simplified design no longer
        # governs the tension face. Fall back to minimum steel and flag it.
        note = ("small eccentricity / compression-controlled: "
                "use full M-N interaction")
        as1 = as_min
    else:
        as1 = max(as1, as_min)

    as2 = max(as2, 0.0)

    if iprint:
        print(
            f"M_Ed={med:.1f} kNm N_Ed={ned:.1f} kN -> M_Eds={med_s:.1f} kNm | "
            f"mu={mu:.3f} (mu_lim={mu_lim:.3f}) x/d={x_d:.3f} | "
            f"As1={as1:.2f} cm2 As2={as2:.2f} cm2 {note}",
        )

    return {
        "As1": as1,
        "As2": as2,
        "As_min": as_min,
        "mu": mu,
        "omega": omega,
        "x_d": x_d,
        "med_s": med_s,
        "doubly": mu > mu_lim,
        "note": note,
    }


def _fctm(fck: float) -> float:
    """Mean axial tensile strength fctm [MPa] (EN 1992-1-1 Table 3.1)."""
    if fck <= 50.0:
        return 0.30 * fck ** (2.0 / 3.0)
    fcm = fck + 8.0
    return 2.12 * math.log(1.0 + fcm / 10.0)


def design_rcbeam_nm(
    beam,
    med: float,
    ned: float,
    iprint: bool = False,
) -> dict:
    """Convenience wrapper designing an :class:`RCBeam` for M and N.

    Args:
        beam (RCBeam): beam object carrying geometry and materials.
        med (float): design bending moment [kNm].
        ned (float): design axial force [kN], compression positive.
        iprint (bool, optional): print a summary. Defaults to False.

    Returns:
        dict: see :func:`calc_asl_nm`.

    """
    return calc_asl_nm(
        beam.b, beam.h, beam.at, beam.ac, med, ned,
        beam.fck, beam.fyk, beam.gammac, beam.gammas, iprint=iprint,
    )
