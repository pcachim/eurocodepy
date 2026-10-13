"""EN 1992-1-1 concrete *area* composites: membrane (§6.109) and slab (§6.1).

Two properties, mirroring the other composite checks:

* **parity** — the composite reproduces the raw scalar formulae
  (``calc_reinf_plane`` for the membrane, ``calc_asl`` for the slab), so the
  design values are unchanged by moving the procedure into the composite;
* **trace invariant + structure** — passing a ``trace`` does not change the
  result and records a non-empty, well-formed report.

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_ec2_area_checks.py
"""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2.uls.shell import (
    annex_f_strut_limit,
    deformation_capacity_ok_2004,
    elastic_compression_angle,
    membrane_strut_limit,
    principal_stresses,
)
from eurocodepy.ec2.uls import (
    MembraneInput,
    SlabInput,
    calc_asl,
    calc_reinf_plane,
    eurocode2_membrane_check,
    eurocode2_slab_check,
)

FCK, FYK = 30.0, 500.0
GC, GS, ACC = 1.5, 1.15, 1.0

MEMBRANE_CASES = [
    (100.0, 50.0, 20.0),      # all tension
    (-200.0, 50.0, 30.0),     # x in compression branch
    (50.0, -200.0, 30.0),     # y in compression branch
    (-150.0, -150.0, 80.0),   # biaxial compression / crushing regime
]


@pytest.mark.parametrize("n_xx,n_yy,n_xy", MEMBRANE_CASES)
def test_membrane_parity(n_xx, n_yy, n_xy):
    t = 0.2
    fyd = FYK * 1e3 / GS
    fcd = ACC * FCK * 1e3 / GC
    nsx, nsy, nc, theta = calc_reinf_plane(n_xx, n_yy, n_xy)
    res = eurocode2_membrane_check(
        MembraneInput(n_xx, n_yy, n_xy, FCK, FYK, t, GC, GS, ACC))
    assert res.asx == pytest.approx(max(nsx, 0.0) / fyd, rel=0, abs=1e-15)
    assert res.asy == pytest.approx(max(nsy, 0.0) / fyd, rel=0, abs=1e-15)
    assert res.sigma_c == pytest.approx(nc / t, rel=0, abs=1e-9)
    # EN 1992-1-1:2004 Annex F.1(3)-(4): σc ≤ fcd without reinforcement, ν·fcd with it
    unreinforced = nsx == 0.0 and nsy == 0.0 and math.isnan(theta)
    nu = 1.0 if unreinforced else 0.6 * (1.0 - FCK / 250.0)
    assert res.crushing == bool(nc > nu * fcd * t)
    assert res.details["nu"] == pytest.approx(nu) and res.details["strut_model"] == "annex_f"
    # and the EN 1992-2 §6.109 strength, as an option
    r109 = eurocode2_membrane_check(MembraneInput(
        n_xx, n_yy, n_xy, FCK, FYK, t, GC, GS, ACC, strut_model="6.109"))
    lim = membrane_strut_limit(n_xx / t, n_yy / t, n_xy / t, FCK, fcd,
                               None if unreinforced else theta)
    assert r109.crushing == bool(nc / t > lim["limit"])
    assert r109.details["nu"] == pytest.approx(lim["factor"])
    assert lim["case"] == ("biaxial_compression" if unreinforced else "yielding")
    assert res.theta == pytest.approx(theta, rel=0, abs=1e-15, nan_ok=True)
    # even top/bottom split
    assert res.asx_bot == res.asx_top == pytest.approx(res.asx / 2.0)
    assert res.asy_bot == res.asy_top == pytest.approx(res.asy / 2.0)


def test_membrane_trace_invariant_and_structure():
    inp = MembraneInput(100.0, 50.0, 20.0, FCK, FYK, 0.2, GC, GS, ACC)
    base = eurocode2_membrane_check(inp)
    rep = CalcReport(title="membrane")
    traced = eurocode2_membrane_check(inp, trace=rep)
    assert traced.asx == base.asx and traced.asy == base.asy
    assert traced.crushing == base.crushing
    d = rep.to_dict()
    assert d["sections"] and any(s["steps"] for s in d["sections"])
    symbols = [st["symbol"] for s in d["sections"] for st in s["steps"]]
    assert "n_xx" in symbols and "A_sx" in symbols


def _fctm(fck):
    return 0.30 * fck ** (2.0 / 3.0) if fck <= 50.0 else \
        2.12 * math.log(1.0 + (fck + 8.0) / 10.0)


