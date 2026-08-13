# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1 slab (plate bending) flexural reinforcement — composite.

The scalar strip design lives in :func:`eurocodepy.ec2.uls.beam.calc_asl`. This
module owns the *procedure* that sizes the four orthogonal reinforcements of a
slab element from its **Wood-Armer design moments** — bottom/top × x/y — each as
a 1 m strip with its own effective depth and the EN 1992-1-1 §9.3.1.1 minimum
reinforcement floor, with a uniform result object and an optional calculation
trace, exactly like the §6.2 shear and §6.4 punching checks.

Sign convention (matching the Wood-Armer output): the *bottom* moments
``mx_bot, my_bot`` are the sagging design moments (positive → bottom tension);
the *top* moments ``mx_top, my_top`` are the hogging design moments
(``≤ 0`` → their magnitude is the top-face demand).

Units: moments in **kNm/m**, strengths in **MPa**, thickness / covers in **m**,
reinforcement areas in **m²/m**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from eurocodepy.ec2.uls.beam import calc_asl


def _fctm(fck: float) -> float:
    """Mean axial tensile strength fctm [MPa] (EN 1992-1-1 Table 3.1)."""
    if fck <= 50.0:
        return 0.30 * fck ** (2.0 / 3.0)
    return 2.12 * math.log(1.0 + (fck + 8.0) / 10.0)


@dataclass
class SlabInput:
    """Concrete slab (plate) element data for the flexural reinforcement design."""

    mx_bot: float             # sagging design moment, x [kNm/m]
    my_bot: float             # sagging design moment, y [kNm/m]
    mx_top: float             # hogging design moment, x [kNm/m] (≤ 0)
    my_top: float             # hogging design moment, y [kNm/m] (≤ 0)
    fck: float                # concrete strength [MPa]
    fyk: float                # reinforcement strength [MPa]
    thickness: float          # slab thickness t [m]
    cover_bot_x: float        # mechanical cover, bottom x [m]
    cover_bot_y: float        # mechanical cover, bottom y [m]
    cover_top_x: float        # mechanical cover, top x [m]
    cover_top_y: float        # mechanical cover, top y [m]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float = 1.0


@dataclass
class SlabResult:
    """Result of the slab flexural reinforcement design."""

    asx_bot: float            # bottom x reinforcement [m²/m]
    asy_bot: float            # bottom y reinforcement [m²/m]
    asx_top: float            # top x reinforcement [m²/m]
    asy_top: float            # top y reinforcement [m²/m]
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 slab — As(x/y bot)={self.asx_bot:.3e}/{self.asy_bot:.3e}, "
                f"As(x/y top)={self.asx_top:.3e}/{self.asy_top:.3e} m²/m")


def eurocode2_slab_check(inp: SlabInput, trace=None) -> SlabResult:
    """Design the four orthogonal reinforcements of a concrete slab element.

    Args:
        inp: The slab element data (Wood-Armer design moments + geometry).
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps into it. ``None`` (default) is a no-op —
            the trace only *records* what was computed.

    Returns:
        A :class:`SlabResult` with the four reinforcement areas [m²/m].

    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    fcd_mpa = inp.alpha_cc * inp.fck / inp.gamma_c
    fyd_mpa = inp.fyk / inp.gamma_s
    t = inp.thickness
    # EN 1992-1-1 §9.3.1.1 → §9.2.1.1 minimum: As,min = max(0.26 fctm/fyk, 0.0013)·b·d.
    as_min_coef = max(0.26 * _fctm(inp.fck) / inp.fyk, 0.0013)

    def _as(med_knm, cover):
        """Reinforcement [m²/m] for a design moment [kNm/m] over a 1 m strip with
        mechanical cover *cover* [m]. Zero when the face is not in tension;
        otherwise the greater of the EC2 minimum and the required area."""
        d = t - cover
        if d <= 0.0 or med_knm <= 0.0:
            return 0.0, d
        as_cm2, _epss, _xd = calc_asl(1.0, d, med_knm, fcd_mpa, fyd_mpa)
        as_req = max(as_cm2, 0.0) * 1e-4              # cm²/m → m²/m
        return max(as_req, as_min_coef * 1.0 * d), d

    asx_bot, dbx = _as(inp.mx_bot, inp.cover_bot_x)
    asy_bot, dby = _as(inp.my_bot, inp.cover_bot_y)
    asx_top, dtx = _as(-inp.mx_top, inp.cover_top_x)
    asy_top, dty = _as(-inp.my_top, inp.cover_top_y)

    _sec("Design moments (Wood-Armer)")
    _t("m_x,bot", inp.mx_bot, "kNm/m", clause="Wood-Armer")
    _t("m_y,bot", inp.my_bot, "kNm/m")
    _t("m_x,top", inp.mx_top, "kNm/m")
    _t("m_y,top", inp.my_top, "kNm/m")

    _sec("Design strengths")
    _t("f_cd", fcd_mpa, "MPa", clause="EN 1992-1-1 §3.1.6",
       expr="f_cd = α_cc·f_ck/γ_c",
       subst=f"{inp.alpha_cc:g}·{inp.fck:g}/{inp.gamma_c:g}")
    _t("f_yd", fyd_mpa, "MPa", expr="f_yd = f_yk/γ_s",
       subst=f"{inp.fyk:g}/{inp.gamma_s:g}")
    _t("As,min/bd", as_min_coef, "—", clause="EN 1992-1-1 §9.3.1.1",
       expr="max(0.26·f_ctm/f_yk, 0.0013)")

    _sec("Flexural reinforcement (EN 1992-1-1 §6.1)")
    _t("A_sx,bot", asx_bot * 1e4, "cm²/m", clause="EN 1992-1-1 §6.1",
       expr="1 m strip, d = t − c", subst=f"d = {dbx:.4g} m")
    _t("A_sy,bot", asy_bot * 1e4, "cm²/m", subst=f"d = {dby:.4g} m")
    _t("A_sx,top", asx_top * 1e4, "cm²/m", subst=f"d = {dtx:.4g} m")
    _t("A_sy,top", asy_top * 1e4, "cm²/m", subst=f"d = {dty:.4g} m")

    return SlabResult(asx_bot=asx_bot, asy_bot=asy_bot,
                      asx_top=asx_top, asy_top=asy_top,
                      details={"fcd_mpa": fcd_mpa, "fyd_mpa": fyd_mpa,
                               "as_min_coef": as_min_coef})
