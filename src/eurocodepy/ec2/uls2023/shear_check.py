# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1:2023 Clause 8.2 shear verification of a rectangular RC section.

Same role and result object as :mod:`eurocodepy.ec2.uls.shear_check` (EN 1992-1-1:2004
§6.2), with the 2023 procedure of 8.2.1:

a. ``τEd ≤ τRdc,min`` (Eq. 8.20): the detailed verification may be omitted;
b. ``τEd ≤ τRd,c`` (Eq. 8.27): no calculated shear reinforcement (8.2.2);
c. otherwise the compression field of 8.2.3, with ``ν = 0,5`` (8.2.3(6)) and
   ``1 ≤ cot θ ≤ cot θmin`` (Eq. 8.41): the flattest strut that does not crush,
   which needs the least reinforcement, and ``Asw/s`` from Eq. (8.42).

The formulae are in :mod:`eurocodepy.ec2.uls2023.shear`. The minimum shear
reinforcement is ``ρw,min`` of Eq. (12.4) (:func:`.detailing.calc_asw_min_s`, with
vertical stirrups); ``asw_min_s`` overrides it, ``0.0`` omits it (minor members,
12.3.3(2); solid, ribbed and hollow core slabs, 12.4.2(3)).

Units: widths / depths in **m**, strengths in **MPa**, forces in **kN**, moments
in **kNm**, ``Asw/s`` in **m²/m**, longitudinal steel ``as_long`` in **m²**.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field

from eurocodepy.ec2.materials import PartialFactorsMixin, concrete_strength_factors

# not ``from eurocodepy.ec2.uls2023 import shear``: until this module is imported that
# attribute is still the EN 1992-1-1:2004 ``shear`` re-exported by the package
_s = importlib.import_module("eurocodepy.ec2.uls2023.shear")
_d = importlib.import_module("eurocodepy.ec2.uls2023.detailing")

__all__ = ["ShearInput", "ShearResult", "eurocode2_shear_check"]

_RHO_L_MAX = 0.02


@dataclass
class ShearInput(PartialFactorsMixin):
    """Rectangular RC section data for the 8.2 shear check."""

    b: float                  # web width [m]
    d: float                  # effective depth [m]
    fck: float                # concrete strength [MPa]
    fyk: float                # stirrup (and flexural) steel strength [MPa]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    gamma_v: float = 1.4      # shear resistance without shear reinforcement (Table 4.3)
    alpha_cc: float | None = None   # η_cc·k_tc of fcd; None = from fck and k_tc
    k_tc: float = 1.0         # 5.1.6(1): 1,0 (late loading) or 0,85
    annex: str | None = None  # national annex of the NDPs; None = values of the EN
    as_long: float = 0.0      # provided longitudinal steel [m²] (for ρl)
    d_lower: float = 20.0     # D_lower of the aggregate [mm] (ddg, 8.2.1(4))
    asw_min_s: float | None = None  # minimum Asw/s [m²/m]; None = Eq. (12.4) with
    #                                  `ductility`; 0.0 omits it (12.3.3(2), 12.4.2(3))
    ductility: str = "B"      # ductility class of the shear reinforcement
    nu: float = _s.NU_DEFAULT  # strut strength reduction (8.2.3(6))
    n_ed: float = 0.0         # axial force at the section [kN], tension positive
    m_ed: float | None = None  # moment at the section [kNm]: with it the shear span
    #                            acs of 8.2.2(3) is used when acs < 4d
    significant_compression: bool = False  # cot θmin = 3,0 (8.2.3(4))


@dataclass
class ShearResult:
    """Result of the 8.2 shear verification."""

    asw_s: float                    # stirrups Asw/s [m²/m]
    vrd_c: float                    # concrete shear resistance [kN]
    vrd_max: float | None           # compression field resistance [kN] (None if no field)
    cot: float                      # cot θ used
    crushing: bool
    mode: str          # 'no_verification'|'no_shear_reinf'|'stirrups'|'strut_crushing'
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2:2023 8.2 shear — {self.mode}"
                + (" (CRUSHING)" if self.crushing else "")
                + f": Asw/s={self.asw_s:.3e} m²/m, cotθ={self.cot:g}")


