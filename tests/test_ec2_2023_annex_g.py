"""EN 1992-1-1:2023 Annex G: membrane, shell and slab elements (ec2.uls2023.annex_g and checks)."""
import math
import random
import warnings

import numpy as np
import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2 import uls, uls2023
from eurocodepy.ec2.uls2023 import annex_g as g
from eurocodepy.ec2.uls2023 import slab_design as sd

TOL = 1e-9


# ── G.3 membrane elements ───────────────────────────────────────────────────

@pytest.mark.parametrize(("sx", "sy", "txy", "case", "cot", "ftdx", "ftdy", "scd"), [
    (5.0, 3.0, 2.0, "tension", 1.0, 7.0, 5.0, 4.0),                       # Table G.1 row 1
    (-5.0, 2.0, 3.0, "x_compression", 5 / 3, 0.0, 2.0 + 9 / 5, 5 * (1 + 0.36)),
    (2.0, -6.0, 3.0, "y_compression", 0.5, 2.0 + 9 / 6, 0.0, 6 * (1 + 0.25)),
])
def test_table_g1_rows(sx, sy, txy, case, cot, ftdx, ftdy, scd):
    r = g.membrane_optimum(sx, sy, txy)
    assert r["case"] == case
    assert (r["cot"], r["ftdx"], r["ftdy"], r["sigma_cd"]) == pytest.approx((cot, ftdx, ftdy, scd))


def test_no_reinforcement_when_both_compressive_and_sx_sy_exceed_tau2():
    assert not g.membrane_needs_reinforcement(-3.0, -2.0, 0.5)
    assert g.membrane_needs_reinforcement(-3.0, -2.0, 3.0)            # σxσy = 6 < 9
    assert g.membrane_needs_reinforcement(-3.0, 2.0, 0.0)
    r = g.membrane_optimum(-3.0, -2.0, 0.5)
    assert r["case"] == "no_reinforcement" and r["cot"] is None
    assert (r["ftdx"], r["ftdy"]) == (0.0, 0.0)
    centre, radius = -2.5, math.sqrt(0.25 + 0.25)
    assert r["sigma_cd"] == pytest.approx(abs(centre - radius))       # principal compression


def test_tau_zero_with_compression_has_an_infinite_strut_angle():
    r = g.membrane_optimum(-4.0, 1.0, 0.0)
    assert r["cot"] == math.inf and r["ftdy"] == 1.0 and r["sigma_cd"] == 4.0


def test_table_g1_matches_2004_calc_reinf_plane_and_the_brute_force_optimum():
    rnd = random.Random(7)
    for _ in range(1500):
        sx, sy, t = rnd.uniform(-10, 10), rnd.uniform(-10, 10), rnd.uniform(0, 6)
        a = g.membrane_optimum(sx, sy, t)
        asx, asy, asc, _cot = uls.calc_reinf_plane(sx, sy, t)
        assert (a["ftdx"], a["ftdy"], a["sigma_cd"]) == pytest.approx((asx, asy, asc), abs=1e-9)
        if a["cot"] is not None and t > 0.05 and math.isfinite(a["cot"]):
            # equilibrium (G.3), (G.4), (G.5) at the optimum angle
            r = g.membrane_resistances(sx, sy, t, a["cot"])
            assert (max(r["ftdx"], 0.0), max(r["ftdy"], 0.0)) == pytest.approx(
                (a["ftdx"], a["ftdy"]), abs=1e-8)
            # no other cot θ needs less total reinforcement
            best = min((max(sx + t * c, 0) + max(sy + t / c, 0)
                        for c in np.linspace(0.05, 20.0, 4000)
                        if sx + t * c >= 0 and sy + t / c >= 0), default=None)
            if best is not None:
                assert a["ftdx"] + a["ftdy"] <= best + 1e-6


