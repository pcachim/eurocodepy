"""EN 1995-1-1:2025 §8.3.3 / §8.3.4 -- tapered, curved and pitched cambered
beams (ec5.uls2025.special_beams). Expected values by hand from Eqs. 8.52-8.75
(checked against the text of the standard)."""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec5 import uls2025 as u25
from eurocodepy.ec5.materials import (LoadDuration, ServiceClass, TimberClass,
                                      TimberForcesType, TimberProduct)
from eurocodepy.ec5.uls import special_beams as sb04
from eurocodepy.ec5.uls2025 import special_beams as sb

A = math.radians(10.0)
T = math.tan(A)


def _gl():
    t = TimberClass("GL24h")
    t.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)
    return t


def test_k_tau_by_product():
    t = _gl()
    assert sb.k_tau(t) == (0.75, 1.5)
    t.timber_product = TimberProduct.LVL_C
    assert sb.k_tau(t) == (1.0, 1.0)


def test_k_m_alpha_equations_8_53_and_8_55():
    fm, fv, ft90, fc90 = 16.6, 2.2, 0.3, 2.5
    ten = 1 / math.sqrt(1 + (fm / (0.75 * fv) * T) ** 2 + (fm / ft90 * T * T) ** 2)
    com = 1 / math.sqrt(1 + (fm / (1.5 * fv) * T) ** 2 + (fm / fc90 * T * T) ** 2)
    assert sb.calc_k_m_alpha(A, fm, fv, ft90, fc90, True) == pytest.approx(ten)
    assert sb.calc_k_m_alpha(A, fm, fv, ft90, fc90, False) == pytest.approx(com)
    # cross-banded LVL: k_tau = 1.0 on both
    one = 1 / math.sqrt(1 + (fm / fv * T) ** 2 + (fm / ft90 * T * T) ** 2)
    assert sb.calc_k_m_alpha(A, fm, fv, ft90, fc90, True, 1.0, 1.0) == \
        pytest.approx(one)


def test_the_2025_k_m_alpha_equals_the_2004_one_for_glulam():
    # 0.75 / 1.5 are the 2004 constants: the two editions agree for GL
    t = _gl()
    a = sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t)
    b = sb04.check_tapered_edge(100.0, 0.14, 0.6, A, True, t)
    assert a.k_m_alpha == pytest.approx(b.k_m_alpha)


def test_tapered_edge_flags_alpha_over_15_degrees():
    t = _gl()
    assert sb.check_tapered_edge(100.0, 0.14, 0.6, math.radians(10), True,
                                 t).details["eq_8_57_valid"]
    assert not sb.check_tapered_edge(100.0, 0.14, 0.6, math.radians(20), True,
                                     t).details["eq_8_57_valid"]


def test_k_dis_and_k_vol_of_the_2025_edition():
    assert sb.K_DIS == {"double_tapered": 1.3, "curved": 1.15,
                        "pitched_cambered": 1.3}
    t = _gl()
    assert sb.calc_k_vol(0.9, t) == pytest.approx((0.6 / 0.9) ** 0.3)
    assert sb.calc_k_vol(0.3, t) > 1.0               # the formula, as written
    assert sb.calc_k_vol(0.9, TimberClass("C24")) == 1.0   # outside the clause
    t.timber_product = TimberProduct.LVL_C
    assert sb.calc_k_vol(0.9, t) == 1.0              # §8.3.4.1(10)


def test_k_v_for_glulam_and_solid():
    t = _gl()
    k_h = t.k_h(0.9, TimberForcesType.Shear)
    exp = min(k_h * 1.0 * 2.75 / t.fvk, 1.0)
    assert sb.calc_k_v(t, 0.9) == pytest.approx(exp)
    assert 0 < sb.calc_k_v(t, 0.9) <= 1.0


