# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1 §5.8 / §6.1 -- reinforced-concrete column design (composite).

A column (or any member dominated by axial compression together with uniaxial
or biaxial bending) is checked in three stages, mirroring the structure of
:mod:`eurocodepy.ec3.uls.member_buckling` for steel members:

1. **Slenderness** (§5.8.3): ``lambda = l0/i`` compared against the simplified
   limit ``lambda_lim`` (Eq. 5.13N). Below the limit, second-order effects may
   be ignored.
2. **Second-order moment** (§5.8.8, the *nominal curvature* method -- the
   method of reference here; the *nominal stiffness* method of §5.8.7 is
   provided as an alternative via :func:`nominal_stiffness_moment` and
   ``ColumnInput.second_order_method``): an additional moment
   ``M2 = N_Ed * e2`` is added to the first-order design moment, together
   with the minimum eccentricity of §6.1(4) and the geometric imperfections
   of §5.2.
3. **Section verification** (§6.1 / §5.8.9): the resulting design moments are
   checked against the section's uniaxial moment resistance ``M_Rd(N_Ed)``,
   obtained by strain-compatibility (parabola-rectangle concrete block,
   bilinear reinforcement) -- see :func:`uniaxial_moment_resistance` --
   combined through the biaxial interaction of Eq. 5.8.9(4) when both
   ``My_Ed`` and ``Mz_Ed`` are present.

Units follow the rest of ``ec2.uls``: lengths in **m**, strengths in **MPa**,
forces in **kN**, moments in **kN.m**, reinforcement areas in **cm2**.

**Sign convention**: ``N_Ed`` is **compression positive**, exactly like
:func:`eurocodepy.ec2.uls.bend_axial.calc_asl_nm`.

**Scope of this first implementation**: rectangular sections only (the
circular case needs the stress-block machinery of
:mod:`eurocodepy.ec2.uls.bend_circ`, not yet reused here). Biaxial
reinforcement is a simple discrete list of bars (:class:`RebarLayout`);
helpers are provided to build a symmetric rectangular arrangement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from eurocodepy.ec2.materials import (
    Concrete,
    ConcreteStressCurve,
    Reinforcement,
    sigma_c,
)
from eurocodepy.utils.crosssection import (
    CircularCrossSection, RectangularCrossSection,
)

__all__ = [
    "ColumnInput",
    "ColumnResult",
    "RebarLayout",
    "biaxial_interaction_exponent",
    "design_column_reinforcement",
    "effective_length",
    "eurocode2_column_check",
    "maximum_column_reinforcement_m2",
    "minimum_column_reinforcement_m2",
    "nominal_curvature_e2",
    "nominal_stiffness_moment",
    "slenderness_limit",
    "uniaxial_moment_resistance",
]

# Number of concrete fibres used to integrate the compression block when
# building the M-N interaction point (strain-compatibility, §3.1.7).
_N_FIBRES = 200


