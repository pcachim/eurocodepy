# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Detailing of members — **EN 1992-1-1:2023** Clause 12.

Minimum reinforcement (12.2), beams (12.3, Table 12.1), slabs (12.4, Table 12.2),
punching shear and integrity reinforcement (12.5), columns (12.6, Table 12.3)
and walls/deep beams (12.7, Table 12.4). The tables are NDPs: the values are
those of the Eurocode (``Editions.ec2["2023"].detailing`` in the database); the
functions that use them take ``annex=`` (a country code, see
:mod:`eurocodepy.annex`) to apply the values of a National Annex.

Units: lengths and areas in **m** / **m²** (bar diameters, ``d_lower`` and the
``d`` of ``φw,max`` in **mm** where stated), strengths in **MPa**, forces in
**kN**, moments in **kNm**, ``cot`` of angles dimensionless, angles in degrees.
"""

import math

from eurocodepy import dbase


def _ndp(group: str, annex: str | None) -> dict:
    """Return the NDP values of ``group`` (Tables 12.1-12.4), with the national annex if any."""
    return dbase.get_edition_params("ec2", "detailing", "2023", annex)[group]


# ── 12.2 Minimum reinforcement rules ────────────────────────────────────────

_DUCTILITY_RHO_W = {"A": 1.0, "B": 0.9, "C": 0.8}      # 12.2(4)
_K_DC = {"A": 1.3, "B": 1.1, "C": 1.0}                 # 12.2(3)
_AXIAL_LIMIT = 0.5                                      # 12.2(2)a): N < 0,5·Ac·fcd


def _ductility(ductility: str) -> str:
    d = ductility.upper()
    if d not in _K_DC:
        msg = f"ductility must be 'A', 'B' or 'C', got '{ductility}'"
        raise ValueError(msg)
    return d


def cracking_check_needed(n_ed_min: float, a_c: float, f_cd: float) -> bool:
    """Return ``True`` if Eq. (12.1) applies: compression ``|NEd,min| < 0,5·Ac·fcd``.

    ``n_ed_min`` [kN] is positive in tension; compression is negative.
    """
    return -n_ed_min < _AXIAL_LIMIT * a_c * f_cd * 1000.0


def calc_m_cr_rect(b: float, h: float, f_ctm: float, n_ed: float = 0.0) -> float:
    """Return the cracking moment ``Mcr(NEd)`` of a rectangular section [kNm], 12.2(2)a).

    Linear stresses, ``fctm`` at the extreme fibre, steel neglected:
    ``(fctm − NEd/A)·b·h²/6`` (``n_ed`` [kN] positive in tension).
    """
    return (f_ctm - n_ed / (b * h) / 1000.0) * b * h**2 / 6.0 * 1000.0


def calc_as_min_tension(a_c: float, f_ctm: float, f_yk: float) -> float:
    """Return ``As,min = Ac·fctm/fyk`` of a member in pure tension [m²], Eq. (12.2)."""
    return a_c * f_ctm / f_yk


def calc_k_dc(ductility: str = "B") -> float:
    """Return ``kdc`` of Eq. (12.3): 1,3 (class A), 1,1 (B), 1,0 (C)."""
    return _K_DC[_ductility(ductility)]


def calc_m_rd_min(m_ed: float, ductility: str = "B") -> float:
    """Return the resistance ``MRd,min = kdc·MEd`` [kNm] that avoids sudden collapse, Eq. (12.3).

    For ``MEd < Mcr(NEd)`` in statically determinate members; the area need not
    exceed that of Eq. (12.1).
    """
    return calc_k_dc(ductility) * abs(m_ed)


def calc_rho_w_min(f_ck: float, f_yk: float, ductility: str = "B") -> float:
    """Return ``ρw,min`` of Eq. (12.4): ``0,08·√fck/fyk``, −10 % for class B, −20 % for C."""
    return 0.08 * math.sqrt(f_ck) / f_yk * _DUCTILITY_RHO_W[_ductility(ductility)]


def calc_asw_min_s(f_ck: float, f_yk: float, b_w: float, alpha_w: float = 90.0,
                   ductility: str = "B") -> float:
    """Return the minimum shear reinforcement ``Asw,min/s`` [m²/m], Eq. (12.4).

    ``ρw,min·bw·sin α`` with ``bw`` [m] and ``alpha_w`` the angle of the shear
    reinforcement [°].
    """
    return calc_rho_w_min(f_ck, f_yk, ductility) * b_w * math.sin(math.radians(alpha_w))


def calc_sigma_sd_min(f_yd: float, a_s_min: float, a_s: float) -> float:
    """Return the design stress ``σsd = fyd·As,min/As`` [MPa] for anchoring the minimum reinforcement, 12.2(6)."""
    return f_yd * a_s_min / a_s


# ── 12.3 Beams ──────────────────────────────────────────────────────────────

def calc_shift_length(z: float, cot: float, alpha_w: float = 90.0, *,
                      shear_reinforcement: bool = True, d: float | None = None) -> float:
    """Return the shift ``al`` of the moment curve [m], Eqs. (12.5)/(12.6).

    ``z·(cot θ − cot α)/2`` with shear reinforcement; ``d`` (``d`` must be given)
    without it.
    """
    if not shear_reinforcement:
        if d is None:
            msg = "d is needed without shear reinforcement (Eq. 12.6)"
            raise ValueError(msg)
        return d
    cot_a = 0.0 if alpha_w == 90.0 else 1.0 / math.tan(math.radians(alpha_w))  # noqa: PLR2004
    return z * (cot - cot_a) / 2.0


def calc_bent_up_anchorage(l_bd: float, *, tension_zone: bool) -> float:
    """Return the anchorage length of a bent-up bar [m], 12.3.2(4): 1,3·lbd (tension) / 0,7·lbd."""
    return (1.3 if tension_zone else 0.7) * l_bd


def beam_max_spacings(d: float, alpha_w: float = 90.0, annex: str | None = None) -> dict:
    """Return the maximum spacings of Table 12.1 [m] (rows 5-7).

    ``s_l_max = 0,75·d·(1 + cot α)`` (stirrups), ``s_bu_max = 0,6·d·(1 + cot α)``
    (bent-up bars) and ``s_tr_max = min(0,75·d, 0,6 m)`` (legs across the section).
    """
    n = _ndp("beams", annex)
    cot_a = 0.0 if alpha_w == 90.0 else 1.0 / math.tan(math.radians(alpha_w))  # noqa: PLR2004
    return {"s_l_max": n["s_l_max"] * d * (1.0 + cot_a),
            "s_bu_max": n["s_bu_max"] * d * (1.0 + cot_a),
            "s_tr_max": min(n["s_tr_max"] * d, n["s_tr_max_limit"])}


def beam_min_stirrups(rho_w_req: float, *, torsion: bool = False,
                      annex: str | None = None) -> float:
    """Return the minimum ratio of stirrups ``ρw,stir`` (Table 12.1, rows 8-9).

    ``0,5·ρw,req`` for shear (unforeseen effects, e.g. compatibility torsion);
    ``0,2·ρw,req`` for torsion in the form of closed stirrups.
    """
    n = _ndp("beams", annex)
    return n["rho_w_stir_torsion" if torsion else "rho_w_stir_shear"] * rho_w_req


def torsion_stirrup_max_spacing(u: float, b: float, h: float,
                                annex: str | None = None) -> float:
    """Return ``s_stir,max = u/8 ≤ min(b, h)`` [m] of torsion stirrups (Table 12.1, row 10)."""
    return min(u / _ndp("beams", annex)["s_stir_max_u_div"], b, h)


def beam_min_support_reinforcement(a_s_req_span: float, annex: str | None = None) -> float:
    """Return the minimum bottom reinforcement at supports ``0,25·As,req,span`` (Table 12.1, rows 3-4)."""
    return _ndp("beams", annex)["support_bottom"] * a_s_req_span


# ── 12.4 Slabs ──────────────────────────────────────────────────────────────

def slab_max_spacings(h: float, d: float, alpha_w: float = 90.0,
                      annex: str | None = None) -> dict:
    """Return the maximum spacings of Table 12.2 [m].

    ``s_slab_max = min(3·h, 0,4 m)`` (bars in tension), ``s_l_max = 0,75·d·(1 + cot α)``
    (stirrups), ``s_bu_max = d`` (bent-up bars), ``s_tr_max = 1,5·d`` (shear legs).
    """
    n = _ndp("slabs", annex)
    cot_a = 0.0 if alpha_w == 90.0 else 1.0 / math.tan(math.radians(alpha_w))  # noqa: PLR2004
    return {"s_slab_max": min(n["s_slab_max_h"] * h, n["s_slab_max_limit"]),
            "s_l_max": n["s_l_max"] * d * (1.0 + cot_a),
            "s_bu_max": n["s_bu_max"] * d, "s_tr_max": n["s_tr_max"] * d}


def slab_min_reinforcement(a_s_req_span: float, annex: str | None = None) -> dict:
    """Return the minimum areas relative to ``As,req,span`` (Table 12.2, rows 3-6).

    ``secondary`` 0,2·As,req,span, ``inner_support``/``end_support_bottom``/
    ``end_support_top`` 0,25·As,req,span (the top one not less than ``As,min`` of 12.2(2)).
    """
    n = _ndp("slabs", annex)
    return {k: n[k] * a_s_req_span for k in
            ("secondary", "inner_support", "end_support_bottom", "end_support_top")}


def slab_edge_reinforcement_length(h: float, l_bd: float) -> float:
    """Return the length of the edge reinforcement ``≥ max(2·h, lbd)`` [m], Figure 12.4."""
    return max(2.0 * h, l_bd)


def slab_min_depth_for_shear_reinforcement(*, bent_up: bool = False) -> float:
    """Return the minimum slab depth with shear reinforcement [m], 12.4.2(2): 0,2 (stirrups, headed bars) or 0,16 (bent-up)."""
    return 0.16 if bent_up else 0.2


def slab_shear_reinforcement_only_bent_up_ok(tau_ed: float, f_cd: float,
                                             alpha: float = 90.0) -> bool:
    """Return ``True`` if the shear reinforcement may be only bent-up bars or assemblies, 12.4.2(5).

    ``τEd ≤ 0,08·fcd`` (vertical) and ``≤ 0,16·fcd`` (45°), linear in between.
    """
    a = min(max(alpha, 45.0), 90.0)
    limit = 0.16 + (0.08 - 0.16) * (a - 45.0) / 45.0
    return tau_ed <= limit * f_cd


# ── 12.5 Slab-column connections ────────────────────────────────────────────

_PHI_W_MAX = {"single_leg": 10.0, "closed": 11.0, "bent_up": 16.0}


def calc_phi_w_max(d: float, kind: str = "closed") -> float:
    """Return the maximum bar diameter of a punching-shear leg [mm], Eqs. (12.7)-(12.9).

    ``d`` in mm. ``kind``: ``"single_leg"`` (single-leg links, open stirrups, 10),
    ``"closed"`` (closed stirrups or similar anchorage, 11) or ``"bent_up"``
    (bent-up bars and headed bars, 16): ``k·√(d/200)``.
    """
    if kind not in _PHI_W_MAX:
        msg = f"kind must be one of {tuple(_PHI_W_MAX)}, got '{kind}'"
        raise ValueError(msg)
    return _PHI_W_MAX[kind] * math.sqrt(d / 200.0)


def punching_reinforcement_spacing(d_v: float, *, column_base: bool = False) -> dict:
    """Return the spacing limits of punching shear reinforcement [m], 12.5.1(2) and Figure 12.7.

    ``tangential_max`` ``1,5·dv``; ``tangential_first_perimeter_max`` (within
    ``2·dv`` of the column edge) ``0,75·dv`` for flat slabs or ``0,5·dv`` for
    column bases; ``radial_max`` the same as that first value; first
    perimeter at ``0,3-0,5·dv`` (flat slabs) or ``0,2-0,3·dv`` (column bases)
    from the column face (Figure 12.7 a, b, stirrups/studs).
    """
    f = 0.5 if column_base else 0.75
    first = (0.2, 0.3) if column_base else (0.3, 0.5)
    return {"tangential_max": 1.5 * d_v, "tangential_first_perimeter_max": f * d_v,
            "radial_max": f * d_v,
            "first_perimeter_min": first[0] * d_v, "first_perimeter_max": first[1] * d_v}


def calc_vrd_int(a_s_int: float, f_yd: float, ductility: str = "B") -> float:
    """Return the integrity-reinforcement resistance ``VRd,int`` [kN], Eq. (12.10).

    ``ΣAs,int·fyd·kint`` with ``kint`` 0,37 (class B) or 0,49 (class C); ``a_s_int`` in m².
    """
    d = _ductility(ductility)
    if d == "A":
        msg = "integrity bars must be of ductility class B or C (12.5.2(1))"
        raise ValueError(msg)
    return a_s_int * f_yd * (0.37 if d == "B" else 0.49) * 1000.0


def calc_vrd_w_int(rho_w: float, f_ywd: float, b_05: float, d_v: float) -> float:
    """Return ``VRd,w,int = ρw·fywd·b0,5·dv`` [kN], Eq. (12.11)."""
    return rho_w * f_ywd * b_05 * d_v * 1000.0


def calc_vrd_hog(n_hog: int, f_ck: float, gamma_c: float, phi: float, s: float,
                 c: float) -> float:
    """Return the hogging-bar contribution ``VRd,hog`` [kN], Eq. (12.12).

    ``nhog·√fck/γC·φ·bef,hog``, ``bef,hog = min(s − φ, 6φ, 4c)``; ``γC`` of the
    accidental situation; ``phi``, ``s`` and ``c`` in m.
    """
    b_ef = min(s - phi, 6.0 * phi, 4.0 * c)
    return n_hog * math.sqrt(f_ck) / gamma_c * phi * b_ef * 1000.0


# ── 12.6 Columns ────────────────────────────────────────────────────────────

_EVEN_BARS_CIRCULAR = 6


def column_min_longitudinal(n_ed: float, f_yd: float, a_c: float, *,
                            all_prestressed: bool = False,
                            annex: str | None = None) -> float:
    """Return ``As,min = max(0,1·NEd/fyd, 0,002·Ac)`` [m²], Table 12.3 row 1.

    ``n_ed`` [kN] compression positive here. The ``0,1·NEd/fyd`` limit is ignored
    when all the longitudinal reinforcement is prestressed.
    """
    n = _ndp("columns", annex)
    a_n = 0.0 if all_prestressed else n["as_min_n"] * n_ed / f_yd / 1000.0
    return max(a_n, n["as_min_ac"] * a_c)


def column_min_bars(shape: str = "polygonal") -> dict:
    """Return the minimum number of longitudinal bars (Table 12.3 row 2).

    ``polygonal``: one at each corner, spacing ≤ 0,4 m; ``circular``: 6, evenly
    distributed, spacing ≤ 0,4 m.
    """
    if shape not in ("polygonal", "circular"):
        msg = "shape must be 'polygonal' or 'circular'"
        raise ValueError(msg)
    return {"min_bars": None if shape == "polygonal" else _EVEN_BARS_CIRCULAR,
            "one_per_corner": shape == "polygonal", "max_spacing": 0.4}


def column_max_stirrup_spacing(phi_l_max: float, h: float, b: float, *,
                               bars_in_resistance: bool = True,
                               prestressed_only: bool = False,
                               annex: str | None = None) -> dict:
    """Return the maximum spacing of transverse reinforcement [m], Table 12.3 row 3.

    ``phi_l_max`` [mm] is the largest longitudinal bar diameter. ``intermediate``:
    ``min(20·φl,max, h, b, 0,3 m)``, or ``min(h, b, 0,4 m)`` when the bars are not
    accounted for in the resistance; ``end_regions`` and ``laps`` ``0,6·s_max,col``
    (end regions over a length ``max(h, b)``; laps where φl ≥ 14 mm). With all
    bars prestressed ``0,3 m`` becomes ``min(h, b, 0,3 m)`` only.
    """
    n = _ndp("columns", annex)
    if bars_in_resistance:
        s = min(n["s_phi"] * phi_l_max / 1000.0, h, b, n["s_limit"])
        if prestressed_only:
            s = min(h, b, n["s_limit"])
    else:
        s = min(h, b, n["s_limit_unused"])
    return {"intermediate": s, "end_regions": n["end_region_factor"] * s,
            "end_region_length": max(h, b), "laps": n["lap_factor"] * s}


def column_min_stirrup_diameter(phi_l_max: float, annex: str | None = None) -> float:
    """Return the minimum diameter of transverse reinforcement ``0,25·φl,max`` [mm], Table 12.3 row 4."""
    return _ndp("columns", annex)["stirrup_phi"] * phi_l_max


def column_min_confinement_stress(f_cd: float, k: float | None = None,
                                  annex: str | None = None) -> float:
    """Return the minimum confinement ``σc2d ≥ k·fcd`` [MPa] of columns with fck > 50 MPa, Table 12.3 note d."""
    return (_ndp("columns", annex)["k_confinement"] if k is None else k) * f_cd


def column_restraint_distance_ok(distance: float, strain_permille: float) -> bool:
    """Return ``True`` if a bar in the compression zone is within 150 mm of a restrained bar (12.6(3)).

    Bars with compressive strain ≤ 2 ‰ need no check; ``distance`` in m.
    """
    return strain_permille <= 2.0 or distance <= 0.15  # noqa: PLR2004


# ── 12.7 Walls and deep beams ───────────────────────────────────────────────

def wall_min_vertical(a_c: float, f_ctm: float, f_yk: float, *,
                      in_plane_loaded: bool = True, annex: str | None = None) -> float:
    """Return ``As,min,v`` of each surface [m²], Table 12.4 row 1.

    ``0,25·Ac·fctm/fyk`` where the member carries in-plane normal and shear
    stresses (designed by 8.5 or Annex G); ``0,001·Ac`` when loaded only by
    vertical in-plane compression and out-of-plane bending.
    """
    n = _ndp("walls", annex)
    return (n["as_v_in_plane"] * a_c * f_ctm / f_yk if in_plane_loaded
            else n["as_v_out_of_plane"] * a_c)


def wall_min_horizontal(a_c: float, f_ctm: float, f_yk: float, a_s_v: float, *,
                        in_plane_loaded: bool = True, annex: str | None = None) -> float:
    """Return ``As,min,h`` of each face [m²], Table 12.4 row 2: ``0,25·Ac·fctm/fyk`` or ``0,25·As,v``."""
    n = _ndp("walls", annex)
    return (n["as_h_in_plane"] * a_c * f_ctm / f_yk if in_plane_loaded
            else n["as_h_out_of_plane"] * a_s_v)


def wall_max_spacings(h: float, annex: str | None = None) -> dict:
    """Return the maximum spacings [m] of Table 12.4: vertical ``min(3·h, 0,4 m)``, horizontal ``0,4 m``."""
    n = _ndp("walls", annex)
    return {"vertical": min(n["s_v_h"] * h, n["s_v_limit"]), "horizontal": n["s_h_limit"]}


def wall_orthogonal_links_required(a_s_v: float, a_c: float,
                                   annex: str | None = None) -> bool:
    """Return ``True`` when 12.7(3) / Table 12.4 row 5 asks for orthogonal links (``As,v > 0,02·Ac``, in compression)."""
    return a_s_v > _ndp("walls", annex)["orthogonal_as_ratio"] * a_c

