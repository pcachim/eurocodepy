# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 3 cross-section classification and Class-4 effective properties.

This module implements two closely related tasks of EN 1993-1-1 / EN 1993-1-5:

1. **Classification** (EN 1993-1-1 §5.5 and Table 5.2) — determine the class
   (1 to 4) of a steel cross-section from the width-to-thickness ratios of its
   compression parts, for pure compression, pure bending and combined axial
   force + bending (through the plastic ratio ``alpha`` and the elastic
   ratio ``psi``). I/H, RHS/SHS and CHS sections are supported.

2. **Class-4 effective properties** (EN 1993-1-5 §4.4) — for a Class-4
   section, reduce the slender compression parts with the effective-width
   method and return the effective area ``A_eff`` (uniform compression) and the
   effective section modulus ``W_eff`` (bending), together with the shift of the
   centroid ``e_N`` that a reduced section produces under axial load.

Design conventions
------------------
* ``fy`` is the yield strength in **N/mm² (MPa)**; ``epsilon = sqrt(235/fy)``.
* Cross-section geometry is read from the eurocodepy profile objects
  (``ProfileI`` / ``ProfileRHS`` / ``ProfileSHS`` / ``ProfileCHS``) whose
  dimensions are stored in **cm**; internally everything is converted to mm,
  mm², mm³ and mm⁴.
* Axial force ``N_Ed`` is in **kN, compression positive**; bending ``M_Ed`` is
  in **kNm**. Classification uses the magnitude of the bending stress on the
  compression side, so only the sign of ``N_Ed`` matters.

The classification part functions (:func:`classify_internal_part`,
:func:`classify_outstand_part`, :func:`classify_chs_part`) are pure and take
dimensionless ratios, so they can be reused directly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum

# ── constants ───────────────────────────────────────────────────────────────

REF_FY = 235.0  # reference yield strength [N/mm²] for epsilon


class SectionClass(IntEnum):
    """Eurocode 3 cross-section class (1 = plastic … 4 = slender)."""

    CLASS_1 = 1
    CLASS_2 = 2
    CLASS_3 = 3
    CLASS_4 = 4


def epsilon(fy: float) -> float:
    """Material factor ``ε = sqrt(235 / fy)`` (EN 1993-1-1 Table 5.2).

    Args:
        fy: Yield strength [N/mm²].

    Returns:
        The dimensionless coefficient ε.

    """
    if fy <= 0.0:
        msg = "fy must be positive (N/mm²)."
        raise ValueError(msg)
    return math.sqrt(REF_FY / fy)


# ── part classification (EN 1993-1-1 Table 5.2) ─────────────────────────────

def classify_internal_part(c_over_t: float, eps: float,
                           psi: float = 1.0, alpha: float = 1.0) -> SectionClass:
    """Classify an *internal* compression part (web, box wall) — Table 5.2/1.

    Class 1 and 2 limits use the plastic compressed fraction ``alpha`` (0…1),
    Class 3 uses the elastic end-stress ratio ``psi = σ2/σ1`` (compression
    positive: +1 uniform compression, −1 pure bending).

    Args:
        c_over_t: Flat width-to-thickness ratio c/t of the part.
        eps: Material factor ε.
        psi: Elastic end-stress ratio σ2/σ1 of the part.
        alpha: Plastic compressed length fraction of the part (0…1).

    Returns:
        The :class:`SectionClass` of the part.

    """
    a = min(max(alpha, 1.0e-9), 1.0)
    # Class 1
    limit_1 = 396.0 * eps / (13.0 * a - 1.0) if a > 0.5 else 36.0 * eps / a
    if c_over_t <= limit_1:
        return SectionClass.CLASS_1
    # Class 2
    limit_2 = 456.0 * eps / (13.0 * a - 1.0) if a > 0.5 else 41.5 * eps / a
    if c_over_t <= limit_2:
        return SectionClass.CLASS_2
    # Class 3 (elastic stress distribution)
    if psi > -1.0:
        limit_3 = 42.0 * eps / (0.67 + 0.33 * psi)
    else:
        limit_3 = 62.0 * eps * (1.0 - psi) * math.sqrt(-psi)
    if c_over_t <= limit_3:
        return SectionClass.CLASS_3
    return SectionClass.CLASS_4