@dataclass
class RebarLayout:
    """A discrete longitudinal reinforcement layout for a rectangular column.

    ``positions_m`` are (y, z) coordinates in metres, relative to the section
    centroid; ``diameters_mm`` gives one bar diameter per position (mm).
    """

    positions_m: list = field(default_factory=list)
    diameters_mm: list = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.positions_m) != len(self.diameters_mm):
            msg = "positions_m and diameters_mm must have the same length."
            raise ValueError(msg)

    def bar_areas_m2(self) -> list:
        """Per-bar cross-section area [m2]."""
        return [math.pi * (d / 1000.0) ** 2 / 4.0 for d in self.diameters_mm]

    def total_area_cm2(self) -> float:
        """Total longitudinal reinforcement area [cm2]."""
        return sum(a * 1.0e4 for a in self.bar_areas_m2())

    @classmethod
    def symmetric_rectangular(
        cls,
        section: RectangularCrossSection,
        cover_m: float,
        n_bars: int,
        diameter_mm: float,
    ) -> "RebarLayout":
        """Distribute ``n_bars`` evenly around the perimeter of a rectangular
        section, at a distance ``cover_m`` (to the bar centre) from each face,
        with a bar forced into each of the 4 corners (``n_bars`` >= 4).

        This is a simple, symmetric arrangement suitable for a first design
        pass; it is not the only valid layout (EC2 imposes only minimum
        spacing/edge-distance rules, §8.2/§9.5.2).
        """
        min_bars = 4
        if n_bars < min_bars:
            msg = "A rectangular column needs at least 4 bars (one per corner)."
            raise ValueError(msg)
        b, h = section.width, section.height
        y0, z0 = b / 2.0 - cover_m, h / 2.0 - cover_m
        perimeter = 2.0 * (2.0 * y0 + 2.0 * z0)
        if perimeter <= 0.0:
            msg = "cover_m too large for the given section."
            raise ValueError(msg)
        corners = [(y0, z0), (-y0, z0), (-y0, -z0), (y0, -z0)]
        positions = list(corners)
        remaining = n_bars - 4
        if remaining > 0:
            edges = [
                ((y0, z0), (-y0, z0), 2.0 * y0),
                ((-y0, z0), (-y0, -z0), 2.0 * z0),
                ((-y0, -z0), (y0, -z0), 2.0 * y0),
                ((y0, -z0), (y0, z0), 2.0 * z0),
            ]
            total_edge_len = sum(length for _, _, length in edges)
            raw_counts = [remaining * length / total_edge_len for _, _, length in edges]
            counts = [int(r) for r in raw_counts]
            leftover = remaining - sum(counts)
            # largest-remainder method: give the leftover bars to the edges
            # whose fractional allocation was largest, so the total is exact.
            order = sorted(range(4), key=lambda i: raw_counts[i] - counts[i], reverse=True)
            for i in range(leftover):
                counts[order[i]] += 1
            for (p0, p1, _length), c in zip(edges, counts):
                for k in range(1, c + 1):
                    t = k / (c + 1)
                    y = p0[0] + t * (p1[0] - p0[0])
                    z = p0[1] + t * (p1[1] - p0[1])
                    positions.append((y, z))
        diameters = [diameter_mm] * len(positions)
        return cls(positions_m=positions, diameters_mm=diameters)

    @classmethod
    def symmetric_rectangular_biaxial(
        cls,
        section: RectangularCrossSection,
        cover_m: float,
        n_y: int,
        n_z: int,
        diameter_mm: float,
    ) -> "RebarLayout":
        """Distribute bars on a rectangular section with an independent bar
        count per face direction -- ``n_y`` bars on each of the two faces
        perpendicular to z (top/bottom, spanning the width ``b``, i.e. along
        y), ``n_z`` bars on each of the two faces perpendicular to y
        (left/right, spanning the height ``h``, along z) -- corners shared
        between the two directions, counted once.

        Unlike :meth:`symmetric_rectangular` (one total ``n_bars`` spread
        proportionally to edge length, always symmetric about both axes
        regardless of the actual M_y/M_z demand), this lets the caller put
        more steel on the faces that resist the governing bending direction
        -- e.g. more bars along y (``n_y``) for a column governed by M_z
        (bending about z, tension/compression on the y-faces), needed to
        design for skew/biaxial bending economically rather than uniformly.

        Total bar count is ``2*n_y + 2*n_z - 4``. Both ``n_y`` and ``n_z``
        must be >= 2 (each face needs at least its two corners).
        """
        min_per_face = 2
        if n_y < min_per_face or n_z < min_per_face:
            msg = ("A rectangular column needs at least 2 bars per face "
                   "(n_y >= 2 and n_z >= 2 -- 4 bars total, one per corner).")
            raise ValueError(msg)
        b, h = section.width, section.height
        y0, z0 = b / 2.0 - cover_m, h / 2.0 - cover_m
        if y0 <= 0.0 or z0 <= 0.0:
            msg = "cover_m too large for the given section."
            raise ValueError(msg)
        positions = []
        # Top (z=+z0) and bottom (z=-z0) faces: n_y bars each, evenly spaced
        # along y, corners included.
        for z_sign in (z0, -z0):
            for k in range(n_y):
                t = k / (n_y - 1) if n_y > 1 else 0.5
                y = -y0 + t * 2.0 * y0
                positions.append((y, z_sign))
        # Left (y=+y0) and right (y=-y0) faces: n_z - 2 bars each, excluding
        # the corners already placed by the loop above.
        for y_sign in (y0, -y0):
            for k in range(1, n_z - 1):
                t = k / (n_z - 1)
                z = -z0 + t * 2.0 * z0
                positions.append((y_sign, z))
        diameters = [diameter_mm] * len(positions)
        return cls(positions_m=positions, diameters_mm=diameters)

    @classmethod
    def symmetric_circular(
        cls,
        section: "CircularCrossSection",
        cover_m: float,
        n_bars: int,
        diameter_mm: float,
    ) -> "RebarLayout":
        """Distribute ``n_bars`` evenly around a circle of radius
        ``section.radius - cover_m`` (to the bar centre), starting at the top
        (0°, +y=0/+z axis convention below) and going counter-clockwise.

        A minimum of 3 bars is enforced (a circular column needs at least a
        triangle to resist biaxial bending); EC2 §9.5.2 practical guidance is
        6 bars minimum, but that is left to the caller (as with the
        rectangular 4-bar minimum, this is only the geometric floor).
        """
        min_bars = 3
        if n_bars < min_bars:
            msg = "A circular column needs at least 3 bars."
            raise ValueError(msg)
        r = section.radius - cover_m
        if r <= 0.0:
            msg = "cover_m too large for the given section."
            raise ValueError(msg)
        positions = []
        for k in range(n_bars):
            theta = 2.0 * math.pi * k / n_bars
            y = r * math.cos(theta)
            z = r * math.sin(theta)
            positions.append((y, z))
        diameters = [diameter_mm] * len(positions)
        return cls(positions_m=positions, diameters_mm=diameters)


