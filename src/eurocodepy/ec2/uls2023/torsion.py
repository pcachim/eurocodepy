# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Torsion — **EN 1992-1-1:2023** Clause 8.3 (the new EC2 generation).

A compact or closed section is designed as an equivalent thin-walled closed
section (8.3.2): the torsion flows round a wall of effective thickness ``t_eff``
enclosing the area ``A_k`` with centre-line perimeter ``u_k``. The torsional
resistance is the least of the stirrups (Eq. 8.82), the longitudinal bars
(Eq. 8.83) and the crushing of the compression field (Eq. 8.84), Eq. (8.81); the
combination with the other internal forces is the linear interaction of
Eq. (8.86). The EC2:2004 counterpart is :mod:`eurocodepy.ec2.uls.torsion`; the
combined shear + torsion procedure is :mod:`eurocodepy.ec2.uls2023.shear_torsion`.

Units: lengths and areas in **m** / **m²**, strengths and stresses in **MPa**,
forces in **kN**, torsion moments in **kNm**, ``Asw/s`` in **m²/m**, ``Asl`` in
**m²**; angles of the compression field as ``cot θ``.

``ν`` (Eq. 8.84) is given by Annex G: Eq. (G.9) with ``ε1`` from Eqs. (G.10) and
(G.11) for reinforcement in both directions (stirrups and longitudinal bars), the
steel strain taken as ``fyd/Es`` (G.3(7)b)); at ``cot θ = 1`` the value 0,60 of
8.3.4(3) is used.
"""

import math

from eurocodepy.ec2.materials import concrete_strength_factors
from eurocodepy.ec2.uls2023.annex_g import calc_eps1_from_x, calc_eps1_from_y, calc_nu

_COT_MIN_DEFAULT = 2.5          # 8.2.3(4)
_NU_COT1 = 0.60                 # 8.3.4(3)
_ES_DEFAULT = 200000.0          # MPa
_FYD_DEFAULT = 500.0 / 1.15     # MPa
_SQUAT_RATIO = 1.5              # 8.3.4(5)
_COVER_FRACTION = 0.07
_MAX_WALL_FRACTION = 0.499      # keeps A_k positive


# ── 8.3.1 / 8.3.2 Internal forces ───────────────────────────────────────────

def distribute_torque(t_ed: float, stiffnesses: list[float]) -> list[float]:
    """Share ``TEd`` among the sub-sections in proportion to ``stiffnesses`` [kNm], 8.3.1(3).

    Use the uncracked torsional stiffnesses or the maximum torsional capacities
    (Eq. 8.84, same strut inclination).
    """
    total = sum(stiffnesses)
    return [t_ed * k / total for k in stiffnesses]


def calc_t_eff(area: float, perimeter: float, cover: float = 0.0,
               thickness: float | None = None) -> float:
    """Return the effective wall thickness ``t_eff = A/u`` [m], 8.3.2(2).

    Not less than ``2·cover`` (``cover`` = distance from the surface to the centre
    of the longitudinal reinforcement); for hollow sections the actual wall
    ``thickness`` is an upper limit.
    """
    t = area / perimeter
    if cover > 0.0:
        t = max(t, 2.0 * cover)
    if thickness is not None:
        t = min(t, thickness)
    return t


def effective_cover(b: float, h: float, cover: float) -> float:
    """Return the cover to use in the torsion model [m], 8.3.4(5).

    When ``bmax/bmin < 1,5`` and ``c > 0,07·bmin`` the calculation is made with a
    reduced cover of ``0,07·bmin`` (partial spalling of the cover).
    """
    b_min, b_max = min(b, h), max(b, h)
    if b_max / b_min < _SQUAT_RATIO and cover > _COVER_FRACTION * b_min:
        return _COVER_FRACTION * b_min
    return cover


def calc_tau_t_ed(t_ed: float, a_k: float, t_eff: float) -> float:
    """Return the torsional shear stress in a wall ``τt = TEd/(2·Ak·teff)`` [MPa], Eq. (8.79)."""
    return abs(t_ed) / (2.0 * a_k * t_eff) / 1000.0


def calc_v_ed_wall(tau_t: float, t_eff: float, z_i: float) -> float:
    """Return the shear force in wall ``i`` due to torsion ``VEd,i = τt·teff·zi`` [kN], Eq. (8.80)."""
    return tau_t * t_eff * z_i * 1000.0


def rectangular_wall(b: float, h: float, cover: float = 0.0) -> dict:
    """Return the equivalent thin-walled section of a solid rectangle.

    ``t_eff`` (``A/u ≥ 2·cover``, limited to keep ``Ak`` positive), ``A_k`` and
    ``u_k`` [m, m², m].
    """
    t_eff = calc_t_eff(b * h, 2.0 * (b + h), cover)
    t_eff = min(t_eff, _MAX_WALL_FRACTION * min(b, h))
    return {"t_eff": t_eff, "a_k": (b - t_eff) * (h - t_eff),
            "u_k": 2.0 * ((b - t_eff) + (h - t_eff))}


# ── 8.3.4 Torsional resistance ──────────────────────────────────────────────

def calc_cot_range(cot_min: float = _COT_MIN_DEFAULT) -> tuple[float, float]:
    """Return the limits ``(1/cot θmin, cot θmin)`` of ``cot θ``, Eq. (8.85)."""
    return 1.0 / cot_min, cot_min


def torsion_nu(cot: float, f_yd: float = _FYD_DEFAULT, e_s: float = _ES_DEFAULT) -> float:
    """Return ``ν`` for Eq. (8.84) from Annex G.

    0,60 at ``cot θ = 1`` (8.3.4(3)); otherwise ``ν = 1/(1 + 110·ε1)`` (G.9) with
    ``ε1 = max(G.10, G.11)`` and the strain of the stirrups and the longitudinal
    bars taken as ``fyd/Es`` (G.3(7)b)). ``f_yd`` and ``e_s`` in MPa; the default
    is B500 with ``γs = 1,15``. E.g. 0,38 at ``cot θ = 2``, 0,29 at ``cot θ = 2,5``.
    """
    if math.isclose(cot, 1.0):
        return _NU_COT1
    eps = f_yd / e_s
    return calc_nu(max(calc_eps1_from_x(eps, cot), calc_eps1_from_y(eps, cot)))


def calc_tau_t_rd_sw(asw_s: float, t_eff: float, f_ywd: float, cot: float) -> float:
    """Return ``τt,Rd,sw = cot θ·Asw/(teff·s)·fywd`` [MPa], Eq. (8.82).

    ``asw_s`` = ``Asw/s`` [m²/m] of the closed stirrup in the wall (one leg).
    """
    return cot * asw_s / t_eff * f_ywd


def calc_tau_t_rd_sl(sum_asl: float, f_yd: float, t_eff: float, u_k: float,
                     cot: float) -> float:
    """Return ``τt,Rd,sl = ΣAsl·fyd/(teff·uk·cot θ)`` [MPa], Eq. (8.83)."""
    return sum_asl * f_yd / (t_eff * u_k * cot)


def calc_tau_t_rd_max(nu: float, f_cd: float, cot: float) -> float:
    """Return ``τt,Rd,max = ν·fcd/(cot θ + tan θ)`` [MPa], Eq. (8.84)."""
    return nu * f_cd / (cot + 1.0 / cot)


def calc_tau_t_rd(tau_sw: float, tau_sl: float, tau_max: float) -> dict:
    """Return ``τt,Rd = min(sw, sl, max)`` [MPa] and the governing mode, Eq. (8.81)."""
    modes = {"stirrups": tau_sw, "longitudinal": tau_sl, "crushing": tau_max}
    mode = min(modes, key=modes.get)
    return {"tau_t_rd": modes[mode], "mode": mode}


def torque_from_stress(tau: float, a_k: float, t_eff: float) -> float:
    """Return the torsion moment ``2·Ak·teff·τ`` [kNm] that gives the stress ``tau`` [MPa]."""
    return 2.0 * a_k * t_eff * tau * 1000.0


def _alpha_cc(fck: float, alpha_cc: float | None, annex: str | None) -> float:
    if alpha_cc is not None:
        return alpha_cc
    return concrete_strength_factors(fck, "2023", annex=annex)[0]


def calc_torsion_resistance(b: float, h: float, fck: float, g_c: float, fyk: float,
                            g_s: float, cot: float, asw_s: float, sum_asl: float,
                            cover: float = 0.0, alpha_cc: float | None = None,
                            nu: float | None = None, cot_min: float = _COT_MIN_DEFAULT,
                            annex: str | None = None) -> dict:
    """Return the torsional resistance of a rectangular section with the given steel, 8.3.4.

    ``asw_s`` [m²/m] of the closed stirrup (one leg), ``sum_asl`` [m²] of the
    longitudinal bars distributed round ``u_k``. ``alpha_cc`` is ``ηcc·ktc``
    of ``fcd`` (``None`` = ``ηcc`` from ``fck``). Returns ``t_rd`` (the resistance
    of Eq. 8.81, kNm), ``t_rd_sw``, ``t_rd_sl``, ``t_rd_max``, the governing
    ``mode``, and ``t_eff``, ``a_k``, ``u_k``.
    """
    lo, hi = calc_cot_range(cot_min)
    if not lo - 1e-9 <= cot <= hi + 1e-9:
        msg = f"cot θ = {cot:g} outside 1/cot θmin ≤ cot θ ≤ cot θmin ({lo:g} to {hi:g}), Eq. (8.85)"
        raise ValueError(msg)
    w = rectangular_wall(b, h, effective_cover(b, h, cover))
    fcd = _alpha_cc(fck, alpha_cc, annex) * fck / g_c
    fyd, fywd = fyk / g_s, fyk / g_s
    n = torsion_nu(cot, fyd, _ES_DEFAULT) if nu is None else nu
    t_sw = calc_tau_t_rd_sw(asw_s, w["t_eff"], fywd, cot)
    t_sl = calc_tau_t_rd_sl(sum_asl, fyd, w["t_eff"], w["u_k"], cot)
    t_mx = calc_tau_t_rd_max(n, fcd, cot)
    gov = calc_tau_t_rd(t_sw, t_sl, t_mx)
    to_t = lambda tau: torque_from_stress(tau, w["a_k"], w["t_eff"])  # noqa: E731
    return {"t_rd": to_t(gov["tau_t_rd"]), "mode": gov["mode"],
            "t_rd_sw": to_t(t_sw), "t_rd_sl": to_t(t_sl), "t_rd_max": to_t(t_mx),
            "t_eff": w["t_eff"], "a_k": w["a_k"], "u_k": w["u_k"], "nu": n}


def calc_torsion(ted: float, b: float, h: float,
                 fck: float, g_c: float, fyk: float, g_s: float,
                 cott: float, cover: float = 0.0,
                 alpha_cc: float | None = None, trace=None,
                 nu: float | None = None, annex: str | None = None) -> dict:
    """Design a solid rectangular section for torsion (EN 1992-1-1:2023 8.3).

    Same arguments and result keys as :func:`eurocodepy.ec2.uls.torsion.calc_torsion`
    (so ``uls2023.calc_torsion`` is a drop-in), with the 2023 model: the closed
    stirrups from Eq. (8.82) and the longitudinal steel from Eq. (8.83) for
    ``τt,Ed = τt,Rd``, the crushing resistance of Eq. (8.84), ``cot θ`` limited by
    Eq. (8.85) and the reduced cover of 8.3.4(5).

    Args:
        ted: design torsion moment ``TEd`` [kNm].
        b, h: section width and height [m].
        fck, g_c, fyk, g_s: concrete strength [MPa] and partial factor, steel
            strength [MPa] and partial factor.
        cott: ``cot θ``, ``1/2,5 ≤ cot θ ≤ 2,5`` (Eq. 8.85).
        cover: distance from the surface to the centre of the longitudinal
            bars [m] (``t_eff ≥ 2·cover``).
        alpha_cc: ``ηcc·ktc`` of ``fcd`` (Eq. 5.3); ``None`` is ``ηcc`` of ``fck``
            with ``ktc = 1`` (late loading). Pass ``0.85·ηcc`` for ``ktc = 0,85``.
        trace: optional :class:`eurocodepy.calc_report.CalcReport` (recording only).
        nu: ``ν`` of Eq. (8.84); ``None`` follows :func:`torsion_nu`.
        annex: national annex country code for ``ηcc``.

    Returns:
        dict with ``t_ef`` [m], ``A_k`` [m²], ``u_k`` [m], ``TRd_max`` [kNm],
        ``Asw_tor_s`` [m²/m, one leg], ``Asl_tor`` [m²], ``util`` (``TEd/TRd,max``),
        and ``tau_t_ed``, ``tau_t_rd_max`` [MPa], ``nu``, ``cover`` (the one used).

    """
    lo, hi = calc_cot_range()
    if not lo - 1e-9 <= cott <= hi + 1e-9:
        msg = f"cot θ = {cott:g} outside {lo:g} ≤ cot θ ≤ {hi:g}, Eq. (8.85)"
        raise ValueError(msg)
    ted = abs(ted)
    cov = effective_cover(b, h, cover)
    w = rectangular_wall(b, h, cov)
    t_eff, a_k, u_k = w["t_eff"], w["a_k"], w["u_k"]

    fyd = fyk / g_s
    a_cc = _alpha_cc(fck, alpha_cc, annex)
    fcd = a_cc * fck / g_c
    n = torsion_nu(cott, fyd, _ES_DEFAULT) if nu is None else nu
    tau_t = calc_tau_t_ed(ted, a_k, t_eff) if a_k > 0.0 else 0.0
    tau_max = calc_tau_t_rd_max(n, fcd, cott)
    trd_max = torque_from_stress(tau_max, a_k, t_eff)

    asw_tor_s = tau_t * t_eff / (cott * fyd) if a_k > 0.0 else 0.0     # (8.82)
    asl_tor = tau_t * t_eff * u_k * cott / fyd if a_k > 0.0 else 0.0   # (8.83)
    util = ted / trd_max if trd_max > 0.0 else float("inf")

    if trace is not None:
        trace.section("Torsion (EN 1992-1-1:2023 8.3)")
        trace.step("T_Ed", ted, "kN·m", clause="EN 1992-1-1:2023 8.3")
        if cov != cover:
            trace.step("c", cov, "m", clause="EN 1992-1-1:2023 8.3.4(5)",
                       note="reduced cover 0,07·b_min (b_max/b_min < 1,5)")
        trace.step("t_eff", t_eff, "m", clause="EN 1992-1-1:2023 8.3.2(2)",
                   expr="t_eff = A/u (≥ 2·c)", subst=f"{b * h:.4g}/{2 * (b + h):.4g}")
        trace.step("A_k", a_k, "m²", expr="A_k = (b − t_eff)·(h − t_eff)")
        trace.step("u_k", u_k, "m", expr="u_k = 2·[(b − t_eff) + (h − t_eff)]")
        trace.step("τ_t,Ed", tau_t, "MPa", clause="EN 1992-1-1:2023 Eq. (8.79)",
                   expr="τ_t = T_Ed/(2·A_k·t_eff)")
        trace.step("cot θ", cott, "—", clause="EN 1992-1-1:2023 Eq. (8.85)",
                   note="1/cot θ_min ≤ cot θ ≤ cot θ_min")
        trace.step("τ_t,Rd,max", tau_max, "MPa", clause="EN 1992-1-1:2023 Eq. (8.84)",
                   expr="τ_t,Rd,max = ν·f_cd/(cot θ + tan θ)",
                   subst=f"ν={n:g}, f_cd={fcd:.4g}, cot θ={cott:g}")
        trace.step("T_Rd,max", trd_max, "kN·m", expr="2·A_k·t_eff·τ_t,Rd,max",
                   ok=(util <= 1.0))
        trace.step("A_sw,tor /s", asw_tor_s, "m²/m", clause="EN 1992-1-1:2023 Eq. (8.82)",
                   expr="Asw/s = τ_t,Ed·t_eff/(cot θ·f_ywd)", note="closed stirrups, one leg")
        trace.step("A_sl,tor", asl_tor, "m²", clause="EN 1992-1-1:2023 Eq. (8.83)",
                   expr="ΣAsl = τ_t,Ed·t_eff·u_k·cot θ/f_yd", note="distributed round u_k")
        trace.step("T_Ed/T_Rd,max", util, "—", clause="EN 1992-1-1:2023 Eq. (8.86)")

    return {"t_ef": t_eff, "A_k": a_k, "u_k": u_k, "TRd_max": trd_max,
            "Asw_tor_s": asw_tor_s, "Asl_tor": asl_tor, "util": util,
            "tau_t_ed": tau_t, "tau_t_rd_max": tau_max, "nu": n, "cover": cov}


# ── 8.3.6 Interaction formula ───────────────────────────────────────────────

def interaction_sum(ratios: list[float]) -> float:
    """Return ``Σ(SEd/SRd)``, Eq. (8.86); the section passes if it is ``≤ 1,0``."""
    return sum(ratios)


def interaction_ok(*s_ed_s_rd: tuple[float, float]) -> dict:
    """Return the linear interaction of Eq. (8.86) for pairs ``(SEd, SRd)``.

    E.g. ``interaction_ok((t_ed, t_rd), (v_ed, v_rd), (m_ed, m_rd))``. Returns the
    ``ratios``, their ``sum`` and ``ok`` (``sum ≤ 1,0``).
    """
    ratios = [abs(e) / r for e, r in s_ed_s_rd]
    total = interaction_sum(ratios)
    return {"ratios": ratios, "sum": total, "ok": total <= 1.0}
