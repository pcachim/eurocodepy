# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1 §6.4 / EN 1992-1-1:2023 §8.4 punching verification — composite.

The scalar formulae live in the edition punch modules
(:mod:`eurocodepy.ec2.uls.punch` for :2004, :mod:`eurocodepy.ec2.uls2023.punch`
for :2023). This module owns the *procedure* that combines them for one column,
so the whole punching check is a single traced composite with a uniform result,
like the shear / EC3 / EC5 checks:

* control perimeters ``u0`` / ``u1`` (:func:`calc_perimeters`);
* the design punching stress ``v_Ed`` (:func:`calc_vedp`), with the load-
  eccentricity factor ``β`` floored at the user ``beta_min``;
* the resistance ``v_Rd,c`` and its minimum, the maximum resistance
  ``v_Rd,max`` (edition-specific: ``η_sys·v_Rd,c`` at 0.5·d for :2023, the strut
  crushing ``0.5·ν·f_cd`` at ``u0`` for :2004), and the outer perimeter
  ``u_out,ef`` (:2023);
* the utilisation, the ``needs_reinf`` and ``crushing`` verdicts.

Units: lengths in **m**, strengths in **MPa**, forces in **kN**, moments in
**kNm** (converted to the mm the punch helpers expect internally).

``dmax``/``eta_sys`` (:2023 only) default from
``dbase.get_edition_params("ec2", "punch_params", "2023")`` -- i.e. from
``Editions.ec2.2023.punch_params`` in eurocodes.json -- instead of being
hard-coded on this dataclass. See ``dev/dbase_versioning.md`` phases 3-4 in
the xdfem2d repository: this replaces the previous approach, where these two
EN 1992-1-1:2023 SS8.4 values were baked in as Python literal defaults, with
a single versioned source of truth that ``get_edition_data``/
``EurocodeMaterials`` consumers can also read. The resolved defaults are
unchanged (20.0 mm / 1.5) -- only where they come from has moved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eurocodepy import dbase

_MM = 1000.0     # m → mm


@dataclass
class PunchInput:
    """Column / slab data for a §6.4 punching check (SI: m, MPa)."""

    d: float                  # effective depth [m]
    bx: float                 # column size in x [m]
    fck: float                # concrete strength [MPa]
    fyk: float                # reinforcement strength [MPa]
    by: float | None = None   # column size in y [m] (None = circular)
    position: str = "center"  # 'center' | 'edge' | 'corner'
    dx: float = 0.0           # edge distance in x [m]
    dy: float = 0.0           # edge distance in y [m]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    gamma_v: float = 1.4
    alpha_cc: float = 1.0
    dmax: float | None = None     # max aggregate size [mm] (:2023); None -> from Editions
    eta_sys: float | None = None  # system factor η_sys (:2023); None -> from Editions
    edition: str = "2004"     # '2004' | '2023'

    def __post_init__(self) -> None:
        """Resolve ``dmax``/``eta_sys`` from the versioned edition data.

        Only fills in values left as ``None`` (explicit constructor args
        always win), and only looks the ``2023`` section up for the
        ``2023`` edition -- the ``2004`` edition never uses these fields.
        """
        if str(self.edition) == "2023":
            params = dbase.get_edition_params("ec2", "punch_params", "2023")
            if self.dmax is None:
                self.dmax = params.get("dmax", 20.0)
            if self.eta_sys is None:
                self.eta_sys = params.get("eta_sys", 1.5)
        else:
            if self.dmax is None:
                self.dmax = 20.0
            if self.eta_sys is None:
                self.eta_sys = 1.5


@dataclass
class PunchResult:
    """Result of the punching verification for one column."""

    v_ed: float                    # design stress [MPa]
    v_rdc: float                   # resistance without reinf. [MPa]
    v_rd_min: float                # minimum resistance [MPa]
    v_rd_max: float                # maximum resistance [MPa]
    beta: float                    # eccentricity factor used
    u1: float                      # control perimeter [m]
    u_out_eff: float | None        # outer perimeter [m] (:2023) or None
    utilization: float
    needs_reinf: bool
    crushing: bool
    edition: str
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 punching ({self.edition}) — util {self.utilization:.3f}"
                + (" | needs reinf." if self.needs_reinf else "")
                + (" | CRUSHING" if self.crushing else ""))