def classify_outstand_part(c_over_t: float, eps: float,
                           psi: float = 1.0, alpha: float = 1.0,
                           tip_in_compression: bool = True) -> SectionClass:
    """Classify an *outstand* flange — Table 5.2/2 (general stress gradient).

    For uniform compression (``psi = 1, alpha = 1``) the well-known limits
    9ε / 10ε / 14ε are recovered. For a stress gradient the Class 1/2 limits use
    the plastic compressed fraction ``alpha`` (with a different form depending on
    whether the free tip is the more compressed edge), and the Class 3 limit is
    ``21ε·√kσ`` with kσ from EN 1993-1-5 Table 4.2.

    Args:
        c_over_t: Flat outstand width-to-thickness ratio c/t.
        eps: Material factor ε.
        psi: Elastic end-stress ratio σ2/σ1 across the outstand.
        alpha: Plastic compressed length fraction of the outstand (0…1).
        tip_in_compression: True if the free edge (tip) is the more compressed
            one; False if the maximum compression is at the supported (web) edge.

    Returns:
        The :class:`SectionClass` of the outstand.

    """
    a = min(max(alpha, 1.0e-9), 1.0)
    if tip_in_compression:
        limit_1 = 9.0 * eps / a
        limit_2 = 10.0 * eps / a
    else:
        limit_1 = 9.0 * eps / (a * math.sqrt(a))
        limit_2 = 10.0 * eps / (a * math.sqrt(a))
    if c_over_t <= limit_1:
        return SectionClass.CLASS_1
    if c_over_t <= limit_2:
        return SectionClass.CLASS_2
    # Class 3: uniform compression keeps the tabulated 14ε; a gradient uses kσ.
    if psi >= 1.0 - 1.0e-9:
        limit_3 = 14.0 * eps
    else:
        limit_3 = 21.0 * eps * math.sqrt(k_sigma_outstand(psi, tip_in_compression))
    if c_over_t <= limit_3:
        return SectionClass.CLASS_3
    return SectionClass.CLASS_4


def classify_chs_part(d_over_t: float, eps: float) -> SectionClass:
    """Classify a circular hollow section (tube) — Table 5.2/3.

    Args:
        d_over_t: Outer-diameter-to-thickness ratio d/t.
        eps: Material factor ε.

    Returns:
        The :class:`SectionClass` of the tube.

    """
    e2 = eps * eps
    if d_over_t <= 50.0 * e2:
        return SectionClass.CLASS_1
    if d_over_t <= 70.0 * e2:
        return SectionClass.CLASS_2
    if d_over_t <= 90.0 * e2:
        return SectionClass.CLASS_3
    return SectionClass.CLASS_4


# ── geometry extraction ─────────────────────────────────────────────────────

@dataclass
class _Geometry:
    """Cross-section geometry normalised to mm (dimensions), mm² (area),
    mm⁴ (inertia) — an internal, unit-consistent view of a profile.
    """

    kind: str            # 'I', 'RHS', 'SHS', 'CHS'
    h: float             # overall depth [mm]
    b: float             # overall width [mm]
    tw: float            # web / side-wall thickness [mm]
    tf: float            # flange / top-wall thickness [mm]
    r: float             # corner / root radius [mm]
    area: float          # gross area [mm²]
    iy: float            # second moment about y (major) [mm⁴]
    iz: float            # second moment about z (minor) [mm⁴]
    c_web: float         # clear (flat) web depth [mm]
    c_flange: float      # clear (flat) flange outstand / top-wall width [mm]


def _cm(x: float) -> float:
    return float(x) * 10.0          # cm → mm


