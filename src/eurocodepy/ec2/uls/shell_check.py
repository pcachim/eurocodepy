# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Shell element reinforcement design by the sandwich model — composite (EN 1992-1-1:2004 basis).

The shell element (membrane forces ``n`` and bending/torsion moments ``m`` per unit
length) is replaced by two layers of thickness ``t = 2·c`` (``c`` the distance to the
bar centres) at the lever arm ``z = h − t``. The sectional forces become in-plane
stresses of each layer,

``σx = n_x/(2t) ± m_x/(t·z)``, ``σy = n_y/(2t) ± m_y/(t·z)``, ``τ = n_xy/(2t) ∓ m_xy/(t·z)``

(upper signs: bottom layer; the formulae of EN 1992-1-1:2023 Eqs. G.12-G.17 and of
EN 1992-2:2005 Annex LL, Eqs. LL.137-LL.142, with the layers of thickness twice the cover,
LL.113-LL.114) and each layer is designed as a membrane — "the outer layers should be designed
as membrane elements, using the design rules of clause 6.109 and Annex F" (LL.112) — with
:func:`eurocodepy.ec2.uls.shell.calc_reinf_plane` (EN 1992-1-1:2004 Annex F): ``As = ftd·t/fyd``.
The concrete strut of each layer is checked (``strut_model`` of the input): ``"annex_f"``
(default; EN 1992-1-1:2004 Annex F.1(3)-(4)) against ``fcd`` where a layer needs no reinforcement
and ``ν·fcd``, ``ν = 0.6·(1 − fck/250)``, otherwise; ``"6.109"`` against the strength of the compression
field of EN 1992-2:2005 §6.109(103) (Eqs. 6.110 and 6.112, see
:func:`eurocodepy.ec2.uls.shell.membrane_strut_limit`).
The 2023 equivalent is :mod:`eurocodepy.ec2.uls2023.shell_check` (``ν = 0,4`` or Eq. G.9).

Sign convention (as ``uls2023.annex_g.sandwich_stresses``): tension positive; sagging
moments (``m_xx``, ``m_yy`` > 0) put the **bottom** layer in tension. Annex LL names the layers
superior (``s``) and inferior (``i``) and has ``+m/z`` in the superior one, i.e. its ``m`` is positive
for tension on the top face: :func:`eurocodepy.ec2.uls.shell.calc_reinf_shell` follows Annex LL (its
"top" layer is the one here called "bottom").

Cracking (Annex LL (102)-(104), (107)): with ``check_cracking`` (default) the principal stresses of the
uncracked section are evaluated through the thickness and the element is cracked where the failure criterion
of Eq. (LL.101) is exceeded (:func:`eurocodepy.ec2.uls.shell.shell_cracking`; transverse shear ``v_x``, ``v_y``
enter this check). An element that is **not cracked** needs no reinforcement from this model and only the
minimum principal stress is checked, ``σmin ≤ fcd`` (LL (103)): the result has zero areas and
``details["cracked"] = False``. ``check_cracking=False`` designs it as cracked.

Not covered (Annex LL): the out-of-plane shear of the inner layer ((109)-(111), (114)b: the truss force
``VEd·cot θ`` adds to the outer layers) and the eccentric reinforcement of (115)c.

Units: forces in **kN/m**, moments in **kNm/m**, strengths in **MPa**, lengths in **m**,
reinforcement areas in **m²/m**.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

from eurocodepy.ec2.materials import PartialFactorsMixin
from eurocodepy.ec2.uls.shell import calc_reinf_plane, shell_cracking, strut_limit

__all__ = ["ShellInput", "ShellResult", "eurocode2_shell_check", "layer_stresses"]


