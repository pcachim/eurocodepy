# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Beams of varying cross-section or curved — **EN 1995-1-1:2004 §6.4**.

* §6.4.2 single tapered beams: bending stress at the tapered (inclined) edge,
  ``σ_m,α,d ≤ k_m,α·f_m,d``;
* §6.4.3 double tapered, curved and pitched cambered beams: the apex zone —
  bending (``k_l``, ``k_r``), tension perpendicular to the grain (``k_p``,
  ``k_dis``, ``k_vol``) and its interaction with shear.

Only the formulas live here. The geometry (angle ``α``, apex height, radius) is
supplied by the caller. Units follow the other ``ec5.uls`` modules: forces in
kN, moments in kNm, section dimensions and radii in m, stresses in MPa, the
lamination thickness in mm, angles in radians.

Scope (§6.4.3(1)): the apex-zone clause applies only to glued laminated
timber and LVL; the caller is responsible for that (see ``check_apex_zone``).
§6.4.2 applies to the parts with a *single* taper (§6.4.3(2)), i.e. outside the
apex zone -- again the caller's choice of where to call it.

Verified against the text of EN 1995-1-1:2004 §6.4: Eqs. 6.37-6.59 (``k_m,α``,
``k_l`` with ``k_1…k_4``, ``r``, ``k_r``, ``k_vol``, ``k_dis``, ``k_p`` with
``k_5…k_7``, the interaction 6.53). The apex-zone volume ``V`` depends on
Figure 6.9, which is not in the text: for a double tapered beam
``V = b·h_ap²·(1 − 0.25·tan α_ap)`` is the area of the zone of width ``h_ap``;
for curved and pitched cambered beams the zone is the curved part, whose volume
the caller passes in ``ApexInput.zone_volume``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from eurocodepy.ec5.materials import (LoadDuration, ServiceClass, Timber,
                                      TimberForcesType, TimberType)

V0_APEX = 0.01            # m³, reference volume (§6.4.3(6))
K_DIS = {"double_tapered": 1.4, "curved": 1.4, "pitched_cambered": 1.7}
APEX_KINDS = tuple(K_DIS)
R_IN_OVER_T_LIMIT = 240.0  # §6.4.3(7): k_r = 1 above this


def _stress(m_ed: float, b: float, h: float) -> float:
    """``6·M/(b·h²)`` in MPa for M [kNm], b, h [m]."""
    if b <= 0.0 or h <= 0.0:
        return 0.0
    return 6.0 * abs(m_ed) / (b * h * h) / 1e3


# ── §6.4.2 — tapered edge ────────────────────────────────────────────────

def calc_k_m_alpha(alpha: float, f_md: float, f_vd: float, f_t90d: float,
                   f_c90d: float, tension: bool) -> float:
    """``k_m,α`` (EN 1995-1-1:2004 Eqs. 6.39/6.40).

    Args:
        alpha: angle between the tapered edge and the grain [rad].
        tension: True when the tapered edge is in tension (Eq. 6.39), False when
            it is in compression (Eq. 6.40).

    """
    t = math.tan(abs(alpha))
    if tension:
        a = f_md / (0.75 * f_vd) * t
        c = f_md / f_t90d * t * t
    else:
        a = f_md / (1.5 * f_vd) * t
        c = f_md / f_c90d * t * t
    return 1.0 / math.sqrt(1.0 + a * a + c * c)


@dataclass
class TaperedEdgeResult:
    """Result of :func:`check_tapered_edge`."""

    sigma_m: float          # σ_m,α,d = σ_m,0,d  [MPa]
    k_m_alpha: float
    f_md: float
    util_cut: float         # tapered edge:   σ / (k_m,α·f_m,d)
    util_grain: float       # straight edge:  σ / f_m,d
    util: float             # governing
    details: dict = field(default_factory=dict)