def _to_geometry(section) -> _Geometry:  # ruff: ignore[missing-type-function-argument]
    """Build a unit-consistent :class:`_Geometry` from a eurocodepy profile.

    The profile dimensions are in cm; areas in cm², inertias in cm⁴. A small
    duck-typed protocol is used (``.type`` plus ``h, b, tw, tf, r, A, Iy, Iz``)
    so any object exposing those attributes works, which keeps this module free
    of a hard import on the (heavier) materials module.
    """
    kind = getattr(section, "type", "").upper()
    h = _cm(section.h)
    b = _cm(section.b)
    tw = _cm(section.tw)
    tf = _cm(section.tf)
    r = _cm(getattr(section, "r", 0.0) or 0.0)
    area = float(getattr(section, "A", 0.0)) * 100.0          # cm² → mm²
    iy = float(getattr(section, "Iy", 0.0)) * 1.0e4           # cm⁴ → mm⁴
    iz = float(getattr(section, "Iz", 0.0)) * 1.0e4

    if kind == "I":
        c_web = h - 2.0 * tf - 2.0 * r
        c_flange = (b - tw - 2.0 * r) / 2.0
    elif kind in ("RHS", "SHS"):
        # Flat width of a hollow-section wall: overall minus the two external
        # corner radii; if the radius is unknown, EN 1993-1-1 allows c = b − 3t.
        c_web = (h - 2.0 * r) if r > 0.0 else (h - 3.0 * tw)
        c_flange = (b - 2.0 * r) if r > 0.0 else (b - 3.0 * tf)
    elif kind == "CHS":
        c_web = c_flange = 0.0                                # d/t handled apart
    else:
        msg = f"Unsupported section type for classification: {kind!r}"
        raise ValueError(msg)

    return _Geometry(kind=kind, h=h, b=b, tw=tw, tf=tf, r=r,
                     area=area, iy=iy, iz=iz,
                     c_web=c_web, c_flange=c_flange)


# ── web stress state under N + M (major axis) ───────────────────────────────

def web_alpha_psi(geo: _Geometry, fy: float,
                  n_ed_kn: float, m_ed_knm: float) -> tuple[float, float]:
    """Plastic ``alpha`` and elastic ``psi`` of the web under N + My.

    ``alpha`` is the fraction of the flat web in compression under the plastic
    stress block; ``psi = σ2/σ1`` is the ratio of the elastic edge stresses of
    the web (compression positive). Pure bending gives ``alpha = 0.5, psi = −1``;
    pure compression gives ``alpha = 1, psi = 1``.

    Args:
        geo: Normalised geometry.
        fy: Yield strength [N/mm²].
        n_ed_kn: Axial force [kN], compression positive.
        m_ed_knm: Bending moment about the major axis [kNm].

    Returns:
        ``(alpha, psi)``.

    """
    c = geo.c_web
    tw = geo.tw
    if c <= 0.0 or tw <= 0.0:
        return 1.0, 1.0

    n = n_ed_kn * 1.0e3                       # kN → N
    m = m_ed_knm * 1.0e6                      # kNm → N·mm

    # Plastic: axial force is carried by a central web strip of half-height a_n.
    a_n = n / (2.0 * tw * fy)                 # [mm]
    alpha = 0.5 + a_n / c
    alpha = min(max(alpha, 0.0), 1.0)

    # Elastic edge stresses of the web (at z = ± c/2 from the centroid).
    area = geo.area
    iy = geo.iy
    if area <= 0.0 or iy <= 0.0:
        return alpha, (1.0 if n_ed_kn > 0 and m_ed_knm == 0 else -1.0)
    sigma_n = n / area
    sigma_m = m * (c / 2.0) / iy
    s1 = sigma_n + sigma_m                    # most compressed edge
    s2 = sigma_n - sigma_m
    if abs(s1) < 1.0e-12:
        psi = 1.0
    else:
        # order so that |s1| is the maximum compressive stress
        if abs(s2) > abs(s1):
            s1, s2 = s2, s1
        psi = s2 / s1
    psi = min(max(psi, -3.0), 1.0)
    return alpha, psi


