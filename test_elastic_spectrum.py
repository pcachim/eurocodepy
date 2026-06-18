"""Tests for the EN 1998-1 elastic response spectrum Se(T) added to ec8.spectrum.

Run on Python >= 3.11 with eurocodepy importable:
    python test_elastic_spectrum.py
or:
    pytest test_elastic_spectrum.py
"""
import math

from eurocodepy.ec8.spectrum import (
    calc_elastic_spectrum,
    damping_correction,
    get_elastic_spectrum_user,
)

AG, S, TB, TC, TD = 2.0, 1.2, 0.15, 0.5, 2.0


def _se_ref(T, xi=5.0):
    eta = max(math.sqrt(10.0 / (5.0 + xi)), 0.55)
    ag_s = AG * S
    if T < TB:
        return ag_s * (1.0 + T / TB * (eta * 2.5 - 1.0))
    if T < TC:
        return ag_s * eta * 2.5
    if T < TD:
        return ag_s * eta * 2.5 * (TC / T)
    return ag_s * eta * 2.5 * (TC * TD / T ** 2)


def test_damping_correction():
    assert abs(damping_correction(5.0) - 1.0) < 1e-12        # eta = 1 at 5%
    assert abs(damping_correction(100.0) - 0.55) < 1e-12     # floored at 0.55


def test_plateau_value():
    # TB <= T <= TC plateau equals ag*S*eta*2.5 (= ag*S*2.5 at 5% damping).
    assert abs(calc_elastic_spectrum(0.3, AG, S, TB, TC, TD) - AG * S * 2.5) < 1e-9


def test_value_at_T0_is_agS():
    assert abs(calc_elastic_spectrum(0.0, AG, S, TB, TC, TD) - AG * S) < 1e-9


def test_matches_closed_form_across_branches():
    for T in (0.0, 0.1, TB, 0.3, TC, 1.0, TD, 3.0):
        got = calc_elastic_spectrum(T, AG, S, TB, TC, TD)
        assert abs(got - _se_ref(T)) < 1e-9, f"mismatch at T={T}"


def test_descending_beyond_tc_is_monotonic():
    Ts = [0.6, 1.0, 1.5, 2.5, 3.5]
    vals = [calc_elastic_spectrum(T, AG, S, TB, TC, TD) for T in Ts]
    assert all(a >= b - 1e-12 for a, b in zip(vals, vals[1:]))


def test_dataframe_helper():
    df = get_elastic_spectrum_user(AG, S, TB, TC, TD, damping=5.0, t_max=4.0)
    assert list(df.columns) == ["period", "value"]
    assert len(df) > 0
    # First row is T=0 → Se = ag*S.
    assert abs(df["value"].iloc[0] - AG * S) < 1e-9


if __name__ == "__main__":
    test_damping_correction()
    test_plateau_value()
    test_value_at_T0_is_agS()
    test_matches_closed_form_across_branches()
    test_descending_beyond_tc_is_monotonic()
    test_dataframe_helper()
    print("OK — elastic spectrum checks passed")
