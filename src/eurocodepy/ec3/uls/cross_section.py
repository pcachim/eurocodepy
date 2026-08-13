# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1993-1-1 §6.2 cross-section resistance under N, My, Mz, Vy, Vz and T.

This module verifies the *cross-section* (no member buckling — that is
§6.3.3, :mod:`eurocodepy.ec3.uls.member_buckling`) against:

* shear resistance about both axes — ``Vpl,Rd`` (§6.2.6), with a slender-web
  shear-buckling flag;
* torsion — the plastic torsion resistance ``T_Rd`` and the torsion-reduced
  shear resistance ``Vpl,T,Rd`` (§6.2.7);
* bending and axial force — the reduced plastic moment ``MN,Rd`` and the
  biaxial interaction (§6.2.9) for Class 1–2, the elastic stress check for
  Class 3 and the effective-section check for Class 4;
* bending and shear — the ``(1 − ρ)`` yield reduction on the shear area when
  ``V_Ed > 0.5·Vpl,Rd`` (§6.2.8);
* their combination (§6.2.10), returned as a single governing utilisation.

Consistent units: forces in **kN**, moments in **kNm**, torsion in **kNm**,
lengths / dimensions in **mm**, stresses in **N/mm²**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

_SQRT3 = math.sqrt(3.0)


# ── elementary resistances ──────────────────────────────────────────────────

def shear_resistance(av: float, fy: float, gamma_M0: float = 1.0) -> float:
    """Plastic shear resistance ``Vpl,Rd = Av·(fy/√3)/γM0`` [kN] (§6.2.6(2)).

    Args:
        av: Shear area [mm²].
        fy: Yield strength [N/mm²].
        gamma_M0: Partial factor.

    Returns:
        Vpl,Rd [kN].

    """
    return av * (fy / _SQRT3) / gamma_M0 / 1e3


def torsion_resistance(wt: float, fy: float, gamma_M0: float = 1.0) -> float:
    """Plastic (St-Venant) torsion resistance ``T_Rd = Wt·(fy/√3)/γM0`` [kNm].

    Args:
        wt: Torsional section modulus [mm³].
        fy: Yield strength [N/mm²].
        gamma_M0: Partial factor.

    Returns:
        T_Rd [kNm].

    """
    return wt * (fy / _SQRT3) / gamma_M0 / 1e6 if wt > 0 else math.inf


def shear_buckling_susceptible(hw: float, tw: float, eps: float,
                               eta: float = 1.2) -> bool:
    """True when an unstiffened web must be checked for shear buckling —
    ``hw/tw > 72·ε/η`` (§6.2.6(6)).
    """
    return tw > 0 and (hw / tw) > 72.0 * eps / eta


def reduced_shear_resistance_torsion(vpl_rd: float, tau_t: float, fy: float,
                                     gamma_M0: float, *, hollow: bool) -> float:
    """Torsion-reduced plastic shear resistance ``Vpl,T,Rd`` (§6.2.7(9)).

    For hollow sections ``Vpl,T,Rd = [1 − τt/(fyd/√3)]·Vpl,Rd``; for I/H
    sections the ``√`` form with the 1.25 factor is used.

    Args:
        vpl_rd: Plastic shear resistance without torsion [kN].
        tau_t: St-Venant torsional shear stress τt,Ed [N/mm²].
        fy: Yield strength [N/mm²].
        gamma_M0: Partial factor.
        hollow: True for RHS/SHS/CHS, False for open (I/H) sections.

    Returns:
        Vpl,T,Rd [kN].

    """
    fyd_shear = (fy / _SQRT3) / gamma_M0
    if fyd_shear <= 0:
        return vpl_rd
    if hollow:
        factor = 1.0 - tau_t / fyd_shear
    else:
        factor = 1.0 - tau_t / (1.25 * fyd_shear)
    return vpl_rd * math.sqrt(max(factor, 0.0)) if not hollow \
        else vpl_rd * max(factor, 0.0)