def flange_alpha_psi_minor(geo: _Geometry, fy: float,  # ruff: ignore[unused-function-argument]
                           n_ed_kn: float, m_ed_knm: float,
                           ) -> tuple[float, float, bool]:
    """Stress state of an I-flange outstand under N + Mz (minor-axis bending).

    Under minor-axis bending the flange outstand spans from the web face
    (supported edge) to the tip (free edge) with a linear stress that, on the
    compression flange, peaks at the tip. Returns ``(alpha, psi, tip)`` where
    ``alpha`` is the plastic compressed fraction of the outstand, ``psi`` its
    elastic end-stress ratio and ``tip`` True when the free tip is the more
    compressed edge.

    Args:
        geo: Normalised geometry.
        fy: Yield strength [N/mm²] (unused; kept for signature symmetry).
        n_ed_kn: Axial force [kN], compression positive.
        m_ed_knm: Bending moment about the minor axis [kNm].

    Returns:
        ``(alpha, psi, tip_in_compression)``.

    """
    y_s = geo.tw / 2.0 + geo.r        # supported (web) edge of the outstand
    y_t = geo.b / 2.0                 # free tip
    area = geo.area
    iz = geo.iz
    if area <= 0.0 or iz <= 0.0:
        return 1.0, 1.0, True

    n = n_ed_kn * 1.0e3
    m = abs(m_ed_knm) * 1.0e6         # compression flange: bending adds compression
    s_s = n / area + m * y_s / iz     # stress at the supported edge
    s_t = n / area + m * y_t / iz     # stress at the free tip

    tip = abs(s_t) >= abs(s_s)
    s1, s2 = (s_t, s_s) if tip else (s_s, s_t)
    psi = s2 / s1 if abs(s1) > 1.0e-12 else 1.0
    psi = min(max(psi, -3.0), 1.0)

    if s_s >= 0.0 and s_t >= 0.0:
        alpha = 1.0                   # whole outstand compressed
    elif s_s < 0.0 and s_t < 0.0:
        alpha = 1.0e-9                # whole outstand in tension → Class 1
    else:
        xi0 = s_s / (s_s - s_t)       # zero-stress crossing, web→tip in (0,1)
        alpha = (1.0 - xi0) if s_t > 0.0 else xi0
    alpha = min(max(alpha, 1.0e-9), 1.0)
    return alpha, psi, tip


def _swap_axes(geo: _Geometry) -> _Geometry:
    """Return the geometry seen from the minor axis (h↔b, tw↔tf, Iy↔Iz).

    For a box section the minor-axis check is the same procedure as the major
    one on this swapped view: the walls that were flanges become the webs
    carrying the bending gradient and vice-versa.
    """
    return _Geometry(kind=geo.kind, h=geo.b, b=geo.h, tw=geo.tf, tf=geo.tw,
                     r=geo.r, area=geo.area, iy=geo.iz, iz=geo.iy,
                     c_web=geo.c_flange, c_flange=geo.c_web)


# ── results ─────────────────────────────────────────────────────────────────

@dataclass
class PartClassification:
    """Classification of a single compression part."""

    name: str                     # 'web', 'flange', 'wall_top', 'tube'
    c_over_t: float
    part_class: SectionClass
    psi: float = 1.0
    alpha: float = 1.0


@dataclass
class ClassificationResult:
    """Result of classifying a whole cross-section."""

    section_class: SectionClass
    epsilon: float
    fy: float
    n_ed: float                   # [kN]
    m_ed: float                   # [kNm]
    parts: list = field(default_factory=list)   # list[PartClassification]

    def __str__(self) -> str:
        """Human-readable summary of the classification."""
        lines = [
            f"Cross-section class: {int(self.section_class)}",
            f"  ε = {self.epsilon:.3f}  (fy = {self.fy:.0f} MPa)",
            f"  N_Ed = {self.n_ed:.1f} kN, M_Ed = {self.m_ed:.1f} kNm",
        ]
        for p in self.parts:
            lines.append(
                f"  {p.name:9s} c/t = {p.c_over_t:6.1f}  "
                f"→ class {int(p.part_class)}  (ψ={p.psi:+.2f}, α={p.alpha:.2f})")
        return "\n".join(lines)


# ── section classification ──────────────────────────────────────────────────

def _ratio(c: float, t: float) -> float:
    return c / t if t > 0.0 else float("inf")


