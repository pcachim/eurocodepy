"""ec2.uls2023.shear_torsion and torsion are the EN 1992-1-1:2023 ones (8.2, 8.3, 8.3.6).

What stays shared with 2004: the result object and the distribution of the
longitudinal torsion steel round the wall.
"""
import pytest

from eurocodepy.ec2 import uls as uls2004
from eurocodepy.ec2 import uls2023


def test_shared_and_distinct_symbols():
    assert uls2023.ShearTorsionResult is uls2004.ShearTorsionResult
    assert uls2023.distribute_torsion_longitudinal is uls2004.distribute_torsion_longitudinal
    assert uls2023.eurocode2_shear_torsion_check is not uls2004.eurocode2_shear_torsion_check
    assert uls2023.ShearTorsionInput is not uls2004.ShearTorsionInput
    assert uls2023.calc_torsion is not uls2004.calc_torsion
    assert uls2023.torsion.__name__ == "eurocodepy.ec2.uls2023.torsion"
    assert uls2023.shear_torsion.__name__ == "eurocodepy.ec2.uls2023.shear_torsion"


def test_submodule_all_matches_uls_all():
    assert set(uls2023.shear_torsion.__all__) == set(uls2004.shear_torsion.__all__)


def test_2023_check_differs_from_2004_and_keeps_the_2004_interface():
    kw = {"b": 0.30, "h": 0.50, "cover": 0.05, "fck": 30.0, "fyk": 500.0,
          "gamma_c": 1.5, "gamma_s": 1.15, "alpha_cc": 1.0, "as_long": 8e-4}
    r2004 = uls2004.eurocode2_shear_torsion_check(uls2004.ShearTorsionInput(**kw), 120.0, 30.0)
    r2023 = uls2023.eurocode2_shear_torsion_check(uls2023.ShearTorsionInput(**kw), 120.0, 30.0)
    assert r2023.interaction != pytest.approx(r2004.interaction)
    assert r2023.asw_total_s > 0.0
    # same fields; the 2004 call signature still works for the 2023 input
    assert set(vars(r2023)) == set(vars(r2004))
