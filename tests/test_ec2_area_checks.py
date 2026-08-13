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
    assert res.crushing == bool(nc > fcd * t)
    assert res.theta == pytest.approx(theta, rel=0, abs=1e-15)
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


def _slab_expected(mxb, myb, mxt, myt, t, cover):
    fcd_mpa = ACC * FCK / GC
    fyd_mpa = FYK / GS
    coef = max(0.26 * _fctm(FCK) / FYK, 0.0013)

    def _as(med, c):
        d = t - c
        if d <= 0.0 or med <= 0.0:
            return 0.0
        as_cm2, _e, _x = calc_asl(1.0, d, med, fcd_mpa, fyd_mpa)
        return max(max(as_cm2, 0.0) * 1e-4, coef * d)
    return (_as(mxb, cover), _as(myb, cover), _as(-mxt, cover), _as(-myt, cover))


SLAB_CASES = [
    (12.0, 6.0, -4.0, -2.0),
    (20.0, 0.0, 0.0, -8.0),
    (0.0, 0.0, 0.0, 0.0),        # nothing in tension → minimum only where d>0
]


@pytest.mark.parametrize("mxb,myb,mxt,myt", SLAB_CASES)
def test_slab_parity(mxb, myb, mxt, myt):
    t, c = 0.20, 0.03
    exp = _slab_expected(mxb, myb, mxt, myt, t, c)
    res = eurocode2_slab_check(
        SlabInput(mxb, myb, mxt, myt, FCK, FYK, t, c, c, c, c, GC, GS, ACC))
    got = (res.asx_bot, res.asy_bot, res.asx_top, res.asy_top)
    for a, b in zip(got, exp):
        assert a == pytest.approx(b, rel=0, abs=1e-15)


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
