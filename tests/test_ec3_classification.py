"""Tests for EC3 cross-section classification and Class-4 effective properties
(``eurocodepy.ec3.classification``).

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_ec3_classification.py
"""
import math

import pytest

from eurocodepy import ec3
from eurocodepy.ec3 import classification as cl
from eurocodepy.ec3.classification import SectionClass

# ── material factor ε ───────────────────────────────────────────────────────


def test_epsilon():
    assert cl.epsilon(235.0) == pytest.approx(1.0)
    assert cl.epsilon(355.0) == pytest.approx(math.sqrt(235.0 / 355.0), rel=1e-9)
    with pytest.raises(ValueError):
        cl.epsilon(0.0)


# ── pure part limits (EN 1993-1-1 Table 5.2) ────────────────────────────────

def test_internal_part_pure_compression_limits():
    # ψ = 1, α = 1 → class limits 33 / 38 / 42 · ε
    e = 1.0
    assert cl.classify_internal_part(33.0, e, psi=1.0, alpha=1.0) == SectionClass.CLASS_1
    assert cl.classify_internal_part(37.9, e, psi=1.0, alpha=1.0) == SectionClass.CLASS_2
    assert cl.classify_internal_part(41.9, e, psi=1.0, alpha=1.0) == SectionClass.CLASS_3
    assert cl.classify_internal_part(42.1, e, psi=1.0, alpha=1.0) == SectionClass.CLASS_4


def test_internal_part_pure_bending_limits():
    # ψ = −1, α = 0.5 → class limits 72 / 83 / 124 · ε
    e = 1.0
    assert cl.classify_internal_part(72.0, e, psi=-1.0, alpha=0.5) == SectionClass.CLASS_1
    assert cl.classify_internal_part(82.9, e, psi=-1.0, alpha=0.5) == SectionClass.CLASS_2
    assert cl.classify_internal_part(123.9, e, psi=-1.0, alpha=0.5) == SectionClass.CLASS_3
    assert cl.classify_internal_part(124.1, e, psi=-1.0, alpha=0.5) == SectionClass.CLASS_4


def test_outstand_flange_limits():
    e = 1.0
    assert cl.classify_outstand_part(9.0, e) == SectionClass.CLASS_1
    assert cl.classify_outstand_part(9.5, e) == SectionClass.CLASS_2
    assert cl.classify_outstand_part(13.0, e) == SectionClass.CLASS_3
    assert cl.classify_outstand_part(15.0, e) == SectionClass.CLASS_4


def test_chs_limits():
    e = 1.0  # ε² = 1 → 50 / 70 / 90
    assert cl.classify_chs_part(50.0, e) == SectionClass.CLASS_1
    assert cl.classify_chs_part(69.0, e) == SectionClass.CLASS_2
    assert cl.classify_chs_part(89.0, e) == SectionClass.CLASS_3
    assert cl.classify_chs_part(91.0, e) == SectionClass.CLASS_4


# ── web stress state under N + M ────────────────────────────────────────────

def test_web_alpha_psi_endpoints():
    geo = cl._to_geometry(ec3.ProfilesI["IPE300"])
    # pure bending → α = 0.5, ψ = −1
    a, p = cl.web_alpha_psi(geo, 235.0, 0.0, 80.0)
    assert a == pytest.approx(0.5, abs=1e-6)
    assert p == pytest.approx(-1.0, abs=1e-6)
    # pure compression → α = 1, ψ = 1
    a, p = cl.web_alpha_psi(geo, 235.0, 500.0, 0.0)
    assert a == pytest.approx(1.0, abs=1e-6)
    assert p == pytest.approx(1.0, abs=1e-6)


# ── section classification against known profiles ───────────────────────────

def test_ipe300_bending_is_class1():
    r = cl.classify_section(ec3.ProfilesI["IPE300"], 235.0, n_ed=0.0, m_ed=100.0)
    assert r.section_class == SectionClass.CLASS_1


def test_ipe300_pure_compression_is_class2():
    # web c/t ≈ 35 → between 33ε and 38ε ⇒ Class 2 in uniform compression.
    r = cl.classify_section(ec3.ProfilesI["IPE300"], 235.0, n_ed=800.0, m_ed=0.0)
    assert r.section_class == SectionClass.CLASS_2
    web = next(p for p in r.parts if p.name == "web")
    assert web.part_class == SectionClass.CLASS_2


def test_higher_grade_can_raise_the_class():
    # The same section is at worst equal, usually a higher class, at S355 (ε<1).
    c235 = cl.classify_section(ec3.ProfilesI["IPE600"], 235.0, n_ed=0.0, m_ed=500.0)
    c355 = cl.classify_section(ec3.ProfilesI["IPE600"], 355.0, n_ed=0.0, m_ed=500.0)
    assert int(c355.section_class) >= int(c235.section_class)


def test_slender_shs_is_class4_in_compression():
    r = cl.classify_section(ec3.ProfilesSHS["SHS200x200x5"], 355.0,
                            n_ed=100.0, m_ed=0.0)
    assert r.section_class == SectionClass.CLASS_4


# ── Class-4 effective properties ────────────────────────────────────────────