# ── bending + axial (§6.2.9) ────────────────────────────────────────────────

def _mn_reduction(kind: str, n: float, geom: dict):
    """Return (MN_y / Mpl_y, MN_z / Mpl_z, alpha, beta) — the reduced-moment
    ratios and the biaxial exponents for the given section family and axial
    utilisation ``n = N_Ed/Npl,Rd`` (0 ≤ n ≤ 1).
    """
    n = min(max(n, 0.0), 1.0)
    if kind == "CHS":
        r = max(1.0 - n ** 1.7, 0.0)
        return r, r, 2.0, 2.0
    if kind in ("RHS", "SHS"):
        area = geom["area"]
        aw = min((area - 2.0 * geom["b"] * geom["t"]) / area, 0.5) if area else 0.5
        af = min((area - 2.0 * geom["h"] * geom["t"]) / area, 0.5) if area else 0.5
        mny = min((1.0 - n) / (1.0 - 0.5 * aw), 1.0)
        mnz = min((1.0 - n) / (1.0 - 0.5 * af), 1.0)
        denom = 1.0 - 1.13 * n * n
        ab = min(1.66 / denom, 6.0) if denom > 0 else 6.0
        return mny, mnz, ab, ab
    # I / H sections (default)
    area = geom["area"]
    a = min((area - 2.0 * geom["b"] * geom["tf"]) / area, 0.5) if area else 0.5
    mny = min((1.0 - n) / (1.0 - 0.5 * a), 1.0)
    mnz = 1.0 if n <= a else max(1.0 - ((n - a) / (1.0 - a)) ** 2, 0.0)
    beta = max(5.0 * n, 1.0)
    return mny, mnz, 2.0, beta


# ── inputs / results ────────────────────────────────────────────────────────

@dataclass
class SectionForces:
    """Design forces on the cross-section (compression N positive)."""

    n_ed: float = 0.0     # axial [kN]
    my_ed: float = 0.0    # major-axis bending [kNm]
    mz_ed: float = 0.0    # minor-axis bending [kNm]
    vy_ed: float = 0.0    # shear parallel to y (in the flanges) [kN]
    vz_ed: float = 0.0    # shear parallel to z (in the web) [kN]
    t_ed: float = 0.0     # torsion [kNm]


