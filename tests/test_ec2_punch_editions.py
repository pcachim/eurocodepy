"""Punching shear comes in two EC2 editions with the same function names:
``ec2.uls`` is EN 1992-1-1:2004 and ``ec2.uls2023`` is prEN 1992-1-1:2023.
``uls2023`` mirrors ``uls`` and overrides only the punching functions.

Run on Python >= 3.11 with eurocodepy importable.
"""
import math

import pytest

from eurocodepy.ec2 import uls, uls2023

# ── the two editions are distinct, but share everything else ────────────────


def test_uls_and_uls2023_punch_are_distinct():
    assert uls.calc_vrdcp is not uls2023.calc_vrdcp
    assert uls.calc_vedp is not uls2023.calc_vedp
    assert uls.punch is not uls2023.punch


def test_uls2023_reexports_the_shared_2004_checks():
    # Non-punching checks have no 2023 version yet → same shared functions.
    assert uls2023.calc_vrd is uls.calc_vrd
    assert uls2023.calc_asws is uls.calc_asws
    assert uls2023.calc_torsion is uls.calc_torsion


# ── EN 1992-1-1:2004 punching (hand-checked) ────────────────────────────────

def test_punch_2004_perimeters_at_2d():
    u0, u1, _bb = uls.calc_perimeters(200.0, 300.0, 300.0)  # d, cx, cy
    assert u0 == pytest.approx(1200.0)                       # 2·(cx+cy)
    assert u1 == pytest.approx(1200.0 + 2.0 * math.pi * 400.0, rel=1e-6)


def test_punch_2004_resistance_and_stress():
    ved = uls.calc_vedp(500.0, 0.0, 0.0, 200.0, 300.0, 300.0)   # VEd, Mx, My
    assert ved == pytest.approx(0.673, abs=3e-3)
    vrdc = uls.calc_vrdcp(0.01, 30.0, 200.0)                    # ρl, fck, d
    assert vrdc == pytest.approx(0.746, abs=3e-3)
    assert uls.calc_vrdcminp(30.0, 200.0) == pytest.approx(0.542, abs=3e-3)


def test_punch_2004_moment_raises_beta():
    v_no_m = uls.calc_vedp(500.0, 0.0, 0.0, 200.0, 300.0, 300.0)
    v_with_m = uls.calc_vedp(500.0, 60.0, 0.0, 200.0, 300.0, 300.0)
    assert v_with_m > v_no_m                                    # β > 1


# ── the two editions give different numbers ─────────────────────────────────

def test_editions_give_different_resistance():
    v04 = uls.calc_vrdcp(0.01, 30.0, 200.0)
    v23 = uls2023.calc_vrdcp(20.0, 0.01, 30.0, 200.0, 300.0, 300.0,
                             gamma_v=1.4)
    assert not math.isclose(float(v04), float(v23), rel_tol=1e-3)
