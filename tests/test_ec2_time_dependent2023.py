"""EN 1992-1-1:2023 Annex B (ec2.time_dependent2023) and the simplified Tables 5.2 and 5.3."""
import itertools
import math

import pytest

import eurocodepy as ec
from eurocodepy.ec2 import sls
from eurocodepy.ec2 import time_dependent2023 as td

Y50 = 18250.0       # 50 years in days


def test_the_sls_functions_delegate_and_stay_array_friendly():
    import numpy as np

    t = np.array([100.0, 1000.0, 10000.0])
    a = sls.creep_coef(t, 28.0, 38.0, 50.0, 200.0, 28.0, "CN")
    assert a.shape == (3,) and a == pytest.approx(td.creep_coefficient(t, 28.0, 38.0, 50, 200))
    b = sls.shrink_strain(t + 1, 1.0, 38.0, 50.0, 200.0, "CN", 1.0, 1.0)
    assert b.shape == (3,) and b == pytest.approx(td.shrinkage_total(t + 1, 1.0, 38.0, 50, 200))
    assert sls.shrink_strain(1000.0, 1.0, 38.0, 50.0, 200.0, "CN", 0.5, 0.5) == pytest.approx(
        td.shrinkage_total(1000.0, 1.0, 38.0, 50, 200, alpha_ndp_b=0.5, alpha_ndp_d=0.5))
    # they validate now: what used to give a number outside Annex B, or a silent "CN", raises
    with pytest.raises(ValueError, match="strength development class"):
        sls.creep_coef(1000.0, 28.0, 38.0, 50.0, 200.0, 28.0, "XX")
    with pytest.raises(ValueError, match="20 % ≤ RH"):
        sls.creep_coef(1000.0, 28.0, 38.0, 10.0, 200.0, 28.0, "CN")
    with pytest.raises(ValueError, match="RH"):
        sls.shrink_strain(1000.0, 1.0, 38.0, 10.0, 200.0, "CN", 1.0, 1.0)
    with pytest.raises(ValueError, match="validity of Annex B"):
        sls.shrink_strain(1000.0, 1.0, 5.0, 50.0, 200.0, "CN", 1.0, 1.0)


def test_it_is_the_same_model_as_the_sls_functions():
    for t, t0, fcm, rh, hn, cls in itertools.product(
            [30, 365, 18250], [1, 7, 28, 91], [28, 43, 68, 98], [30, 50, 80, 100],
            [100, 500, 1000], ["CS", "CN", "CR"]):
        if t < t0:
            continue
        assert td.creep_coefficient(t, t0, fcm, rh, hn, cls) == pytest.approx(
            sls.creep_coef(t, t0, fcm, rh, hn, t0, cls), rel=1e-12)
    for t, ts, fcm, rh, hn, cls in itertools.product(
            [10, 365, 18250], [1, 7], [28, 43, 98], [30, 50, 80, 99, 100], [100, 500, 1000],
            ["CS", "CN", "CR"]):
        assert td.shrinkage_total(t, ts, fcm, rh, hn, cls) == pytest.approx(
            sls.shrink_strain(t, ts, fcm, rh, hn, cls, 1.0, 1.0), rel=1e-12)
    # with the temperature-adjusted age at loading
    for t0, t0_t in itertools.product([1, 28, 91], [0.5, 3, 10, 40]):
        assert td.creep_coefficient(Y50, t0, 43, 50, 200, "CN", t0_T=t0_t) == pytest.approx(
            sls.creep_coef(Y50, t0, 43, 50, 200, t0_t, "CN"), rel=1e-12)


