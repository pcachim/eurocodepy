"""EN 1992-1-1:2023 Clause 8.3 torsion: ec2.uls2023.torsion and the combined shear+torsion check.

Hand values: b = 0,3 m, h = 0,5 m, cover (to bar centre) 0,05 m, C30, B500, cot θ = 2.
"""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2 import uls, uls2023
from eurocodepy.ec2.uls2023 import torsion as tr

FYD = 500.0 / 1.15


def nu_g(cot, fyd=FYD, es=200000.0):
    """ν of Eq. (G.9) with ε1 = max(G.10, G.11), ε = fyd/Es (G.3(7)b)."""
    eps = fyd / es
    return 1.0 / (1.0 + 110.0 * max(eps + (eps + 0.001) * cot**2, eps + (eps + 0.001) / cot**2))


def test_wall_geometry_eq_8_79_8_80():
    t = tr.calc_t_eff(0.15, 1.6)
    assert t == pytest.approx(0.15 / 1.6)
    assert tr.calc_t_eff(0.15, 1.6, cover=0.05) == pytest.approx(0.1)         # >= 2c
    assert tr.calc_t_eff(0.15, 1.6, cover=0.05, thickness=0.08) == 0.08       # hollow: actual wall
    w = tr.rectangular_wall(0.3, 0.5, 0.05)
    assert w["t_eff"] == pytest.approx(0.1)
    assert w["a_k"] == pytest.approx(0.2 * 0.4)
    assert w["u_k"] == pytest.approx(2 * (0.2 + 0.4))
    assert tr.rectangular_wall(0.3, 0.5, 5.0)["t_eff"] == pytest.approx(0.499 * 0.3)   # keeps Ak > 0
    tau = tr.calc_tau_t_ed(30.0, 0.08, 0.1)
    assert tau == pytest.approx(30.0 / (2 * 0.08 * 0.1) / 1000.0)
    assert tr.calc_v_ed_wall(tau, 0.1, 0.4) == pytest.approx(tau * 0.1 * 0.4 * 1000.0)
    assert tr.distribute_torque(60.0, [1.0, 2.0, 3.0]) == pytest.approx([10.0, 20.0, 30.0])


def test_reduced_cover_8_3_4_5():
    assert tr.effective_cover(0.3, 0.4, 0.05) == pytest.approx(0.07 * 0.3)    # 1,33 < 1,5, c > 0,07·bmin
    assert tr.effective_cover(0.3, 0.5, 0.05) == 0.05                          # 1,67 >= 1,5
    assert tr.effective_cover(0.3, 0.4, 0.015) == 0.015                        # c <= 0,07·bmin


def test_resistance_formulae_eqs_8_81_to_8_85():
    assert tr.calc_cot_range() == (0.4, 2.5)
    assert tr.calc_tau_t_rd_sw(5e-4, 0.1, FYD, 2.0) == pytest.approx(2.0 * 5e-4 / 0.1 * FYD)
    assert tr.calc_tau_t_rd_sl(1e-3, FYD, 0.1, 1.2, 2.0) == pytest.approx(1e-3 * FYD / (0.1 * 1.2 * 2.0))
    assert tr.calc_tau_t_rd_max(0.5, 20.0, 2.0) == pytest.approx(0.5 * 20.0 / 2.5)
    r = tr.calc_tau_t_rd(3.0, 2.0, 4.0)
    assert r == {"tau_t_rd": 2.0, "mode": "longitudinal"}
    assert tr.calc_tau_t_rd(1.0, 2.0, 4.0)["mode"] == "stirrups"
    assert tr.calc_tau_t_rd(3.0, 2.0, 1.5)["mode"] == "crushing"
    assert tr.torque_from_stress(1.0, 0.08, 0.1) == pytest.approx(2 * 0.08 * 0.1 * 1000.0)


def test_nu_follows_annex_g():
    assert tr.torsion_nu(1.0) == 0.60                      # 8.3.4(3)
    assert tr.torsion_nu(2.0) == pytest.approx(nu_g(2.0))
    assert tr.torsion_nu(2.0) == pytest.approx(0.379, abs=1e-3)
    assert tr.torsion_nu(2.5) == pytest.approx(0.292, abs=1e-3)
    assert tr.torsion_nu(0.8) == pytest.approx(nu_g(0.8))   # flatter than 45°: G.11 governs
    assert tr.torsion_nu(0.5) == pytest.approx(tr.torsion_nu(2.0))   # symmetric in cot ↔ 1/cot
    assert tr.torsion_nu(2.0, f_yd=500.0 / 1.0) < tr.torsion_nu(2.0)  # higher strain, lower ν
    assert tr.torsion_nu(2.0) < 0.5                         # the value of 8.2.3(6) is not safe here


