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
import warnings
from dataclasses import dataclass, field

import numpy as np

from eurocodepy.ec2.materials import PartialFactorsMixin
from eurocodepy.ec2.uls.beam import calc_asl


def _fctm(fck: float) -> float:
    """Mean axial tensile strength fctm [MPa] (EN 1992-1-1 Table 3.1)."""
    if fck <= 50.0:
        return 0.30 * fck ** (2.0 / 3.0)
    return 2.12 * math.log(1.0 + (fck + 8.0) / 10.0)


MIN_REINF_OPTIONS = ("demand", "bottom", "all")


def min_reinf_applies(min_reinf: str, *, bottom: bool) -> bool:
    """Return whether the minimum reinforcement is provided on a face with no tension.

    ``"demand"`` (default): only where the moment needs reinforcement, a face with no
    tension gets 0; ``"bottom"``: also on the bottom faces, the tension face of the span
    (EN 1992-1-1 §9.3.1.1: the minimum applies where tension may occur); ``"all"``: on
    the four faces.
    """
    if min_reinf not in MIN_REINF_OPTIONS:
        msg = f"min_reinf must be one of {MIN_REINF_OPTIONS}, got '{min_reinf}'"
        raise ValueError(msg)
    return min_reinf == "all" or (min_reinf == "bottom" and bottom)


def strip_reinforcement(med_knm: float, cover: float, t: float, fcd_mpa: float,
                        fyd_mpa: float, as_min_coef: float,
                        xd_limit: float | None = None, *,
                        force_min: bool = False) -> tuple[float, float]:
    """Return ``(As [m²/m], d [m])`` for a 1 m strip with design moment ``med_knm`` [kNm/m].

    ``d = t − cover``. For a face not in tension (``med_knm ≤ 0``) zero, or the minimum
    ``as_min_coef·d`` with ``force_min``; otherwise the greater of the minimum and the
    area required by :func:`calc_asl`. If the moment is beyond what a singly reinforced
    strip can carry (``calc_asl`` has no solution) the area is ``nan``; if ``x/d``
    exceeds ``xd_limit`` (EN 1992-1-1 §5.6.3(2): 0.45 up to C50/60, 0.35 above) the
    strip is over-reinforced. Both cases issue a ``UserWarning``: compression
    reinforcement or a deeper slab is needed.
    """
    d = t - cover
    if d <= 0.0:
        return 0.0, d
    if med_knm <= 0.0:
        return (as_min_coef * 1.0 * d if force_min else 0.0), d
    with np.errstate(invalid="ignore"):               # the warning below says it
        as_cm2, _epss, _xd = calc_asl(1.0, d, med_knm, fcd_mpa, fyd_mpa)
    if not math.isfinite(as_cm2):
        warnings.warn(
            f"moment {med_knm:.4g} kNm/m exceeds the capacity of a singly reinforced "
            f"strip of depth {d:.4g} m (f_cd = {fcd_mpa:.4g} MPa): no solution, "
            "As = nan; increase the depth or provide compression reinforcement",
            UserWarning, stacklevel=3)
        return math.nan, d
    if xd_limit is not None and _xd > xd_limit + 1e-9:
        warnings.warn(
            f"moment {med_knm:.4g} kNm/m gives x/d = {_xd:.3f} > {xd_limit:g} in a strip of "
            f"depth {d:.4g} m: over-reinforced (no ductility); increase the depth or "
            "provide compression reinforcement",
            UserWarning, stacklevel=3)
    as_req = max(as_cm2, 0.0) * 1e-4              # cm²/m → m²/m
    return max(as_req, as_min_coef * 1.0 * d), d


@dataclass
class SlabInput(PartialFactorsMixin):
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
    min_reinf: str = "demand"  # 'demand' | 'bottom' | 'all' (see min_reinf_applies)


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

    xd_limit = 0.45 if inp.fck <= 50.0 else 0.35          # §5.6.3(2)

    def _as(med_knm, cover, *, bottom):
        return strip_reinforcement(
            med_knm, cover, t, fcd_mpa, fyd_mpa, as_min_coef, xd_limit,
            force_min=min_reinf_applies(inp.min_reinf, bottom=bottom))

    asx_bot, dbx = _as(inp.mx_bot, inp.cover_bot_x, bottom=True)
    asy_bot, dby = _as(inp.my_bot, inp.cover_bot_y, bottom=True)
    asx_top, dtx = _as(-inp.mx_top, inp.cover_top_x, bottom=False)
    asy_top, dty = _as(-inp.my_top, inp.cover_top_y, bottom=False)

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
    _t("A_s,min /bd", as_min_coef, "—", clause="EN 1992-1-1 §9.3.1.1",
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