def test_the_equations_reproduce_tables_5_2_and_5_3():
    """The tables are the model after 50 years (fck,28 = 35 MPa, fcm = 43): within the rounding."""
    for cls, rh, hn in itertools.product(["CS", "CN", "CR"], [50, 80], [100, 200, 500, 1000]):
        for t0 in ec.dbase.get_edition_params("ec2", "creep_shrinkage", "2023")["creep_50y"]["t0"][cls]:
            if (cls, t0) == ("CR", 1):
                continue        # the table row of t0,adj = 1 day: CR cannot be loaded earlier than 1 day (t0,adj = 4)
            tab = td.creep_coefficient_50y(t0, cls, rh, hn, 35.0)
            assert td.creep_coefficient(t0 + Y50, t0, 43.0, rh, hn, cls) == pytest.approx(
                tab, rel=0.04, abs=0.06), (cls, rh, hn, t0)
    for cls, rh, hn in itertools.product(["CS", "CN", "CR"], [50, 80], [100, 200, 500, 1000]):
        tab = td.shrinkage_50y(cls, rh, hn, 35.0)
        assert td.shrinkage_total(1.0 + Y50, 1.0, 43.0, rh, hn, cls) == pytest.approx(
            tab, rel=0.05, abs=2e-5), (cls, rh, hn)
    # worked numbers (C30/37, CN, RH 50 %, hn 200 mm, loaded at 28 days)
    assert td.creep_coefficient(Y50 + 28, 28, 38.0, 50, 200) == pytest.approx(2.459, abs=1e-3)
    c = td.creep_basic(Y50 + 28, 28, 38.0), td.creep_drying(Y50 + 28, 28, 38.0, 50, 200)
    assert sum(c) == pytest.approx(td.creep_coefficient(Y50 + 28, 28, 38.0, 50, 200))


def test_strength_and_stiffness_development_b4():
    assert td.calc_s_c(30.0, "CN") == 0.5 and td.calc_s_c(35.0, "CN") == 0.5
    assert td.calc_s_c(36.0, "CN") == 0.4 and td.calc_s_c(59.0, "CS") == 0.5
    assert td.calc_s_c(60.0, "CR") == 0.1 and td.calc_s_c(20.0, "CS") == 0.6
    b7 = td.calc_beta_cc(7.0, 30.0, "CN")
    assert b7 == pytest.approx(math.exp(0.5 * (1 - math.sqrt(28 / 7))))        # = exp(-0,5)
    assert td.calc_beta_cc(28.0, 30.0) == 1.0 and td.calc_beta_cc(100.0, 30.0) == 1.0
    assert td.calc_beta_cc(7.0, 30.0, "CR") > b7 > td.calc_beta_cc(7.0, 30.0, "CS")
    assert td.fcm_t(7.0, 38.0, 30.0) == pytest.approx(b7 * 38.0)
    assert td.fctm_t(7.0, 2.9, 30.0) == pytest.approx(b7**0.6 * 2.9)
    assert td.ecm_t(7.0, 31900.0, 30.0) == pytest.approx(b7 ** (1 / 3) * 31900.0)
    # t_ref = 91 days: the reference age is the one of the specified strength
    assert td.calc_beta_cc(28.0, 30.0, "CN", t_ref=91.0) < 1.0
    with pytest.raises(ValueError, match="positive"):
        td.calc_beta_cc(0.0, 30.0)
    with pytest.raises(ValueError, match="strength development class"):
        td.calc_s_c(30.0, "CX")


def test_ages_temperature_and_adjusted_age_b17_b18():
    assert td.temperature_adjusted_age([10.0], [20.0]) == pytest.approx(10.0, rel=0.003)
    assert td.temperature_adjusted_age([10.0], [30.0]) > 10.0 > td.temperature_adjusted_age([10.0], [10.0])
    two = td.temperature_adjusted_age([5.0, 5.0], [20.0, 20.0])
    assert two == pytest.approx(td.temperature_adjusted_age([10.0], [20.0]))
    with pytest.raises(ValueError, match="0 °C ≤ T ≤ 80 °C"):
        td.temperature_adjusted_age([1.0], [90.0])
    with pytest.raises(ValueError, match="same length"):
        td.temperature_adjusted_age([1.0], [])
    assert td.adjusted_loading_age(28.0, "CN") == 28.0                           # αSC = 0
    cs = td.adjusted_loading_age(28.0, "CS")
    cr = td.adjusted_loading_age(28.0, "CR")
    assert cs == pytest.approx(28.0 / (9 / (2 + 28**1.2) + 1)) and cr == pytest.approx(28.0 * (9 / (2 + 28**1.2) + 1))
    assert cs < 28.0 < cr
    assert td.adjusted_loading_age(0.1, "CS") == 0.5                              # ≥ 0,5


