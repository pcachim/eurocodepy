# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1 membrane (in-plane) reinforcement design — composite.

The scalar force resolution lives in :func:`eurocodepy.ec2.uls.shell.calc_reinf_plane`
(the Wood/Baumann membrane equations, returning the reinforcement *forces* and
the concrete compression). This module owns the *procedure* that turns those
forces into reinforcement areas and a concrete-crushing verdict, so the whole
membrane design has a single source of truth and a uniform result object with an
optional calculation trace, exactly like the §6.2 shear and §6.4 punching checks.

* resolve the membrane forces ``n_xx, n_yy, n_xy`` [kN/m] into the reinforcement
  forces ``n_sx, n_sy`` and the concrete compression ``n_c`` (§6.109, via
  :func:`calc_reinf_plane`);
* size the orthogonal reinforcement ``As_x = max(n_sx, 0)/f_yd``,
  ``As_y = max(n_sy, 0)/f_yd`` [m²/m] and split each evenly between a top and a
  bottom layer (the usual orthogonal-mesh detailing);
* check the concrete stress ``σ_c = n_c / t`` against ``f_cd`` — a simplified
  crushing check (no §6.109 cracked-concrete ν reduction), at the same level of
  rigour as the beam-shear crushing check.

Units: forces per unit length in **kN/m**, strengths in **MPa**, thickness in
**m**, reinforcement areas in **m²/m**.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eurocodepy.ec2.uls.shell import calc_reinf_plane


@dataclass
class MembraneInput:
    """Concrete membrane (plane-stress) element data for the reinforcement design."""

    n_xx: float               # membrane force per unit length, x [kN/m]
    n_yy: float               # membrane force per unit length, y [kN/m]
    n_xy: float               # membrane shear flow per unit length [kN/m]
    fck: float                # concrete strength [MPa]
    fyk: float                # reinforcement strength [MPa]
    thickness: float          # element thickness t [m]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float = 1.0


@dataclass
class MembraneResult:
    """Result of the membrane reinforcement design."""

    asx: float                # reinforcement area, x [m²/m] (full, before split)
    asy: float                # reinforcement area, y [m²/m]
    asx_bot: float            # x reinforcement, bottom layer [m²/m]
    asx_top: float            # x reinforcement, top layer [m²/m]
    asy_bot: float            # y reinforcement, bottom layer [m²/m]
    asy_top: float            # y reinforcement, top layer [m²/m]
    nsx: float                # reinforcement force, x [kN/m]
    nsy: float                # reinforcement force, y [kN/m]
    nc: float                 # concrete compression force per unit length [kN/m]
    sigma_c: float            # concrete stress n_c/t [kN/m²]
    fcd: float                # design concrete strength [kN/m²]
    theta: float              # compression-field angle parameter
    crushing: bool
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 membrane — As_x={self.asx:.3e} As_y={self.asy:.3e} m²/m"
                + (" (CRUSHING)" if self.crushing else ""))


def eurocode2_membrane_check(inp: MembraneInput, trace=None) -> MembraneResult:
    """Design the orthogonal reinforcement of a concrete membrane element.

    Args:
        inp: The membrane element data.
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps into it. ``None`` (default) is a no-op —
            the trace only *records* what was computed.

    Returns:
        A :class:`MembraneResult` with the orthogonal reinforcement areas (full
        and split top/bottom), the concrete compression / stress and the
        crushing verdict.

    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    fyd = inp.fyk * 1e3 / inp.gamma_s               # [kN/m²]
    fcd = inp.alpha_cc * inp.fck * 1e3 / inp.gamma_c  # [kN/m²]
    t = inp.thickness

    nsx, nsy, nc, theta = calc_reinf_plane(inp.n_xx, inp.n_yy, inp.n_xy)
    asx = max(nsx, 0.0) / fyd if fyd > 0 else 0.0    # [m²/m]
    asy = max(nsy, 0.0) / fyd if fyd > 0 else 0.0
    sigma_c = nc / t if t > 0 else 0.0                # [kN/m²]
    crushing = bool(nc > fcd * t)

    _sec("Membrane forces (per unit length)")
    _t("n_xx", inp.n_xx, "kN/m", clause="EN 1992-1-1 §6.109",
       expr="n_xx = σ_x·t", latex=r"n_{xx}=\sigma_x\,t")
    _t("n_yy", inp.n_yy, "kN/m", expr="n_yy = σ_y·t",
       latex=r"n_{yy}=\sigma_y\,t")
    _t("n_xy", inp.n_xy, "kN/m", expr="n_xy = τ_xy·t",
       latex=r"n_{xy}=\tau_{xy}\,t")

    _sec("Design strengths")
    _t("f_cd", fcd / 1e3, "MPa", clause="EN 1992-1-1 §3.1.6",
       expr="f_cd = α_cc·f_ck/γ_c",
       subst=f"{inp.alpha_cc:g}·{inp.fck:g}/{inp.gamma_c:g}")
    _t("f_yd", fyd / 1e3, "MPa", expr="f_yd = f_yk/γ_s",
       subst=f"{inp.fyk:g}/{inp.gamma_s:g}")

    _sec("Reinforcement (Wood/Baumann)")
    _t("θ", theta, "—", clause="EN 1992-1-1 §6.109",
       note="compression-field angle parameter (cot θ) from the membrane solution")
    _t("n_sx", nsx, "kN/m", clause="EN 1992-1-1 §6.109",
       expr="n_sx = n_xx + |n_xy| (tension branch)")
    _t("n_sy", nsy, "kN/m", expr="n_sy = n_yy + |n_xy| (tension branch)")
    _t("A_sx", asx * 1e4, "cm²/m", clause="EN 1992-1-1 §6.109",
       expr="A_sx = max(n_sx, 0)/f_yd", latex=r"A_{sx}=\max(n_{sx},0)/f_{yd}")
    _t("A_sy", asy * 1e4, "cm²/m",
       expr="A_sy = max(n_sy, 0)/f_yd", latex=r"A_{sy}=\max(n_{sy},0)/f_{yd}")
    _t("A_sx,bot", asx / 2.0 * 1e4, "cm²/m", note="even top/bottom split")
    _t("A_sx,top", asx / 2.0 * 1e4, "cm²/m")
    _t("A_sy,bot", asy / 2.0 * 1e4, "cm²/m")
    _t("A_sy,top", asy / 2.0 * 1e4, "cm²/m")

    _sec("Concrete crushing")
    _t("σ_c", sigma_c / 1e3, "MPa", clause="EN 1992-1-1 §6.109",
       expr="σ_c = n_c/t", latex=r"\sigma_c=n_c/t")
    _t("f_cd", fcd / 1e3, "MPa", expr="f_cd = α_cc·f_ck/γ_c")
    _t("σ_c ≤ f_cd", sigma_c / 1e3, "MPa", ok=(not crushing),
       subst=f"{sigma_c / 1e3:.3g} ≤ {fcd / 1e3:.3g}",
       note="simplified crushing check (no §6.109 ν reduction)")

    return MembraneResult(
        asx=asx, asy=asy,
        asx_bot=asx / 2.0, asx_top=asx / 2.0,
        asy_bot=asy / 2.0, asy_top=asy / 2.0,
        nsx=nsx, nsy=nsy, nc=nc, sigma_c=sigma_c, fcd=fcd,
        theta=theta, crushing=crushing,
        details={"fyd": fyd})
