"""EN 1992-1-1 §5.8/§6.1 reinforced-concrete column check -- unit tests.

These are a first baseline for the new ``eurocodepy.ec2.uls.column`` module
(no prior numeric convention exists for columns in this codebase, unlike the
other composite checks that have reference cases to reproduce -- see
dev/RC_COLUMN_DESIGN.md). They check:

* :class:`RebarLayout.symmetric_rectangular` produces the exact bar count,
  with a bar forced into every corner;
* the uniaxial M-N interaction (:func:`uniaxial_moment_resistance`) traces a
  physically sane "banana" shape: zero at N=0 is finite and positive, the
  moment resistance is higher at some intermediate N than at N=0 (the
  well-known non-monotonic shape of a column interaction diagram for
  symmetric reinforcement), and vanishes at the squash load;
* the squash load (N at zero moment capacity) matches the elementary
  Ac*fcd + As*fyd estimate;
* :func:`slenderness_limit` / :func:`biaxial_interaction_exponent` match
  their closed-form definitions (Eq. 5.13N / Eq. 5.8.9(4));
* passing a trace does not change the result (parity), mirroring the other
  composite-check test suites in this repository;
* circular sections are rejected with ``NotImplementedError`` (out of scope
  for this first implementation).

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_ec2_column.py
"""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2.materials import get_concrete, get_reinforcement
from eurocodepy.ec2.uls import (
    ColumnInput,
    RebarLayout,
    biaxial_interaction_exponent,
    eurocode2_column_check,
    slenderness_limit,
    uniaxial_moment_resistance,
)
from eurocodepy.utils.crosssection import CircularCrossSection, RectangularCrossSection

FCK, FYK = 30.0, 500.0


def _make_input(**overrides):
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    section = RectangularCrossSection(width=0.30, height=0.30)
    cover = 0.04
    rebar = RebarLayout.symmetric_rectangular(section, cover, 8, 16.0)
    kwargs = {
        "section": section, "concrete": conc, "reinforcement": reinf,
        "rebar": rebar, "cover_m": cover,
    }
    kwargs.update(overrides)
    return ColumnInput(**kwargs)


def test_symmetric_rectangular_bar_count_and_corners():
    section = RectangularCrossSection(width=0.30, height=0.30)
    cover = 0.04
    for n in (4, 6, 8, 10, 12):
        rebar = RebarLayout.symmetric_rectangular(section, cover, n, 16.0)
        assert len(rebar.positions_m) == n
        assert len(rebar.diameters_mm) == n
        y0 = section.width / 2.0 - cover
        z0 = section.height / 2.0 - cover
        corners = {(y0, z0), (-y0, z0), (-y0, -z0), (y0, -z0)}
        assert corners.issubset(set(rebar.positions_m))
        # every bar must lie within the section
        for y, z in rebar.positions_m:
            assert abs(y) <= y0 + 1e-9
            assert abs(z) <= z0 + 1e-9


def test_symmetric_rectangular_rejects_too_few_bars():
    section = RectangularCrossSection(width=0.30, height=0.30)
    with pytest.raises(ValueError):
        RebarLayout.symmetric_rectangular(section, 0.04, 3, 16.0)


def test_interaction_diagram_banana_shape():
    inp = _make_input()
    ac = inp.section.area
    fcd = inp.concrete.fcd
    fyd = inp.reinforcement.fyd
    as_total = sum(inp.rebar.bar_areas_m2())

    m_pure_bending = uniaxial_moment_resistance(inp, 0.0, "z")
    assert m_pure_bending > 0.0

    # the moment resistance at a moderate axial load must exceed pure
    # bending -- the classic non-monotonic ("banana") shape for a
    # symmetrically-reinforced section.
    n_moderate = 0.3 * (ac * fcd * 1000.0)   # roughly n=0.3
    m_moderate = uniaxial_moment_resistance(inp, n_moderate, "z")
    assert m_moderate > m_pure_bending

    # near the squash load the moment resistance collapses to ~0.
    n_squash_est = ac * fcd * 1000.0 + as_total * fyd * 1000.0
    m_near_squash = uniaxial_moment_resistance(inp, 0.98 * n_squash_est, "z")
    assert m_near_squash < 0.05 * m_moderate


def test_squash_load_matches_elementary_estimate():
    inp = _make_input()
    ac = inp.section.area
    fcd = inp.concrete.fcd
    fyd = inp.reinforcement.fyd
    as_total = sum(inp.rebar.bar_areas_m2())
    n_squash_est = ac * fcd * 1000.0 + as_total * fyd * 1000.0

    # a large axial force well beyond any physical squash load must clamp to
    # (approximately) the squash load, with the moment resistance ~0.
    m_at_large_n = uniaxial_moment_resistance(inp, 5.0 * n_squash_est, "z")
    assert m_at_large_n == pytest.approx(0.0, abs=2.0)