def test_creep_components_and_validity():
    bc = td.creep_basic(1000.0, 28.0, 43.0)
    assert bc == pytest.approx(1.8 / 43.0**0.7 * math.log((30 / 28 + 0.035) ** 2 * 972 + 1))
    dc = td.creep_drying(1000.0, 28.0, 43.0, 50.0, 200.0)
    assert dc > 0 and td.creep_drying(1000.0, 28.0, 43.0, 100.0, 200.0) == 0.0   # no drying at RH 100 %
    assert td.creep_coefficient(28.0, 28.0, 43.0, 50, 200) == 0.0                 # no loading time yet
    assert td.creep_coefficient(1e4, 28.0, 43.0, 50, 200) > td.creep_coefficient(1e3, 28.0, 43.0, 50, 200)
    assert td.creep_coefficient(Y50, 28.0, 43.0, 50, 100) > td.creep_coefficient(Y50, 28.0, 43.0, 50, 1000)
    with pytest.raises(ValueError, match="at least 1 day"):
        td.creep_coefficient(100.0, 0.5, 43.0, 50, 200)
    with pytest.raises(ValueError, match="not be less than t0"):
        td.creep_coefficient(10.0, 28.0, 43.0, 50, 200)
    with pytest.raises(ValueError, match="20 % ≤ RH"):
        td.creep_coefficient(1000.0, 28.0, 43.0, 10, 200)
    with pytest.raises(ValueError, match="validity of Annex B"):
        td.creep_coefficient(1000.0, 28.0, 15.0, 50, 200)
    with pytest.raises(TypeError, match="unknown factors"):
        td.creep_coefficient(1000.0, 28.0, 43.0, 50, 200, xi_x=1.0)


def test_nonlinear_creep_characteristic_values_and_creep_strain():
    assert td.creep_nonlinear(2.0, 0.3) == 2.0 and td.creep_nonlinear(2.0, 0.4) == 2.0
    assert td.creep_nonlinear(2.0, 0.5) == pytest.approx(2.0 * math.exp(0.15))
    with pytest.raises(ValueError, match="kσ > 0,6"):
        td.creep_nonlinear(2.0, 0.7)
    assert [td.characteristic_value(2.0, f) for f in ("0.05", "0.10", "0.90", "0.95")] == pytest.approx(
        [1.0, 1.2, 2.8, 3.0])
    with pytest.raises(ValueError, match="fractile"):
        td.characteristic_value(2.0, "0.5")
    assert td.creep_strain(2.0, 10.0, 35000.0) == pytest.approx(2.0 * 10.0 / 35000.0)
    assert td.calc_alpha_c(38.0) == pytest.approx(1.0 / (0.8 + 0.2 * 38 / 88))
    assert td.calc_alpha_c(150.0) == 1.0                                          # ≥ 1,0


def test_creep_function_and_superposition_b40_b41():
    ecm = 33000.0
    j = td.creep_compliance(1000.0, 28.0, 38.0, ecm, 50, 200)
    ac = td.calc_alpha_c(38.0)
    phi = td.creep_coefficient(1000.0, 28.0, 38.0, 50, 200)
    assert j == pytest.approx(1.0 / (ac * ecm) + phi / (ac * ecm))                # t0 = 28: Ec(t0) = Ec(28)
    # a stress step later is loaded when the concrete is stiffer: J is smaller, the elastic part larger
    assert td.creep_compliance(1000.0, 7.0, 38.0, ecm, 50, 200) > j
    eps = td.strain_history(1000.0, [(28.0, 10.0)], 38.0, ecm, 50, 200)
    assert eps == pytest.approx(10.0 * j)
    two = td.strain_history(1000.0, [(28.0, 10.0), (90.0, 4.0)], 38.0, ecm, 50, 200)
    assert two == pytest.approx(10.0 * j + 4.0 * td.creep_compliance(1000.0, 90.0, 38.0, ecm, 50, 200))