def classify_section(section, fy: float,  # ruff: ignore[missing-type-function-argument]
                     n_ed: float = 0.0, m_ed: float = 0.0,
                     axis: str = "y") -> ClassificationResult:
    """Classify a steel cross-section under N + M (EN 1993-1-1 §5.5).

    Args:
        section: A eurocodepy profile object (``ProfileI`` / ``ProfileRHS`` /
            ``ProfileSHS`` / ``ProfileCHS``) or any object exposing
            ``type, h, b, tw, tf, r, A, Iy, Iz``.
        fy: Yield strength [N/mm²].
        n_ed: Axial force [kN], compression positive.
        m_ed: Bending moment [kNm] about the chosen axis.
        axis: ``"y"`` for major-axis bending (default) or ``"z"`` for minor-axis
            bending.

    Returns:
        A :class:`ClassificationResult` with the governing (highest) class and
        the per-part breakdown.

    """
    eps = epsilon(fy)
    geo = _to_geometry(section)
    axis = axis.lower()
    parts: list[PartClassification] = []

    if geo.kind == "CHS":
        d_t = _ratio(geo.h, geo.tf)
        cls = classify_chs_part(d_t, eps)
        parts.append(PartClassification("tube", d_t, cls, psi=1.0, alpha=1.0))

    elif geo.kind in ("RHS", "SHS"):
        # A box has only internal parts. The minor-axis check is the major-axis
        # procedure applied to the axis-swapped geometry.
        gg = geo if axis == "y" else _swap_axes(geo)
        alpha, psi = web_alpha_psi(gg, fy, n_ed, m_ed)
        web_ct = _ratio(gg.c_web, gg.tw)
        parts.append(PartClassification(
            "web", web_ct, classify_internal_part(web_ct, eps, psi=psi, alpha=alpha),
            psi=psi, alpha=alpha))
        fl_ct = _ratio(gg.c_flange, gg.tf)
        parts.append(PartClassification(
            "flange", fl_ct, classify_internal_part(fl_ct, eps, psi=1.0, alpha=1.0),
            psi=1.0, alpha=1.0))

    elif axis == "y":                              # I / H — major axis
        alpha, psi = web_alpha_psi(geo, fy, n_ed, m_ed)
        web_ct = _ratio(geo.c_web, geo.tw)
        parts.append(PartClassification(
            "web", web_ct, classify_internal_part(web_ct, eps, psi=psi, alpha=alpha),
            psi=psi, alpha=alpha))
        fl_ct = _ratio(geo.c_flange, geo.tf)       # outstand, uniform compression
        parts.append(PartClassification(
            "flange", fl_ct, classify_outstand_part(fl_ct, eps),
            psi=1.0, alpha=1.0))

    else:                                          # I / H — minor axis
        # Flanges carry the bending as gradient outstands; the web sees only the
        # uniform axial stress (Class 1 when it is not in compression).
        a_f, psi_f, tip = flange_alpha_psi_minor(geo, fy, n_ed, m_ed)
        fl_ct = _ratio(geo.c_flange, geo.tf)
        parts.append(PartClassification(
            "flange", fl_ct,
            classify_outstand_part(fl_ct, eps, psi=psi_f, alpha=a_f,
                                   tip_in_compression=tip),
            psi=psi_f, alpha=a_f))
        web_ct = _ratio(geo.c_web, geo.tw)
        if n_ed > 0.0:
            web_cls = classify_internal_part(web_ct, eps, psi=1.0, alpha=1.0)
        else:
            web_cls = SectionClass.CLASS_1         # unstressed / in tension
        parts.append(PartClassification("web", web_ct, web_cls,
                                        psi=1.0, alpha=1.0))

    section_class = SectionClass(max(int(p.part_class) for p in parts))
    return ClassificationResult(section_class=section_class, epsilon=eps,
                                fy=fy, n_ed=n_ed, m_ed=m_ed, parts=parts)


# ── Class-4 effective properties (EN 1993-1-5 §4.4) ─────────────────────────

def k_sigma_internal(psi: float) -> float:
    """Buckling factor kσ for an internal compression element — Table 4.1."""
    if psi >= 1.0:
        return 4.0
    if psi > 0.0:
        return 8.2 / (1.05 + psi)
    if psi == 0.0:
        return 7.81
    if psi > -1.0:
        return 7.81 - 6.29 * psi + 9.78 * psi * psi
    if psi == -1.0:
        return 23.9
    return 5.98 * (1.0 - psi) ** 2               # -3 ≤ ψ < -1