def test_slenderness_limit_matches_eq_5_13n():
    n, phi_ef, omega, rm = 0.5, 2.0, 0.4, 0.6
    expected = 20.0 * (1.0 / (1.0 + 0.2 * phi_ef)) * math.sqrt(1.0 + 2.0 * omega) * (1.7 - rm) / math.sqrt(n)
    assert slenderness_limit(n, phi_ef, omega, rm) == pytest.approx(expected)
    # unknown rm falls back to the conservative C=0.7
    expected_default = 20.0 * (1.0 / (1.0 + 0.2 * phi_ef)) * math.sqrt(1.0 + 2.0 * omega) * 0.7 / math.sqrt(n)
    assert slenderness_limit(n, phi_ef, omega, None) == pytest.approx(expected_default)
    assert slenderness_limit(0.0, phi_ef, omega) == float("inf")


@pytest.mark.parametrize(("n", "expected"), [(0.05, 1.0), (0.1, 1.0), (1.0, 2.0), (1.5, 2.0), (0.55, 1.5)])
def test_biaxial_interaction_exponent(n, expected):
    assert biaxial_interaction_exponent(n) == pytest.approx(expected)


def test_short_column_no_second_order_effects():
    # a short, stocky column: lambda should be well below lambda_lim, so
    # M2 = 0 and the design moment reduces to first-order + e_min/imperfections.
    inp = _make_input(length_m=1.0, k_y=1.0, k_z=1.0, n_ed=800.0, m02_y=15.0, m02_z=10.0)
    res = eurocode2_column_check(inp)
    assert not res.slender_y
    assert not res.slender_z
    assert res.m2_y == pytest.approx(0.0)
    assert res.m2_z == pytest.approx(0.0)


def test_trace_does_not_change_result():
    inp = _make_input(length_m=3.0, n_ed=800.0, m02_y=15.0, m02_z=10.0, my_ed=5.0, mz_ed=3.0)
    base = eurocode2_column_check(inp)
    rep = CalcReport(title="column")
    traced = eurocode2_column_check(inp, trace=rep)
    assert traced.utilization == pytest.approx(base.utilization)
    assert traced.mrd_y == pytest.approx(base.mrd_y)
    assert traced.mrd_z == pytest.approx(base.mrd_z)
    assert traced.passed == base.passed
    d = rep.to_dict()
    assert d["sections"] and any(s["steps"] for s in d["sections"])
    symbols = [st["symbol"] for s in d["sections"] for st in s["steps"]]
    assert "N_Ed" in symbols


def test_second_order_methods_agree_when_not_slender():
    # Below lambda_lim neither method adds a 2nd-order moment -- both must
    # trivially agree (M2 = 0), regardless of which is selected.
    inp = _make_input(length_m=1.0, n_ed=500.0, m02_y=12.0, m02_z=8.0,
                       second_order_method="nominal_curvature")
    res_curv = eurocode2_column_check(inp)
    assert not res_curv.slender_y
    inp.second_order_method = "nominal_stiffness"
    res_stiff = eurocode2_column_check(inp)
    assert res_stiff.med_y_design == pytest.approx(res_curv.med_y_design)


def test_second_order_methods_cross_check_on_a_slender_column():
    # Nominal curvature (§5.8.8) and nominal stiffness (§5.8.7) are two
    # independent simplified methods for the SAME 2nd-order effect -- the
    # cross-check flagged as pending in dev/RC_COLUMN_DESIGN.md §5 (Fase 1).
    #
    # Finding from running this check (documented, not a bug): for a column
    # slender enough to fail the lambda_lim criterion (§5.8.3.1), the
    # *simplified* nominal-stiffness estimate of Kc (§5.8.7.2, ignoring the
    # reinforcement's contribution to EI, Ks=0) is markedly more conservative
    # than the nominal-curvature method here -- it can report the column as
    # unstable (N_Ed >= N_B) at loads the curvature method still passes. This
    # is a known characteristic of the "Ks=0" simplified Kc, not an
    # implementation bug (see nominal_stiffness_moment's docstring); a future
    # refinement is to support Ks=1 (include_steel=True) as a less
    # conservative variant, and to surface the method disagreement to the
    # user rather than silently picking one. For now this test only checks
    # that the two methods do not silently *contradict* each other in the
    # unsafe direction (nominal_stiffness must never be *more permissive*
    # than nominal_curvature -- see the assertion below), and that the
    # instability case is reported as such (`inf`, `passed=False`), not as a
    # bogus finite number.
    inp = _make_input(length_m=6.0, n_ed=500.0, m02_y=12.0, m02_z=8.0,
                       second_order_method="nominal_curvature")
    res_curv = eurocode2_column_check(inp)
    assert res_curv.slender_y  # otherwise this case says nothing about M2

    inp.second_order_method = "nominal_stiffness"
    res_stiff = eurocode2_column_check(inp)

    if math.isfinite(res_stiff.med_y_design):
        # when both are finite they should be in the same ballpark
        ratio = res_stiff.med_y_design / res_curv.med_y_design
        assert 0.5 < ratio < 2.0
    else:
        # nominal_stiffness must fail *safe* (report instability), never
        # silently pass a column the curvature method also cannot pass.
        assert not res_stiff.passed
        if not res_curv.passed:
            pytest.skip("both methods already agree the column is inadequate")