def test_shrinkage_components_b23_to_b33():
    fcm = 43.0
    cbs = td.shrinkage_basic(10000.0, fcm, "CN")
    assert cbs == pytest.approx(700 * (fcm / (60 + fcm)) ** 2.5 * 1e-6 * (1 - math.exp(-0.2 * 100.0)))
    assert td.shrinkage_basic(10000.0, fcm, "CS") > td.shrinkage_basic(10000.0, fcm, "CR")   # 800 vs 600
    assert td.rh_eq(35.0 + 8) == pytest.approx(99 * (35 / 43) ** 0.1) and td.rh_eq(20.0) == 99.0
    eq = td.rh_eq(fcm)
    assert td.calc_beta_rh(50.0, fcm) == pytest.approx(1.55 * (1 - (50 / eq) ** 3))          # (B.29)
    assert td.calc_beta_rh(98.5, fcm) == pytest.approx(1.55 * (1 - (98.5 / eq) ** 2))        # (B.30)
    assert td.calc_beta_rh(100.0, fcm) == pytest.approx(1.55 * (1 - (100 / eq) ** 2) - 0.25)  # (B.31)
    d = td.shrinkage_drying(1000.0, 1.0, fcm, 50.0, 200.0, "CN")
    assert d == pytest.approx((220 + 440) * math.exp(-0.012 * fcm) * 1e-6 * td.calc_beta_rh(50.0, fcm)
                              * math.sqrt(999.0 / (0.035 * 200**2 + 999.0)))
    assert td.shrinkage_total(1000.0, 1.0, fcm, 50.0, 200.0) == pytest.approx(
        td.shrinkage_basic(1000.0, fcm) + d)
    # αNDP and the characteristic values
    assert td.shrinkage_total(1000.0, 1.0, fcm, 50.0, 200.0, alpha_ndp_b=0.0, alpha_ndp_d=0.5) == pytest.approx(d * 0.5)
    assert td.characteristic_value(td.shrinkage_total(1000.0, 1.0, fcm, 50, 200), "0.95") == pytest.approx(
        1.5 * td.shrinkage_total(1000.0, 1.0, fcm, 50, 200))
    with pytest.raises(ValueError, match="ts"):
        td.shrinkage_total(1.0, 10.0, fcm, 50.0, 200.0)


def test_test_calibration_factors_b7():
    base = td.creep_coefficient(5000.0, 28.0, 43.0, 50, 200)
    assert td.creep_coefficient(5000.0, 28.0, 43.0, 50, 200, xi_bc1=1.2, xi_dc1=1.2) == pytest.approx(1.2 * base)
    slower = td.creep_coefficient(5000.0, 28.0, 43.0, 50, 200, xi_bc2=2.0, xi_dc2=2.0)
    assert slower < base                                                          # slower time development
    assert td.shrinkage_total(5000.0, 1.0, 43.0, 50, 200, xi_bs1=1.5, xi_ds1=1.5) == pytest.approx(
        1.5 * td.shrinkage_total(5000.0, 1.0, 43.0, 50, 200))
    assert td.shrinkage_total(5000.0, 1.0, 43.0, 50, 200, xi_bs2=2.0, xi_ds2=2.0) != pytest.approx(
        td.shrinkage_total(5000.0, 1.0, 43.0, 50, 200))
    assert td.shrinkage_basic(100.0, 43.0, "CN", xi_bs2=2.0) > td.shrinkage_basic(100.0, 43.0, "CN")


