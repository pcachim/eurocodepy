"""Column design comes in two EC2 editions with the same function names:
``ec2.uls`` is EN 1992-1-1:2004 and ``ec2.uls2023`` is EN 1992-1-1:2023
(mirrors the pattern already used for punching shear, see
``test_ec2_punch_editions.py``).

Unlike punching, the 2023 column module currently overrides **nothing** --
see ``ec2/uls2023/column.py``'s own docstring for why (no confirmed primary
source for the revised coefficients yet). This test suite is the guard
mentioned in ``dev/RC_COLUMN_DESIGN.md`` §3.3: it fails the day someone
overrides a 2023 column function without a matching, deliberate update here,
so a silent, undocumented divergence between the two editions cannot happen
unnoticed.

Run on Python >= 3.11 with eurocodepy importable.
"""
import pytest

from eurocodepy.ec2 import uls, uls2023
from eurocodepy.ec2.materials import get_concrete, get_reinforcement
from eurocodepy.utils.crosssection import RectangularCrossSection


def _make_input(module):
    conc = get_concrete("C30/37")
    reinf = get_reinforcement("B500B")
    section = RectangularCrossSection(width=0.30, height=0.30)
    cover = 0.04
    rebar = module.RebarLayout.symmetric_rectangular(section, cover, 8, 16.0)
    return module.ColumnInput(
        section=section, concrete=conc, reinforcement=reinf, rebar=rebar,
        cover_m=cover, length_m=3.0, k_y=1.0, k_z=1.0,
        m02_y=15.0, m02_z=10.0, phi_ef=2.0, n_ed=800.0, my_ed=5.0, mz_ed=3.0,
    )


def test_uls2023_column_is_currently_identical_to_uls():
    # As long as ec2/uls2023/column.py overrides nothing, every symbol must
    # be the *same object* as its 2004 counterpart (not just numerically
    # equal) -- this is what "inherited via import *" means.
    assert uls2023.eurocode2_column_check is uls.eurocode2_column_check
    assert uls2023.slenderness_limit is uls.slenderness_limit
    assert uls2023.biaxial_interaction_exponent is uls.biaxial_interaction_exponent
    assert uls2023.nominal_curvature_e2 is uls.nominal_curvature_e2
    assert uls2023.nominal_stiffness_moment is uls.nominal_stiffness_moment
    assert uls2023.uniaxial_moment_resistance is uls.uniaxial_moment_resistance
    assert uls2023.ColumnInput is uls.ColumnInput
    assert uls2023.ColumnResult is uls.ColumnResult
    assert uls2023.RebarLayout is uls.RebarLayout


def test_uls2023_column_gives_identical_numeric_result():
    # Belt-and-braces: even if a future change made the objects distinct
    # without updating this file, the *numbers* would still have to match
    # today's expectations (2004 == 2023, nothing overridden yet).
    inp_04 = _make_input(uls)
    inp_23 = _make_input(uls2023)
    res_04 = uls.eurocode2_column_check(inp_04)
    res_23 = uls2023.eurocode2_column_check(inp_23)
    assert res_23.utilization == pytest.approx(res_04.utilization)
    assert res_23.mrd_y == pytest.approx(res_04.mrd_y)
    assert res_23.mrd_z == pytest.approx(res_04.mrd_z)
    assert res_23.lambda_lim_y == pytest.approx(res_04.lambda_lim_y)
    assert res_23.passed == res_04.passed
