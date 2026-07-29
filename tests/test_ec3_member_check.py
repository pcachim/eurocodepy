"""Tests for the EN 1993-1-1 §6.3.3 combined member check
(``eurocodepy.ec3.uls.member_buckling``) — flexural buckling, lateral-torsional
buckling and the Annex B interaction of N + My + Mz.

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_ec3_member_check.py
"""
import math

import pytest

from eurocodepy import ec3
from eurocodepy.ec3.uls import member_buckling as mb

# IPE300 section properties in SI (mm), used across the combined-check tests.
IPE300 = dict(
    area=5381.0, w_y=628400.0, w_z=125200.0,
    iy=8.356e7, iz=6.038e6, it=1.975e5, iw=1.2426e11,
    curve_y="a", curve_z="b", curve_lt="b", fy=275.0, section_class=1,
)


# ── reduction factors against EN 1993-1-1 Table 6.4 ─────────────────────────

def test_reduction_chi_matches_table_6_4_at_lambda_one():
    assert mb.reduction_chi(1.0, "a") == pytest.approx(0.6656, abs=5e-4)
    assert mb.reduction_chi(1.0, "b") == pytest.approx(0.5970, abs=5e-4)
    assert mb.reduction_chi(1.0, "c") == pytest.approx(0.5399, abs=5e-4)
    assert mb.reduction_chi(1.0, "d") == pytest.approx(0.4671, abs=5e-4)


def test_reduction_chi_plateau_and_monotonicity():
    assert mb.reduction_chi(0.2, "b") == 1.0
    assert mb.reduction_chi(0.0, "b") == 1.0
    # χ decreases as slenderness grows
    assert mb.reduction_chi(0.5, "b") > mb.reduction_chi(1.5, "b")


def test_reduction_chi_lt_plateau_and_cap():
    assert mb.reduction_chi_lt(0.4, "b", rolled=True) == 1.0     # λ̄ ≤ λ̄_LT,0
    chi = mb.reduction_chi_lt(1.5, "b", rolled=True)
    assert 0.0 < chi <= min(1.0, 1.0 / 1.5**2) + 1e-9


def test_elastic_critical_moment_scales_and_is_positive():
    mcr = mb.elastic_critical_moment(6.038e6, 1.975e5, 1.2426e11, 4000.0)
    assert mcr > 0
    # doubling C1 doubles M_cr
    mcr2 = mb.elastic_critical_moment(6.038e6, 1.975e5, 1.2426e11, 4000.0, c1=2.0)
    assert mcr2 == pytest.approx(2.0 * mcr, rel=1e-12)


def test_cm_factor_linear_diagram():
    assert mb.cm_factor(1.0) == pytest.approx(1.0)
    assert mb.cm_factor(0.0) == pytest.approx(0.6)
    assert mb.cm_factor(-1.0) == pytest.approx(0.4)     # floor at 0.4


# ── the combined check ──────────────────────────────────────────────────────

def test_pure_strut_equals_flexural_buckling_resistance():
    r = mb.eurocode3_member_check(mb.MemberInput(
        n_ed=300.0, my_ed=0.0, mz_ed=0.0,
        lcr_y=4000.0, lcr_z=4000.0, **IPE300))
    # No bending ⇒ utilization is the weak-axis buckling ratio N/Nb,Rd,z.
    nb_rd_z = r.details["Nb_Rd_z"]
    assert r.utilization == pytest.approx(300.0 / nb_rd_z, rel=1e-9)
    assert r.chi_lt == 1.0                    # no LTB without a moment


def test_short_member_has_no_buckling_reduction():
    r = mb.eurocode3_member_check(mb.MemberInput(
        n_ed=300.0, my_ed=0.0, mz_ed=0.0,
        lcr_y=1.0, lcr_z=1.0, **IPE300))
    assert r.chi_y == pytest.approx(1.0)
    assert r.chi_z == pytest.approx(1.0)
    npl_rd = IPE300["area"] * IPE300["fy"] / 1e3
    assert r.utilization == pytest.approx(300.0 / npl_rd, rel=1e-9)


def test_worked_ipe300_beam_column():
    # Hand-checked: (6.61) ≈ 0.612, (6.62) ≈ 0.913, governed by weak axis + LTB.
    r = mb.eurocode3_member_check(mb.MemberInput(
        n_ed=300.0, my_ed=50.0, mz_ed=0.0,
        lcr_y=4000.0, lcr_z=4000.0, l_lt=4000.0,
        cmy=0.9, cmz=0.9, cm_lt=0.9, **IPE300))
    assert r.util_6_61 == pytest.approx(0.612, abs=5e-3)
    assert r.util_6_62 == pytest.approx(0.913, abs=5e-3)
    assert r.utilization == pytest.approx(r.util_6_62)
    assert r.passed is True
    assert r.lambda_z == pytest.approx(1.3755, abs=1e-3)
    assert r.chi_lt == pytest.approx(0.6725, abs=2e-3)


def test_utilization_increases_with_axial_force():
    def util(n):
        return mb.eurocode3_member_check(mb.MemberInput(
            n_ed=n, my_ed=50.0, lcr_y=4000.0, lcr_z=4000.0,
            cmy=0.9, cmz=0.9, cm_lt=0.9, **IPE300)).utilization

    assert util(100.0) < util(300.0) < util(600.0)


def test_biaxial_bending_adds_to_utilization():
    common = dict(n_ed=200.0, my_ed=40.0, lcr_y=4000.0, lcr_z=4000.0,
                  cmy=0.9, cmz=0.9, cm_lt=0.9, **IPE300)
    uniaxial = mb.eurocode3_member_check(mb.MemberInput(mz_ed=0.0, **common))
    biaxial = mb.eurocode3_member_check(mb.MemberInput(mz_ed=10.0, **common))
    assert biaxial.utilization > uniaxial.utilization


def test_not_susceptible_to_lt_uses_chi_lt_one():
    r = mb.eurocode3_member_check(mb.MemberInput(
        n_ed=300.0, my_ed=50.0, lcr_y=4000.0, lcr_z=4000.0,
        susceptible_lt=False, cmy=0.9, cmz=0.9, cm_lt=0.9, **IPE300))
    assert r.chi_lt == 1.0


# ── profile convenience wrapper (needs the eurocodepy profile DB) ───────────

def test_member_check_profile_runs_for_a_catalogue_ipe():
    r = ec3.member_check_profile(
        ec3.ProfilesI["IPE300"], fy=275.0,
        n_ed=300.0, my_ed=50.0, mz_ed=0.0,
        lcr_y=4000.0, lcr_z=4000.0)
    assert isinstance(r, mb.MemberCheckResult)
    assert 0.0 < r.utilization < 2.0
    assert math.isfinite(r.m_cr)
