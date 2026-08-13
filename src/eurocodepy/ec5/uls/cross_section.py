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

from dataclasses import dataclass, field

from eurocodepy.ec5.materials import LoadDuration, ServiceClass, Timber
from eurocodepy.ec5.uls.bending import check_bending_with_normal
from eurocodepy.ec5.uls.shear import check_shear_with_torsion
from eurocodepy.utils import CrossSection


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
        # Design strengths first — check_bending_with_normal() already called
        # timber.design_values(), so kmod/fmd/f{c,t}0d/fvd are populated on
        # inp.timber; report them before the forces so the reader immediately
        # sees which material values the whole check is based on.
        t = inp.timber
        trace.section("Design strengths")
        trace.step("k_mod", getattr(t, "kmod", 0.0), "—",
                   clause="EN 1995-1-1 §3.1.3, Table 3.1",
                   note=f"{getattr(inp.service_class, 'name', inp.service_class)} · "
                        f"{getattr(inp.load_duration, 'name', inp.load_duration)}")
        trace.step("γ_M", getattr(t, "safety", 0.0), "—",
                   clause="EN 1995-1-1 Table 2.3")
        trace.step("f_md", getattr(t, "fmd", 0.0), "MPa",
                   expr="f_md = k_mod·f_mk/γ_M")
        trace.step("f_t0d", getattr(t, "ft0d", 0.0), "MPa",
                   expr="f_t0d = k_mod·f_t0k/γ_M")
        trace.step("f_c0d", getattr(t, "fc0d", 0.0), "MPa",
                   expr="f_c0d = k_mod·f_c0k/γ_M")
        trace.step("f_vd", getattr(t, "fvd", 0.0), "MPa",
                   expr="f_vd = k_mod·f_vk/γ_M")
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
        trace.section("Stability factors (§6.3)")
        trace.step("k_c,y", k_c[0], "—", clause="EN 1995-1-1 §6.3.2",
                   expr="k_c = 1/(k+√(k²−λ_rel²))",
                   note="flexural buckling (y)")
        trace.step("k_c,z", k_c[1], "—", clause="EN 1995-1-1 §6.3.2",
                   note="flexural buckling (z)")
        trace.step("k_crit (k_m)", k_m, "—", clause="EN 1995-1-1 §6.3.3",
                   note="lateral-torsional stability")
        trace.section("Bending + axial (§6.2.3 / §6.3)")
        trace.step("Eq. (6.19/6.23)", float(bchecks.get("check1", u_nm)), "—",
                   clause="EN 1995-1-1 §6.2.3/§6.3.2",
                   expr="σ_N/f + σ_m,y/f_m + k_m·σ_m,z/f_m ≤ 1",
                   ok=float(bchecks.get("check1", u_nm)) <= 1.0)
        if "check2" in bchecks:
            trace.step("Eq. (6.20/6.24)", float(bchecks["check2"]), "—",
                       clause="EN 1995-1-1 §6.2.3/§6.3.2",
                       expr="σ_N/f + k_m·σ_m,y/f_m + σ_m,z/f_m ≤ 1",
                       ok=float(bchecks["check2"]) <= 1.0)
        trace.step("U_N+M", u_nm, "—", ok=u_nm <= 1.0)
        trace.section("Shear + torsion (§6.1.7 / §6.1.8)")
        trace.step("U_V", u_v, "—", clause="EN 1995-1-1 §6.1.7",
                   expr="τ_d/f_v,d ≤ 1", ok=u_v <= 1.0)
        trace.step("U_T", u_t, "—", clause="EN 1995-1-1 §6.1.8",
                   expr="τ_tor,d/(k_shape·f_v,d) ≤ 1", ok=u_t <= 1.0)
        trace.section("Combined utilisation")
        trace.step("Utilisation", utilization, "—",
                   expr="max(U_N+M, U_V, U_T) ≤ 1", ok=utilization <= 1.0,
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