@dataclass
class SectionResistanceResult:
    """Result of the §6.2 cross-section verification."""

    util_shear_y: float
    util_shear_z: float
    util_torsion: float
    util_bending_axial: float
    utilization: float                # governing
    passed: bool
    vpl_rd_y: float                   # [kN]
    vpl_rd_z: float                   # [kN]
    t_rd: float                       # [kNm]
    npl_rd: float                     # [kN]
    shear_reduces_moment: bool
    web_shear_buckling: bool
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Readable summary of the section check."""
        return (
            f"EC3 §6.2 section check — {'PASS' if self.passed else 'FAIL'}\n"
            f"  shear:   Vy {self.util_shear_y:.3f} | Vz {self.util_shear_z:.3f}\n"
            f"  torsion: {self.util_torsion:.3f}\n"
            f"  N+My+Mz: {self.util_bending_axial:.3f}\n"
            f"  → utilization {self.utilization:.3f}"
        )


@dataclass
class SectionResistanceInput:
    """Cross-section data for the §6.2 check (mm / N units)."""

    kind: str = "I"                   # 'I' | 'RHS' | 'SHS' | 'CHS'
    section_class: int = 1
    fy: float = 355.0                 # [N/mm²]
    gamma_M0: float = 1.0
    # geometry [mm]
    area: float = 0.0
    area_eff: float | None = None
    b: float = 0.0
    h: float = 0.0
    tw: float = 0.0
    tf: float = 0.0
    hw: float = 0.0                   # clear web depth (I) [mm]
    eps: float = 1.0                  # material factor √(235/fy)
    # resistance moduli [mm³]
    wpl_y: float = 0.0
    wpl_z: float = 0.0
    wel_y: float = 0.0
    wel_z: float = 0.0
    weff_y: float = 0.0
    weff_z: float = 0.0
    wt: float = 0.0                   # torsional modulus [mm³]
    av_y: float = 0.0                 # shear area (flanges) [mm²]
    av_z: float = 0.0                 # shear area (web) [mm²]
    # Class-4 centroid shift additional moments [kNm]
    d_my: float = 0.0
    d_mz: float = 0.0


def eurocode3_section_check(inp: SectionResistanceInput,
                            f: SectionForces,
                            trace=None) -> SectionResistanceResult:
    """Verify a cross-section under N + My + Mz + Vy + Vz + T (EN 1993-1-1 §6.2).

    Args:
        inp: The cross-section data.
        f: The design forces.
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps (clause, expression, substitution,
            value) into it. ``None`` (default) is a no-op and leaves the result
            identical — the trace only *records* what was computed.

    Returns:
        A :class:`SectionResistanceResult` with the shear, torsion and
        bending+axial utilisations, the governing value and pass/fail.

    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    fy, gm0 = inp.fy, inp.gamma_M0
    hollow = inp.kind in ("RHS", "SHS", "CHS")
    area = inp.area
    area_eff = inp.area_eff if inp.area_eff is not None else area

    _sec("Inputs")
    _t("N_Ed", f.n_ed,
       "kN (compression)" if f.n_ed >= 0 else "kN (tension)")
    _t("My_Ed", f.my_ed, "kNm")
    _t("Mz_Ed", f.mz_ed, "kNm")
    _t("Vy_Ed", f.vy_ed, "kN")
    _t("Vz_Ed", f.vz_ed, "kN")
    _t("T_Ed", f.t_ed, "kNm")
    _t("f_y", fy, "N/mm²")
    _t("γ_M0", gm0, "—", clause="EN 1993-1-1 §6.1")
    _t("Section class", inp.section_class, "—", clause="EN 1993-1-1 §5.5",
       note=f"{inp.kind} section")

    # ── shear resistances (with torsion reduction) ──
    vpl_y = shear_resistance(inp.av_y, fy, gm0)
    vpl_z = shear_resistance(inp.av_z, fy, gm0)
    t_rd = torsion_resistance(inp.wt, fy, gm0)
    tau_t = (abs(f.t_ed) * 1e6 / inp.wt) if inp.wt > 0 else 0.0
    if f.t_ed != 0.0 and inp.wt > 0:
        vpl_ty = reduced_shear_resistance_torsion(vpl_y, tau_t, fy, gm0, hollow=hollow)
        vpl_tz = reduced_shear_resistance_torsion(vpl_z, tau_t, fy, gm0, hollow=hollow)
    else:
        vpl_ty, vpl_tz = vpl_y, vpl_z

    u_vy = abs(f.vy_ed) / vpl_ty if vpl_ty > 0 else 0.0
    u_vz = abs(f.vz_ed) / vpl_tz if vpl_tz > 0 else 0.0
    u_t = abs(f.t_ed) / t_rd if math.isfinite(t_rd) and t_rd > 0 else 0.0

    web_sb = shear_buckling_susceptible(inp.hw, inp.tw, inp.eps)

    _sec("Shear resistance (§6.2.6)")
    _t("Vpl,Rd,y", vpl_y, "kN", clause="EN 1993-1-1 §6.2.6(2)",
       expr="Vpl,Rd = A_v·(f_y/√3)/γ_M0",
       latex=r"V_{pl,Rd}=\frac{A_v (f_y/\sqrt3)}{\gamma_{M0}}",
       subst=f"{inp.av_y:.0f}·({fy:.0f}/√3)/{gm0:g}/1e3")
    _t("Vpl,Rd,z", vpl_z, "kN", clause="EN 1993-1-1 §6.2.6(2)",
       expr="Vpl,Rd = A_v·(f_y/√3)/γ_M0",
       subst=f"{inp.av_z:.0f}·({fy:.0f}/√3)/{gm0:g}/1e3")
    if web_sb:
        _t("Web shear buckling", "check", "—", clause="EN 1993-1-1 §6.2.6(6)",
           expr="h_w/t_w > 72·ε/η", note="slender web — verify per EN 1993-1-5")
    if f.t_ed != 0.0 and inp.wt > 0:
        _sec("Torsion (§6.2.7)")
        _t("τ_t,Ed", tau_t, "N/mm²", expr="τ_t = T_Ed/W_t")
        _t("T_Rd", t_rd, "kNm", clause="EN 1993-1-1 §6.2.7",
           expr="T_Rd = W_t·(f_y/√3)/γ_M0")
        _t("Vpl,T,Rd,y", vpl_ty, "kN", clause="EN 1993-1-1 §6.2.7(9)",
           note="torsion-reduced shear resistance")
        _t("Vpl,T,Rd,z", vpl_tz, "kN", clause="EN 1993-1-1 §6.2.7(9)")
        _t("U_T = T_Ed/T_Rd", u_t, "—", ok=u_t <= 1.0)
    _t("U_Vy = Vy_Ed/Vpl,Rd,y", u_vy, "—", clause="EN 1993-1-1 §6.2.6",
       ok=u_vy <= 1.0)
    _t("U_Vz = Vz_Ed/Vpl,Rd,z", u_vz, "—", clause="EN 1993-1-1 §6.2.6",
       ok=u_vz <= 1.0)

    # ── shear → moment reduction (§6.2.8): ρ when V > 0.5·Vpl ──
    def _rho(v_ed, vpl):
        if vpl <= 0 or abs(v_ed) <= 0.5 * vpl:
            return 0.0
        return (2.0 * abs(v_ed) / vpl - 1.0) ** 2

    rho_z = _rho(f.vz_ed, vpl_tz)     # affects My (web shear)
    rho_y = _rho(f.vy_ed, vpl_ty)     # affects Mz (flange shear)
    shear_reduces = rho_z > 0.0 or rho_y > 0.0

    if shear_reduces:
        _sec("Shear–moment reduction (§6.2.8)")
        _t("ρ_z", rho_z, "—", clause="EN 1993-1-1 §6.2.8",
           expr="ρ = (2·V_Ed/Vpl,Rd − 1)²  for V_Ed > 0.5·Vpl,Rd",
           latex=r"\rho=\left(\frac{2V_{Ed}}{V_{pl,Rd}}-1\right)^2",
           note="reduces My")
        _t("ρ_y", rho_y, "—", clause="EN 1993-1-1 §6.2.8", note="reduces Mz")

    # ── bending + axial ──
    npl_rd = area_eff * fy / gm0 / 1e3
    my, mz = f.my_ed, f.mz_ed

    _sec("Bending + axial (§6.2.9)")
    _t("Npl,Rd", npl_rd, "kN", clause="EN 1993-1-1 §6.2.4",
       expr="Npl,Rd = A·f_y/γ_M0",
       subst=f"{area_eff:.0f}·{fy:.0f}/{gm0:g}/1e3")

    if inp.section_class <= 2:
        # Plastic. Reduce Wpl for high coincident shear (§6.2.8): the web area
        # loses (1 − (1 − ρ)) of its contribution to Wpl,y (and flanges to Wpl,z).
        wpl_y = inp.wpl_y
        wpl_z = inp.wpl_z
        # §6.2.8: web shear reduces Wpl,y by ρ·Aw²/(4·tw); flange shear reduces
        # Wpl,z (no closed form → the conservative (1 − ρ) factor is used).
        if rho_z > 0 and inp.tw > 0:
            aw = inp.hw * inp.tw if inp.hw > 0 else inp.av_z
            wpl_y = max(inp.wpl_y - rho_z * aw ** 2 / (4.0 * inp.tw), 0.0)
        if rho_y > 0:
            wpl_z = inp.wpl_z * (1.0 - rho_y)
        mpl_y = wpl_y * fy / gm0 / 1e6
        mpl_z = wpl_z * fy / gm0 / 1e6
        n = abs(f.n_ed) / npl_rd if npl_rd > 0 else 0.0
        geom = {"area": area, "b": inp.b, "h": inp.h,
                "tf": inp.tf, "t": inp.tw}
        rny, rnz, alpha, beta = _mn_reduction(inp.kind, n, geom)
        mn_y = rny * mpl_y
        mn_z = rnz * mpl_z
        ratio_y = abs(my) / mn_y if mn_y > 0 else (math.inf if my else 0.0)
        ratio_z = abs(mz) / mn_z if mn_z > 0 else (math.inf if mz else 0.0)
        interaction = ratio_y ** alpha + ratio_z ** beta
        # Report the governing utilisation: the biaxial interaction unity check
        # plus the individual limits (so a uniaxial case reads as the linear
        # ratio, and pure axial as N/Npl,Rd — §6.2.4/§6.2.9).
        u_nm = max(interaction, ratio_y, ratio_z, n)
        _t("n = N_Ed/Npl,Rd", n, "—")
        _t("Mpl,Rd,y", mpl_y, "kNm", expr="Mpl,Rd = W_pl,y·f_y/γ_M0")
        _t("Mpl,Rd,z", mpl_z, "kNm", expr="Mpl,Rd = W_pl,z·f_y/γ_M0")
        _t("MN,Rd,y", mn_y, "kNm", clause="EN 1993-1-1 §6.2.9.1",
           note="axial-reduced plastic moment")
        _t("MN,Rd,z", mn_z, "kNm", clause="EN 1993-1-1 §6.2.9.1")
        _t("Interaction", interaction, "—", clause="EN 1993-1-1 §6.2.9.1(6)",
           expr="(My/MN,y)^α + (Mz/MN,z)^β ≤ 1",
           latex=r"\left(\frac{M_y}{M_{N,y}}\right)^{\alpha}"
                 r"+\left(\frac{M_z}{M_{N,z}}\right)^{\beta}\le1",
           subst=f"({abs(my):.4g}/{mn_y:.4g})^{alpha:g}"
                 f"+({abs(mz):.4g}/{mn_z:.4g})^{beta:g}")
    else:
        # Elastic (Class 3) / effective (Class 4): σx,Ed ≤ fy/γM0.
        if inp.section_class == 3 or (inp.weff_y <= 0 and inp.weff_z <= 0):
            a_use, wy, wz = area, inp.wel_y, inp.wel_z
            dmy = dmz = 0.0
        else:
            a_use, wy, wz = area_eff, inp.weff_y, inp.weff_z
            dmy, dmz = inp.d_my, inp.d_mz
        sig = abs(f.n_ed) * 1e3 / a_use if a_use > 0 else 0.0
        sig += abs(my + dmy) * 1e6 / wy if wy > 0 else 0.0
        sig += abs(mz + dmz) * 1e6 / wz if wz > 0 else 0.0
        # Reduce the yield on the shear-affected fibre when V is high (§6.2.10).
        fyd = fy / gm0
        u_nm = sig / fyd if fyd > 0 else 0.0
        if rho_z > 0:
            u_nm = max(u_nm, sig / (fyd * math.sqrt(max(1.0 - rho_z, 1e-9))))
        cls_note = ("elastic (Class 3)" if inp.section_class == 3
                    else "effective (Class 4)")
        _t("σ_x,Ed", sig, "N/mm²", clause="EN 1993-1-1 §6.2.9.2/§6.2.9.3",
           expr="σ_x = N/A + My/W_y + Mz/W_z", note=cls_note)
        _t("f_yd", fyd, "N/mm²", expr="f_yd = f_y/γ_M0")
        _t("U = σ_x,Ed/f_yd", u_nm, "—", ok=u_nm <= 1.0)

    utilization = max(u_vy, u_vz, u_t, u_nm)
    _sec("Combined utilisation (§6.2.10)")
    _t("U_N+M", u_nm, "—", ok=u_nm <= 1.0)
    _t("Utilisation", utilization, "—", clause="EN 1993-1-1 §6.2.1(7)",
       expr="max(U_Vy, U_Vz, U_T, U_N+M) ≤ 1", ok=utilization <= 1.0,
       note="governing cross-section check")
    return SectionResistanceResult(
        util_shear_y=u_vy, util_shear_z=u_vz, util_torsion=u_t,
        util_bending_axial=u_nm, utilization=utilization,
        passed=utilization <= 1.0,
        vpl_rd_y=vpl_ty, vpl_rd_z=vpl_tz, t_rd=t_rd, npl_rd=npl_rd,
        shear_reduces_moment=shear_reduces, web_shear_buckling=web_sb,
        details={"rho_z": rho_z, "rho_y": rho_y, "tau_t": tau_t,
                 "vpl_rd_y_no_T": vpl_y, "vpl_rd_z_no_T": vpl_z})