def test_apex_double_tapered_matches_hand_calculation():
    t = _gl()
    inp = sb.ApexInput(m_ap=300.0, v_ap=10.0, b=0.14, h_ap=0.9, alpha_ap=A,
                       kind="double_tapered", straightening=True)
    r = sb.check_apex_zone(inp, t)
    s0 = 6 * 300.0 / (0.14 * 0.9 ** 2) / 1e3
    assert r.k_dis == 1.3 and r.k_r == 1.0 and r.volume == 0.0
    assert r.sigma_m == pytest.approx((1 + 1.4 * T + 5.4 * T * T) * s0)
    assert r.sigma_t90 == pytest.approx(0.2 * T * s0)
    k_vol = (0.6 / 0.9) ** 0.3
    cap = 1.3 * k_vol * t.ft90d
    assert r.util_tension90 == pytest.approx(r.sigma_t90 / cap)
    tau = 1.5 * 10.0 / (0.14 * 0.9) / 1e3                 # no k_cr in 2025
    assert r.tau == pytest.approx(tau)
    k_v = sb.calc_k_v(t, 0.9)
    assert r.util_interaction == pytest.approx(tau / (k_v * t.fvd)
                                               + r.util_tension90)
    assert r.util == max(r.util_bending, r.util_tension90, r.util_interaction)


def test_curved_beam_uses_k_dis_1_15_and_k_r():
    t = _gl()
    r = sb.check_apex_zone(sb.ApexInput(
        m_ap=200.0, v_ap=0.0, b=0.14, h_ap=0.9, r_in=5.0, t_lam=33,
        kind="curved"), t)
    assert r.k_dis == 1.15 and r.k_r < 1.0
    assert r.radius == pytest.approx(5.45)


def test_volume_inputs_are_ignored():
    t = _gl()
    base = dict(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A, r_in=15.0,
                kind="curved")
    a = sb.check_apex_zone(sb.ApexInput(**base), t)
    b = sb.check_apex_zone(sb.ApexInput(zone_volume=3.0, beam_volume=1.0, **base), t)
    assert a.k_vol == b.k_vol and a.util == b.util


def test_reinforcement_is_recommended_not_required():
    t = _gl()
    base = dict(v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A, r_in=15.0)
    # pitched cambered: always when there is tension perpendicular (8.3.1(3))
    pc = sb.check_apex_zone(sb.ApexInput(m_ap=50.0, kind="pitched_cambered",
                                         **base), t)
    assert pc.details["reinforce_advised"] and "8.3.1(3)" in pc.details["reinforce_reason"]
    assert "recommended" in pc.details["reinforce_reason"]
    assert pc.util > 0                      # still verified without it
    # no tension perpendicular: nothing to reinforce
    none = sb.check_apex_zone(sb.ApexInput(m_ap=50.0, kind="pitched_cambered",
                                           straightening=False, **base), t)
    assert not none.details["reinforce_advised"]
    # curved / double tapered: only above 60 % of f_t,90,d
    low = sb.check_apex_zone(sb.ApexInput(m_ap=10.0, kind="curved", **base), t)
    high = sb.check_apex_zone(sb.ApexInput(m_ap=2000.0, kind="curved", **base), t)
    assert not low.details["reinforce_advised"]
    assert high.details["reinforce_advised"] and "8.3.1(4)" in high.details["reinforce_reason"]
    assert high.details["t90_over_f"] > 0.6


def test_scope_flag_for_solid_timber():
    r = sb.check_apex_zone(sb.ApexInput(m_ap=100.0, v_ap=0.0, b=0.14, h_ap=0.9,
                                        alpha_ap=A), TimberClass("C24"))
    assert r.details["in_scope"] is False


def test_trace_is_inert_and_cites_the_2025_clauses():
    t = _gl()
    inp = sb.ApexInput(m_ap=300.0, v_ap=10.0, b=0.14, h_ap=0.9, alpha_ap=A,
                       r_in=15.0, kind="pitched_cambered", straightening=True)
    rep = CalcReport()
    traced = sb.check_apex_zone(inp, t, trace=rep)
    assert traced == sb.check_apex_zone(inp, t)
    steps = {s["symbol"]: s for sec in rep.to_dict()["sections"]
             for s in sec["steps"]}
    assert steps["k_dis"]["clause"].endswith("Eq. 8.68")
    assert steps["k_vol"]["clause"].endswith("Eq. 8.69")
    assert "Eq. 8.70" in steps["τ_d/(k_v·f_v,d) + σ_t,90,d/(k_dis·k_vol·f_t,90,d)"]["clause"]
    assert steps["Reinforcement"]["value"] == "recommended (optional)"
    rep2 = CalcReport()
    sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t, trace=rep2)
    assert "§8.3.3" in rep2.to_dict()["sections"][0]["title"]


