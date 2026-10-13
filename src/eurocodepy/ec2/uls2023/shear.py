# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Shear — **EN 1992-1-1:2023** Clause 8.2 (the new EC2 generation).

The formulae of 8.2.1 (general procedure), 8.2.2 (members without shear
reinforcement), 8.2.3 (members with shear reinforcement, compression field),
8.2.4 (in-plane shear and transverse bending), 8.2.5 (web-flange shear) and
8.2.6 (shear at interfaces). The EC2:2004 counterpart is
:mod:`eurocodepy.ec2.uls.shear`; the verification procedure that combines the
formulae is :mod:`eurocodepy.ec2.uls2023.shear_check`.

Units: lengths and areas in **m** / **m²** (aggregate parameters ``d_lower`` and
``d_dg`` in **mm**), strengths and stresses in **MPa**, forces in **kN**,
moments in **kNm**, ``Asw/s`` in **m²/m**, angles of the compression field as
``cot θ``. Axial forces ``n_ed`` are positive in **tension** (EN 1992-1-1:2023
3.10). ``gamma_v`` is the partial factor of Table 4.3 (see
:func:`eurocodepy.ec2.material_partial_factors`).

Not covered: the minimum shear reinforcement (Clause 12, ``ρw,min``) and the
reductions of 8.2.2(8)-(11); the caller passes the minimum reinforcement.
"""

import math

from eurocodepy import dbase

NU_DEFAULT = 0.5          # 8.2.3(6)
_MM = 1000.0
_MIN_RATIO = 0.5          # v_Ed,y/v_Ed,x limits of 8.2.1(5) and 8.2.2(7)
_MAX_RATIO = 2.0
_MAX_DDG = 40.0           # mm, 8.2.1(4)
_MIN_ALPHA_W = 45.0       # 8.2.3(13)
_MAX_ALPHA_W = 90.0
_MIN_ALPHA_I = 35.0       # 8.2.6(5)
_MAX_ALPHA_I = 135.0
_DUCT_RATIO = 8.0         # 8.2.3(10)


# ── 8.2.1 General verification procedure ────────────────────────────────────

def calc_lever_arm(d: float) -> float:
    """Return the lever arm for the shear calculation ``z = 0,9·d`` [m] (8.2.1(3))."""
    return 0.9 * d


def calc_tau_ed(v_ed: float, b_w: float, z: float) -> float:
    """Return the average shear stress ``τEd = VEd/(bw·z)`` [MPa], Eq. (8.18).

    For planar members pass ``b_w = 1`` and ``v_ed`` per unit width, Eq. (8.19).
    """
    return abs(v_ed) / (b_w * z) / 1000.0


def calc_ddg(fck: float, d_lower: float = 20.0) -> float:
    """Return the failure-zone roughness parameter ``ddg`` [mm], 8.2.1(4).

    ``16 + D_lower·min(1, (60/fck)²) ≤ 40 mm``; ``d_lower`` [mm] is the smallest
    upper sieve size of the coarsest aggregate fraction (``D_max`` if unknown).
    """
    return min(16.0 + d_lower * min(1.0, (60.0 / fck) ** 2), _MAX_DDG)


def calc_taurdc_min(fck: float, fyd: float, d: float, d_lower: float = 20.0,
                    gamma_v: float = 1.4) -> float:
    """Return ``τRdc,min`` [MPa], Eq. (8.20).

    ``fyd`` [MPa] is the yield strength used for the flexural reinforcement
    (``fpd − σpm,∞`` for prestressed members without ordinary reinforcement).
    """
    ddg = calc_ddg(fck, d_lower)
    return 11.0 / gamma_v * math.sqrt(fck / fyd * ddg / (d * _MM))


def planar_shear_force(v_ed_x: float, v_ed_y: float) -> float:
    """Return the design shear force per unit width ``vEd`` [kN/m], Eq. (8.21)."""
    return math.hypot(v_ed_x, v_ed_y)


def _planar_ratio(v_ed_x: float, v_ed_y: float) -> float:
    return math.inf if v_ed_x == 0.0 else abs(v_ed_y / v_ed_x)


def planar_effective_depth(v_ed_x: float, v_ed_y: float, d_x: float, d_y: float,
                           *, smooth: bool = False) -> float:
    """Return the effective depth of a planar member [m], Eqs. (8.22)-(8.26).

    ``smooth=False`` uses the steps (8.22)-(8.24) by the ratio ``vEd,y/vEd,x``;
    ``smooth=True`` the alternative ``d = dx·cos²αv + dy·sin²αv`` (8.25).
    """
    if smooth:
        a_v = math.atan2(abs(v_ed_y), abs(v_ed_x))
        return d_x * math.cos(a_v) ** 2 + d_y * math.sin(a_v) ** 2
    r = _planar_ratio(v_ed_x, v_ed_y)
    if r <= _MIN_RATIO:
        return d_x
    if r >= _MAX_RATIO:
        return d_y
    return 0.5 * (d_x + d_y)


def planar_rho_l(v_ed_x: float, v_ed_y: float, rho_x: float, rho_y: float) -> float:
    """Return ``ρl`` of a planar member with different ratios, Eqs. (8.38)-(8.40)."""
    r = _planar_ratio(v_ed_x, v_ed_y)
    if r <= _MIN_RATIO:
        return rho_x
    if r >= _MAX_RATIO:
        return rho_y
    a_v = math.atan2(abs(v_ed_y), abs(v_ed_x))
    return rho_x * math.cos(a_v) ** 4 + rho_y * math.sin(a_v) ** 4


# ── 8.2.2 Members without shear reinforcement ───────────────────────────────

def calc_taurdc(rho_l: float, fck: float, d: float, fyd: float,
                d_lower: float = 20.0, gamma_v: float = 1.4,
                d_shear: float | None = None) -> float:
    """Return ``τRd,c`` [MPa], Eq. (8.27): ``0,66/γv·(100·ρl·fck·ddg/d)^(1/3) ≥ τRdc,min``.

    ``d_shear`` replaces ``d`` in the bracket (``av`` of Eq. (8.29), times
    ``kvp`` of Eq. (8.31) when there is an axial force); ``τRdc,min`` always
    uses ``d``.
    """
    ddg = calc_ddg(fck, d_lower)
    dd = d if d_shear is None else d_shear
    t = 0.66 / gamma_v * (100.0 * rho_l * fck * ddg / (dd * _MM)) ** (1.0 / 3.0)
    return max(t, calc_taurdc_min(fck, fyd, d, d_lower, gamma_v))


def calc_acs(m_ed: float, v_ed: float, d: float) -> float:
    """Return the effective shear span ``acs = |MEd/VEd| ≥ d`` [m], Eq. (8.30)."""
    return d if v_ed == 0.0 else max(abs(m_ed / v_ed), d)


def calc_av(a_cs: float, d: float) -> float:
    """Return the mechanical shear span ``av = √(acs·d/4)`` [m], Eq. (8.29).

    Applies for ``acs < 4d`` (``av = d`` at ``acs = 4d``); otherwise ``d`` is returned.
    """
    return math.sqrt(a_cs * d / 4.0) if a_cs < 4.0 * d else d


def calc_kvp(n_ed: float, v_ed: float, d: float, a_cs: float) -> float:
    """Return ``kvp = 1 + NEd/|VEd|·d/(3·acs) ≥ 0,1``, Eq. (8.31).

    ``n_ed`` is positive in tension; compression (``n_ed < 0``) reduces ``kvp``
    and so increases the resistance.
    """
    return max(1.0 + n_ed / abs(v_ed) * d / (3.0 * a_cs), 0.1)


def calc_k1(e_p: float, d: float, a_cs0: float, a_c: float, b_w: float,
            z: float) -> float:
    """Return ``k1`` of Eq. (8.34): ``0,5/acs,0·(ep + d/3)·Ac/(bw·z) ≤ 0,18·Ac/(bw·z)``."""
    base = a_c / (b_w * z)
    return min(0.5 / a_cs0 * (e_p + d / 3.0) * base, 0.18 * base)


def calc_taurdc_axial(rho_l: float, fck: float, d: float, fyd: float,
                      n_ed: float, a_c: float, b_w: float, e_p: float,
                      a_cs0: float, d_lower: float = 20.0, gamma_v: float = 1.4,
                      d_shear: float | None = None) -> dict:
    """Return ``τRd,c`` with the effect of an axial force/prestress, Eqs. (8.32)-(8.35).

    ``n_ed`` [kN] positive in tension (compression ``σcp = n_ed/Ac < 0`` raises
    the resistance); ``e_p`` [m] is the eccentricity of the force, positive
    towards the tension side; ``a_cs0`` [m] is Eq. (8.30) without the effect of
    the axial force. ``d_shear`` replaces ``d`` in ``τRdc,0`` (``av,0``).

    Returns a dict with ``tau_rdc``, ``tau_rdc0``, ``tau_rdc_min``,
    ``tau_rdc_max``, ``k1`` and ``sigma_cp`` (MPa).
    """
    z = calc_lever_arm(d)
    ddg = calc_ddg(fck, d_lower)
    dd = d if d_shear is None else d_shear
    t0 = 0.66 / gamma_v * (100.0 * rho_l * fck * ddg / (dd * _MM)) ** (1.0 / 3.0)
    t_min = calc_taurdc_min(fck, fyd, d, d_lower, gamma_v)
    t_max = min(2.15 * t0 * (a_cs0 / d) ** (1.0 / 6.0), 2.7 * t0)
    k1 = calc_k1(e_p, d, a_cs0, a_c, b_w, z)
    sigma_cp = n_ed / a_c / 1000.0
    t = min(max(t0 - k1 * sigma_cp, t_min), t_max)
    return {"tau_rdc": t, "tau_rdc0": t0, "tau_rdc_min": t_min,
            "tau_rdc_max": t_max, "k1": k1, "sigma_cp": sigma_cp}


def calc_d_prestressed(d_s: float, a_s: float, d_p: float, a_p: float) -> float:
    """Return ``d`` of a member with bonded tendons [m], Eq. (8.36)."""
    return (d_s**2 * a_s + d_p**2 * a_p) / (d_s * a_s + d_p * a_p)


def calc_rho_l_prestressed(d_s: float, a_s: float, d_p: float, a_p: float,
                           b_w: float, d: float) -> float:
    """Return ``ρl`` of a member with bonded tendons, Eq. (8.37)."""
    return (d_s * a_s + d_p * a_p) / (b_w * d**2)


# ── 8.2.3 Members with shear reinforcement ──────────────────────────────────

def calc_cot_theta_min(n_ed: float = 0.0, v_ed: float = 0.0, ductility: str = "B",
                       *, significant_compression: bool = False) -> float:
    """Return the upper limit ``cot θmin`` of Eq. (8.41), 8.2.3(4).

    2,5 for ordinary members; 3,0 with ``significant_compression`` (average axial
    compressive stress ≥ 3 MPa and compression chord ``x ≤ 0,25·d``);
    ``2,5 − 0,1·NEd/|VEd| ≥ 1,0`` in tension (``n_ed > 0``). Ductility class A
    reinforcement reduces it by 20 %.
    """
    if n_ed > 0.0:
        c = 1.0 if v_ed == 0.0 else max(2.5 - 0.1 * n_ed / abs(v_ed), 1.0)
    elif significant_compression:
        c = 3.0
    else:
        c = 2.5
    return 0.8 * c if ductility.upper() == "A" else c


def calc_rho_w(a_sw: float, b_w: float, s: float) -> float:
    """Return the shear reinforcement ratio ``ρw = Asw/(bw·s)``, Eq. (8.43)."""
    return a_sw / (b_w * s)


def calc_tau_rd_sy(rho_w: float, f_ywd: float, cot: float,
                   alpha_w: float = 90.0) -> float:
    """Return ``τRd,sy`` [MPa] for yielding of the shear reinforcement.

    ``ρw·fywd·cot θ`` (8.42); inclined reinforcement (``alpha_w`` in degrees,
    ``45° ≤ αw < 90°``): ``ρw·fywd·(cot θ + cot αw)·sin αw`` (8.59).
    """
    a = _check_alpha_w(alpha_w)
    return rho_w * f_ywd * (cot + _cot(a)) * math.sin(a)


def calc_sigma_cd(tau_ed: float, cot: float, alpha_w: float = 90.0) -> float:
    """Return the compression-field stress ``σcd`` [MPa], Eq. (8.44) / (8.60).

    ``τEd·(cot θ + tan θ)``; inclined: ``τEd·(1 + cot²θ)/(cot θ + cot αw)``.
    """
    a = _check_alpha_w(alpha_w)
    return tau_ed * (1.0 + cot**2) / (cot + _cot(a))


def calc_tau_rd(rho_w: float, f_ywd: float, nu: float, f_cd: float, cot: float,
                alpha_w: float = 90.0) -> float:
    """Return ``τRd`` [MPa]: the lesser of ``τRd,sy`` and ``ν·fcd·(cot θ + cot αw)/(1 + cot²θ)``."""
    a = _check_alpha_w(alpha_w)
    return min(calc_tau_rd_sy(rho_w, f_ywd, cot, alpha_w),
               nu * f_cd * (cot + _cot(a)) / (1.0 + cot**2))


def calc_cot_theta_opt(rho_w: float, f_ywd: float, nu: float, f_cd: float,
                       cot_min: float) -> float:
    """Return ``cot θ`` of simultaneous yielding and crushing, 8.2.3(5) NOTE.

    ``√(ν·fcd/(ρw·fywd) − 1)`` limited to ``1 ≤ cot θ ≤ cot θmin`` (vertical
    shear reinforcement).
    """
    r = nu * f_cd / (rho_w * f_ywd) - 1.0
    c = math.sqrt(r) if r > 0.0 else 1.0
    return min(max(c, 1.0), cot_min)


def calc_cot_theta_crush(tau_ed: float, nu: float, f_cd: float,
                         alpha_w: float = 90.0) -> float | None:
    """Return the largest ``cot θ`` that satisfies ``σcd ≤ ν·fcd``, or ``None``.

    Vertical shear reinforcement: solves ``τEd·(c + 1/c) = ν·fcd``,
    ``c = (r + √(r² − 4))/2`` with ``r = ν·fcd/τEd``; ``None`` when the
    compression field crushes even at ``cot θ = 1``. For inclined
    reinforcement the equation (8.60) is solved numerically.
    """
    if tau_ed <= 0.0:
        return math.inf
    if _check_alpha_w(alpha_w) == math.pi / 2.0:
        r = nu * f_cd / tau_ed
        return None if r < 2.0 else 0.5 * (r + math.sqrt(r * r - 4.0))  # noqa: PLR2004
    lo, hi = 1.0, 20.0
    if calc_sigma_cd(tau_ed, lo, alpha_w) > nu * f_cd:
        return None
    if calc_sigma_cd(tau_ed, hi, alpha_w) <= nu * f_cd:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if calc_sigma_cd(tau_ed, mid, alpha_w) <= nu * f_cd:
            lo = mid
        else:
            hi = mid
    return lo


def calc_asw_s(v_ed: float, z: float, f_ywd: float, cot: float,
               alpha_w: float = 90.0) -> float:
    """Return the shear reinforcement ``Asw/s`` [m²/m] for ``VEd`` [kN].

    From ``τRd,sy = τEd`` with Eqs. (8.42) / (8.59), ``τEd = VEd/(bw·z)``.
    """
    a = _check_alpha_w(alpha_w)
    return abs(v_ed) / (z * f_ywd * (cot + _cot(a)) * math.sin(a)) / 1000.0


def calc_vrd_s(asw_s: float, z: float, f_ywd: float, cot: float,
               alpha_w: float = 90.0) -> float:
    """Return the shear resistance ``VRd,s`` [kN] of the reinforcement (yielding)."""
    a = _check_alpha_w(alpha_w)
    return asw_s * z * f_ywd * (cot + _cot(a)) * math.sin(a) * 1000.0


def calc_vrd_max(b_w: float, z: float, nu: float, f_cd: float, cot: float,
                 alpha_w: float = 90.0) -> float:
    """Return the compression-field resistance ``VRd,max`` [kN] (``σcd = ν·fcd``)."""
    a = _check_alpha_w(alpha_w)
    return nu * f_cd * b_w * z * (cot + _cot(a)) / (1.0 + cot**2) * 1000.0


def calc_nu(eps_x: float, cot: float) -> float:
    """Return the strength-reduction factor ``ν`` from the strains, Eq. (8.45).

    ``1/(1 + 110·(εx + (εx + 0,001)·cot²θ)) ≤ 1,0``; ``eps_x`` is Eq. (8.46) and
    only valid with ductility class B or C reinforcement.
    """
    return min(1.0 / (1.0 + 110.0 * (eps_x + (eps_x + 0.001) * cot**2)), 1.0)


def calc_n_vd(v_ed: float, cot: float, alpha_w: float = 90.0) -> float:
    """Return the additional tensile force ``NVd`` [kN], Eq. (8.50) / (8.61)."""
    a = _check_alpha_w(alpha_w)
    return abs(v_ed) * (cot - _cot(a))


def calc_chord_forces(m_ed: float, v_ed: float, n_ed: float, z: float,
                      cot: float, alpha_w: float = 90.0) -> dict:
    """Return the chord forces ``Ftd`` and ``Fcd`` [kN], Eqs. (8.50)-(8.52).

    ``m_ed`` in kNm, ``n_ed`` positive in tension. ``Fcd`` is positive in
    compression.
    """
    n_vd = calc_n_vd(v_ed, cot, alpha_w)
    return {"n_vd": n_vd,
            "f_td": m_ed / z + (n_vd + n_ed) / 2.0,
            "f_cd": m_ed / z - (n_vd + n_ed) / 2.0}


def calc_eps_x(f_td: float, a_st: float, e_s: float, f_cd: float,
               a_cc: float | None = None, e_c: float | None = None,
               a_sc: float | None = None) -> float:
    """Return the average chord strain ``εx ≥ 0``, Eqs. (8.46)-(8.49).

    ``f_td``/``f_cd`` [kN] from :func:`calc_chord_forces`, areas [m²], moduli
    [MPa]. A compression chord in compression (``f_cd ≥ 0``) needs ``a_cc`` and
    ``e_c``; in tension (``f_cd < 0``) it needs ``a_sc``.
    """
    eps_xt = f_td / (a_st * e_s * 1000.0)
    if f_cd >= 0.0:
        if a_cc is None or e_c is None:
            msg = "a_cc and e_c are needed when the compression chord is in compression"
            raise ValueError(msg)
        eps_xc = -f_cd / (a_cc * e_c * 1000.0)
    else:
        if a_sc is None:
            msg = "a_sc is needed when the 'compression' chord is in tension"
            raise ValueError(msg)
        eps_xc = abs(f_cd) / (a_sc * e_s * 1000.0)
    return max(0.5 * (eps_xt + eps_xc), 0.0)


def calc_sigma_swd(eps_x: float, cot: float, e_s: float, f_ywd: float,
                   alpha_w: float = 90.0) -> float:
    """Return the stress in the shear reinforcement for ``cot θ < 1`` [MPa].

    Eq. (8.56) (vertical) / (8.63) (inclined), limited to ``fywd``.
    """
    a = _check_alpha_w(alpha_w)
    s = e_s * ((eps_x + 0.001) * (cot + _cot(a)) ** 2 / (1.0 + _cot(a) ** 2) - 0.001)
    return min(s, f_ywd)


def calc_tau_rd_near_support(nu: float, f_cd: float, rho_w_f_ywd: float,
                             cot: float, cot_beta: float,
                             alpha_w: float = 90.0) -> float:
    """Return ``τRd`` with concentrated loads near a support [MPa], Eqs. (8.55)/(8.62).

    ``ν·fcd·(cot θ − cot βincl)/(1 + cot²θ) + ρw·fywd·(cot βincl + cot αw)·sin αw``
    limited to ``ν·fcd·(cot θ + cot αw)/(1 + cot²θ)``; ``rho_w_f_ywd`` is
    ``ρw·fywd`` (or ``ρw·fywd + qd/bw`` for a distributed load).
    """
    a = _check_alpha_w(alpha_w)
    t = (nu * f_cd * (cot - cot_beta) / (1.0 + cot**2)
         + rho_w_f_ywd * (cot_beta + _cot(a)) * math.sin(a))
    return min(t, nu * f_cd * (cot + _cot(a)) / (1.0 + cot**2))


def calc_delta_m_ed(tau_ed: float, rho_w_f_ywd: float, cot: float, z: float,
                    b_w: float, a: float, x: float) -> float:
    """Return the additional moment ``ΔMEd`` [kNm], Eq. (8.57).

    ``(τEd − ρw·fywd·cot θ)·z·bw·(a/2 − x)``; ``a`` and ``x`` in m.
    """
    return (tau_ed - rho_w_f_ywd * cot) * z * b_w * (a / 2.0 - x) * 1000.0


def calc_bw_nom(b_w: float, sum_phi_duct: float, duct: str = "grouted_steel") -> float:
    """Return the nominal web width ``bw,nom = bw − kduct·Σφduct`` [m], Eq. (8.54).

    Applies when ``Σφduct > bw/8``; otherwise ``bw`` is returned. ``duct`` is
    ``"grouted_steel"`` (kduct 0,5), ``"grouted_plastic"`` (0,8) or
    ``"other"`` (1,2: not grouted, thick plastic or soft filling).
    """
    k = {"grouted_steel": 0.5, "grouted_plastic": 0.8, "other": 1.2}
    if duct not in k:
        msg = f"duct must be one of {tuple(k)}, got '{duct}'"
        raise ValueError(msg)
    return b_w if sum_phi_duct <= b_w / _DUCT_RATIO else b_w - k[duct] * sum_phi_duct


# ── 8.2.4 In-plane shear and transverse bending ─────────────────────────────

def calc_taurdm(tau_rd: float, m_ed: float, m_rd: float) -> float:
    """Return ``τRdm = τRd·√(1 − mEd/mRd)`` [MPa], Eq. (8.64)."""
    return tau_rd * math.sqrt(max(1.0 - abs(m_ed) / m_rd, 0.0))


def transverse_bending_negligible(tau_ed: float, tau_rd: float,
                                  m_ed: float, m_rd: float) -> bool:
    """Return ``True`` if 8.2.4(1) allows the interaction to be ignored.

    ``τEd/τRd < 0,2`` or ``mEd/mRd < 0,1``.
    """
    return tau_ed / tau_rd < 0.2 or abs(m_ed) / m_rd < 0.1  # noqa: PLR2004


# ── 8.2.5 Shear between web and flanges ─────────────────────────────────────

def calc_tau_ed_flange(delta_f_d: float, h_f: float, delta_x: float) -> float:
    """Return the longitudinal shear stress web-flange [MPa], Eq. (8.65).

    ``ΔFd`` [kN] over ``Δx`` [m] for a flange of thickness ``hf`` [m].
    """
    return abs(delta_f_d) / (h_f * delta_x) / 1000.0


def flange_cot_theta_range(*, compression_flange: bool) -> tuple[float, float]:
    """Return ``(1, cot θf,max)``: 3,0 in compression flanges, 1,25 in tension (8.67)-(8.68)."""
    return 1.0, 3.0 if compression_flange else 1.25


def calc_asf_sf(tau_ed: float, h_f: float, f_yd: float, cot_f: float) -> float:
    """Return the flange transverse reinforcement ``Asf/sf`` [m²/m], Eq. (8.69)."""
    return tau_ed * h_f / (f_yd * cot_f)


def flange_crushing_ok(tau_ed: float, cot_f: float, f_cd: float,
                       nu: float = NU_DEFAULT) -> bool:
    """Return ``True`` if ``τEd·(cot θf + tan θf) ≤ ν·fcd``, Eqs. (8.70)-(8.71)."""
    return tau_ed * (cot_f + 1.0 / cot_f) <= nu * f_cd


def flange_check_omitted(tau_ed: float, a_st_min: float, s_f: float, h_f: float,
                         f_yd: float) -> bool:
    """Return ``True`` if Eq. (8.66) lets the web-flange verification be omitted.

    ``τEd ≤ Ast,min/(sf·hf)·fyd`` with ``Ast,min`` [m²] of Table 12.1 (NDP).
    """
    return tau_ed <= a_st_min / (s_f * h_f) * f_yd


# ── 8.2.6 Shear at interfaces ───────────────────────────────────────────────

def interface_coefficients(roughness: str, edition: str = "2023",
                           annex: str | None = None) -> dict:
    """Return the Table 8.2 coefficients (``c_v1``, ``mu_v``, ``c_v2``, ``k_v``, ``k_dowel``).

    ``annex`` is the country code of a national annex that patches the table.
    """
    table = dbase.get_edition_params("ec2", "shear_interface", edition, annex)
    if roughness not in table or roughness.startswith("_"):
        msg = f"roughness must be one of {[k for k in table if not k.startswith('_')]}"
        raise ValueError(msg)
    return dict(table[roughness])


def calc_tau_edi(v_edi: float, a_i: float) -> float:
    """Return ``τEdi = VEdi/Ai`` [MPa], Eq. (8.74); ``v_edi`` [kN], ``a_i`` [m²]."""
    return v_edi / a_i / 1000.0


def calc_tau_edi_composite(beta_new: float, v_ed: float, z: float, b_i: float) -> float:
    """Return ``τEdi = βnew·VEd/(z·bi)`` [MPa] for composite action, Eq. (8.75)."""
    return beta_new * abs(v_ed) / (z * b_i) / 1000.0


def calc_tau_rdi(fck: float, gamma_c: float, f_cd: float, roughness: str,
                 sigma_n: float = 0.0, rho_i: float = 0.0, f_yd: float = 0.0,
                 alpha: float = 90.0, *, anchored: bool = True,
                 topping: bool = False, dowel: bool = True,
                 annex: str | None = None) -> float:
    """Return the interface shear resistance ``τRdi`` [MPa], Eqs. (8.76)-(8.77).

    ``sigma_n`` [MPa] is positive in compression (limited to ``0,6·fcd``); in
    tension ``cv1 = cv2 = 0`` and ``μv·σn = 0``. ``rho_i = Asi/Ai``.
    ``alpha`` [°] is the inclination of the interface reinforcement
    (35°-135°, 35°-90° for very smooth and smooth surfaces).

    ``anchored=True`` (reinforcement anchored for ``σsd = fyd``, or none
    needed): Eq. (8.76). ``anchored=False``: Eq. (8.77); ``topping=True``
    raises ``cv2`` by 1,2 (cast-in-place topping, rough/very rough);
    ``dowel=False`` sets ``kdowel = 0`` (bar closer than 10φ to the edge).
    ``annex`` selects the coefficients of a national annex.
    """
    c = interface_coefficients(roughness, annex=annex)
    tension = sigma_n < 0.0
    sn = 0.0 if tension else min(sigma_n, 0.6 * f_cd)
    root = math.sqrt(fck) / gamma_c
    if anchored:
        if not (_MIN_ALPHA_I <= alpha <= _MAX_ALPHA_I) or (
                roughness in ("very_smooth", "smooth") and alpha > _MAX_ALPHA_W):
            msg = "alpha outside the range of 8.2.6(5)"
            raise ValueError(msg)
        a = math.radians(alpha)
        cv1 = 0.0 if tension else c["c_v1"]
        t = (cv1 * root + c["mu_v"] * sn
             + rho_i * f_yd * (c["mu_v"] * math.sin(a) + math.cos(a)))
        return min(t, 0.30 * f_cd + rho_i * f_yd * math.cos(a))
    if c["c_v2"] is None:
        msg = "Eq. (8.77) has no coefficients for keyed interfaces"
        raise ValueError(msg)
    cv2 = 0.0 if tension else c["c_v2"] * (1.2 if topping else 1.0)
    k_dowel = c["k_dowel"] if dowel else 0.0
    t = (cv2 * root + c["mu_v"] * sn + c["k_v"] * rho_i * f_yd * c["mu_v"]
         + k_dowel * rho_i * math.sqrt(f_yd * f_cd))
    return min(t, 0.25 * f_cd)


def calc_as_min_interface(t_min: float, f_ctm: float, f_yk: float) -> float:
    """Return the minimum interface reinforcement per length ``as,min = tmin·fctm/fyk``, Eq. (8.78)."""
    return t_min * f_ctm / f_yk


# ── helpers ─────────────────────────────────────────────────────────────────

def _check_alpha_w(alpha_w: float) -> float:
    if not (_MIN_ALPHA_W <= alpha_w <= _MAX_ALPHA_W):
        msg = "alpha_w must be between 45° and 90° (8.2.3(13))"
        raise ValueError(msg)
    return math.radians(alpha_w)


def _cot(a: float) -> float:
    return 0.0 if a == math.pi / 2.0 else 1.0 / math.tan(a)