# ── convenience: build the input from a eurocodepy profile ─────────────────

def section_check_profile(profile, fy: float, forces: SectionForces, *,  # ruff: ignore[missing-type-function-argument]
                          gamma_M0: float = 1.0) -> SectionResistanceResult:
    """Run the §6.2 check for a eurocodepy profile under the given forces.

    The section is classified under N + My; the resistance moduli, shear areas,
    torsional modulus and (for Class 4) effective properties are taken from the
    profile / classification. Geometry is read from the profile (cm → mm).
    """
    from eurocodepy.ec3 import classification as _cl

    cm2, cm3, cm4 = 1e2, 1e3, 1e4
    kind = getattr(profile, "type", "I").upper()
    area = float(profile.A) * cm2
    b = float(profile.b) * 10.0
    h = float(profile.h) * 10.0
    tw = float(profile.tw) * 10.0
    tf = float(profile.tf) * 10.0
    r = float(getattr(profile, "r", 0.0) or 0.0) * 10.0
    hw = h - 2.0 * tf - 2.0 * r if kind == "I" else h - 2.0 * tw

    res = _cl.classify_section(profile, fy, n_ed=forces.n_ed, m_ed=forces.my_ed)
    cls = int(res.section_class)
    d_my = d_mz = 0.0
    weff_y = weff_z = 0.0
    area_eff = area
    if cls == 4:
        eff = _cl.effective_properties(profile, fy)
        area_eff = eff.A_eff
        weff_y = eff.W_eff_y
        weff_z = float(profile.Wel_z) * cm3
        d_my = forces.n_ed * eff.e_Ny / 1e3

    inp = SectionResistanceInput(
        kind=kind, section_class=cls, fy=fy, gamma_M0=gamma_M0,
        area=area, area_eff=area_eff, b=b, h=h, tw=tw, tf=tf, hw=hw,
        eps=_cl.epsilon(fy),
        wpl_y=float(profile.Wpl_y) * cm3, wpl_z=float(profile.Wpl_z) * cm3,
        wel_y=float(profile.Wel_y) * cm3, wel_z=float(profile.Wel_z) * cm3,
        weff_y=weff_y, weff_z=weff_z,
        wt=float(getattr(profile, "WT", 0.0)) * cm3,
        av_y=float(profile.Av_y) * cm2, av_z=float(profile.Av_z) * cm2,
        d_my=d_my, d_mz=d_mz)
    return eurocode3_section_check(inp, forces)
