# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Combined shear + torsion design — **EN 1992-1-1:2023** (8.2, 8.3 and 8.3.6).

The 2023 counterpart of :mod:`eurocodepy.ec2.uls.shear_torsion`, with the same
procedure and result object:

* the shear check of 8.2 (:mod:`eurocodepy.ec2.uls2023.shear_check`) gives the
  shear stirrups and the compression-field angle ``cot θ``; with no shear
  reinforcement required, ``cot θmin`` is used;
* the torsion design of 8.3 (:mod:`eurocodepy.ec2.uls2023.torsion`) uses the SAME
  ``cot θ`` (the compression field is shared) and gives the closed stirrups
  (Eq. 8.82), the longitudinal steel (Eq. 8.83) and ``TRd,max`` (Eq. 8.84);
* the crushing of the compression field is verified with the linear interaction
  of Eq. (8.86), ``TEd/TRd,max + VEd/VRd,max ≤ 1,0``.

``ShearTorsionResult`` and ``distribute_torsion_longitudinal`` are the 2004 ones.
The minimum torsion stirrups of Table 12.1 (rows 8-9) are not added here; see
:mod:`eurocodepy.ec2.uls2023.detailing`.

Units: m, MPa, kN, kNm; ``Asw/s`` in m²/m, areas in m².
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from eurocodepy.ec2.materials import PartialFactorsMixin, concrete_strength_factors
from eurocodepy.ec2.uls.shear_torsion import (
    ShearTorsionResult,
    distribute_torsion_longitudinal,
)

# not ``from eurocodepy.ec2.uls2023 import ...``: until imported, those attributes are
# the EN 1992-1-1:2004 modules re-exported by the package
_shear = importlib.import_module("eurocodepy.ec2.uls2023.shear")
_shear_check = importlib.import_module("eurocodepy.ec2.uls2023.shear_check")
_torsion = importlib.import_module("eurocodepy.ec2.uls2023.torsion")

__all__ = [
    "ShearTorsionInput",
    "ShearTorsionResult",
    "distribute_torsion_longitudinal",
    "eurocode2_shear_torsion_check",
]


@dataclass
class ShearTorsionInput(PartialFactorsMixin):
    """Rectangular RC section data for the combined 8.2/8.3 check (SI: m, MPa)."""

    b: float                  # section width [m]
    h: float                  # section height [m]
    cover: float              # distance to the centre of the longitudinal bars [m]
    fck: float                # concrete strength [MPa]
    fyk: float                # stirrup / longitudinal steel strength [MPa]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    gamma_v: float = 1.4      # shear resistance without shear reinforcement (Table 4.3)
    alpha_cc: float | None = None   # η_cc·k_tc of fcd; None = from fck and k_tc
    k_tc: float = 1.0
    annex: str | None = None
    as_long: float = 0.0      # provided longitudinal steel [m²] (for ρl)
    d_lower: float = 20.0     # D_lower of the aggregate [mm]
    min_shear: bool = True    # False omits the minimum stirrups (see asw_min_s)
    asw_min_s: float | None = None  # minimum Asw/s [m²/m]; None = Eq. (12.4)
    ductility: str = "B"
    nu_t: float | None = None  # ν of Eq. (8.84); None = torsion_nu(cot θ)


