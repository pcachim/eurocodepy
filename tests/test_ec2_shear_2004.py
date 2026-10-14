"""EN 1992-1-1:2004, 6.2.3: VRd = min(VRd,s, VRd,max) and its inverse."""
import pytest

from eurocodepy.ec2.uls.shear import calc_asws, calc_vrd, calc_vrdmax

ARGS = (0.3, 0.46, 30.0, 1.5, 500.0, 1.15, 2.0)      # bw [m], d [m], fck, gamma_c, fyk, gamma_s, cot


def test_vrd_is_the_smaller_of_stirrups_and_strut():
    vrd_max = calc_vrdmax(0.3, 0.46, 30.0, 1.5, 2.0)
    light = calc_vrd(*ARGS, 5e-4)                    # few stirrups: VRd,s governs
    heavy = calc_vrd(*ARGS, 5e-3)                    # many stirrups: the strut governs
    assert light == pytest.approx(5e-4 * 0.9 * 0.46 * 500 / 1.15 * 2.0 * 1000.0)
    assert light < vrd_max
    assert heavy == pytest.approx(vrd_max)


def test_asws_and_vrd_are_consistent():
    asw_s, vrd_max = calc_asws(*ARGS, 150.0)
    assert vrd_max >= 150.0
    assert calc_vrd(*ARGS, asw_s) == pytest.approx(150.0)