@dataclass
class ColumnInput:
    """Data for a single reinforced-concrete column ULS check."""

    section: RectangularCrossSection
    concrete: Concrete
    reinforcement: Reinforcement
    rebar: RebarLayout
    cover_m: float
    alpha_cc: float = 1.0
    length_m: float = 3.0
    k_y: float = 1.0
    k_z: float = 1.0
    m01_y: float = 0.0
    m02_y: float = 0.0
    m01_z: float = 0.0
    m02_z: float = 0.0
    braced_y: bool = True
    braced_z: bool = True
    phi_ef: float = 2.0
    n_ed: float = 0.0
    my_ed: float = 0.0
    mz_ed: float = 0.0
    second_order_method: str = "nominal_curvature"


@dataclass
class ColumnResult:
    """Result of the §5.8/§6.1 column ULS check."""

    lambda_y: float = 0.0
    lambda_z: float = 0.0
    lambda_lim_y: float = 0.0
    lambda_lim_z: float = 0.0
    slender_y: bool = False
    slender_z: bool = False
    e2_y: float = 0.0
    e2_z: float = 0.0
    m2_y: float = 0.0
    m2_z: float = 0.0
    n_b_y: object = None
    n_b_z: object = None
    method_used: str = "nominal_curvature"
    med_y_design: float = 0.0
    med_z_design: float = 0.0
    biaxial_exponent_a: float = 1.0
    mrd_y: float = 0.0
    mrd_z: float = 0.0
    n_ratio: float = 0.0
    utilization: float = 0.0
    passed: bool = False
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f"EC2 §5.8/§6.1 column -- utilization={self.utilization:.3f}"
                + (" (FAIL)" if not self.passed else " (OK)"))


# --------------------------------------------------------------------------
# Slenderness (§5.8.3)
# --------------------------------------------------------------------------

def effective_length(length_m: float, k: float) -> float:
    """l0 = k * length_m (§5.8.3.2)."""
    return k * length_m


def slenderness_limit(n: float, phi_ef: float, omega: float,
                       rm=None) -> float:
    """Simplified slenderness limit lambda_lim (Eq. 5.13N).

    Args:
        n: N_Ed / (Ac.fcd).
        phi_ef: effective creep coefficient.
        omega: As.fyd / (Ac.fcd), the mechanical reinforcement ratio.
        rm: M01/M02 (first-order end moment ratio); ``None`` if unknown
            (uses the conservative default C = 0.7).

    Returns:
        lambda_lim. Returns +inf when n <= 0 (no compression, the criterion
        does not apply -- 2nd-order effects must then be assessed by other
        means).

    """
    if n <= 0.0:
        return float("inf")
    a = 1.0 / (1.0 + 0.2 * phi_ef)
    b = math.sqrt(1.0 + 2.0 * omega)
    c = (1.7 - rm) if rm is not None else 0.7
    return 20.0 * a * b * c / math.sqrt(n)


def biaxial_interaction_exponent(n: float) -> float:
    """Biaxial-bending interaction exponent 'a' (§5.8.9(4)).

    a = 1.0 for n <= 0.1, a = 2.0 for n >= 1.0, linear interpolation between.
    """
    if n <= 0.1:
        return 1.0
    if n >= 1.0:
        return 2.0
    return 1.0 + (n - 0.1) / (1.0 - 0.1)


# --------------------------------------------------------------------------
# Second-order moment -- two alternative methods
# --------------------------------------------------------------------------

