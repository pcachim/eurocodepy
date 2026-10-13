# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Design of membrane-, shell- and slab elements — **EN 1992-1-1:2023 Annex G**.

* G.3 membrane elements: optimum reinforcement (Table G.1), the resistances for a
  chosen strut inclination (Eqs. G.3-G.5), the deformation-capacity limits
  (Eqs. G.6-G.7) and the strength-reduction factor ``ν`` (Eqs. G.8-G.11);
* G.4 shell and slab elements: the sandwich model (Eqs. G.12-G.17), the slab
  formulae (Eqs. G.18-G.21) and the optimum reinforcement of Tables G.2 and G.3;
* G.5 refined crack control of membrane elements (Eqs. G.22-G.27).

Sign convention: stresses and strains positive in **tension** (compression
negative); in slabs sagging moments are positive (bottom tension) and hogging
moments negative. The membrane functions are linear in the force unit, so they
work with stresses [MPa] or with forces per unit length [kN/m] alike; ``ν`` and
the strains are dimensionless. The 2004 equivalent of G.3 is
:func:`eurocodepy.ec2.uls.shell.calc_reinf_plane` (Annex F).
"""

import math

import numpy as np

_TOL = 1.0e-12
_NU_SIMPLE = 0.4                  # G.8
_RANGE = (0.4, 2.5)               # G.6, G.7, G.18-G.21
_SLAB_TORSION_LIMIT = 0.07        # G.4(5): |mEdxy| < 0,07·d²·fcd
_CRACK_ANGLE = (15.0, 75.0)       # G.5(1)


# ── G.3 Membrane elements ───────────────────────────────────────────────────

def membrane_needs_reinforcement(s_x: float, s_y: float, tau_xy: float) -> bool:
    """Return ``False`` if both stresses are compressive and ``σx·σy > τ²``, G.3(1).

    There the reinforcement is not required; the principal compressive stress
    must not exceed ``fcd``.
    """
    return not (s_x < 0.0 and s_y < 0.0 and s_x * s_y > tau_xy**2)


def membrane_optimum(s_x: float, s_y: float, tau_xy: float) -> dict:
    """Return the optimum reinforcement of a membrane element, Table G.1.

    Returns ``cot`` (``cot θ*``, ``math.inf`` for ``τ = 0`` with compression),
    ``ftdx``, ``ftdy`` (``ftdx*``, ``ftdy*``), ``sigma_cd`` (``σcd*``, in the
    unreinforced case the principal compressive stress) and ``case``
    (``"tension"``, ``"x_compression"``, ``"y_compression"`` or
    ``"no_reinforcement"``). In the last case ``cot`` is ``None``.
    """
    t = abs(tau_xy)
    t2 = tau_xy**2
    if s_x >= -t and s_y >= -t:
        return {"cot": 1.0, "ftdx": s_x + t, "ftdy": s_y + t,
                "sigma_cd": 2.0 * t, "case": "tension"}
    if s_x < -t and s_x <= s_y and s_x * s_y <= t2:
        cot = math.inf if t < _TOL else -s_x / t
        return {"cot": cot, "ftdx": 0.0, "ftdy": s_y + t2 / abs(s_x),
                "sigma_cd": abs(s_x) * (1.0 + (tau_xy / s_x) ** 2),
                "case": "x_compression"}
    if s_y < -t and s_x >= s_y and s_x * s_y <= t2:
        cot = 0.0 if t < _TOL else t / -s_y
        return {"cot": cot, "ftdx": s_x + t2 / abs(s_y), "ftdy": 0.0,
                "sigma_cd": abs(s_y) * (1.0 + (tau_xy / s_y) ** 2),
                "case": "y_compression"}
    centre = 0.5 * (s_x + s_y)
    radius = math.sqrt(t2 + 0.25 * (s_x - s_y) ** 2)
    return {"cot": None, "ftdx": 0.0, "ftdy": 0.0,
            "sigma_cd": abs(centre - radius), "case": "no_reinforcement"}


def membrane_resistances(s_x: float, s_y: float, tau_xy: float, cot: float) -> dict:
    """Return the tensile strengths needed for a chosen ``cot θ``, Eqs. (G.3)-(G.5).

    ``ftdx = σx + |τ|·cot θ``, ``ftdy = σy + |τ|/cot θ`` and
    ``σcd = |τ|·(cot θ + tan θ)``. ``valid`` is ``False`` if one of the strengths
    is negative (``cot θ`` must be chosen to avoid that).
    """
    t = abs(tau_xy)
    ftdx = s_x + t * cot
    ftdy = s_y + t / cot
    return {"ftdx": ftdx, "ftdy": ftdy, "sigma_cd": t * (cot + 1.0 / cot),
            "valid": ftdx >= -_TOL and ftdy >= -_TOL}


def _within(value: float, optimum: float) -> bool:
    if optimum <= _TOL:
        return value <= _TOL
    return _RANGE[0] * optimum - _TOL <= value <= _RANGE[1] * optimum + _TOL


def deformation_capacity_ok(ftdx: float, ftdy: float, s_x: float, s_y: float,
                            tau_xy: float) -> bool:
    """Return ``True`` if ``0,4·ft* ≤ ft ≤ 2,5·ft*`` in both directions, Eqs. (G.6)-(G.7)."""
    opt = membrane_optimum(s_x, s_y, tau_xy)
    return _within(ftdx, opt["ftdx"]) and _within(ftdy, opt["ftdy"])


def calc_nu_simple() -> float:
    """Return ``ν = 0,4``, Eq. (G.8)."""
    return _NU_SIMPLE


def calc_nu(eps_1: float) -> float:
    """Return ``ν = 1/(1 + 110·ε1) ≤ 1,0``, Eq. (G.9)."""
    return min(1.0 / (1.0 + 110.0 * eps_1), 1.0)


def calc_eps1_from_x(eps_x: float, cot: float) -> float:
    """Return ``ε1 = εx + (εx + 0,001)·cot²θ``, Eq. (G.10)."""
    return eps_x + (eps_x + 0.001) * cot**2


def calc_eps1_from_y(eps_y: float, cot: float) -> float:
    """Return ``ε1 = εy + (εy + 0,001)/cot²θ``, Eq. (G.11)."""
    return eps_y + (eps_y + 0.001) / cot**2


def estimate_eps1(ftdx: float, ftdy: float, cot: float, f_yd: float, e_s: float,
                  lam: float = 1.0, f_ctd: float | None = None,
                  e_cd: float | None = None, *, uncracked: bool = False) -> float:
    """Estimate the principal strain ``ε1`` of G.3(7) for a known ``cot θ``.

    ``ε`` of the reinforcement is taken as ``fyd/(λ·Es)`` (``λ`` = provided/required
    reinforcement, 1,0 if exactly the required): only direction x required
    (``ftdy = 0``): Eq. (G.10); only y required: Eq. (G.11); both required: the
    larger of the two. With ``uncracked=True`` and both strengths below ``f_ctd``,
    ``ε1 = fctd/Ecd`` (c).
    """
    if uncracked and f_ctd is not None and e_cd is not None \
            and ftdx < f_ctd and ftdy < f_ctd:
        return f_ctd / e_cd
    eps = f_yd / (lam * e_s)
    need_x, need_y = ftdx > _TOL, ftdy > _TOL
    if not need_x and not need_y:
        msg = "no reinforcement is required: ε1 is not needed (use fcd, G.3(1))"
        raise ValueError(msg)
    if need_x and not need_y:
        return calc_eps1_from_x(eps, cot)
    if need_y and not need_x:
        return calc_eps1_from_y(eps, cot)
    return max(calc_eps1_from_x(eps, cot), calc_eps1_from_y(eps, cot))


def estimate_nu(ftdx: float, ftdy: float, cot: float, f_yd: float, e_s: float,
                lam: float = 1.0) -> float:
    """Return ``ν`` of Eq. (G.9) with ``ε1`` from :func:`estimate_eps1`."""
    return calc_nu(estimate_eps1(ftdx, ftdy, cot, f_yd, e_s, lam))


# ── G.4 Shell and slab elements ─────────────────────────────────────────────

def sandwich_stresses(n: tuple[float, float, float], m: tuple[float, float, float],
                      t: float, z: float) -> dict:
    """Return the in-plane stresses of the bottom and top layers, Eqs. (G.12)-(G.17).

    ``n = (nEdx, nEdy, nEdxy)`` [force/length], ``m = (mEdx, mEdy, mEdxy)``
    [moment/length], ``t`` the thickness of each layer and ``z`` the lever arm
    between them (same length unit). Returns ``{"bottom": (σx, σy, τ),
    "top": (σ'x, σ'y, τ')}``.
    """
    nx, ny, nxy = n
    mx, my, mxy = m
    tz = t * z
    bottom = (0.5 * nx / t + mx / tz, 0.5 * ny / t + my / tz, 0.5 * nxy / t - mxy / tz)
    top = (0.5 * nx / t - mx / tz, 0.5 * ny / t - my / tz, 0.5 * nxy / t + mxy / tz)
    return {"bottom": bottom, "top": top}


def shell_design(n: tuple[float, float, float], m: tuple[float, float, float],
                 t: float, z: float) -> dict:
    """Design the two layers of a shell element with the sandwich model, G.4(1)-(2).

    Applies :func:`membrane_optimum` to each layer of :func:`sandwich_stresses`;
    ``ftdx``/``ftdy`` of the result are tensile strengths per unit of layer
    thickness (multiply by ``t`` for the force per unit length). Returns
    ``{"bottom": ..., "top": ...}`` with the dicts of :func:`membrane_optimum`
    plus the layer ``stresses``.
    """
    layers = sandwich_stresses(n, m, t, z)
    out = {}
    for name, (sx, sy, txy) in layers.items():
        d = membrane_optimum(sx, sy, txy)
        d["stresses"] = (sx, sy, txy)
        out[name] = d
    return out


def slab_torsion_simplified_ok(m_edxy: float, d: float, f_cd: float) -> bool:
    """Return ``True`` if ``|mEdxy| < 0,07·d²·fcd`` (G.4(5), 8.1.3(1)).

    ``m_edxy`` [kNm/m], ``d`` [m], ``f_cd`` [MPa].
    """
    return abs(m_edxy) < _SLAB_TORSION_LIMIT * d**2 * f_cd * 1000.0


def slab_optimum_bottom(m_x: float, m_y: float, m_xy: float) -> dict:
    """Return the required bottom-layer capacities ``mRdx``, ``mRdy``, Table G.2.

    Sagging moments positive. ``case``: ``1`` (``mx + |mxy|``, ``my + |mxy|``),
    ``2`` (``mRdx = 0``), ``3`` (``mRdy = 0``) or ``4`` (no reinforcement).
    """
    a = abs(m_xy)
    if m_x >= -a and m_y >= -a:
        return {"m_rdx": m_x + a, "m_rdy": m_y + a, "case": 1}
    if m_x < 0.0 and m_y < 0.0 and m_x * m_y > m_xy**2:
        return {"m_rdx": 0.0, "m_rdy": 0.0, "case": 4}
    if m_x <= m_y:                               # m_x < -|mxy|
        return {"m_rdx": 0.0, "m_rdy": m_y + m_xy**2 / abs(m_x), "case": 2}
    return {"m_rdx": m_x + m_xy**2 / abs(m_y), "m_rdy": 0.0, "case": 3}


def slab_optimum_top(m_x: float, m_y: float, m_xy: float) -> dict:
    """Return the required top-layer capacities ``m'Rdx``, ``m'Rdy``, Table G.3.

    The table is Table G.2 for the mirrored moments (``-mx``, ``-my``).
    """
    return slab_optimum_bottom(-m_x, -m_y, m_xy)


def slab_required_moments(m_x: float, m_y: float, m_xy: float,
                          cot_bot: float = 1.0, cot_top: float = 1.0) -> dict:
    """Return the capacities of Eqs. (G.18)-(G.21) for chosen ``cot θ`` of the layers.

    ``mRdx = mx + cot θbot·|mxy|``, ``mRdy = my + |mxy|/cot θbot``,
    ``m'Rdx = −mx + cot θtop·|mxy|``, ``m'Rdy = −my + |mxy|/cot θtop`` (valid for
    ``nEd = 0``), clipped at 0. ``within_range`` is ``True`` where the value is
    between 0,4 and 2,5 times the optimum of Tables G.2/G.3.
    """
    a = abs(m_xy)
    raw = {"m_rdx": m_x + cot_bot * a, "m_rdy": m_y + a / cot_bot,
           "m_rdx_top": -m_x + cot_top * a, "m_rdy_top": -m_y + a / cot_top}
    bot, top = slab_optimum_bottom(m_x, m_y, m_xy), slab_optimum_top(m_x, m_y, m_xy)
    opt = {"m_rdx": bot["m_rdx"], "m_rdy": bot["m_rdy"],
           "m_rdx_top": top["m_rdx"], "m_rdy_top": top["m_rdy"]}
    out = {k: max(v, 0.0) for k, v in raw.items()}
    out["within_range"] = {k: _within(out[k], opt[k]) for k in raw}
    out["optimum"] = opt
    return out


# ── G.5 Refined crack control of membrane elements ──────────────────────────

def crack_inclination_applies(theta_deg: float) -> bool:
    """Return ``True`` if ``15° < θ < 75°``, where G.5 applies (G.5(1))."""
    return _CRACK_ANGLE[0] < theta_deg < _CRACK_ANGLE[1]


def calc_sr_m_cal(theta: float, sr_m_cal_x: float, sr_m_cal_y: float) -> float:
    """Return the mean spacing of inclined cracks ``sr,m,cal``, Eq. (G.22).

    ``1/(sin θ/sr,m,cal,x + cos θ/sr,m,cal,y)``; ``theta`` in radians.
    """
    return 1.0 / (math.sin(theta) / sr_m_cal_x + math.cos(theta) / sr_m_cal_y)


def _eps_diff(sigma_s: float, k_t: float, sr_ratio: float, f_ct_eff: float,
              rho_p_eff: float, alpha_e: float, e_s: float) -> float:
    a = (sigma_s - k_t * sr_ratio * f_ct_eff / rho_p_eff * (1.0 + alpha_e * rho_p_eff)) / e_s
    return max(a, (1.0 - k_t) * sigma_s / e_s)


def calc_eps_diff_x(sigma_sx: float, k_t: float, sr_m_cal: float, sr_m_cal_x: float,
                    theta: float, f_ct_eff: float, rho_px_eff: float,
                    alpha_e: float, e_s: float) -> float:
    """Return ``εsmx − εcmx`` of Eq. (G.24); ``theta`` in radians, stresses in MPa."""
    ratio = sr_m_cal / (sr_m_cal_x * math.sin(theta))
    return _eps_diff(sigma_sx, k_t, ratio, f_ct_eff, rho_px_eff, alpha_e, e_s)


def calc_eps_diff_y(sigma_sy: float, k_t: float, sr_m_cal: float, sr_m_cal_y: float,
                    theta: float, f_ct_eff: float, rho_py_eff: float,
                    alpha_e: float, e_s: float) -> float:
    """Return ``εsmy − εcmy`` of Eq. (G.25); ``theta`` in radians, stresses in MPa."""
    ratio = sr_m_cal / (sr_m_cal_y * math.cos(theta))
    return _eps_diff(sigma_sy, k_t, ratio, f_ct_eff, rho_py_eff, alpha_e, e_s)


def calc_eps_2(tau_xy: float, theta: float, e_cm: float) -> float:
    """Return ``|ε2| = |τEdxy|·(cot θ + tan θ)/Ecm``, Eq. (G.26)."""
    return abs(tau_xy) * (1.0 / math.tan(theta) + math.tan(theta)) / e_cm


def calc_eps_sm_cm(eps_diff_x: float, eps_diff_y: float, eps_2: float) -> float:
    """Return ``εsm − εcm = (εsmx − εcmx) + (εsmy − εcmy) + |ε2|``, Eq. (G.23)."""
    return eps_diff_x + eps_diff_y + abs(eps_2)


def calc_cot_theta_cracking(s_x: float, s_y: float, tau_xy: float,
                            rho_x: float, rho_y: float) -> float:
    """Return the positive root of Eq. (G.27) for ``cot θ``.

    ``|τ|/ρx·cot⁴θ + σx/ρx·cot³θ − σy/ρy·cot θ − |τ|/ρy = 0`` with the stresses at the
    point (tension positive) and the reinforcement ratios ``ρx``, ``ρy`` of G.3(2).
    If there is more than one positive real root the largest is returned;
    ``ValueError`` if there is none.
    """
    t = abs(tau_xy)
    roots = np.roots([t / rho_x, s_x / rho_x, 0.0, -s_y / rho_y, -t / rho_y])
    real = [r.real for r in roots if abs(r.imag) < 1e-9 and r.real > 0.0]
    if not real:
        msg = "Eq. (G.27) has no positive real root for these stresses"
        raise ValueError(msg)
    return max(real)