def eurocode2_shear_torsion_check(inp: ShearTorsionInput, v_ed: float, t_ed: float,
                                  distribution_mode: str = "top_bottom",
                                  trace=None) -> ShearTorsionResult:
    """Combined shear + torsion check of one rectangular RC section (EN 1992-1-1:2023).

    Args:
        inp: The section / material data.
        v_ed: Design shear force ``V_Ed`` [kN] (its magnitude is used).
        t_ed: Design torsion moment ``T_Ed`` [kN·m] (its magnitude is used).
        distribution_mode: ``"top_bottom"`` (default) or ``"perimeter"``, passed to
            :func:`distribute_torsion_longitudinal`.
        trace (CalcReport | None): Optional :class:`eurocodepy.calc_report.CalcReport`; recording only.

    Returns:
        A :class:`ShearTorsionResult` (``interaction`` is Eq. 8.86).

    """
    def _t(*a, **k):
        if trace is not None:
            trace.step(*a, **k)

    v_abs, t_abs = abs(v_ed), abs(t_ed)
    alpha_cc = (inp.alpha_cc if inp.alpha_cc is not None
                else concrete_strength_factors(inp.fck, "2023", annex=inp.annex)[0] * inp.k_tc)
    asw_min = 0.0 if not inp.min_shear else inp.asw_min_s

    shear_inp = _shear_check.ShearInput(
        b=inp.b, d=inp.h - inp.cover, fck=inp.fck, fyk=inp.fyk,
        gamma_c=inp.gamma_c, gamma_s=inp.gamma_s, gamma_v=inp.gamma_v,
        alpha_cc=alpha_cc, annex=inp.annex, as_long=inp.as_long, d_lower=inp.d_lower,
        asw_min_s=asw_min, ductility=inp.ductility)
    shear_r = _shear_check.eurocode2_shear_check(shear_inp, v_abs, trace=trace)

    # the compression field is shared by shear and torsion
    if shear_r.mode in ("stirrups", "strut_crushing"):
        cot = shear_r.cot
    else:
        cot = _shear.calc_cot_theta_min(ductility=inp.ductility)

    tors = _torsion.calc_torsion(t_abs, inp.b, inp.h, inp.fck, inp.gamma_c, inp.fyk,
                                 inp.gamma_s, cot, cover=inp.cover, alpha_cc=alpha_cc,
                                 trace=trace, nu=inp.nu_t, annex=inp.annex)

    asw_shear_s = float(shear_r.asw_s)
    asw_tor_s = float(tors["Asw_tor_s"])
    # closed torsion stirrups add per leg to the two vertical walls
    asw_total_s = asw_shear_s + 2.0 * asw_tor_s

    vrd_max = shear_r.vrd_max
    v_ratio = (v_abs / vrd_max) if vrd_max else 0.0
    t_ratio = float(tors["util"])
    interaction = _torsion.interaction_sum([t_ratio, v_ratio])      # Eq. (8.86)

    asl_tor_total = float(tors["Asl_tor"])
    asl_tor_by_face = distribute_torsion_longitudinal(
        inp.b, inp.h, asl_tor_total, cover=tors["cover"], mode=distribution_mode)

    crushing = bool(shear_r.crushing or interaction > 1.0)
    passed = (not crushing) and interaction <= 1.0

    if trace is not None:
        trace.section("Shear + torsion interaction (EN 1992-1-1:2023 8.3.6)")
    _t("cot θ (shared)", cot, "—", clause="EN 1992-1-1:2023 8.3.4(4)",
       note="same compression field for V_Rd,max and T_Rd,max")
    _t("V_Ed/V_Rd,max", v_ratio, "—", expr="V_Ed/V_Rd,max",
       subst=(f"{v_abs:.4g}/{vrd_max:.4g}" if vrd_max else "—"))
    _t("T_Ed/T_Rd,max", t_ratio, "—", expr="T_Ed/T_Rd,max",
       subst=f"{t_abs:.4g}/{float(tors['TRd_max']):.4g}")
    _t("Interaction", interaction, "—", clause="EN 1992-1-1:2023 Eq. (8.86)",
       expr="Σ S_Ed/S_Rd ≤ 1.0", subst=f"{t_ratio:.4g} + {v_ratio:.4g}",
       ok=(interaction <= 1.0))
    _t("A_sw/s (shear + 2·torsion)", asw_total_s, "m²/m",
       expr="Asw/s = Asw/s,shear + 2·Asw,tor/s",
       subst=f"{asw_shear_s:.4g} + 2·{asw_tor_s:.4g}")
    _t("Crushing", crushing, "—", ok=(not crushing))

    return ShearTorsionResult(
        asw_shear_s=asw_shear_s, asw_tor_s=asw_tor_s, asw_total_s=asw_total_s,
        asl_tor_total=asl_tor_total, asl_tor_by_face=asl_tor_by_face,
        vrd_max=(float(vrd_max) if vrd_max is not None else None),
        trd_max=float(tors["TRd_max"]), cot=float(cot),
        v_ratio=float(v_ratio), t_ratio=t_ratio, interaction=float(interaction),
        crushing=crushing, passed=passed,
        details={"shear_mode": shear_r.mode, "vrd_c": float(shear_r.vrd_c),
                 "t_ef": float(tors["t_ef"]), "A_k": float(tors["A_k"]),
                 "u_k": float(tors["u_k"]), "nu": float(tors["nu"]),
                 "tau_t_ed": float(tors["tau_t_ed"])},
    )
