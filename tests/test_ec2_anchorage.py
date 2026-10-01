"""EC2 §8.4 / §8.7 anchorage and lap lengths (ec2.uls.anchorage).

Hand-checked against EN 1992-1-1: for C30/37 the ultimate bond stress in good
conditions is f_bd = 2.25·(0.7·0.3·30^(2/3)/1.5) = 3.04 MPa (Table of §8.4.2
commonly quoted as 3.0 MPa), so a Ø16 bar of B500 (f_yd = 434.8 MPa) needs
l_b,rqd = (16/4)·434.8/3.04 = 572 mm ≈ 36·φ.
"""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2.uls import (
    anchorage_coefficients, basic_anchorage_length, beam_cover_distance,
    bond_conditions_beam, bond_strength, design_anchorage_length,
    lap_coefficient_alpha6, lap_length,
)
from eurocodepy.ec2.uls import anchorage as anc

FCK, FYK = 30.0, 500.0
FYD = FYK / 1.15


def test_bond_strength_c30():
    r = bond_strength(FCK, 16.0)
    fctm = 0.30 * FCK ** (2 / 3)
    assert r["fctd"] == pytest.approx(0.7 * fctm / 1.5)
    assert r["eta1"] == 1.0 and r["eta2"] == 1.0
    assert r["fbd"] == pytest.approx(3.0414, abs=1e-3)


def test_poor_bond_and_large_bars():
    good = bond_strength(FCK, 16.0)["fbd"]
    poor = bond_strength(FCK, 16.0, good_bond=False)
    assert poor["eta1"] == 0.7
    assert poor["fbd"] == pytest.approx(0.7 * good)
    big = bond_strength(FCK, 40.0)
    assert big["eta2"] == pytest.approx(0.92)
    assert big["fbd"] == pytest.approx(0.92 * good)
    assert bond_strength(FCK, 32.0)["eta2"] == 1.0


def test_fctd_is_capped_at_c60():
    assert (bond_strength(90.0, 16.0)["fctd"]
            == pytest.approx(bond_strength(60.0, 16.0)["fctd"]))
    assert bond_strength(60.0, 16.0)["fctd"] == pytest.approx(2.032, abs=2e-3)
    assert (bond_strength(50.0, 16.0)["fbd"]
            > bond_strength(30.0, 16.0)["fbd"])


def test_basic_anchorage_length():
    fbd = bond_strength(FCK, 16.0)["fbd"]
    lb = basic_anchorage_length(16.0, FYD, fbd)
    assert lb == pytest.approx(571.8, abs=0.5)
    assert lb / 16.0 == pytest.approx(35.7, abs=0.1)
    with pytest.raises(ValueError):
        basic_anchorage_length(16.0, FYD, 0.0)


def test_bond_conditions_in_a_beam():
    assert bond_conditions_beam(250.0, "top") == "good"
    assert bond_conditions_beam(500.0, "top") == "poor"
    assert bond_conditions_beam(500.0, "bottom") == "good"
    with pytest.raises(ValueError):
        bond_conditions_beam(500.0, "side")