def test_tables_5_2_and_5_3_lookup_and_interpolation():
    # grid values: C35, CN, loaded at 28 days (CN row 3), RH 50 %, hn 200 -> 2.2; humid 1.6
    assert td.creep_coefficient_50y(28, "CN", 50, 200, 35.0) == pytest.approx(2.2)
    assert td.creep_coefficient_50y(28, "CN", 80, 200, 35.0) == pytest.approx(1.6)
    assert td.creep_coefficient_50y(1, "CN", 50, 100, 35.0) == pytest.approx(4.2)
    assert td.creep_coefficient_50y(3, "CS", 50, 1000, 35.0) == pytest.approx(3.1)
    assert td.creep_coefficient_50y(23, "CR", 80, 500, 35.0) == pytest.approx(1.6)
    # the strength factor (35/fck)^A, A = 0,79 (dry, hn = 200)
    assert td.creep_coefficient_50y(28, "CN", 50, 200, 50.0) == pytest.approx(2.2 * (35 / 50) ** 0.79)
    assert td.creep_coefficient_50y(28, "CN", 50, 200, 20.0) == pytest.approx(2.2 * (35 / 20) ** 0.79)
    # interpolation in hn (linear) and t0 (logarithmic)
    mid = td.creep_coefficient_50y(28, "CN", 50, 350, 35.0)
    assert mid == pytest.approx(0.5 * (2.2 + 1.9))
    lo, hi = td.creep_coefficient_50y(7, "CN", 50, 200, 35.0), td.creep_coefficient_50y(28, "CN", 50, 200, 35.0)
    assert td.creep_coefficient_50y(14, "CN", 50, 200, 35.0) == pytest.approx(
        lo + (math.log(2) / math.log(4)) * (hi - lo))
    # shrinkage, Table 5.3: CN, fck 35, RH 50 %, hn 200 -> 0,59 ‰
    assert td.shrinkage_50y("CN", 50, 200, 35.0) == pytest.approx(0.59e-3)
    assert td.shrinkage_50y("CS", 80, 1000, 20.0) == pytest.approx(0.21e-3)
    assert td.shrinkage_50y("CR", 50, 100, 80.0) == pytest.approx(0.55e-3)
    assert td.shrinkage_50y("CN", 50, 200, 42.5) == pytest.approx(0.5 * (0.59 + 0.54) * 1e-3)
    for args, msg in [((28, "CN", 65, 200, 35.0), "RH = 50"), ((28, "CN", 50, 50, 35.0), "hn = 50"),
                      ((0.5, "CN", 50, 200, 35.0), "t0 = 0.5"), ((28, "CN", 50, 200, 120.0), "fck"),
                      ((28, "CX", 50, 200, 35.0), "class")]:
        with pytest.raises(ValueError, match=msg):
            td.creep_coefficient_50y(*args)
    with pytest.raises(ValueError, match="fck = 90"):
        td.shrinkage_50y("CS", 50, 200, 90.0)                                    # CS only up to C50


def test_table_5_3_is_an_ndp_the_annex_can_patch():
    ec.register_annex({"country": "XB", "editions": {"ec2": {"2023": {"creep_shrinkage": {
        "shrinkage_50y": {"CN": {"dry": [[0.5, 0.5, 0.5, 0.5]] * 4}}}}}}})
    try:
        assert td.shrinkage_50y("CN", 50, 200, 35.0, annex="XB") == pytest.approx(0.5e-3)
        assert td.shrinkage_50y("CN", 80, 200, 35.0, annex="XB") == pytest.approx(0.34e-3)   # humid untouched
        assert td.shrinkage_50y("CN", 50, 200, 35.0) == pytest.approx(0.59e-3)
    finally:
        ec.unregister_annex("XB")


def test_relaxation_b9():
    assert td.relaxation_rho1000(0.7, "wire") == 2.5 and td.relaxation_rho1000(0.8, "wire") == 4.5
    assert td.relaxation_rho1000(0.5, "wire") == 0.0
    assert td.relaxation_rho1000(0.75, "wire") == pytest.approx(3.5)              # linear interpolation
    assert td.relaxation_rho1000(0.7, "bar", 12.0) == 6.0 and td.relaxation_rho1000(0.7, "bar", 20.0) == 4.0
    assert td.relaxation_rho1000(0.6, "bar", 12.0) == pytest.approx(3.0)
    with pytest.raises(ValueError, match="outside 0.5-0.7"):
        td.relaxation_rho1000(0.75, "bar", 12.0)                                  # bars: no value at 80 %
    with pytest.raises(ValueError, match="outside"):
        td.relaxation_rho1000(0.85, "wire")
    with pytest.raises(ValueError, match="kind"):
        td.relaxation_rho1000(0.7, "tendon")
    # Eq. (B.43): after 1000 h the loss is ρ1000, then (24 t/1000)^0,16
    assert td.relaxation_loss(1000 / 24, 1000.0, 2.5) == pytest.approx(25.0)
    assert td.relaxation_loss(Y50, 1000.0, 2.5) == pytest.approx(25.0 * (24 * Y50 / 1000) ** 0.16)
    assert td.relaxation_loss(Y50, 1000.0, 2.5, k_rho=0.2) > td.relaxation_loss(Y50, 1000.0, 2.5)
    assert td.relaxation_loss_fit(100.0, 1000.0, 0.16, 0.01) == pytest.approx(1000.0 * 0.01 * 100.0**0.16)


