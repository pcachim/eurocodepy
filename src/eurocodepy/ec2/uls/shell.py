# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

import math

import numpy as np

TOLER = 1.0e-12


def calc_reinf_plane(n_xx: float, n_yy: float, n_xy: float) -> list:
    """Calculate the reinforcement in a plane element.

    Args:
        n_xx (float): axial force in x direction
        n_yy (float): axial force in y direction
        n_xy (float): shear force in xy direction

    Returns:
        list: ``[asx, asy, asc, cot θ]``, the reinforcement in both directions, the
            concrete stress and the strut inclination. ``cot θ`` is ``math.inf`` for
            ``n_xy = 0`` with compression in x (the strut is parallel to x) and
            ``math.nan`` when no reinforcement is required (both compressive and
            ``n_xx·n_yy > n_xy²``): the angle is undefined there.

    """
    abs_n_xy = abs(n_xy)
    n_xx_n_yy = n_xx * n_yy
    n_xy_2 = n_xy * n_xy
    if n_xx >= -abs_n_xy and n_yy >= -abs_n_xy:
        theta = 1.0
        asx = n_xx + abs_n_xy
        asy = n_yy + abs_n_xy
        asc = 2.0 * abs_n_xy
    elif n_xx < -abs_n_xy and n_xx <= n_yy and n_xx_n_yy <= n_xy_2:
        theta = math.inf if abs_n_xy < TOLER else -n_xx / abs_n_xy
        asx = 0.0
        asy = n_yy + n_xy_2 / abs(n_xx)
        asc = abs(n_xx) * (1.0 + (abs_n_xy / n_xx)**2)
    elif n_yy < -abs_n_xy and n_xx >= n_yy and n_xx_n_yy <= n_xy_2:
        theta = -abs_n_xy / n_yy
        asx = n_xx + n_xy_2 / abs(n_yy)
        asy = 0.0
        asc = abs(n_yy) * (1.0 + (abs_n_xy / n_yy)**2)
    else:
        cen = (n_xx + n_yy) * 0.5
        rad = math.sqrt(n_xy_2 + 0.25 * (n_xx - n_yy)**2)
        theta = math.nan                      # no reinforcement: θ undefined
        asx = 0.0
        asy = 0.0
        asc = abs(cen - rad)

    return [asx, asy, asc, theta]


def cal_reinf_shell_plan(top_forces: tuple, bottom_forces: tuple) -> np.ndarray:
    """Calculate reinforcement for shell plane given top and bottom force tuples.

    Args:
        top_forces (tuple): (n_t_xx, n_t_yy, n_t_xy)
        bottom_forces (tuple): (n_b_xx, n_b_yy, n_b_xy)

    Returns:
        np.ndarray: Reinforcement and concrete stresses for both layers.

    """
    return np.array(
        calc_reinf_plane(*top_forces) + calc_reinf_plane(*bottom_forces),
    )


def calc_reinf_shell(n_xx: float, n_yy: float, n_xy: float,
                    m_xx: float, m_yy: float, m_xy: float,
                    rec: float, h: float) -> np.ndarray:
    """Calculate the forces to ccalculate the reinforcement in a shell element.

    Args:
        n_xx (float): axial force in x direction
        n_yy (float): axial force in y direction
        n_xy (float): shear force in xy direction
        m_xx (float): moment in x direction (bending)
        m_yy (float): moment in y direction (bending)
        m_xy (float): moment in xy direction (torsion)
        rec (float): cover to reinforcement
        h (float): height of the shell

    This is the sandwich model of EN 1992-2:2005 Annex LL (Eqs. LL.137-LL.142 with
    ``y_s = y_i = z/2``, layers of thickness twice the cover): the "top" layer is its superior
    layer (``n/2 + m/z``, ``n_xy/2 − m_xy/z``), so ``m`` is positive for tension on the top face.

    Returns:
        np.ndarray: 8 values, ``[asx, asy, asc, cot θ]`` of the "top" layer followed
            by the same four of the "bottom" layer (``calc_reinf_plane`` of each
            layer). They are per unit of layer thickness ``t = 2·rec`` — stresses in
            the unit of ``n/t`` (kN/m² for n in kN/m) — so multiply ``asx`` and
            ``asy`` by ``t`` for the force per unit length. All ``nan`` if the two
            layers overlap (``h < 4·rec``).

    The "top" layer is the one in tension for a positive ``m_xx`` and ``m_yy`` (Annex LL);
    the sandwich model of EN 1992-1-1:2023 Annex G has sagging positive (the bottom layer in
    tension), see :func:`eurocodepy.ec2.uls2023.annex_g.sandwich_stresses`, and
    :func:`eurocodepy.ec2.uls.shell_check.eurocode2_shell_check` for the composite.

    """
    t = 2 * rec
    z = h - t
    if h - 4 * rec < 0:
        return np.full(8, math.nan)

    n_t_xx = (0.5 * n_xx + m_xx / z) / t
    n_t_yy = (0.5 * n_yy + m_yy / z) / t
    n_t_xy = (0.5 * n_xy - m_xy / z) / t

    n_b_xx = (0.5 * n_xx - m_xx / z) / t
    n_b_yy = (0.5 * n_yy - m_yy / z) / t
    n_b_xy = (0.5 * n_xy + m_xy / z) / t

    return cal_reinf_shell_plan((n_t_xx, n_t_yy, n_t_xy), (n_b_xx, n_b_yy, n_b_xy))