def nominal_curvature_e2(n_ed: float, ac: float, fcd: float, as_total_m2: float,
                          fyd: float, fck: float, es_mpa: float, lam: float,
                          l0: float, phi_ef: float, d: float):
    """Nominal-curvature second-order moment (§5.8.8, Eqs. 5.33-5.37).

    Returns:
        (e2, M2): additional eccentricity [m] and additional moment [kNm].

    """
    if ac <= 0.0 or fcd <= 0.0:
        return 0.0, 0.0
    omega = as_total_m2 * fyd / (ac * fcd) if (ac * fcd) > 0 else 0.0
    n = n_ed / (ac * fcd * 1000.0)  # fcd is MPa = 1000 kN/m2; n_ed is kN
    nu = 1.0 + omega
    n_bal = 0.4
    denom = nu - n_bal
    kr = 1.0 if abs(denom) < 1.0e-12 else (nu - n) / denom
    kr = max(0.0, min(1.0, kr))
    beta = 0.35 + fck / 200.0 - lam / 150.0
    k_phi = max(1.0, 1.0 + beta * phi_ef)
    eps_yd = fyd / es_mpa
    if d <= 0.0:
        return 0.0, 0.0
    inv_r0 = eps_yd / (0.45 * d)
    inv_r = kr * k_phi * inv_r0
    c = 10.0
    e2 = inv_r * l0 * l0 / c
    m2 = n_ed * e2
    return e2, m2


def nominal_stiffness_moment(n_ed: float, m0_ed: float, ac: float, ic: float,
                              ecm: float, fck: float, lam: float, l0: float,
                              phi_ef: float, es_mpa=None,
                              i_s=None,
                              include_steel: bool = False,
                              ):
    """Nominal-stiffness alternative (§5.8.7, Eqs. 5.20-5.24).

    Returns:
        (n_b, m_total, stable): the Euler critical load N_B [kN], the
        amplified total moment [kNm], and whether N_Ed < N_B (``stable``);
        when ``stable`` is False the section is unstable at this stiffness
        estimate and M_total is returned as +inf rather than dividing by a
        non-positive denominator.

    """
    if ac <= 0.0 or l0 <= 0.0:
        return 0.0, float("inf"), False
    n = n_ed / (ac * (fck / 1.5) * 1000.0) if fck > 0 else 0.0  # fck/1.5 as a rough fcd, MPa->kN/m2
    k1 = math.sqrt(fck / 20.0)
    k2 = min(0.20, n * lam / 170.0)
    k2 = max(0.0, k2)
    kc = k1 * k2 / (1.0 + phi_ef)
    ecd = ecm / 1.2
    ei = kc * ecd * ic * 1000.0
    if include_steel and es_mpa is not None and i_s is not None:
        ei += 1.0 * es_mpa * i_s * 1000.0
    n_b = (math.pi ** 2) * ei / (l0 * l0) if l0 > 0 else 0.0
    if n_ed >= n_b > 0.0:
        return n_b, float("inf"), False
    if n_b <= 0.0:
        return n_b, float(m0_ed), True
    m_total = m0_ed / (1.0 - n_ed / n_b)
    return n_b, m_total, True


# --------------------------------------------------------------------------
# Section verification -- strain-compatibility M-N interaction (§6.1)
# --------------------------------------------------------------------------