def _slab_expected(mxb, myb, mxt, myt, t, cover, min_reinf="bottom"):
    fcd_mpa = ACC * FCK / GC
    fyd_mpa = FYK / GS
    coef = max(0.26 * _fctm(FCK) / FYK, 0.0013)

    def _as(med, c, bottom):
        d = t - c
        if d <= 0.0:
            return 0.0
        if med <= 0.0:
            return coef * d if (min_reinf == "all" or (min_reinf == "bottom" and bottom)) else 0.0
        as_cm2, _e, _x = calc_asl(1.0, d, med, fcd_mpa, fyd_mpa)
        return max(max(as_cm2, 0.0) * 1e-4, coef * d)
    return (_as(mxb, cover, True), _as(myb, cover, True), _as(-mxt, cover, False), _as(-myt, cover, False))


SLAB_CASES = [
    (12.0, 6.0, -4.0, -2.0),
    (20.0, 0.0, 0.0, -8.0),
    (0.0, 0.0, 0.0, 0.0),        # nothing in tension → the minimum on the faces min_reinf asks for
]


@pytest.mark.parametrize("min_reinf", ["demand", "bottom", "all"])
@pytest.mark.parametrize("mxb,myb,mxt,myt", SLAB_CASES)
def test_slab_parity(mxb, myb, mxt, myt, min_reinf):
    t, c = 0.20, 0.03
    exp = _slab_expected(mxb, myb, mxt, myt, t, c, min_reinf)
    res = eurocode2_slab_check(
        SlabInput(mxb, myb, mxt, myt, FCK, FYK, t, c, c, c, c, GC, GS, ACC, min_reinf))
    if min_reinf == "demand":                                  # the default
        dflt = eurocode2_slab_check(SlabInput(mxb, myb, mxt, myt, FCK, FYK, t, c, c, c, c, GC, GS, ACC))
        assert (dflt.asx_bot, dflt.asy_bot, dflt.asx_top, dflt.asy_top) == (
            res.asx_bot, res.asy_bot, res.asx_top, res.asy_top)
    got = (res.asx_bot, res.asy_bot, res.asx_top, res.asy_top)
    for a, b in zip(got, exp):
        assert a == pytest.approx(b, rel=0, abs=1e-15)


def test_slab_min_reinf_option_and_default():
    inp = dict(mx_bot=0.0, my_bot=0.0, mx_top=0.0, my_top=0.0, fck=FCK, fyk=FYK,
               thickness=0.2, cover_bot_x=0.03, cover_bot_y=0.03, cover_top_x=0.03,
               cover_top_y=0.03)
    dflt = eurocode2_slab_check(SlabInput(**inp))              # default: a face with no tension gets 0
    assert dflt.asx_bot == dflt.asy_bot == dflt.asx_top == dflt.asy_top == 0.0
    bot = eurocode2_slab_check(SlabInput(min_reinf="bottom", **inp))
    assert bot.asx_bot > 0 and bot.asy_bot > 0 and bot.asx_top == bot.asy_top == 0.0
    assert eurocode2_slab_check(SlabInput(min_reinf="all", **inp)).asx_top > 0
    with pytest.raises(ValueError, match="min_reinf"):
        eurocode2_slab_check(SlabInput(min_reinf="top", **inp))


def test_slab_warns_when_over_reinforced_or_without_solution():
    import warnings
    inp = dict(mx_top=0.0, my_top=0.0, fck=FCK, fyk=FYK, thickness=0.2, cover_bot_x=0.03,
               cover_bot_y=0.03, cover_top_x=0.03, cover_top_y=0.03)
    with warnings.catch_warnings():
        warnings.simplefilter("error")                      # below the limit: silent
        eurocode2_slab_check(SlabInput(mx_bot=150.0, my_bot=10.0, **inp))
    with pytest.warns(UserWarning, match=r"x/d = 0\.\d+ > 0\.45.*over-reinforced"):
        r = eurocode2_slab_check(SlabInput(mx_bot=200.0, my_bot=10.0, **inp))
    assert math.isfinite(r.asx_bot)                         # the value is still returned
    with pytest.warns(UserWarning, match="exceeds the capacity"):
        assert math.isnan(eurocode2_slab_check(SlabInput(mx_bot=400.0, my_bot=10.0, **inp)).asx_bot)
    # C60 (fcd = 40 MPa): the limit is 0.35 and 300 kNm/m gives x/d ≈ 0.40
    hi = dict(inp, fck=60.0)
    with pytest.warns(UserWarning, match="> 0.35"):
        eurocode2_slab_check(SlabInput(mx_bot=300.0, my_bot=10.0, **hi))


