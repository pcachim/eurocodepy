"""Tests for the rectangular RC M-N design (ec2.uls.bend_axial.calc_asl_nm).

Run on Python >= 3.11 with eurocodepy importable:
    python tests/test_bend_axial.py
or:
    pytest tests/test_bend_axial.py
"""
import math

from eurocodepy.ec2.uls import calc_asl, calc_asl_nm

# Reference section / materials used throughout.
B, H, D1, D2 = 0.30, 0.50, 0.05, 0.05
FCK, FYK = 30.0, 500.0
GC, GS = 1.5, 1.15
FCD = FCK / GC
FYD = FYK / GS
D = H - D1


def test_pure_bending_matches_calc_asl():
    """With N = 0 and d1 == d2 the tension steel must equal calc_asl exactly."""
    ref, _eps, _x = calc_asl(B, D, 150.0, FCD, FYD)
    r = calc_asl_nm(B, H, D1, D2, 150.0, 0.0, FCK, FYK, GC, GS)
    assert abs(r["As1"] - ref) < 1e-6
    assert r["As2"] == 0.0
    assert not r["doubly"]


def test_compression_reduces_tension_steel():
    """An axial compression should reduce the required tension reinforcement."""
    bending = calc_asl_nm(B, H, D1, D2, 150.0, 0.0, FCK, FYK, GC, GS)
    comp = calc_asl_nm(B, H, D1, D2, 150.0, 200.0, FCK, FYK, GC, GS)
    assert comp["As1"] < bending["As1"]


def test_tension_increases_tension_steel():
    """An axial tension should increase the required tension reinforcement."""
    bending = calc_asl_nm(B, H, D1, D2, 150.0, 0.0, FCK, FYK, GC, GS)
    tens = calc_asl_nm(B, H, D1, D2, 150.0, -200.0, FCK, FYK, GC, GS)
    assert tens["As1"] > bending["As1"]


def test_high_moment_is_doubly_reinforced():
    """A moment above the singly-reinforced limit must add compression steel."""
    r = calc_asl_nm(B, H, D1, D2, 500.0, 0.0, FCK, FYK, GC, GS)
    assert r["doubly"]
    assert r["As2"] > 0.0
    assert r["mu"] > 0.29


def test_mu_lim_is_about_0_295_for_fck_below_50():
    """The singly/doubly threshold corresponds to x/d = 0.45 (mu_lim ~ 0.295)."""
    # Probe just below and just above by scaling the moment.
    fcd = FCK / GC
    m_lim = 0.295 * B * D * D * fcd * 1000.0   # kNm at the boundary
    below = calc_asl_nm(B, H, D1, D2, m_lim * 0.95, 0.0, FCK, FYK, GC, GS)
    above = calc_asl_nm(B, H, D1, D2, m_lim * 1.05, 0.0, FCK, FYK, GC, GS)
    assert not below["doubly"]
    assert above["doubly"]


def test_as_min_uses_fctm_not_sqrt_fck():
    """Minimum tension steel must follow 0.26*fctm/fyk*b*d (EC2 9.2.1.1)."""
    r = calc_asl_nm(B, H, D1, D2, 1.0, 0.0, FCK, FYK, GC, GS)  # tiny moment
    fctm = 0.30 * FCK ** (2.0 / 3.0)
    as_min_expected = max(0.26 * fctm / FYK, 0.0013) * B * D * 1e4  # cm2
    assert abs(r["As_min"] - as_min_expected) < 1e-6
    # And it must be far below the (wrong) sqrt(fck) value.
    as_min_sqrt = 0.26 * math.sqrt(FCK) / FYK * B * D * 1e4
    assert r["As_min"] < 0.7 * as_min_sqrt


def test_small_eccentricity_is_flagged():
    """Large compression with a small moment is compression-controlled."""
    r = calc_asl_nm(B, H, D1, D2, 20.0, 1500.0, FCK, FYK, GC, GS)
    assert r["note"]
    assert r["As1"] == r["As_min"]


def test_sagging_hogging_magnitude_symmetry():
    """±M with the same axial give the same tension steel magnitude (symmetric
    section): the face is decided by the caller, the area must mirror."""
    rs = calc_asl_nm(B, H, D1, D2, 150.0, 200.0, FCK, FYK, GC, GS)
    rh = calc_asl_nm(B, H, D1, D2, -150.0, 200.0, FCK, FYK, GC, GS)
    assert abs(rs["As1"] - rh["As1"]) < 1e-6
    assert rs["med_s"] > 0 and rh["med_s"] < 0


def test_moment_transfer_sign():
    """M_Eds includes the axial transfer term N*(h/2 - d1)."""
    med, ned = 100.0, 300.0
    r = calc_asl_nm(B, H, D1, D2, med, ned, FCK, FYK, GC, GS)
    assert abs(r["med_s"] - (med + ned * (H / 2.0 - D1))) < 1e-9


if __name__ == "__main__":
    test_pure_bending_matches_calc_asl()
    test_compression_reduces_tension_steel()
    test_tension_increases_tension_steel()
    test_high_moment_is_doubly_reinforced()
    test_mu_lim_is_about_0_295_for_fck_below_50()
    test_as_min_uses_fctm_not_sqrt_fck()
    test_small_eccentricity_is_flagged()
    test_sagging_hogging_magnitude_symmetry()
    test_moment_transfer_sign()
    print("All bend_axial tests passed.")