def test_resistances_for_a_chosen_angle_eqs_g3_g5():
    r = g.membrane_resistances(5.0, 3.0, 2.0, 2.0)
    assert r["ftdx"] == pytest.approx(5.0 + 2.0 * 2.0)
    assert r["ftdy"] == pytest.approx(3.0 + 2.0 / 2.0)
    assert r["sigma_cd"] == pytest.approx(2.0 * (2.0 + 0.5))
    assert r["valid"]
    assert not g.membrane_resistances(-5.0, 3.0, 2.0, 1.0)["valid"]   # ftdx < 0


def test_deformation_capacity_limits_g6_g7():
    # optimum for (5, 3, 2): ftdx* = 7, ftdy* = 5
    assert g.deformation_capacity_ok(7.0, 5.0, 5.0, 3.0, 2.0)
    assert g.deformation_capacity_ok(0.4 * 7.0, 2.5 * 5.0, 5.0, 3.0, 2.0)    # at the limits
    assert not g.deformation_capacity_ok(0.39 * 7.0, 5.0, 5.0, 3.0, 2.0)
    assert not g.deformation_capacity_ok(7.0, 2.6 * 5.0, 5.0, 3.0, 2.0)
    # optimum 0 in x: only 0 is acceptable
    assert g.deformation_capacity_ok(0.0, 3.8, -5.0, 2.0, 3.0)
    assert not g.deformation_capacity_ok(0.5, 3.8, -5.0, 2.0, 3.0)


def test_nu_and_strain_estimates_g8_to_g11():
    assert g.calc_nu_simple() == 0.4
    assert g.calc_nu(0.0) == 1.0 and g.calc_nu(0.01) == pytest.approx(1 / 2.1)
    assert g.calc_eps1_from_x(0.002, 2.0) == pytest.approx(0.002 + 0.003 * 4)
    assert g.calc_eps1_from_y(0.002, 2.0) == pytest.approx(0.002 + 0.003 / 4)
    eps = 434.78 / 200000.0
    # only x required (G.10), only y (G.11), both: the larger (G.3(7)a-b)
    assert g.estimate_eps1(5.0, 0.0, 2.0, 434.78, 200000.0) == pytest.approx(g.calc_eps1_from_x(eps, 2.0))
    assert g.estimate_eps1(0.0, 5.0, 2.0, 434.78, 200000.0) == pytest.approx(g.calc_eps1_from_y(eps, 2.0))
    assert g.estimate_eps1(5.0, 5.0, 2.0, 434.78, 200000.0) == pytest.approx(g.calc_eps1_from_x(eps, 2.0))
    # λ > 1 lowers the strain (d); uncracked: fctd/Ecd (c)
    assert g.estimate_eps1(5.0, 5.0, 1.0, 434.78, 200000.0, lam=1.5) < g.estimate_eps1(
        5.0, 5.0, 1.0, 434.78, 200000.0)
    assert g.estimate_eps1(1.0, 1.0, 1.0, 434.78, 200000.0, f_ctd=1.3, e_cd=33000.0,
                           uncracked=True) == pytest.approx(1.3 / 33000.0)
    with pytest.raises(ValueError, match="no reinforcement"):
        g.estimate_eps1(0.0, 0.0, 1.0, 434.78, 200000.0)
    assert g.estimate_nu(7.0, 5.0, 1.0, 434.78, 200000.0) == pytest.approx(
        g.calc_nu(g.calc_eps1_from_x(eps, 1.0)))


# ── G.4 shell and slab elements ─────────────────────────────────────────────

