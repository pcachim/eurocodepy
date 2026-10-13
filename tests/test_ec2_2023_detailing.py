"""EN 1992-1-1:2023 Clause 12 (detailing): ec2.uls2023.detailing."""
import math

import pytest

from eurocodepy.ec2 import uls2023
from eurocodepy.ec2.uls2023 import detailing as dt


def test_minimum_shear_reinforcement_eq_12_4():
    base = 0.08 * math.sqrt(30.0) / 500.0
    assert dt.calc_rho_w_min(30.0, 500.0, "A") == pytest.approx(base)
    assert dt.calc_rho_w_min(30.0, 500.0, "B") == pytest.approx(0.9 * base)
    assert dt.calc_rho_w_min(30.0, 500.0, "C") == pytest.approx(0.8 * base)
    assert dt.calc_asw_min_s(30.0, 500.0, 0.3, 90.0, "B") == pytest.approx(0.9 * base * 0.3)
    assert dt.calc_asw_min_s(30.0, 500.0, 0.3, 45.0, "A") == pytest.approx(
        base * 0.3 * math.sin(math.radians(45.0)))
    with pytest.raises(ValueError, match="ductility"):
        dt.calc_rho_w_min(30.0, 500.0, "D")


def test_shear_check_uses_12_4_by_default():
    inp = uls2023.ShearInput(b=0.3, d=0.5, fck=30.0, fyk=500.0, as_long=0.0015)
    low = uls2023.eurocode2_shear_check(inp, 30.0)
    assert low.mode == "no_verification"
    assert low.asw_s == pytest.approx(dt.calc_asw_min_s(30.0, 500.0, 0.3))
    assert low.details["asw_min"] == low.asw_s
    off = uls2023.eurocode2_shear_check(
        uls2023.ShearInput(b=0.3, d=0.5, fck=30.0, fyk=500.0, as_long=0.0015,
                           asw_min_s=0.0), 30.0)
    assert off.asw_s == 0.0
    # the designed stirrups are never below the minimum
    hi = uls2023.eurocode2_shear_check(
        uls2023.ShearInput(b=0.3, d=0.5, fck=30.0, fyk=500.0, as_long=0.0015,
                           asw_min_s=1.0e-3), 150.0)
    assert hi.asw_s == 1.0e-3


def test_min_flexural_reinforcement_eqs_12_1_to_12_3():
    assert dt.cracking_check_needed(-100.0, 0.15, 20.0)           # < 0,5·Ac·fcd = 1500 kN
    assert not dt.cracking_check_needed(-2000.0, 0.15, 20.0)
    assert dt.cracking_check_needed(50.0, 0.15, 20.0)             # tension
    assert dt.calc_m_cr_rect(0.3, 0.5, 2.9) == pytest.approx(2.9 * 0.3 * 0.25 / 6 * 1000.0)
    # compression raises Mcr, tension lowers it
    assert dt.calc_m_cr_rect(0.3, 0.5, 2.9, -300.0) > dt.calc_m_cr_rect(0.3, 0.5, 2.9)
    assert dt.calc_m_cr_rect(0.3, 0.5, 2.9, 300.0) < dt.calc_m_cr_rect(0.3, 0.5, 2.9)
    assert dt.calc_as_min_tension(0.15, 2.9, 500.0) == pytest.approx(0.15 * 2.9 / 500.0)
    assert [dt.calc_k_dc(c) for c in "ABC"] == [1.3, 1.1, 1.0]
    assert dt.calc_m_rd_min(-100.0, "A") == pytest.approx(130.0)
    assert dt.calc_sigma_sd_min(434.8, 5e-4, 1e-3) == pytest.approx(217.4)


def test_beams_table_12_1_and_12_3_2():
    sp = dt.beam_max_spacings(0.5)
    assert sp["s_l_max"] == pytest.approx(0.375)
    assert sp["s_bu_max"] == pytest.approx(0.3)
    assert sp["s_tr_max"] == pytest.approx(0.375)
    assert dt.beam_max_spacings(1.2)["s_tr_max"] == 0.6                      # <= 600 mm
    assert dt.beam_max_spacings(0.5, 45.0)["s_l_max"] == pytest.approx(0.75)
    assert dt.beam_min_stirrups(2.0e-3) == pytest.approx(1.0e-3)
    assert dt.beam_min_stirrups(2.0e-3, torsion=True) == pytest.approx(4.0e-4)
    assert dt.torsion_stirrup_max_spacing(1.6, 0.3, 0.5) == pytest.approx(0.2)
    assert dt.torsion_stirrup_max_spacing(4.0, 0.3, 0.5) == pytest.approx(0.3)
    assert dt.beam_min_support_reinforcement(8e-4) == pytest.approx(2e-4)
    assert dt.calc_shift_length(0.45, 2.0) == pytest.approx(0.45)            # Eq. (12.5)
    assert dt.calc_shift_length(0.45, 2.0, 45.0) == pytest.approx(0.45 * (2 - 1) / 2)
    assert dt.calc_shift_length(0.45, 2.0, shear_reinforcement=False, d=0.5) == 0.5
    with pytest.raises(ValueError, match="d is needed"):
        dt.calc_shift_length(0.45, 2.0, shear_reinforcement=False)
    assert dt.calc_bent_up_anchorage(0.5, tension_zone=True) == pytest.approx(0.65)
    assert dt.calc_bent_up_anchorage(0.5, tension_zone=False) == pytest.approx(0.35)


