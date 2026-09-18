# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1 §6.2 + §6.3 shear + torsion verification — composite.

Mirrors :func:`eurocodepy.ec5.uls.shear.check_shear_with_torsion` (the timber
equivalent): the scalar formulae already live in
:mod:`eurocodepy.ec2.uls.shear_check` (§6.2, the variable-angle truss) and
:mod:`eurocodepy.ec2.uls.torsion` (§6.3, thin-walled closed section). This
module owns the *procedure* that combines them for one rectangular section —
summing stirrups, applying the Eq. 6.29 interaction, and distributing the
torsion longitudinal steel — so the combination has a single source of truth,
reusable outside xdfem2D and unit-tested here, per ``dev/GRILLAGE_DESIGN.md``
(xdfem2d repository) §3/§5.1.

**Fixes a real defect found while writing the xdfem2d regression tests for
this migration (dev/GRILLAGE_DESIGN.md §2.3/§7)**: :class:`.shear_check.
ShearInput` has no cot-theta field at all — :func:`eurocode2_shear_check`
always sweeps internally for the flattest non-crushing strut, ignoring any
angle the caller might have wanted. Meanwhile :func:`.torsion.calc_torsion`
takes ``cott`` as a direct argument and its resistance genuinely depends on
it. xdfem2D's own ``RCSection.shear_reinforcement`` accepted a ``cotg_theta``
parameter that it silently never forwarded anywhere, while
``RCSection.torsion_reinforcement`` used it directly — so the two
resistances combined in Eq. 6.29 could be computed at *different* strut
angles, which violates EC2 §6.3.2(3) ("the same value of shear strut angle
should be used ... for both the torsion and shear verification").

This function does not accept a caller-supplied ``cotg_theta`` at all: it
runs the shear check first, reads back the cot θ it actually used
(``ShearResult.cot``), and passes that same value into ``calc_torsion``. The
two verifications are therefore always consistent by construction. This is a
deliberate behaviour change from xdfem2d's pre-migration ``rc_design.py``:
whenever the old ``elem.rc_cotg_theta`` did not coincide with the angle
``eurocode2_shear_check`` would have picked anyway, the torsion resistance
(``T_Rd,max``) and longitudinal/stirrup areas computed here will differ from
the old (buggy) numbers — see ``tests/test_ec2_shear_torsion.py`` for the
case that demonstrates this explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eurocodepy.ec2.uls.shear_check import ShearInput, eurocode2_shear_check
from eurocodepy.ec2.uls.torsion import calc_torsion

__all__ = [
    "ShearTorsionInput",
    "ShearTorsionResult",
    "distribute_torsion_longitudinal",
    "eurocode2_shear_torsion_check",
]


@dataclass
class ShearTorsionInput:
    """Rectangular RC section data for the combined §6.2/§6.3 check (SI: m, MPa).

    Deliberately uses plain ``fck``/``fyk`` scalars (like :class:`.shear_check.
    ShearInput` and :func:`.torsion.calc_torsion`), not the richer ``Concrete``/
    ``Reinforcement`` material objects used by :mod:`.column` — this check
    composes two functions that already take scalars, so there is nothing to
    gain from introducing an object layer here.
    """

    b: float                  # section width [m]
    h: float                  # section height [m]
    cover: float               # mechanical cover [m] (bounds the torsion wall thickness)
    fck: float                 # concrete strength [MPa]
    fyk: float                 # stirrup / longitudinal steel strength [MPa]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float = 1.0
    as_long: float = 0.0       # provided longitudinal steel [m²] (for V_Rd,c's rho_l)
    min_shear: bool = True     # enforce the §9.2.2 minimum shear stirrups


@dataclass
class ShearTorsionResult:
    """Result of the combined §6.2 shear + §6.3 torsion verification."""

    asw_shear_s: float             # shear-only stirrups Asw/s [m²/m]
    asw_tor_s: float                # torsion closed stirrups Asw,tor/s [m²/m], per leg
    asw_total_s: float              # asw_shear_s + 2·asw_tor_s [m²/m] (two vertical legs)
    asl_tor_total: float            # total longitudinal torsion steel [m²]
    asl_tor_by_face: dict           # {"top","bottom","side_left","side_right"} [m²]
    vrd_max: float | None           # shear strut-crushing resistance [kN] (None if V≤VRd,c)
    trd_max: float                  # torsion strut-crushing resistance [kN·m]
    cot: float                      # cot θ used by BOTH verifications (§6.3.2(3))
    v_ratio: float                  # V_Ed / V_Rd,max (0 if V_Rd,max is None)
    t_ratio: float                  # T_Ed / T_Rd,max
    interaction: float              # EC2 Eq. 6.29: t_ratio + v_ratio
    crushing: bool                  # shear crushing OR interaction > 1.0
    passed: bool                    # not crushing and interaction ≤ 1.0
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 §6.2+§6.3 shear+torsion — interaction {self.interaction:.3f}"
                + (" | CRUSHING" if self.crushing else "")
                + f" (cotθ={self.cot:g})")


