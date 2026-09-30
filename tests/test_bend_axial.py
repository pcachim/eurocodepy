"""Tests for the rectangular RC M-N design (ec2.uls.bend_axial.calc_asl_nm).

Run on Python >= 3.11 with eurocodepy importable:
    python tests/test_bend_axial.py
or:
    pytest tests/test_bend_axial.py
"""
import math

import numpy as np

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


# ---------------------------------------------------------------------------
# Strain-compatibility design (calc_asl_nm_strain / method="auto")
# ---------------------------------------------------------------------------

from eurocodepy.ec2.uls import calc_asl_nm_strain  # noqa: E402


def _fibre_mrd(as1, as2, ned, b=B, h=H, d1=D1, d2=D2, nf=1500):
    """Independent M_Rd at N_Ed: numerical fibres + bisection on x (sagging)."""
    fcd, fyd, es = FCK / GC, FYK / GS, 200e3
    ys = (np.arange(nf) + 0.5) / nf * h
    dy = h / nf

    def forces(x):
        k = 3.5e-3 / x if x <= h else 2e-3 / (x - 3 / 7 * h)
        ec = np.clip(k * (x - ys), 0.0, None)
        sc = np.where(ec < 2e-3, fcd * (1 - (1 - ec / 2e-3) ** 2), fcd) * (ec > 0)
        fc = (sc * b * dy * 1e3).sum()
        mc = (sc * b * dy * 1e3 * (h / 2 - ys)).sum()
        s1 = np.clip(es * k * (x - (h - d1)), -fyd, fyd)
        s2 = np.clip(es * k * (x - d2), -fyd, fyd)
        f1, f2 = as1 * 1e-4 * s1 * 1e3, as2 * 1e-4 * s2 * 1e3
        return fc + f1 + f2, mc + f2 * (h / 2 - d2) - f1 * (h / 2 - d1)

    lo, hi = 1e-4, 500 * h
    for _ in range(100):
        mid = math.sqrt(lo * hi)
        if forces(mid)[0] < ned:
            lo = mid
        else:
            hi = mid
    return forces(hi)[1]


def test_strain_matches_simplified_when_tension_controlled():
    """Where the simplified method applies, both agree to a few percent."""
    for med, ned in ((150.0, 0.0), (300.0, 0.0), (150.0, -200.0), (250.0, 300.0)):
        s = calc_asl_nm(B, H, D1, D2, med, ned, FCK, FYK, GC, GS)
        q = calc_asl_nm_strain(B, H, D1, D2, med, ned, FCK, FYK, GC, GS)
        assert abs(q["As1"] - s["As1"]) <= 0.03 * s["As1"] + 1e-6, (med, ned)
        assert q["As2"] == 0.0


def test_strain_design_is_exact_against_independent_fibres():
    """The returned steel carries (N, M) exactly (M_Rd/M_Ed = 1 on the boundary)."""
    for med, ned in ((300.0, 1000.0), (450.0, 1000.0), (450.0, 2000.0),
                     (300.0, 3000.0)):
        q = calc_asl_nm_strain(B, H, D1, D2, med, ned, FCK, FYK, GC, GS)
        assert q["feasible"]
        mrd = _fibre_mrd(q["As1"], q["As2"], ned)
        assert mrd >= med * 0.995, (med, ned, mrd)      # safe
        assert mrd <= med * 1.02, (med, ned, mrd)       # and not wasteful


def test_strain_beats_simplified_in_compression_controlled_range():
    """Small eccentricity + high N: the simplified result is far too heavy."""
    s = calc_asl_nm(B, H, D1, D2, 300.0, 3000.0, FCK, FYK, GC, GS)
    q = calc_asl_nm_strain(B, H, D1, D2, 300.0, 3000.0, FCK, FYK, GC, GS)
    assert s["note"]                                   # simplified flags it
    assert q["As1"] + q["As2"] < 0.7 * (s["As1"] + s["As2"])


def test_auto_uses_simplified_at_low_axial_force_and_strain_above():
    fcd_ac = B * H * FCK / GC * 1000.0                   # kN, nu = 1 reference
    for ned in (-300.0, 0.0, 0.04 * fcd_ac):             # tension, flexure, nu<=0.05
        auto = calc_asl_nm(B, H, D1, D2, 150.0, ned, FCK, FYK, GC, GS, method="auto")
        ref = calc_asl_nm(B, H, D1, D2, 150.0, ned, FCK, FYK, GC, GS)
        assert auto == ref and auto["method"] == "simplified"
    ned = 0.2 * fcd_ac                                   # nu = 0.2
    auto = calc_asl_nm(B, H, D1, D2, 300.0, ned, FCK, FYK, GC, GS, method="auto")
    strain = calc_asl_nm_strain(B, H, D1, D2, 300.0, ned, FCK, FYK, GC, GS)
    assert auto == strain and auto["method"] == "strain"


def test_auto_threshold_is_configurable():
    ned = 0.2 * B * H * FCK / GC * 1000.0
    low = calc_asl_nm(B, H, D1, D2, 300.0, ned, FCK, FYK, GC, GS, method="auto",
                      nu_simplified=0.05)
    high = calc_asl_nm(B, H, D1, D2, 300.0, ned, FCK, FYK, GC, GS, method="auto",
                       nu_simplified=0.5)
    assert low["method"] == "strain" and high["method"] == "simplified"


def test_auto_still_falls_back_when_simplified_flags_low_nu():
    # nu just under the threshold but very small eccentricity: the simplified
    # method flags itself, so auto must not return its As_min answer.
    ned = 0.049 * B * H * FCK / GC * 1000.0
    plain = calc_asl_nm(B, H, D1, D2, 5.0, ned, FCK, FYK, GC, GS)
    auto = calc_asl_nm(B, H, D1, D2, 5.0, ned, FCK, FYK, GC, GS, method="auto")
    if plain["note"]:
        assert auto["method"] == "strain"
    else:
        assert auto["method"] == "simplified"


def test_strain_has_no_neutral_axis_limit():
    """High moment, some compression: strain uses less steel than the
    simplified method, whose x/d <= 0.45 cap forces compression steel."""
    ned = 0.2 * B * H * FCK / GC * 1000.0
    s = calc_asl_nm(B, H, D1, D2, 450.0, ned, FCK, FYK, GC, GS)
    q = calc_asl_nm_strain(B, H, D1, D2, 450.0, ned, FCK, FYK, GC, GS)
    assert q["x_d"] > 0.45 or q["As1"] + q["As2"] <= s["As1"] + s["As2"]


def test_strain_hogging_mirrors_sagging():
    up = calc_asl_nm_strain(B, H, D1, D2, 300.0, 1500.0, FCK, FYK, GC, GS)
    dn = calc_asl_nm_strain(B, H, D1, D2, -300.0, 1500.0, FCK, FYK, GC, GS)
    assert abs(up["As1"] - dn["As1"]) < 1e-9
    assert abs(up["As2"] - dn["As2"]) < 1e-9


def test_strain_flags_section_too_small():
    q = calc_asl_nm_strain(B, H, D1, D2, 300.0, 12000.0, FCK, FYK, GC, GS)
    assert q["note"]                                   # > 4 % Ac or infeasible


def test_bad_method_rejected():
    import pytest
    with pytest.raises(ValueError):
        calc_asl_nm(B, H, D1, D2, 100.0, 0.0, FCK, FYK, GC, GS, method="nope")