def eurocode2_shear_check(inp: ShearInput, v_ed: float, trace=None) -> ShearResult:  # noqa: PLR0915
    """Verify the shear of a rectangular RC section (EN 1992-1-1:2023 8.2).

    Args:
        inp: The section data.
        v_ed: Design shear force ``V_Ed`` [kN] (its magnitude is used).
        trace (CalcReport | None): Optional :class:`eurocodepy.calc_report.CalcReport`; ``None``
            (default) is a no-op.

    Returns:
        A :class:`ShearResult`. ``vrd_c`` is ``τRd,c·bw·z`` and ``vrd_max`` the
        compression-field resistance at the ``cot θ`` used.

    """
    def _t(*a, **k):
        if trace is not None:
            trace.step(*a, **k)

    def _sec(title):
        if trace is not None:
            trace.section(title)

    b, d = inp.b, inp.d
    v = abs(v_ed)
    z = _s.calc_lever_arm(d)
    fyd = inp.fyk / inp.gamma_s
    if inp.alpha_cc is None:
        alpha_cc = concrete_strength_factors(inp.fck, "2023", annex=inp.annex)[0] * inp.k_tc
    else:
        alpha_cc = inp.alpha_cc
    fcd = alpha_cc * inp.fck / inp.gamma_c
    rho_l = min(inp.as_long / (b * d), _RHO_L_MAX) if b * d > 0 else 0.0

    asw_min_s = (_d.calc_asw_min_s(inp.fck, inp.fyk, b, 90.0, inp.ductility)
                 if inp.asw_min_s is None else inp.asw_min_s)

    tau_ed = _s.calc_tau_ed(v, b, z)
    ddg = _s.calc_ddg(inp.fck, inp.d_lower)
    tau_min = _s.calc_taurdc_min(inp.fck, fyd, d, inp.d_lower, inp.gamma_v)

    # shear span and axial force (8.2.2(3)-(4))
    d_shear = None
    a_cs = None
    if inp.m_ed is not None and v > 0.0:
        a_cs = _s.calc_acs(inp.m_ed, v, d)
        d_shear = _s.calc_av(a_cs, d)
    if inp.n_ed != 0.0 and v > 0.0:
        if a_cs is None:
            msg = "m_ed is needed with n_ed (shear span acs of Eq. 8.30)"
            raise ValueError(msg)
        d_shear = (d if d_shear is None else d_shear) * _s.calc_kvp(inp.n_ed, v, d, a_cs)
    tau_rdc = _s.calc_taurdc(rho_l, inp.fck, d, fyd, inp.d_lower, inp.gamma_v, d_shear)
    vrdc = tau_rdc * b * z * 1000.0

    _sec("Inputs")
    _t("V_Ed", v, "kN")
    _t("f_ck", inp.fck, "MPa")
    _t("f_cd", fcd, "MPa", clause="EN 1992-1-1:2023 Eq. (5.3)",
       expr="f_cd = η_cc·k_tc·f_ck/γ_c", subst=f"{alpha_cc:.4g}·{inp.fck:g}/{inp.gamma_c:g}")
    _t("ρ_l", rho_l, "—", clause="EN 1992-1-1:2023 Eq. (8.28)",
       expr="ρ_l = A_sl/(b_w·d)", subst=f"{inp.as_long:.4g}/({b:g}·{d:.4g})")
    _t("z", z, "m", clause="EN 1992-1-1:2023 8.2.1(3)", expr="z = 0,9·d")
    _t("τ_Ed", tau_ed, "MPa", clause="EN 1992-1-1:2023 Eq. (8.18)",
       expr="τ_Ed = V_Ed/(b_w·z)", subst=f"{v:.4g}/({b:g}·{z:.4g})/1000")
    _sec("Resistance without shear reinforcement (8.2.1, 8.2.2)")
    _t("d_dg", ddg, "mm", clause="EN 1992-1-1:2023 8.2.1(4)",
       expr="d_dg = 16 + D_lower·min(1,(60/f_ck)²) ≤ 40",
       subst=f"D_lower={inp.d_lower:g}")
    _t("τ_Rdc,min", tau_min, "MPa", clause="EN 1992-1-1:2023 Eq. (8.20)",
       expr="τ_Rdc,min = 11/γ_v·√(f_ck/f_yd·d_dg/d)",
       subst=f"11/{inp.gamma_v:g}·√({inp.fck:g}/{fyd:.4g}·{ddg:.4g}/{d * 1000:.4g})")
    _t("τ_Rd,c", tau_rdc, "MPa", clause="EN 1992-1-1:2023 Eq. (8.27)",
       expr="τ_Rd,c = 0,66/γ_v·(100·ρ_l·f_ck·d_dg/d)^(1/3) ≥ τ_Rdc,min",
       subst=f"γ_v={inp.gamma_v:g}, ρ_l={rho_l:.4g}, f_ck={inp.fck:g}")
    _t("V_Rd,c", vrdc, "kN", expr="V_Rd,c = τ_Rd,c·b_w·z")

    details = {"tau_ed": tau_ed, "tau_rdc": tau_rdc, "tau_rdc_min": tau_min,
               "d_dg": ddg, "rho_l": rho_l, "z": z, "f_cd": fcd,
               "d_shear": d_shear, "asw_min": asw_min_s}

    if tau_ed <= tau_min:
        _t("τ_Ed ≤ τ_Rdc,min", True, "—", ok=True, clause="EN 1992-1-1:2023 8.2.1(1)a)",
           note="detailed verification may be omitted")
        return ShearResult(asw_s=asw_min_s, vrd_c=vrdc, vrd_max=None, cot=1.0,
                           crushing=False, mode="no_verification", details=details)
    if tau_ed <= tau_rdc:
        _t("τ_Ed ≤ τ_Rd,c", True, "—", ok=True, clause="EN 1992-1-1:2023 8.2.1(1)b)",
           note="no calculated shear reinforcement")
        return ShearResult(asw_s=asw_min_s, vrd_c=vrdc, vrd_max=None, cot=1.0,
                           crushing=False, mode="no_shear_reinf", details=details)

    # ── compression field (8.2.3): flattest strut that does not crush ──
    cot_min = _s.calc_cot_theta_min(inp.n_ed, v, inp.ductility,
                                    significant_compression=inp.significant_compression)
    cot_crush = _s.calc_cot_theta_crush(tau_ed, inp.nu, fcd)
    crushing = cot_crush is None
    cot = 1.0 if crushing else min(cot_min, cot_crush)
    vrd_max = _s.calc_vrd_max(b, z, inp.nu, fcd, cot)
    asw_s = max(_s.calc_asw_s(v, z, fyd, cot), asw_min_s)
    details.update({"cot_theta_min": cot_min, "cot_theta_crush": cot_crush})

    _sec("Compression field (8.2.3)")
    _t("τ_Ed > τ_Rd,c", True, "—", note="shear reinforcement required")
    _t("cot θ_min", cot_min, "—", clause="EN 1992-1-1:2023 Eq. (8.41)")
    _t("cot θ", cot, "—", clause="EN 1992-1-1:2023 8.2.3(4)",
       note="flattest strut that carries V_Ed (1 ≤ cot θ ≤ cot θ_min), ν = "
            f"{inp.nu:g}")
    _t("V_Rd,max", vrd_max, "kN", clause="EN 1992-1-1:2023 Eq. (8.44)",
       expr="V_Rd,max = ν·f_cd·b_w·z/(cot θ + tan θ)", ok=(not crushing))
    if crushing:
        _t("Strut crushing", True, "—", ok=False, clause="EN 1992-1-1:2023 Eq. (8.44)",
           note="σ_cd > ν·f_cd even at θ = 45°")
    _t("A_sw/s", asw_s, "m²/m", clause="EN 1992-1-1:2023 Eq. (8.42)",
       expr="A_sw/s = V_Ed/(z·f_ywd·cot θ)",
       subst=f"{v:.4g}/({z:.4g}·{fyd:.4g}·{cot:g})/1000", ok=(not crushing))

    return ShearResult(asw_s=float(asw_s), vrd_c=vrdc, vrd_max=float(vrd_max),
                       cot=float(cot), crushing=crushing,
                       mode="strut_crushing" if crushing else "stirrups",
                       details=details)
