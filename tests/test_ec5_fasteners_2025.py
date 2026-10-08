"""EN 1995-1-1:2025 §11.2.2 axial resistance of screws and rods
(ec5.uls2025.fasteners) and its use as dowel-type reinforcement of apex zones
(§8.3.2(8)). Expected values by hand from Table 11.2 and Eqs. 11.1-11.4."""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec5 import uls2025 as u
from eurocodepy.ec5.materials import (LoadDuration, ServiceClass, TimberClass,
                                      TimberType)
from eurocodepy.ec5.uls2025 import fasteners as fx
from eurocodepy.ec5.uls2025 import special_beams as sb

SVC, LD = ServiceClass.SC1, LoadDuration.MediumDuration


def test_factors_of_table_11_2_B1():
    assert fx.calc_k_w(90) == 1.0 and fx.calc_k_w(30) == 1.0
    assert fx.calc_k_w(15) == pytest.approx(0.3 + 0.7 * 15 / 30)
    assert fx.calc_k_w(0) == pytest.approx(0.3)
    assert fx.calc_k_mat(None) == 1.0
    assert fx.calc_k_mat(12.6, parallel_laminated=False) == 1.0
    assert fx.calc_k_mat(3.0) == pytest.approx(1 + math.log(3.0) / 12)
    assert fx.calc_k_mat(12.6) == 1.15                    # capped
    assert fx.calc_k_mat(0.4) == 1.0                      # at least one lamination
    assert (fx.calc_k_rho(3), fx.calc_k_rho(5), fx.calc_k_rho(6),
            fx.calc_k_rho(90), fx.calc_k_rho(45, softwood=False)) == \
        (0.7, 0.7, 1.1, 1.1, 1.6)


def test_withdrawal_strength_equation_4():
    f = fx.withdrawal_strength_screw(8.0, 385.0, eps=90.0, n_p=3.0)
    exp = 8.2 * 1.0 * (1 + math.log(3) / 12) * 8.0 ** -0.33 * (385 / 350) ** 1.1
    assert f == pytest.approx(exp)
    f15 = fx.withdrawal_strength_screw(8.0, 385.0, eps=15.0, n_p=3.0)
    assert f15 == pytest.approx(8.2 * 0.65 * (1 + math.log(3) / 12)
                                * 8.0 ** -0.33 * (385 / 350) ** 1.1)


def test_forces_equations_11_3_and_11_4():
    assert fx.withdrawal_resistance(8.0, 400.0, 5.0) == pytest.approx(
        math.pi * 8 * 400 * 5.0 / 1e3)
    assert fx.steel_tensile_resistance(19.635, 920.0) == pytest.approx(
        0.9 * 19.635 * 920 / 1e3)


def test_axial_tensile_resistance_equation_11_1_takes_the_minimum():
    f, mode = fx.axial_tensile_resistance(50.0, 16.0, 0.8, 1.25, 1.25)
    assert f == pytest.approx(16.0 / 1.25) and mode == "steel"
    f, mode = fx.axial_tensile_resistance(10.0, 16.0, 0.8, 1.25, 1.25)
    assert f == pytest.approx(0.8 / 1.25 * 10.0) and mode == "withdrawal"


def test_validity_limits_of_table_11_2():
    assert fx.screw_validity(8.0, 5.0, 400.0, 385.0) == []
    msgs = fx.screw_validity(30.0, 5.0, 100.0, 750.0)
    assert len(msgs) == 4
    assert any("d1/d" in m for m in msgs) and any("5d" in m for m in msgs)


def _gl():
    return TimberClass("GL24h")


def _screw(**kw):
    d = dict(d=8.0, f_uk=920.0, gamma_r=1.25, gamma_m2=1.25, d1=5.0)
    d.update(kw)
    return sb.DowelReinforcement(**d)


def test_dowel_reinforcement_resistance_by_hand():
    t = _gl()
    r = sb.check_dowel_reinforcement(10.0, _screw(), t, 0.9, 33.0, SVC, LD)
    l_r = 0.9 / 2 - 0.033                                  # default l_r
    assert r.l_r == pytest.approx(l_r)
    n_p = l_r * 1e3 / 33.0
    f_wk = fx.withdrawal_strength_screw(8.0, t.rhok, 90.0, n_p)
    F_wk = math.pi * 8.0 * l_r * 1e3 * f_wk / 1e3
    F_tk = 0.9 * math.pi * 5.0 ** 2 / 4 * 920.0 / 1e3
    t.design_values(SVC, LD)
    exp = min(t.kmod / 1.25 * F_wk, F_tk / 1.25)
    assert r.F_rd == pytest.approx(exp)
    assert r.governing == "steel"                         # Ø8 in 417 mm: steel
    assert r.util == pytest.approx(10.0 / exp)
    assert r.F_bond == pytest.approx(t.kmod / 1.25 * F_wk)
    assert r.F_tensile == pytest.approx(F_tk / 1.25)