def check_tapered_edge(m_ed: float, b: float, h: float, alpha: float,
                       tension_on_cut_edge: bool, timber: Timber,
                       service_class: ServiceClass = ServiceClass.SC1,
                       load_duration: LoadDuration = LoadDuration.MediumDuration,
                       trace=None) -> TaperedEdgeResult:
    """Bending of a single tapered beam (EN 1995-1-1:2004 §6.4.2).

    ``σ_m,α,d = σ_m,0,d = 6·M_d/(b·h²)`` with *h* the depth **at the section**;
    the tapered edge is checked against ``k_m,α·f_m,d`` (Eqs. 6.37-6.40) and the
    straight edge against ``f_m,d``. ``f_m,d`` includes the size factor ``k_h``
    of the depth, as in the cross-section check.

    Args:
        trace (CalcReport | None): optional :class:`eurocodepy.calc_report.CalcReport` recording the
            steps; the result is identical with or without it.

    """
    timber.design_values(service_class, load_duration)
    k_h = timber.k_h(h, TimberForcesType.Bending)
    f_md = timber.fmd * k_h
    sigma = _stress(m_ed, b, h)
    k_ma = calc_k_m_alpha(alpha, f_md, timber.fvd, timber.ft90d,
                          timber.fc90d, tension_on_cut_edge)
    u_cut = sigma / (k_ma * f_md) if f_md > 0 else 0.0
    u_grain = sigma / f_md if f_md > 0 else 0.0
    res = TaperedEdgeResult(
        sigma_m=sigma, k_m_alpha=k_ma, f_md=f_md,
        util_cut=u_cut, util_grain=u_grain, util=max(u_cut, u_grain),
        details={"alpha": alpha, "h": h, "k_h": k_h,
                 "tension_on_cut_edge": tension_on_cut_edge,
                 "f_vd": timber.fvd, "f_t90d": timber.ft90d,
                 "f_c90d": timber.fc90d})
    if trace is not None:
        _trace_tapered(trace, m_ed, b, h, alpha, tension_on_cut_edge, timber,
                       k_h, res)
    return res


def _trace_tapered(trace, m_ed, b, h, alpha, tension, t, k_h, r):
    trace.section("Tapered edge (§6.4.2)")
    trace.step("M_d", abs(m_ed), "kNm")
    trace.step("b / h", (round(b, 4), round(h, 4)), "m",
               note="h = depth at the section")
    trace.step("α", math.degrees(alpha), "°", clause="EN 1995-1-1 §6.4.2",
               note="angle between the tapered edge and the grain")
    trace.step("σ_m,α,d = σ_m,0,d", r.sigma_m, "MPa", clause="EN 1995-1-1 Eq. 6.37",
               expr="6·M_d/(b·h²)",
               subst=f"6·{abs(m_ed):.4g}/({b:.4g}·{h:.4g}²)/1e3",
               latex=r"\sigma_{m,\alpha,d}=\sigma_{m,0,d}=\dfrac{6M_d}{b\,h^2}")
    trace.step("k_h", k_h, "—", clause="EN 1995-1-1 §3.2 / §3.3",
               note="size factor on f_m,d")
    trace.step("f_m,d", r.f_md, "MPa", expr="f_m,d·k_h")
    edge = "tension" if tension else "compression"
    eq = "Eq. 6.39" if tension else "Eq. 6.40"
    f1 = 0.75 if tension else 1.5
    trace.step("k_m,α", r.k_m_alpha, "—", clause=f"EN 1995-1-1 {eq}",
               expr=("1/√(1+(f_m,d/(%s·f_v,d)·tanα)²+(f_m,d/f_%s,90,d·tan²α)²)"
                     % (f1, "t" if tension else "c")),
               note=f"tapered edge in {edge}")
    trace.step("σ_m,α,d / (k_m,α·f_m,d)", r.util_cut, "—",
               clause="EN 1995-1-1 Eq. 6.38", ok=r.util_cut <= 1.0,
               note="tapered edge")
    trace.step("σ_m,0,d / f_m,d", r.util_grain, "—",
               clause="EN 1995-1-1 §6.4.2", ok=r.util_grain <= 1.0,
               note="straight edge")


# ── §6.4.3 — apex zone ───────────────────────────────────────────────────

def calc_k_r(r_in: float | None, t_lam: float) -> float:
    """Bending-strength reduction of curved laminations (Eq. 6.49):
    ``k_r = 1`` for ``r_in/t ≥ 240``, else ``0.76 + 0.001·r_in/t``.

    Args:
        r_in: inner radius [m]; ``None`` (straight lower edge) gives 1.
        t_lam: thickness of the laminations [mm].

    """
    if r_in is None or not math.isfinite(r_in) or t_lam <= 0.0:
        return 1.0
    ratio = r_in * 1e3 / t_lam
    return 1.0 if ratio >= R_IN_OVER_T_LIMIT else 0.76 + 0.001 * ratio