def k_sigma_outstand(psi: float = 1.0,
                     tip_in_compression: bool = True) -> float:
    """Buckling factor kσ for an outstand element — EN 1993-1-5 Table 4.2.

    Two stress arrangements are covered. When the maximum compression is at the
    free tip (``tip_in_compression=True``) kσ grows quickly as ψ drops (0.43 at
    ψ=1, 1.70 at ψ=0, 23.8 at ψ=−1). When the maximum compression is at the
    supported edge (tip in tension) kσ stays close to 0.43…0.85.
    """
    if tip_in_compression:
        if psi >= 1.0:
            return 0.43
        if psi > 0.0:
            return 0.578 / (psi + 0.34)
        if psi == 0.0:
            return 1.70
        if psi > -1.0:
            return 1.7 - 5.0 * psi + 17.1 * psi * psi
        return 23.8                               # ψ = -1
    # Maximum compression at the supported edge (0.57 − 0.21ψ + 0.07ψ²).
    return 0.57 - 0.21 * psi + 0.07 * psi * psi


def plate_slenderness(c_over_t: float, eps: float, k_sigma: float) -> float:
    """Normalised plate slenderness ``λ̄p`` (EN 1993-1-5 §4.4(2))."""
    return c_over_t / (28.4 * eps * math.sqrt(k_sigma))


def reduction_factor_internal(lambda_p: float, psi: float) -> float:
    """Reduction factor ρ for an internal compression element — §4.4(2)."""
    limit = 0.5 + math.sqrt(max(0.085 - 0.055 * psi, 0.0))
    if lambda_p <= limit:
        return 1.0
    rho = (lambda_p - 0.055 * (3.0 + psi)) / (lambda_p * lambda_p)
    return min(rho, 1.0)


def reduction_factor_outstand(lambda_p: float) -> float:
    """Reduction factor ρ for an outstand compression element — §4.4(2)."""
    if lambda_p <= 0.748:
        return 1.0
    rho = (lambda_p - 0.188) / (lambda_p * lambda_p)
    return min(rho, 1.0)


@dataclass
class EffectiveProperties:
    """Class-4 effective cross-section properties (EN 1993-1-5 §4.4).

    Areas in mm², moduli in mm³, the centroid shift in mm.
    """

    section_class: SectionClass
    A_eff: float                  # effective area, uniform compression [mm²]
    e_Ny: float                   # centroid shift along z under axial load [mm]
    W_eff_y: float                # effective modulus, major-axis bending [mm³]
    A_gross: float                # gross area [mm²]
    W_el_y_gross: float           # gross elastic modulus about y [mm³]

    def __str__(self) -> str:
        """Human-readable summary of the effective properties."""
        return (
            f"Class {int(self.section_class)} effective properties:\n"
            f"  A_eff   = {self.A_eff:10.1f} mm²  (A = {self.A_gross:.1f} mm²)\n"
            f"  e_N,z   = {self.e_Ny:10.2f} mm\n"
            f"  W_eff,y = {self.W_eff_y:10.1f} mm³  "
            f"(W_el,y = {self.W_el_y_gross:.1f} mm³)"
        )


# A plate is (area, z-centroid, own second moment about its own axis), all in mm.
_Plate = tuple


def _plates_area(plates: list) -> tuple[float, float]:
    """Return (total area, area·z) of a list of plates."""
    a = sum(p[0] for p in plates)
    az = sum(p[0] * p[1] for p in plates)
    return a, az


def _plates_inertia_about(plates: list, z0: float) -> float:
    """Second moment of a plate list about the axis z = z0 (parallel axis)."""
    return sum(p[2] + p[0] * (p[1] - z0) ** 2 for p in plates)


def _gross_plates_i(geo: _Geometry) -> list:
    """Gross plates of an I-section about y (z measured from mid-height)."""
    zf = (geo.h - geo.tf) / 2.0
    a_f = geo.b * geo.tf
    i_f = geo.b * geo.tf ** 3 / 12.0
    a_w = geo.tw * geo.c_web
    i_w = geo.tw * geo.c_web ** 3 / 12.0
    return [
        (a_f, +zf, i_f),          # top (compression) flange
        (a_f, -zf, i_f),          # bottom flange
        (a_w, 0.0, i_w),          # web
    ]


def _gross_plates_box(geo: _Geometry) -> list:
    """Gross plates of an RHS/SHS about y (two flanges + two webs)."""
    zf = (geo.h - geo.tf) / 2.0
    a_f = geo.c_flange * geo.tf     # flat top/bottom wall
    i_f = geo.c_flange * geo.tf ** 3 / 12.0
    a_w = geo.tw * geo.c_web        # one side wall
    i_w = geo.tw * geo.c_web ** 3 / 12.0
    return [
        (a_f, +zf, i_f),          # top wall
        (a_f, -zf, i_f),          # bottom wall
        (a_w, 0.0, i_w),          # side wall 1
        (a_w, 0.0, i_w),          # side wall 2
    ]