def test_namespace_exposes_the_2025_checks():
    assert u25.check_apex_zone is sb.check_apex_zone
    assert u25.check_tapered_edge is sb.check_tapered_edge
    assert u25.calc_k_vol is sb.calc_k_vol
    assert u25.calc_k_r is sb04.calc_k_r      # unchanged formula, shared
    assert u25.PlaneReinforcement is sb.PlaneReinforcement
    assert u25.check_plane_reinforcement is sb.check_plane_reinforcement
    assert u25.reinforcement_layout is sb.reinforcement_layout


def test_reinforced_apex_drops_the_unreinforced_tension_checks():
    t = _gl()
    base = dict(m_ap=300.0, v_ap=40.0, b=0.14, h_ap=0.9, alpha_ap=A,
                r_in=15.0, kind="pitched_cambered", straightening=True)
    plain = sb.check_apex_zone(sb.ApexInput(**base), t)
    rf = sb.check_apex_zone(sb.ApexInput(reinforced=True, **base), t)
    assert plain.util_tension90 > 0 and plain.util_interaction > 0
    assert rf.util_tension90 == 0.0 and rf.util_interaction == 0.0   # 8.67, 8.70
    assert rf.util_bending == plain.util_bending                      # 8.58 stays
    assert rf.util == rf.util_bending
    assert rf.sigma_t90 == plain.sigma_t90                            # 8.71 still
    assert rf.details["reinforced"] and not rf.details["reinforce_advised"]


def test_reinforcement_force_equation_8_76():
    t = _gl()
    inp = dict(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A, r_in=15.0,
               kind="curved", reinforced=True)
    r = sb.check_apex_zone(sb.ApexInput(**inp), t)
    assert r.details["F_t90_rf_per_m"] == pytest.approx(r.sigma_t90 * 0.14 * 1e3)
    assert r.details["F_t90_rf_Ed"] is None                  # no a1 given
    r = sb.check_apex_zone(sb.ApexInput(a1=0.4, **inp), t)
    assert r.details["F_t90_rf_Ed"] == pytest.approx(
        r.details["F_t90_rf_per_m"] * 0.4)


def test_no_tension_no_force_when_the_moment_does_not_straighten():
    r = sb.check_apex_zone(sb.ApexInput(
        m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A, r_in=15.0,
        kind="curved", reinforced=True, straightening=False), _gl())
    assert r.details["F_t90_rf_per_m"] == 0.0


def test_reinforced_trace_says_why_and_gives_the_force():
    rep = CalcReport()
    sb.check_apex_zone(sb.ApexInput(
        m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A, r_in=15.0,
        kind="curved", reinforced=True, a1=0.4), _gl(), trace=rep)
    steps = {s["symbol"]: s for sec in rep.to_dict()["sections"]
             for s in sec["steps"]}
    assert "8.3.4.2(1)" in steps["Reinforced"]["clause"]
    assert steps["F_t,90,rf,Ed"]["clause"].endswith("Eq. 8.76")
    assert "σ_t,90,d / (k_dis·k_vol·f_t,90,d)" not in steps      # not applied
    assert "Reinforcement" not in steps                          # already done


def test_2004_ignores_the_reinforced_field():
    t = _gl()
    a = sb04.check_apex_zone(sb04.ApexInput(
        m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A, r_in=15.0,
        kind="curved", reinforced=True), t)
    assert a.util_tension90 > 0