def calc_k_l(h_ap: float, r: float | None, alpha_ap: float) -> float:
    """``k_l`` of the apex bending stress (Eqs. 6.43-6.47), ``r = r_in + 0.5·h_ap``;
    ``r = None`` (straight) leaves ``k_1``."""
    t = math.tan(abs(alpha_ap))
    k1 = 1.0 + 1.4 * t + 5.4 * t * t
    if r is None or not math.isfinite(r) or r <= 0.0:
        return k1
    k2 = 0.35 - 8.0 * t
    k3 = 0.6 + 8.3 * t - 7.8 * t * t
    k4 = 6.0 * t * t
    x = h_ap / r
    return k1 + k2 * x + k3 * x * x + k4 * x ** 3


def calc_k_p(h_ap: float, r: float | None, alpha_ap: float) -> float:
    """``k_p`` of the apex tension perpendicular to the grain (Eqs. 6.56-6.59),
    ``r = r_in + 0.5·h_ap``; ``r = None`` (straight) leaves ``k_5``."""
    t = math.tan(abs(alpha_ap))
    k5 = 0.2 * t
    if r is None or not math.isfinite(r) or r <= 0.0:
        return k5
    k6 = 0.25 - 1.5 * t + 2.6 * t * t
    k7 = 2.1 * t - 4.0 * t * t
    x = h_ap / r
    return k5 + k6 * x + k7 * x * x


def apex_volume(b: float, h_ap: float, alpha_ap: float,
                beam_volume: float | None = None,
                zone_volume: float | None = None) -> float:
    """Stressed volume of the apex zone [m³] (§6.4.3(6), Figure 6.9), taken not
    greater than ``2/3`` of the beam volume when that is given.

    Double tapered beam: the zone is ``h_ap`` wide, ``V = b·h_ap²·(1 − 0.25·
    tan α_ap)``. Curved and pitched cambered beams: the zone is the curved
    part, whose volume is passed as *zone_volume*.
    """
    if zone_volume is not None and zone_volume > 0.0:
        v = zone_volume
    else:
        v = b * h_ap * h_ap * (1.0 - 0.25 * math.tan(abs(alpha_ap)))
    if beam_volume is not None and beam_volume > 0.0:
        v = min(v, 2.0 * beam_volume / 3.0)
    return v


def calc_k_vol(volume: float, timber: Timber) -> float:
    """Volume factor ``(V0/V)^0.2`` for glulam and LVL, 1 for solid timber."""
    if getattr(timber, "material", None) in (TimberType.GLULAM, TimberType.LVL):
        return (V0_APEX / volume) ** 0.2 if volume > 0.0 else 1.0
    return 1.0


@dataclass
class ApexInput:
    """Geometry and actions of an apex zone (double tapered, curved or pitched
    cambered beam)."""

    m_ap: float                     # design moment at the apex [kNm]
    v_ap: float                     # design shear at the apex [kN]
    b: float                        # width [m]
    h_ap: float                     # depth at the apex [m]
    alpha_ap: float = 0.0           # upper edge to grain at the apex [rad]
    r_in: float | None = None       # inner radius [m]; None = straight lower edge
    t_lam: float = 33.0             # lamination thickness [mm]
    kind: str = "double_tapered"    # one of APEX_KINDS (selects k_dis)
    straightening: bool = True      # M tends to straighten the beam → t_90 > 0
    beam_volume: float | None = None  # V_b [m³], to cap V at 2/3·V_b
    zone_volume: float | None = None  # volume of the curved part [m³]; None =
    #                                   the double tapered zone of width h_ap
    reinforced: bool = False        # EN 1995-1-1:2025 only (ignored by 2004)
    a1: float | None = None         # reinforcement spacing along the grain [m]
    zone_length: float | None = None  # length of the apex zone [m] (curved part
    #                                   of curved / pitched cambered beams)
    reinforcement: object | None = None  # a PlaneReinforcement (2025 only)


@dataclass
class ApexResult:
    """Result of :func:`check_apex_zone`."""

    util_bending: float             # k_l·σ / (k_r·f_m,d)
    util_tension90: float           # σ_t,90 / (k_dis·k_vol·f_t,90,d)
    util_interaction: float         # τ/f_v,d + util_tension90
    util: float                     # governing
    k_l: float
    k_p: float
    k_r: float
    k_dis: float
    k_vol: float
    volume: float
    radius: float | None            # r = r_in + 0.5·h_ap
    sigma_m: float                  # [MPa]
    sigma_t90: float                # [MPa]
    tau: float                      # [MPa]
    details: dict = field(default_factory=dict)


