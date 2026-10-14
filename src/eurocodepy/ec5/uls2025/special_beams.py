# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Members with special geometries — **EN 1995-1-1:2025** (§8.3.3, §8.3.4).

Second-generation counterpart of :mod:`eurocodepy.ec5.uls.special_beams`
(EN 1995-1-1:2004 §6.4); same function names, drop-in swappable. What changed:

* **§8.3.3 single tapered beams** -- ``k_m,α`` (Eqs. 8.53-8.56) now carries
  ``k_τ,t = 0.75`` / ``k_τ,c = 1.5`` for GL, BGL, LVL-P and GLVL-P and ``1.0``
  for LVL-C and GLVL-C; Eq. 8.57 (``σ = 6M/(b h²)``) is given up to ``α = 15°``.
* **§8.3.4 apex zone** -- the polynomials ``k_1…k_7``, ``r`` and ``k_r`` are the
  2004 ones (Eqs. 8.59-8.66, 8.72-8.75); ``k_dis`` is **1.3** (double tapered
  and pitched cambered) / **1.15** (curved) (Eq. 8.68); the volume factor is
  ``k_vol = (h_ref/h_ap)^0.3`` with ``h_ref = 600 mm`` (Eq. 8.69) -- no apex
  volume any more; the shear interaction is
  ``τ_d/(k_v·f_v,d) + σ_t,90,d/(k_dis·k_vol·f_t,90,d) ≤ 1`` (Eq. 8.70) with
  ``k_v`` of §8.1.11.1(3) instead of ``k_cr``.
