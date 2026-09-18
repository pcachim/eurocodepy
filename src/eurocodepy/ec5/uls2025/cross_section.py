# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Grouped cross-section / member verification — **EN 1995-1-1:2025** (§8).

Same grouped API as :mod:`eurocodepy.ec5.uls.cross_section` (the dataclasses are
re-used unchanged), but the underlying bending-with-axial and shear-with-torsion
checks are the second-generation §8 versions from :mod:`eurocodepy.ec5.uls2025`.
"""

from __future__ import annotations

from eurocodepy.ec5.materials import TimberForcesType, TimberType

# The force / input / result dataclasses are edition-independent — re-use them.
from eurocodepy.ec5.uls.cross_section import (
    TimberForces as TimberForces,
    TimberSectionInput as TimberSectionInput,
    TimberSectionResult as TimberSectionResult,
)
from eurocodepy.ec5.uls2025.bending import check_bending_with_normal
from eurocodepy.ec5.uls2025.shear import (
    F_V_REF_K_GLULAM,
    F_V_REF_K_TIMBER,
    K_VAR,
    check_shear_with_torsion,
)
from eurocodepy.utils import CrossSectionShape


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
            are reported as single values (their Table 8.2 β/φ derivation is
            not broken out step-by-step yet, unlike the 2004 edition's
            λ_rel/k/k_c chain) — a narrower trace than :mod:`eurocodepy.ec5.uls`
            for now.

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
        trace.step("k_c,y", k_c[0], "—", clause="EN 1995-1-1:2025 Eq. 8.40",
                   note="Table 8.2 β/φ derivation not broken out step-by-step yet")
        trace.step("k_c,z", k_c[1], "—", clause="EN 1995-1-1:2025 Eq. 8.40")
        trace.step("k_m (LTB)", k_m, "—", clause="EN 1995-1-1:2025 Eq. 8.46")

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
