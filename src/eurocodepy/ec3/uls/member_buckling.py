# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1993-1-1 §6.3.3 member stability check under combined N + My + Mz.

This module verifies a uniform steel member subjected to an axial force and
bi-axial bending against the two interaction equations (6.61) and (6.62),
accounting for flexural buckling about both axes (§6.3.1), lateral-torsional
buckling (§6.3.2) and the interaction factors ``kij`` of Annex B (Method 2).

Consistent units
----------------
Forces in **kN**, moments in **kNm**, lengths and section dimensions in **mm**
(so areas mm², moduli mm³, second moments mm⁴, the warping constant mm⁶), and
stresses / moduli in **N/mm² (MPa)**. Internally everything is reduced to N and
N·mm.

The cross-section resistances follow the section class: plastic moduli for
Class 1–2, elastic for Class 3, effective (``Weff``, ``Aeff``) for Class 4 —
the caller supplies the already-selected moduli, or uses
:func:`member_check_profile`, which derives them from the profile via
:mod:`eurocodepy.ec3.classification`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

E_STEEL = 210_000.0     # Young's modulus [N/mm²]
G_STEEL = 81_000.0      # shear modulus [N/mm²]

# Imperfection factors α for the flexural buckling curves (Table 6.1) and for
# the lateral-torsional buckling curves (Table 6.3).
_ALPHA = {"a0": 0.13, "a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}


# ── reduction factors ───────────────────────────────────────────────────────

def reduction_chi(lambda_bar: float, curve: str = "b") -> float:
    """Flexural-buckling reduction factor χ (EN 1993-1-1 §6.3.1.2).

    Args:
        lambda_bar: Non-dimensional slenderness λ̄.
        curve: Buckling curve ``'a0' | 'a' | 'b' | 'c' | 'd'``.

    Returns:
        χ ≤ 1.0 (and χ = 1.0 for λ̄ ≤ 0.2).

    """
    if lambda_bar <= 0.2:
        return 1.0
    alpha = _ALPHA.get(curve, 0.34)
    phi = 0.5 * (1.0 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    return min(1.0 / (phi + math.sqrt(max(phi**2 - lambda_bar**2, 0.0))), 1.0)


def reduction_chi_lt(lambda_lt: float, curve: str = "b",
                     *, rolled: bool = True,
                     lambda_lt0: float = 0.4, beta: float = 0.75) -> float:
    """Lateral-torsional buckling reduction factor χ_LT.

    With ``rolled=True`` the method for rolled / equivalent-welded sections is
    used (§6.3.2.3): ``Φ_LT = 0.5·[1 + α_LT·(λ̄_LT − λ̄_LT,0) + β·λ̄_LT²]`` and
    ``χ_LT ≤ min(1, 1/λ̄_LT²)``. With ``rolled=False`` the general case
    (§6.3.2.2) is used (``λ̄_LT,0 = 0.2``, ``β = 1``). LTB is ignored
    (χ_LT = 1) below ``λ̄_LT,0``.

    Args:
        lambda_lt: Non-dimensional LTB slenderness λ̄_LT.
        curve: LTB buckling curve.
        rolled: Use the rolled / welded method (§6.3.2.3) when True.
        lambda_lt0: Plateau length λ̄_LT,0 (0.4 for rolled).
        beta: Factor β (0.75 for rolled).

    Returns:
        χ_LT ≤ 1.0.

    """
    if not rolled:
        lambda_lt0, beta = 0.2, 1.0
    if lambda_lt <= lambda_lt0:
        return 1.0
    alpha = _ALPHA.get(curve, 0.34)
    phi = 0.5 * (1.0 + alpha * (lambda_lt - lambda_lt0) + beta * lambda_lt**2)
    chi = 1.0 / (phi + math.sqrt(max(phi**2 - beta * lambda_lt**2, 0.0)))
    cap = min(1.0, 1.0 / lambda_lt**2) if rolled else 1.0
    return min(chi, cap)


def elastic_critical_moment(iz: float, it: float, iw: float, length: float,
                            c1: float = 1.0, e: float = E_STEEL,
                            g: float = G_STEEL) -> float:
    """Elastic critical moment M_cr for LTB of a doubly-symmetric section [N·mm].

    Standard closed form for end-moment loading, no load-application offset and
    ``k = kw = 1``:
    ``M_cr = C1·π²·E·Iz/L²·√(Iw/Iz + L²·G·It/(π²·E·Iz))``.

    Args:
        iz: Minor-axis second moment of area [mm⁴].
        it: St-Venant torsion constant [mm⁴].
        iw: Warping constant [mm⁶].
        length: Buckling length for LTB [mm].
        c1: Equivalent-moment factor C1.
        e: Young's modulus [N/mm²].
        g: Shear modulus [N/mm²].

    Returns:
        M_cr [N·mm].

    """
    if iz <= 0.0 or length <= 0.0:
        return math.inf
    pi2eiz = math.pi**2 * e * iz
    root = iw / iz + (length**2 * g * it) / pi2eiz
    return c1 * pi2eiz / length**2 * math.sqrt(max(root, 0.0))


# ── elastic critical buckling forces (§6.3.1) ───────────────────────────────

def calc_Ncr(e: float, i: float, length: float, k: float = 1.0) -> float:
    """Euler critical buckling force ``Ncr = π²·E·I/(K·L)²`` [same force unit].

    Args:
        e: Young's modulus.
        i: Second moment of area about the buckling axis.
        length: Member length.
        k: Buckling-length factor (0.5 fixed-fixed, 1.0 pinned-pinned, …).

    Returns:
        The Euler critical load (consistent units).

    """
    leff = k * length
    return (math.pi**2 * e * i) / (leff**2) if leff > 0 else math.inf


def calc_Ncr_T(e: float, g: float, i_w: float, i_t: float,
               length: float) -> float:
    """Torsional buckling load ``Ncr,T = π²·E·Iw/L² + G·It`` (§6.3.1.4).

    Args:
        e: Young's modulus.
        g: Shear modulus.
        i_w: Warping constant.
        i_t: Torsion constant.
        length: Effective length.

    Returns:
        Torsional buckling load.

    """
    return (math.pi**2 * e * i_w) / (length**2) + g * i_t


def calc_Ncr_TF(e: float, g: float, length: float, iy: float, it: float,
                iw: float, area: float, ey: float,
                ky: float = 1.0, kt: float = 1.0) -> float:
    """Torsional-flexural buckling load ``Ncr,TF`` (EN 1993-1-1 §6.3.1.4).

    Combines the y-axis Euler load and the torsional load. ``ey`` is the
    shear-centre-to-centroid distance and ``area`` the cross-sectional area
    (kept for interface completeness / future coupling terms).

    Args:
        e: Young's modulus.
        g: Shear modulus.
        length: Member length.
        iy: Second moment of area about y.
        it: Torsion constant.
        iw: Warping constant.
        area: Cross-sectional area.
        ey: Shear-centre-to-centroid distance.
        ky: Flexural buckling-length factor.
        kt: Torsional buckling-length factor.

    Returns:
        Critical torsional-flexural load.

    """
    ly, lt = ky * length, kt * length
    ncr_y = (math.pi**2 * e * iy) / (ly**2)
    ncr_t = (g * it * math.pi**2 / lt**2) + (e * iw * math.pi**4 / lt**4)
    return 1.0 / ((1.0 / ncr_y) + (1.0 / ncr_t))


# ── Annex B interaction factors (Method 2) ─────────────────────────────────

def cm_factor(psi: float) -> float:
    """Equivalent uniform moment factor C_m for a linear moment diagram
    (Annex B, Table B.3): ``Cm = 0.6 + 0.4·ψ ≥ 0.4`` where ψ ∈ [−1, 1] is the
    end-moment ratio.
    """
    return max(0.6 + 0.4 * psi, 0.4)


def _interaction_factors(n_y: float, n_z: float,
                         lam_y: float, lam_z: float,
                         cmy: float, cmz: float, cm_lt: float,
                         cls: int, susceptible_lt: bool) -> tuple:
    """Return (kyy, kyz, kzy, kzz) per Annex B (Method 2), Tables B.1 / B.2."""
    plastic = cls in (1, 2)
    # kyy, kzz — common to both tables.
    if plastic:
        kyy = cmy * min(1.0 + (lam_y - 0.2) * n_y, 1.0 + 0.8 * n_y)
        kzz = cmz * min(1.0 + (lam_z - 0.2) * n_z, 1.0 + 0.8 * n_z)
    else:
        kyy = cmy * min(1.0 + 0.6 * lam_y * n_y, 1.0 + 0.6 * n_y)
        kzz = cmz * min(1.0 + 0.6 * lam_z * n_z, 1.0 + 0.6 * n_z)
    kyz = 0.6 * kzz if plastic else kzz

    if not susceptible_lt:
        kzy = 0.6 * kyy if plastic else kyy
        return kyy, kyz, kzy, kzz

    # Members susceptible to torsional deformations — Table B.2 kzy.
    denom = cm_lt - 0.25
    coef = 0.1 if plastic else 0.05
    if denom <= 0.0:
        kzy = 1.0
    elif lam_z < 0.4 and plastic:
        kzy = min(0.6 + lam_z, 1.0 - (coef * lam_z) / denom * n_z)
    else:
        kzy = max(1.0 - (coef * lam_z) / denom * n_z,
                  1.0 - coef / denom * n_z)
    return kyy, kyz, kzy, kzz


# ── inputs / results ────────────────────────────────────────────────────────

@dataclass
class MemberInput:
    """Everything needed for a §6.3.3 check of one uniform member.

    Forces are design values; a compressive N_Ed is **positive**. Section
    moduli ``w_y`` / ``w_z`` must already match the section class (plastic for
    Class 1–2, elastic for Class 3, effective for Class 4); ``area`` is the
    gross area and ``area_eff`` the effective one (Class 4, defaults to gross).
    """

    # forces
    n_ed: float                       # axial force [kN], compression +
    my_ed: float = 0.0                # bending about y (major) [kNm]
    mz_ed: float = 0.0                # bending about z (minor) [kNm]
    # cross-section (mm units) and resistance moduli
    area: float = 0.0                 # gross area [mm²]
    area_eff: float | None = None     # effective area [mm²] (Class 4)
    w_y: float = 0.0                  # section modulus about y [mm³]
    w_z: float = 0.0                  # section modulus about z [mm³]
    iy: float = 0.0                   # second moment about y [mm⁴]
    iz: float = 0.0                   # second moment about z [mm⁴]
    it: float = 0.0                   # torsion constant [mm⁴]
    iw: float = 0.0                   # warping constant [mm⁶]
    # member geometry
    lcr_y: float = 0.0                # buckling length, y-axis [mm]
    lcr_z: float = 0.0                # buckling length, z-axis [mm]
    l_lt: float = 0.0                 # LTB length [mm] (defaults to lcr_z)
    # curves and moment factors
    curve_y: str = "a"
    curve_z: str = "b"
    curve_lt: str = "b"
    c1: float = 1.0                   # C1 for M_cr
    cmy: float = 0.9
    cmz: float = 0.9
    cm_lt: float = 0.9
    # material / safety
    fy: float = 355.0                 # yield strength [N/mm²]
    e_mod: float = E_STEEL
    g_mod: float = G_STEEL
    gamma_m1: float = 1.0
    # classification & options
    section_class: int = 1
    susceptible_lt: bool = True       # member can undergo LTB
    rolled_lt: bool = True            # use §6.3.2.3 for χ_LT
    # Class-4 additional moments from the centroid shift N·e_N [kNm]
    d_my: float = 0.0
    d_mz: float = 0.0
    m_cr: float | None = None         # override the computed M_cr [N·mm]


@dataclass
class MemberCheckResult:
    """Result of the §6.3.3 combined member check."""

    util_6_61: float
    util_6_62: float
    utilization: float                # max of the two
    passed: bool
    # resistances [kN, kNm]
    n_rk: float
    my_rk: float
    mz_rk: float
    chi_y: float
    chi_z: float
    chi_lt: float
    lambda_y: float
    lambda_z: float
    lambda_lt: float
    m_cr: float                       # [kNm]
    kyy: float
    kyz: float
    kzy: float
    kzz: float
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Readable summary of the member check."""
        return (
            f"EC3 §6.3.3 member check — {'PASS' if self.passed else 'FAIL'}\n"
            f"  (6.61) = {self.util_6_61:.3f}\n"
            f"  (6.62) = {self.util_6_62:.3f}   → utilization {self.utilization:.3f}\n"
            f"  χy={self.chi_y:.3f} χz={self.chi_z:.3f} χLT={self.chi_lt:.3f}\n"
            f"  λ̄y={self.lambda_y:.3f} λ̄z={self.lambda_z:.3f} "
            f"λ̄LT={self.lambda_lt:.3f}\n"
            f"  kyy={self.kyy:.3f} kyz={self.kyz:.3f} "
            f"kzy={self.kzy:.3f} kzz={self.kzz:.3f}"
        )


# ── the check ───────────────────────────────────────────────────────────────

def eurocode3_member_check(inp: MemberInput, trace=None) -> MemberCheckResult:
    """Verify a member under N + My + Mz (EN 1993-1-1 Eqs 6.61 & 6.62).

    Args:
        inp: A :class:`MemberInput` with the forces, section properties, member
            geometry, buckling curves, moment factors and material.
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps (clause, expression, substitution, value)
            into it for a full calculation report. ``None`` (default) is a no-op
            and leaves the computed result identical — the trace only *records*.

    Returns:
        A :class:`MemberCheckResult` with both interaction utilizations, the
        governing value and pass/fail, plus the buckling reduction factors,
        slendernesses and interaction factors used.

    """
    rep = trace

    def _t(*a, **k):                       # record a step only in explain mode
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    fy = inp.fy
    area = inp.area
    area_eff = inp.area_eff if inp.area_eff is not None else area
    gm1 = inp.gamma_m1
    l_lt = inp.l_lt or inp.lcr_z

    _sec("Inputs")
    _t("N_Ed", inp.n_ed, "kN", note="compression positive")
    _t("My_Ed", inp.my_ed, "kNm")
    _t("Mz_Ed", inp.mz_ed, "kNm")
    _t("f_y", fy, "N/mm²")
    _t("γ_M1", gm1, "—", clause="EN 1993-1-1 §6.1")
    _t("L_cr,y", inp.lcr_y, "mm")
    _t("L_cr,z", inp.lcr_z, "mm")
    _t("L_LT", l_lt, "mm")

    # ── characteristic resistances (N, N·mm) ──
    n_rk = area_eff * fy                       # [N]  (Aeff = A for class 1-3)
    my_rk = inp.w_y * fy                        # [N·mm]
    mz_rk = inp.w_z * fy

    _sec("Characteristic resistances (§6.2)")
    _t("N_Rk", n_rk / 1e3, "kN", clause="EN 1993-1-1 §6.3.1.3",
       expr="N_Rk = A_eff·f_y",
       subst=f"{area_eff:.0f}·{fy:.0f}/1e3")
    _t("My_Rk", my_rk / 1e6, "kNm", expr="My_Rk = W_y·f_y",
       subst=f"{inp.w_y:.0f}·{fy:.0f}/1e6")
    _t("Mz_Rk", mz_rk / 1e6, "kNm", expr="Mz_Rk = W_z·f_y")

    # ── flexural buckling ──
    def _lambda(icr_i, lcr):
        ncr = math.pi**2 * inp.e_mod * icr_i / lcr**2 if lcr > 0 else math.inf
        return math.sqrt(area_eff * fy / ncr) if ncr > 0 else 0.0

    lam_y = _lambda(inp.iy, inp.lcr_y)
    lam_z = _lambda(inp.iz, inp.lcr_z)
    chi_y = reduction_chi(lam_y, inp.curve_y)
    chi_z = reduction_chi(lam_z, inp.curve_z)

    # Elastic critical loads, recomputed here only for the report substitution
    # (identical to what `_lambda` used above — display only, no effect on the
    # result).
    ncr_y = (math.pi**2 * inp.e_mod * inp.iy / inp.lcr_y**2
             if inp.lcr_y > 0 else math.inf)
    ncr_z = (math.pi**2 * inp.e_mod * inp.iz / inp.lcr_z**2
             if inp.lcr_z > 0 else math.inf)
    _sec("Flexural buckling (§6.3.1)")
    _t("N_cr,y", ncr_y / 1e3, "kN", clause="EN 1993-1-1 §6.3.1.3",
       expr="N_cr,y = π²·E·I_y / L_cr,y²",
       latex=r"N_{cr,y}=\frac{\pi^2 E I_y}{L_{cr,y}^2}",
       subst=f"π²·{inp.e_mod:.0f}·{inp.iy:.4g}/{inp.lcr_y:.0f}²/1e3")
    _t("λ̄_y", lam_y, "—", clause="EN 1993-1-1 §6.3.1.2",
       expr="λ̄_y = √(A_eff·f_y / N_cr,y)",
       latex=r"\bar\lambda_y=\sqrt{A_{eff}f_y/N_{cr,y}}",
       subst=f"√({area_eff:.0f}·{fy:.0f}/{ncr_y:.4g})")
    _t("χ_y", chi_y, "—", clause="EN 1993-1-1 §6.3.1.2",
       expr="χ = 1/(Φ+√(Φ²−λ̄²)) ≤ 1",
       latex=r"\chi=\frac{1}{\Phi+\sqrt{\Phi^2-\bar\lambda^2}}\le1",
       note=f"buckling curve {inp.curve_y}")
    _t("N_cr,z", ncr_z / 1e3, "kN", clause="EN 1993-1-1 §6.3.1.3",
       expr="N_cr,z = π²·E·I_z / L_cr,z²",
       latex=r"N_{cr,z}=\frac{\pi^2 E I_z}{L_{cr,z}^2}",
       subst=f"π²·{inp.e_mod:.0f}·{inp.iz:.4g}/{inp.lcr_z:.0f}²/1e3")
    _t("λ̄_z", lam_z, "—", clause="EN 1993-1-1 §6.3.1.2",
       expr="λ̄_z = √(A_eff·f_y / N_cr,z)",
       latex=r"\bar\lambda_z=\sqrt{A_{eff}f_y/N_{cr,z}}",
       subst=f"√({area_eff:.0f}·{fy:.0f}/{ncr_z:.4g})")
    _t("χ_z", chi_z, "—", clause="EN 1993-1-1 §6.3.1.2",
       expr="χ = 1/(Φ+√(Φ²−λ̄²)) ≤ 1",
       latex=r"\chi=\frac{1}{\Phi+\sqrt{\Phi^2-\bar\lambda^2}}\le1",
       note=f"buckling curve {inp.curve_z}")

    # ── lateral-torsional buckling ──
    if inp.susceptible_lt and inp.my_ed != 0.0:
        m_cr = inp.m_cr if inp.m_cr is not None else elastic_critical_moment(
            inp.iz, inp.it, inp.iw, l_lt, inp.c1, inp.e_mod, inp.g_mod)
        lam_lt = math.sqrt(my_rk / m_cr) if m_cr > 0 else 0.0
        chi_lt = reduction_chi_lt(lam_lt, inp.curve_lt, rolled=inp.rolled_lt)
    else:
        m_cr = math.inf
        lam_lt = 0.0
        chi_lt = 1.0

    _sec("Lateral-torsional buckling (§6.3.2)")
    _t("M_cr", m_cr / 1e6 if math.isfinite(m_cr) else math.inf, "kNm",
       clause="EN 1993-1-1 §6.3.2",
       expr="M_cr = C1·π²EI_z/L² · √(I_w/I_z + L²·G·I_t/(π²EI_z))",
       latex=r"M_{cr}=C_1\frac{\pi^2EI_z}{L^2}"
             r"\sqrt{\frac{I_w}{I_z}+\frac{L^2 G I_t}{\pi^2 E I_z}}",
       note="LTB not relevant" if not math.isfinite(m_cr) else f"C₁={inp.c1:g}")
    _t("λ̄_LT", lam_lt, "—", clause="EN 1993-1-1 §6.3.2.2",
       expr="λ̄_LT = √(My_Rk / M_cr)",
       latex=r"\bar\lambda_{LT}=\sqrt{M_{y,Rk}/M_{cr}}",
       subst=(f"√({my_rk / 1e6:.4g}/{m_cr / 1e6:.4g})"
              if math.isfinite(m_cr) else ""))
    _t("χ_LT", chi_lt, "—", clause="EN 1993-1-1 §6.3.2.3",
       expr="χ_LT = 1/(Φ_LT+√(Φ_LT²−β·λ̄_LT²)) ≤ 1",
       latex=r"\chi_{LT}=\frac{1}{\Phi_{LT}+"
             r"\sqrt{\Phi_{LT}^2-\beta\bar\lambda_{LT}^2}}\le1",
       note=f"curve {inp.curve_lt}, {'rolled' if inp.rolled_lt else 'welded'}")

    # ── design resistances (kN, kNm) ──
    n_b_rd_y = chi_y * n_rk / gm1 / 1e3
    n_b_rd_z = chi_z * n_rk / gm1 / 1e3
    my_b_rd = chi_lt * my_rk / gm1 / 1e6
    mz_rd = mz_rk / gm1 / 1e6

    _sec("Design resistances")
    _t("N_b,Rd,y", n_b_rd_y, "kN", clause="EN 1993-1-1 §6.3.1.1",
       expr="N_b,Rd,y = χ_y·N_Rk/γ_M1",
       latex=r"N_{b,Rd,y}=\chi_y N_{Rk}/\gamma_{M1}",
       subst=f"{chi_y:.3f}·{n_rk / 1e3:.4g}/{gm1:g}")
    _t("N_b,Rd,z", n_b_rd_z, "kN", clause="EN 1993-1-1 §6.3.1.1",
       expr="N_b,Rd,z = χ_z·N_Rk/γ_M1",
       latex=r"N_{b,Rd,z}=\chi_z N_{Rk}/\gamma_{M1}",
       subst=f"{chi_z:.3f}·{n_rk / 1e3:.4g}/{gm1:g}")
    _t("My_b,Rd", my_b_rd, "kNm", clause="EN 1993-1-1 §6.3.2.1",
       expr="My_b,Rd = χ_LT·My_Rk/γ_M1",
       latex=r"M_{y,b,Rd}=\chi_{LT} M_{y,Rk}/\gamma_{M1}",
       subst=f"{chi_lt:.3f}·{my_rk / 1e6:.4g}/{gm1:g}")
    _t("Mz_Rd", mz_rd, "kNm", expr="Mz_Rd = Mz_Rk/γ_M1",
       latex=r"M_{z,Rd}=M_{z,Rk}/\gamma_{M1}",
       subst=f"{mz_rk / 1e6:.4g}/{gm1:g}")

    # ── interaction factors ──
    n_y = inp.n_ed / n_b_rd_y if n_b_rd_y > 0 else 0.0
    n_z = inp.n_ed / n_b_rd_z if n_b_rd_z > 0 else 0.0
    kyy, kyz, kzy, kzz = _interaction_factors(
        n_y, n_z, lam_y, lam_z, inp.cmy, inp.cmz, inp.cm_lt,
        inp.section_class, inp.susceptible_lt)

    _sec("Interaction factors (§6.3.3)")
    _t("k_yy", kyy, "—", clause="EN 1993-1-1 Annex A/B")
    _t("k_yz", kyz, "—")
    _t("k_zy", kzy, "—")
    _t("k_zz", kzz, "—")

    # ── total moments (add the Class-4 shift) ──
    my = inp.my_ed + inp.d_my
    mz = inp.mz_ed + inp.d_mz

    # ── Eqs 6.61 / 6.62 ──
    u_661 = (n_y
             + kyy * my / my_b_rd
             + kyz * mz / mz_rd) if mz_rd else math.inf
    u_662 = (n_z
             + kzy * my / my_b_rd
             + kzz * mz / mz_rd) if mz_rd else math.inf
    util = max(u_661, u_662)

    _sec("Combined check (§6.3.3)")
    _t("Eq. (6.61)", u_661, "—", clause="EN 1993-1-1 Eq. 6.61",
       expr="N_Ed/N_b,Rd,y + k_yy·My/My_b,Rd + k_yz·Mz/Mz_Rd ≤ 1",
       latex=r"\frac{N_{Ed}}{N_{b,Rd,y}}+k_{yy}\frac{M_{y}}{M_{y,b,Rd}}"
             r"+k_{yz}\frac{M_{z}}{M_{z,Rd}}\le1",
       subst=(f"{n_y:.3f}+{kyy:.3f}·{my:.4g}/{my_b_rd:.4g}"
              f"+{kyz:.3f}·{mz:.4g}/{mz_rd:.4g}") if mz_rd else "",
       ok=u_661 <= 1.0)
    _t("Eq. (6.62)", u_662, "—", clause="EN 1993-1-1 Eq. 6.62",
       expr="N_Ed/N_b,Rd,z + k_zy·My/My_b,Rd + k_zz·Mz/Mz_Rd ≤ 1",
       latex=r"\frac{N_{Ed}}{N_{b,Rd,z}}+k_{zy}\frac{M_{y}}{M_{y,b,Rd}}"
             r"+k_{zz}\frac{M_{z}}{M_{z,Rd}}\le1",
       subst=(f"{n_z:.3f}+{kzy:.3f}·{my:.4g}/{my_b_rd:.4g}"
              f"+{kzz:.3f}·{mz:.4g}/{mz_rd:.4g}") if mz_rd else "",
       ok=u_662 <= 1.0)
    _t("Utilization", util, "—", note="max of (6.61), (6.62)", ok=util <= 1.0)

    return MemberCheckResult(
        util_6_61=u_661, util_6_62=u_662, utilization=util,
        passed=util <= 1.0,
        n_rk=n_rk / 1e3, my_rk=my_rk / 1e6, mz_rk=mz_rk / 1e6,
        chi_y=chi_y, chi_z=chi_z, chi_lt=chi_lt,
        lambda_y=lam_y, lambda_z=lam_z, lambda_lt=lam_lt,
        m_cr=m_cr / 1e6 if math.isfinite(m_cr) else math.inf,
        kyy=kyy, kyz=kyz, kzy=kzy, kzz=kzz,
        details={"n_y": n_y, "n_z": n_z,
                 "Nb_Rd_y": n_b_rd_y, "Nb_Rd_z": n_b_rd_z,
                 "My_b_Rd": my_b_rd, "Mz_Rd": mz_rd})


# ── convenience: build the input from a eurocodepy profile ─────────────────

def member_check_profile(profile, fy: float, *,  # ruff: ignore[missing-type-function-argument]
                         n_ed: float, my_ed: float = 0.0, mz_ed: float = 0.0,
                         lcr_y: float, lcr_z: float, l_lt: float | None = None,
                         c1: float = 1.0, cmy: float = 0.9, cmz: float = 0.9,
                         cm_lt: float = 0.9, gamma_m1: float = 1.0,
                         susceptible_lt: bool = True,
                         rolled_lt: bool = True) -> MemberCheckResult:
    """Run the §6.3.3 check for a eurocodepy profile.

    The section is classified (:func:`eurocodepy.ec3.classification.classify_section`)
    under the given N + My; the resistance moduli and area are chosen from the
    class (plastic → elastic → effective), the Class-4 centroid shift is turned
    into the additional moment ``N·e_N``, and the buckling curves are read from
    the profile (``CurveA``/``CurveB``) when available.

    Geometry is taken from the profile (dimensions in cm → mm, properties in the
    catalogue units): ``A, Iy, Iz, IT, Iw, Wel_y, Wpl_y, Wel_z, Wpl_z``.
    """
    from eurocodepy.ec3 import classification as _cl

    cm = 10.0
    cm2, cm3, cm4, cm6 = 1e2, 1e3, 1e4, 1e6
    area = float(profile.A) * cm2                 # cm² → mm²
    iy = float(profile.Iy) * cm4
    iz = float(profile.Iz) * cm4
    it = float(getattr(profile, "IT", 0.0)) * cm4
    iw = float(getattr(profile, "Iw", 0.0)) * cm6  # cm⁶ → mm⁶
    wel_y = float(profile.Wel_y) * cm3
    wpl_y = float(profile.Wpl_y) * cm3
    wel_z = float(profile.Wel_z) * cm3
    wpl_z = float(profile.Wpl_z) * cm3

    result = _cl.classify_section(profile, fy, n_ed=n_ed, m_ed=my_ed)
    cls = int(result.section_class)

    if cls in (1, 2):
        w_y, w_z, area_eff = wpl_y, wpl_z, area
        d_my = d_mz = 0.0
    elif cls == 3:
        w_y, w_z, area_eff = wel_y, wel_z, area
        d_my = d_mz = 0.0
    else:                                          # Class 4
        eff = _cl.effective_properties(profile, fy)
        area_eff = eff.A_eff
        w_y = eff.W_eff_y
        w_z = wel_z                                # minor Weff not modelled yet
        d_my = n_ed * eff.e_Ny / 1e3               # N·e_N: kN·mm → kNm
        d_mz = 0.0

    curve_y = getattr(profile, "CurveA", "a") or "a"
    curve_z = getattr(profile, "CurveB", "b") or "b"

    inp = MemberInput(
        n_ed=n_ed, my_ed=my_ed, mz_ed=mz_ed,
        area=area, area_eff=area_eff, w_y=w_y, w_z=w_z,
        iy=iy, iz=iz, it=it, iw=iw,
        lcr_y=lcr_y, lcr_z=lcr_z, l_lt=(l_lt if l_lt is not None else lcr_z),
        curve_y=curve_y, curve_z=curve_z, curve_lt=curve_z,
        c1=c1, cmy=cmy, cmz=cmz, cm_lt=cm_lt,
        fy=fy, gamma_m1=gamma_m1, section_class=cls,
        susceptible_lt=susceptible_lt, rolled_lt=rolled_lt,
        d_my=d_my, d_mz=d_mz)
    return eurocode3_member_check(inp)
