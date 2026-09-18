# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1995-1-1 cross-section / member verification under N, My, Mz, Vy, Vz, T.

This module groups the timber ULS checks the same way
:mod:`eurocodepy.ec3.uls.cross_section` groups the steel ones: a single
dataclass-based entry point that takes all the design forces at once, runs

* bending + axial force (with the compression/LTB stability factors
  ``k_c`` and ``k_crit``) — :func:`eurocodepy.ec5.uls.bending.check_bending_with_normal`;
* shear + torsion — :func:`eurocodepy.ec5.uls.shear.check_shear_with_torsion`,

and returns a single governing utilisation with the individual parts and a
pass/fail flag, so callers get one uniform result object for a timber member
just like the steel :class:`~eurocodepy.ec3.uls.cross_section.SectionResistanceResult`.

This grouping is **edition-independent**: it calls whichever bending / shear
checks the package it lives in provides. Here (``ec5.uls``) those are the
**EN 1995-1-1:2004** (§6) versions; :mod:`eurocodepy.ec5.uls2025.cross_section`
reuses the same dataclasses but calls the :2025 (§8) checks.

Sign / unit convention follows the underlying EC5 functions: forces in **kN**,
moments (bending and torsion) in **kNm**, lengths in **m** (section) / **mm**
(effective lengths), and a **negative** ``n_ed`` is compression (positive is
tension).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from eurocodepy.ec5.materials import LoadDuration, ServiceClass, Timber, TimberForcesType
from eurocodepy.ec5.uls.bending import (
    BETA_C_GLULAM,
    BETA_C_TIMBER,
    LAMBDA_REL_C_LIM,
    LAMBDA_REL_M_HIGH,
    LAMBDA_REL_M_LOW,
    calc_mcr,
    check_bending_with_normal,
)
from eurocodepy.ec5.uls.shear import check_shear_with_torsion
from eurocodepy.utils import CrossSection, CrossSectionShape


@dataclass
class TimberForces:
    """Design forces on the timber cross-section (compression ``n_ed`` < 0).

    Units: forces in kN, moments (bending and torsion) in kNm.
    """

    n_ed: float = 0.0     # axial [kN]  (negative = compression)
    my_ed: float = 0.0    # major-axis bending [kNm]
    mz_ed: float = 0.0    # minor-axis bending [kNm]
    vy_ed: float = 0.0    # shear parallel to y [kN]
    vz_ed: float = 0.0    # shear parallel to z [kN]
    t_ed: float = 0.0     # torsion [kNm]


@dataclass
class TimberSectionInput:
    """Everything needed to verify a timber member section (EN 1995-1-1)."""

    section: CrossSection
    timber: Timber
    service_class: ServiceClass = ServiceClass.SC1
    load_duration: LoadDuration = LoadDuration.MediumDuration
    # buckling / LTB effective lengths [mm]; default to no buckling data.
    l_0y: float = 0.0     # flexural buckling length about y [mm]
    l_0z: float = 0.0     # flexural buckling length about z [mm]
    l_0m: float = 0.0     # lateral-torsional (LTB) length [mm]


