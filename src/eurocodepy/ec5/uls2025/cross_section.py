# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Grouped cross-section / member verification — **EN 1995-1-1:2025** (§8).

Same grouped API as :mod:`eurocodepy.ec5.uls.cross_section` (the dataclasses are
re-used unchanged), but the underlying bending-with-axial and shear-with-torsion
checks are the second-generation §8 versions from :mod:`eurocodepy.ec5.uls2025`.
"""

from __future__ import annotations

import math

from eurocodepy.ec5.materials import TimberForcesType, TimberType

# The force / input / result dataclasses are edition-independent — re-use them.
from eurocodepy.ec5.uls.cross_section import (
    TimberForces as TimberForces,
    TimberSectionInput as TimberSectionInput,
    TimberSectionResult as TimberSectionResult,
)
from eurocodepy.ec5.uls2025.bending import (
    EPSILON_GLULAM,
    EPSILON_TIMBER,
    LAMBDA_M_REL,
    LAMBDA_REL_LIM,
    THETA_TWIST_BASE,
    calc_mcr,
    check_bending_with_normal,
)
from eurocodepy.ec5.uls2025.shear import (
    F_V_REF_K_GLULAM,
    F_V_REF_K_TIMBER,
    K_VAR,
    check_shear_with_torsion,
)
from eurocodepy.utils import CrossSectionShape


def _kc_axis_detail_2025(l0_mm: float, i_gyr: float, fc0k: float, e0k: float,
                         fmk_axis: float, epsilon: float) -> dict:
    """Re-derive :func:`eurocodepy.ec5.uls2025.bending.calc_k_c`'s single-axis
    ``λ_rel, β_c, φ, k_c`` chain (EN 1995-1-1:2025 §8.3, Table 8.2, Eq. 8.40)
    purely for display — a pure function of already-known inputs, re-run
    only so the trace can show the intermediate values calc_k_c itself
    discards; never used to recompute the design result.

    Unlike the 2004 edition's single β_c per timber type, here β_c is scaled
    by that axis's size-factored bending strength ``f_mk_axis`` (Table 8.2),
    so y and z genuinely differ even for the same timber/E/A.
    """
    if l0_mm <= 0.0 or i_gyr <= 0.0 or fmk_axis <= 0.0:
        return {"lam_rel": 0.0, "beta_c": 0.0, "phi": None, "k_c": 1.0,
                "buckles": False}
    lam_rel = (l0_mm / 1e3) / i_gyr / math.pi * math.sqrt(fc0k / e0k)
    beta_c_base = epsilon * math.pi * math.sqrt(3.0 * e0k / fc0k) * fc0k
    beta_c = beta_c_base / fmk_axis
    if lam_rel <= LAMBDA_REL_LIM:
        return {"lam_rel": lam_rel, "beta_c": beta_c, "phi": None,
                "k_c": 1.0, "buckles": False}
    phi = 0.5 * (1.0 + beta_c * (lam_rel - LAMBDA_REL_LIM) + lam_rel**2)
    k_c = 1.0 / (phi + math.sqrt(phi**2 - lam_rel**2))
    return {"lam_rel": lam_rel, "beta_c": beta_c, "phi": phi, "k_c": k_c,
            "buckles": True}


def _k_m_detail_2025(l_0m: float, section, timber) -> dict:
    """Re-derive :func:`eurocodepy.ec5.uls2025.bending.calc_k_m`'s ``M_y,crit,
    λ_rel,m, β_m, β_twist, φ`` chain (EN 1995-1-1:2025 §8.3, Table 8.2,
    Eqs. 8.43/8.46/8.47) purely for display, same rationale as
    :func:`_kc_axis_detail_2025`."""
    m_cr = calc_mcr(l_0m, section, timber)
    wy = section.bend_mod_y
    if not math.isfinite(m_cr) or m_cr <= 0.0 or wy <= 0.0:
        return {"m_cr": m_cr, "lam_rel_m": None, "beta_m": None,
                "beta_twist": None, "phi": None, "k_m": 1.0, "governs": False}
    lam_rel_m = math.sqrt(timber.fmk * wy / m_cr)
    ratio = section.height / section.width
    epsilon = EPSILON_TIMBER if timber.type == "timber" else EPSILON_GLULAM
    beta_m = epsilon * ratio * math.pi / 2.0 * math.sqrt(3.0 * timber.E0k / timber.Gk)
    beta_twist = THETA_TWIST_BASE / section.height * ratio
    if lam_rel_m <= LAMBDA_REL_LIM:
        return {"m_cr": m_cr, "lam_rel_m": lam_rel_m, "beta_m": beta_m,
                "beta_twist": beta_twist, "phi": None, "k_m": 1.0,
                "governs": False}
    phi = 0.5 * (1.0 + beta_m * beta_twist * (lam_rel_m - LAMBDA_M_REL) + lam_rel_m**2)
    k_m = 1.0 / (phi + math.sqrt(phi**2 - lam_rel_m**2))
    return {"m_cr": m_cr, "lam_rel_m": lam_rel_m, "beta_m": beta_m,
            "beta_twist": beta_twist, "phi": phi, "k_m": k_m, "governs": True}


def eurocode5_section_check(inp: TimberSectionInput,
                            f: TimberForces,
                            trace=None) -> TimberSectionResult:
    """Verify a timber member under N + My + Mz + Vy + Vz + T (EN 1995-1-1:2025).

    Identical grouping to :func:`eurocodepy.ec5.uls.eurocode5_section_check`, but
    calling the §8 (2025) bending / shear checks.

    Args:
        inp: The section, material, service class / load duration and the
            effective lengths for the compression and LTB stability factors.
        f: The design forces (kN / kNm; negative ``n_ed`` is compression).
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps into it (recording only — the result
            is identical to ``trace=None``). Previously this edition had no
            ``trace`` parameter at all, so ``xdfem2d.timber_design``'s
            ``with_reports`` silently produced *zero* reports for any member
            using the 2025 edition (caught by an ``except TypeError``); this
            parameter closes that gap. The stability factors ``k_c``/``k_m``
            now break out their full Table 8.2 β/φ derivation step-by-step
            (:func:`_kc_axis_detail_2025` / :func:`_k_m_detail_2025`), matching
            the 2004 edition's λ_rel/k/k_c chain — the only structural
            difference is that here β_c is scaled per-axis by that axis's
            size-factored f_mk (Table 8.2), rather than a single β_c per
            timber type as in 2004.

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
        kmod = getattr(t, "kmod", 0.0)
        gamma_m = getattr(t, "safety", 0.0)

        trace.section("Design strengths")
        trace.step("k_mod", kmod, "—",
                   clause="EN 1995-1-1:2025 §3.1.3",
                   note=f"{getattr(inp.service_class, 'name', inp.service_class)} · "
                        f"{getattr(inp.load_duration, 'name', inp.load_duration)}")
        trace.step("γ_M", gamma_m, "—", clause="EN 1995-1-1:2025 Table 2.3")
        trace.step("f_c0d", getattr(t, "fc0d", 0.0), "MPa",
                   expr="f_c0d = k_mod·f_c0k/γ_M",
                   subst=f"{kmod:.3g}·{getattr(t, 'fc0k', 0.0):.4g}/{gamma_m:.3g}",
                   latex=r"f_{c0d}=k_{mod}\,f_{c0k}/\gamma_M")
        trace.step("f_t0d", getattr(t, "ft0d", 0.0), "MPa",
                   expr="f_t0d = k_mod·f_t0k/γ_M",
                   subst=f"{kmod:.3g}·{getattr(t, 'ft0k', 0.0):.4g}/{gamma_m:.3g}",
                   latex=r"f_{t0d}=k_{mod}\,f_{t0k}/\gamma_M")
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

        # Stresses [MPa] — same closed formulas check_bending_with_normal /
        # check_shear_with_torsion use internally, recomputed here only so the
        # subst= strings can show the actual numbers (never used to recompute
        # the design result, which always comes from `bend`/`shear`).
        sig_n = abs(f.n_ed) / sec.area / 1e3
        sig_my = abs(f.my_ed) / sec.bend_mod_y / 1e3
        sig_mz = abs(f.mz_ed) / sec.bend_mod_z / 1e3
        k_hy = t.k_h(sec.height, TimberForcesType.Bending)
        k_hz = t.k_h(sec.width, TimberForcesType.Bending)
        fmdy = t.fmd * k_hy
        fmdz = t.fmd * k_hz
        kred = 0.7 if sec.shape == "rectangular" else 1.0
        trace.section("Stresses (§8.1)")
        trace.step("σ_N", sig_n, "MPa", expr="|N_Ed|/A",
                   subst=f"|{f.n_ed:.4g}|/{sec.area:.4g}/1e3")
        trace.step("σ_m,y", sig_my, "MPa", expr="|My_Ed|/W_y",
                   subst=f"|{f.my_ed:.4g}|/{sec.bend_mod_y:.4g}/1e3")
        trace.step("σ_m,z", sig_mz, "MPa", expr="|Mz_Ed|/W_z",
                   subst=f"|{f.mz_ed:.4g}|/{sec.bend_mod_z:.4g}/1e3")
        trace.step("f_m,d,y / f_m,d,z", (round(fmdy, 3), round(fmdz, 3)), "MPa",
                   expr="f_md·k_h", note="size-factored bending strength")
        trace.step("k_red", kred, "—", clause="EN 1995-1-1:2025 §8.1.8.1(2)",
                   note="0.7 rectangular, else 1.0")

        trace.section("Stability factors (§8.3)")
        fmky = t.fmk * k_hy
        fmkz = t.fmk * k_hz
        epsilon = EPSILON_TIMBER if t.type == "timber" else EPSILON_GLULAM
        kd_y = _kc_axis_detail_2025(inp.l_0y, sec.radius_y, t.fc0k, t.E0k, fmky, epsilon)
        kd_z = _kc_axis_detail_2025(inp.l_0z, sec.radius_z, t.fc0k, t.E0k, fmkz, epsilon)
        for axis, kd, k_c_i in (("y", kd_y, k_c[0]), ("z", kd_z, k_c[1])):
            if not kd["buckles"]:
                trace.step(f"k_c,{axis}", k_c_i, "—", clause="EN 1995-1-1:2025 §8.3",
                           note=f"λ_rel={kd['lam_rel']:.3g} ≤ {LAMBDA_REL_LIM} "
                                "→ no buckling reduction")
                continue
            trace.step(f"λ_rel,{axis}", kd["lam_rel"], "—",
                       clause="EN 1995-1-1:2025 §8.3",
                       expr="(l_0/i)/π·√(f_c0k/E_0,05)",
                       subst=f"({(inp.l_0y if axis == 'y' else inp.l_0z):.4g}/1e3/"
                             f"{(sec.radius_y if axis == 'y' else sec.radius_z):.4g})"
                             f"/π·√({t.fc0k:.4g}/{t.E0k:.4g})")
            trace.step(f"β_c,{axis}", kd["beta_c"], "—",
                       clause="EN 1995-1-1:2025 Table 8.2",
                       expr="ε·π·√(3·E_0,05/f_c0k)·f_c0k/f_mk",
                       note=f"f_mk,{axis} (size-factored) = "
                            f"{(fmky if axis == 'y' else fmkz):.4g} MPa")
            trace.step(f"φ_{axis}", kd["phi"], "—",
                       clause="EN 1995-1-1:2025 Eq. 8.40",
                       expr="0.5·[1+β_c·(λ_rel−0.3)+λ_rel²]",
                       subst=f"0.5·[1+{kd['beta_c']:.4g}·({kd['lam_rel']:.4g}−0.3)"
                             f"+{kd['lam_rel']:.4g}²]")
            trace.step(f"k_c,{axis}", k_c_i, "—", clause="EN 1995-1-1:2025 Eq. 8.40",
                       expr="1/(φ+√(φ²−λ_rel²))",
                       subst=f"1/({kd['phi']:.4g}+√({kd['phi']:.4g}²−{kd['lam_rel']:.4g}²))",
                       latex=r"k_c=\dfrac{1}{arphi+\sqrt{arphi^2-\lambda_{rel}^2}}",
                       note=f"flexural buckling ({axis})")
        kmd = _k_m_detail_2025(inp.l_0m, sec, t)
        if not kmd["governs"]:
            note = ("no LTB data (l_0m = 0)" if kmd["lam_rel_m"] is None
                    else f"λ_rel,m={kmd['lam_rel_m']:.3g} ≤ {LAMBDA_REL_LIM} "
                         "→ no LTB reduction")
            trace.step("k_m (LTB)", k_m, "—", clause="EN 1995-1-1:2025 §8.3", note=note)
        else:
            trace.step("M_y,crit", kmd["m_cr"], "kNm", clause="EN 1995-1-1:2025 §8.3",
                       expr="(π/l_ef)·√(E_0,05·G_0,05·I_tor·I_z)")
            trace.step("λ_rel,m", kmd["lam_rel_m"], "—",
                       clause="EN 1995-1-1:2025 Eq. 8.43",
                       expr="√(f_mk·W_y/M_y,crit)",
                       subst=f"√({t.fmk:.4g}·{sec.bend_mod_y:.4g}/{kmd['m_cr']:.4g})")
            trace.step("β_m / β_twist", (round(kmd["beta_m"], 4), round(kmd["beta_twist"], 5)),
                       "—", clause="EN 1995-1-1:2025 Table 8.2",
                       note="β_m=ε·(h/b)·π/2·√(3·E_0,05/G_0,05); "
                            "β_twist=θ_0/h·(h/b)")
            trace.step("φ", kmd["phi"], "—", clause="EN 1995-1-1:2025 Eq. 8.47",
                       expr="0.5·[1+β_m·β_twist·(λ_rel,m−0.55)+λ_rel,m²]")
            trace.step("k_m (LTB)", k_m, "—", clause="EN 1995-1-1:2025 Eq. 8.46",
                       expr="1/(φ+√(φ²−λ_rel,m²))",
                       latex=r"k_m=\dfrac{1}{arphi+\sqrt{arphi^2-\lambda_{rel,m}^2}}",
                       note="lateral-torsional stability")

        trace.section("Bending + axial (§8.1.8)")
        p_exp = 2.0 if sec.shape == "rectangular" else 1.0
        f_ax = t.fc0d if f.n_ed < 0.0 else t.ft0d
        f_sym = "f_c0d" if f.n_ed < 0.0 else "f_t0d"
        sig_ax_over_f = (sig_n / f_ax) if f_ax else 0.0
        eqs = (("8.26", "8.27", "8.39", "8.44") if f.n_ed < 0.0
               else ("8.24", "8.25", None, "8.45"))
        trace.step("σ_N/f", sig_ax_over_f, "—", expr=f"σ_N/{f_sym}",
                   subst=f"{sig_n:.4g}/{f_ax:.4g}" if f_ax else None,
                   note=f"exponent p={p_exp:.0f}" if f.n_ed < 0.0 else None)
        trace.step(f"Eq. ({eqs[0]})", float(bchecks.get("check1", u_nm)), "—",
                   clause="EN 1995-1-1:2025 §8.1.8", ok=float(bchecks.get("check1", u_nm)) <= 1.0)
        trace.step(f"Eq. ({eqs[1]})", float(bchecks.get("check2", u_nm)), "—",
                   clause="EN 1995-1-1:2025 §8.1.8", ok=float(bchecks.get("check2", u_nm)) <= 1.0)
        if eqs[2] is not None and "check3" in bchecks and bchecks["check3"] not in (True, 0.0):
            trace.step(f"Eq. ({eqs[2]})", float(bchecks["check3"]), "—",
                       clause="EN 1995-1-1:2025 §8.1.8 (buckling)",
                       ok=float(bchecks["check3"]) <= 1.0)
        trace.step(f"Eq. ({eqs[3]})", float(bchecks.get("check4", u_nm)), "—",
                   clause="EN 1995-1-1:2025 §8.1.8 (LTB)",
                   ok=float(bchecks.get("check4", u_nm)) <= 1.0)
        trace.step("U_N+M", u_nm, "—", expr="max of the checks above", ok=u_nm <= 1.0)

        trace.section("Shear + torsion (§8.1.9)")
        tau_v_y = 1.5 * abs(f.vy_ed) / sec.area / 1e3
        tau_v_z = 1.5 * abs(f.vz_ed) / sec.area / 1e3
        ratio = sec.height / sec.width
        alpha = (1.0 / 3.0) * (1.0 - 0.672 * ratio + 0.3 * ratio**2)
        tau_tor = alpha * abs(f.t_ed) / sec.area / 1e3
        trace.step("τ_v,y / τ_v,z", (round(tau_v_y, 4), round(tau_v_z, 4)), "MPa",
                   expr="1.5·|V|/A")
        trace.step("τ_tor", tau_tor, "MPa", expr="α·|T_Ed|/A",
                   subst=f"{alpha:.4g}·|{f.t_ed:.4g}|/{sec.area:.4g}/1e3",
                   note=f"α={alpha:.3g} from h/b={ratio:.3g}")
        f_v_ref = (F_V_REF_K_GLULAM if t.material is TimberType.GLULAM
                   else F_V_REF_K_TIMBER)
        trace.step("k_v (size, y/z)", "from k_h·k_var·f_v,ref,k/f_vk (§8.1.9, Table 8.3)",
                   "—", note=f"k_var={K_VAR:.2g}, f_v,ref,k={f_v_ref:.3g} MPa "
                              f"({getattr(t.material, 'value', t.material)})")
        k_shape_note = ("1.2 circular" if sec.shape is CrossSectionShape.CIRCULAR
                        else "1.0 rectangular CLT, else min(1+0.05·h/b, 1.3)")
        trace.step("k_shape", "Eq. 8.35", "—", note=k_shape_note)
        trace.step("U shear (Eq. 8.28/8.29)", u_v, "—",
                   clause="EN 1995-1-1:2025 §8.1.9", ok=u_v <= 1.0)
        trace.step("U torsion (Eq. 8.34)", u_t, "—",
                   clause="EN 1995-1-1:2025 §8.1.9", ok=u_t <= 1.0)

        trace.section("Combined utilisation")
        trace.step("Utilisation", utilization, "—",
                   expr="max(U_N+M, U_V, U_T) ≤ 1",
                   subst=f"max({u_nm:.4g}, {u_v:.4g}, {u_t:.4g}) ≤ 1",
                   latex=r"\max(U_{N+M},\,U_V,\,U_T)\leq 1", ok=utilization <= 1.0,
                   note="governing timber section check")

    return TimberSectionResult(
        util_bending_axial=u_nm, util_shear=u_v, util_torsion=u_t,
        utilization=utilization, passed=utilization <= 1.0,
        k_c=tuple(bend.get("k_c", (1.0, 1.0))),
        k_m=float(bend.get("k_m", 1.0)),
        details={"bending": bend, "shear": shear})
