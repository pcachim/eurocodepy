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
(G.4(5)). Otherwise — or with ``method="sandwich"`` — the **sandwich model** of
G.4(1)-(3) is used: the element is replaced by two layers of thickness ``t = 2·c``
(``c`` the mean distance to the bar centres) at the lever arm ``z = h − t``, the
sectional forces ``nEd`` (optional, ``n_x``, ``n_y``, ``n_xy`` [kN/m]) and moments become
in-plane stresses of each layer (Eqs. G.12-G.17) and each layer is designed as a membrane
(Table G.1: ``As = ftd·t/fyd``). Each layer's strut is checked: ``σcd ≤ ν·fcd`` with
``ν = 0,4`` (Eq. G.8, ``nu_mode="simple"``) or Eq. (G.9) (``"strain"``); ``details["crushing"]``
is the verdict and a ``UserWarning`` says so. ``method="auto"`` (default) takes the tables
where they apply and the sandwich model otherwise; ``"optimum"`` forces the tables
(``UserWarning`` outside their range).

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
    n_x: float = 0.0          # in-plane forces of a shell element [kN/m] (sandwich model only)
    n_y: float = 0.0
    n_xy: float = 0.0
    method: str = "auto"      # 'auto' | 'optimum' (Tables G.2/G.3) | 'sandwich' (G.4(1))
    nu_mode: str = "simple"   # ν of the sandwich layers: 'simple' 0,4 (G.8) | 'strain' (G.9)
    lam: float = 1.0          # provided/required reinforcement, for ε1 (G.3(7)d)
    e_s: float = 200000.0     # modulus of the reinforcement [MPa]


_METHODS = ("auto", "optimum", "sandwich")
_NU_MODES = ("simple", "strain")


def eurocode2_slab_check(inp: SlabInput, trace=None) -> SlabResult:
    """Design the four orthogonal reinforcements of a slab element (Annex G.4(5)).

    Returns:
        A :class:`SlabResult`; ``details`` has the required capacities
        (``m_rdx``, ``m_rdy``, ``m_rdx_top``, ``m_rdy_top`` [kNm/m]; in the sandwich
        model ``ftd·t·z`` of each layer), ``method`` (``"optimum"`` or ``"sandwich"``),
        ``torsion_simplified_ok`` and ``crushing`` (``None`` for the tables; for the
        sandwich model whether a layer's strut exceeds ``ν·fcd``) with, for the sandwich
        model, ``layers`` (per layer: ``ftdx``, ``ftdy``, ``sigma_cd``, ``nu``, ``crushing``,
        ``case``, ``cot``), ``t_layer`` and ``z``.

    """
    if inp.method not in _METHODS:
        msg = f"method must be one of {_METHODS}, got '{inp.method}'"
        raise ValueError(msg)
    if inp.nu_mode not in _NU_MODES:
        msg = f"nu_mode must be one of {_NU_MODES}, got '{inp.nu_mode}'"
        raise ValueError(msg)
    in_plane = any((inp.n_x, inp.n_y, inp.n_xy))
    if inp.method == "optimum" and in_plane:
        msg = "the optimum formulae of G.4(5) are for nEd = 0: use method='sandwich'"
        raise ValueError(msg)

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

    d_min = t - max(inp.cover_bot_x, inp.cover_bot_y, inp.cover_top_x, inp.cover_top_y)
    simplified_ok = (not in_plane) and _g.slab_torsion_simplified_ok(inp.m_xy, d_min, fcd)
    if inp.method == "sandwich" or (inp.method == "auto" and not simplified_ok):
        return _sandwich(inp, fcd, fyd, fctm, trace)

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
                 "torsion_simplified_ok": ok, "f_cd": fcd, "fctm": fctm,
                 "method": "optimum", "crushing": None})