def test_design_matches_the_hand_calculation():
    r = tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0, cover=0.05)
    a_k, t_eff, u_k = 0.08, 0.1, 1.2
    fcd = 1.0 * 30.0 / 1.5                                   # eta_cc = 1 (fck <= 40)
    tau_t = 30.0 / (2 * a_k * t_eff) / 1000.0
    assert r["tau_t_ed"] == pytest.approx(tau_t)
    assert r["nu"] == pytest.approx(nu_g(2.0))
    assert r["TRd_max"] == pytest.approx(2 * a_k * t_eff * nu_g(2.0) * fcd / 2.5 * 1000.0)
    assert r["Asw_tor_s"] == pytest.approx(tau_t * t_eff / (2.0 * FYD))        # Eq. (8.82)
    assert r["Asl_tor"] == pytest.approx(tau_t * t_eff * u_k * 2.0 / FYD)      # Eq. (8.83)
    assert r["util"] == pytest.approx(30.0 / r["TRd_max"])
    assert (r["t_ef"], r["A_k"], r["u_k"]) == pytest.approx((t_eff, a_k, u_k))


def test_design_and_resistance_are_consistent():
    d = tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0, cover=0.05)
    r = tr.calc_torsion_resistance(0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0,
                                   d["Asw_tor_s"], d["Asl_tor"], cover=0.05)
    assert r["t_rd_sw"] == pytest.approx(30.0)               # the steel designed for 30 kNm
    assert r["t_rd_sl"] == pytest.approx(30.0)
    assert r["t_rd"] == pytest.approx(30.0)
    assert r["t_rd_max"] > r["t_rd"]
    less = tr.calc_torsion_resistance(0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0,
                                      d["Asw_tor_s"] / 2, d["Asl_tor"], cover=0.05)
    assert less["mode"] == "stirrups"
    assert less["t_rd"] == pytest.approx(15.0)


def test_eta_cc_alpha_cc_nu_and_cot_range():
    hi = tr.calc_torsion(30.0, 0.3, 0.5, 60.0, 1.5, 500.0, 1.15, 2.0, cover=0.05)
    assert hi["TRd_max"] == pytest.approx(
        2 * 0.08 * 0.1 * nu_g(2.0) * ((40 / 60) ** (1 / 3) * 60 / 1.5) / 2.5 * 1000.0)
    one = tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 1.0, cover=0.05)
    assert one["nu"] == 0.60
    given = tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 0.8, cover=0.05, nu=0.45)
    assert given["nu"] == 0.45                                # an explicit nu wins
    assert tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 0.8, cover=0.05)["nu"] == pytest.approx(nu_g(0.8))
    flat = tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 0.4, cover=0.05, nu=0.45)
    assert flat["Asl_tor"] < given["Asl_tor"]
    with pytest.raises(ValueError, match="8.85"):
        tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 3.0)
    with pytest.raises(ValueError, match="8.85"):
        tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 0.3, nu=0.5)
    assert tr.calc_torsion(30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0, cover=0.05,
                           alpha_cc=0.85)["TRd_max"] < tr.calc_torsion(
        30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0, cover=0.05)["TRd_max"]


def test_squat_section_uses_the_reduced_cover():
    sq = tr.calc_torsion(30.0, 0.3, 0.4, 30.0, 1.5, 500.0, 1.15, 2.0, cover=0.05)
    assert sq["cover"] == pytest.approx(0.021)
    assert sq["t_ef"] == pytest.approx(max(0.12 / 1.4, 0.042))


def test_interaction_eq_8_86():
    assert tr.interaction_sum([0.3, 0.2, 0.1]) == pytest.approx(0.6)
    r = tr.interaction_ok((30.0, 100.0), (-60.0, 200.0), (50.0, 100.0))
    assert r["ratios"] == pytest.approx([0.3, 0.3, 0.5])
    assert r["sum"] == pytest.approx(1.1) and not r["ok"]
    assert tr.interaction_ok((10.0, 100.0), (10.0, 100.0))["ok"]