def test_membrane_strut_default_is_annex_f_of_en_1992_1_1():
    # σcd ≤ ν·fcd, ν = 0,6(1 − fck/250) = 0,528 (F.1(4), Expression 6.5); fcd where no reinforcement (F.1(3))
    r = eurocode2_membrane_check(MembraneInput(-1500.0, -200.0, 800.0, FCK, FYK, 0.2, GC, GS, ACC))
    assert r.details["nu"] == pytest.approx(0.528) and r.details["strut_model"] == "annex_f"
    assert r.sigma_c / 1e3 == pytest.approx(9.633, abs=1e-3) and not r.crushing     # 9,63 < 0,528·20 = 10,56
    big = eurocode2_membrane_check(MembraneInput(-1900.0, -200.0, 800.0, FCK, FYK, 0.2, GC, GS, ACC))
    assert big.sigma_c / 1e3 < ACC * FCK / GC and big.crushing                      # below fcd, above ν·fcd
    both = eurocode2_membrane_check(MembraneInput(-400.0, -300.0, 50.0, FCK, FYK, 0.2, GC, GS, ACC))
    assert both.details["nu"] == 1.0 and both.details["case"] == "biaxial compression"
    rep = CalcReport(title="m")
    eurocode2_membrane_check(MembraneInput(100.0, 50.0, 20.0, FCK, FYK, 0.2, GC, GS, ACC), trace=rep)
    clauses = {st.clause for sec in rep.sections for st in sec.steps if st.clause}
    assert any("Annex F.1(4)" in c for c in clauses) and not any("6.109" in c for c in clauses)
    with pytest.raises(ValueError, match="strut_model"):
        eurocode2_membrane_check(MembraneInput(1.0, 1.0, 1.0, FCK, FYK, 0.2, GC, GS, ACC, strut_model="x"))
    assert annex_f_strut_limit(30.0, 20.0, None) == {
        **annex_f_strut_limit(30.0, 20.0, None), "limit": 20.0, "factor": 1.0}
    assert annex_f_strut_limit(30.0, 20.0, 1.0)["limit"] == pytest.approx(0.528 * 20.0)


def test_deformation_capacity_limits_of_annex_f_2004():
    # optimum for (5, 3, 2): ftdx* = 7, ftdy* = 5; ½·ft* ≤ ft ≤ 2·ft*
    assert deformation_capacity_ok_2004(7.0, 5.0, 5.0, 3.0, 2.0)
    assert deformation_capacity_ok_2004(3.5, 10.0, 5.0, 3.0, 2.0)
    assert not deformation_capacity_ok_2004(3.4, 5.0, 5.0, 3.0, 2.0)
    assert not deformation_capacity_ok_2004(7.0, 10.1, 5.0, 3.0, 2.0)
    assert deformation_capacity_ok_2004(0.0, 3.8, -5.0, 2.0, 3.0)         # optimum 0: only 0 allowed
    assert not deformation_capacity_ok_2004(0.1, 3.8, -5.0, 2.0, 3.0)


def test_membrane_strut_limit_of_en_1992_2_6_109():
    # (-1500, -200, 800) kN/m, t = 0,2, C30: θ = 28.1°, θel = 25.5°, |Δθ| = 2.6°
    r = eurocode2_membrane_check(MembraneInput(-1500.0, -200.0, 800.0, FCK, FYK, 0.2, GC, GS, ACC,
                                               strut_model="6.109"))
    nu1 = 0.6 * (1 - FCK / 250.0)
    s = r.details["strut"]
    assert r.details["case"] == "x compression" and s["case"] == "yielding"
    assert s["theta"] == pytest.approx(28.07, abs=0.01) and s["theta_el"] == pytest.approx(25.45, abs=0.01)
    assert s["factor"] == pytest.approx(nu1 * (1 - 0.032 * s["delta_theta"]))     # Eq. (6.112)
    assert r.details["nu"] == pytest.approx(0.4837, abs=1e-4)
    assert r.sigma_c / 1e3 == pytest.approx(9.633, abs=1e-3) and not r.crushing    # 9,63 < 9,67 MPa
    big = eurocode2_membrane_check(MembraneInput(-1700.0, -200.0, 800.0, FCK, FYK, 0.2, GC, GS, ACC,
                                                 strut_model="6.109"))
    assert big.sigma_c / 1e3 < ACC * FCK / GC and big.crushing                     # below fcd, above σcd,max
    rep = CalcReport(title="m")
    tension = eurocode2_membrane_check(MembraneInput(100.0, 50.0, 20.0, FCK, FYK, 0.2, GC, GS, ACC,
                                                     strut_model="6.109"), trace=rep)
    assert not tension.details["strut"]["angle_ok"]                                # |θ − θel| = 26° > 15°
    assert any(st.ok is False for sec in rep.sections for st in sec.steps if st.symbol == "σ_cd,max / f_cd")
    assert not tension.crushing                                                    # (the strut stress is small)
    clauses = {st.clause for sec in rep.sections for st in sec.steps if st.clause}
    assert any("EN 1992-2:2005 §6.109" in c for c in clauses)
    assert not any(c.startswith("EN 1992-1-1 §6.109") for c in clauses)


