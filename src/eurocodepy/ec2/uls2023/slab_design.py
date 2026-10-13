# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1:2023 Annex G.4 slab flexural reinforcement design — composite (``uls2023.slab_design``).

Unlike :mod:`eurocodepy.ec2.uls.slab_check` (which takes Wood-Armer moments), this
takes the design moments ``mEdx``, ``mEdy`` and the torsional moment ``mEdxy`` of the
slab element and finds the required capacities of the bottom and top layers with
Tables G.2 and G.3 (the optimum reinforcement, G.4(5)); each is then designed as a
1 m strip (:func:`eurocodepy.ec2.uls.beam.calc_asl`) with its own effective depth and
the minimum reinforcement of 12.2(2) / Table 12.2 (Eq. 12.1: ``MR,min ≥ Mcr`` with
the lever arm taken as ``0,9·d``).

The simplified treatment applies for ``nEd = 0`` and ``|mEdxy| < 0,07·d²·fcd``
(G.4(5)); otherwise a ``UserWarning`` is issued and ``details["torsion_simplified_ok"]``
is ``False`` (use the sandwich model, :func:`.annex_g.shell_design`).

Sign convention: sagging moments positive (bottom tension), hogging negative
(Tables G.2 and G.3). Units: moments in **kNm/m**, strengths in **MPa**, lengths in
**m**, reinforcement areas in **m²/m**.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

from eurocodepy.ec2.materials import PartialFactorsMixin, concrete_strength_factors
from eurocodepy.ec2.uls.slab_check import SlabResult, min_reinf_applies, strip_reinforcement
from eurocodepy.ec2.uls2023 import annex_g as _g

__all__ = ["SlabInput", "SlabResult", "eurocode2_slab_check"]

_FCK_LIMIT = 50.0


def _fctm(fck: float) -> float:
    """Mean tensile strength [MPa], EN 1992-1-1:2023 Table 5.1."""
    return 0.3 * fck ** (2.0 / 3.0) if fck <= _FCK_LIMIT else 1.1 * fck ** (1.0 / 3.0)


@dataclass
class SlabInput(PartialFactorsMixin):
    """Concrete slab element data (design moments of the element)."""

    m_x: float                # design moment, x [kNm/m] (sagging +)
    m_y: float                # design moment, y [kNm/m]
    m_xy: float               # design torsional moment [kNm/m]
    fck: float                # concrete strength [MPa]
    fyk: float                # reinforcement strength [MPa]
    thickness: float          # slab thickness [m]
    cover_bot_x: float        # distance to the centre of the bottom x bars [m]
    cover_bot_y: float
    cover_top_x: float
    cover_top_y: float
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float | None = None   # η_cc·k_tc of fcd; None = from fck and k_tc
    k_tc: float = 1.0
    annex: str | None = None
    min_reinf: str = "demand"  # 'demand' | 'bottom' | 'all': faces with no tension that get As,min


def eurocode2_slab_check(inp: SlabInput, trace=None) -> SlabResult:
    """Design the four orthogonal reinforcements of a slab element (Annex G.4(5)).

    Returns:
        A :class:`SlabResult`; ``details`` has the required capacities
        (``m_rdx``, ``m_rdy``, ``m_rdx_top``, ``m_rdy_top`` [kNm/m]), the table rows
        (``case_bot``, ``case_top``) and ``torsion_simplified_ok``.

    """
    def _t(*a, **k):
        if trace is not None:
            trace.step(*a, **k)

    def _sec(title):
        if trace is not None:
            trace.section(title)

    alpha_cc = (inp.alpha_cc if inp.alpha_cc is not None
                else concrete_strength_factors(inp.fck, "2023", annex=inp.annex)[0] * inp.k_tc)
    fcd = alpha_cc * inp.fck / inp.gamma_c
    fyd = inp.fyk / inp.gamma_s
    t = inp.thickness
    fctm = _fctm(inp.fck)

    bot = _g.slab_optimum_bottom(inp.m_x, inp.m_y, inp.m_xy)
    top = _g.slab_optimum_top(inp.m_x, inp.m_y, inp.m_xy)

    def _as(med, cover, *, bottom):
        d = t - cover
        # Eq. (12.1): MR,min = As,min·fyk·0.9·d ≥ Mcr = fctm·t²/6 (per metre)
        as_min = fctm * t**2 / (5.4 * d * inp.fyk) if d > 0 else 0.0
        return strip_reinforcement(
            med, cover, t, fcd, fyd, as_min / d if d > 0 else 0.0,
            force_min=min_reinf_applies(inp.min_reinf, bottom=bottom))

    asx_bot, dbx = _as(bot["m_rdx"], inp.cover_bot_x, bottom=True)
    asy_bot, dby = _as(bot["m_rdy"], inp.cover_bot_y, bottom=True)
    asx_top, dtx = _as(top["m_rdx"], inp.cover_top_x, bottom=False)
    asy_top, dty = _as(top["m_rdy"], inp.cover_top_y, bottom=False)

    d_min = min(dbx, dby, dtx, dty)
    ok = _g.slab_torsion_simplified_ok(inp.m_xy, d_min, fcd)
    if not ok:
        warnings.warn(
            f"|m_xy| = {abs(inp.m_xy):.4g} kNm/m ≥ 0,07·d²·f_cd: the optimum formulae of "
            "G.4(5) do not apply; design with the sandwich model (annex_g.shell_design)",
            UserWarning, stacklevel=2)

    _sec("Design moments (Annex G.4)")
    _t("m_Ed,x", inp.m_x, "kNm/m", clause="EN 1992-1-1:2023 G.4(5)")
    _t("m_Ed,y", inp.m_y, "kNm/m")
    _t("m_Ed,xy", inp.m_xy, "kNm/m")
    _t("|m_Ed,xy| < 0,07·d²·f_cd", ok, "—", ok=ok, clause="EN 1992-1-1:2023 G.4(5)")
    _sec("Required capacities (Tables G.2 and G.3)")
    _t("m_Rdx", bot["m_rdx"], "kNm/m", clause="EN 1992-1-1:2023 Table G.2",
       note=f"row {bot['case']}")
    _t("m_Rdy", bot["m_rdy"], "kNm/m")
    _t("m'_Rdx", top["m_rdx"], "kNm/m", clause="EN 1992-1-1:2023 Table G.3",
       note=f"row {top['case']}")
    _t("m'_Rdy", top["m_rdy"], "kNm/m")
    _sec("Flexural reinforcement")
    _t("A_sx,bot", asx_bot * 1e4, "cm²/m", subst=f"d = {dbx:.4g} m")
    _t("A_sy,bot", asy_bot * 1e4, "cm²/m", subst=f"d = {dby:.4g} m")
    _t("A_sx,top", asx_top * 1e4, "cm²/m", subst=f"d = {dtx:.4g} m")
    _t("A_sy,top", asy_top * 1e4, "cm²/m", subst=f"d = {dty:.4g} m")

    return SlabResult(
        asx_bot=asx_bot, asy_bot=asy_bot, asx_top=asx_top, asy_top=asy_top,
        details={"m_rdx": bot["m_rdx"], "m_rdy": bot["m_rdy"],
                 "m_rdx_top": top["m_rdx"], "m_rdy_top": top["m_rdy"],
                 "case_bot": bot["case"], "case_top": top["case"],
                 "torsion_simplified_ok": ok, "f_cd": fcd, "fctm": fctm})