def test_calc_torsion_is_a_drop_in_for_2004_arguments_and_trace():
    args = (30.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.0)
    r4 = uls.calc_torsion(*args, cover=0.05)
    r3 = uls2023.calc_torsion(*args, cover=0.05, alpha_cc=1.0)
    assert set(r4) <= set(r3)
    assert r3["TRd_max"] != pytest.approx(r4["TRd_max"])     # nu 0,5 vs 0,6·(1 - fck/250)
    rep = CalcReport(title="torsion 2023")
    uls2023.calc_torsion(*args, cover=0.05, trace=rep)
    syms = {st.symbol for sec in rep.sections for st in sec.steps}
    assert {"τ_t,Ed", "τ_t,Rd,max", "T_Rd,max", "A_sw,tor /s", "A_sl,tor"} <= syms


# ── combined check ──────────────────────────────────────────────────────────

def _inp(**kw):
    base = {"b": 0.3, "h": 0.5, "cover": 0.05, "fck": 30.0, "fyk": 500.0, "as_long": 0.0015}
    base.update(kw)
    return uls2023.ShearTorsionInput(**base)


def test_combined_check_shares_the_angle_and_adds_the_stirrups():
    r = uls2023.eurocode2_shear_torsion_check(_inp(), 150.0, 15.0)
    assert r.cot == 2.5 and r.details["shear_mode"] == "stirrups"
    assert r.asw_total_s == pytest.approx(r.asw_shear_s + 2 * r.asw_tor_s)
    assert r.asw_tor_s > 0 and r.asl_tor_total > 0
    assert sum(r.asl_tor_by_face.values()) == pytest.approx(r.asl_tor_total)
    assert r.interaction == pytest.approx(r.t_ratio + r.v_ratio)             # Eq. (8.86)
    assert r.passed and not r.crushing
    # torsion was designed for the shear angle
    t = uls2023.calc_torsion(15.0, 0.3, 0.5, 30.0, 1.5, 500.0, 1.15, 2.5, cover=0.05)
    assert r.asw_tor_s == pytest.approx(t["Asw_tor_s"])
    assert r.trd_max == pytest.approx(t["TRd_max"])


def test_combined_check_without_shear_reinforcement_uses_cot_theta_min():
    r = uls2023.eurocode2_shear_torsion_check(_inp(), 30.0, 20.0)
    assert r.details["shear_mode"] in ("no_verification", "no_shear_reinf")
    assert r.cot == 2.5
    assert r.vrd_max is None and r.v_ratio == 0.0
    ra = uls2023.eurocode2_shear_torsion_check(_inp(ductility="A"), 30.0, 20.0)
    assert ra.cot == pytest.approx(2.0)                                       # class A: -20 %


def test_combined_check_crushing_and_interaction():
    just = uls2023.eurocode2_shear_torsion_check(_inp(), 150.0, 30.0)         # Annex G ν: T/TRd,max = 0,93
    assert just.interaction > 1.0 and not just.passed
    big = uls2023.eurocode2_shear_torsion_check(_inp(), 300.0, 60.0)
    assert big.interaction > 1.0 and big.crushing and not big.passed
    crush = uls2023.eurocode2_shear_torsion_check(_inp(), 700.0, 10.0)
    assert crush.crushing and crush.cot == 1.0 and crush.details["nu"] == 0.60


def test_combined_check_options_distribution_trace_and_annex():
    top = uls2023.eurocode2_shear_torsion_check(_inp(), 150.0, 30.0)
    per = uls2023.eurocode2_shear_torsion_check(_inp(), 150.0, 30.0, distribution_mode="perimeter")
    assert top.asl_tor_by_face["side_left"] == 0.0 < per.asl_tor_by_face["side_left"]
    off = uls2023.eurocode2_shear_torsion_check(_inp(min_shear=False), 30.0, 0.0)
    assert off.asw_shear_s == 0.0
    rep = CalcReport(title="shear+torsion 2023")
    uls2023.eurocode2_shear_torsion_check(_inp(), 150.0, 30.0, trace=rep)
    titles = [sec.title for sec in rep.sections]
    assert any("8.3.6" in t for t in titles)
    inp = uls2023.ShearTorsionInput.from_partial_factors(
        "2023", "accidental", b=0.3, h=0.5, cover=0.05, fck=30.0, fyk=500.0, as_long=0.0015)
    assert (inp.gamma_c, inp.gamma_s, inp.gamma_v) == (1.15, 1.0, 1.15)
    assert uls2023.eurocode2_shear_torsion_check(inp, 150.0, 30.0).asw_total_s > 0
