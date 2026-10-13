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
    # σc ≤ ν·fcd, ν = 0,6(1 − fck/250); fcd where no reinforcement is needed
    nu = 1.0 if (nsx == 0.0 and nsy == 0.0 and math.isnan(theta)) else 0.6 * (1.0 - FCK / 250.0)
    assert res.crushing == bool(nc > nu * fcd * t)
    assert res.details["nu"] == pytest.approx(nu)
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


def test_membrane_nu_and_clause_text():
    # 2004: ν = 0,6(1 − fck/250) = 0,528 → ν·fcd = 10,6 MPa; Annex G (2023) gives 0,4·fcd = 8 MPa
    r = eurocode2_membrane_check(MembraneInput(-1500.0, -200.0, 800.0, FCK, FYK, 0.2, GC, GS, ACC))
    nu = 0.6 * (1 - FCK / 250.0)
    assert r.details["nu"] == pytest.approx(nu) and r.details["case"] == "x compression"
    assert r.sigma_c / 1e3 == pytest.approx(9.633, abs=1e-3) and not r.crushing    # 9,6 < 0,528·20
    big = eurocode2_membrane_check(MembraneInput(-2500.0, -200.0, 800.0, FCK, FYK, 0.2, GC, GS, ACC))
    assert big.sigma_c / 1e3 < ACC * FCK / GC                                    # below fcd...
    assert big.crushing and big.sigma_c / 1e3 > nu * FCK / GC                    # ...above ν·fcd
    rep = CalcReport(title="m")
    eurocode2_membrane_check(MembraneInput(100.0, 50.0, 20.0, FCK, FYK, 0.2, GC, GS, ACC), trace=rep)
    clauses = {st.clause for sec in rep.sections for st in sec.steps if st.clause}
    assert not any("6.109" in c for c in clauses) and any("Annex F" in c for c in clauses)


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