def effective_properties(section, fy: float) -> EffectiveProperties:  # ruff: ignore[missing-type-function-argument]
    """Class-4 effective properties of an I or RHS/SHS section (EN 1993-1-5).

    Computes the effective area under uniform compression (``A_eff`` and the
    resulting centroid shift ``e_N``) and the effective section modulus in
    major-axis bending (``W_eff,y``). For sections of Class 1–3 the gross
    properties are returned unchanged (ρ = 1). CHS Class-4 sections are governed
    by shell buckling (EN 1993-1-6) and are not handled here.

    Args:
        section: A eurocodepy profile object or compatible.
        fy: Yield strength [N/mm²].

    Returns:
        :class:`EffectiveProperties`.

    """
    eps = epsilon(fy)
    geo = _to_geometry(section)
    if geo.kind == "CHS":
        msg = ("Class-4 CHS is governed by shell buckling (EN 1993-1-6); "
               "the effective-width method does not apply.")
        raise NotImplementedError(msg)

    cls = classify_section(section, fy, n_ed=0.0, m_ed=0.0).section_class
    is_i = geo.kind == "I"
    gross = _gross_plates_i(geo) if is_i else _gross_plates_box(geo)
    a_gross, az_gross = _plates_area(gross)
    z_c = az_gross / a_gross if a_gross else 0.0
    i_gross = _plates_inertia_about(gross, z_c)
    z_max = geo.h / 2.0
    wel_plate = i_gross / z_max if z_max else 0.0
    # True (catalogue) gross properties — used as the reference, with the
    # slender-element reductions applied as the effective/gross ratio computed
    # from the idealised flat-plate model (which omits the root fillets).
    a_true = geo.area if geo.area > 0.0 else a_gross
    wel_true = (geo.iy / z_max) if (geo.iy > 0.0 and z_max) else wel_plate

    # ── Effective area under uniform compression (ψ = 1 on every part) ──
    # Flange / top wall reduction.
    if is_i:
        fl_ct = geo.c_flange / geo.tf if geo.tf else 0.0
        lam_f = plate_slenderness(fl_ct, eps, k_sigma_outstand(1.0))
        rho_f = reduction_factor_outstand(lam_f)
    else:
        fl_ct = geo.c_flange / geo.tf if geo.tf else 0.0
        lam_f = plate_slenderness(fl_ct, eps, k_sigma_internal(1.0))
        rho_f = reduction_factor_internal(lam_f, 1.0)
    # Web / side-wall reduction under uniform compression.
    web_ct = geo.c_web / geo.tw if geo.tw else 0.0
    lam_w = plate_slenderness(web_ct, eps, k_sigma_internal(1.0))
    rho_w = reduction_factor_internal(lam_w, 1.0)

    if is_i:
        loss_top_flange = (1.0 - rho_f) * geo.b * geo.tf
        loss_bot_flange = (1.0 - rho_f) * geo.b * geo.tf
        loss_web = (1.0 - rho_w) * geo.tw * geo.c_web
        zf = (geo.h - geo.tf) / 2.0
        # centroid shift from the removed (ineffective) areas
        removed = [
            (loss_top_flange, +zf),
            (loss_bot_flange, -zf),
            (loss_web, 0.0),
        ]
    else:
        loss_flange = (1.0 - rho_f) * geo.c_flange * geo.tf   # per wall
        loss_web = (1.0 - rho_w) * geo.tw * geo.c_web         # per wall
        zf = (geo.h - geo.tf) / 2.0
        removed = [
            (loss_flange, +zf),
            (loss_flange, -zf),
            (loss_web, 0.0),
            (loss_web, 0.0),
        ]
    a_removed = sum(a for a, _ in removed)
    a_eff_plate = a_gross - a_removed
    rho_area = a_eff_plate / a_gross if a_gross else 1.0
    a_eff = a_true * rho_area
    # centroid of the effective area (symmetric losses ⇒ e_N = 0)
    if a_eff_plate > 0.0:
        z_eff = (az_gross - sum(a * z for a, z in removed)) / a_eff_plate
    else:
        z_eff = z_c
    e_ny = z_eff - z_c

    # ── Effective modulus in major-axis bending (as a ratio on W_el,true) ──
    weff_plate = _effective_modulus_bending(geo, eps, is_i)
    ratio_w = weff_plate / wel_plate if wel_plate else 1.0
    w_eff_y = wel_true * ratio_w

    return EffectiveProperties(
        section_class=cls, A_eff=a_eff, e_Ny=e_ny, W_eff_y=w_eff_y,
        A_gross=a_true, W_el_y_gross=wel_true)


