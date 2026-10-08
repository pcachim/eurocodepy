"""EN 1995-1-1:2004 §6.4 -- tapered, curved and pitched cambered beams
(ec5.uls.special_beams).

The expected values are computed by hand from Eqs. 6.37-6.59 of the standard
(the coefficients were checked against its text). The apex-zone volume depends
on Figure 6.9, which is not in the text.
"""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec5.materials import (LoadDuration, ServiceClass, TimberClass,
                                      TimberForcesType)
from eurocodepy.ec5.uls import special_beams as sb

A = math.radians(10.0)
T = math.tan(A)


def _gl():
    t = TimberClass("GL24h")
    t.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)
    return t


def test_k_m_alpha_vanishes_to_one_without_taper():
    assert sb.calc_k_m_alpha(0.0, 16.0, 2.0, 0.3, 2.0, True) == 1.0
    assert sb.calc_k_m_alpha(0.0, 16.0, 2.0, 0.3, 2.0, False) == 1.0


def test_k_m_alpha_tension_equation_6_38():
    fm, fv, ft90 = 16.6, 2.2, 0.3
    exp = 1 / math.sqrt(1 + (fm / (0.75 * fv) * T) ** 2 + (fm / ft90 * T * T) ** 2)
    assert sb.calc_k_m_alpha(A, fm, fv, ft90, 2.5, True) == pytest.approx(exp)


def test_k_m_alpha_compression_equation_6_39():
    fm, fv, fc90 = 16.6, 2.2, 2.5
    exp = 1 / math.sqrt(1 + (fm / (1.5 * fv) * T) ** 2 + (fm / fc90 * T * T) ** 2)
    assert sb.calc_k_m_alpha(A, fm, fv, 0.3, fc90, False) == pytest.approx(exp)


def test_tension_edge_is_more_severe_than_compression_edge():
    t = _gl()
    ten = sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t)
    com = sb.check_tapered_edge(100.0, 0.14, 0.6, A, False, t)
    assert ten.k_m_alpha < com.k_m_alpha < 1.0
    assert ten.util_cut > com.util_cut


def test_tapered_edge_stress_and_utilisation():
    t = _gl()
    r = sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t)
    sigma = 6 * 100.0 / (0.14 * 0.6 ** 2) / 1e3          # MPa
    assert r.sigma_m == pytest.approx(sigma)
    f_md = t.fmd * t.k_h(0.6, TimberForcesType.Bending)
    assert r.f_md == pytest.approx(f_md)
    assert r.util_grain == pytest.approx(sigma / f_md)
    assert r.util_cut == pytest.approx(sigma / (r.k_m_alpha * f_md))
    assert r.util == max(r.util_cut, r.util_grain)


def test_depth_enters_squared():
    t = _gl()
    a = sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t).sigma_m
    b = sb.check_tapered_edge(100.0, 0.14, 0.3, A, True, t).sigma_m
    assert b == pytest.approx(4 * a)


def test_k_r():
    assert sb.calc_k_r(None, 33) == 1.0
    assert sb.calc_k_r(240 * 0.033, 33) == pytest.approx(1.0)
    assert sb.calc_k_r(5.0, 33) == pytest.approx(0.76 + 0.001 * 5000 / 33)


def test_k_l_k_p_straight_reduce_to_k1_k5():
    assert sb.calc_k_l(1.0, None, A) == pytest.approx(1 + 1.4 * T + 5.4 * T * T)
    assert sb.calc_k_p(1.0, None, A) == pytest.approx(0.2 * T)
    assert sb.calc_k_l(1.0, None, 0.0) == 1.0
    assert sb.calc_k_p(1.0, None, 0.0) == 0.0


def test_k_l_k_p_with_radius():
    h, r = 1.0, 20.0
    x = h / r
    k_l = (1 + 1.4 * T + 5.4 * T * T) + (0.35 - 8 * T) * x \
        + (0.6 + 8.3 * T - 7.8 * T * T) * x * x + 6 * T * T * x ** 3
    k_p = 0.2 * T + (0.25 - 1.5 * T + 2.6 * T * T) * x \
        + (2.1 * T - 4 * T * T) * x * x
    assert sb.calc_k_l(h, r, A) == pytest.approx(k_l)
    assert sb.calc_k_p(h, r, A) == pytest.approx(k_p)


def test_volume_and_k_vol():
    v = sb.apex_volume(0.14, 1.0, A)
    assert v == pytest.approx(0.14 * (1 - 0.25 * T))
    assert sb.apex_volume(0.14, 1.0, A, beam_volume=0.1) == pytest.approx(0.2 / 3)
    t = _gl()
    assert sb.calc_k_vol(v, t) == pytest.approx((0.01 / v) ** 0.2)
    assert sb.calc_k_vol(v, TimberClass("C24")) == 1.0