def test_sandwich_eqs_g12_to_g17():
    n, m = (10.0, 5.0, 2.0), (20.0, 10.0, 5.0)
    t, z = 0.08, 0.12
    s = g.sandwich_stresses(n, m, t, z)
    assert s["bottom"] == pytest.approx((0.5 * 10 / t + 20 / (t * z), 0.5 * 5 / t + 10 / (t * z),
                                         0.5 * 2 / t - 5 / (t * z)))
    assert s["top"] == pytest.approx((0.5 * 10 / t - 20 / (t * z), 0.5 * 5 / t - 10 / (t * z),
                                      0.5 * 2 / t + 5 / (t * z)))
    # bottom + top carry the membrane force n/t exactly, and the moment
    assert s["bottom"][0] + s["top"][0] == pytest.approx(n[0] / t)
    assert (s["bottom"][0] - s["top"][0]) * t * z / 2 == pytest.approx(m[0])


def test_sandwich_is_the_2004_shell_with_the_layers_labelled_the_other_way():
    # the layer calc_reinf_shell calls "top" is Annex G's "bottom" (all three components)
    rec, h = 0.04, 0.2
    t, z = 2 * rec, h - 2 * rec
    old = uls.calc_reinf_shell(10.0, 5.0, 2.0, 20.0, 10.0, 5.0, rec, h)
    new = g.shell_design((10.0, 5.0, 2.0), (20.0, 10.0, 5.0), t, z)
    assert old[:4] == pytest.approx([new["bottom"]["ftdx"], new["bottom"]["ftdy"],
                                     new["bottom"]["sigma_cd"], new["bottom"]["cot"]])
    # (the 2004 function returns a meaningless cot θ when no reinforcement is needed)
    assert new["top"]["case"] == "no_reinforcement" and new["top"]["cot"] is None
    assert old[4:7] == pytest.approx([new["top"]["ftdx"], new["top"]["ftdy"],
                                      new["top"]["sigma_cd"]])
    assert new["bottom"]["stresses"] == pytest.approx(
        g.sandwich_stresses((10.0, 5.0, 2.0), (20.0, 10.0, 5.0), t, z)["bottom"])


def test_calc_reinf_shell_2004_returns_eight_values():
    r = uls.calc_reinf_shell(10.0, 5.0, 2.0, 20.0, 10.0, 5.0, 0.04, 0.2)    # used to raise TypeError
    assert r.shape == (8,) and np.all(np.isfinite(r[:3])) and np.all(np.isfinite(r[4:7]))
    assert np.isnan(uls.calc_reinf_shell(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.06, 0.2)).all()


@pytest.mark.parametrize(("mx", "my", "mxy", "case", "mrdx", "mrdy"), [
    (5.0, 3.0, 2.0, 1, 7.0, 5.0),                                  # Table G.2 row 1
    (-5.0, 2.0, 3.0, 2, 0.0, 2.0 + 9 / 5),                         # row 2
    (2.0, -6.0, 3.0, 3, 2.0 + 9 / 6, 0.0),                         # row 3
    (-4.0, -3.0, 1.0, 4, 0.0, 0.0),                                # row 4
])
def test_table_g2_bottom_layer(mx, my, mxy, case, mrdx, mrdy):
    r = g.slab_optimum_bottom(mx, my, mxy)
    assert r["case"] == case
    assert (r["m_rdx"], r["m_rdy"]) == pytest.approx((mrdx, mrdy))


@pytest.mark.parametrize(("mx", "my", "mxy", "case", "mrdx", "mrdy"), [
    (-5.0, -3.0, 2.0, 1, 7.0, 5.0),                                # Table G.3 row 1
    (5.0, -2.0, 3.0, 2, 0.0, 2.0 + 9 / 5),                         # row 2: mx > |mxy|, mxmy <= mxy²
    (-2.0, 6.0, 3.0, 3, 2.0 + 9 / 6, 0.0),                         # row 3
    (4.0, 3.0, 1.0, 4, 0.0, 0.0),                                  # row 4: hogging reinforcement not needed
])
def test_table_g3_top_layer(mx, my, mxy, case, mrdx, mrdy):
    r = g.slab_optimum_top(mx, my, mxy)
    assert r["case"] == case
    assert (r["m_rdx"], r["m_rdy"]) == pytest.approx((mrdx, mrdy))


