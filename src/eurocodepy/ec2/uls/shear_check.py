# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1 §6.2 shear verification of a rectangular RC section — composite.

The scalar formulae live in :mod:`eurocodepy.ec2.uls.shear`
(:func:`calc_vrdc`, :func:`calc_asws`). This module owns the *procedure* that
combines them into one verdict, so the whole EC2 shear check has a single source
of truth and a uniform result object with an optional calculation trace, exactly
like the EC3 / EC5 section checks:

* the concrete resistance ``V_Rd,c`` (§6.2.2); if ``V_Ed ≤ V_Rd,c`` no designed
  stirrups are needed (only the §9.2.2 minimum, when enabled);
* otherwise the variable-angle truss (§6.2.3): sweep ``cot θ`` from 2.5 down to
  1.0 in 0.1 steps and take the flattest strut that does not crush
  (``V_Rd,max ≥ V_Ed``), giving the stirrups ``Asw/s``;
* if the strut crushes even at ``θ = 45°`` (cot = 1) the section is inadequate
  in shear and is flagged as crushing, with the stirrups reported at the
  crushing limit.

Units: widths / depths in **m**, strengths in **MPa**, forces in **kN**,
``Asw/s`` in **m²/m**, longitudinal steel ``as_long`` in **m²**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from eurocodepy.ec2.uls.shear import calc_asws, calc_vrdc


@dataclass
class ShearInput:
    """Rectangular RC section data for the §6.2 shear check."""

    b: float                  # web width [m]
    d: float                  # effective depth [m]
    fck: float                # concrete strength [MPa]
    fyk: float                # stirrup strength [MPa]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    as_long: float = 0.0      # provided longitudinal steel [m²] (for ρl)
    min_shear: bool = True    # enforce the §9.2.2 minimum stirrups


@dataclass
class ShearResult:
    """Result of the §6.2 shear verification."""

    asw_s: float                    # stirrups Asw/s [m²/m]
    vrd_c: float                    # concrete shear resistance [kN]
    vrd_max: float | None           # strut crushing resistance [kN] (None if V≤VRdc)
    cot: float                      # cot θ used
    crushing: bool
    mode: str                       # 'no_shear_reinf'|'stirrups'|'strut_crushing'
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 §6.2 shear — {self.mode}"
                + (" (CRUSHING)" if self.crushing else "")
                + f": Asw/s={self.asw_s:.3e} m²/m, cotθ={self.cot:g}")


def eurocode2_shear_check(inp: ShearInput, v_ed: float,
                          trace=None) -> ShearResult:
    """Verify the shear of a rectangular RC section (EN 1992-1-1 §6.2).

    Args:
        inp: The section data.
        v_ed: Design shear force ``V_Ed`` [kN] (its magnitude is used).
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`. When given,
            the check records its steps into it. ``None`` (default) is a no-op —
            the trace only *records* what was computed.

    Returns:
        A :class:`ShearResult` with ``Asw/s``, ``V_Rd,c``, ``V_Rd,max``, the
        ``cot θ`` used, the crushing flag and the mode.

    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    b, d = inp.b, inp.d
    fck, fyk = inp.fck, inp.fyk
    gc, gs = inp.gamma_c, inp.gamma_s
    v = abs(v_ed)

    # ── concrete resistance V_Rd,c (§6.2.2) ──
    rho_l = min(inp.as_long / (b * d), 0.02) if (b * d) > 0 else 0.0
    _vrd_min, _vrd_c, vrdc = calc_vrdc(b, d, fck, gc, rho_l)
    vrdc = float(vrdc)

    # ── minimum stirrups ρw,min (§9.2.2), vertical ──
    asw_min = (0.08 * math.sqrt(fck) / fyk * b) if inp.min_shear else 0.0

    _sec("Inputs")
    _t("V_Ed", v, "kN")
    _t("f_ck", fck, "MPa")
    _t("f_yk", fyk, "MPa")
    _t("ρ_l", rho_l, "—", clause="EN 1992-1-1 §6.2.2",
       expr="ρ_l = min(As_l/(b·d), 0.02)")

    _sec("Concrete shear resistance (§6.2.2)")
    _t("V_Rd,c", vrdc, "kN", clause="EN 1992-1-1 §6.2.2(1)",
       expr="V_Rd,c = [C_Rd,c·k·(100·ρ_l·f_ck)^(1/3)]·b·d ≥ v_min·b·d")

    if v <= vrdc:
        _t("V_Ed ≤ V_Rd,c", True, "—", ok=True,
           note="no designed stirrups — minimum only" if inp.min_shear
                else "no shear reinforcement required")
        if inp.min_shear:
            _t("Asw/s,min", asw_min, "m²/m", clause="EN 1992-1-1 §9.2.2",
               expr="ρ_w,min = 0.08·√f_ck/f_yk")
        return ShearResult(
            asw_s=float(asw_min), vrd_c=vrdc, vrd_max=None, cot=2.5,
            crushing=False, mode="no_shear_reinf",
            details={"vrd_min": float(_vrd_min), "rho_l": rho_l,
                     "asw_min": float(asw_min)})

    # ── variable-angle truss (§6.2.3): flattest non-crushing strut ──
    _sec("Variable-angle truss (§6.2.3)")
    _t("V_Ed > V_Rd,c", True, "—",
       note="stirrups required; sweep cot θ 2.5 → 1.0")
    asw_s = vrd_max = None
    cot_used = 1.0
    cot = 2.5
    while cot >= 1.0 - 1e-9:
        cot_r = round(cot, 1)
        asw, vrdmax = calc_asws(b, d, fck, gc, fyk, gs, cot_r, v)
        if asw == asw:                     # not NaN → feasible at this angle
            asw_s, vrd_max, cot_used = asw, vrdmax, cot_r
            break
        cot -= 0.1

    crushing = False
    if asw_s is None:
        # Strut crushing even at θ = 45° (cot = 1): inadequate in shear. Report
        # the stirrups at the crushing limit (V = V_Rd,max).
        crushing = True
        cot_used = 1.0
        _asw, vrd_max = calc_asws(b, d, fck, gc, fyk, gs, 1.0, v)
        asw_s, _ = calc_asws(b, d, fck, gc, fyk, gs, 1.0, vrd_max)

    asw_s = asw_min if asw_s != asw_s else max(asw_s, asw_min)
    vrd_max = float(vrd_max)
    asw_s = float(asw_s)

    _t("cot θ", cot_used, "—", clause="EN 1992-1-1 §6.2.3(1)",
       note="flattest strut carried (1.0 ≤ cot θ ≤ 2.5)")
    _t("V_Rd,max", vrd_max, "kN", clause="EN 1992-1-1 §6.2.3(3)",
       expr="V_Rd,max = α_cw·b·z·ν₁·f_cd/(cot θ + tan θ)",
       ok=(not crushing))
    if crushing:
        _t("Strut crushing", True, "—", clause="EN 1992-1-1 §6.2.3(3)",
           ok=False, note="V_Ed > V_Rd,max even at θ = 45°")
    _t("Asw/s", asw_s, "m²/m", clause="EN 1992-1-1 §6.2.3(3)",
       expr="Asw/s = V_Ed/(z·f_ywd·cot θ)", ok=(not crushing))

    return ShearResult(
        asw_s=asw_s, vrd_c=vrdc, vrd_max=vrd_max, cot=cot_used,
        crushing=crushing,
        mode="strut_crushing" if crushing else "stirrups",
        details={"vrd_min": float(_vrd_min), "rho_l": rho_l,
                 "asw_min": float(asw_min)})
