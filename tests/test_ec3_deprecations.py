"""The legacy ``ec3.uls.checks`` / ``ec3.uls.bending`` modules are deprecated in
favour of ``cross_section`` and ``member_buckling``; they still work but warn.

Run on Python >= 3.11 with eurocodepy importable.
"""
import importlib
import sys
import warnings

import pytest

from eurocodepy.ec3 import uls


def test_combined_check_warns_and_points_to_cross_section():
    with pytest.warns(DeprecationWarning, match="cross_section"):
        uls.eurocode3_combined_check(
            N_Ed=100.0, M_Ed=50.0, V_Ed=20.0, area=5000.0,
            area_v=2500.0, W_el=5.0e5, fy=275.0)


def test_buckling_check_warns_and_points_to_member_buckling():
    params = uls.BucklingParameters(A=5000.0, fy=275.0, L_cr=4000.0, i=125.0)
    with pytest.warns(DeprecationWarning, match="member_buckling"):
        uls.eurocode3_buckling_check(N_Ed=300.0, params=params)


def test_ltb_check_warns():
    with pytest.warns(DeprecationWarning):
        uls.check_ltb_resistance(
            f_y=275e6, E=210e9, G=81e9, gamma_M1=1.0,
            I_y=8.356e-5, I_z=6.038e-6, W_el_z=8.05e-5,
            I_w=1.2426e-7, I_t=1.975e-7, L=4.0, M_Ed=100e3)


def test_bending_module_import_warns():
    sys.modules.pop("eurocodepy.ec3.uls.bending", None)
    with pytest.warns(DeprecationWarning, match="member_buckling"):
        importlib.import_module("eurocodepy.ec3.uls.bending")


def test_calc_ncr_reexport_still_works_without_warning():
    # calc_Ncr moved to member_buckling but is re-exported from checks with no
    # deprecation (it is a plain helper, not a deprecated check).
    from eurocodepy.ec3.uls.checks import calc_Ncr as calc_from_checks
    with warnings.catch_warnings():
        warnings.simplefilter("error")           # any warning would fail here
        val = calc_from_checks(210000.0, 8.356e7, 4000.0, 1.0)
    assert val == pytest.approx(uls.calc_Ncr(210000.0, 8.356e7, 4000.0, 1.0))