def _section_forces(x: float, inp: "ColumnInput", axis: str):
    """Concrete + steel axial force and moment about the centroid for a given
    neutral-axis depth ``x`` [m], measured from the extreme compression
    fibre, with the extreme-fibre concrete strain fixed at eps_cu2 (ULS,
    §3.1.7).

    ``axis`` selects the bending direction: "z" bends about the local
    z-axis (compression varies along the section height, extreme fibres at
    +/- h/2); "y" bends about y (compression varies along the width).

    Returns (N, M): N compression-positive [kN], M [kNm], both referred to
    the section centroid.
    """
    section = inp.section
    conc = inp.concrete
    reinf = inp.reinforcement
    fyd = reinf.fyd
    es = reinf.Es
    # conc.eps_c2 / eps_cu2 are stored in per-mille (matching
    # eurocodepy.ec2.materials.sigma_c's own convention) -- keep a per-mille
    # value to feed sigma_c, and a fractional (strain) value for E*eps steel
    # stresses.
    eps_cu2_pm = conc.eps_cu2
    eps_cu2 = eps_cu2_pm / 1000.0

    circular = isinstance(section, CircularCrossSection)
    if circular:
        # A circle is symmetric about both axes -- "y" and "z" bending are
        # geometrically identical, only the rebar coordinate picked below
        # (pos_index) differs.
        depth = section.diameter
        radius = section.radius
        pos_index = 0 if axis == "y" else 1
        if axis not in ("y", "z"):
            msg = "axis must be 'y' or 'z'."
            raise ValueError(msg)
    elif axis == "z":
        depth = section.height
        width = section.width
        pos_index = 1
    elif axis == "y":
        depth = section.width
        width = section.height
        pos_index = 0
    else:
        msg = "axis must be 'y' or 'z'."
        raise ValueError(msg)

    half = depth / 2.0

    n_c = 0.0
    m_c = 0.0
    if x > 0.0:
        du = min(x, depth * 1.5) / _N_FIBRES
        for i in range(_N_FIBRES):
            u = (i + 0.5) * du
            if u > depth:
                break
            eps_pm = eps_cu2_pm * (1.0 - u / x) if x > 0 else 0.0
            if eps_pm <= 0.0:
                continue
            sig = float(sigma_c(min(eps_pm, eps_cu2_pm), conc,
                                 ConcreteStressCurve.ParaboleRectangle))
            if circular:
                # Chord width at distance (radius - u) from the centre.
                dist_from_centre = radius - u
                chord_sq = radius * radius - dist_from_centre * dist_from_centre
                if chord_sq <= 0.0:
                    continue
                width_i = 2.0 * math.sqrt(chord_sq)
                area = width_i * du
            else:
                area = width * du
            force = sig * area * 1000.0
            n_c += force
            coord = half - u
            m_c += force * coord

    n_s = 0.0
    m_s = 0.0
    areas = inp.rebar.bar_areas_m2()
    for (pos, area) in zip(inp.rebar.positions_m, areas):
        coord = pos[pos_index]
        u = half - coord
        eps = eps_cu2 * (1.0 - u / x) if x > 0 else -eps_cu2
        sig = max(-fyd, min(fyd, eps * es))
        force = sig * area * 1000.0
        n_s += force
        m_s += force * coord

    return n_c + n_s, m_c + m_s


def uniaxial_moment_resistance(inp: "ColumnInput", n_ed: float, axis: str,
                                trace=None) -> float:
    """Uniaxial moment resistance M_Rd for the given axial force N_Ed.

    Solves, by bisection on the neutral-axis depth x, for the force
    equilibrium N(x) = n_ed, then returns the corresponding resisting moment
    about the section centroid (its absolute value).

    :class:`RectangularCrossSection` and :class:`CircularCrossSection` are
    supported; T/L sections are not (no fibre-width profile defined for
    them yet).
    """
    if not isinstance(inp.section, (RectangularCrossSection,
                                    CircularCrossSection)):
        msg = ("uniaxial_moment_resistance: only RectangularCrossSection "
               "and CircularCrossSection are supported in this version "
               "(T/L sections are not yet reduced to a fibre width "
               "profile).")
        raise NotImplementedError(msg)

    if isinstance(inp.section, CircularCrossSection):
        depth = inp.section.diameter
    else:
        depth = inp.section.height if axis == "z" else inp.section.width
    # x_hi must be large enough that the strain profile approaches the
    # uniform eps_cu2 needed for near-squash N (see nominal squash capacity,
    # x -> large); 50x the depth converges to within ~0.1% of the true squash
    # load for typical column proportions.
    x_lo, x_hi = 1.0e-6, 50.0 * depth

    n_lo, _ = _section_forces(x_lo, inp, axis)
    n_hi, _ = _section_forces(x_hi, inp, axis)
    target = max(min(n_ed, n_hi), n_lo)

    x = x_hi
    for _ in range(60):
        x_mid = 0.5 * (x_lo + x_hi)
        n_mid, _ = _section_forces(x_mid, inp, axis)
        if n_mid < target:
            x_lo = x_mid
        else:
            x_hi = x_mid
        x = x_mid

    _, m = _section_forces(x, inp, axis)
    m_rd = abs(m)

    if trace is not None:
        trace.section(f"Uniaxial M-N interaction, axis {axis} (EN 1992-1-1 §6.1)")
        trace.step("N_Ed", n_ed, "kN")
        trace.step("x (neutral axis)", x, "m", clause="EN 1992-1-1 §3.1.7",
                   note="strain-compatibility, eps_cu2 at extreme compression fibre")
        trace.step(f"M_Rd_{axis}", m_rd, "kNm", clause="EN 1992-1-1 §6.1",
                   note="strain-compatibility bisection (60 iterations) — no closed form to substitute")

    return m_rd


# --------------------------------------------------------------------------
# Composite check
# --------------------------------------------------------------------------