def test_tables_g2_g3_are_complete_and_the_capacity_balances_the_moment():
    rnd = random.Random(3)
    for _ in range(2000):
        mx, my, mxy = rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-5, 5)
        for res in (g.slab_optimum_bottom(mx, my, mxy), g.slab_optimum_top(mx, my, mxy)):
            assert res["case"] in (1, 2, 3, 4)
            assert res["m_rdx"] >= 0.0 and res["m_rdy"] >= 0.0
    # Table G.2 equals the membrane optimum of the same numbers (Table G.1) for the bottom layer
    for mx, my, mxy in [(5.0, 3.0, 2.0), (-5.0, 2.0, 3.0), (2.0, -6.0, 3.0), (-4.0, -3.0, 1.0)]:
        slab, mem = g.slab_optimum_bottom(mx, my, mxy), g.membrane_optimum(mx, my, mxy)
        assert (slab["m_rdx"], slab["m_rdy"]) == pytest.approx((mem["ftdx"], mem["ftdy"]))


def test_slab_equations_g18_to_g21_and_the_range_rule():
    r = g.slab_required_moments(5.0, 3.0, 2.0, cot_bot=1.0, cot_top=1.0)
    assert r["m_rdx"] == pytest.approx(5.0 + 2.0) and r["m_rdy"] == pytest.approx(3.0 + 2.0)
    assert r["m_rdx_top"] == pytest.approx(0.0 + 0) or r["m_rdx_top"] >= 0.0
    r2 = g.slab_required_moments(5.0, 3.0, 2.0, cot_bot=2.0, cot_top=1.0)
    assert r2["m_rdx"] == pytest.approx(5.0 + 2.0 * 2.0)
    assert r2["m_rdy"] == pytest.approx(3.0 + 2.0 / 2.0)
    assert r2["optimum"]["m_rdx"] == pytest.approx(7.0)
    assert r["within_range"]["m_rdx"] and r2["within_range"]["m_rdx"]        # 9 ≤ 2,5·7
    far = g.slab_required_moments(5.0, 3.0, 2.0, cot_bot=8.0)                # 5+16 = 21 > 2,5·7
    assert not far["within_range"]["m_rdx"]
    assert g.slab_torsion_simplified_ok(5.0, 0.17, 20.0)                     # 0,07·0,17²·20·1000 = 40,5
    assert not g.slab_torsion_simplified_ok(41.0, 0.17, 20.0)


# ── G.5 crack control ───────────────────────────────────────────────────────

def test_crack_control_eqs_g22_to_g27():
    assert g.crack_inclination_applies(45.0)
    assert not g.crack_inclination_applies(15.0) and not g.crack_inclination_applies(80.0)
    th = math.radians(40.0)
    sr = g.calc_sr_m_cal(th, 0.2, 0.3)
    assert sr == pytest.approx(1.0 / (math.sin(th) / 0.2 + math.cos(th) / 0.3))
    assert g.calc_sr_m_cal(math.pi / 2, 0.2, 0.3) == pytest.approx(0.2)      # cracks ⟂ x
    # (G.24)/(G.25): sinθ / cosθ in the denominator of the spacing ratio
    kw = {"k_t": 0.4, "f_ct_eff": 1.45, "alpha_e": 6.0, "e_s": 200000.0}
    dx = g.calc_eps_diff_x(300.0, sr_m_cal=sr, sr_m_cal_x=0.2, theta=th, rho_px_eff=0.02, **kw)
    ratio = sr / (0.2 * math.sin(th))
    first = (300.0 - 0.4 * ratio * 1.45 / 0.02 * (1 + 6.0 * 0.02)) / 200000.0
    assert dx == pytest.approx(max(first, 0.6 * 300.0 / 200000.0))
    dy = g.calc_eps_diff_y(250.0, sr_m_cal=sr, sr_m_cal_y=0.3, theta=th, rho_py_eff=0.015, **kw)
    ratio_y = sr / (0.3 * math.cos(th))
    first_y = (250.0 - 0.4 * ratio_y * 1.45 / 0.015 * (1 + 6.0 * 0.015)) / 200000.0
    assert dy == pytest.approx(max(first_y, 0.6 * 250.0 / 200000.0))
    assert dx >= 0.6 * 300.0 / 200000.0 and dy >= 0.6 * 250.0 / 200000.0     # the max() floor
    e2 = g.calc_eps_2(-2.0, th, 33000.0)
    assert e2 == pytest.approx(2.0 * (1 / math.tan(th) + math.tan(th)) / 33000.0)
    assert g.calc_eps_sm_cm(dx, dy, -e2) == pytest.approx(dx + dy + e2)