def test_slabs_table_12_2_and_12_4_2():
    sp = dt.slab_max_spacings(0.2, 0.17)
    assert sp["s_slab_max"] == pytest.approx(0.4)                            # min(0,6; 0,4)
    assert dt.slab_max_spacings(0.1, 0.08)["s_slab_max"] == pytest.approx(0.3)
    assert sp["s_l_max"] == pytest.approx(0.75 * 0.17)
    assert sp["s_bu_max"] == 0.17
    assert sp["s_tr_max"] == pytest.approx(1.5 * 0.17)
    m = dt.slab_min_reinforcement(1e-3)
    assert m["secondary"] == pytest.approx(2e-4)
    assert m["inner_support"] == pytest.approx(2.5e-4)
    assert dt.slab_edge_reinforcement_length(0.2, 0.7) == 0.7
    assert dt.slab_edge_reinforcement_length(0.4, 0.5) == 0.8
    assert dt.slab_min_depth_for_shear_reinforcement() == 0.2
    assert dt.slab_min_depth_for_shear_reinforcement(bent_up=True) == 0.16
    assert dt.slab_shear_reinforcement_only_bent_up_ok(0.08 * 20.0, 20.0)
    assert not dt.slab_shear_reinforcement_only_bent_up_ok(0.09 * 20.0, 20.0)
    assert dt.slab_shear_reinforcement_only_bent_up_ok(0.16 * 20.0, 20.0, 45.0)
    assert dt.slab_shear_reinforcement_only_bent_up_ok(0.12 * 20.0, 20.0, 67.5)   # interpolated


def test_punching_reinforcement_12_5_1():
    assert dt.calc_phi_w_max(200.0, "closed") == pytest.approx(11.0)
    assert dt.calc_phi_w_max(450.0, "single_leg") == pytest.approx(10.0 * math.sqrt(2.25))
    assert dt.calc_phi_w_max(200.0, "bent_up") == 16.0
    with pytest.raises(ValueError, match="kind"):
        dt.calc_phi_w_max(200.0, "x")
    flat = dt.punching_reinforcement_spacing(0.2)
    assert flat["tangential_max"] == pytest.approx(0.3)
    assert flat["tangential_first_perimeter_max"] == pytest.approx(0.15)
    base = dt.punching_reinforcement_spacing(0.2, column_base=True)
    assert base["tangential_first_perimeter_max"] == pytest.approx(0.1)


def test_integrity_reinforcement_eqs_12_10_to_12_12():
    assert dt.calc_vrd_int(1e-3, 434.8, "B") == pytest.approx(1e-3 * 434.8 * 0.37 * 1000.0)
    assert dt.calc_vrd_int(1e-3, 434.8, "C") == pytest.approx(1e-3 * 434.8 * 0.49 * 1000.0)
    with pytest.raises(ValueError, match="class B or C"):
        dt.calc_vrd_int(1e-3, 434.8, "A")
    assert dt.calc_vrd_w_int(0.002, 434.8, 2.5, 0.2) == pytest.approx(0.002 * 434.8 * 2.5 * 0.2 * 1000.0)
    v = dt.calc_vrd_hog(4, 30.0, 1.15, 0.016, 0.15, 0.03)
    b_ef = min(0.15 - 0.016, 6 * 0.016, 4 * 0.03)
    assert v == pytest.approx(4 * math.sqrt(30.0) / 1.15 * 0.016 * b_ef * 1000.0)


def test_columns_table_12_3():
    assert dt.column_min_longitudinal(500.0, 434.8, 0.09) == pytest.approx(0.002 * 0.09)
    assert dt.column_min_longitudinal(4000.0, 434.8, 0.09) == pytest.approx(0.1 * 4000 / 434.8 / 1000)
    assert dt.column_min_longitudinal(4000.0, 434.8, 0.09, all_prestressed=True) == pytest.approx(0.00018)
    assert dt.column_min_bars("circular")["min_bars"] == 6
    assert dt.column_min_bars()["one_per_corner"]
    with pytest.raises(ValueError, match="shape"):
        dt.column_min_bars("oval")
    s = dt.column_max_stirrup_spacing(20.0, 0.4, 0.3)
    assert s["intermediate"] == pytest.approx(0.3)                           # min(0,4; 0,4; 0,3; 0,3)
    assert s["end_regions"] == pytest.approx(0.18)
    assert s["end_region_length"] == 0.4
    assert dt.column_max_stirrup_spacing(12.0, 0.4, 0.3)["intermediate"] == pytest.approx(0.24)
    assert dt.column_max_stirrup_spacing(20.0, 0.5, 0.45, bars_in_resistance=False)["intermediate"] == 0.4
    assert dt.column_min_stirrup_diameter(25.0) == pytest.approx(6.25)
    assert dt.column_min_confinement_stress(30.0) == pytest.approx(0.6)
    assert dt.column_restraint_distance_ok(0.2, 1.5)
    assert not dt.column_restraint_distance_ok(0.2, 2.5)
    assert dt.column_restraint_distance_ok(0.1, 2.5)


def test_walls_table_12_4():
    assert dt.wall_min_vertical(0.2, 2.9, 500.0) == pytest.approx(0.25 * 0.2 * 2.9 / 500.0)
    assert dt.wall_min_vertical(0.2, 2.9, 500.0, in_plane_loaded=False) == pytest.approx(2e-4)
    assert dt.wall_min_horizontal(0.2, 2.9, 500.0, 4e-4) == pytest.approx(0.25 * 0.2 * 2.9 / 500.0)
    assert dt.wall_min_horizontal(0.2, 2.9, 500.0, 4e-4, in_plane_loaded=False) == pytest.approx(1e-4)
    assert dt.wall_max_spacings(0.2) == {"vertical": pytest.approx(0.4), "horizontal": 0.4}
    assert dt.wall_max_spacings(0.1)["vertical"] == pytest.approx(0.3)
    assert dt.wall_orthogonal_links_required(0.005, 0.2)
    assert not dt.wall_orthogonal_links_required(0.003, 0.2)