def test_membrane_strut_limit_function_cases():
    # Eq. (6.110): 0,85·fcd·(1 + 3,8α)/(1 + α)²: 0,85 in uniaxial compression, 1,02 for α = 1
    f = 20.0e3
    uni = membrane_strut_limit(-10.0, 0.0, 0.0, FCK, f, None)
    assert uni["alpha"] == 0.0 and uni["factor"] == pytest.approx(0.85) and uni["case"] == "biaxial_compression"
    eq = membrane_strut_limit(-10.0, -10.0, 0.0, FCK, f, None)
    assert eq["alpha"] == pytest.approx(1.0) and eq["factor"] == pytest.approx(0.85 * 4.8 / 4.0)
    mid = membrane_strut_limit(-10.0, -4.7, 0.0, FCK, f, None)
    assert mid["alpha"] == pytest.approx(0.47) and mid["factor"] == pytest.approx(
        0.85 * (1 + 3.8 * 0.47) / 1.47**2)
    # Eq. (6.112): the reduction grows with |θ − θel| up to 15°, beyond it the angle is flagged
    base = membrane_strut_limit(-1.0, 3.0, 2.0, FCK, f, 1.0)
    assert base["delta_theta"] == pytest.approx(abs(45.0 - base["theta_el"]))
    ok = membrane_strut_limit(0.0, 0.0, 5.0, FCK, f, 1.0)                           # θ = θel = 45°
    assert ok["delta_theta"] == pytest.approx(0.0) and ok["factor"] == pytest.approx(0.528)
    far = membrane_strut_limit(10.0, 0.0, 1.0, FCK, f, 1.0)
    assert not far["angle_ok"] and far["factor"] == pytest.approx(0.528 * (1 - 0.032 * 15.0))
    # θel: 45° in pure shear, 0° in compression along x, 90° along y
    assert elastic_compression_angle(0.0, 0.0, 5.0) == pytest.approx(45.0)
    assert elastic_compression_angle(-5.0, 0.0, 0.0) == pytest.approx(0.0)
    assert elastic_compression_angle(0.0, -5.0, 0.0) == pytest.approx(90.0)
    s1, s2 = principal_stresses(3.0, -1.0, 2.0)
    assert (s1, s2) == pytest.approx((1.0 + math.sqrt(8.0), 1.0 - math.sqrt(8.0)))


def test_calc_reinf_plane_theta_where_it_is_undefined():
    assert calc_reinf_plane(-4.0, 1.0, 0.0)[3] == math.inf               # τ = 0, x compression
    assert calc_reinf_plane(1.0, -4.0, 0.0)[3] == 0.0                    # τ = 0, y compression
    assert math.isnan(calc_reinf_plane(-3.0, -2.0, 0.5)[3])              # no reinforcement


def test_slab_trace_invariant_and_structure():
    inp = SlabInput(12.0, 6.0, -4.0, -2.0, FCK, FYK, 0.2,
                    0.03, 0.03, 0.03, 0.03, GC, GS, ACC)
    base = eurocode2_slab_check(inp)
    rep = CalcReport(title="slab")
    traced = eurocode2_slab_check(inp, trace=rep)
    assert (traced.asx_bot, traced.asy_bot, traced.asx_top, traced.asy_top) == \
        (base.asx_bot, base.asy_bot, base.asx_top, base.asy_top)
    d = rep.to_dict()
    symbols = [st["symbol"] for s in d["sections"] for st in s["steps"]]
    assert "m_x,bot" in symbols and "A_sx,bot" in symbols


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