_DELTA_THETA_MAX = 15.0          # degrees, EN 1992-2 6.109 Expr. (6.112)


def principal_stresses(sx: float, sy: float, txy: float) -> tuple[float, float]:
    """Return the principal stresses ``(σ1, σ2)``, ``σ1 ≥ σ2`` (tension positive)."""
    centre = 0.5 * (sx + sy)
    radius = math.hypot(0.5 * (sx - sy), txy)
    return centre + radius, centre - radius


def elastic_compression_angle(sx: float, sy: float, txy: float) -> float:
    """Return ``θel``, the inclination [°, 0-90] of the principal compression to the x axis.

    For the sign convention of the membrane equations (``|τ|``): ``90° − ½·atan2(2|τ|, σx − σy)``;
    e.g. 45° in pure shear, 0° in uniaxial compression along x.
    """
    return 90.0 - 0.5 * math.degrees(math.atan2(2.0 * abs(txy), sx - sy))


def membrane_strut_limit(sx: float, sy: float, txy: float, fck: float, fcd: float,
                         cot: float | None) -> dict:
    """Return the maximum compressive stress of the concrete field, EN 1992-2:2005 §6.109(103).

    ``sx``, ``sy``, ``txy`` (any consistent stress or force-per-length unit, tension
    positive) and ``fcd`` in the same unit; ``cot`` is the ``cot θ`` of the reinforcement
    design (:func:`calc_reinf_plane`), ``None`` where no reinforcement is required.

    * both principal stresses compressive (no reinforcement), Eq. (6.110):
      ``0,85·fcd·(1 + 3,8·α)/(1 + α)²``, ``α = |σ_smaller|/|σ_larger| ≤ 1``;
    * reinforcement that yields (the design case), Eq. (6.112):
      ``ν'·fcd·(1 − 0,032·|θ − θel|)``, ``ν' = 0,6·(1 − fck/250)``, ``|θ − θel|``
      limited to 15° (beyond it the factor is that of 15° and ``angle_ok`` is ``False``:
      the clause does not cover a larger deviation).

    Case (ii), reinforcement that does not yield (Eq. 6.111), does not arise in a design where
    the reinforcement is sized to yield. Returns ``limit``, ``factor`` (= limit/fcd), ``case``
    (``"biaxial_compression"`` or ``"yielding"``), ``alpha``, ``theta``, ``theta_el``,
    ``delta_theta`` and ``angle_ok``.
    """
    s1, s2 = principal_stresses(sx, sy, txy)
    if cot is None:
        a = min(abs(s1), abs(s2)) / max(abs(s1), abs(s2)) if max(abs(s1), abs(s2)) > 0 else 0.0
        factor = 0.85 * (1.0 + 3.8 * a) / (1.0 + a) ** 2
        return {"limit": factor * fcd, "factor": factor, "case": "biaxial_compression",
                "alpha": a, "theta": None, "theta_el": None, "delta_theta": None,
                "angle_ok": True}
    theta = 0.0 if math.isinf(cot) else math.degrees(math.atan2(1.0, cot))
    theta_el = elastic_compression_angle(sx, sy, txy)
    delta = abs(theta - theta_el)
    nu = 0.6 * (1.0 - fck / 250.0)
    factor = nu * (1.0 - 0.032 * min(delta, _DELTA_THETA_MAX))
    return {"limit": factor * fcd, "factor": factor, "case": "yielding", "alpha": None,
            "theta": theta, "theta_el": theta_el, "delta_theta": delta,
            "angle_ok": delta <= _DELTA_THETA_MAX + 1e-9}