def test_the_module_is_exported_and_the_2004_functions_are_unchanged():
    from eurocodepy.ec2 import CreepParams, calc_creep_coef, time_dependent2023

    assert time_dependent2023 is td
    p = CreepParams(t=18250, h0=200, rh=50, t0=28, fck=30.0, cem=0.0)
    assert calc_creep_coef(p) != pytest.approx(td.creep_coefficient(18250, 28, 38.0, 50, 200), rel=1e-3)


def test_the_functions_accept_arrays_and_broadcast():
    import numpy as np

    t = np.array([100.0, 1000.0, 10000.0, Y50 + 28])
    phi = td.creep_coefficient(t, 28.0, 38.0, 50, 200)
    assert phi.shape == (4,) and np.all(np.diff(phi) > 0)
    assert phi == pytest.approx([td.creep_coefficient(float(x), 28.0, 38.0, 50, 200) for x in t])
    assert td.creep_basic(t, 28.0, 38.0).shape == (4,) and td.creep_drying(t, 28.0, 38.0, 50, 200).shape == (4,)
    # broadcasting: ages x humidities, notional sizes, strengths
    grid = td.creep_coefficient(t[:, None], 28.0, 38.0, np.array([40.0, 60.0, 80.0]), 200)
    assert grid.shape == (4, 3) and np.all(grid[:, 0] > grid[:, 2])
    assert td.creep_coefficient(Y50 + 28, 28.0, 38.0, 50, np.array([100.0, 500.0])).shape == (2,)
    assert td.creep_coefficient(Y50 + 28, np.array([7.0, 28.0, 91.0]), 38.0, 50, 200).shape == (3,)
    eps = td.shrinkage_total(t + 1, 1.0, 38.0, 50, 200)
    assert eps.shape == (4,) and eps == pytest.approx([td.shrinkage_total(float(x) + 1, 1.0, 38.0, 50, 200) for x in t])
    assert td.shrinkage_basic(t, 38.0).shape == (4,) and td.shrinkage_drying(t + 1, 1.0, 38.0, 50, 200).shape == (4,)
    assert td.calc_beta_rh(np.array([30.0, 50.0, 98.5, 100.0]), 43.0).shape == (4,)
    assert td.calc_beta_rh(np.array([30.0, 50.0, 98.5, 100.0]), 43.0) == pytest.approx(
        [td.calc_beta_rh(r, 43.0) for r in (30.0, 50.0, 98.5, 100.0)])
    ages = np.array([3.0, 7.0, 14.0, 28.0, 60.0])
    b = td.calc_beta_cc(ages, 30.0, "CN")
    assert b.shape == (5,) and b[-1] == 1.0 and np.all(np.diff(b) >= 0)
    assert td.fcm_t(ages, 38.0, 30.0).shape == (5,) and td.ecm_t(ages, 33000.0, 30.0).shape == (5,)
    assert td.adjusted_loading_age(np.array([1.0, 28.0]), "CS").shape == (2,)
    assert td.creep_nonlinear(2.0, np.array([0.3, 0.5, 0.6])) == pytest.approx(
        [2.0, 2.0 * math.exp(0.15), 2.0 * math.exp(0.3)])
    assert td.relaxation_loss(np.array([10.0, 100.0]), 1000.0, 2.5).shape == (2,)
    assert td.creep_compliance(t, 28.0, 38.0, 33000.0, 50, 200).shape == (4,)
    assert td.strain_history(t, [(28.0, 10.0), (90.0, 4.0)], 38.0, 33000.0, 50, 200).shape == (4,)
    # a scalar in gives a plain number out
    assert isinstance(td.creep_coefficient(1000.0, 28.0, 38.0, 50, 200), float)
    # a single invalid element refuses the whole array
    with pytest.raises(ValueError, match="20 % ≤ RH"):
        td.creep_coefficient(1000.0, 28.0, 38.0, np.array([50.0, 10.0]), 200)
    with pytest.raises(ValueError, match="not be less than t0"):
        td.creep_coefficient(np.array([1000.0, 10.0]), 28.0, 38.0, 50, 200)
    with pytest.raises(ValueError, match="validity of Annex B"):
        td.shrinkage_basic(100.0, np.array([38.0, 200.0]))
