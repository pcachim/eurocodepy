"""Regression tests for the populated ``Editions.ec2.2023`` overrides.

Values and clause references come from EN 1992-1-1:2023 (E), Clause 5
(Materials): Table 5.1 (concrete strength classes, incl. the new C100/115
class), Eq. (5.1) (Ecm = kE . fcm^(1/3), kE = 9500 for quartzite aggregates),
Eq. (5.3)-(5.5) (fcd/fctd design assumptions: fck_ref, k_tc, k_tt), and
5.2.4(4)/5.3.3(3)-(4) (unit weight of reinforcing/prestressing steel, 78.5
kN/m3; Es/Ep design defaults, 200000 MPa).

These tests lock in the *current* state of the overrides so a future,
unrelated change to dbase.py or eurocodes.json cannot silently alter the
resolved 2023 values without the test failing.
"""
import math

from eurocodepy import dbase


def test_ec2_2023_is_registered_and_not_default():
    editions = dbase.db["Editions"]["ec2"]
    assert editions["2004"]["default"] is True
    assert editions["2023"]["default"] is False


def test_ec2_2023_concrete_grade_ecm_uses_kE_quartzite_formula():
    d2023 = dbase.get_edition_data("ec2", "2023")
    kE = 9500.0
    for grade, fcm in {
        "C20_25": 28.0, "C30_37": 38.0, "C90_105": 98.0,
    }.items():
        expected = round(kE * fcm ** (1.0 / 3.0), 1)
        assert d2023["Concrete"]["Grade"][grade]["Ecm"] == expected
        # sibling fields (fck, fctm, ...) must survive the Ecm-only override
        assert d2023["Concrete"]["Grade"][grade]["fck"] == \
            dbase.ConcreteGrades[grade]["fck"]


def test_ec2_2023_adds_c100_115_grade_not_present_in_2004():
    assert "C100_115" not in dbase.ConcreteGrades
    d2023 = dbase.get_edition_data("ec2", "2023")
    g = d2023["Concrete"]["Grade"]["C100_115"]
    assert g["fck"] == 100.0
    assert g["fcm"] == 108.0


def test_ec2_2023_fcd_fctd_scalar_overrides():
    d2023 = dbase.get_edition_data("ec2", "2023")
    params = d2023["Concrete"]["Parameters"]
    assert params["fck_ref"] == 40.0
    assert params["k_tc"]["short_loading"] == 1.0
    assert params["k_tc"]["other"] == 0.85
    assert params["k_tt"]["short_loading"] == 0.8
    assert params["k_tt"]["other"] == 0.7
    # gamma_cc etc. from the 2004 base are untouched siblings
    assert params["gamma_cc"] == dbase.ConcreteParams["gamma_cc"]


def test_ec2_2023_reinforcement_and_prestress_unit_weight_and_modulus():
    d2023 = dbase.get_edition_data("ec2", "2023")
    assert d2023["Reinforcement"]["Parameters"]["weigh"] == 78.5
    assert d2023["Reinforcement"]["Parameters"]["Es"] == 200000.0
    assert d2023["Prestress"]["Parameters"]["weigh"] == 78.5
    assert d2023["Prestress"]["Parameters"]["Ep"] == 200000.0
    # the 2004 base values are untouched
    assert dbase.ReinforcementParams["weigh"] == 77.0
    assert dbase.PrestressParams["weigh"] == 77.0


def test_2004_base_materials_are_fully_unaffected():
    # Sanity: resolving "2004" explicitly, or omitting the edition, must
    # still equal the untouched base Materials dict exactly.
    assert dbase.get_edition_data("ec2", "2004") == dbase.Materials
    assert dbase.get_edition_data("ec2") == dbase.Materials
