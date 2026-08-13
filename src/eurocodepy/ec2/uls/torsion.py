# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EC2 (EN 1992-1-1) §6.3 — St-Venant torsion of solid rectangular sections.

A solid section is designed as an equivalent thin-walled closed section: the
torsion flows around a wall of effective thickness ``t_ef`` enclosing an area
``A_k`` with centre-line perimeter ``u_k``. From it come the closed torsion
stirrups (per leg), the longitudinal torsion reinforcement distributed around
``u_k``, and the crushing resistance ``T_Rd,max`` used in the shear-torsion
interaction (Eq. 6.29).

Units follow the rest of ``ec2.uls``: lengths in m, strengths in MPa, torsion
in kN·m; reinforcement is returned in SI (m²/m for stirrups per unit length,
m² for the total longitudinal area), and resistances in kN·m.
"""


def calc_torsion(ted: float, b: float, h: float,
                 fck: float, g_c: float, fyk: float, g_s: float,
                 cott: float, cover: float = 0.0,
                 alpha_cc: float = 1.0, trace=None) -> dict:
    """Design a solid rectangular section for St-Venant torsion (EC2 §6.3).

    Args:
        ted (float): design torsion moment T_Ed [kN·m].
        b (float): section width [m].
        h (float): section height [m].
        fck (float): characteristic concrete strength [MPa].
        g_c (float): concrete partial factor.
        fyk (float): characteristic steel strength [MPa].
        g_s (float): steel partial factor.
        cott (float): truss inclination cot(theta) (1.0 ≤ cot θ ≤ 2.5).
        cover (float): mechanical cover to the longitudinal-bar centre [m]; a
            lower bound of 2·cover is applied to the effective wall thickness
            (EC2 §6.3.2(1)). Defaults to 0.0 (no lower bound).
        alpha_cc (float): long-term/loading coefficient on f_cd. Defaults to 1.0.
        trace: optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the design records its steps into it. ``None`` (default) is a no-op —
            the trace only *records* what was computed, so the result is
            unchanged.

    Returns:
        dict with keys:
          t_ef  [m]     — effective wall thickness A/u (≥ 2·cover).
          A_k   [m²]    — area enclosed by the wall centre-line.
          u_k   [m]     — centre-line perimeter.
          TRd_max [kN·m]— crushing torsion resistance (Eq. 6.30).
          Asw_tor_s [m²/m] — closed torsion stirrups, area per unit length,
                             per single leg (add to the per-leg shear stirrups).
          Asl_tor [m²]  — total longitudinal torsion steel, to distribute
                          around u_k.
          util          — T_Ed / T_Rd,max (the torsion side of Eq. 6.29).

    """
    ted = abs(ted)
    area = b * h
    peri = 2.0 * (b + h)
    t_ef = area / peri
    if cover > 0.0:
        t_ef = max(t_ef, 2.0 * cover)
    # Keep the centre-line area positive for slender sections.
    t_ef = min(t_ef, 0.499 * min(b, h))

    a_k = (b - t_ef) * (h - t_ef)
    u_k = 2.0 * ((b - t_ef) + (h - t_ef))

    fyd = fyk / g_s
    fcd = alpha_cc * fck / g_c
    niu = 0.6 * (1.0 - fck / 250.0)
    sin_cos = 1.0 / (cott + 1.0 / cott)           # sin(theta)·cos(theta)

    trd_max = 2.0 * niu * fcd * a_k * t_ef * sin_cos * 1000.0     # kN·m

    asw_tor_s = ted / (2.0 * a_k * fyd * cott) / 1000.0 if a_k > 0 else 0.0
    asl_tor = ted * cott * u_k / (2.0 * a_k * fyd) / 1000.0 if a_k > 0 else 0.0
    util = (ted / trd_max) if trd_max > 0.0 else float("inf")

    if trace is not None:
        trace.section("Torsion (EN 1992-1-1 §6.3)")
        trace.step("T_Ed", ted, "kN·m", clause="EN 1992-1-1 §6.3")
        trace.step("t_ef", t_ef, "m", clause="EN 1992-1-1 §6.3.2(1)",
                   expr="t_ef = A/u (≥ 2·cover)", latex=r"t_{ef}=A/u")
        trace.step("A_k", a_k, "m²", clause="EN 1992-1-1 §6.3.2",
                   expr="A_k = (b − t_ef)·(h − t_ef)",
                   latex=r"A_k=(b-t_{ef})(h-t_{ef})")
        trace.step("u_k", u_k, "m", expr="u_k = 2·[(b − t_ef) + (h − t_ef)]")
        trace.step("cot θ", cott, "—", note="1.0 ≤ cot θ ≤ 2.5")
        trace.step("T_Rd,max", trd_max, "kN·m", clause="EN 1992-1-1 §6.3.2(4)",
                   expr="T_Rd,max = 2·ν·f_cd·A_k·t_ef·sinθ·cosθ",
                   latex=r"T_{Rd,max}=2\nu f_{cd}A_k t_{ef}\sin\theta\cos\theta",
                   ok=(util <= 1.0))
        trace.step("Asw,tor/s", asw_tor_s, "m²/m", clause="EN 1992-1-1 §6.3.2(3)",
                   expr="Asw,tor/s = T_Ed/(2·A_k·f_yd·cot θ)",
                   latex=r"\frac{A_{sw,tor}}{s}=\frac{T_{Ed}}{2A_k f_{yd}\cot\theta}",
                   note="closed stirrups, per single leg")
        trace.step("Asl,tor", asl_tor, "m²", clause="EN 1992-1-1 §6.3.2(3)",
                   expr="Asl,tor = T_Ed·cot θ·u_k/(2·A_k·f_yd)",
                   latex=r"A_{sl,tor}=\frac{T_{Ed}\cot\theta\,u_k}{2A_k f_{yd}}",
                   note="total longitudinal, distributed around u_k")
        trace.step("T_Ed/T_Rd,max", util, "—", clause="EN 1992-1-1 Eq. 6.29",
                   note="torsion side of the shear–torsion interaction")

    return {
        "t_ef": t_ef,
        "A_k": a_k,
        "u_k": u_k,
        "TRd_max": trd_max,
        "Asw_tor_s": asw_tor_s,
        "Asl_tor": asl_tor,
        "util": util,
    }