def eurocode2_punching_check(inp: PunchInput, n_ed: float,
                             m_ed_x: float = 0.0, m_ed_y: float = 0.0,
                             rho_l: float = 0.005, beta_min: float = 1.0,
                             trace=None) -> PunchResult:
    """Punching check of one column (EN 1992-1-1 §6.4 / EN :2023 §8.4).

    Args:
        inp: The column / slab data (and the EC2 edition).
        n_ed: Punching force ``V_Ed`` [kN] (its magnitude is used).
        m_ed_x, m_ed_y: Transferred moments [kNm].
        rho_l: Longitudinal reinforcement ratio at the column (already resolved).
        beta_min: Floor on the eccentricity factor ``β`` (EC2 §6.4.3(6)).
        trace: Optional :class:`eurocodepy.calc_report.CalcReport`; recording
            only — ``None`` leaves the result identical.

    Returns:
        A :class:`PunchResult`.

    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    is_2023 = str(inp.edition) == "2023"
    if is_2023:
        from eurocodepy.ec2 import uls2023 as _p
    else:
        from eurocodepy.ec2 import uls as _p

    dv = inp.d * _MM
    bx = inp.bx * _MM
    by = None if inp.by is None else inp.by * _MM
    dx, dy = inp.dx * _MM, inp.dy * _MM
    fyd = inp.fyk / inp.gamma_s
    ned = abs(n_ed)
    medx, medy = abs(m_ed_x), abs(m_ed_y)

    u0, u1, _bb = _p.calc_perimeters(dv, bx, by, position=inp.position,
                                     dx=dx, dy=dy)
    v_ed = float(_p.calc_vedp(ned, medx, medy, dv, bx, by,
                              position=inp.position, dx=dx, dy=dy))
    # Floor β at the user minimum (§6.4.3(6)).
    v0 = ned / u1 / dv * 1e3                    # v_Ed without β [MPa]
    beta = v_ed / v0 if v0 > 0 else 1.0
    beta_eff = max(beta, beta_min or 1.0)
    v_ed = beta_eff * v0

    _sec("Inputs")
    _t("V_Ed", ned, "kN")
    _t("M_Ed,x", medx, "kNm")
    _t("M_Ed,y", medy, "kNm")
    _t("d", inp.d, "m")
    _t("ρ_l", rho_l, "—")
    _t("Edition", "EN 1992-1-1:2023" if is_2023 else "EN 1992-1-1:2004", "—")
    _sec("Control perimeters (§6.4.2)")
    _t("u0", u0 / _MM, "m", clause="EN 1992-1-1 §6.4.2",
       note="at the loaded-area face")
    _t("u1", u1 / _MM, "m", clause="EN 1992-1-1 §6.4.2",
       note="control perimeter (2·d for :2004, 0.5·d for :2023)")
    _sec("Design punching stress (§6.4.3)")
    _t("β", beta_eff, "—", clause="EN 1992-1-1 §6.4.3",
       expr="β = v_Ed(with moment) / v_Ed(N only), floored at β_min",
       subst=f"max({beta:.3g}, {beta_min or 1.0:g})",
       note=f"β_min = {beta_min:g}")
    _t("v_Ed", v_ed, "MPa", clause="EN 1992-1-1 §6.4.3",
       expr="v_Ed = β·V_Ed/(u1·d)",
       subst=f"{beta_eff:.3g}·{ned:.4g}/({u1/_MM:.4g}·{dv/_MM:.4g})·1e3")

    if is_2023:
        v_rdc = float(_p.calc_vrdcp(inp.dmax, rho_l, inp.fck, dv, bx, by,
                                    gamma_v=inp.gamma_v, position=inp.position,
                                    dx=dx, dy=dy))
        v_rd_min = float(_p.calc_vrdcminp(inp.fck, fyd, dv, dmax=inp.dmax,
                                          gamma_v=inp.gamma_v))
        v_rd_max = inp.eta_sys * v_rdc
        v_ed_max = v_ed
        needs0 = v_ed > max(v_rdc, v_rd_min)
        u_out_eff = (beta_eff * ned * 1e3 / (v_rdc * dv) / _MM
                     if (needs0 and v_rdc > 0) else None)
        _sec("Resistance (EN 1992-1-1:2023 §8.4)")
        _t("v_Rd,c", v_rdc, "MPa", clause="EN 1992-1-1:2023 §8.4.3",
           subst=f"d_max={inp.dmax:g}, ρ_l={rho_l:.4g}, f_ck={inp.fck:g}, d={dv:.4g} mm")
        _t("v_Rd,min", v_rd_min, "MPa", clause="EN 1992-1-1:2023 §8.4.3",
           subst=f"f_ck={inp.fck:g}, f_yd={fyd:.4g}, d={dv:.4g} mm, d_max={inp.dmax:g}")
        _t("v_Rd,max", v_rd_max, "MPa", clause="EN 1992-1-1:2023 §8.4.4",
           expr="v_Rd,max = η_sys·v_Rd,c",
           subst=f"{inp.eta_sys:g}·{v_rdc:.4g}", note=f"η_sys = {inp.eta_sys:g}")
    else:
        v_rdc = float(_p.calc_vrdcp(rho_l, inp.fck, dv, gamma_c=inp.gamma_c))
        v_rd_min = float(_p.calc_vrdcminp(inp.fck, dv))
        nu = 0.6 * (1.0 - inp.fck / 250.0)
        fcd = inp.alpha_cc * inp.fck / inp.gamma_c
        v_rd_max = 0.5 * nu * fcd
        v_ed_max = beta_eff * ned / u0 / dv * 1e3
        u_out_eff = None
        _sec("Resistance (EN 1992-1-1:2004 §6.4.4/§6.4.5)")
        _t("v_Rd,c", v_rdc, "MPa", clause="EN 1992-1-1 §6.4.4",
           expr="v_Rd,c = C_Rd,c·k·(100·ρ_l·f_ck)^(1/3) ≥ v_min",
           subst=f"ρ_l={rho_l:.4g}, f_ck={inp.fck:g}, d={dv:.4g} mm, γ_c={inp.gamma_c:g}")
        _t("v_Rd,min", v_rd_min, "MPa", clause="EN 1992-1-1 §6.4.4",
           subst=f"f_ck={inp.fck:g}, d={dv:.4g} mm")
        _t("v_Rd,max", v_rd_max, "MPa", clause="EN 1992-1-1 §6.4.5(3)",
           expr="v_Rd,max = 0.5·ν·f_cd  (at u0)",
           subst=f"0.5·{nu:.3g}·{fcd:.4g}")

    v_rd = max(v_rdc, v_rd_min)
    util = v_ed / v_rd if v_rd > 0 else float("inf")
    needs = bool(v_ed > v_rd)
    crushing = bool(v_ed_max > v_rd_max)

    _sec("Verdict")
    _t("Utilisation", util, "—",
       clause=("EN 1992-1-1:2023 §8.4" if is_2023 else "EN 1992-1-1 §6.4"),
       expr="v_Ed / max(v_Rd,c, v_Rd,min)",
       subst=f"{v_ed:.4g}/max({v_rdc:.4g}, {v_rd_min:.4g})", ok=not needs)
    _t("Needs reinforcement", needs, "—", ok=not needs)
    _t("Crushing", crushing, "—", ok=not crushing,
       note="v_Ed(max) > v_Rd,max")
    if u_out_eff is not None:
        _t("u_out,ef", u_out_eff, "m", clause="EN 1992-1-1:2023 §8.4.5",
           expr="u_out,ef = β·V_Ed/(v_Rd,c·d)",
           subst=f"{beta_eff:.3g}·{ned:.4g}·1e3/({v_rdc:.4g}·{dv:.4g})/{_MM:g}",
           note="beyond this perimeter no punching reinforcement is needed")

    return PunchResult(
        v_ed=float(v_ed), v_rdc=float(v_rdc), v_rd_min=float(v_rd_min),
        v_rd_max=float(v_rd_max), beta=float(beta_eff), u1=float(u1 / _MM),
        u_out_eff=(float(u_out_eff) if u_out_eff is not None else None),
        utilization=float(util), needs_reinf=needs, crushing=crushing,
        edition="2023" if is_2023 else "2004",
        details={"u0": float(u0 / _MM), "v_ed_max": float(v_ed_max),
                 "rho_l": float(rho_l)})