def test_reinforcement_layout_figure_8_11():
    # double tapered: zone h_ap long, elements at ±a1/2, ±3a1/2 ...
    lay = sb.reinforcement_layout("double_tapered", 0.9, 0.3)
    assert [round(x, 3) for x, _ in lay] == [-0.45, -0.15, 0.15, 0.45]
    assert [k for _, k in lay] == [0.67, 1.0, 1.0, 0.67]    # outer quarters
    # curved: k_ka = 1.0 everywhere, zone = the curved part
    cur = sb.reinforcement_layout("curved", 0.9, 0.3, zone_length=2.0)
    assert len(cur) == 6 and all(k == 1.0 for _, k in cur)
    pc = sb.reinforcement_layout("pitched_cambered", 0.9, 0.5, zone_length=2.0)
    assert {k for _, k in pc} == {1.0, 0.67}
    assert sb.reinforcement_layout("curved", 0.9, 0.3) == []   # no zone length
    assert sb.reinforcement_layout("double_tapered", 0.9, 0.0) == []


def test_dowel_spacing_limits_8_3_4_2_4():
    assert sb.check_dowel_spacing(0.30, 0.9)[0]
    ok, msg = sb.check_dowel_spacing(0.20, 0.9)
    assert not ok and "250" in msg
    ok, msg = sb.check_dowel_spacing(0.70, 0.9)
    assert not ok and "0.75" in msg


def _plane(**kw):
    d = dict(b_r=0.06, t_r=0.012, f_td=200.0, f_b2d=0.4, l_r_l=0.45)
    d.update(kw)
    return sb.PlaneReinforcement(**d)


def test_plane_reinforcement_resistance_equations_8_49_8_50():
    r = sb.check_plane_reinforcement(5.0, _plane())
    assert r.F_bond == pytest.approx(0.4e3 * 0.45 * 0.06)       # 10.8 kN
    assert r.F_tensile == pytest.approx(200e3 * 0.06 * 0.012)   # 144 kN
    assert r.F_rd == pytest.approx(10.8) and r.governing == "bond"
    assert r.util == pytest.approx(5.0 / 10.8)
    # l_r = min(l_r,l ; l_r,u)
    r2 = sb.check_plane_reinforcement(5.0, _plane(l_r_u=0.30))
    assert r2.l_r == 0.30 and r2.F_rd == pytest.approx(0.4e3 * 0.30 * 0.06)
    # n_r multiplies; a thin weak reinforcement is governed by its tension
    r3 = sb.check_plane_reinforcement(5.0, _plane(n_r=2, f_td=5.0, f_b2d=5.0))
    assert r3.governing == "tensile"
    assert r3.F_rd == pytest.approx(2 * 5e3 * 0.06 * 0.012)
    # effective width enters the bond only
    r4 = sb.check_plane_reinforcement(5.0, _plane(b_r_ef=0.03))
    assert r4.F_bond == pytest.approx(0.4e3 * 0.45 * 0.03)
    assert r4.F_tensile == r.F_tensile


def test_apex_with_plane_reinforcement_verifies_each_element():
    t = _gl()
    inp = sb.ApexInput(m_ap=300.0, v_ap=40.0, b=0.14, h_ap=0.9, alpha_ap=A,
                       kind="double_tapered", reinforced=True, a1=0.3,
                       reinforcement=_plane())
    r = sb.check_apex_zone(inp, t)
    rf = r.details["reinforcement"]
    assert len(rf["elements"]) == 4
    f_c = r.sigma_t90 * 0.14 * 1e3 * 0.3                         # k_ka = 1
    worst = rf["worst"]
    assert worst[1] == 1.0 and worst[2] == pytest.approx(f_c)
    assert rf["util"] == pytest.approx(f_c / 10.8)
    outer = [e for e in rf["elements"] if e[1] == 0.67][0]
    assert outer[2] == pytest.approx(0.67 * f_c)                 # less loaded
    assert r.util_tension90 == 0.0 and r.util_interaction == 0.0  # 8.67, 8.70


def test_no_verification_without_data_or_spacing():
    t = _gl()
    base = dict(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A,
                kind="double_tapered", reinforced=True)
    assert sb.check_apex_zone(sb.ApexInput(a1=0.3, **base), t) \
        .details["reinforcement"] is None
    assert sb.check_apex_zone(sb.ApexInput(reinforcement=_plane(), **base), t) \
        .details["reinforcement"] is None


