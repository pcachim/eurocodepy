# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1:2023 Annex G.3 membrane (in-plane) reinforcement design — composite.

The 2023 counterpart of :mod:`eurocodepy.ec2.uls.membrane_check`, with the same
input fields (plus the 2023 ones) and result object:

* the optimum reinforcement of Table G.1 (:func:`.annex_g.membrane_optimum`), as
  forces per unit length ``n_sx = ftdx*·t``, ``n_sy = ftdy*·t`` and the strut stress
  ``σcd*``;
* the orthogonal reinforcement ``As,x = n_sx/fyd``, ``As,y = n_sy/fyd`` [m²/m],
  split evenly between the top and bottom layers;
* the crushing check of the compression field, ``σcd ≤ ν·fcd`` (Eq. G.5) with
  ``ν = 0,4`` (Eq. G.8, ``nu_mode="simple"``) or the refined ``ν`` of Eq. (G.9)
  (``nu_mode="strain"``); where no reinforcement is required (both stresses
  compressive, ``σx·σy > τ²``) the principal compressive stress is limited to
  ``fcd`` (G.3(1)).

Units: forces per unit length in **kN/m**, strengths in **MPa**, thickness in **m**,
reinforcement areas in **m²/m**. Tension is positive.
"""

from __future__ import annotations

from dataclasses import dataclass

from eurocodepy.ec2.materials import PartialFactorsMixin, concrete_strength_factors
from eurocodepy.ec2.uls.membrane_check import MembraneResult
from eurocodepy.ec2.uls2023 import annex_g as _g

__all__ = ["MembraneInput", "MembraneResult", "eurocode2_membrane_check"]

_NU_MODES = ("simple", "strain")


@dataclass
class MembraneInput(PartialFactorsMixin):
    """Concrete membrane (plane-stress) element data for the reinforcement design."""

    n_xx: float               # membrane force per unit length, x [kN/m]
    n_yy: float               # membrane force per unit length, y [kN/m]
    n_xy: float               # membrane shear flow per unit length [kN/m]
    fck: float                # concrete strength [MPa]
    fyk: float                # reinforcement strength [MPa]
    thickness: float          # element thickness t [m]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float | None = None   # η_cc·k_tc of fcd; None = from fck and k_tc
    k_tc: float = 1.0
    annex: str | None = None
    nu_mode: str = "simple"   # 'simple' (ν = 0,4, G.8) or 'strain' (G.9-G.11)
    lam: float = 1.0          # provided/required reinforcement, for ε1 (G.3(7)d)
    e_s: float = 200000.0     # modulus of the reinforcement [MPa]


def eurocode2_membrane_check(inp: MembraneInput, trace=None) -> MembraneResult:
    """Design the orthogonal reinforcement of a concrete membrane element (Annex G.3).

    Args:
        inp: The membrane element data.
        trace (CalcReport | None): Optional :class:`eurocodepy.calc_report.CalcReport` (recording only).

    Returns:
        A :class:`MembraneResult`: ``theta`` is ``cot θ*`` (``None`` if no
        reinforcement is required); ``nsx``, ``nsy`` the reinforcement forces and
        ``nc`` the strut force ``σcd*·t`` [kN/m]; ``details`` has ``nu``, ``nu_mode``,
        ``case`` and ``eps_1``.

    """
    if inp.nu_mode not in _NU_MODES:
        msg = f"nu_mode must be one of {_NU_MODES}, got '{inp.nu_mode}'"
        raise ValueError(msg)

    def _t(*a, **k):
        if trace is not None:
            trace.step(*a, **k)

    def _sec(title):
        if trace is not None:
            trace.section(title)

    alpha_cc = (inp.alpha_cc if inp.alpha_cc is not None
                else concrete_strength_factors(inp.fck, "2023", annex=inp.annex)[0] * inp.k_tc)
    fyd_mpa = inp.fyk / inp.gamma_s
    fcd_mpa = alpha_cc * inp.fck / inp.gamma_c
    fyd, fcd = fyd_mpa * 1e3, fcd_mpa * 1e3           # [kN/m²]
    t = inp.thickness

    opt = _g.membrane_optimum(inp.n_xx, inp.n_yy, inp.n_xy)
    nsx, nsy, nc, cot = opt["ftdx"], opt["ftdy"], opt["sigma_cd"], opt["cot"]
    asx = nsx / fyd if fyd > 0 else 0.0
    asy = nsy / fyd if fyd > 0 else 0.0
    sigma_c = nc / t if t > 0 else 0.0                # [kN/m²]

    eps_1 = None
    if opt["case"] == "no_reinforcement":
        nu, limit = 1.0, fcd                          # G.3(1): σ ≤ fcd
    elif inp.nu_mode == "simple":
        nu = _g.calc_nu_simple()                      # G.8
        limit = nu * fcd
    else:
        eps_1 = _g.estimate_eps1(nsx, nsy, cot, fyd_mpa, inp.e_s, inp.lam)
        nu = _g.calc_nu(eps_1)                        # G.9
        limit = nu * fcd
    crushing = bool(sigma_c > limit)

    _sec("Membrane forces (per unit length)")
    _t("n_xx", inp.n_xx, "kN/m", clause="EN 1992-1-1:2023 G.3")
    _t("n_yy", inp.n_yy, "kN/m")
    _t("n_xy", inp.n_xy, "kN/m")
    _sec("Design strengths")
    _t("f_cd", fcd_mpa, "MPa", clause="EN 1992-1-1:2023 Eq. (5.3)",
       expr="f_cd = η_cc·k_tc·f_ck/γ_c", subst=f"{alpha_cc:.4g}·{inp.fck:g}/{inp.gamma_c:g}")
    _t("f_yd", fyd_mpa, "MPa", expr="f_yd = f_yk/γ_s", subst=f"{inp.fyk:g}/{inp.gamma_s:g}")
    _sec("Optimum reinforcement (Table G.1)")
    _t("case", opt["case"], "—", clause="EN 1992-1-1:2023 Table G.1")
    _t("cot θ*", cot if cot is not None else float("nan"), "—")
    _t("n_sx", nsx, "kN/m", expr="f_tdx*·t")
    _t("n_sy", nsy, "kN/m", expr="f_tdy*·t")
    _t("A_sx", asx * 1e4, "cm²/m", expr="A_sx = n_sx/f_yd")
    _t("A_sy", asy * 1e4, "cm²/m", expr="A_sy = n_sy/f_yd")
    _sec("Concrete crushing (G.3, G.5)")
    _t("σ_cd", sigma_c / 1e3, "MPa", clause="EN 1992-1-1:2023 Eq. (G.5)",
       expr="σ_cd = σ_cd*", subst=f"{nc:.4g}/{t:g}")
    _t("ν", nu, "—", clause="EN 1992-1-1:2023 Eq. (G.8)/(G.9)",
       note=f"{inp.nu_mode}" if opt["case"] != "no_reinforcement" else "no reinforcement: σ ≤ f_cd")
    _t("σ_cd ≤ ν·f_cd", sigma_c / 1e3, "MPa", ok=(not crushing),
       subst=f"{sigma_c / 1e3:.3g} ≤ {limit / 1e3:.3g}")

    return MembraneResult(
        asx=asx, asy=asy, asx_bot=asx / 2.0, asx_top=asx / 2.0,
        asy_bot=asy / 2.0, asy_top=asy / 2.0,
        nsx=nsx, nsy=nsy, nc=nc, sigma_c=sigma_c, fcd=fcd,
        theta=cot, crushing=crushing,
        details={"fyd": fyd, "nu": nu, "nu_mode": inp.nu_mode, "case": opt["case"],
                 "eps_1": eps_1})