def test_effective_properties_of_class13_are_the_gross():
    sec = ec3.ProfilesI["IPE300"]
    ep = cl.effective_properties(sec, 235.0)
    assert int(ep.section_class) <= 3
    # gross reference equals the catalogue values
    assert ep.A_gross == pytest.approx(sec.A * 100.0, rel=1e-6)
    # nothing removed → effective equals gross
    assert ep.A_eff == pytest.approx(ep.A_gross, rel=1e-6)
    assert ep.W_eff_y == pytest.approx(ep.W_el_y_gross, rel=1e-6)
    assert ep.e_Ny == pytest.approx(0.0, abs=1e-9)


def test_effective_properties_reduce_a_class4_section():
    sec = ec3.ProfilesSHS["SHS200x200x5"]
    ep = cl.effective_properties(sec, 355.0)
    assert int(ep.section_class) == 4
    assert ep.A_eff < ep.A_gross        # slender walls removed
    assert ep.W_eff_y < ep.W_el_y_gross
    # sanity: still most of the section is effective
    assert ep.A_eff / ep.A_gross > 0.7
    assert ep.W_eff_y / ep.W_el_y_gross > 0.7


def test_class4_chs_is_not_handled_by_effective_width():
    # A slender CHS classifies as Class 4 but is governed by shell buckling.
    slender = next(s for s in ec3.ProfilesCHS.values()
                   if cl.classify_section(s, 355.0).section_class
                   == SectionClass.CLASS_4)
    with pytest.raises(NotImplementedError):
        cl.effective_properties(slender, 355.0)


# ── outstand with a stress gradient (Table 5.2/2) ───────────────────────────

def test_outstand_gradient_reduces_to_uniform():
    # ψ = 1, α = 1, tip in compression → the uniform 9/10/14 limits.
    e = 1.0
    for ct in (9.0, 9.5, 13.0, 15.0):
        assert (cl.classify_outstand_part(ct, e)
                == cl.classify_outstand_part(ct, e, psi=1.0, alpha=1.0,
                                             tip_in_compression=True))


def test_k_sigma_outstand_two_arrangements():
    # tip in compression grows fast; tip in tension stays low (Table 4.2).
    assert cl.k_sigma_outstand(1.0, tip_in_compression=True) == pytest.approx(0.43)
    assert cl.k_sigma_outstand(0.0, tip_in_compression=True) == pytest.approx(1.70)
    assert cl.k_sigma_outstand(-1.0, tip_in_compression=True) == pytest.approx(23.8)
    assert cl.k_sigma_outstand(1.0, tip_in_compression=False) == pytest.approx(0.43)
    assert cl.k_sigma_outstand(0.0, tip_in_compression=False) == pytest.approx(0.57)
    assert cl.k_sigma_outstand(-1.0, tip_in_compression=False) == pytest.approx(0.85)


def test_outstand_gradient_is_more_lenient_than_uniform():
    # A moderately slender outstand that is Class 4 in uniform compression can
    # be a lower class once a favourable stress gradient (α < 1) is accounted.
    e = 1.0
    ct = 12.0
    uniform = cl.classify_outstand_part(ct, e)
    graded = cl.classify_outstand_part(ct, e, psi=-0.5, alpha=0.6,
                                       tip_in_compression=False)
    assert int(graded) <= int(uniform)


# ── minor-axis combined classification ──────────────────────────────────────

def test_flange_alpha_psi_minor_pure_bending():
    geo = cl._to_geometry(ec3.ProfilesI["IPE300"])
    a, psi, tip = cl.flange_alpha_psi_minor(geo, 235.0, 0.0, 30.0)
    assert tip is True                 # the free tip is the most compressed
    assert a == pytest.approx(1.0)     # whole compression half-flange in comp.
    assert 0.0 < psi < 1.0             # ψ = y_support / y_tip


def test_minor_axis_ipe_bending_is_class1():
    r = cl.classify_section(ec3.ProfilesI["IPE300"], 235.0,
                            n_ed=0.0, m_ed=30.0, axis="z")
    assert r.section_class == SectionClass.CLASS_1


def test_minor_axis_ipe_compression_web_governs():
    r = cl.classify_section(ec3.ProfilesI["IPE300"], 235.0,
                            n_ed=800.0, m_ed=0.0, axis="z")
    assert r.section_class == SectionClass.CLASS_2
    web = next(p for p in r.parts if p.name == "web")
    assert web.part_class == SectionClass.CLASS_2


def test_box_minor_equals_major_for_square_section():
    sec = ec3.ProfilesSHS["SHS200x200x5"]
    cy = cl.classify_section(sec, 355.0, n_ed=100.0, m_ed=0.0, axis="y")
    cz = cl.classify_section(sec, 355.0, n_ed=100.0, m_ed=0.0, axis="z")
    assert cy.section_class == cz.section_class


def test_rectangular_box_minor_axis_can_be_more_slender():
    # A tall RHS is stocky about the major axis but its long walls become
    # uniformly compressed (and thus more slender) about the minor axis.
    sec = ec3.ProfilesRHS["RHS200x100x5"]
    cy = cl.classify_section(sec, 355.0, n_ed=0.0, m_ed=50.0, axis="y")
    cz = cl.classify_section(sec, 355.0, n_ed=0.0, m_ed=50.0, axis="z")
    assert int(cz.section_class) >= int(cy.section_class)