def _sandwich(inp: SlabInput, fcd: float, fyd: float, fctm: float, trace) -> SlabResult:
    """Annex G.4(1)-(3): the two-layer sandwich model, each layer a membrane (Table G.1)."""
    covers = (inp.cover_bot_x, inp.cover_bot_y, inp.cover_top_x, inp.cover_top_y)
    t_layer = 2.0 * sum(covers) / len(covers)
    z = inp.thickness - t_layer
    if z <= 0.0 or t_layer <= 0.0:
        msg = (f"the layers (t = 2·c = {t_layer:.4g} m) do not fit in the slab "
               f"({inp.thickness:g} m): z = {z:.4g} m")
        raise ValueError(msg)

    n = (inp.n_x, inp.n_y, inp.n_xy)
    m = (inp.m_x, inp.m_y, inp.m_xy)
    layers = _g.shell_design(n, m, t_layer, z)
    fyd_kpa, fcd_kpa = fyd * 1e3, fcd * 1e3                       # [kN/m²]

    crushing = False
    out = {}
    for name, lay in layers.items():
        if lay["case"] == "no_reinforcement":
            nu = 1.0                                              # G.3(1): σ ≤ fcd
        elif inp.nu_mode == "simple":
            nu = _g.calc_nu_simple()                              # G.8
        else:
            nu = _g.estimate_nu(lay["ftdx"], lay["ftdy"], lay["cot"], fyd, inp.e_s, inp.lam)
        lay_crush = bool(lay["sigma_cd"] > nu * fcd_kpa)
        crushing = crushing or lay_crush
        out[name] = {**lay, "nu": nu, "crushing": lay_crush}

    def _area(layer, key, *, bottom):
        a = layer[key] * t_layer / fyd_kpa                        # ftd·t / fyd [m²/m]
        if min_reinf_applies(inp.min_reinf, bottom=bottom):
            d = inp.thickness - (inp.cover_bot_x if bottom else inp.cover_top_x)
            # Eq. (12.1): MR,min = As,min·fyk·0.9·d ≥ Mcr = fctm·t²/6 (per metre)
            a = max(a, fctm * inp.thickness**2 / (5.4 * d * inp.fyk))
        return a

    asx_bot, asy_bot = _area(out["bottom"], "ftdx", bottom=True), _area(out["bottom"], "ftdy", bottom=True)
    asx_top, asy_top = _area(out["top"], "ftdx", bottom=False), _area(out["top"], "ftdy", bottom=False)

    if crushing:
        names = [k for k, v in out.items() if v["crushing"]]
        warnings.warn(
            "sandwich model: the concrete strut of the " + " and ".join(names)
            + " layer exceeds ν·f_cd (G.5): increase the thickness or the concrete strength",
            UserWarning, stacklevel=3)

    if trace is not None:
        trace.section("Sandwich model (Annex G.4)")
        trace.step("t", t_layer, "m", clause="EN 1992-1-1:2023 G.4(2)", expr="t = 2·c")
        trace.step("z", z, "m", expr="z = h − t")
        for name, lay in out.items():
            trace.step(f"layer {name}", lay["case"], "—", clause="EN 1992-1-1:2023 Table G.1",
                       note=f"σx,σy,τ = {lay['stresses'][0]:.4g}, {lay['stresses'][1]:.4g}, "
                            f"{lay['stresses'][2]:.4g} kN/m²")
            trace.step(f"σ_cd ({name})", lay["sigma_cd"] / 1e3, "MPa", ok=(not lay["crushing"]),
                       subst=f"≤ ν·f_cd = {lay['nu']:g}·{fcd:.4g}")
        trace.section("Flexural reinforcement")
        trace.step("A_sx,bot", asx_bot * 1e4, "cm²/m", expr="f_tdx·t/f_yd")
        trace.step("A_sy,bot", asy_bot * 1e4, "cm²/m")
        trace.step("A_sx,top", asx_top * 1e4, "cm²/m")
        trace.step("A_sy,top", asy_top * 1e4, "cm²/m")

    b, tp = out["bottom"], out["top"]
    return SlabResult(
        asx_bot=asx_bot, asy_bot=asy_bot, asx_top=asx_top, asy_top=asy_top,
        details={"method": "sandwich", "layers": out, "t_layer": t_layer, "z": z,
                 "crushing": crushing, "f_cd": fcd, "fctm": fctm,
                 "torsion_simplified_ok": (not any((inp.n_x, inp.n_y, inp.n_xy))
                                           and _g.slab_torsion_simplified_ok(
                                               inp.m_xy, inp.thickness - max(covers), fcd)),
                 # the capacities ftd·t·z: the Tables G.2/G.3 values when nEd = 0
                 "m_rdx": b["ftdx"] * t_layer * z, "m_rdy": b["ftdy"] * t_layer * z,
                 "m_rdx_top": tp["ftdx"] * t_layer * z, "m_rdy_top": tp["ftdy"] * t_layer * z})