def test_n_r_and_l_r_override():
    t = _gl()
    one = sb.check_dowel_reinforcement(10.0, _screw(), t, 0.9, 33.0, SVC, LD)
    two = sb.check_dowel_reinforcement(10.0, _screw(n_r=2), t, 0.9, 33.0, SVC, LD)
    assert two.F_rd == pytest.approx(2 * one.F_rd)
    short = sb.check_dowel_reinforcement(
        10.0, _screw(l_r_l=0.05, l_r_u=0.20), t, 0.9, 33.0, SVC, LD)
    assert short.l_r == 0.05 and short.governing == "withdrawal"
    assert not short.details["warnings"]                  # 50 mm ≥ 5d = 40 mm
    tiny = sb.check_dowel_reinforcement(
        10.0, _screw(l_r_l=0.03), t, 0.9, 33.0, SVC, LD)
    assert any("5d" in w for w in tiny.details["warnings"])


def test_bonded_in_rods_use_f_wk_4_and_the_right_steel_area():
    t = _gl()
    rib = sb.check_dowel_reinforcement(
        10.0, sb.DowelReinforcement(d=16.0, f_uk=540.0, gamma_r=1.25,
                                    gamma_m2=1.25, kind="bonded_rod"),
        t, 0.9, 33.0, SVC, LD)
    assert rib.details["f_wk"] == 4.0
    assert rib.details["F_tk"] == pytest.approx(
        0.9 * math.pi * 16 ** 2 / 4 * 540 / 1e3)
    met = sb.check_dowel_reinforcement(
        10.0, sb.DowelReinforcement(d=16.0, f_uk=540.0, gamma_r=1.25,
                                    gamma_m2=1.25, kind="bonded_rod",
                                    thread="metric"),
        t, 0.9, 33.0, SVC, LD)
    assert met.details["F_tk"] == pytest.approx(
        0.9 * math.pi * (0.86 * 16) ** 2 / 4 * 540 / 1e3)
    bad = sb.check_dowel_reinforcement(
        10.0, sb.DowelReinforcement(d=16.0, f_uk=540.0, gamma_r=1.25,
                                    gamma_m2=1.25, kind="bonded_rod", eps=10.0),
        t, 0.9, 33.0, SVC, LD)
    assert any("30°-90°" in w for w in bad.details["warnings"])


def test_missing_inner_diameter_is_flagged():
    r = sb.check_dowel_reinforcement(10.0, _screw(d1=None), _gl(), 0.9, 33.0,
                                     SVC, LD)
    assert any("d1" in w for w in r.details["warnings"])


def test_apex_with_dowel_reinforcement_verifies_the_elements():
    t = _gl()
    a = math.radians(10)
    inp = sb.ApexInput(m_ap=300.0, v_ap=40.0, b=0.14, h_ap=0.9, alpha_ap=a,
                       kind="double_tapered", reinforced=True, a1=0.3,
                       reinforcement=_screw())
    r = sb.check_apex_zone(inp, t, SVC, LD)
    rf = r.details["reinforcement"]
    assert len(rf["elements"]) == 4 and rf["spacing"][0]
    f_c = r.sigma_t90 * 0.14 * 1e3 * 0.3
    assert rf["worst"][2] == pytest.approx(f_c)
    f_rd = rf["worst"][3].F_rd
    assert rf["util"] == pytest.approx(f_c / f_rd)
    assert r.util_tension90 == 0.0 and r.util_interaction == 0.0
    rep = CalcReport()
    sb.check_apex_zone(inp, t, SVC, LD, trace=rep)
    steps = {s["symbol"]: s for sec in rep.to_dict()["sections"]
             for s in sec["steps"]}
    assert steps["f_w,k"]["clause"].endswith("Table 11.2 B.1 (4)")
    assert steps["F_ax,t,d"]["clause"].endswith("Eq. 11.1")
    assert steps["F_t,90,rf,Rd"]["clause"].endswith("§8.3.2(8)")
    assert steps["F_t,90,rf,Ed / F_t,90,rf,Rd"]["clause"].endswith("Eq. 8.48")


def test_namespace_exports():
    assert u.DowelReinforcement is sb.DowelReinforcement
    assert u.check_dowel_reinforcement is sb.check_dowel_reinforcement
    assert u.fasteners is fx