def test_cot_theta_from_g27():
    # σx = σy = 0: cot⁴θ = ρx/ρy
    assert g.calc_cot_theta_cracking(0.0, 0.0, 2.0, 0.02, 0.01) == pytest.approx((2.0) ** 0.25)
    rho_x, rho_y, sx, sy, t = 0.01, 0.015, 3.0, 1.0, 2.0
    c = g.calc_cot_theta_cracking(sx, sy, t, rho_x, rho_y)
    assert t / rho_x * c**4 + sx / rho_x * c**3 - sy / rho_y * c - t / rho_y == pytest.approx(0, abs=1e-9)
    assert c > 0


# ── membrane check ──────────────────────────────────────────────────────────

def _mem(**kw):
    base = {"n_xx": 100.0, "n_yy": 50.0, "n_xy": 20.0, "fck": 30.0, "fyk": 500.0, "thickness": 0.2}
    base.update(kw)
    return uls2023.MembraneInput(**base)


def test_membrane_check_designs_table_g1_and_checks_nu_fcd():
    r = uls2023.eurocode2_membrane_check(_mem())
    fyd = 500.0e3 / 1.15
    assert r.details["case"] == "tension" and r.theta == 1.0
    assert (r.nsx, r.nsy, r.nc) == pytest.approx((120.0, 70.0, 40.0))
    assert r.asx == pytest.approx(120.0 / fyd) and r.asy == pytest.approx(70.0 / fyd)
    assert r.asx_bot == r.asx_top == pytest.approx(r.asx / 2)
    assert r.details["nu"] == 0.4 and not r.crushing
    assert r.sigma_c == pytest.approx(40.0 / 0.2)


def test_membrane_check_applies_nu_where_2004_does_not():
    kw = {"n_xx": -1500.0, "n_yy": -200.0, "n_xy": 800.0}
    r = uls2023.eurocode2_membrane_check(_mem(**kw))
    assert r.details["case"] == "x_compression"
    assert r.sigma_c / 1e3 == pytest.approx(9.633, abs=1e-3) and r.fcd / 1e3 == pytest.approx(20.0)
    assert r.crushing                                       # 9,63 > 0,4·20
    assert not uls.eurocode2_membrane_check(uls.MembraneInput(**{**kw, "fck": 30.0, "fyk": 500.0,
                                                                 "thickness": 0.2})).crushing
    # the refined ν (G.9) is higher for this strain state and the section passes
    strain = uls2023.eurocode2_membrane_check(_mem(nu_mode="strain", **kw))
    assert strain.details["nu"] > 0.4 and strain.details["eps_1"] > 0.0
    assert strain.details["nu"] == pytest.approx(g.calc_nu(strain.details["eps_1"]))
    # without reinforcement the limit is fcd (G.3(1)), not ν·fcd
    both = uls2023.eurocode2_membrane_check(_mem(n_xx=-400.0, n_yy=-300.0, n_xy=50.0))
    assert both.details["case"] == "no_reinforcement" and both.details["nu"] == 1.0
    assert both.asx == both.asy == 0.0 and both.theta is None and not both.crushing
    crush = uls2023.eurocode2_membrane_check(_mem(n_xx=-5000.0, n_yy=-4500.0, n_xy=50.0))
    assert crush.crushing and crush.sigma_c / 1e3 > 20.0     # principal compression above fcd