def distribute_torsion_longitudinal(b: float, h: float, asl_tor_total: float,
                                    cover: float = 0.0,
                                    mode: str = "top_bottom") -> dict:
    """Distribute the total torsion longitudinal steel ``Asl,tor`` onto faces.

    EC2 §6.3.2(3) requires ``Asl,tor`` to be distributed around the perimeter
    ``u_k`` of the equivalent thin-walled section, with at least one bar in
    each corner — not simply split between the top and bottom flexural
    faces. ``dev/GRILLAGE_DESIGN.md`` §2.4 documents this as a known
    simplification in xdfem2D's pre-migration code; §5.1/§6 phase 3 asks for
    this function to exist now with the simplified behaviour as the
    (non-default-breaking) default, and the perimeter-proportional mode
    available as an explicit opt-in ahead of that phase.

    Args:
        b, h: outer section dimensions [m].
        asl_tor_total: total longitudinal torsion steel [m²] (e.g. from
            ``calc_torsion``'s ``Asl_tor``).
        cover: mechanical cover [m], used to reproduce the same effective
            wall thickness ``t_ef`` (and hence the same ``u_k``) that
            :func:`eurocodepy.ec2.uls.torsion.calc_torsion` computed the
            steel from, so the "perimeter" mode distributes it around the
            actual wall centre-line, not the outer section perimeter.
        mode: ``"top_bottom"`` (default) splits the total 50/50 onto the top
            and bottom faces, matching xdfem2D's current behaviour exactly
            (``side_left``/``side_right`` are 0.0). ``"perimeter"``
            distributes proportionally to each face's share of the wall
            centre-line perimeter ``u_k`` -- ``top``/``bottom`` get
            ``asl_tor_total · b_k/u_k`` each and ``side_left``/``side_right``
            get ``asl_tor_total · h_k/u_k`` each, where ``b_k``/``h_k`` are
            the wall centre-line dimensions.

    Returns:
        dict with keys ``top``, ``bottom``, ``side_left``, ``side_right``
        [m²], summing to ``asl_tor_total``.

    """
    if mode == "top_bottom":
        half = asl_tor_total / 2.0
        return {"top": half, "bottom": half, "side_left": 0.0, "side_right": 0.0}

    if mode != "perimeter":
        msg = f"Unknown distribution mode {mode!r} (expected 'top_bottom' or 'perimeter')"
        raise ValueError(msg)

    # Reproduce calc_torsion's own t_ef/u_k exactly (EC2 §6.3.2(1)).
    area = b * h
    peri = 2.0 * (b + h)
    t_ef = area / peri if peri > 0 else 0.0
    if cover > 0.0:
        t_ef = max(t_ef, 2.0 * cover)
    t_ef = min(t_ef, 0.499 * min(b, h))
    b_k = b - t_ef
    h_k = h - t_ef
    u_k = 2.0 * (b_k + h_k)
    if u_k <= 0.0:
        return {"top": asl_tor_total / 2.0, "bottom": asl_tor_total / 2.0,
                "side_left": 0.0, "side_right": 0.0}

    top = bottom = asl_tor_total * b_k / u_k
    side_left = side_right = asl_tor_total * h_k / u_k
    return {"top": top, "bottom": bottom,
            "side_left": side_left, "side_right": side_right}