def _effective_modulus_bending(geo: _Geometry, eps: float, is_i: bool) -> float:
    """Effective elastic modulus W_eff,y for major-axis bending.

    The compression flange (outstand for I, internal for box) is reduced under
    uniform compression; the web is an internal part under a bending stress
    gradient (ψ = −1 for a doubly-symmetric section on the gross section, per
    §4.4(3)) and is split into two effective strips. The centroid of the
    resulting effective section is relocated and W_eff = I_eff / z_max.
    """
    zf = (geo.h - geo.tf) / 2.0
    c = geo.c_web
    tw = geo.tw

    # Compression-flange reduction (uniform compression).
    if is_i:
        fl_ct = geo.c_flange / geo.tf if geo.tf else 0.0
        rho_f = reduction_factor_outstand(
            plate_slenderness(fl_ct, eps, k_sigma_outstand(1.0)))
        a_f = geo.b * geo.tf
        i_f = geo.b * geo.tf ** 3 / 12.0
    else:
        fl_ct = geo.c_flange / geo.tf if geo.tf else 0.0
        rho_f = reduction_factor_internal(
            plate_slenderness(fl_ct, eps, k_sigma_internal(1.0)), 1.0)
        a_f = geo.c_flange * geo.tf
        i_f = geo.c_flange * geo.tf ** 3 / 12.0

    n_web = 1 if is_i else 2       # number of identical webs / side walls

    # Web in bending: ψ = −1, compression zone height c/2, effective strips
    # b_e1 = 0.4·b_eff at the compressed edge, b_e2 = 0.6·b_eff next to the NA.
    psi_web = -1.0
    rho_w = reduction_factor_internal(
        plate_slenderness(c / tw if tw else 0.0, eps,
                          k_sigma_internal(psi_web)), psi_web)
    b_c = c / (1.0 - psi_web)                 # = c/2 for ψ = −1
    b_eff = rho_w * b_c
    b_e1 = 0.4 * b_eff
    b_e2 = 0.6 * b_eff

    plates: list = []
    # Compression flange (reduced) and tension flange (full).
    plates.append((rho_f * a_f, +zf, rho_f * i_f))
    plates.append((a_f, -zf, i_f))
    # Tension half of the web (fully effective): z ∈ [−c/2, 0].
    a_wt = tw * (c / 2.0)
    z_wt = -c / 4.0
    i_wt = tw * (c / 2.0) ** 3 / 12.0
    # Effective compression strips of the web.
    #  strip 1 at the compressed edge: z ∈ [c/2 − b_e1, c/2]
    z_s1 = (c / 2.0) - b_e1 / 2.0
    a_s1 = tw * b_e1
    i_s1 = tw * b_e1 ** 3 / 12.0
    #  strip 2 adjacent to the neutral axis: z ∈ [0, b_e2]
    z_s2 = b_e2 / 2.0
    a_s2 = tw * b_e2
    i_s2 = tw * b_e2 ** 3 / 12.0
    for _ in range(n_web):
        plates.append((a_wt, z_wt, i_wt))
        plates.append((a_s1, z_s1, i_s1))
        plates.append((a_s2, z_s2, i_s2))

    a_tot, az_tot = _plates_area(plates)
    z_na = az_tot / a_tot if a_tot else 0.0
    i_eff = _plates_inertia_about(plates, z_na)
    # Extreme fibre distance from the shifted neutral axis.
    z_extreme = max(geo.h / 2.0 - z_na, geo.h / 2.0 + z_na)
    return i_eff / z_extreme if z_extreme else 0.0