def test_membrane_check_options_trace_and_errors():
    with pytest.raises(ValueError, match="nu_mode"):
        uls2023.eurocode2_membrane_check(_mem(nu_mode="x"))
    hi = uls2023.eurocode2_membrane_check(_mem(fck=60.0, n_xx=-900.0, n_yy=-100.0, n_xy=300.0))
    assert hi.fcd / 1e3 == pytest.approx((40 / 60) ** (1 / 3) * 60 / 1.5)
    rep = CalcReport(title="membrane G")
    uls2023.eurocode2_membrane_check(_mem(), trace=rep)
    symbols = {st.symbol for sec in rep.sections for st in sec.steps}
    assert {"cot θ*", "A_sx", "ν", "σ_cd ≤ ν·f_cd"} <= symbols
    inp = uls2023.MembraneInput.from_partial_factors("2023", "accidental", n_xx=1.0, n_yy=1.0,
                                                     n_xy=1.0, fck=30.0, fyk=500.0, thickness=0.2)
    assert (inp.gamma_c, inp.gamma_s) == (1.15, 1.0)


# ── slab design ─────────────────────────────────────────────────────────────

def _slab(**kw):
    base = {"m_x": 50.0, "m_y": 30.0, "m_xy": 10.0, "fck": 30.0, "fyk": 500.0, "thickness": 0.2,
            "cover_bot_x": 0.03, "cover_bot_y": 0.04, "cover_top_x": 0.03, "cover_top_y": 0.04}
    base.update(kw)
    return sd.SlabInput(**base)


def test_slab_design_uses_the_optimum_capacities_and_the_covers():
    r = sd.eurocode2_slab_check(_slab())
    assert r.details["case_bot"] == 1 and r.details["m_rdx"] == pytest.approx(60.0)
    assert r.details["m_rdy"] == pytest.approx(40.0)
    # bottom x and y are the strips of 60 and 40 kNm/m with d = 0,17 and 0,16 m
    ref_x = uls.calc_asl(1.0, 0.17, 60.0, 20.0, 500 / 1.15)[0] * 1e-4
    ref_y = uls.calc_asl(1.0, 0.16, 40.0, 20.0, 500 / 1.15)[0] * 1e-4
    assert r.asx_bot == pytest.approx(ref_x) and r.asy_bot == pytest.approx(ref_y)
    # top: mx, my > 0 and mx·my > mxy² (Table G.3 row 4): nothing needed
    assert r.details["case_top"] == 4 and r.details["m_rdx_top"] == 0.0
    assert r.asx_top == r.asy_top == 0.0
    assert r.details["torsion_simplified_ok"]


def test_slab_design_minimum_reinforcement_eq_12_1():
    r = sd.eurocode2_slab_check(_slab(m_x=1.0, m_y=1.0, m_xy=0.5))
    fctm = 0.3 * 30.0 ** (2 / 3)
    assert r.asx_bot == pytest.approx(fctm * 0.2**2 / (5.4 * 0.17 * 500.0))   # Mcr/(0,9·d·fyk)
    assert sd._fctm(60.0) == pytest.approx(1.1 * 60.0 ** (1 / 3))


