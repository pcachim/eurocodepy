"""Phase 4 (dev/GRILLAGE_DESIGN.md sec 6.4): ec2.uls2023.shear_torsion parity.

The EN 1992-1-1:2023 strut-crushing coefficients for shear+torsion have
not been confirmed against the approved text (see the module's own
docstring), so uls2023.shear_torsion is currently a pure re-export of the
2004 module -- these tests pin that down explicitly so a future, silent
divergence (someone editing one module and forgetting the other) shows up
as a real regression instead of shipping unnoticed.
"""
from eurocodepy.ec2 import uls as uls2004
from eurocodepy.ec2 import uls2023


def test_shear_torsion_symbols_are_the_same_objects():
    # A pure re-export (no override yet) must point at the identical
    # functions/classes, not merely equal-looking copies.
    assert uls2023.eurocode2_shear_torsion_check is uls2004.eurocode2_shear_torsion_check
    assert uls2023.ShearTorsionInput is uls2004.ShearTorsionInput
    assert uls2023.ShearTorsionResult is uls2004.ShearTorsionResult
    assert uls2023.distribute_torsion_longitudinal is uls2004.distribute_torsion_longitudinal


def test_shear_torsion_check_gives_identical_numbers_in_both_editions():
    inp = uls2004.ShearTorsionInput(b=0.30, h=0.50, cover=0.05, fck=30.0, fyk=500.0,
                                     gamma_c=1.5, gamma_s=1.15, alpha_cc=1.0,
                                     as_long=8e-4)
    r2004 = uls2004.eurocode2_shear_torsion_check(inp, v_ed=120.0, t_ed=30.0)
    r2023 = uls2023.eurocode2_shear_torsion_check(inp, v_ed=120.0, t_ed=30.0)

    assert r2023.asw_total_s == r2004.asw_total_s
    assert r2023.asl_tor_total == r2004.asl_tor_total
    assert r2023.interaction == r2004.interaction
    assert r2023.cot == r2004.cot


def test_shear_torsion_submodule_all_matches_uls_all():
    assert set(uls2023.shear_torsion.__all__) == set(uls2004.shear_torsion.__all__)