* **§8.3.1 reinforcement** -- optional but *recommended* ("should be
  reinforced"): for pitched cambered beams against tension perpendicular to
  the grain (§8.3.1(3)); for curved and double tapered beams of GL/BGL when
  ``σ_t,90,d`` exceeds 60 % of ``f_t,90,d`` (§8.3.1(4)). The beam is still
  verified without reinforcement (Eqs. 8.67, 8.70); where reinforcement carries
  the full tension those two may be disregarded (§8.3.4.2(1)). The
  recommendation is reported in ``ApexResult.details["reinforce_advised"]``;
  the design of the reinforcement (§8.3.2, §8.3.4.2) is not done here.

Scope (§8.3.4.1(1)): softwood GL and BGL, and double tapered LVL-P / GLVL-P. The
caller decides what to do for other products (``details["in_scope"]``).
Units as in the 2004 module: kN, kNm, m, MPa, ``t_lam`` in mm, angles in rad.
"""
from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass, field

from eurocodepy import dbase
from eurocodepy.ec5.materials import (LoadDuration, ServiceClass, Timber,
                                      TimberForcesType, TimberProduct,
                                      TimberType)
from eurocodepy.ec5.uls2025 import fasteners as fx
from eurocodepy.ec5.uls.special_beams import (  # noqa: F401  (shared with 2004)
    ApexInput,
    ApexResult,
    TaperedEdgeResult,
    _stress,
    calc_k_l,
    calc_k_p,
    calc_k_r,
)
from eurocodepy.ec5.uls2025.shear import F_V_REF_K_GLULAM, F_V_REF_K_TIMBER, K_VAR

H_REF = 0.6                      # m, reference height of k_vol (Eq. 8.69)
K_DIS = {"double_tapered": 1.3, "curved": 1.15, "pitched_cambered": 1.3}
APEX_KINDS = tuple(K_DIS)
ALPHA_MAX_EQ_8_57 = math.radians(15.0)
REINFORCE_RATIO = 0.6            # §8.3.1(4)
K_KA_CENTRAL = 1.0               # Eq. 8.76: curved; central half of the zone
K_KA_OUTER = 0.67                # Eq. 8.76: outer quarters of the zone
K_K_APEX = 1.0                   # Eq. 8.51: double tapered, curved, pitched
A1_MIN = 0.25                    # m, §8.3.4.2(4) dowel-type reinforcement
A1_MAX_OVER_HAP = 0.75           # §8.3.4.2(4): a_1 <= 0.75 h_ap
F_B2K = 0.75                     # MPa, §8.3.2(10) bond line (triangular stress)
_CROSS = (TimberProduct.LVL_C, TimberProduct.GLVL_C)


def k_tau(timber: Timber) -> tuple[float, float]:
    """``(k_τ,t, k_τ,c)`` (Eqs. 8.54/8.56): 0.75/1.5, or 1.0/1.0 for LVL-C and
    GLVL-C."""
    if getattr(timber, "timber_product", None) in _CROSS:
        return 1.0, 1.0
    return 0.75, 1.5


def in_scope(timber: Timber) -> bool:
    """§8.3.4.1(1): glued laminated timber and LVL (the caller checks the
    softwood and the beam type)."""
    return getattr(timber, "material", None) in (TimberType.GLULAM,
                                                 TimberType.LVL)


def calc_k_m_alpha(alpha: float, f_md: float, f_vd: float, f_t90d: float,
                   f_c90d: float, tension: bool,
                   k_tau_t: float = 0.75, k_tau_c: float = 1.5) -> float:
    """``k_m,α`` (EN 1995-1-1:2025 Eqs. 8.53 / 8.55).

    Args:
        alpha: angle at the tapered edge [rad] (Figure 8.9).
        tension: True for tensile stresses parallel to the tapered edge.
        k_tau_t: Eq. 8.54 (see :func:`k_tau`).
        k_tau_c: Eq. 8.56 (see :func:`k_tau`).

    """
    t = math.tan(abs(alpha))
    if tension:
        a = f_md / (k_tau_t * f_vd) * t
        c = f_md / f_t90d * t * t
    else:
        a = f_md / (k_tau_c * f_vd) * t
        c = f_md / f_c90d * t * t
    return 1.0 / math.sqrt(1.0 + a * a + c * c)


def calc_k_vol(h_ap: float, timber: Timber) -> float:
    """Volume factor ``(h_ref/h_ap)^0.3`` (Eq. 8.69) for GL, BGL, LVL-P and
    GLVL-P; 1.0 for LVL-C / GLVL-C (§8.3.4.1(10)) and for products outside the
    clause."""
    if not in_scope(timber) or getattr(timber, "timber_product", None) in _CROSS:
        return 1.0
    return (H_REF / h_ap) ** 0.3 if h_ap > 0.0 else 1.0


def calc_k_v(timber: Timber, h: float) -> float:
    """Shear adjustment ``k_v`` of §8.1.11.1(3) for a depth *h* [m] (the same
    rule as :func:`eurocodepy.ec5.uls2025.shear.check_shear_with_torsion`)."""
    if timber.material is TimberType.TIMBER:
        ref = F_V_REF_K_TIMBER
    elif timber.material is TimberType.GLULAM:
        ref = F_V_REF_K_GLULAM
    else:
        return 1.0
    k_hv = timber.k_h(h, TimberForcesType.Shear)
    return min(k_hv * K_VAR * ref / timber.fvk, 1.0)


def apex_volume(*_a, **_k) -> float:
    """Not used in the 2025 edition (``k_vol`` depends on ``h_ap`` only)."""
    return 0.0


# ── §8.3.4.2 — reinforcement against tension perpendicular to the grain ────

@dataclass
class PlaneReinforcement:
    """Bonded-on plane reinforcement (§8.3.2(3), Figure 8.11, Eq. 8.49).

    Lengths in m, strengths in MPa (design values). ``l_r_l`` / ``l_r_u`` are
    the reinforced lengths above / below the axis prone to splitting (the
    neutral axis, Figure 8.11): for reinforcement covering the full height
    symmetrically each is ``h_ap/2`` (the default); the smaller governs
    (Eq. 8.50). ``f_b2d`` defaults to ``k_mod·f_b2,k/γ_M`` with
    ``f_b2,k = 0.75 MPa`` (§8.3.2(10)) and ``γ_M = 1.30`` for bond line failure
    (Table 4.4), Eq. 4.6 with ``η = 1``.
    """

    b_r: float                      # width of one reinforcement [m]
    t_r: float                      # thickness of one reinforcement [m]
    f_td: float                     # design tensile strength of it [MPa]
    f_b2d: float | None = None      # design strength of the bond line [MPa]
    l_r_l: float | None = None      # reinforced length above the axis [m]
    l_r_u: float | None = None      # ... below (None = same as l_r_l) [m]
    b_r_ef: float | None = None     # effective width [m] (None = b_r)
    n_r: int = 1                    # number of reinforcements per element


@dataclass
class DowelReinforcement:
    """Internal dowel-type reinforcement (§8.3.2(2)): fully threaded screws, rods
    with wood screw thread, or bonded-in rods; resistance from §11.2.2 with the
    reinforced length ``l_r`` as withdrawal length (§8.3.2(8)).

    ``kind``: ``"screw"`` (screws and rods with wood screw thread, Table 11.2
    B.1, ``A_s`` from ``d1``) or ``"bonded_rod"`` (``f_w,k = 4.0``, Table 11.2 C;
    ``A_s`` from ``d`` for ribbed rods or ``0.86·d`` for rods with metric
    thread, ``thread="metric"``). ``gamma_r`` and ``gamma_m2`` default to the
    partial factors of Table 4.4 (``γ_R = 1.30`` for connections with dowel-type
    fasteners, ``γ_M2 = 1.25`` for steel in tension). Lengths in m except the
    fastener dimensions (mm); strengths in MPa.
    """

    d: float                        # diameter [mm]
    f_uk: float                     # characteristic steel tensile strength [MPa]
    gamma_r: float | None = None    # γ_R (Table 4.4); None = the database value
    gamma_m2: float | None = None   # γ_M2 (Table 4.4); None = the database value
    kind: str = "screw"
    d1: float | None = None         # inner thread diameter [mm] (screws)
    thread: str = "ribbed"          # bonded-in rods: "ribbed" | "metric"
    eps: float = 90.0               # fastener axis to grain [°]
    k_screw: float = fx.K_SCREW
    l_r_l: float | None = None      # reinforced length above the axis [m]
    l_r_u: float | None = None      # ... below (None = same) [m]
    n_r: int = 1                    # fasteners per element


@dataclass
class ReinforcementResult:
    """Resistance and check of one reinforcing element (Eqs. 8.48-8.50)."""

    F_rd: float                     # [kN]
    F_ed: float                     # [kN]
    util: float                     # F_ed / F_rd  (Eq. 8.48)
    governing: str                  # "bond" | "tensile" | "withdrawal" | "steel"
    l_r: float                      # min(l_r_l, l_r_u) [m]
    F_bond: float                   # bond line, or timber withdrawal [kN]
    F_tensile: float                # reinforcement tension, or steel [kN]
    details: dict = field(default_factory=dict)


def connection_safety() -> dict:
    """Partial factors of connections, EN 1995-1-1:2025 Tables 4.4 / 4.5 (NDP),
    from the database (``Editions.ec5["2025"].connection_safety``)."""
    return dbase.get_edition_params("ec5", "connection_safety", "2025")


def bond_design_strength(timber: Timber, service_class: ServiceClass,
                         load_duration: LoadDuration) -> float:
    """``f_b2,d = k_mod·f_b2,k/γ_M`` [MPa] with ``f_b2,k = 0.75 MPa``
    (§8.3.2(10)), ``γ_M = 1.30`` for bond line failure (Table 4.4), Eq. 4.6 with
    ``η = 1``."""
    timber.design_values(service_class, load_duration)
    return timber.kmod * F_B2K / connection_safety()["gamma_M_bond_line"]


def reinforcement_layout(kind: str, h_ap: float, a1: float,
                         zone_length: float | None = None) -> list:
    """Positions and ``k_ka`` of the reinforcing elements along the apex zone:
    ``[(x, k_ka)]`` with *x* from the centre of the zone [m].

    The elements are centred on the zone at spacing ``a1`` (the first at
    ``±a1/2``, Figure 8.11a). The zone is ``h_ap`` long for a double tapered
    beam (``0.5·h_ap`` each side of the apex, Figure 8.10a) and the curved part
    (*zone_length*) for curved and pitched cambered beams. ``k_ka`` (Eq. 8.76)
    is 1.0 for curved beams and for the central half of the zone, 0.67 in its
    outer quarters.
    """
    length = h_ap if kind == "double_tapered" else zone_length
    if not length or a1 <= 0.0:
        return []
    xs, k = [], 0
    while (k + 0.5) * a1 <= length / 2 + 1e-9:
        xs += [-(k + 0.5) * a1, (k + 0.5) * a1]
        k += 1
    xs.sort()
    return [(x, K_KA_CENTRAL if kind == "curved" or abs(x) <= length / 4 + 1e-9
             else K_KA_OUTER) for x in xs]


def check_dowel_spacing(a1: float, h_ap: float) -> tuple[bool, str]:
    """§8.3.4.2(4): ``0.25 m ≤ a_1 ≤ 0.75·h_ap`` for internal dowel-type
    reinforcement. Returns ``(ok, message)``."""
    hi = A1_MAX_OVER_HAP * h_ap
    if a1 < A1_MIN - 1e-9:
        return False, f"a_1 = {a1 * 1e3:.0f} mm is below 250 mm"
    if a1 > hi + 1e-9:
        return False, (f"a_1 = {a1 * 1e3:.0f} mm exceeds 0.75·h_ap = "
                       f"{hi * 1e3:.0f} mm")
    return True, ""


def check_dowel_reinforcement(F_ed: float, rf: DowelReinforcement,
                              timber: Timber, h_ap: float, t_lam: float,
                              service_class: ServiceClass = ServiceClass.SC1,
                              load_duration: LoadDuration = LoadDuration.MediumDuration,
                              trace=None) -> ReinforcementResult:
    """``F_t,90,rf,Ed / F_t,90,rf,Rd ≤ 1`` (Eq. 8.48) for internal dowel-type
    reinforcement: ``F_Rd = n_r·F_ax,t,d`` with ``F_ax,t,d`` of Eq. 11.1 using
    the reinforced length ``l_r = min{l_r,l ; l_r,u}`` as withdrawal length
    (§8.3.2(8), Eq. 8.50). ``l_r`` defaults to ``h_ap/2 − t_lam`` (the full
    height without the outer lamination, §8.3.4.2(4)); for glulam the number of
    penetrated laminations is ``n_p = l_r/t_lam``. Softwood is assumed
    (§8.3.4.1(1)). *F_ed* in kN. The limits of Table 11.2 that are not met are
    in ``details["warnings"]``.
    """
    cs = connection_safety()
    gamma_r = rf.gamma_r if rf.gamma_r else cs["gamma_R_dowel_type"]
    gamma_m2 = rf.gamma_m2 if rf.gamma_m2 else cs["gamma_M2_steel_tension_fracture"]
    default_l = max(h_ap / 2 - t_lam / 1e3, 0.0)
    l_l = default_l if rf.l_r_l is None else rf.l_r_l
    l_u = l_l if rf.l_r_u is None else rf.l_r_u
    l_r = min(l_l, l_u)
    l_w = l_r * 1e3                                  # mm
    timber.design_values(service_class, load_duration)
    k_mod = timber.kmod
    rho = float(getattr(timber, "rhok", 0.0) or 0.0)
    warns = []
    if rf.kind == "bonded_rod":
        f_wk = fx.F_W_K_BONDED_IN_ROD
        a_s = math.pi * (rf.d if rf.thread == "ribbed" else 0.86 * rf.d) ** 2 / 4
        if not 30.0 <= rf.eps <= 90.0:
            warns.append(f"ε = {rf.eps:g}° is outside 30°-90° (Table 11.2 C)")
    else:
        d1 = rf.d1 if rf.d1 else 0.0
        n_p = l_w / t_lam if t_lam > 0 else None
        f_wk = fx.withdrawal_strength_screw(
            rf.d, rho, rf.eps, n_p, rf.k_screw,
            parallel_laminated=timber.material is TimberType.GLULAM)
        a_s = math.pi * d1 ** 2 / 4
        warns += fx.screw_validity(rf.d, d1, l_w, rho)
        if not d1:
            warns.append("the inner thread diameter d1 is needed for the "
                         "steel tensile resistance")
    f_wk_force = fx.withdrawal_resistance(rf.d, l_w, f_wk)
    f_tk_force = fx.steel_tensile_resistance(a_s, rf.f_uk)
    f_ax, mode = fx.axial_tensile_resistance(f_wk_force, f_tk_force, k_mod,
                                             gamma_r, gamma_m2)
    f_rd = rf.n_r * f_ax
    res = ReinforcementResult(
        F_rd=f_rd, F_ed=F_ed, util=F_ed / f_rd if f_rd > 0 else math.inf,
        governing=mode, l_r=l_r,
        F_bond=rf.n_r * k_mod / gamma_r * f_wk_force,
        F_tensile=rf.n_r * f_tk_force / gamma_m2,
        details={"f_wk": f_wk, "F_wk": f_wk_force, "F_tk": f_tk_force,
                 "F_ax_t_d": f_ax, "k_mod": k_mod, "warnings": warns,
                 "kind": rf.kind})
    if trace is not None:
        c = "EN 1995-1-1:2025 "
        trace.section("Dowel-type reinforcement (§8.3.2, §11.2.2)")
        trace.step("l_r (withdrawal length)", l_r, "m", clause=c + "Eq. 8.50",
                   expr="min{l_r,l ; l_r,u}",
                   note="default h_ap/2 − t_l" if rf.l_r_l is None else "")
        trace.step("f_w,k", f_wk, "MPa",
                   clause=c + ("Table 11.2 C (9)" if rf.kind == "bonded_rod"
                               else "Table 11.2 B.1 (4)"),
                   expr=("4.0" if rf.kind == "bonded_rod" else
                         "k_screw·k_w·k_mat·d^-0.33·(ρ_k/350)^k_ρ"))
        trace.step("F_w,k", f_wk_force, "kN", clause=c + "Eq. 11.3",
                   expr="π·d·l_w·f_w,k")
        trace.step("F_t,k", f_tk_force, "kN", clause=c + "Eq. 11.4",
                   expr="0.9·A_s·f_u,k")
        trace.step("k_mod / γ_R / γ_M2", (round(k_mod, 3), gamma_r, gamma_m2),
                   "—", clause=c + "Eq. 11.1",
                   note="γ_R, γ_M2: Table 4.4"
                        + ("" if rf.gamma_r and rf.gamma_m2 else " (defaults)"))
        trace.step("F_ax,t,d", f_ax, "kN", clause=c + "Eq. 11.1",
                   expr="min{k_mod/γ_R·F_w,k ; F_t,k/γ_M2}",
                   note=f"governed by the {mode}")
        trace.step("F_t,90,rf,Rd", f_rd, "kN", clause=c + "§8.3.2(8)",
                   expr="n_r·F_ax,t,d")
        trace.step("F_t,90,rf,Ed / F_t,90,rf,Rd", res.util, "—",
                   clause=c + "Eq. 8.48", ok=res.util <= 1.0)
        for w in warns:
            trace.step("Limit not met", w, "—", clause=c + "Table 11.2")
    return res


def check_plane_reinforcement(F_ed: float, rf: PlaneReinforcement,
                              trace=None) -> ReinforcementResult:
    """``F_t,90,rf,Ed / F_t,90,rf,Rd ≤ 1`` (Eq. 8.48) with the resistance of
    bonded-on plane reinforcement
    ``F_Rd = n_r·min{f_b2,d·l_r·b_r,ef ; f_t,d·b_r·t_r/k_k}`` (Eq. 8.49),
    ``l_r = min{l_r,l ; l_r,u}`` (Eq. 8.50), ``k_k = 1.0`` for double tapered,
    curved and pitched cambered beams (Eq. 8.51).

    *F_ed* in kN. The design values ``f_t,d`` and ``f_b2,d`` are the caller's
    (``f_b2,k = 0.75 MPa`` is the characteristic bond strength, §8.3.2(10)).
    """
    if rf.f_b2d is None or rf.l_r_l is None:
        msg = ("PlaneReinforcement.f_b2d and l_r_l must be given (or resolved "
               "from the apex by check_apex_zone)")
        raise ValueError(msg)
    l_u = rf.l_r_l if rf.l_r_u is None else rf.l_r_u
    l_r = min(rf.l_r_l, l_u)
    b_ef = rf.b_r if rf.b_r_ef is None else rf.b_r_ef
    f_bond = rf.n_r * rf.f_b2d * 1e3 * l_r * b_ef
    f_tens = rf.n_r * rf.f_td * 1e3 * rf.b_r * rf.t_r / K_K_APEX
    f_rd = min(f_bond, f_tens)
    res = ReinforcementResult(
        F_rd=f_rd, F_ed=F_ed, util=F_ed / f_rd if f_rd > 0 else math.inf,
        governing="bond" if f_bond <= f_tens else "tensile", l_r=l_r,
        F_bond=f_bond, F_tensile=f_tens)
    if trace is not None:
        c = "EN 1995-1-1:2025 "
        trace.section("Plane reinforcement (§8.3.2, §8.3.4.2)")
        trace.step("l_r", l_r, "m", clause=c + "Eq. 8.50",
                   expr="min{l_r,l ; l_r,u}")
        trace.step("n_r·f_b2,d·l_r·b_r,ef", f_bond, "kN", clause=c + "Eq. 8.49",
                   note="bond line")
        trace.step("n_r·f_t,d·b_r·t_r/k_k", f_tens, "kN", clause=c + "Eq. 8.49",
                   note=f"tensile strength of the reinforcement, k_k = {K_K_APEX}"
                        " (Eq. 8.51)")
        trace.step("F_t,90,rf,Rd", f_rd, "kN", clause=c + "Eq. 8.49",
                   expr="n_r·min{…}", note=f"governed by the {res.governing}")
        trace.step("F_t,90,rf,Ed / F_t,90,rf,Rd", res.util, "—",
                   clause=c + "Eq. 8.48", ok=res.util <= 1.0)
    return res


# ── §8.3.3 — tapered edge ────────────────────────────────────────────────

def check_tapered_edge(m_ed: float, b: float, h: float, alpha: float,
                       tension_on_cut_edge: bool, timber: Timber,
                       service_class: ServiceClass = ServiceClass.SC1,
                       load_duration: LoadDuration = LoadDuration.MediumDuration,
                       trace=None) -> TaperedEdgeResult:
    """Bending at the tapered edge of a single tapered beam (§8.3.3).

    ``σ_m,α,d = σ_m,0,d = 6·M_d/(b·h²)`` (Eq. 8.57, valid up to ``α = 15°`` --
    ``details["eq_8_57_valid"]`` says whether it holds) against
    ``k_m,α·f_m,d`` (Eq. 8.52); the straight edge against ``f_m,d``. ``f_m,d``
    includes the size factor ``k_h`` of the depth *h*.
    """
    timber.design_values(service_class, load_duration)
    k_h = timber.k_h(h, TimberForcesType.Bending)
    f_md = timber.fmd * k_h
    kt, kc = k_tau(timber)
    sigma = _stress(m_ed, b, h)
    k_ma = calc_k_m_alpha(alpha, f_md, timber.fvd, timber.ft90d, timber.fc90d,
                          tension_on_cut_edge, kt, kc)
    u_cut = sigma / (k_ma * f_md) if f_md > 0 else 0.0
    u_grain = sigma / f_md if f_md > 0 else 0.0
    res = TaperedEdgeResult(
        sigma_m=sigma, k_m_alpha=k_ma, f_md=f_md, util_cut=u_cut,
        util_grain=u_grain, util=max(u_cut, u_grain),
        details={"alpha": alpha, "h": h, "k_h": k_h, "k_tau_t": kt,
                 "k_tau_c": kc, "tension_on_cut_edge": tension_on_cut_edge,
                 "eq_8_57_valid": abs(alpha) <= ALPHA_MAX_EQ_8_57 + 1e-12,
                 "f_vd": timber.fvd, "f_t90d": timber.ft90d,
                 "f_c90d": timber.fc90d})
    if trace is not None:
        _trace_tapered(trace, m_ed, b, h, alpha, tension_on_cut_edge, kt, kc,
                       k_h, res)
    return res


def _trace_tapered(trace, m_ed, b, h, alpha, tension, kt, kc, k_h, r):
    trace.section("Tapered edge (§8.3.3)")
    trace.step("M_d", abs(m_ed), "kNm")
    trace.step("b / h", (round(b, 4), round(h, 4)), "m",
               note="h = depth at the section")
    trace.step("α", math.degrees(alpha), "°", clause="EN 1995-1-1:2025 §8.3.3",
               note="angle at the tapered edge (Figure 8.9)")
    trace.step("σ_m,α,d = σ_m,0,d", r.sigma_m, "MPa",
               clause="EN 1995-1-1:2025 Eq. 8.57", expr="6·M_d/(b·h²)",
               subst=f"6·{abs(m_ed):.4g}/({b:.4g}·{h:.4g}²)/1e3",
               latex=r"\sigma_{m,\alpha,d}=\sigma_{m,0,d}=\dfrac{6M_d}{b\,h^2}",
               note="" if r.details["eq_8_57_valid"]
               else "α > 15°: Eq. 8.57 is given up to 15° only")
    trace.step("k_h", k_h, "—", note="size factor on f_m,d")
    trace.step("f_m,d", r.f_md, "MPa", expr="f_m,d·k_h")
    edge = "tension" if tension else "compression"
    trace.step("k_τ", kt if tension else kc, "—",
               clause="EN 1995-1-1:2025 Eq. " + ("8.54" if tension else "8.56"),
               note="GL, BGL, LVL-P, GLVL-P: 0.75 / 1.5; LVL-C, GLVL-C: 1.0")
    trace.step("k_m,α", r.k_m_alpha, "—",
               clause="EN 1995-1-1:2025 Eq. " + ("8.53" if tension else "8.55"),
               expr="1/√(1+(f_m,d/(k_τ·f_v,d)·tanα)²+(f_m,d/f_%s,90,d·tan²α)²)"
                    % ("t" if tension else "c"),
               note=f"tapered edge in {edge}")
    trace.step("σ_m,α,d / (k_m,α·f_m,d)", r.util_cut, "—",
               clause="EN 1995-1-1:2025 Eq. 8.52", ok=r.util_cut <= 1.0,
               note="tapered edge")
    trace.step("σ_m,0,d / f_m,d", r.util_grain, "—",
               clause="EN 1995-1-1:2025 §8.3.3", ok=r.util_grain <= 1.0,
               note="straight edge")


# ── §8.3.4 — apex zone ───────────────────────────────────────────────────

def check_apex_zone(inp: ApexInput, timber: Timber,
                    service_class: ServiceClass = ServiceClass.SC1,
                    load_duration: LoadDuration = LoadDuration.MediumDuration,
                    trace=None) -> ApexResult:
    """Apex zone of a double tapered, curved or pitched cambered beam
    (EN 1995-1-1:2025 §8.3.4).

    * bending ``σ_m,d = k_l,ap·6·M_ap/(b·h_ap²) ≤ k_r·f_m,d`` (Eqs. 8.58-8.61);
    * tension perpendicular ``σ_t,90,d = k_p,ap·6·M_ap/(b·h_ap²) ≤
      k_dis·k_vol·f_t,90,d`` (Eqs. 8.67, 8.71) -- only when ``M_ap`` tensions
      the inner curved edge;
    * interaction with shear ``τ_d/(k_v·f_v,d) + σ_t,90,d/(k_dis·k_vol·f_t,90,d)
      ≤ 1`` (Eq. 8.70), ``τ_d = 1.5·V/(b·h_ap)``.

    ``ApexInput.beam_volume`` / ``zone_volume`` are not used. The reinforcement
    recommended by §8.3.1(3)-(4) (optional) is reported in
    ``details["reinforce_advised"]``.

    With ``ApexInput.reinforced`` the reinforcement carries the full tension
    perpendicular to the grain and **Eqs. 8.67 and 8.70 do not apply**
    (§8.3.4.2(1)): ``util_tension90`` and ``util_interaction`` are 0; the apex
    bending (8.58) still does. The design tensile force of the reinforcement,
    ``F_t,90,rf,Ed = k_ka·σ_t,90,d·b·a_1`` (Eq. 8.76, ``k_ka = 1`` -- the most
    unfavourable value), is returned in ``details["F_t90_rf_per_m"]`` [kN/m of
    beam axis] and, when ``a1`` is given, ``details["F_t90_rf_Ed"]`` [kN]. The
    reinforcement itself (Eqs. 8.48-8.51, §11.2.2, §8.3.4.2(4)) is not verified.
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
    k_vol = calc_k_vol(inp.h_ap, timber)
    k_v = calc_k_v(timber, inp.h_ap)

    s0 = _stress(inp.m_ap, inp.b, inp.h_ap)
    sigma_m = k_l * s0
    sigma_t = k_p * s0 if inp.straightening else 0.0
    tau = (1.5 * abs(inp.v_ap) / (inp.b * inp.h_ap) / 1e3
           if inp.b > 0 and inp.h_ap > 0 else 0.0)

    k_h = timber.k_h(inp.h_ap, TimberForcesType.Bending)
    f_md = timber.fmd * k_h
    u_m = sigma_m / (k_r * f_md) if f_md > 0 else 0.0
    cap_t = k_dis * k_vol * timber.ft90d
    u_t = sigma_t / cap_t if cap_t > 0 else 0.0
    fvd_eff = k_v * timber.fvd
    u_i = (tau / fvd_eff if fvd_eff > 0 else 0.0) + u_t
    f_rf_m = sigma_t * inp.b * 1e3            # kN per m of beam axis (k_ka = 1)
    f_rf = f_rf_m * inp.a1 if inp.a1 else None
    if inp.reinforced:          # §8.3.4.2(1): 8.67 and 8.70 are disregarded
        u_t = 0.0
        u_i = 0.0
    rf_res = _verify_reinforcement(inp, sigma_t, timber, service_class,
                                   load_duration)

    ratio = sigma_t / timber.ft90d if timber.ft90d > 0 else 0.0
    reinforce, why = False, ""
    if inp.reinforced:
        pass                       # it is already reinforced
    elif sigma_t > 0.0 and inp.kind == "pitched_cambered":
        reinforce, why = True, ("§8.3.1(3): reinforcement recommended for "
                                "pitched cambered beams")
    elif ratio > REINFORCE_RATIO:
        reinforce, why = True, ("§8.3.1(4): reinforcement recommended, "
                                "σ_t,90,d exceeds 60 % of f_t,90,d "
                                f"({ratio:.0%})")
    res = ApexResult(
        util_bending=u_m, util_tension90=u_t, util_interaction=u_i,
        util=max(u_m, u_t, u_i), k_l=k_l, k_p=k_p, k_r=k_r, k_dis=k_dis,
        k_vol=k_vol, volume=0.0, radius=r, sigma_m=sigma_m, sigma_t90=sigma_t,
        tau=tau,
        details={"f_md": f_md, "k_h": k_h, "k_v": k_v, "f_vd": timber.fvd,
                 "f_t90d": timber.ft90d, "kind": inp.kind,
                 "straightening": inp.straightening,
                 "t90_over_f": ratio, "reinforce_advised": reinforce,
                 "reinforce_reason": why, "in_scope": in_scope(timber),
                 "reinforced": inp.reinforced, "F_t90_rf_per_m": f_rf_m,
                 "F_t90_rf_Ed": f_rf, "reinforcement": rf_res})
    if trace is not None:
        _trace_apex(trace, inp, res, s0, timber, service_class, load_duration)
    return res


def _check_rf(f_ed, rf, inp, timber, svc, ld, trace=None):
    """The check of the reinforcement type given (plane or dowel-type)."""
    if isinstance(rf, DowelReinforcement):
        return check_dowel_reinforcement(f_ed, rf, timber, inp.h_ap, inp.t_lam,
                                         svc, ld, trace=trace)
    # plane: resolve the defaults that depend on the apex and the timber
    changes = {}
    if rf.l_r_l is None:
        changes["l_r_l"] = inp.h_ap / 2
    if rf.f_b2d is None:
        changes["f_b2d"] = bond_design_strength(timber, svc, ld)
    if changes:
        rf = dataclasses.replace(rf, **changes)
    return check_plane_reinforcement(f_ed, rf, trace=trace)


def _verify_reinforcement(inp, sigma_t, timber=None, service_class=None,
                          load_duration=None):
    """The reinforcing elements of a reinforced apex with plane reinforcement
    and a spacing given: ``{"elements": [(x, k_ka, F_ed, result)], "util",
    "governing", "spacing"}`` or ``None``. The most unfavourable element is the
    one with ``k_ka = 1``."""
    rf = inp.reinforcement
    if not inp.reinforced or rf is None or not inp.a1:
        return None
    layout = reinforcement_layout(inp.kind, inp.h_ap, inp.a1, inp.zone_length)
    if not layout:
        return None
    elems = []
    for x, k_ka in layout:
        f_ed = k_ka * sigma_t * inp.b * 1e3 * inp.a1
        elems.append((x, k_ka, f_ed, _check_rf(
            f_ed, rf, inp, timber, service_class, load_duration)))
    worst = max(elems, key=lambda e: e[3].util)
    return {"elements": elems, "util": worst[3].util,
            "governing": worst[3].governing, "worst": worst,
            "spacing": check_dowel_spacing(inp.a1, inp.h_ap)}


def _trace_apex(trace, inp, r, s0, timber=None, service_class=None,
                load_duration=None):
    c = "EN 1995-1-1:2025 "
    trace.section(f"Apex zone (§8.3.4) — {inp.kind.replace('_', ' ')}")
    trace.step("M_ap,d", abs(inp.m_ap), "kNm")
    trace.step("V_ap,d", abs(inp.v_ap), "kN")
    trace.step("b / h_ap", (round(inp.b, 4), round(inp.h_ap, 4)), "m")
    trace.step("α_ap", math.degrees(abs(inp.alpha_ap)), "°",
               clause=c + "§8.3.4.1", note="taper in the middle of the apex zone")
    if r.radius is None:
        trace.step("r", "∞", "m", note="straight lower edge: k_l,ap = k_1, "
                   "k_p,ap = k_5, k_r = 1")
    else:
        trace.step("r", r.radius, "m", clause=c + "Eq. 8.66",
                   expr="r_in + 0.5·h_ap",
                   subst=f"{inp.r_in:.4g}+0.5·{inp.h_ap:.4g}")
    trace.step("6·M_ap/(b·h_ap²)", s0, "MPa", expr="6·M_ap,d/(b·h_ap²)",
               subst=f"6·{abs(inp.m_ap):.4g}/({inp.b:.4g}·{inp.h_ap:.4g}²)/1e3")
    trace.step("k_l,ap", r.k_l, "—", clause=c + "Eq. 8.61",
               expr="k_1+k_2·(h_ap/r)+k_3·(h_ap/r)²+k_4·(h_ap/r)³")
    trace.step("k_r", r.k_r, "—", clause=c + "Eq. 8.59",
               expr="1 if r_in/t_l ≥ 240, else 0.76+0.001·r_in/t_l",
               note=f"t_l = {inp.t_lam:.4g} mm")
    trace.step("k_h", r.details["k_h"], "—", note="size factor on f_m,d")
    trace.step("f_m,d", r.details["f_md"], "MPa", expr="f_m,d·k_h")
    trace.step("σ_m,d", r.sigma_m, "MPa", clause=c + "Eq. 8.60",
               expr="k_l,ap·6·M_ap,d/(b·h_ap²)")
    trace.step("σ_m,d / (k_r·f_m,d)", r.util_bending, "—",
               clause=c + "Eq. 8.58", ok=r.util_bending <= 1.0)
    trace.step("k_p,ap", r.k_p, "—", clause=c + "Eq. 8.72",
               expr="k_5+k_6·(h_ap/r)+k_7·(h_ap/r)²")
    trace.step("k_dis", r.k_dis, "—", clause=c + "Eq. 8.68",
               note="double tapered, pitched cambered: 1.3; curved: 1.15")
    trace.step("k_vol", r.k_vol, "—", clause=c + "Eq. 8.69",
               expr="(h_ref/h_ap)^0.3", subst=f"({H_REF}/{inp.h_ap:.4g})^0.3",
               note="h_ref = 600 mm; 1.0 for LVL-C / GLVL-C")
    if inp.straightening:
        trace.step("σ_t,90,d", r.sigma_t90, "MPa", clause=c + "Eq. 8.71",
                   expr="k_p,ap·6·M_ap,d/(b·h_ap²)")
    else:
        trace.step("σ_t,90,d", 0.0, "MPa", clause=c + "§8.3.4",
                   note="M_ap does not tension the inner edge: no tension "
                        "perpendicular to the grain")
    if inp.reinforced:
        trace.step("Reinforced", "yes", "—", clause=c + "§8.3.4.2(1)",
                   note="the reinforcement carries the full tension "
                        "perpendicular to the grain: Eqs. 8.67 and 8.70 are "
                        "disregarded")
        trace.step("F_t,90,rf,Ed / a_1", r.details["F_t90_rf_per_m"], "kN/m",
                   clause=c + "Eq. 8.76", expr="k_ka·σ_t,90,d·b",
                   subst=f"1.0·{r.sigma_t90:.4g}·{inp.b:.4g}·1e3",
                   note="k_ka = 1.0 (central half of the apex zone; 0.67 in "
                        "the outer quarters of double tapered and pitched "
                        "cambered beams)")
        if r.details["F_t90_rf_Ed"] is not None:
            trace.step("F_t,90,rf,Ed", r.details["F_t90_rf_Ed"], "kN",
                       clause=c + "Eq. 8.76", expr="k_ka·σ_t,90,d·b·a_1",
                       subst=f"{r.details['F_t90_rf_per_m']:.4g}·{inp.a1:.4g}",
                       note="k_ka = 1.0")
        rf = r.details["reinforcement"]
        if rf is not None:
            x, k_ka, f_ed, _res = rf["worst"]
            trace.step("Elements / k_ka", (len(rf["elements"]), K_KA_OUTER),
                       "—", clause=c + "Eq. 8.76 / Figure 8.11",
                       note="centred on the apex zone at a_1; k_ka = 1.0 in the "
                            "central half, 0.67 in the outer quarters")
            _check_rf(f_ed, inp.reinforcement, inp, timber, service_class,
                      load_duration, trace=trace)
        elif inp.reinforcement is None:
            trace.step("F_t,90,rf,Rd", "not verified", "—", clause=c + "Eq. 8.48",
                       note="no reinforcement data given (plane: Eq. 8.49; "
                            "screws and rods: §11.2.2)")
        else:
            trace.step("F_t,90,rf,Rd", "not verified", "—", clause=c + "Eq. 8.48",
                       note="the spacing a_1 is needed")
        return
    trace.step("σ_t,90,d / (k_dis·k_vol·f_t,90,d)", r.util_tension90, "—",
               clause=c + "Eq. 8.67", ok=r.util_tension90 <= 1.0)
    trace.step("k_v", r.details["k_v"], "—", clause=c + "§8.1.11.1(3)")
    trace.step("τ_d", r.tau, "MPa", expr="1.5·V_ap,d/(b·h_ap)",
               subst=f"1.5·{abs(inp.v_ap):.4g}/({inp.b:.4g}·{inp.h_ap:.4g})/1e3")
    trace.step("τ_d/(k_v·f_v,d) + σ_t,90,d/(k_dis·k_vol·f_t,90,d)",
               r.util_interaction, "—", clause=c + "Eq. 8.70",
               ok=r.util_interaction <= 1.0)
    if r.details["reinforce_advised"]:
        trace.step("Reinforcement", "recommended (optional)", "—",
                   clause=c + "§8.3.1",
                   note=r.details["reinforce_reason"] + "; if it carries the "
                        "full tension, Eqs. 8.67 and 8.70 may be disregarded "
                        "(§8.3.4.2(1))")