def test_slab_design_hogging_and_torsion_limits():
    r = sd.eurocode2_slab_check(_slab(m_x=-40.0, m_y=-20.0, m_xy=5.0, min_reinf="demand"))
    assert r.details["case_top"] == 1 and r.details["m_rdx_top"] == pytest.approx(45.0)
    assert r.asx_top > 0 and r.asy_top > 0 and r.asx_bot == r.asy_bot == 0.0
    dflt = sd.eurocode2_slab_check(_slab(m_x=-40.0, m_y=-20.0, m_xy=5.0))     # default is "demand"
    assert dflt.asx_bot == dflt.asy_bot == 0.0
    mn = sd.eurocode2_slab_check(_slab(m_x=-40.0, m_y=-20.0, m_xy=5.0, min_reinf="bottom"))
    assert mn.asx_bot > 0 and mn.asy_bot > 0 and mn.asx_top == r.asx_top
    with pytest.warns(UserWarning, match="0,07"):
        big = sd.eurocode2_slab_check(_slab(m_xy=60.0, method="optimum"))   # forced: warns
    assert not big.details["torsion_simplified_ok"] and big.details["method"] == "optimum"
    with pytest.warns(UserWarning, match="exceeds the capacity"):
        over = sd.eurocode2_slab_check(_slab(m_x=300.0, m_y=10.0, m_xy=5.0))
    assert math.isnan(over.asx_bot)


def test_slab_design_trace_and_isolation_from_2004_names():
    rep = CalcReport(title="slab G")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sd.eurocode2_slab_check(_slab(), trace=rep)
    symbols = {st.symbol for sec in rep.sections for st in sec.steps}
    assert {"m_Rdx", "m'_Rdx", "A_sx,bot"} <= symbols
    assert uls2023.SlabInput is uls.SlabInput                 # 2004 names untouched
    assert uls2023.slab_design.__name__ == "eurocodepy.ec2.uls2023.slab_design"


# ── sandwich model (G.4(1)-(3)) ─────────────────────────────────────────────

def test_sandwich_with_ned_zero_gives_the_table_capacities():
    # the sandwich model with nEd = 0 IS Tables G.2/G.3: ftd·t·z = mRd
    for mx, my, mxy in [(50.0, 30.0, 10.0), (-5.0, 20.0, 12.0), (-40.0, -20.0, 5.0),
                        (15.0, -30.0, 8.0)]:
        opt = sd.eurocode2_slab_check(_slab(m_x=mx, m_y=my, m_xy=mxy, method="optimum"))
        sw = sd.eurocode2_slab_check(_slab(m_x=mx, m_y=my, m_xy=mxy, method="sandwich"))
        assert sw.details["method"] == "sandwich" and opt.details["method"] == "optimum"
        for k in ("m_rdx", "m_rdy", "m_rdx_top", "m_rdy_top"):
            assert sw.details[k] == pytest.approx(opt.details[k]), k


def test_sandwich_areas_are_ftd_t_over_fyd():
    r = sd.eurocode2_slab_check(_slab(method="sandwich"))
    t = 2 * (0.03 + 0.04 + 0.03 + 0.04) / 4
    z = 0.2 - t
    assert (r.details["t_layer"], r.details["z"]) == pytest.approx((t, z))
    fyd = 500.0 / 1.15
    assert r.asx_bot == pytest.approx(60.0 / z / (fyd * 1e3))       # (mx + |mxy|)/(z·fyd)
    assert r.asy_bot == pytest.approx(40.0 / z / (fyd * 1e3))
    assert r.asx_top == r.asy_top == 0.0
    assert r.details["layers"]["bottom"]["case"] == "tension"
    assert r.details["layers"]["top"]["case"] == "no_reinforcement"