def test_reinforcement_trace_has_the_resistance_steps():
    rep = CalcReport()
    sb.check_apex_zone(sb.ApexInput(
        m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A,
        kind="double_tapered", reinforced=True, a1=0.3,
        reinforcement=_plane()), _gl(), trace=rep)
    steps = {s["symbol"]: s for sec in rep.to_dict()["sections"]
             for s in sec["steps"]}
    assert steps["F_t,90,rf,Rd"]["clause"].endswith("Eq. 8.49")
    assert steps["F_t,90,rf,Ed / F_t,90,rf,Rd"]["clause"].endswith("Eq. 8.48")
    assert steps["l_r"]["clause"].endswith("Eq. 8.50")
    rep2 = CalcReport()
    sb.check_apex_zone(sb.ApexInput(
        m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A,
        kind="double_tapered", reinforced=True, a1=0.3), _gl(), trace=rep2)
    s2 = {s["symbol"]: s for sec in rep2.to_dict()["sections"]
          for s in sec["steps"]}
    assert s2["F_t,90,rf,Rd"]["value"] == "not verified"


def test_defaults_come_from_the_database_tables_4_4():
    cs = sb.connection_safety()
    assert (cs["gamma_R_dowel_type"], cs["gamma_M2_steel_tension_fracture"],
            cs["gamma_M_bond_line"]) == (1.30, 1.25, 1.30)
    t = TimberClass("GL24h", edition="2025")
    t.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)
    assert sb.bond_design_strength(t, ServiceClass.SC1,
                                   LoadDuration.MediumDuration) == pytest.approx(
        t.kmod * 0.75 / 1.30)


def test_dowel_partial_factors_default_to_1_30_and_1_25():
    t = TimberClass("GL24h", edition="2025")
    d = dict(d=8.0, f_uk=920.0, d1=5.0)
    SVC, LD = ServiceClass.SC1, LoadDuration.MediumDuration
    dflt = sb.check_dowel_reinforcement(10.0, sb.DowelReinforcement(**d), t,
                                        0.9, 33.0, SVC, LD)
    expl = sb.check_dowel_reinforcement(
        10.0, sb.DowelReinforcement(gamma_r=1.30, gamma_m2=1.25, **d), t, 0.9,
        33.0, SVC, LD)
    assert dflt.F_rd == expl.F_rd and dflt.util == expl.util
    other = sb.check_dowel_reinforcement(
        10.0, sb.DowelReinforcement(gamma_r=1.5, gamma_m2=1.5, **d), t, 0.9,
        33.0, SVC, LD)
    assert other.F_rd < dflt.F_rd


def test_plane_reinforcement_defaults_resolve_in_the_apex_check():
    t = TimberClass("GL24h", edition="2025")
    SVC, LD = ServiceClass.SC1, LoadDuration.MediumDuration
    base = dict(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A,
                kind="double_tapered", reinforced=True, a1=0.3)
    rf = sb.PlaneReinforcement(b_r=0.06, t_r=0.012, f_td=200.0)   # f_b2d, l_r_l unset
    r = sb.check_apex_zone(sb.ApexInput(reinforcement=rf, **base), t, SVC, LD)
    worst = r.details["reinforcement"]["worst"][3]
    t.design_values(SVC, LD)
    f_b2d = t.kmod * 0.75 / 1.30
    assert worst.l_r == pytest.approx(0.45)                       # h_ap/2
    assert worst.F_bond == pytest.approx(f_b2d * 1e3 * 0.45 * 0.06)
    # explicit values are used as given
    r2 = sb.check_apex_zone(sb.ApexInput(
        reinforcement=sb.PlaneReinforcement(b_r=0.06, t_r=0.012, f_td=200.0,
                                            f_b2d=0.4, l_r_l=0.3), **base),
        t, SVC, LD)
    assert r2.details["reinforcement"]["worst"][3].F_bond == pytest.approx(
        0.4e3 * 0.3 * 0.06)


def test_unresolved_plane_reinforcement_is_refused_by_the_bare_check():
    with pytest.raises(ValueError, match="f_b2d"):
        sb.check_plane_reinforcement(5.0, sb.PlaneReinforcement(
            b_r=0.06, t_r=0.012, f_td=200.0))