STRUT_MODELS = ("annex_f", "6.109")


def annex_f_strut_limit(fck: float, fcd: float, cot: float | None) -> dict:
    """Return the maximum compressive stress of the concrete field, EN 1992-1-1:2004 Annex F.1(3)-(4).

    Where no reinforcement is required (``cot is None``: both stresses compressive and
    ``σx·σy > τ²``) ``σ ≤ fcd`` (F.1(3)); with reinforcement the concrete stress "should not
    generally exceed ``ν·fcd``", ``ν = 0.6·(1 − fck/250)`` of Expression (6.5) (F.1(4)).
    Same keys as :func:`membrane_strut_limit` (``alpha``, ``theta`` ... are ``None``).
    """
    if cot is None:
        return {"limit": fcd, "factor": 1.0, "case": "no_reinforcement", "alpha": None,
                "theta": None, "theta_el": None, "delta_theta": None, "angle_ok": True}
    nu = 0.6 * (1.0 - fck / 250.0)
    return {"limit": nu * fcd, "factor": nu, "case": "reinforced", "alpha": None,
            "theta": None, "theta_el": None, "delta_theta": None, "angle_ok": True}


def strut_limit(model: str, sx: float, sy: float, txy: float, fck: float, fcd: float,
                cot: float | None) -> dict:
    """Return the strut strength by ``model``: ``"annex_f"`` (EN 1992-1-1:2004, the default of
    the 2004 composites) or ``"6.109"`` (EN 1992-2:2005 §6.109(103), :func:`membrane_strut_limit`)."""
    if model == "annex_f":
        return annex_f_strut_limit(fck, fcd, cot)
    if model == "6.109":
        return membrane_strut_limit(sx, sy, txy, fck, fcd, cot)
    msg = f"strut_model must be one of {STRUT_MODELS}, got '{model}'"
    raise ValueError(msg)


def deformation_capacity_ok_2004(ftdx: float, ftdy: float, sx: float, sy: float,
                                 txy: float) -> bool:
    """Return ``True`` if ``½·ft* ≤ ft ≤ 2·ft*`` in both directions, EN 1992-1-1:2004 F.1(4).

    ``ft*`` is the optimum reinforcement (Expressions F.2/F.3 or F.5/F.6, i.e. :func:`calc_reinf_plane`)
    and ``ftdx``, ``ftdy`` the reinforcement of Expressions (F.8)/(F.9) for another ``cot θ``
    (tension positive, as the rest of the module).
    """
    ox, oy = calc_reinf_plane(sx, sy, txy)[:2]

    def _ok(v, o):
        return v <= TOLER if o <= TOLER else 0.5 * o - TOLER <= v <= 2.0 * o + TOLER
    return _ok(ftdx, ox) and _ok(ftdy, oy)


# ── EN 1992-2:2005 Annex LL (107): is the shell element cracked? ─────────────

def _fctm_2004(fck: float) -> float:
    """Mean axial tensile strength [MPa], EN 1992-1-1:2004 Table 3.1."""
    if fck <= 50.0:  # noqa: PLR2004
        return 0.30 * fck ** (2.0 / 3.0)
    return 2.12 * math.log(1.0 + (fck + 8.0) / 10.0)