def test_auto_takes_the_tables_inside_their_range_and_the_sandwich_outside():
    inside = sd.eurocode2_slab_check(_slab())
    assert inside.details["method"] == "optimum" and inside.details["torsion_simplified_ok"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")       # (the strut may crush: that is reported, not a "tables" warning)
        out = sd.eurocode2_slab_check(_slab(m_xy=45.0))
    assert out.details["method"] == "sandwich" and not out.details["torsion_simplified_ok"]
    assert out.details["crushing"] in (True, False)
    # in-plane forces always need the sandwich model
    shell = sd.eurocode2_slab_check(_slab(n_x=100.0))
    assert shell.details["method"] == "sandwich"
    with pytest.raises(ValueError, match="nEd = 0"):
        sd.eurocode2_slab_check(_slab(n_x=100.0, method="optimum"))


def test_sandwich_in_plane_forces_enter_both_layers():
    zero = dict(m_x=0.0, m_y=0.0, m_xy=0.0, method="sandwich")
    ten = sd.eurocode2_slab_check(_slab(n_x=200.0, **zero))
    # pure tension in x: n/2 per layer, As = n/(2·fyd) in both
    assert ten.asx_bot == pytest.approx(100.0 / (500.0 / 1.15 * 1e3))
    assert ten.asx_top == pytest.approx(100.0 / (500.0 / 1.15 * 1e3))
    assert ten.asy_bot == ten.asy_top == 0.0
    base = sd.eurocode2_slab_check(_slab(method="sandwich"))
    t = base.details["t_layer"]
    # compression relieves the bottom layer, the top layer is then in compression
    comp = sd.eurocode2_slab_check(_slab(method="sandwich", n_x=-400.0))
    assert comp.asx_bot < base.asx_bot
    assert comp.details["layers"]["top"]["stresses"][0] == pytest.approx(
        -0.5 * 400.0 / t - 50.0 / (t * base.details["z"]))


def test_sandwich_crushing_check_and_nu_modes():
    big = dict(m_x=60.0, m_y=60.0, m_xy=190.0, thickness=0.2, method="sandwich")
    with pytest.warns(UserWarning, match="bottom and top layer.*exceeds"):
        r = sd.eurocode2_slab_check(_slab(**big))
    assert r.details["crushing"] and all(v["crushing"] for v in r.details["layers"].values())
    assert r.details["layers"]["bottom"]["nu"] == 0.4
    # the refined ν is higher than 0,4 and the verdict follows it
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sr = sd.eurocode2_slab_check(_slab(nu_mode="strain", **big))
    nu = sr.details["layers"]["bottom"]["nu"]
    assert nu == pytest.approx(g.estimate_nu(
        sr.details["layers"]["bottom"]["ftdx"], sr.details["layers"]["bottom"]["ftdy"],
        sr.details["layers"]["bottom"]["cot"], 500 / 1.15, 200000.0))
    assert sr.details["layers"]["bottom"]["sigma_cd"] > 0
    # a section that needs no reinforcement is limited to fcd, not ν·fcd
    both = sd.eurocode2_slab_check(_slab(m_x=-20.0, m_y=-20.0, m_xy=1.0, method="sandwich"))
    assert both.details["layers"]["bottom"]["nu"] == 1.0


def test_sandwich_minimum_reinforcement_and_errors():
    kw = dict(m_x=0.0, m_y=0.0, m_xy=0.0, method="sandwich")
    assert sd.eurocode2_slab_check(_slab(**kw)).asx_bot == 0.0
    mn = sd.eurocode2_slab_check(_slab(min_reinf="bottom", **kw))
    assert mn.asx_bot > 0 and mn.asy_bot > 0 and mn.asx_top == 0.0
    with pytest.raises(ValueError, match="method"):
        sd.eurocode2_slab_check(_slab(method="x"))
    with pytest.raises(ValueError, match="nu_mode"):
        sd.eurocode2_slab_check(_slab(nu_mode="x"))
    with pytest.raises(ValueError, match="do not fit"):
        sd.eurocode2_slab_check(_slab(method="sandwich", thickness=0.07))


def test_sandwich_trace():
    rep = CalcReport(title="sandwich")
    sd.eurocode2_slab_check(_slab(method="sandwich"), trace=rep)
    symbols = {st.symbol for sec in rep.sections for st in sec.steps}
    assert {"t", "z", "layer bottom", "σ_cd (top)", "A_sx,bot"} <= symbols