def eurocode2_column_check(inp: "ColumnInput", trace=None) -> "ColumnResult":
    """Full §5.8/§6.1 column check: slenderness, 2nd-order moment (nominal
    curvature or nominal stiffness), and biaxial section verification.
    """
    rep = trace

    def _t(*a, **k):
        if rep is not None:
            rep.step(*a, **k)

    def _sec(title):
        if rep is not None:
            rep.section(title)

    section = inp.section
    conc = inp.concrete
    reinf = inp.reinforcement
    fcd = inp.alpha_cc * conc.fcd
    fyd = reinf.fyd
    ac = section.area
    as_total_m2 = sum(inp.rebar.bar_areas_m2())
    n_ed = inp.n_ed

    n_ratio = n_ed / (ac * fcd * 1000.0) if (ac * fcd) > 0 else 0.0  # fcd MPa = 1000 kN/m2
    omega = as_total_m2 * fyd / (ac * fcd) if (ac * fcd) > 0 else 0.0

    _sec("Inputs")
    _t("N_Ed", n_ed, "kN", note="compression positive")
    _t("My_Ed", inp.my_ed, "kNm")
    _t("Mz_Ed", inp.mz_ed, "kNm")
    _t("n", n_ratio, "—", expr="n = N_Ed/(A_c·f_cd)",
       subst=f"{n_ed:.4g}/({ac:.4g}·{fcd:.4g}·1000)")
    _t("ω", omega, "—", expr="ω = A_s·f_yd/(A_c·f_cd)",
       subst=f"{as_total_m2:.4g}·{fyd:.4g}/({ac:.4g}·{fcd:.4g})")

    l0_y = effective_length(inp.length_m, inp.k_y)
    l0_z = effective_length(inp.length_m, inp.k_z)
    lam_y = l0_y / section.radius_y if section.radius_y > 0 else float("inf")
    lam_z = l0_z / section.radius_z if section.radius_z > 0 else float("inf")

    rm_y = (inp.m01_y / inp.m02_y) if inp.m02_y != 0.0 else None
    rm_z = (inp.m01_z / inp.m02_z) if inp.m02_z != 0.0 else None
    lam_lim_y = slenderness_limit(n_ratio, inp.phi_ef, omega, rm_y)
    lam_lim_z = slenderness_limit(n_ratio, inp.phi_ef, omega, rm_z)
    slender_y = lam_y > lam_lim_y
    slender_z = lam_z > lam_lim_z

    _sec("Slenderness (§5.8.3)")
    _t("λ_y", lam_y, "—", expr="λ_y = l0_y/i_y",
       subst=f"{l0_y:.4g}/{section.radius_y:.4g}")
    _t("λ_lim,y", lam_lim_y, "—", clause="EN 1992-1-1 Eq. 5.13N",
       expr="λ_lim = f(n, φ_ef, ω, r_m)",
       subst=f"n={n_ratio:.3g}, φ_ef={inp.phi_ef:g}, ω={omega:.3g}, "
             f"r_m={(f'{rm_y:.3g}' if rm_y is not None else '—')}",
       ok=(not slender_y))
    _t("λ_z", lam_z, "—", expr="λ_z = l0_z/i_z",
       subst=f"{l0_z:.4g}/{section.radius_z:.4g}")
    _t("λ_lim,z", lam_lim_z, "—", clause="EN 1992-1-1 Eq. 5.13N",
       expr="λ_lim = f(n, φ_ef, ω, r_m)",
       subst=f"n={n_ratio:.3g}, φ_ef={inp.phi_ef:g}, ω={omega:.3g}, "
             f"r_m={(f'{rm_z:.3g}' if rm_z is not None else '—')}",
       ok=(not slender_z))

    theta0 = 1.0 / 200.0
    alpha_h = max(2.0 / 3.0, min(1.0, 2.0 / math.sqrt(inp.length_m))) if inp.length_m > 0 else 1.0
    alpha_m = 1.0
    theta_i = theta0 * alpha_h * alpha_m

    h_y = section.height
    h_z = section.width
    e0_y = max(h_y / 30.0, 0.02)
    e0_z = max(h_z / 30.0, 0.02)

    method = inp.second_order_method
    _sec(f"Second-order moment ({method})")

    def _combine(axis, l0, lam, slender, e0, m02, h, d):
        ei = theta_i * l0 / 2.0
        m0_ed = max(abs(m02), n_ed * (e0 + ei))
        if not slender or n_ed <= 0.0:
            return m0_ed, 0.0, 0.0, None
        if method == "nominal_stiffness":
            ic = (section.width * section.height ** 3 / 12.0 if axis == "z"
                  else section.height * section.width ** 3 / 12.0)
            n_b, m_total, stable = nominal_stiffness_moment(
                n_ed, m0_ed, ac, ic, conc.Ecm, conc.fck, lam, l0, inp.phi_ef,
                es_mpa=reinf.Es, i_s=None, include_steel=False)
            m2 = (m_total - m0_ed) if stable else float("inf")
            e2 = (m2 / n_ed) if n_ed > 0 and stable else 0.0
            return (m0_ed if stable else float("inf")), e2, m2, n_b
        e2, m2 = nominal_curvature_e2(
            n_ed, ac, fcd, as_total_m2, fyd, conc.fck, reinf.Es, lam, l0,
            inp.phi_ef, d)
        return m0_ed, e2, m2, None

    d_y = h_y - inp.cover_m
    d_z = h_z - inp.cover_m
    m0_ed_y, e2_y, m2_y, n_b_y = _combine(
        "z", l0_y, lam_y, slender_y, e0_y, inp.m02_y, h_y, d_y)
    m0_ed_z, e2_z, m2_z, n_b_z = _combine(
        "y", l0_z, lam_z, slender_z, e0_z, inp.m02_z, h_z, d_z)

    med_y_design = m0_ed_y + m2_y if math.isfinite(m0_ed_y) else float("inf")
    med_z_design = m0_ed_z + m2_z if math.isfinite(m0_ed_z) else float("inf")
    med_y_design += abs(inp.my_ed)
    med_z_design += abs(inp.mz_ed)

    _t("e2_y", e2_y, "m")
    _t("M2_y", m2_y, "kNm")
    _t("M_Ed,y (design)", med_y_design, "kNm", clause="EN 1992-1-1 §5.8.8")
    _t("e2_z", e2_z, "m")
    _t("M2_z", m2_z, "kNm")
    _t("M_Ed,z (design)", med_z_design, "kNm", clause="EN 1992-1-1 §5.8.8")

    mrd_y = uniaxial_moment_resistance(inp, n_ed, "z", trace=rep)
    mrd_z = uniaxial_moment_resistance(inp, n_ed, "y", trace=rep)

    a = biaxial_interaction_exponent(n_ratio)
    ry = (med_y_design / mrd_y) if mrd_y > 0 else float("inf")
    rz = (med_z_design / mrd_z) if mrd_z > 0 else float("inf")
    utilization = ry ** a + rz ** a if math.isfinite(ry) and math.isfinite(rz) else float("inf")
    passed = utilization <= 1.0

    _sec("Biaxial interaction (§5.8.9)")
    _t("a", a, "—", clause="EN 1992-1-1 Eq. 5.8.9(4)")
    _t("Utilisation", utilization, "—",
       expr="(M_Ed,y/M_Rd,y)^a + (M_Ed,z/M_Rd,z)^a",
       subst=f"({med_y_design:.4g}/{mrd_y:.4g})^{a:.3g} + "
             f"({med_z_design:.4g}/{mrd_z:.4g})^{a:.3g}",
       ok=passed)

    return ColumnResult(
        lambda_y=lam_y, lambda_z=lam_z,
        lambda_lim_y=lam_lim_y, lambda_lim_z=lam_lim_z,
        slender_y=slender_y, slender_z=slender_z,
        e2_y=e2_y, e2_z=e2_z, m2_y=m2_y, m2_z=m2_z,
        n_b_y=n_b_y, n_b_z=n_b_z, method_used=method,
        med_y_design=med_y_design, med_z_design=med_z_design,
        biaxial_exponent_a=a, mrd_y=mrd_y, mrd_z=mrd_z,
        n_ratio=n_ratio, utilization=utilization, passed=passed,
        details={"omega": omega, "theta_i": theta_i, "l0_y": l0_y, "l0_z": l0_z},
    )