def test_table_8_2_coefficients():
    phi = 16.0
    # straight, tension: alpha2 = 1 - 0.15 (cd - phi)/phi
    a = anchorage_coefficients(phi, cd=phi)
    assert a["alpha2"] == pytest.approx(1.0)
    a = anchorage_coefficients(phi, cd=3 * phi)
    assert a["alpha2"] == pytest.approx(0.7)
    assert anchorage_coefficients(phi, cd=10 * phi)["alpha2"] == 0.7   # floor
    assert anchorage_coefficients(phi, cd=0.5 * phi)["alpha2"] == 1.0  # ceiling
    # bent: alpha1 = 0.7 only when cd > 3 phi
    assert anchorage_coefficients(phi, cd=4 * phi, shape="bent")["alpha1"] == 0.7
    assert anchorage_coefficients(phi, cd=2 * phi, shape="bent")["alpha1"] == 1.0
    assert anchorage_coefficients(phi, cd=3 * phi, shape="bent")["alpha2"] == \
        pytest.approx(1.0)
    # confinement: alpha3 = 1 - K lambda
    a_s = math.pi * phi ** 2 / 4
    a = anchorage_coefficients(phi, cd=phi, k=0.1, sum_ast=3.0 * a_s,
                               sum_ast_min=0.25 * a_s)
    assert a["lam"] == pytest.approx(2.75)
    assert a["alpha3"] == pytest.approx(1 - 0.1 * 2.75)
    # welded bars and transverse pressure
    assert anchorage_coefficients(phi, cd=phi, welded=True)["alpha4"] == 0.7
    assert anchorage_coefficients(phi, cd=phi, pressure=5.0)["alpha5"] == \
        pytest.approx(0.8)
    # compression: nothing but alpha4
    c = anchorage_coefficients(phi, cd=3 * phi, kind="compression")
    assert (c["alpha1"], c["alpha2"], c["alpha3"], c["alpha5"]) == (1, 1, 1, 1)
    # alpha2*alpha3*alpha5 >= 0.7 (Table 8.2 note)
    low = anchorage_coefficients(phi, cd=3 * phi, k=0.1, sum_ast=5 * a_s,
                                 sum_ast_min=0.0, pressure=7.0)
    assert low["alpha2"] * low["alpha3"] * low["alpha5"] >= 0.7 - 1e-9
    for bad in (dict(kind="shear"), dict(shape="hook")):
        with pytest.raises(ValueError):
            anchorage_coefficients(phi, cd=phi, **bad)


def test_design_anchorage_length_straight():
    r = design_anchorage_length(16.0, FCK, FYK, cd=16.0)
    assert r["lb_rqd"] == pytest.approx(571.8, abs=0.5)
    assert r["lbd"] == pytest.approx(r["lb_rqd"])          # all alphas = 1
    assert not r["governed_by_min"]
    assert r["sigma_sd"] == pytest.approx(FYD)
    # Eq. 8.4: product of the alphas times lb,rqd
    r2 = design_anchorage_length(16.0, FCK, FYK, cd=4 * 16.0, shape="bent")
    prod = (r2["alpha1"] * r2["alpha2"] * r2["alpha3"] * r2["alpha4"]
            * r2["alpha5"])
    assert r2["lbd"] == pytest.approx(prod * r2["lb_rqd"])
    assert r2["lbd"] < r["lbd"]                             # a hook shortens it


def test_minimum_lengths_govern_for_small_stresses():
    r = design_anchorage_length(16.0, FCK, FYK, cd=16.0, sigma_sd=20.0)
    assert r["governed_by_min"]
    assert r["lbd"] == pytest.approx(max(0.3 * r["lb_rqd"], 160.0, 100.0))
    c = design_anchorage_length(16.0, FCK, FYK, cd=16.0, kind="compression",
                                sigma_sd=20.0)
    assert c["lb_min"] == pytest.approx(max(0.6 * c["lb_rqd"], 160.0, 100.0))
    tiny = design_anchorage_length(6.0, FCK, FYK, cd=6.0, sigma_sd=1.0)
    assert tiny["lb_min"] == 100.0                          # the 100 mm floor


def test_poor_bond_and_class_trends():
    good = design_anchorage_length(16.0, FCK, FYK, cd=16.0)["lbd"]
    poor = design_anchorage_length(16.0, FCK, FYK, cd=16.0,
                                   good_bond=False)["lbd"]
    assert poor == pytest.approx(good / 0.7)
    assert design_anchorage_length(16.0, 50.0, FYK, cd=16.0)["lbd"] < good
    assert design_anchorage_length(25.0, FCK, FYK, cd=25.0)["lbd"] > good