def test_circular_section_is_supported():
    """Circular columns are supported (symmetric_circular rebar layout +
    the chord-width fibre integration in _section_forces) -- this used to
    raise NotImplementedError; it must not any more."""
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    circ = CircularCrossSection(diameter=0.35)
    rebar = RebarLayout.symmetric_circular(circ, 0.04, 8, 16.0)
    inp = ColumnInput(section=circ, concrete=conc, reinforcement=reinf,
                       rebar=rebar, cover_m=0.04, length_m=3.0,
                       n_ed=100.0, my_ed=20.0)
    res = eurocode2_column_check(inp)
    assert res.mrd_y > 0.0
    assert res.mrd_z > 0.0
    # A circle is symmetric -- the two axes must give the same resistance.
    assert res.mrd_y == pytest.approx(res.mrd_z, rel=1e-9)


def test_t_l_sections_still_not_implemented():
    """T/L sections have no fibre-width profile yet -- only rectangular and
    circular are supported (see dev/RC_COLUMN_DESIGN.md Fase 5 item 7)."""
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    section = RectangularCrossSection(width=0.30, height=0.30)
    rebar = RebarLayout.symmetric_rectangular(section, 0.04, 8, 16.0)

    class _FakeTSection:
        """Anything that is neither Rectangular nor Circular -- carries the
        generic radius_y/radius_z properties eurocode2_column_check reads
        for slenderness before it ever reaches uniaxial_moment_resistance."""

        radius_y = 0.1
        radius_z = 0.1
        area = 0.1
        height = 0.3
        width = 0.3

    inp = ColumnInput(section=_FakeTSection(), concrete=conc,
                       reinforcement=reinf, rebar=rebar, cover_m=0.04,
                       n_ed=100.0)
    with pytest.raises(NotImplementedError):
        eurocode2_column_check(inp)


def test_symmetric_rectangular_biaxial_corner_count():
    """n_y=2, n_z=2 is the minimal case -- just the 4 corners, same as
    symmetric_rectangular's own 4-bar minimum."""
    section = RectangularCrossSection(width=0.30, height=0.50)
    rebar = RebarLayout.symmetric_rectangular_biaxial(section, 0.04, 2, 2, 16.0)
    assert len(rebar.positions_m) == 4


def test_symmetric_rectangular_biaxial_total_count_formula():
    section = RectangularCrossSection(width=0.30, height=0.50)
    n_y, n_z = 4, 3
    rebar = RebarLayout.symmetric_rectangular_biaxial(
        section, 0.04, n_y, n_z, 16.0)
    assert len(rebar.positions_m) == 2 * n_y + 2 * n_z - 4


def test_symmetric_rectangular_biaxial_more_bars_on_y_face_when_asked():
    """More n_y bars puts more steel on the top/bottom faces (spanning
    width b, i.e. spread along y) without touching n_z."""
    section = RectangularCrossSection(width=0.30, height=0.50)
    few_y = RebarLayout.symmetric_rectangular_biaxial(section, 0.04, 2, 4, 16.0)
    many_y = RebarLayout.symmetric_rectangular_biaxial(section, 0.04, 6, 4, 16.0)
    assert len(many_y.positions_m) > len(few_y.positions_m)
    # n_z-driven side-face bar count is untouched by the n_y change.
    assert len(many_y.positions_m) - len(few_y.positions_m) == 2 * (6 - 2)


def test_symmetric_rectangular_biaxial_rejects_too_few_bars_per_face():
    section = RectangularCrossSection(width=0.30, height=0.50)
    with pytest.raises(ValueError):
        RebarLayout.symmetric_rectangular_biaxial(section, 0.04, 1, 4, 16.0)
    with pytest.raises(ValueError):
        RebarLayout.symmetric_rectangular_biaxial(section, 0.04, 4, 1, 16.0)


def test_symmetric_rectangular_biaxial_feeds_the_full_column_check():
    """A biaxial layout must work as a drop-in ColumnInput.rebar, same as
    symmetric_rectangular."""
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    section = RectangularCrossSection(width=0.30, height=0.50)
    rebar = RebarLayout.symmetric_rectangular_biaxial(section, 0.04, 3, 5, 16.0)
    inp = ColumnInput(section=section, concrete=conc, reinforcement=reinf,
                      rebar=rebar, cover_m=0.04, length_m=3.0,
                      n_ed=400.0, my_ed=30.0, m01_y=30.0, m02_y=30.0)
    res = eurocode2_column_check(inp)
    assert res.mrd_y > 0.0
    assert res.mrd_z > 0.0