def check_apex_zone(inp: ApexInput, timber: Timber,
                    service_class: ServiceClass = ServiceClass.SC1,
                    load_duration: LoadDuration = LoadDuration.MediumDuration,
                    trace=None) -> ApexResult:
    """Apex zone of a double tapered, curved or pitched cambered beam
    (EN 1995-1-1:2004 §6.4.3).

    * bending ``σ_m,d = k_l·6·M_ap/(b·h_ap²) ≤ k_r·f_m,d`` (Eqs. 6.41-6.43);
    * tension perpendicular ``σ_t,90,d = k_p·6·M_ap/(b·h_ap²) ≤
      k_dis·k_vol·f_t,90,d`` (Eqs. 6.50-6.54) -- only when ``M_ap`` tensions
      the inner curved edge, i.e. tends to straighten the beam (§6.4.3(8));
    * valid for glued laminated timber and LVL only (§6.4.3(1)); the caller
      decides what to do for other products;
    * interaction with shear ``τ_d/f_v,d + σ_t,90,d/(k_dis·k_vol·f_t,90,d) ≤ 1``
      (Eq. 6.53), ``τ_d = 1.5·V/(k_cr·b·h_ap)``.

    ``f_m,d`` includes the size factor ``k_h`` of ``h_ap``. *trace* is an
    optional :class:`eurocodepy.calc_report.CalcReport`.
    """
    if inp.kind not in K_DIS:
        msg = f"kind must be one of {APEX_KINDS}, got {inp.kind!r}"
        raise ValueError(msg)
    timber.design_values(service_class, load_duration)
    r = None if inp.r_in is None else inp.r_in + 0.5 * inp.h_ap
    k_l = calc_k_l(inp.h_ap, r, inp.alpha_ap)
    k_p = calc_k_p(inp.h_ap, r, inp.alpha_ap)
    k_r = calc_k_r(inp.r_in, inp.t_lam)
    k_dis = K_DIS[inp.kind]
    vol = apex_volume(inp.b, inp.h_ap, inp.alpha_ap, inp.beam_volume,
                      inp.zone_volume)
    k_vol = calc_k_vol(vol, timber)

    s0 = _stress(inp.m_ap, inp.b, inp.h_ap)
    sigma_m = k_l * s0
    sigma_t = k_p * s0 if inp.straightening else 0.0
    kcr = getattr(timber, "kcr", 1.0) or 1.0
    tau = (1.5 * abs(inp.v_ap) / (kcr * inp.b * inp.h_ap) / 1e3
           if inp.b > 0 and inp.h_ap > 0 else 0.0)

    k_h = timber.k_h(inp.h_ap, TimberForcesType.Bending)
    f_md = timber.fmd * k_h
    u_m = sigma_m / (k_r * f_md) if f_md > 0 else 0.0
    cap_t = k_dis * k_vol * timber.ft90d
    u_t = sigma_t / cap_t if cap_t > 0 else 0.0
    u_i = (tau / timber.fvd if timber.fvd > 0 else 0.0) + u_t
    res = ApexResult(
        util_bending=u_m, util_tension90=u_t, util_interaction=u_i,
        util=max(u_m, u_t, u_i), k_l=k_l, k_p=k_p, k_r=k_r, k_dis=k_dis,
        k_vol=k_vol, volume=vol, radius=r, sigma_m=sigma_m, sigma_t90=sigma_t,
        tau=tau,
        details={"f_md": f_md, "k_h": k_h, "f_vd": timber.fvd,
                 "f_t90d": timber.ft90d, "kind": inp.kind,
                 "straightening": inp.straightening})
    if trace is not None:
        _trace_apex(trace, inp, timber, res, s0, kcr)
    return res