def test_alpha6_table_8_3():
    assert lap_coefficient_alpha6(10.0) == 1.0
    assert lap_coefficient_alpha6(25.0) == 1.0
    assert lap_coefficient_alpha6(33.0) == pytest.approx(1.149, abs=1e-3)
    assert lap_coefficient_alpha6(50.0) == pytest.approx(math.sqrt(2.0))
    assert lap_coefficient_alpha6(100.0) == 1.5
    with pytest.raises(ValueError):
        lap_coefficient_alpha6(-1.0)


def test_lap_length():
    r = lap_length(16.0, FCK, FYK, cd=16.0, rho1=50.0)
    assert r["alpha6"] == pytest.approx(math.sqrt(2.0))
    assert r["l0"] == pytest.approx(math.sqrt(2.0) * r["lb_rqd"])
    assert r["l0"] == pytest.approx(808.6, abs=1.0)
    assert r["l0_min"] == pytest.approx(max(0.3 * r["alpha6"] * r["lb_rqd"],
                                            15 * 16.0, 200.0))
    assert lap_length(16.0, FCK, FYK, cd=16.0, rho1=25.0)["l0"] \
        == pytest.approx(r["lb_rqd"])
    assert lap_length(16.0, FCK, FYK, cd=16.0, rho1=100.0)["alpha6"] == 1.5
    small = lap_length(16.0, FCK, FYK, cd=16.0, sigma_sd=10.0)
    assert small["governed_by_min"] and small["l0"] == small["l0_min"]
    # no alpha4 in a lap, alpha1 = 1 (straight)
    assert "alpha4" not in r and r["alpha1"] == 1.0


def test_lap_confinement_uses_the_minimum_transverse_steel():
    a_s = math.pi * 16.0 ** 2 / 4
    plain = lap_length(16.0, FCK, FYK, cd=16.0, k=0.1)           # ΣAst = 0
    assert plain["alpha3"] == 1.0              # lam = -1 would give 1.1: capped
    conf = lap_length(16.0, FCK, FYK, cd=16.0, k=0.1, sum_ast=4.0 * a_s)
    assert conf["alpha3"] == pytest.approx(1.0 - 0.1 * 3.0)       # (4-1)·As/As
    assert conf["l0"] < plain["l0"]


def test_beam_cover_distance_fig_8_3():
    # 300 wide, 38 to the bar (30 cover + 8 stirrup), 4 x Ø16
    # clear spacing = (300 - 76 - 64)/3 = 53.3 -> half = 26.7 < 38
    assert beam_cover_distance(300.0, 38.0, 4, 16.0) == pytest.approx(26.667,
                                                                       abs=1e-3)
    assert beam_cover_distance(300.0, 38.0, 1, 16.0) == 38.0      # no neighbour
    assert beam_cover_distance(300.0, 38.0, 2, 16.0) == 38.0      # wide spacing
    assert beam_cover_distance(300.0, 38.0, 2, 16.0, side_cover=25.0) == 25.0


def test_validation():
    with pytest.raises(ValueError):
        bond_strength(FCK, 0.0)
    with pytest.raises(ValueError):
        anchorage_coefficients(16.0, 16.0, kind="x")


def test_trace_records_the_steps():
    rep = CalcReport(title="anchorage")
    r = design_anchorage_length(16.0, FCK, FYK, cd=16.0, trace=rep)
    syms = [st.symbol for s in rep.sections for st in s.steps]
    for want in ("f_bd", "l_b,rqd", "l_bd", "α_2"):
        assert want in syms
    lbd = next(st for s in rep.sections for st in s.steps if st.symbol == "l_bd")
    assert lbd.value == pytest.approx(r["lbd"])
    rep2 = CalcReport()
    lap_length(16.0, FCK, FYK, cd=16.0, trace=rep2)
    assert any(st.symbol == "l_0" for s in rep2.sections for st in s.steps)
    assert design_anchorage_length(16.0, FCK, FYK, cd=16.0)["lbd"] == r["lbd"]


def test_module_is_exported():
    import eurocodepy.ec2.uls as uls
    assert uls.anchorage is anc
    assert uls.design_anchorage_length is anc.design_anchorage_length
