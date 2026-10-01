# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EC2 (EN 1992-1-1:2004) §8.4 and §8.7 — anchorage and lap lengths of ribbed bars.

* §8.4.2  ultimate bond stress ``f_bd = 2.25·η1·η2·f_ctd``
* §8.4.3  basic required anchorage length ``l_b,rqd = (φ/4)·σ_sd/f_bd``
* §8.4.4  design anchorage length ``l_bd = α1·α2·α3·α4·α5·l_b,rqd ≥ l_b,min``
  (Table 8.2 coefficients; minimum lengths of Eq. 8.6 / 8.7)
* §8.7.3  lap length ``l_0 = α1·α2·α3·α5·α6·l_b,rqd ≥ l_0,min`` (Eq. 8.10)

Units — unlike the rest of ``ec2.uls`` these are the units the code itself uses
for bond: **lengths and diameters in mm, areas in mm², strengths in MPa**.

Every function returns a plain ``dict`` (the intermediate values included, so a
caller can show the calculation) and accepts the optional
:class:`eurocodepy.calc_report.CalcReport` as ``trace=``; passing ``None`` is a
no-op.

Simplifications, each one on the safe side and named in the docstring of the
function it affects: ``f_ctd`` is capped at the C60/75 value (§8.4.2(2)); the
bond condition of a bar in a beam follows Fig. 8.2 in its common reading
(:func:`bond_conditions_beam`); the transverse-pressure and welded-bar
coefficients are 1 unless given.
"""
from __future__ import annotations

import math

GAMMA_C = 1.5
GAMMA_S = 1.15
FCK_CAP_FCTD = 60.0       # §8.4.2(2): f_ctd limited to the value for C60/75


# ----------------------------------------------------------------------------
# §8.4.2 — bond strength
# ----------------------------------------------------------------------------

def fctm(fck: float) -> float:
    """Mean tensile strength [MPa] (EN 1992-1-1 Table 3.1)."""
    if fck <= 50.0:
        return 0.30 * fck ** (2.0 / 3.0)
    return 2.12 * math.log(1.0 + (fck + 8.0) / 10.0)


def design_tensile_strength(fck: float, gamma_c: float = GAMMA_C,
                            alpha_ct: float = 1.0) -> float:
    """``f_ctd = α_ct·f_ctk,0.05/γ_c`` [MPa] with ``f_ctk,0.05 = 0.7·f_ctm``,
    for bond: the concrete class is capped at C60/75 (§8.4.2(2))."""
    f = min(float(fck), FCK_CAP_FCTD)
    return alpha_ct * 0.7 * fctm(f) / gamma_c


def bond_conditions_beam(h: float, face: str = "bottom") -> str:
    """``"good"`` or ``"poor"`` bond for a horizontal bar of a beam of depth
    *h* [mm] (EN 1992-1-1 Fig. 8.2, common reading): every bar is in good
    conditions when ``h ≤ 250 mm``; otherwise bars of the **bottom** face are
    good and bars of the **top** face poor (they sit in the upper part of the
    section, where the concrete is placed last)."""
    if face not in ("bottom", "top"):
        raise ValueError("face must be 'bottom' or 'top'")
    if h <= 250.0 or face == "bottom":
        return "good"
    return "poor"


def bond_strength(fck: float, phi: float, good_bond: bool = True,
                  gamma_c: float = GAMMA_C, alpha_ct: float = 1.0,
                  trace=None) -> dict:
    """Ultimate bond stress (§8.4.2(2)): ``f_bd = 2.25·η1·η2·f_ctd``.

    Args:
        fck: characteristic cylinder strength [MPa].
        phi: bar diameter [mm].
        good_bond: ``η1 = 1.0`` for good bond conditions, ``0.7`` otherwise.
        gamma_c, alpha_ct: partial factor / long-term coefficient of ``f_ctd``.
        trace: optional ``CalcReport``.

    Returns:
        ``{"fctd", "eta1", "eta2", "fbd"}`` (MPa).
    """
    if phi <= 0:
        raise ValueError("the bar diameter must be > 0")
    fctd = design_tensile_strength(fck, gamma_c, alpha_ct)
    eta1 = 1.0 if good_bond else 0.7
    eta2 = 1.0 if phi <= 32.0 else (132.0 - phi) / 100.0
    fbd = 2.25 * eta1 * eta2 * fctd
    if trace is not None:
        trace.section("Bond strength (EN 1992-1-1 §8.4.2)")
        trace.step("f_ctd", fctd, "MPa", clause="EN 1992-1-1 §8.4.2(2)",
                   expr="f_ctd = α_ct·0.7·f_ctm/γ_c (class capped at C60/75)")
        trace.step("η_1", eta1, "—", clause="EN 1992-1-1 §8.4.2(2)",
                   note="1.0 good bond / 0.7 otherwise")
        trace.step("η_2", eta2, "—", clause="EN 1992-1-1 §8.4.2(2)",
                   note="1.0 for φ ≤ 32 mm, (132 − φ)/100 otherwise")
        trace.step("f_bd", fbd, "MPa", clause="EN 1992-1-1 Eq. 8.2",
                   expr="f_bd = 2.25·η_1·η_2·f_ctd")
    return {"fctd": fctd, "eta1": eta1, "eta2": eta2, "fbd": fbd}


def basic_anchorage_length(phi: float, sigma_sd: float, fbd: float) -> float:
    """Basic required anchorage length (§8.4.3, Eq. 8.3)
    ``l_b,rqd = (φ/4)·σ_sd/f_bd`` [mm]; *sigma_sd* is the design stress of the
    bar at the start of the anchorage [MPa]."""
    if fbd <= 0:
        raise ValueError("the bond stress must be > 0")
    return phi / 4.0 * sigma_sd / fbd


# ----------------------------------------------------------------------------
# §8.4.4 — Table 8.2 coefficients
# ----------------------------------------------------------------------------

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def anchorage_coefficients(phi: float, cd: float, kind: str = "tension",
                           shape: str = "straight", k: float = 0.0,
                           sum_ast: float = 0.0, sum_ast_min: float = 0.0,
                           a_s: float | None = None, welded: bool = False,
                           pressure: float = 0.0) -> dict:
    """The coefficients ``α1 … α5`` of Table 8.2.

    Args:
        phi: bar diameter [mm].
        cd: cover distance of Fig. 8.3 — the smallest of half the clear
            spacing, the side cover and the top/bottom cover [mm].
        kind: ``"tension"`` or ``"compression"`` (all α = 1 except ``α4``).
        shape: ``"straight"`` or ``"bent"`` (hooks, bends and loops).
        k: confinement factor of Fig. 8.4 (0.1 / 0.05 / 0) for ``α3``.
        sum_ast: transverse reinforcement along the anchorage ``ΣA_st`` [mm²].
        sum_ast_min: ``ΣA_st,min`` (0.25·A_s for beams, A_s for slabs) [mm²].
        a_s: area of one anchored bar [mm²]; default ``π·φ²/4``.
        welded: transverse welded bars ⇒ ``α4 = 0.7``.
        pressure: transverse pressure ``p`` at the ultimate limit state [MPa].

    Returns:
        ``{"alpha1", "alpha2", "alpha3", "alpha4", "alpha5", "lam"}`` — with
        ``α2·α3·α5 ≥ 0.7`` enforced for bars in tension.
    """
    if kind not in ("tension", "compression"):
        raise ValueError("kind must be 'tension' or 'compression'")
    if shape not in ("straight", "bent"):
        raise ValueError("shape must be 'straight' or 'bent'")
    a_bar = a_s if a_s is not None else math.pi * phi ** 2 / 4.0
    alpha4 = 0.7 if welded else 1.0
    if kind == "compression":
        return {"alpha1": 1.0, "alpha2": 1.0, "alpha3": 1.0, "alpha4": alpha4,
                "alpha5": 1.0, "lam": 0.0}
    if shape == "straight":
        alpha1 = 1.0
        alpha2 = _clamp(1.0 - 0.15 * (cd - phi) / phi, 0.7, 1.0)
    else:                                   # hooks / bends / loops
        alpha1 = 0.7 if cd > 3.0 * phi else 1.0
        alpha2 = _clamp(1.0 - 0.15 * (cd - 3.0 * phi) / phi, 0.7, 1.0)
    lam = (sum_ast - sum_ast_min) / a_bar if a_bar > 0 else 0.0
    alpha3 = _clamp(1.0 - k * lam, 0.7, 1.0)
    alpha5 = _clamp(1.0 - 0.04 * pressure, 0.7, 1.0)
    # Table 8.2 note: the product α2·α3·α5 must be at least 0.7
    prod = alpha2 * alpha3 * alpha5
    if prod < 0.7:
        scale = 0.7 / prod
        alpha2 = min(1.0, alpha2 * scale)
        prod = alpha2 * alpha3 * alpha5
        if prod < 0.7:
            alpha3 = min(1.0, alpha3 * 0.7 / prod)
    return {"alpha1": alpha1, "alpha2": alpha2, "alpha3": alpha3,
            "alpha4": alpha4, "alpha5": alpha5, "lam": lam}


def design_anchorage_length(phi: float, fck: float, fyk: float, cd: float,
                            good_bond: bool = True, kind: str = "tension",
                            shape: str = "straight",
                            sigma_sd: float | None = None, k: float = 0.0,
                            sum_ast: float = 0.0, sum_ast_min: float = 0.0,
                            welded: bool = False, pressure: float = 0.0,
                            gamma_c: float = GAMMA_C, gamma_s: float = GAMMA_S,
                            alpha_ct: float = 1.0, trace=None) -> dict:
    """Design anchorage length (§8.4.4, Eq. 8.4):
    ``l_bd = α1·α2·α3·α4·α5·l_b,rqd ≥ l_b,min``.

    ``l_b,min`` is ``max(0.3·l_b,rqd, 10φ, 100 mm)`` in tension (Eq. 8.6) and
    ``max(0.6·l_b,rqd, 10φ, 100 mm)`` in compression (Eq. 8.7). *sigma_sd*
    defaults to the design yield stress ``f_yk/γ_s`` (the bar fully stressed
    where the anchorage starts — the safe choice for a curtailed bar).

    Returns:
        ``{"fctd", "eta1", "eta2", "fbd", "sigma_sd", "lb_rqd", "alpha1" …
        "alpha5", "lbd", "lb_min", "governed_by_min", "kind", "shape"}``.
    """
    bs = bond_strength(fck, phi, good_bond, gamma_c, alpha_ct, trace=trace)
    fyd = fyk / gamma_s
    sig = fyd if sigma_sd is None else float(sigma_sd)
    lb_rqd = basic_anchorage_length(phi, sig, bs["fbd"])
    al = anchorage_coefficients(phi, cd, kind, shape, k, sum_ast,
                                sum_ast_min, None, welded, pressure)
    prod = (al["alpha1"] * al["alpha2"] * al["alpha3"] * al["alpha4"]
            * al["alpha5"])
    frac = 0.3 if kind == "tension" else 0.6
    lb_min = max(frac * lb_rqd, 10.0 * phi, 100.0)
    lbd = max(prod * lb_rqd, lb_min)
    if trace is not None:
        trace.section("Anchorage length (EN 1992-1-1 §8.4.3–§8.4.4)")
        trace.step("σ_sd", sig, "MPa", clause="EN 1992-1-1 §8.4.3",
                   note="design stress at the start of the anchorage")
        trace.step("l_b,rqd", lb_rqd, "mm", clause="EN 1992-1-1 Eq. 8.3",
                   expr="l_b,rqd = (φ/4)·σ_sd/f_bd")
        for i in range(1, 6):
            trace.step(f"α_{i}", al[f"alpha{i}"], "—",
                       clause="EN 1992-1-1 Table 8.2")
        trace.step("l_b,min", lb_min, "mm",
                   clause="EN 1992-1-1 Eq. 8.6" if kind == "tension"
                   else "EN 1992-1-1 Eq. 8.7")
        trace.step("l_bd", lbd, "mm", clause="EN 1992-1-1 Eq. 8.4",
                   expr="l_bd = α_1·α_2·α_3·α_4·α_5·l_b,rqd ≥ l_b,min")
    return {**bs, "sigma_sd": sig, "lb_rqd": lb_rqd, **al, "lbd": lbd,
            "lb_min": lb_min, "governed_by_min": prod * lb_rqd < lb_min,
            "kind": kind, "shape": shape}


# ----------------------------------------------------------------------------
# §8.7.3 — laps
# ----------------------------------------------------------------------------

def lap_coefficient_alpha6(rho1: float) -> float:
    """``α6 = √(ρ1/25)`` limited to ``1 ≤ α6 ≤ 1.5`` (Table 8.3), with
    ``ρ1`` the percentage of lapped bars (of the section) within ``0.65·l_0``
    of the centre of the lap [%]."""
    if rho1 < 0:
        raise ValueError("rho1 must be >= 0")
    return _clamp(math.sqrt(rho1 / 25.0), 1.0, 1.5)


def lap_length(phi: float, fck: float, fyk: float, cd: float, rho1: float = 50.0,
               good_bond: bool = True, sigma_sd: float | None = None,
               k: float = 0.0, sum_ast: float = 0.0,
               sum_ast_min: float | None = None, pressure: float = 0.0,
               gamma_c: float = GAMMA_C, gamma_s: float = GAMMA_S,
               alpha_ct: float = 1.0, trace=None) -> dict:
    """Design lap length of ribbed bars in tension (§8.7.3, Eq. 8.10):
    ``l_0 = α1·α2·α3·α5·α6·l_b,rqd ≥ l_0,min`` with
    ``l_0,min = max(0.3·α6·l_b,rqd, 15φ, 200 mm)``.

    ``α1 … α5`` are those of Table 8.2 for straight bars (``α4`` does not
    apply to laps); for ``α3`` the minimum transverse reinforcement of a lap is
    ``ΣA_st,min = 1.0·A_s·(σ_sd/f_yd)`` (*sum_ast_min* defaults to it).

    Returns:
        ``{"fbd", "sigma_sd", "lb_rqd", "alpha1", "alpha2", "alpha3",
        "alpha5", "alpha6", "l0", "l0_min", "governed_by_min"}``.
    """
    bs = bond_strength(fck, phi, good_bond, gamma_c, alpha_ct, trace=trace)
    fyd = fyk / gamma_s
    sig = fyd if sigma_sd is None else float(sigma_sd)
    lb_rqd = basic_anchorage_length(phi, sig, bs["fbd"])
    a_bar = math.pi * phi ** 2 / 4.0
    ast_min = a_bar * sig / fyd if sum_ast_min is None else sum_ast_min
    al = anchorage_coefficients(phi, cd, "tension", "straight", k, sum_ast,
                                ast_min, a_bar, False, pressure)
    a6 = lap_coefficient_alpha6(rho1)
    prod = al["alpha1"] * al["alpha2"] * al["alpha3"] * al["alpha5"] * a6
    l0_min = max(0.3 * a6 * lb_rqd, 15.0 * phi, 200.0)
    l0 = max(prod * lb_rqd, l0_min)
    if trace is not None:
        trace.section("Lap length (EN 1992-1-1 §8.7.3)")
        trace.step("l_b,rqd", lb_rqd, "mm", clause="EN 1992-1-1 Eq. 8.3")
        trace.step("α_6", a6, "—", clause="EN 1992-1-1 Table 8.3",
                   expr="α_6 = √(ρ_1/25), 1 ≤ α_6 ≤ 1.5")
        trace.step("l_0,min", l0_min, "mm", clause="EN 1992-1-1 Eq. 8.11")
        trace.step("l_0", l0, "mm", clause="EN 1992-1-1 Eq. 8.10",
                   expr="l_0 = α_1·α_2·α_3·α_5·α_6·l_b,rqd ≥ l_0,min")
    return {"fbd": bs["fbd"], "sigma_sd": sig, "lb_rqd": lb_rqd,
            "alpha1": al["alpha1"], "alpha2": al["alpha2"],
            "alpha3": al["alpha3"], "alpha5": al["alpha5"], "alpha6": a6,
            "l0": l0, "l0_min": l0_min, "governed_by_min": prod * lb_rqd < l0_min}


def beam_cover_distance(width: float, cover: float, n_bars: int, phi: float,
                        side_cover: float | None = None) -> float:
    """``c_d`` of Fig. 8.3 for the bars of one layer of a beam [mm]: the smallest
    of half the clear spacing between bars, the side cover and the
    top/bottom cover. *width* is the section width, *cover* the cover to the
    outside of the bar (nominal cover plus stirrup), *side_cover* defaults to
    *cover*. A single bar has no neighbour: only the covers count."""
    c1 = cover if side_cover is None else side_cover
    best = min(cover, c1)
    if n_bars > 1:
        free = width - 2.0 * c1 - n_bars * phi
        best = min(best, free / (n_bars - 1) / 2.0)
    return max(best, 0.0)