@dataclass
class TimberSectionResult:
    """Result of the grouped EN 1995-1-1 cross-section / member verification."""

    util_bending_axial: float
    util_shear: float
    util_torsion: float
    utilization: float                 # governing
    passed: bool
    k_c: tuple[float, float] = (1.0, 1.0)   # compression stability (y, z)
    k_m: float = 1.0                        # LTB stability factor
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Readable summary of the timber section check."""
        return (
            f"EC5 section check — {'PASS' if self.passed else 'FAIL'}\n"
            f"  N+My+Mz:  {self.util_bending_axial:.3f} "
            f"(k_cy {self.k_c[0]:.2f} | k_cz {self.k_c[1]:.2f} | k_m {self.k_m:.2f})\n"
            f"  shear:    {self.util_shear:.3f}\n"
            f"  torsion:  {self.util_torsion:.3f}\n"
            f"  → utilization {self.utilization:.3f}"
        )


def _kc_axis_detail(l0_mm: float, i_gyr: float, fc0k: float, e005: float,
                    beta_c: float) -> dict:
    """Re-derive :func:`eurocodepy.ec5.uls.bending.calc_k_c`'s single-axis
    ``λ, λ_rel, k, k_c`` chain (EN 1995-1-1:2004 §6.3.2, Eqs. 6.21/6.22 and
    6.27-6.29) purely for display — a pure function of already-known inputs,
    re-run only so the trace can show the intermediate values calc_k_c itself
    discards; never used to recompute the design result."""
    if l0_mm <= 0.0 or i_gyr <= 0.0:
        return {"lam": 0.0, "lam_rel": 0.0, "k": None, "k_c": 1.0, "buckles": False}
    lam = (l0_mm / 1e3) / i_gyr
    lam_rel = lam / math.pi * math.sqrt(fc0k / e005)
    if lam_rel <= LAMBDA_REL_C_LIM:
        return {"lam": lam, "lam_rel": lam_rel, "k": None, "k_c": 1.0, "buckles": False}
    k = 0.5 * (1.0 + beta_c * (lam_rel - LAMBDA_REL_C_LIM) + lam_rel**2)
    k_c = 1.0 / (k + math.sqrt(k**2 - lam_rel**2))
    return {"lam": lam, "lam_rel": lam_rel, "k": k, "k_c": k_c, "buckles": True}


def _k_crit_detail(l_0m: float, section, timber) -> dict:
    """Re-derive :func:`eurocodepy.ec5.uls.bending.calc_k_m`'s ``M_y,crit,
    σ_m,crit, λ_rel,m`` chain (EN 1995-1-1:2004 §6.3.3, Eqs. 6.30/6.31/6.34)
    purely for display, same rationale as :func:`_kc_axis_detail`."""
    m_cr = calc_mcr(l_0m, section, timber)
    wy = section.bend_mod_y
    if not math.isfinite(m_cr) or m_cr <= 0.0 or wy <= 0.0:
        return {"m_cr": m_cr, "sig_crit": None, "lam_rel_m": None,
                "k_crit": 1.0, "governs": False}
    sig_crit = m_cr / wy
    lam_rel_m = math.sqrt(timber.fmk / sig_crit)
    if lam_rel_m <= LAMBDA_REL_M_LOW:
        k_crit = 1.0
    elif lam_rel_m <= LAMBDA_REL_M_HIGH:
        k_crit = 1.56 - 0.75 * lam_rel_m
    else:
        k_crit = 1.0 / lam_rel_m**2
    return {"m_cr": m_cr, "sig_crit": sig_crit, "lam_rel_m": lam_rel_m,
            "k_crit": k_crit, "governs": lam_rel_m > LAMBDA_REL_M_LOW}


def eurocode5_section_check(inp: TimberSectionInput,
                            f: TimberForces,
                            trace=None) -> TimberSectionResult:
    """Verify a timber member under N + My + Mz + Vy + Vz + T (EN 1995-1-1).

    Groups the EC5 bending-with-axial and shear-with-torsion checks into one
    call and returns the governing utilisation, mirroring the EC3
    :func:`eurocodepy.ec3.uls.cross_section.eurocode3_section_check` API.

    Args:
        inp: The section, material, service class / load duration and the
            effective lengths for the compression and LTB stability factors.
        f: The design forces (kN / kNm; negative ``n_ed`` is compression).
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps into it (recording only — the result is
            identical to ``trace=None``).

    Returns:
        A :class:`TimberSectionResult` with the bending+axial, shear and torsion
        utilisations, the governing value, the stability factors and pass/fail.

    """
    bend = check_bending_with_normal(
        n_ed=f.n_ed, m_ed_y=f.my_ed, m_ed_z=f.mz_ed,
        section=inp.section, timber=inp.timber,
        l_0y=inp.l_0y, l_0z=inp.l_0z, l_0m=inp.l_0m,
        service_class=inp.service_class, load_duration=inp.load_duration)

    shear = check_shear_with_torsion(
        v_ed_y=f.vy_ed, v_ed_z=f.vz_ed, t_ed=f.t_ed,
        section=inp.section, timber=inp.timber,
        service_class=inp.service_class, load_duration=inp.load_duration)

    u_nm = float(bend["utilization"])
    u_v = float(shear["util_shear"])
    u_t = float(shear["util_torsion"])
    utilization = max(u_nm, u_v, u_t)

    if trace is not None:
        k_c = tuple(bend.get("k_c", (1.0, 1.0)))
        k_m = float(bend.get("k_m", 1.0))
        bchecks = bend.get("checks", {})
        schecks = shear.get("checks", {})
        sec, t = inp.section, inp.timber
        # Design strengths first — check_bending_with_normal() already called
        # timber.design_values(), so kmod/fmd/f{c,t}0d/fvd are populated on
        # inp.timber; report them before the forces so the reader immediately
        # sees which material values the whole check is based on.
        kmod = getattr(t, "kmod", 0.0)
        gamma_m = getattr(t, "safety", 0.0)
        trace.section("Design strengths")
        trace.step("k_mod", kmod, "—",
                   clause="EN 1995-1-1 §3.1.3, Table 3.1",
                   note=f"{getattr(inp.service_class, 'name', inp.service_class)} · "
                        f"{getattr(inp.load_duration, 'name', inp.load_duration)}")
        trace.step("γ_M", gamma_m, "—", clause="EN 1995-1-1 Table 2.3")
        trace.step("f_md", getattr(t, "fmd", 0.0), "MPa",
                   expr="f_md = k_mod·f_mk/γ_M",
                   subst=f"{kmod:.3g}·{getattr(t, 'fmk', 0.0):.4g}/{gamma_m:.3g}",
                   latex=r"f_{md}=k_{mod}\,f_{mk}/\gamma_M")
        trace.step("f_t0d", getattr(t, "ft0d", 0.0), "MPa",
                   expr="f_t0d = k_mod·f_t0k/γ_M",
                   subst=f"{kmod:.3g}·{getattr(t, 'ft0k', 0.0):.4g}/{gamma_m:.3g}",
                   latex=r"f_{t0d}=k_{mod}\,f_{t0k}/\gamma_M")
        trace.step("f_c0d", getattr(t, "fc0d", 0.0), "MPa",
                   expr="f_c0d = k_mod·f_c0k/γ_M",
                   subst=f"{kmod:.3g}·{getattr(t, 'fc0k', 0.0):.4g}/{gamma_m:.3g}",
                   latex=r"f_{c0d}=k_{mod}\,f_{c0k}/\gamma_M")
        trace.step("f_vd", getattr(t, "fvd", 0.0), "MPa",
                   expr="f_vd = k_mod·f_vk/γ_M",
                   subst=f"{kmod:.3g}·{getattr(t, 'fvk', 0.0):.4g}/{gamma_m:.3g}",
                   latex=r"f_{vd}=k_{mod}\,f_{vk}/\gamma_M")
        trace.section("Inputs")
        trace.step("N_Ed", f.n_ed,
                   "kN (tension)" if f.n_ed >= 0 else "kN (compression)")
        trace.step("My_Ed", f.my_ed, "kNm")
        trace.step("Mz_Ed", f.mz_ed, "kNm")
        trace.step("Vy_Ed", f.vy_ed, "kN")
        trace.step("Vz_Ed", f.vz_ed, "kN")
        trace.step("T_Ed", f.t_ed, "kNm")
        trace.step("Service class", getattr(inp.service_class, "name",
                                            inp.service_class), "—")
        trace.step("Load duration", getattr(inp.load_duration, "name",
                                            inp.load_duration), "—",
                   note="sets k_mod (EN 1995-1-1 §3.1.3, Table 3.1)")

        # Stresses [MPa] and the biaxial-bending factor k_m — recomputed here
        # (same closed formulas as check_bending_with_normal) purely so the
        # subst= strings below can show the actual numbers; the design result
        # itself always comes from `bend`/`shear`, never from these.
        sig_ax = abs(f.n_ed) / sec.area / 1e3
        sig_my = abs(f.my_ed) / sec.bend_mod_y / 1e3
        sig_mz = abs(f.mz_ed) / sec.bend_mod_z / 1e3
        km_red = 0.7 if sec.shape == "rectangular" else 1.0
        k_hy = t.k_h(sec.height, TimberForcesType.Bending)
        k_hz = t.k_h(sec.width, TimberForcesType.Bending)
        fmdy = t.fmd * k_hy
        fmdz = t.fmd * k_hz
        trace.section("Stresses (§6.1.6)")
        trace.step("σ_N", sig_ax, "MPa", expr="|N_Ed|/A",
                   subst=f"|{f.n_ed:.4g}|/{sec.area:.4g}/1e3",
                   latex=r"\sigma_N=|N_{Ed}|/A")
        trace.step("σ_m,y", sig_my, "MPa", expr="|My_Ed|/W_y",
                   subst=f"|{f.my_ed:.4g}|/{sec.bend_mod_y:.4g}/1e3",
                   latex=r"\sigma_{m,y}=|M_{y,Ed}|/W_y")
        trace.step("σ_m,z", sig_mz, "MPa", expr="|Mz_Ed|/W_z",
                   subst=f"|{f.mz_ed:.4g}|/{sec.bend_mod_z:.4g}/1e3",
                   latex=r"\sigma_{m,z}=|M_{z,Ed}|/W_z")
        trace.step("k_h,y / k_h,z", (round(k_hy, 4), round(k_hz, 4)), "—",
                   clause="EN 1995-1-1 §3.2", note="size factor on f_md")
        trace.step("f_m,d,y / f_m,d,z", (round(fmdy, 3), round(fmdz, 3)), "MPa",
                   expr="f_md·k_h", note="size-factored bending strength")
        trace.step("k_m (biaxial)", km_red, "—", clause="EN 1995-1-1 §6.1.6",
                   note="0.7 rectangular solid/glulam/LVL, else 1.0")

        trace.section("Stability factors (§6.3)")
        beta_c = BETA_C_TIMBER if t.type == "timber" else BETA_C_GLULAM
        kd_y = _kc_axis_detail(inp.l_0y, sec.radius_y, t.fc0k, t.E0k, beta_c)
        kd_z = _kc_axis_detail(inp.l_0z, sec.radius_z, t.fc0k, t.E0k, beta_c)
        for axis, l0_ax, i_ax, kd, k_c_i in (
                ("y", inp.l_0y, sec.radius_y, kd_y, k_c[0]),
                ("z", inp.l_0z, sec.radius_z, kd_z, k_c[1])):
            if not kd["buckles"]:
                trace.step(f"k_c,{axis}", k_c_i, "—", clause="EN 1995-1-1 §6.3.2",
                           note=f"λ_rel={kd['lam_rel']:.3g} ≤ {LAMBDA_REL_C_LIM} "
                                "→ no buckling reduction")
                continue
            trace.step(f"λ_rel,{axis}", kd["lam_rel"], "—",
                       clause="EN 1995-1-1 §6.3.2 Eq. 6.21/6.22",
                       expr="(l_0/i)/π·√(f_c0k/E_0,05)",
                       subst=f"({l0_ax:.4g}/1e3/{i_ax:.4g})/π·√({t.fc0k:.4g}/{t.E0k:.4g})")
            trace.step(f"k_{axis}", kd["k"], "—",
                       clause="EN 1995-1-1 §6.3.2 Eq. 6.27/6.28",
                       expr="0.5·[1+β_c·(λ_rel−0.3)+λ_rel²]",
                       subst=f"0.5·[1+{beta_c:.2g}·({kd['lam_rel']:.4g}−0.3)"
                             f"+{kd['lam_rel']:.4g}²]")
            trace.step(f"k_c,{axis}", k_c_i, "—", clause="EN 1995-1-1 §6.3.2 Eq. 6.29",
                       expr="1/(k+√(k²−λ_rel²))",
                       subst=f"1/({kd['k']:.4g}+√({kd['k']:.4g}²−{kd['lam_rel']:.4g}²))",
                       latex=r"k_c=\dfrac{1}{k+\sqrt{k^2-\lambda_{rel}^2}}",
                       note=f"flexural buckling ({axis})")
        kmd = _k_crit_detail(inp.l_0m, sec, t)
        if not kmd["governs"]:
            note = ("no LTB data (l_0m = 0)" if kmd["sig_crit"] is None
                    else f"λ_rel,m={kmd['lam_rel_m']:.3g} ≤ {LAMBDA_REL_M_LOW} "
                         "→ no LTB reduction")
            trace.step("k_crit (k_m)", k_m, "—", clause="EN 1995-1-1 §6.3.3", note=note)
        else:
            trace.step("M_y,crit", kmd["m_cr"], "kNm",
                       clause="EN 1995-1-1 §6.3.3 Eq. 6.31",
                       expr="(π/l_ef)·√(E_0,05·I_z·G_0,05·I_tor)")
            trace.step("σ_m,crit", kmd["sig_crit"], "MPa",
                       expr="M_y,crit/W_y",
                       subst=f"{kmd['m_cr']:.4g}/{sec.bend_mod_y:.4g}")
            trace.step("λ_rel,m", kmd["lam_rel_m"], "—",
                       clause="EN 1995-1-1 §6.3.3 Eq. 6.30",
                       expr="√(f_mk/σ_m,crit)",
                       subst=f"√({t.fmk:.4g}/{kmd['sig_crit']:.4g})")
            trace.step("k_crit (k_m)", k_m, "—", clause="EN 1995-1-1 §6.3.3 Eq. 6.34",
                       expr="k_crit = f(λ_rel,m)",
                       subst=f"λ_rel,m={kmd['lam_rel_m']:.4g}",
                       latex=r"k_{crit}=f(\lambda_{rel,m})",
                       note="lateral-torsional stability")

        trace.section("Bending + axial (§6.2.3 / §6.3)")
        sig_ax_over_f = (sig_ax / t.fc0d) if f.n_ed < 0.0 else (sig_ax / t.ft0d)
        f_used = t.fc0d if f.n_ed < 0.0 else t.ft0d
        f_sym = "f_c0d" if f.n_ed < 0.0 else "f_t0d"
        trace.step("σ_N/f", sig_ax_over_f, "—", expr=f"σ_N/{f_sym}",
                   subst=f"{sig_ax:.4g}/{f_used:.4g}")
        trace.step("σ_m,y/f_m,d,y", sig_my / fmdy if fmdy else 0.0, "—",
                   subst=(f"{sig_my:.4g}/{fmdy:.4g}" if fmdy else None))
        trace.step("σ_m,z/f_m,d,z", sig_mz / fmdz if fmdz else 0.0, "—",
                   subst=(f"{sig_mz:.4g}/{fmdz:.4g}" if fmdz else None))
        eq_num = "6.19/6.23" if f.n_ed < 0.0 else "6.17/6.18"
        trace.step(f"Eq. ({eq_num})", float(bchecks.get("check1", u_nm)), "—",
                   clause="EN 1995-1-1 §6.2.3/§6.3.2",
                   expr="σ_N/f + σ_m,y/f_m + k_m·σ_m,z/f_m ≤ 1",
                   subst=f"{sig_ax_over_f:.4g}+{(sig_my/fmdy if fmdy else 0):.4g}"
                         f"+{km_red:.2g}·{(sig_mz/fmdz if fmdz else 0):.4g} ≤ 1",
                   latex=r"\frac{\sigma_N}{f}+\frac{\sigma_{m,y}}{f_m}+k_m\frac{\sigma_{m,z}}{f_m}\leq 1",
                   ok=float(bchecks.get("check1", u_nm)) <= 1.0)
        if "check2" in bchecks:
            eq_num2 = "6.20/6.24" if f.n_ed < 0.0 else "6.18"
            trace.step(f"Eq. ({eq_num2})", float(bchecks["check2"]), "—",
                       clause="EN 1995-1-1 §6.2.3/§6.3.2",
                       expr="σ_N/f + k_m·σ_m,y/f_m + σ_m,z/f_m ≤ 1",
                       subst=f"{sig_ax_over_f:.4g}"
                             f"+{km_red:.2g}·{(sig_my/fmdy if fmdy else 0):.4g}"
                             f"+{(sig_mz/fmdz if fmdz else 0):.4g} ≤ 1",
                       latex=r"\frac{\sigma_N}{f}+k_m\frac{\sigma_{m,y}}{f_m}+\frac{\sigma_{m,z}}{f_m}\leq 1",
                       ok=float(bchecks["check2"]) <= 1.0)
        trace.step("U_N+M", u_nm, "—", expr="max of the checks above", ok=u_nm <= 1.0)

        trace.section("Shear + torsion (§6.1.7 / §6.1.8)")
        tau_v_y = 1.5 * abs(f.vy_ed) / sec.area / 1e3
        tau_v_z = 1.5 * abs(f.vz_ed) / sec.area / 1e3
        ratio = sec.height / sec.width
        alpha = (1.0 / 3.0) * (1.0 - 0.672 * ratio + 0.3 * ratio**2)
        tau_tor = alpha * abs(f.t_ed) / sec.area / 1e3
        k_shape = (1.2 if sec.shape is CrossSectionShape.CIRCULAR
                   else min(1.0 + 0.15 * ratio, 2.0))
        fvdt = k_shape * t.fvd
        trace.step("τ_v,y / τ_v,z", (round(tau_v_y, 4), round(tau_v_z, 4)), "MPa",
                   expr="1.5·V/A", latex=r"\tau_v=1.5\,V/A")
        trace.step("τ_tor", tau_tor, "MPa", expr="α·T_Ed/A",
                   subst=f"{alpha:.4g}·{abs(f.t_ed):.4g}/{sec.area:.4g}/1e3",
                   note=f"α={alpha:.3g} from h/b={ratio:.3g}")
        trace.step("k_shape", k_shape, "—", clause="EN 1995-1-1 §6.1.8 Eq. 6.15",
                   note="1.2 circular, else min(1+0.15·h/b, 2.0)")
        trace.step("f_v,d,tor", fvdt, "MPa", expr="k_shape·f_v,d",
                   subst=f"{k_shape:.4g}·{t.fvd:.4g}")
        trace.step("U_V", u_v, "—", clause="EN 1995-1-1 §6.1.7",
                   expr="τ_d/f_v,d ≤ 1",
                   subst=f"max({tau_v_y:.4g}, {tau_v_z:.4g})/{t.fvd:.4g} ≤ 1",
                   latex=r"\tau_d/f_{v,d}\leq 1", ok=u_v <= 1.0)
        trace.step("U_T", u_t, "—", clause="EN 1995-1-1 §6.1.8",
                   expr="τ_tor,d/(k_shape·f_v,d) ≤ 1",
                   subst=f"{tau_tor:.4g}/{fvdt:.4g} ≤ 1",
                   latex=r"\tau_{tor,d}/(k_{shape}\,f_{v,d})\leq 1", ok=u_t <= 1.0)
        trace.section("Combined utilisation")
        trace.step("Utilisation", utilization, "—",
                   expr="max(U_N+M, U_V, U_T) ≤ 1",
                   subst=f"max({u_nm:.4g}, {u_v:.4g}, {u_t:.4g}) ≤ 1",
                   latex=r"\max(U_{N+M},\,U_V,\,U_T)\leq 1", ok=utilization <= 1.0,
                   note="governing timber section check")

    return TimberSectionResult(
        util_bending_axial=u_nm,
        util_shear=u_v,
        util_torsion=u_t,
        utilization=utilization,
        passed=utilization <= 1.0,
        k_c=tuple(bend.get("k_c", (1.0, 1.0))),
        k_m=float(bend.get("k_m", 1.0)),
        details={"bending": bend, "shear": shear})