@dataclass
class ShellInput(PartialFactorsMixin):
    """Shell element data for the sandwich-model design."""

    n_xx: float               # membrane force, x [kN/m]
    n_yy: float               # membrane force, y [kN/m]
    n_xy: float               # membrane shear flow [kN/m]
    m_xx: float               # bending moment, x [kNm/m] (sagging +)
    m_yy: float               # bending moment, y [kNm/m]
    m_xy: float               # torsional moment [kNm/m]
    fck: float                # concrete strength [MPa]
    fyk: float                # reinforcement strength [MPa]
    thickness: float          # shell thickness h [m]
    cover: float              # distance from the surface to the bar centres [m]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float = 1.0
    strut_model: str = "annex_f"   # 'annex_f' (EN 1992-1-1:2004 F.1) | '6.109' (EN 1992-2)
    v_x: float = 0.0               # transverse shear [kN/m]: only for the cracking check
    v_y: float = 0.0
    check_cracking: bool = True    # LL (107): an uncracked element is not designed
    fctm: float | None = None      # mean tensile strength [MPa] of the cracking check (None: Table 3.1)


@dataclass
class ShellResult:
    """Result of the sandwich-model design (areas in m²/m)."""

    asx_bot: float
    asy_bot: float
    asx_top: float
    asy_top: float
    crushing: bool                  # the strut of a layer exceeds ν·fcd
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 shell (sandwich) — As(x/y bot)={self.asx_bot:.3e}/{self.asy_bot:.3e}, "
                f"As(x/y top)={self.asx_top:.3e}/{self.asy_top:.3e} m²/m"
                + (" (CRUSHING)" if self.crushing else ""))


def layer_stresses(n: tuple[float, float, float], m: tuple[float, float, float],
                   t: float, z: float) -> dict:
    """Return the in-plane stresses ``(σx, σy, τ)`` [force/length²] of the bottom and top layers."""
    tz = t * z
    return {"bottom": (0.5 * n[0] / t + m[0] / tz, 0.5 * n[1] / t + m[1] / tz,
                       0.5 * n[2] / t - m[2] / tz),
            "top": (0.5 * n[0] / t - m[0] / tz, 0.5 * n[1] / t - m[1] / tz,
                    0.5 * n[2] / t + m[2] / tz)}


def _needs_reinforcement(sx: float, sy: float, txy: float) -> bool:
    return not (sx < 0.0 and sy < 0.0 and sx * sy > txy**2)


