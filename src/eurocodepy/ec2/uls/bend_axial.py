# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Rectangular RC section design for combined bending and axial force (M-N).

EN 1992-1-1 ultimate-limit-state design of the tension (As1) and compression
(As2) reinforcement of a rectangular section subjected to a bending moment and
an axial force, using the simplified rectangular stress block and the
transferred-moment method.

The axial force is referred to the section mid-height (centroid). The applied
moment is transferred to the level of the tension reinforcement,

    M_Eds = M_Ed + N_Ed * (h/2 - d1)            (N_Ed compression positive)

and the section is then designed as in pure bending for ``M_Eds``; the axial
force is finally introduced through axial equilibrium,

    As1 = (Fc + As2*fyd - N_Ed) / fyd ,         As2 from the residual moment.

This reduces exactly to the pure-bending result of :func:`calc_asl` when
``N_Ed = 0`` and ``d1 = d2``, so the two share a single source of truth for the
``omega`` relationship.
"""

import math

from eurocodepy.ec2.materials import Concrete, GammaC, GammaS
from eurocodepy.ec2.uls.beam import calc_asl


def _alpha_lim(fck: float) -> float:
    """Limiting neutral-axis ratio x/d for a singly reinforced section."""
    return 0.45 if fck <= 50.0 else 0.35


def _mu_lim(fck: float) -> float:
    """Limiting reduced moment for the simplified rectangular stress block.

    Derived from the maximum allowed neutral-axis depth (x/d = ``_alpha_lim``)
    with ``x/d = 1.25*omega`` (rectangular block), i.e. omega_max = alpha/1.25
    and mu_lim = omega_max*(1 - omega_max/2). For fck <= 50 this gives
    ~0.295, consistent with the eurocodepy bending routine.
    """
    omega_max = _alpha_lim(fck) / 1.25
    return omega_max * (1.0 - 0.5 * omega_max)


def calc_asl_nm(
    b: float,
    h: float,
    d1: float,
    d2: float,
    med: float,
    ned: float,
    fck: float,
    fyk: float,
    gamma_c: float = GammaC,
    gamma_s: float = GammaS,
    alpha_cc: float = 1.0,
    iprint: bool = False,
    trace=None,
    method: str = "simplified",
    nu_simplified: float = 0.05,
) -> dict:
    """Design a rectangular RC section for combined bending and axial force.

    Args:
        b (float): section width [m].
        h (float): section height [m].
        d1 (float): mechanical cover to the tension reinforcement, measured
            from the tension face [m]. The effective depth is ``d = h - d1``.
        d2 (float): mechanical cover to the compression reinforcement, measured
            from the compression face [m].
        med (float): design bending moment about the section mid-height [kNm].
        ned (float): design axial force [kN], **compression positive**.
        fck (float): characteristic concrete strength [MPa].
        fyk (float): characteristic reinforcement yield strength [MPa].
        gamma_c (float, optional): concrete partial factor. Defaults to GammaC.
        gamma_s (float, optional): steel partial factor. Defaults to GammaS.
        alpha_cc (float, optional): long-term/loading coefficient on fcd.
            Defaults to 1.0 (EN 1992-1-1 recommended / Portuguese NA).
        iprint (bool, optional): print a summary. Defaults to False.
        trace: optional ``CalcReport`` the steps are recorded into.
        method (str, optional): ``"simplified"`` (default) is the rectangular
            stress block / transferred-moment method described above.
            ``"strain"`` always uses :func:`calc_asl_nm_strain`.
            ``"auto"`` uses the simplified method where it is reliable — flexure
            with little axial compression, ``nu <= nu_simplified``, tension
            included — and strain compatibility otherwise, or whenever the
            simplified method flags itself inapplicable.
        nu_simplified (float, optional): for ``method="auto"``, the largest
            reduced axial force ``nu = N_Ed/(b*h*fcd)`` (compression positive)
            still designed with the simplified method. Defaults to 0.05: up to
            there it stays within about +10 % / -1 % of steel and 1.1 % of
            capacity against strain compatibility (the excess at high moments
            is the x/d <= 0.45 limit it imposes, EN 1992-1-1 §5.5(4), which
            the strain method does not).

    Returns:
        dict: with keys
            ``As1`` tension reinforcement [cm2],
            ``As2`` compression reinforcement [cm2],
            ``As_min`` minimum tension reinforcement [cm2],
            ``mu`` reduced (transferred) moment,
            ``omega`` mechanical reinforcement ratio,
            ``x_d`` neutral-axis ratio x/d,
            ``med_s`` transferred design moment [kNm],
            ``doubly`` whether compression steel is required,
            ``note`` text flag for special cases (e.g. small eccentricity).

    Notes:
        The simplified method is valid while the section is in the
        tension-/balanced-controlled regime (neutral axis within the section
        and the tension steel able to yield). For members dominated by axial
        compression with small eccentricity it returns ``As1 = As_min`` and a
        ``note`` flag; a full M-N interaction (strain compatibility) is then
        required and should be used instead.

    """
    if method not in ("simplified", "auto", "strain"):
        msg = f"method must be 'simplified', 'auto' or 'strain', not {method!r}."
        raise ValueError(msg)
    if method == "strain":
        return calc_asl_nm_strain(b, h, d1, d2, med, ned, fck, fyk,
                                  gamma_c, gamma_s, alpha_cc, trace=trace)
    if method == "auto" and ned / (b * h * alpha_cc * fck / gamma_c * 1000.0) > nu_simplified:
        return calc_asl_nm_strain(b, h, d1, d2, med, ned, fck, fyk,
                                  gamma_c, gamma_s, alpha_cc, trace=trace)

    d = h - d1
    if d <= 0:
        msg = "Effective depth d = h - d1 must be positive."
        raise ValueError(msg)

    fcd = alpha_cc * fck / gamma_c          # [MPa]
    fyd = fyk / gamma_s                       # [MPa]

    # Transfer the moment to the tension-reinforcement level. The applied moment
    # decides which face is in tension; the axial force (compression positive)
    # is referred to that tension steel, which sits (h/2 - d1) from the centroid.
    # Using the magnitude keeps the result symmetric for sagging vs hogging:
    # |M_Eds| = |M_Ed| + N_comp·(h/2 - d1)  (axial tension reduces it).
    zs = h / 2.0 - d1
    med_s_abs = abs(med) + ned * zs            # [kNm]
    if med_s_abs < 0.0:
        med_s_abs = 0.0
    med_s = math.copysign(med_s_abs, med) if med != 0.0 else med_s_abs

    mu = med_s_abs / (b * d * d * fcd) / 1000.0
    mu_lim = _mu_lim(fck)

    note = ""
    if mu <= mu_lim:
        # Singly reinforced for the transferred moment (reuse calc_asl so the
        # omega relationship has a single source of truth).
        if med_s_abs < 1.0e-9:
            ast_bending, x_d = 0.0, 0.0
        else:
            ast_bending, _epss, x_d = calc_asl(b, d, med_s_abs, fcd, fyd)
        as2 = 0.0
        # Axial equilibrium: As1 = Fc/fyd - Ned/fyd  (Fc = ast_bending*fyd).
        # ned is compression-positive and reduces the tension steel regardless
        # of the moment sign (i.e. of which face is in tension).
        as1 = ast_bending - ned / fyd * 10.0   # [cm2]
        omega = 1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * mu))
    else:
        # Doubly reinforced: cap the concrete contribution at mu_lim and carry
        # the residual moment with compression steel.
        omega = 1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * mu_lim))
        x_d = 1.25 * omega
        med_lim = mu_lim * b * d * d * fcd * 1000.0       # [kNm]
        dmed = med_s_abs - med_lim                          # [kNm]
        as2 = dmed / ((d - d2) * fyd) * 10.0                # [cm2]
        # Tension steel = concrete block steel + compression steel - axial.
        as1 = (omega * b * d * fcd / fyd * 10000.0
               + as2
               - ned / fyd * 10.0)                          # [cm2]

    # EN 1992-1-1 9.2.1.1 minimum tension reinforcement, using fctm.
    fctm = _fctm(fck)
    as_min = max(0.26 * fctm / fyk, 0.0013) * b * d * 10000.0   # [cm2]

    if as1 < 0.0:
        # Section dominated by axial compression: simplified design no longer
        # governs the tension face. Fall back to minimum steel and flag it.
        note = ("small eccentricity / compression-controlled: "
                "use full M-N interaction")
        as1 = as_min
    else:
        as1 = max(as1, as_min)

    as2 = max(as2, 0.0)

    if note and method == "auto":
        # Still flagged inapplicable inside the low-nu range: solve by strain
        # compatibility instead of returning As_min.
        return calc_asl_nm_strain(b, h, d1, d2, med, ned, fck, fyk,
                                  gamma_c, gamma_s, alpha_cc, trace=trace)

    if iprint:
        print(
            f"M_Ed={med:.1f} kNm N_Ed={ned:.1f} kN -> M_Eds={med_s:.1f} kNm | "
            f"mu={mu:.3f} (mu_lim={mu_lim:.3f}) x/d={x_d:.3f} | "
            f"As1={as1:.2f} cm2 As2={as2:.2f} cm2 {note}",
        )

    if trace is not None:
        # Design strengths first, so the reader immediately sees what the
        # whole check is based on before the forces/checks that use them.
        trace.section("Design strengths")
        trace.step("f_cd", fcd, "MPa", clause="EN 1992-1-1 §3.1.6",
                   expr="f_cd = α_cc·f_ck/γ_c",
                   subst=f"{alpha_cc:g}·{fck:g}/{gamma_c:g}")
        trace.step("f_yd", fyd, "MPa", expr="f_yd = f_yk/γ_s",
                   subst=f"{fyk:g}/{gamma_s:g}")
        trace.section("Inputs")
        trace.step("M_Ed", med, "kNm")
        trace.step("N_Ed", ned,
                   "kN (compression)" if ned >= 0 else "kN (tension)")
        trace.step("f_ck", fck, "MPa")
        trace.step("f_yk", fyk, "MPa")
        trace.step("d = h − d1", d, "m", expr="d = h − d1")
        trace.section("Flexure (EN 1992-1-1 §6.1)")
        trace.step("M_Eds", med_s, "kNm", clause="EN 1992-1-1 §6.1",
                   expr="M_Eds = |M_Ed| + N_Ed·(h/2 − d1)",
                   subst=f"{abs(med):.4g} + {ned:.4g}·{zs:.4g}")
        trace.step("μ", mu, "—", clause="EN 1992-1-1 §6.1",
                   expr="μ = M_Eds/(b·d²·f_cd)",
                   latex=r"\mu=\frac{M_{Eds}}{b\,d^2 f_{cd}}",
                   subst=f"{med_s_abs:.4g}/({b:g}·{d:.4g}²·{fcd:g})/1000")
        trace.step("μ_lim", mu_lim, "—", clause="EN 1992-1-1 §5.5",
                   note="doubly reinforced" if mu > mu_lim else "singly reinforced")
        trace.step("ω", omega, "—", expr="ω = 1 − √(1 − 2μ)",
                   latex=r"\omega=1-\sqrt{1-2\mu}")
        trace.step("x/d", x_d, "—", expr="x/d = 1.25·ω")
        trace.section("Reinforcement")
        trace.step("A_s,min", as_min, "cm²", clause="EN 1992-1-1 §9.2.1.1",
                   expr="A_s,min = max(0.26·f_ctm/f_yk, 0.0013)·b·d")
        trace.step("A_s1 (tension)", as1, "cm²", ok=True,
                   note=note or "governing tension steel")
        trace.step("A_s2 (compression)", as2, "cm²",
                   note="doubly reinforced" if mu > mu_lim else "not required")

    return {
        "As1": as1,
        "As2": as2,
        "As_min": as_min,
        "mu": mu,
        "omega": omega,
        "x_d": x_d,
        "med_s": med_s,
        "doubly": mu > mu_lim,
        "note": note,
        "method": "simplified",
    }


# ---------------------------------------------------------------------------
# Strain-compatibility design (any eccentricity, including compression-controlled)
# ---------------------------------------------------------------------------

_ES_MPA = 200_000.0          # reinforcing steel modulus [MPa] (EN 1992-1-1 §3.2.7)
_AS_MAX_RATIO = 0.04         # EN 1992-1-1 §9.2.1.1(3) / §9.5.2(3): As,max = 0.04 Ac


def _concrete_block(x, h, w, fcd, eps_c2, eps_cu2, n):
    """Force and moment of the parabola-rectangle concrete block.

    Closed-form integration (no fibres) of the EN 1992-1-1 §3.1.7 diagram over
    a rectangle of width ``w`` and depth ``h``, for a linear strain profile
    with neutral axis at ``x`` from the more compressed face. Above ``x = h``
    the profile pivots about the point at ``h(1 - eps_c2/eps_cu2)`` (strain
    ``eps_c2``), as in Figure 6.1 (pivot C).

    Returns ``(k, Fc, Mc)``: curvature [1/m], compression force [kN] and its
    moment about the section centroid [kNm] (positive = compression on the
    ``u = 0`` face).
    """
    if x <= h:
        k = eps_cu2 / x
    else:
        k = eps_c2 / (x - h * (1.0 - eps_c2 / eps_cu2))
    hh = min(x, h)
    u1 = x - eps_c2 / k                     # strain = eps_c2 here
    ua = min(max(u1, 0.0), hh)
    a = 1.0 - k * x / eps_c2                # t(u) = 1 - eps/eps_c2 = a + c*u
    c = k / eps_c2
    t_hh = max(a + c * hh, 0.0)
    t_a = max(a + c * ua, 0.0)
    i0 = (t_hh ** (n + 1) - t_a ** (n + 1)) / (c * (n + 1))
    j0 = ((t_hh ** (n + 2) - t_a ** (n + 2)) / (n + 2)
          - a * (t_hh ** (n + 1) - t_a ** (n + 1)) / (n + 1)) / (c * c)
    f_per_fcd = hh - i0                      # ∫ sigma/fcd du
    s_per_fcd = 0.5 * hh * hh - j0           # ∫ sigma/fcd * u du
    fc = fcd * w * f_per_fcd * 1000.0
    mc = fcd * w * (0.5 * h * f_per_fcd - s_per_fcd) * 1000.0
    return k, fc, mc


def _steel_stress(k, x, u, fyd):
    """Steel stress [MPa, compression positive] at depth ``u`` from the face."""
    return max(-fyd, min(fyd, _ES_MPA * k * (x - u)))


def calc_asl_nm_strain(
    b: float,
    h: float,
    d1: float,
    d2: float,
    med: float,
    ned: float,
    fck: float,
    fyk: float,
    gamma_c: float = GammaC,
    gamma_s: float = GammaS,
    alpha_cc: float = 1.0,
    trace=None,
) -> dict:
    """Design a rectangular section for M-N by strain compatibility.

    Same inputs and result keys as :func:`calc_asl_nm`, but valid for **any**
    eccentricity, including the compression-controlled range where the
    simplified method breaks down (there it over-designs by a factor that grows
    with N, e.g. 2-3x for small eccentricities).

    Method. The parabola-rectangle diagram (EN 1992-1-1 §3.1.7, closed-form
    integrals) and an elastic-perfectly-plastic steel (``f_yd``, no hardening)
    give, for a strain profile fixed by the neutral-axis depth ``x``, the
    concrete force/moment and the steel stresses ``s1``, ``s2``. With those
    known, equilibrium in N and M is **linear** in the two steel areas, so for
    each ``x`` the pair ``(As1, As2)`` follows from a 2x2 solve; the design is
    the ``x`` that minimises ``As1 + As2`` with both non-negative and
    ``As1 >= As_min``. A section already adequate with ``As1 = As_min`` and
    ``As2 = 0`` is returned as such.

    The tension face is the one selected by the sign of ``med`` (positive =
    tension at the bottom, as in :func:`calc_asl_nm`); ``As1`` is the steel on
    that face and ``As2`` on the opposite one. ``ned`` is compression-positive.

    No limit is placed on the neutral-axis depth: the ``x/d <= 0.45`` bound of
    §5.5(4) exists for beam ductility/redistribution and the simplified method
    applies it; with significant axial compression it does not govern.

    Returns the :func:`calc_asl_nm` keys (``mu`` and ``omega`` are ``None``:
    the stress-block quantities do not exist here; ``med_s`` is ``med``) plus
    ``x`` [m] and ``feasible``; ``note`` reports when the total steel exceeds
    the 4 % ``A_c`` limit of §9.2.1.1(3), in which case the section must be
    enlarged.
    """
    d = h - d1
    if d <= 0:
        msg = "Effective depth d = h - d1 must be positive."
        raise ValueError(msg)

    conc = Concrete.from_fck(fck)
    eps_c2, eps_cu2, n_exp = conc.eps_c2 / 1000.0, conc.eps_cu2 / 1000.0, conc.n
    fcd = alpha_cc * fck / gamma_c
    fyd = fyk / gamma_s

    m_abs = abs(med)
    u1, u2 = h - d1, d2                # depth of tension / compression steel
    z1 = h / 2.0 - u1                  # lever arms about the centroid [m]
    z2 = h / 2.0 - u2
    fctm = _fctm(fck)
    as_min = max(0.26 * fctm / fyk, 0.0013) * b * d * 10000.0     # [cm2]

    def state(x):
        k, fc, mc = _concrete_block(x, h, b, fcd, eps_c2, eps_cu2, n_exp)
        return (fc, mc, _steel_stress(k, x, u1, fyd),
                _steel_stress(k, x, u2, fyd))

    def forces(x):
        """Steel forces P1, P2 [kN] (on top of As_min) and stresses at profile x."""
        fc, mc, s1, s2 = state(x)
        p1_min = 0.1 * as_min * s1                       # [kN]
        nr = ned - fc - p1_min
        mr = m_abs - mc - p1_min * z1
        p2 = (mr - nr * z1) / (z2 - z1)
        return nr - p2, p2, s1, s2

    def areas(p1, p2, s1, s2):
        """(a1, a2) [cm2] carrying forces p1, p2; None where a steel is unstressed."""
        if abs(s1) < 1.0e-9 or abs(s2) < 1.0e-9:
            return None
        return p1 / (0.1 * s1), p2 / (0.1 * s2)

    def capacity_ok(as1, as2):
        """Is (N, |M|) inside the M-N diagram of this layout?"""
        lo, hi = 1.0e-4 * h, 500.0 * h
        for _ in range(80):
            mid = math.sqrt(lo * hi)
            fc, _mc, s1, s2 = state(mid)
            if fc + 0.1 * (as1 * s1 + as2 * s2) < ned:
                lo = mid
            else:
                hi = mid
        fc, mc, s1, s2 = state(hi)
        if abs(fc + 0.1 * (as1 * s1 + as2 * s2) - ned) > 1.0e-3 * max(abs(ned), 1.0) + 1.0e-6:
            return False, hi
        mrd = mc + 0.1 * (as1 * s1 * z1 + as2 * s2 * z2)
        return mrd >= m_abs - 1.0e-9, hi

    def root(fun, lo, hi):
        """Bisection of a continuous ``fun`` that changes sign on [lo, hi]."""
        flo = fun(lo)
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            fm = fun(mid)
            if (fm > 0.0) == (flo > 0.0):
                lo, flo = mid, fm
            else:
                hi = mid
        return 0.5 * (lo + hi)

    ok, x_sol = capacity_ok(as_min, 0.0)
    as1, as2 = as_min, 0.0
    feasible = True
    if not ok:
        # Candidate designs, each an exact equilibrium of (N, M) at some profile
        # x with a1, a2 >= 0. The minimum of a1 + a2 lies on a boundary of the
        # feasible set (a1 = 0 or a2 = 0, i.e. P1 = 0 or P2 = 0: continuous in x,
        # no division by the steel stress) or in its interior; so collect the
        # roots of P1 and P2 plus every feasible grid point, and keep the best.
        x_lo, x_hi, n_grid = 0.005 * h, 200.0 * h, 400
        ratio = (x_hi / x_lo) ** (1.0 / (n_grid - 1))
        xs = [x_lo * ratio ** i for i in range(n_grid)]
        fs = [forces(x) for x in xs]
        best = None                                      # (total, a1, a2, x)

        def consider(x):
            nonlocal best
            p1, p2, s1, s2 = forces(x)
            ar = areas(p1, p2, s1, s2)
            if ar is None:
                return
            a1_, a2_ = ar
            if a1_ < -1.0e-6 or a2_ < -1.0e-6:
                return
            a1_ = a1_ if a1_ > 1.0e-9 else 0.0           # drop round-off
            a2_ = a2_ if a2_ > 1.0e-9 else 0.0
            if best is None or a1_ + a2_ < best[0]:
                best = (a1_ + a2_, a1_, a2_, x)

        for i, x in enumerate(xs):
            consider(x)
            if i == 0:
                continue
            for idx in (0, 1):                           # P1 and P2 sign changes
                if (fs[i - 1][idx] > 0.0) != (fs[i][idx] > 0.0):
                    consider(root(lambda t, j=idx: forces(t)[j], xs[i - 1], x))
        if best is None:
            feasible = False
            x_sol = xs[0]
        else:
            _tot, a1, a2, x_sol = best
            as1, as2 = as_min + a1, a2
            ok2, _ = capacity_ok(as1, as2)
            if not ok2:                                  # numerical guard: safe side
                as1, as2 = as1 * 1.001, as2 * 1.001 + 1.0e-6
    note = ""
    if not feasible:
        note = "no strain-compatibility solution: enlarge the section"
    elif as1 + as2 > _AS_MAX_RATIO * b * h * 1.0e4:
        note = ("total steel exceeds 4% Ac (EN 1992-1-1 9.2.1.1(3)): "
                "enlarge the section")

    if trace is not None:
        trace.section("Flexure with axial force — strain compatibility "
                      "(EN 1992-1-1 §6.1)")
        trace.step("f_cd", fcd, "MPa", clause="EN 1992-1-1 §3.1.6")
        trace.step("f_yd", fyd, "MPa")
        trace.step("M_Ed", med, "kNm")
        trace.step("N_Ed", ned, "kN (compression)" if ned >= 0 else "kN (tension)")
        trace.step("x (neutral axis)", x_sol, "m", clause="EN 1992-1-1 §3.1.7",
                   note="parabola-rectangle diagram, minimum total steel")
        trace.step("A_s,min", as_min, "cm²", clause="EN 1992-1-1 §9.2.1.1")
        trace.step("A_s1 (tension face)", as1, "cm²", ok=feasible)
        trace.step("A_s2 (opposite face)", as2, "cm²")

    return {
        "As1": as1,
        "As2": as2,
        "As_min": as_min,
        "mu": None,
        "omega": None,
        "x_d": x_sol / d,
        "x": x_sol,
        "med_s": med,
        "doubly": as2 > 0.0,
        "feasible": feasible,
        "note": note,
        "method": "strain",
    }


def _fctm(fck: float) -> float:
    """Mean axial tensile strength fctm [MPa] (EN 1992-1-1 Table 3.1)."""
    if fck <= 50.0:
        return 0.30 * fck ** (2.0 / 3.0)
    fcm = fck + 8.0
    return 2.12 * math.log(1.0 + fcm / 10.0)


def design_rcbeam_nm(
    beam,
    med: float,
    ned: float,
    iprint: bool = False,
) -> dict:
    """Convenience wrapper designing an :class:`RCBeam` for M and N.

    Args:
        beam (RCBeam): beam object carrying geometry and materials.
        med (float): design bending moment [kNm].
        ned (float): design axial force [kN], compression positive.
        iprint (bool, optional): print a summary. Defaults to False.

    Returns:
        dict: see :func:`calc_asl_nm`.

    """
    return calc_asl_nm(
        beam.b, beam.h, beam.at, beam.ac, med, ned,
        beam.fck, beam.fyk, beam.gammac, beam.gammas, iprint=iprint,
    )
