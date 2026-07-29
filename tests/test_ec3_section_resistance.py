"""Tests for the EN 1993-1-1 §6.2 cross-section resistance
(``eurocodepy.ec3.uls.cross_section``) — shear (Vy, Vz), torsion and the
interaction with N, My, Mz.

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_ec3_section_resistance.py
"""
import math

import pytest

from eurocodepy import ec3
from eurocodepy.ec3.uls import cross_section as sr

# IPE300, S275, in SI (mm) — hand-checked reference section.
IPE300 = dict(
    kind="I", fy=275.0, gamma_M0=1.0,
    area=5381.0, b=150.0, h=300.0, tw=7.1, tf=10.7, hw=248.6,
    eps=math.sqrt(235.0 / 275.0),
    wpl_y=628400.0, wpl_z=125200.0, wel_y=557100.0, wel_z=80500.0,
    wt=27820.0, av_y=3210.0, av_z=2568.0,
)


def _inp(cls=1, **kw):
    d = dict(IPE300); d["section_class"] = cls; d.update(kw)
    return sr.SectionResistanceInput(**d)


# ── elementary resistances ──────────────────────────────────────────────────

def test_shear_and_torsion_resistances():
    assert sr.shear_resistance(2568.0, 275.0) == pytest.approx(407.7, abs=0.2)
    assert sr.shear_resistance(3210.0, 275.0) == pytest.approx(509.6, abs=0.2)
    assert sr.torsion_resistance(27820.0, 275.0) == pytest.approx(4.417, abs=2e-3)


def test_shear_buckling_flag():
    # IPE300 web is stocky; a very slender web trips the flag.
    assert sr.shear_buckling_susceptible(248.6, 7.1, IPE300["eps"]) is False
    assert sr.shear_buckling_susceptible(1000.0, 5.0, 1.0) is True


# ── single-action utilisations ──────────────────────────────────────────────

def test_pure_shear():
    r = sr.eurocode3_section_check(_inp(), sr.SectionForces(vz_ed=200.0))
    assert r.util_shear_z == pytest.approx(200.0 / 407.7, abs=2e-3)
    assert r.util_shear_y == 0.0


def test_pure_torsion():
    r = sr.eurocode3_section_check(_inp(), sr.SectionForces(t_ed=2.0))
    assert r.util_torsion == pytest.approx(2.0 / 4.417, abs=3e-3)


def test_pure_moments_read_as_linear_ratio():
    r_y = sr.eurocode3_section_check(_inp(), sr.SectionForces(my_ed=100.0))
    assert r_y.util_bending_axial == pytest.approx(100.0 / 172.81, abs=3e-3)
    r_z = sr.eurocode3_section_check(_inp(), sr.SectionForces(mz_ed=20.0))
    assert r_z.util_bending_axial == pytest.approx(20.0 / 34.43, abs=3e-3)


def test_pure_axial_is_n_over_npl():
    r = sr.eurocode3_section_check(_inp(), sr.SectionForces(n_ed=500.0))
    assert r.util_bending_axial == pytest.approx(500.0 / 1479.8, abs=3e-3)


def test_at_moment_capacity_utilisation_is_one():
    r = sr.eurocode3_section_check(_inp(), sr.SectionForces(my_ed=172.81))
    assert r.util_bending_axial == pytest.approx(1.0, abs=1e-3)


# ── interactions ────────────────────────────────────────────────────────────

def test_axial_reduces_the_moment_capacity():
    m_only = sr.eurocode3_section_check(_inp(), sr.SectionForces(my_ed=120.0))
    m_and_n = sr.eurocode3_section_check(
        _inp(), sr.SectionForces(n_ed=600.0, my_ed=120.0))
    assert m_and_n.util_bending_axial > m_only.util_bending_axial


def test_biaxial_bending_adds():
    uni = sr.eurocode3_section_check(_inp(), sr.SectionForces(my_ed=100.0))
    bi = sr.eurocode3_section_check(
        _inp(), sr.SectionForces(my_ed=100.0, mz_ed=15.0))
    assert bi.util_bending_axial > uni.util_bending_axial


def test_high_shear_reduces_bending_capacity():
    low = sr.eurocode3_section_check(
        _inp(), sr.SectionForces(my_ed=150.0, vz_ed=100.0))
    high = sr.eurocode3_section_check(
        _inp(), sr.SectionForces(my_ed=150.0, vz_ed=350.0))
    assert not low.shear_reduces_moment
    assert high.shear_reduces_moment           # Vz > 0.5·Vpl,z
    assert high.util_bending_axial > low.util_bending_axial


def test_torsion_reduces_the_shear_resistance():
    no_t = sr.eurocode3_section_check(_inp(), sr.SectionForces(vz_ed=200.0))
    with_t = sr.eurocode3_section_check(
        _inp(), sr.SectionForces(vz_ed=200.0, t_ed=3.0))
    assert with_t.vpl_rd_z < no_t.vpl_rd_z
    assert with_t.util_shear_z > no_t.util_shear_z


# ── classes 3 / 4 ───────────────────────────────────────────────────────────

def test_class3_is_the_elastic_stress_check():
    r = sr.eurocode3_section_check(_inp(cls=3), sr.SectionForces(n_ed=300.0, my_ed=80.0))
    sig = 300e3 / 5381.0 + 80e6 / 557100.0
    assert r.util_bending_axial == pytest.approx(sig / 275.0, rel=1e-6)


def test_class4_uses_effective_properties_and_shift():
    inp = _inp(cls=4, area_eff=4000.0, weff_y=5.0e5, weff_z=6.0e4, d_my=5.0)
    r = sr.eurocode3_section_check(inp, sr.SectionForces(n_ed=200.0, my_ed=60.0))
    sig = 200e3 / 4000.0 + (60.0 + 5.0) * 1e6 / 5.0e5
    assert r.util_bending_axial == pytest.approx(sig / 275.0, rel=1e-6)


# ── combined + profile wrapper ──────────────────────────────────────────────

def test_combined_governing_and_pass():
    r = sr.eurocode3_section_check(
        _inp(), sr.SectionForces(n_ed=300.0, my_ed=120.0, mz_ed=15.0,
                                 vz_ed=150.0, t_ed=1.0))
    assert r.utilization == max(r.util_shear_y, r.util_shear_z,
                                r.util_torsion, r.util_bending_axial)
    assert r.passed is (r.utilization <= 1.0)


def test_section_check_profile_runs_for_a_catalogue_ipe():
    r = ec3.section_check_profile(
        ec3.ProfilesI["IPE300"], 275.0,
        sr.SectionForces(n_ed=300.0, my_ed=120.0, vz_ed=150.0))
    assert isinstance(r, sr.SectionResistanceResult)
    assert 0.0 < r.utilization < 3.0