def eurocode2_shell_check(inp: ShellInput, trace=None) -> ShellResult:
    """Design the four orthogonal reinforcements of a shell element (sandwich model).

    Args:
        inp: The shell element data.
        trace: Optional :class:`eurocodepy.calc_report.CalcReport` (recording only).

    Returns:
        A :class:`ShellResult`; ``details`` has, per layer (``"layers"``), the
        ``stresses``, ``ftdx``, ``ftdy`` (per unit of layer thickness, [kN/m²]),
        ``sigma_cd`` [kN/m²], ``cot`` (``None`` without reinforcement), ``nu`` and
        ``crushing``, plus ``t_layer``, ``z``, ``f_cd``, ``f_yd`` [MPa].

    """
    def _t(*a, **k):
        if trace is not None:
            trace.step(*a, **k)

    t = 2.0 * inp.cover
    z = inp.thickness - t
    if inp.cover <= 0.0 or z <= 0.0:
        msg = (f"the layers (t = 2·c = {t:.4g} m) do not fit in the shell "
               f"({inp.thickness:g} m): z = {z:.4g} m")
        raise ValueError(msg)
    fcd = inp.alpha_cc * inp.fck / inp.gamma_c
    fyd = inp.fyk / inp.gamma_s

    cracking = None
    if inp.check_cracking:
        cracking = shell_cracking(
            (inp.n_xx, inp.n_yy, inp.n_xy), (inp.m_xx, inp.m_yy, inp.m_xy), inp.thickness,
            inp.fck, (inp.v_x, inp.v_y), inp.fctm)
        if not cracking["cracked"]:
            # LL (103): only σmin ≤ fcd is checked
            over = bool(-cracking["sigma_min"] > fcd)
            if over:
                warnings.warn(
                    f"uncracked shell element: the minimum principal stress "
                    f"{-cracking['sigma_min']:.3g} MPa exceeds f_cd = {fcd:.3g} MPa (LL (103))",
                    UserWarning, stacklevel=2)
            if trace is not None:
                trace.section("Cracking (EN 1992-2 Annex LL (107))")
                _t("Φ", cracking["phi_max"], "—", clause="EN 1992-2:2005 Eq. (LL.101)",
                   expr="α·J2/fcm² + λ·√J2/fcm + β·I1/fcm − 1 ≤ 0", ok=True,
                   note="not cracked: no reinforcement from the sandwich model")
                _t("σ_min ≤ f_cd", -cracking["sigma_min"], "MPa", ok=(not over),
                   clause="EN 1992-2:2005 Annex LL (103)")
            return ShellResult(
                asx_bot=0.0, asy_bot=0.0, asx_top=0.0, asy_top=0.0, crushing=over,
                details={"cracked": False, "cracking": cracking, "layers": {}, "t_layer": t,
                         "z": z, "f_cd": fcd, "f_yd": fyd})
    stresses = layer_stresses((inp.n_xx, inp.n_yy, inp.n_xy),
                              (inp.m_xx, inp.m_yy, inp.m_xy), t, z)
    layers = {}
    crushing = False
    for name, (sx, sy, txy) in stresses.items():
        ftdx, ftdy, scd, cot = calc_reinf_plane(sx, sy, txy)
        reinforced = _needs_reinforcement(sx, sy, txy)
        lim = strut_limit(inp.strut_model, sx, sy, txy, inp.fck, fcd * 1e3,
                          cot if reinforced else None)
        nu = lim["factor"]
        crush = bool(scd > lim["limit"])
        crushing = crushing or crush
        layers[name] = {"stresses": (sx, sy, txy), "ftdx": ftdx, "ftdy": ftdy,
                        "sigma_cd": scd, "cot": (cot if reinforced else None),
                        "nu": nu, "crushing": crush, "strut": lim}

    def _area(name, key):
        return layers[name][key] * t / (fyd * 1e3)          # ftd·t/fyd [m²/m]

    asx_bot, asy_bot = _area("bottom", "ftdx"), _area("bottom", "ftdy")
    asx_top, asy_top = _area("top", "ftdx"), _area("top", "ftdy")

    if crushing:
        names = " and ".join(k for k, v in layers.items() if v["crushing"])
        warnings.warn(
            f"sandwich model: the concrete strut of the {names} layer exceeds ν·f_cd: "
            "increase the thickness or the concrete strength",
            UserWarning, stacklevel=2)

    if trace is not None:
        if cracking is not None:
            trace.section("Cracking (EN 1992-2 Annex LL (107))")
            _t("Φ", cracking["phi_max"], "—", clause="EN 1992-2:2005 Eq. (LL.101)",
               expr="α·J2/fcm² + λ·√J2/fcm + β·I1/fcm − 1 ≤ 0", ok=False,
               note="Φ > 0: cracked, the sandwich model applies")
        trace.section("Sandwich model (layers of a shell element)")
        _t("t", t, "m", expr="t = 2·c")
        _t("z", z, "m", expr="z = h − t")
        _t("f_cd", fcd, "MPa", expr="f_cd = α_cc·f_ck/γ_c")
        _t("f_yd", fyd, "MPa", expr="f_yd = f_yk/γ_s")
        for name, lay in layers.items():
            sx, sy, txy = lay["stresses"]
            _t(f"layer {name}", float(sx), "kN/m²", clause="EN 1992-1-1 Annex F",
               note=f"σx={sx:.4g}, σy={sy:.4g}, τ={txy:.4g} kN/m²")
            _t(f"σ_cd ({name})", lay["sigma_cd"] / 1e3, "MPa", ok=(not lay["crushing"]),
               subst=f"≤ ν·f_cd = {lay['nu']:.3g}·{fcd:.4g}")
        trace.section("Flexural reinforcement")
        _t("A_sx,bot", asx_bot * 1e4, "cm²/m", expr="f_tdx·t/f_yd")
        _t("A_sy,bot", asy_bot * 1e4, "cm²/m")
        _t("A_sx,top", asx_top * 1e4, "cm²/m")
        _t("A_sy,top", asy_top * 1e4, "cm²/m")

    return ShellResult(
        asx_bot=asx_bot, asy_bot=asy_bot, asx_top=asx_top, asy_top=asy_top,
        crushing=crushing,
        details={"layers": layers, "t_layer": t, "z": z, "f_cd": fcd, "f_yd": fyd,
                 "cracked": True if cracking is not None else None, "cracking": cracking})