def _trace_apex(trace, inp, t, r, s0, kcr):
    trace.section(f"Apex zone (§6.4.3) — {inp.kind.replace('_', ' ')}")
    trace.step("M_ap,d", abs(inp.m_ap), "kNm")
    trace.step("V_ap,d", abs(inp.v_ap), "kN")
    trace.step("b / h_ap", (round(inp.b, 4), round(inp.h_ap, 4)), "m")
    trace.step("α_ap", math.degrees(abs(inp.alpha_ap)), "°",
               clause="EN 1995-1-1 §6.4.3",
               note="upper edge to the grain at the apex")
    if r.radius is None:
        trace.step("r", "∞", "m", note="straight lower edge: k_l = k_1, "
                   "k_p = k_5, k_r = 1")
    else:
        trace.step("r", r.radius, "m", clause="EN 1995-1-1 §6.4.3",
                   expr="r_in + 0.5·h_ap",
                   subst=f"{inp.r_in:.4g}+0.5·{inp.h_ap:.4g}")
    trace.step("6·M_ap/(b·h_ap²)", s0, "MPa", expr="6·M_ap,d/(b·h_ap²)",
               subst=f"6·{abs(inp.m_ap):.4g}/({inp.b:.4g}·{inp.h_ap:.4g}²)/1e3")
    trace.step("k_l", r.k_l, "—", clause="EN 1995-1-1 Eq. 6.43",
               expr="k_1+k_2·(h_ap/r)+k_3·(h_ap/r)²+k_4·(h_ap/r)³")
    trace.step("k_r", r.k_r, "—", clause="EN 1995-1-1 Eq. 6.49",
               expr="1 if r_in/t ≥ 240, else 0.76+0.001·r_in/t",
               note=f"t = {inp.t_lam:.4g} mm")
    trace.step("k_h", r.details["k_h"], "—", clause="EN 1995-1-1 §3.2 / §3.3")
    trace.step("f_m,d", r.details["f_md"], "MPa", expr="f_m,d·k_h")
    trace.step("σ_m,d", r.sigma_m, "MPa", clause="EN 1995-1-1 Eq. 6.42",
               expr="k_l·6·M_ap,d/(b·h_ap²)")
    trace.step("σ_m,d / (k_r·f_m,d)", r.util_bending, "—",
               clause="EN 1995-1-1 Eq. 6.41", ok=r.util_bending <= 1.0)
    trace.step("k_p", r.k_p, "—", clause="EN 1995-1-1 Eq. 6.56",
               expr="k_5+k_6·(h_ap/r)+k_7·(h_ap/r)²")
    trace.step("k_dis", r.k_dis, "—", clause="EN 1995-1-1 Eq. 6.52",
               note={"double_tapered": "double tapered / curved: 1.4",
                     "curved": "double tapered / curved: 1.4",
                     "pitched_cambered": "pitched cambered: 1.7"}[inp.kind])
    trace.step("V (apex zone)", r.volume, "m³", clause="EN 1995-1-1 §6.4.3(6)",
               expr=("volume of the curved part" if inp.zone_volume
                     else "b·h_ap²·(1−0.25·tanα_ap)"),
               note="≤ 2/3 of the beam volume" if inp.beam_volume else "")
    trace.step("k_vol", r.k_vol, "—", clause="EN 1995-1-1 Eq. 6.51",
               expr="(V_0/V)^0.2 (glulam, LVL); 1 otherwise",
               note="V_0 = 0.01 m³")
    if inp.straightening:
        trace.step("σ_t,90,d", r.sigma_t90, "MPa", clause="EN 1995-1-1 Eq. 6.54",
                   expr="k_p·6·M_ap,d/(b·h_ap²)")
    else:
        trace.step("σ_t,90,d", 0.0, "MPa", clause="EN 1995-1-1 §6.4.3(8)",
                   note="M_ap does not tension the inner edge: no tension "
                        "perpendicular to the grain")
    trace.step("σ_t,90,d / (k_dis·k_vol·f_t,90,d)", r.util_tension90, "—",
               clause="EN 1995-1-1 Eq. 6.50", ok=r.util_tension90 <= 1.0)
    trace.step("τ_d", r.tau, "MPa", expr="1.5·V_ap,d/(k_cr·b·h_ap)",
               subst=f"1.5·{abs(inp.v_ap):.4g}/({kcr:.3g}·{inp.b:.4g}·{inp.h_ap:.4g})/1e3")
    trace.step("τ_d/f_v,d + σ_t,90,d/(k_dis·k_vol·f_t,90,d)",
               r.util_interaction, "—", clause="EN 1995-1-1 Eq. 6.53",
               ok=r.util_interaction <= 1.0)