def ottosen_phi(sigma_1: float, sigma_2: float, sigma_3: float, f_cm: float,
                f_ctm: float) -> float:
    """Return ``Φ`` of Eq. (LL.101), the failure criterion of EN 1992-2:2005 Annex LL (107).

    ``Φ = α·J2/fcm² + λ·√J2/fcm + β·I1/fcm − 1`` with Eqs. (LL.102)-(LL.112); the principal
    stresses are in tension-positive MPa. ``Φ ≤ 0``: not cracked; ``Φ > 0``: cracked.
    """
    k = f_ctm / f_cm
    alpha = 1.0 / (9.0 * k**1.4)
    beta = 1.0 / (3.7 * k**1.1)
    c1 = 1.0 / (0.7 * k**0.9)
    c2 = 1.0 - 6.8 * (k - 0.07) ** 2
    i1 = sigma_1 + sigma_2 + sigma_3
    sm = i1 / 3.0
    j2 = ((sigma_1 - sigma_2) ** 2 + (sigma_2 - sigma_3) ** 2 + (sigma_3 - sigma_1) ** 2) / 6.0
    j3 = (sigma_1 - sm) * (sigma_2 - sm) * (sigma_3 - sm)
    if j2 <= 0.0:
        lam = 0.0                      # hydrostatic: the √J2 term vanishes
    else:
        cos3t = min(max(1.5 * math.sqrt(3.0) * j3 / j2**1.5, -1.0), 1.0)
        if cos3t >= 0.0:
            lam = c1 * math.cos(math.acos(c2 * cos3t) / 3.0)
        else:
            lam = c1 * math.cos(math.pi / 3.0 - math.acos(-c2 * cos3t) / 3.0)
    return (alpha * j2 / f_cm**2 + lam * math.sqrt(max(j2, 0.0)) / f_cm
            + beta * i1 / f_cm - 1.0)


def shell_stresses_at_level(n: tuple[float, float, float], m: tuple[float, float, float],
                            v: tuple[float, float], h: float, z: float) -> np.ndarray:
    """Return the 3×3 stress tensor [MPa] of an uncracked shell element at depth ``z``.

    ``n`` [kN/m], ``m`` [kNm/m], ``v = (vx, vy)`` [kN/m], thickness ``h`` and ``z`` [m] measured from
    the mid-plane towards the **bottom** face (sagging moments give tension for ``z > 0``):
    ``σ = n/h + 12·m·z/h³``, ``τxy = n_xy/h − 12·m_xy·z/h³`` (the sign of the sandwich model) and
    the parabolic transverse shear ``τxz = 1.5·vx/h·(1 − 4z²/h²)``, ``τyz`` likewise; ``σz = 0``.
    """
    sx = (n[0] / h + 12.0 * m[0] * z / h**3) / 1000.0
    sy = (n[1] / h + 12.0 * m[1] * z / h**3) / 1000.0
    txy = (n[2] / h - 12.0 * m[2] * z / h**3) / 1000.0
    shape = 1.5 * (1.0 - 4.0 * z * z / (h * h)) / h / 1000.0
    txz, tyz = v[0] * shape, v[1] * shape
    return np.array([[sx, txy, txz], [txy, sy, tyz], [txz, tyz, 0.0]])


def shell_cracking(n: tuple[float, float, float], m: tuple[float, float, float], h: float,
                   fck: float, v: tuple[float, float] = (0.0, 0.0), f_ctm: float | None = None,
                   n_levels: int = 21) -> dict:
    """Check whether a shell element is cracked, EN 1992-2:2005 Annex LL (102), (107).

    The principal stresses of the uncracked section are evaluated at ``n_levels`` depths and
    Eq. (LL.101) is applied; the element is cracked where ``Φ > 0`` at any level. Returns
    ``cracked``, ``phi_max``, ``z_crit`` [m], ``sigma_min`` (the most compressive principal stress
    of all levels, [MPa]; LL (103): in an uncracked element it must not exceed ``fcd``),
    ``f_cm`` and ``f_ctm`` [MPa].
    """
    fcm = fck + 8.0
    fctm = _fctm_2004(fck) if f_ctm is None else f_ctm
    phi_max, z_crit, s_min = -math.inf, 0.0, math.inf
    for i in range(n_levels):
        z = -0.5 * h + h * i / (n_levels - 1)
        sig = np.sort(np.linalg.eigvalsh(shell_stresses_at_level(n, m, v, h, z)))[::-1]
        phi = ottosen_phi(float(sig[0]), float(sig[1]), float(sig[2]), fcm, fctm)
        s_min = min(s_min, float(sig[2]))
        if phi > phi_max:
            phi_max, z_crit = phi, z
    return {"cracked": phi_max > 0.0, "phi_max": phi_max, "z_crit": z_crit,
            "sigma_min": s_min, "f_cm": fcm, "f_ctm": fctm}