# ---------------------------------------------------------------------------
# Fase 4 — automatic reinforcement design (dev/RC_COLUMN_DESIGN.md §5.4)
# ---------------------------------------------------------------------------

def minimum_column_reinforcement_m2(ac_m2: float, n_ed: float, fyk_mpa: float,
                                    gamma_s: float = 1.15) -> float:
    """EC2 §9.5.2(2): As,min = max(0.10*N_Ed/f_yd, 0.002*Ac) [m²].

    ``n_ed`` [kN] compression-positive (as elsewhere in this module),
    ``ac_m2`` [m²], ``fyk_mpa`` [MPa]. A non-compressive N_Ed (n_ed<=0)
    still requires the geometric minimum 0.002*Ac.
    """
    fyd_mpa = fyk_mpa / gamma_s
    as_force = max(n_ed, 0.0) / (fyd_mpa * 1000.0)  # MPa -> kN/m2
    return max(0.10 * as_force, 0.002 * ac_m2)


def maximum_column_reinforcement_m2(ac_m2: float) -> float:
    """EC2 §9.5.2(3): As,max = 0.04*Ac outside lap locations."""
    return 0.04 * ac_m2


def design_column_reinforcement(
    inp: ColumnInput,
    diameters_mm: tuple = (10.0, 12.0, 16.0, 20.0, 25.0, 32.0, 40.0),
    n_bars_options: tuple = (4, 6, 8, 10, 12, 16, 20),
    n_per_face_options: tuple = (2, 3, 4, 5, 6),
) -> tuple[ColumnInput, "ColumnResult"]:
    """Suggest the lightest reinforcement layout that satisfies both the EC2
    §9.5.2 min/max reinforcement ratios and the full §5.8/§6.1 column check
    (:func:`eurocode2_column_check`).

    ``inp.rebar`` is ignored (a placeholder value is fine). For a circular
    section, every ``(n_bars, diameter)`` combination in ``n_bars_options`` x
    ``diameters_mm`` is tried (:meth:`RebarLayout.symmetric_circular` — a
    circle has no face direction to split bars over, so a single bar count
    is all it needs). For a rectangular section, every ``(n_y, n_z,
    diameter)`` combination in ``n_per_face_options`` x ``n_per_face_options``
    x ``diameters_mm`` is tried instead
    (:meth:`RebarLayout.symmetric_rectangular_biaxial`) — independent counts
    per face direction let the search put more steel where the governing
    bending direction (M_y or M_z) actually needs it, rather than always
    spreading it symmetrically. Either way, the geometrically valid
    candidates (min <= As <= max) are ranked by total steel area, and the
    lightest one that passes the full check is returned.

    Returns ``(updated_input, result)`` where ``updated_input`` is ``inp``
    with ``rebar`` replaced by the chosen layout — pass it back through
    :func:`eurocode2_column_check` (or its trace variant) to get a full
    calculation report for the chosen reinforcement.

    Raises
    ------
    ValueError
        If no combination within the given search ranges satisfies EC2 —
        the section needs to be enlarged, or the ranges widened.
    """
    from dataclasses import replace

    ac_m2 = inp.section.area
    as_min = minimum_column_reinforcement_m2(ac_m2, inp.n_ed, inp.reinforcement.fyk)
    as_max = maximum_column_reinforcement_m2(ac_m2)

    circular = isinstance(inp.section, CircularCrossSection)

    candidates = []
    if circular:
        min_bars_floor = 3
        for n_bars in n_bars_options:
            if n_bars < min_bars_floor:
                continue
            for dia in diameters_mm:
                try:
                    rebar = RebarLayout.symmetric_circular(
                        inp.section, inp.cover_m, n_bars, dia)
                except ValueError:
                    continue
                as_total = rebar.total_area_cm2() / 1e4
                if as_total < as_min or as_total > as_max:
                    continue
                candidates.append((as_total, (n_bars,), dia, rebar))
    else:
        min_per_face = 2
        for n_y in n_per_face_options:
            if n_y < min_per_face:
                continue
            for n_z in n_per_face_options:
                if n_z < min_per_face:
                    continue
                for dia in diameters_mm:
                    try:
                        rebar = RebarLayout.symmetric_rectangular_biaxial(
                            inp.section, inp.cover_m, n_y, n_z, dia)
                    except ValueError:
                        continue
                    as_total = rebar.total_area_cm2() / 1e4
                    if as_total < as_min or as_total > as_max:
                        continue
                    candidates.append((as_total, (n_y, n_z), dia, rebar))
    candidates.sort(key=lambda c: c[0])

    for as_total, _n, _dia, rebar in candidates:
        trial = replace(inp, rebar=rebar)
        res = eurocode2_column_check(trial)
        if res.passed:
            return trial, res

    msg = ("No reinforcement layout within the searched diameters "
          f"{diameters_mm} and bar counts "
          f"{n_bars_options if circular else n_per_face_options} satisfies "
          "both EC2 §9.5.2 (min/max reinforcement) and the §5.8/§6.1 column "
          "check — enlarge the section, reduce the actions, or widen the "
          "search ranges.")
    raise ValueError(msg)
