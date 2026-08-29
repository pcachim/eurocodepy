"""Tests for the composite EC2 §6.2 + §6.3 shear+torsion check
(``ec2.uls.shear_torsion``), added per dev/GRILLAGE_DESIGN.md (xdfem2d
repository) §3/§5.1 — moving the shear+torsion combination that used to live
only in xdfem2d's ``rc_design.py`` into eurocodepy, as a reusable, unit-
tested composite, mirroring ``ec5.uls.shear.check_shear_with_torsion``.

Run on Python >= 3.11 with eurocodepy importable.
"""
import math

import pytest

from eurocodepy.ec2.uls import (
    ShearTorsionInput,
    distribute_torsion_longitudinal,
    eurocode2_shear_torsion_check,
)
from eurocodepy.ec2.uls.shear_check import ShearInput, eurocode2_shear_check
from eurocodepy.ec2.uls.torsion import calc_torsion

FCK, FYK = 30.0, 500.0


def _rect_input(b=0.3, h=0.5, cover=0.045, as_long=8e-4):
    return ShearTorsionInput(b=b, h=h, cover=cover, fck=FCK, fyk=FYK,
                             as_long=as_long)


# ── same cot θ used for both verifications (dev/GRILLAGE_DESIGN.md §2.3) ──

def test_torsion_resistance_is_consistent_with_the_shared_cot_used():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=150.0, t_ed=40.0)

    # Recompute T_Rd,max directly with the SAME cot θ the result reports,
    # and confirm it's exactly what calc_torsion would give -- i.e. r.cot
    # really is the angle that produced r.trd_max, not just a copy of some
    # unrelated shear-side number.
    tors = calc_torsion(40.0, inp.b, inp.h, inp.fck, inp.gamma_c, inp.fyk,
                        inp.gamma_s, r.cot, cover=inp.cover,
                        alpha_cc=inp.alpha_cc)
    assert r.trd_max == pytest.approx(tors["TRd_max"])


def test_shear_cot_and_torsion_cot_never_diverge_by_construction():
    # Whatever cot the shear check's internal sweep lands on for a given
    # V_Ed, torsion is always computed with that SAME value -- there is no
    # code path where they could differ (unlike the pre-migration xdfem2d
    # bug this replaces).
    inp = _rect_input()
    shear_r = eurocode2_shear_check(
        ShearInput(b=inp.b, d=inp.h - inp.cover, fck=inp.fck, fyk=inp.fyk,
                  as_long=inp.as_long), v_ed=150.0)
    r = eurocode2_shear_torsion_check(inp, v_ed=150.0, t_ed=40.0)
    assert r.cot == shear_r.cot


def test_demonstrates_the_bug_this_migration_fixes_vs_an_arbitrary_cot():
    """dev/GRILLAGE_DESIGN.md §2.3/§7: xdfem2d's pre-migration code computed
    torsion with the user's ``elem.rc_cotg_theta`` directly, regardless of
    what ``eurocode2_shear_check`` picked internally for shear -- violating
    EC2 §6.3.2(3) whenever the two differ. This test shows the two really
    can differ (an "arbitrary" cot given straight to calc_torsion gives a
    different T_Rd,max than the shared-cot result from the composite
    function), confirming the fix is not cosmetic.
    """
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=150.0, t_ed=40.0)

    arbitrary_cot = 1.0 if r.cot != 1.0 else 2.5   # guaranteed to differ from r.cot
    old_style_tors = calc_torsion(40.0, inp.b, inp.h, inp.fck, inp.gamma_c,
                                  inp.fyk, inp.gamma_s, arbitrary_cot,
                                  cover=inp.cover, alpha_cc=inp.alpha_cc)
    assert old_style_tors["TRd_max"] != pytest.approx(r.trd_max)


# ── stirrup summation / interaction formula ──────────────────────────────

def test_asw_total_is_shear_plus_twice_torsion_stirrups():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=150.0, t_ed=40.0)
    assert r.asw_total_s == pytest.approx(r.asw_shear_s + 2.0 * r.asw_tor_s)


def test_interaction_is_the_exact_linear_eq_6_29_sum():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=150.0, t_ed=40.0)
    assert r.interaction == pytest.approx(r.t_ratio + r.v_ratio)


def test_low_forces_pass_with_no_crushing():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=20.0, t_ed=5.0)
    assert r.interaction < 1.0
    assert not r.crushing
    assert r.passed


def test_high_forces_trip_crushing_via_interaction():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=250.0, t_ed=200.0)
    assert r.interaction > 1.0
    assert r.crushing
    assert not r.passed


# ── longitudinal torsion steel distribution (§2.4 / Phase 3 groundwork) ──

def test_default_distribution_matches_the_old_50_50_top_bottom_split():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(inp, v_ed=20.0, t_ed=30.0)
    faces = r.asl_tor_by_face
    assert faces["side_left"] == 0.0
    assert faces["side_right"] == 0.0
    assert faces["top"] == pytest.approx(r.asl_tor_total / 2.0)
    assert faces["bottom"] == pytest.approx(r.asl_tor_total / 2.0)


def test_perimeter_mode_distributes_to_all_four_faces_and_sums_to_total():
    inp = _rect_input()
    r = eurocode2_shear_torsion_check(
        inp, v_ed=20.0, t_ed=30.0, distribution_mode="perimeter")
    faces = r.asl_tor_by_face
    assert faces["side_left"] > 0.0
    assert faces["side_right"] > 0.0
    assert sum(faces.values()) == pytest.approx(r.asl_tor_total)


def test_square_section_splits_evenly_across_all_four_faces_in_perimeter_mode():
    # b == h -> the wall centre-line is itself square (b_k == h_k), so a
    # perimeter-proportional split must be exactly 1/4 per face.
    square = ShearTorsionInput(b=0.4, h=0.4, cover=0.045, fck=FCK, fyk=FYK)
    faces = distribute_torsion_longitudinal(square.b, square.h, 0.0008,
                                            cover=square.cover, mode="perimeter")
    assert faces["top"] == pytest.approx(0.0002, rel=1e-9)
    assert faces["bottom"] == pytest.approx(0.0002, rel=1e-9)
    assert faces["side_left"] == pytest.approx(0.0002, rel=1e-9)
    assert faces["side_right"] == pytest.approx(0.0002, rel=1e-9)


def test_perimeter_mode_favours_the_longer_pair_of_faces():
    # A tall, narrow section (h >> b): the two b-faces (top/bottom) are each
    # SHORTER than each h-face (side_left/side_right), so each side face
    # should carry more steel than each top/bottom face.
    tall = ShearTorsionInput(b=0.25, h=0.6, cover=0.045, fck=FCK, fyk=FYK)
    faces = distribute_torsion_longitudinal(tall.b, tall.h, 0.001,
                                            cover=tall.cover, mode="perimeter")
    assert faces["side_left"] > faces["top"]
    assert faces["side_right"] > faces["bottom"]


def test_unknown_distribution_mode_raises():
    with pytest.raises(ValueError):
        distribute_torsion_longitudinal(0.3, 0.5, 0.0004, mode="nonsense")