def test_apex_double_tapered_matches_hand_calculation():
    t = _gl()
    inp = sb.ApexInput(m_ap=300.0, v_ap=10.0, b=0.14, h_ap=0.9, alpha_ap=A,
                       kind="double_tapered", straightening=True)
    r = sb.check_apex_zone(inp, t)
    s0 = 6 * 300.0 / (0.14 * 0.9 ** 2) / 1e3
    assert r.k_dis == 1.4 and r.k_r == 1.0 and r.radius is None
    assert r.sigma_m == pytest.approx((1 + 1.4 * T + 5.4 * T * T) * s0)
    f_md = t.fmd * t.k_h(0.9, TimberForcesType.Bending)
    assert r.util_bending == pytest.approx(r.sigma_m / f_md)
    assert r.sigma_t90 == pytest.approx(0.2 * T * s0)
    vol = 0.14 * 0.81 * (1 - 0.25 * T)
    cap = 1.4 * (0.01 / vol) ** 0.2 * t.ft90d
    assert r.util_tension90 == pytest.approx(r.sigma_t90 / cap)
    tau = 1.5 * 10.0 / (t.kcr * 0.14 * 0.9) / 1e3
    assert r.tau == pytest.approx(tau)
    assert r.util_interaction == pytest.approx(tau / t.fvd + r.util_tension90)
    assert r.util == max(r.util_bending, r.util_tension90, r.util_interaction)


def test_no_tension_perpendicular_when_moment_increases_curvature():
    t = _gl()
    base = dict(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A,
                r_in=15.0, kind="pitched_cambered")
    on = sb.check_apex_zone(sb.ApexInput(straightening=True, **base), t)
    off = sb.check_apex_zone(sb.ApexInput(straightening=False, **base), t)
    assert on.util_tension90 > 0.0 == off.util_tension90
    assert on.util_bending == off.util_bending      # bending applies to both
    assert on.k_dis == 1.7


def test_curved_beam_k_r_reduces_strength():
    t = _gl()
    tight = sb.check_apex_zone(sb.ApexInput(
        m_ap=200.0, v_ap=0.0, b=0.14, h_ap=0.9, r_in=5.0, t_lam=33,
        kind="curved"), t)
    loose = sb.check_apex_zone(sb.ApexInput(
        m_ap=200.0, v_ap=0.0, b=0.14, h_ap=0.9, r_in=50.0, t_lam=33,
        kind="curved"), t)
    assert tight.k_r < 1.0 == loose.k_r
    assert tight.util_bending > loose.util_bending


def test_zone_volume_overrides_the_double_tapered_area():
    assert sb.apex_volume(0.14, 1.0, A, zone_volume=0.5) == 0.5
    assert sb.apex_volume(0.14, 1.0, A, beam_volume=0.3, zone_volume=0.5) \
        == pytest.approx(0.2)
    t = _gl()
    base = dict(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9, alpha_ap=A,
                r_in=15.0, kind="curved")
    small = sb.check_apex_zone(sb.ApexInput(**base), t)
    big = sb.check_apex_zone(sb.ApexInput(zone_volume=2.0, **base), t)
    assert big.volume == 2.0 and big.k_vol < small.k_vol


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        sb.check_apex_zone(sb.ApexInput(1, 1, 0.1, 0.5, kind="x"), _gl())


def test_2025_has_its_own_checks_and_shares_the_polynomials():
    from eurocodepy.ec5 import uls2025
    assert uls2025.check_apex_zone is not sb.check_apex_zone
    assert uls2025.special_beams.calc_k_l is sb.calc_k_l
    assert uls2025.special_beams.ApexInput is sb.ApexInput


def _steps(rep):
    return {st["symbol"]: st for sec in rep.to_dict()["sections"]
            for st in sec["steps"]}


def test_trace_does_not_change_the_tapered_result():
    t = _gl()
    plain = sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t)
    rep = CalcReport(title="x")
    traced = sb.check_tapered_edge(100.0, 0.14, 0.6, A, True, t, trace=rep)
    assert traced == plain
    st = _steps(rep)
    assert st["k_m,α"]["value"] == pytest.approx(plain.k_m_alpha)
    assert st["k_m,α"]["clause"].endswith("Eq. 6.39")
    assert st["σ_m,α,d / (k_m,α·f_m,d)"]["ok"] == (plain.util_cut <= 1.0)
    assert sb.check_tapered_edge(100.0, 0.14, 0.6, A, False, t,
                                 trace=CalcReport()).k_m_alpha > plain.k_m_alpha


def test_trace_does_not_change_the_apex_result():
    t = _gl()
    inp = sb.ApexInput(m_ap=300.0, v_ap=10.0, b=0.14, h_ap=0.9, alpha_ap=A,
                       r_in=15.0, kind="pitched_cambered", straightening=True)
    plain = sb.check_apex_zone(inp, t)
    rep = CalcReport()
    traced = sb.check_apex_zone(inp, t, trace=rep)
    assert traced == plain
    st = _steps(rep)
    for sym in ("k_l", "k_r", "k_p", "k_dis", "k_vol", "V (apex zone)",
                "σ_t,90,d", "τ_d"):
        assert sym in st, sym
    assert st["k_dis"]["value"] == 1.7
    assert st["τ_d/f_v,d + σ_t,90,d/(k_dis·k_vol·f_t,90,d)"]["value"] == \
        pytest.approx(plain.util_interaction)
    assert rep.to_markdown()                                # renders


def test_trace_says_when_there_is_no_tension_perpendicular():
    t = _gl()
    rep = CalcReport()
    sb.check_apex_zone(sb.ApexInput(m_ap=300.0, v_ap=0.0, b=0.14, h_ap=0.9,
                                    alpha_ap=A, straightening=False), t,
                       trace=rep)
    assert "no tension" in _steps(rep)["σ_t,90,d"]["note"]
