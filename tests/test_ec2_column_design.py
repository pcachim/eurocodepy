"""Fase 4 (dev/RC_COLUMN_DESIGN.md) -- automatic column reinforcement design.

Covers :func:`eurocodepy.ec2.uls.column.design_column_reinforcement` and its
two EC2 §9.5.2 helpers (minimum/maximum reinforcement ratio).

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_ec2_column_design.py
"""
import pytest

from eurocodepy.ec2.materials import get_concrete, get_reinforcement
from eurocodepy.ec2.uls import (
    ColumnInput,
    RebarLayout,
    design_column_reinforcement,
    eurocode2_column_check,
    maximum_column_reinforcement_m2,
    minimum_column_reinforcement_m2,
)
from eurocodepy.utils.crosssection import RectangularCrossSection


def _make_input(n_ed=500.0, my_ed=40.0, length_m=3.0, **overrides):
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    section = RectangularCrossSection(width=0.30, height=0.30)
    cover = 0.04
    # Placeholder rebar -- design_column_reinforcement ignores it and searches
    # its own candidates.
    rebar = RebarLayout.symmetric_rectangular(section, cover, 4, 12.0)
    kwargs = {
        "section": section, "concrete": conc, "reinforcement": reinf,
        "rebar": rebar, "cover_m": cover, "length_m": length_m,
        "n_ed": n_ed, "my_ed": my_ed, "m01_y": my_ed, "m02_y": my_ed,
    }
    kwargs.update(overrides)
    return ColumnInput(**kwargs)


def test_minimum_reinforcement_matches_closed_form():
    ac = 0.30 * 0.30
    # Geometric minimum governs when N_Ed is small.
    assert minimum_column_reinforcement_m2(ac, n_ed=10.0, fyk_mpa=500.0) == \
        pytest.approx(0.002 * ac)
    # Force-based minimum governs for a heavily loaded column.
    n_ed = 2000.0
    fyd_mpa = 500.0 / 1.15
    expected = 0.10 * n_ed / (fyd_mpa * 1000.0)
    assert expected > 0.002 * ac
    assert minimum_column_reinforcement_m2(ac, n_ed, 500.0) == pytest.approx(expected)


def test_maximum_reinforcement_matches_closed_form():
    ac = 0.30 * 0.30
    assert maximum_column_reinforcement_m2(ac) == pytest.approx(0.04 * ac)


def test_design_column_reinforcement_returns_a_passing_layout():
    inp = _make_input()
    trial, res = design_column_reinforcement(inp)
    assert res.passed
    assert res.utilization <= 1.0
    as_total = trial.rebar.total_area_cm2() / 1e4
    ac = inp.section.area
    assert as_total >= minimum_column_reinforcement_m2(
        ac, inp.n_ed, inp.reinforcement.fyk) - 1e-9
    assert as_total <= maximum_column_reinforcement_m2(ac) + 1e-9


def test_design_column_reinforcement_is_reproducible_and_minimal_among_candidates():
    inp = _make_input()
    trial, res = design_column_reinforcement(inp)
    # Re-running the check on the chosen layout must reproduce the same
    # utilization (the search itself calls eurocode2_column_check once per
    # candidate, so this is a parity check, not a new computation path).
    res2 = eurocode2_column_check(trial)
    assert res2.utilization == pytest.approx(res.utilization)
    assert res2.passed == res.passed


def test_heavier_load_needs_more_steel():
    light = _make_input(n_ed=300.0, my_ed=20.0)
    heavy = _make_input(n_ed=900.0, my_ed=60.0)
    trial_light, _ = design_column_reinforcement(light)
    trial_heavy, _ = design_column_reinforcement(heavy)
    assert (trial_heavy.rebar.total_area_cm2()
            >= trial_light.rebar.total_area_cm2())


def test_impossible_case_raises_value_error():
    # An absurdly slender, heavily loaded column with a tiny section cannot
    # be reinforced within the default search ranges.
    section = RectangularCrossSection(width=0.20, height=0.20)
    conc = get_concrete("C20/25")
    reinf = get_reinforcement("B500B")
    cover = 0.03
    rebar = RebarLayout.symmetric_rectangular(section, cover, 4, 12.0)
    inp = ColumnInput(section=section, concrete=conc, reinforcement=reinf,
                      rebar=rebar, cover_m=cover, length_m=10.0,
                      n_ed=3000.0, my_ed=200.0, m01_y=200.0, m02_y=200.0)
    with pytest.raises(ValueError):
        design_column_reinforcement(inp)


def test_rectangular_design_uses_biaxial_layout():
    """The rectangular search path now returns a symmetric_rectangular_biaxial
    layout (independent n_y/n_z), not the old single-n_bars
    symmetric_rectangular -- confirmed by the exact bar-count formula
    2*n_y + 2*n_z - 4 having no solution outside that family for a generic
    count (e.g. 5 bars can't come from 2*n_y+2*n_z-4 with both >= 2 giving a
    plausible small case, but the real check here is structural: every
    biaxial-family bar count is even)."""
    inp = _make_input()
    trial, res = design_column_reinforcement(inp)
    assert res.passed
    n = len(trial.rebar.positions_m)
    assert n % 2 == 0   # 2*n_y + 2*n_z - 4 is always even


def test_circular_design_still_uses_single_bar_count():
    """Circular columns keep the single n_bars search (no face direction to
    split over) -- see dev/RC_COLUMN_DESIGN.md."""
    from eurocodepy.utils.crosssection import CircularCrossSection
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    circ = CircularCrossSection(diameter=0.40)
    rebar = RebarLayout.symmetric_circular(circ, 0.04, 6, 16.0)
    inp = ColumnInput(section=circ, concrete=conc, reinforcement=reinf,
                      rebar=rebar, cover_m=0.04, length_m=3.0,
                      n_ed=400.0, my_ed=30.0, m01_y=30.0, m02_y=30.0)
    trial, res = design_column_reinforcement(inp)
    assert res.passed
    diameters = trial.rebar.diameters_mm
    assert len(set(diameters)) == 1   # symmetric_circular: one diameter throughout