def eurocode2_shear_torsion_check(inp: ShearTorsionInput, v_ed: float, t_ed: float,
                                  distribution_mode: str = "top_bottom",
                                  trace=None) -> ShearTorsionResult:
    """Combined shear + torsion check of one rectangular RC section (EC2 §6.2/§6.3).

    Runs :func:`eurocode2_shear_check` and :func:`calc_torsion` with the SAME
    cot θ (the angle the shear check picks — see the module docstring for why
    this fixes a real defect rather than only mirroring it), sums the closed
    stirrups, and verifies the linear interaction of Eq. 6.29.

    Args:
        inp: The section / material data.
        v_ed: Design shear force ``V_Ed`` [kN] (its magnitude is used).
        t_ed: Design torsion moment ``T_Ed`` [kN·m] (its magnitude is used).
        distribution_mode: Passed straight to
            :func:`distribute_torsion_longitudinal` -- ``"top_bottom"``
            (default, matches xdfem2D's pre-migration behaviour) or
            ``"perimeter"``.
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`; recording
            only — ``None`` leaves the result identical. Passed through to
            both the shear check and the torsion design, so both sets of
            steps land in the same report, plus a final interaction section.

    Returns:
        A :class:`ShearTorsionResult`.

    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    v_ed_abs = abs(v_ed)
    t_ed_abs = abs(t_ed)
    d = inp.h - inp.cover

    shear_inp = ShearInput(b=inp.b, d=d, fck=inp.fck, fyk=inp.fyk,
                           gamma_c=inp.gamma_c, gamma_s=inp.gamma_s,
                           as_long=inp.as_long, min_shear=inp.min_shear)
    shear_r = eurocode2_shear_check(shear_inp, v_ed_abs, trace=trace)

    # EC2 §6.3.2(3): use the SAME cot θ for torsion as the one the shear
    # check actually used — not a separately requested value (see module
    # docstring: eurocode2_shear_check never respected one anyway).
    cot = shear_r.cot

    tors = calc_torsion(t_ed_abs, inp.b, inp.h, inp.fck, inp.gamma_c,
                        inp.fyk, inp.gamma_s, cot, cover=inp.cover,
                        alpha_cc=inp.alpha_cc, trace=trace)

    asw_shear_s = float(shear_r.asw_s)
    asw_tor_s = float(tors["Asw_tor_s"])
    # Closed torsion stirrups add per leg to the two vertical walls, i.e.
    # 2·Asw_tor_s on top of the shear stirrups (matches xdfem2D's existing
    # convention, unchanged by this migration).
    asw_total_s = asw_shear_s + 2.0 * asw_tor_s

    vrd_max = shear_r.vrd_max
    v_ratio = (v_ed_abs / vrd_max) if vrd_max else 0.0
    t_ratio = float(tors["util"])
    interaction = t_ratio + v_ratio

    asl_tor_total = float(tors["Asl_tor"])
    asl_tor_by_face = distribute_torsion_longitudinal(
        inp.b, inp.h, asl_tor_total, cover=inp.cover, mode=distribution_mode)

    crushing = bool(shear_r.crushing or interaction > 1.0)
    passed = (not crushing) and interaction <= 1.0

    _sec("Shear + torsion interaction (EC2 §6.3.2(3) / Eq. 6.29)")
    _t("cot θ (shared)", cot, "—", clause="EN 1992-1-1 §6.3.2(3)",
       note="same strut angle used for both V_Rd,max and T_Rd,max")
    _t("V_Ed/V_Rd,max", v_ratio, "—", expr="V_Ed/V_Rd,max",
       subst=(f"{v_ed_abs:.4g}/{vrd_max:.4g}" if vrd_max else "—"))
    _t("T_Ed/T_Rd,max", t_ratio, "—", expr="T_Ed/T_Rd,max",
       subst=f"{t_ed_abs:.4g}/{float(tors['TRd_max']):.4g}")
    _t("Interaction", interaction, "—", clause="EN 1992-1-1 Eq. 6.29",
       expr="T_Ed/T_Rd,max + V_Ed/V_Rd,max ≤ 1.0",
       subst=f"{t_ratio:.4g} + {v_ratio:.4g}", ok=(interaction <= 1.0))
    _t("Asw/s (shear + 2·torsion)", asw_total_s, "m²/m",
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
                 "u_k": float(tors["u_k"])},
    )
