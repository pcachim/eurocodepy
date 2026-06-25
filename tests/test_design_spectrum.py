"""Tests for the EN 1998-1 design response spectrum (ec8.spectrum.calc_spectrum).

Run on Python >= 3.11 with eurocodepy importable:
    python tests/test_design_spectrum.py
or:
    pytest tests/test_design_spectrum.py
"""
from eurocodepy.ec8.spectrum import calc_spectrum

AG, S, Q, TB, TC, TD, BETA = 2.0, 1.2, 3.0, 0.15, 0.5, 2.0, 0.2


def _sd(T):
    return calc_spectrum(T, AG, S, Q, TB, TC, TD, BETA)


def test_plateau_uses_behaviour_factor():
    # TB <= T <= TC plateau = ag*S*2.5/q.
    assert abs(_sd(0.3) - AG * S * 2.5 / Q) < 1e-9


def test_value_at_T0():
    # Sd(0) = ag*S*(2/3).
    assert abs(_sd(0.0) - AG * S * 2.0 / 3.0) < 1e-9


def test_lower_bound_is_beta_ag_not_beta_ag_s():
    # EN 1998-1 eq. 3.15/3.16: the floor is beta*ag (NO soil factor S).
    floor = BETA * AG
    # At a long period the unbounded value is tiny, so the floor governs.
    assert abs(_sd(4.0) - floor) < 1e-9
    # And it must never dip below the floor.
    for T in (0.0, TB, TC, TD, 1.0, 3.0, 4.0):
        assert _sd(T) >= floor - 1e-12


if __name__ == "__main__":
    test_plateau_uses_behaviour_factor()
    test_value_at_T0()
    test_lower_bound_is_beta_ag_not_beta_ag_s()
    print("OK — design spectrum checks passed")
