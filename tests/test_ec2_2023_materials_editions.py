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
import pytest

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
    assert params["k_tc"]["late_loading"] == 1.0
    assert params["k_tc"]["other"] == 0.85
    assert params["k_tt"]["late_loading"] == 0.8
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


# ── Table 5.1 and 8.1.2 of EN 1992-1-1:2023 in the grades ────────────────────

TABLE_5_1 = {   # grade: (fck, fcm, fctm, fctk,0.05, fctk,0.95)
    "C12_15": (12, 20, 1.6, 1.1, 2.0), "C16_20": (16, 24, 1.9, 1.3, 2.5), "C20_25": (20, 28, 2.2, 1.5, 2.9),
    "C25_30": (25, 33, 2.6, 1.8, 3.3), "C30_37": (30, 38, 2.9, 2.0, 3.8), "C35_45": (35, 43, 3.2, 2.2, 4.2),
    "C40_50": (40, 48, 3.5, 2.5, 4.6), "C45_55": (45, 53, 3.8, 2.7, 4.9), "C50_60": (50, 58, 4.1, 2.9, 5.3),
    "C55_67": (55, 63, 4.2, 2.9, 5.4), "C60_75": (60, 68, 4.3, 3.0, 5.6), "C70_85": (70, 78, 4.5, 3.2, 5.9),
    "C80_95": (80, 88, 4.7, 3.3, 6.2), "C90_105": (90, 98, 4.9, 3.5, 6.4), "C100_115": (100, 108, 5.1, 3.6, 6.6),
}


def test_2023_grades_are_table_5_1():
    import pytest

    from eurocodepy.ec2 import Concrete

    d2023 = dbase.get_edition_data("ec2", "2023")["Concrete"]["Grade"]
    assert set(d2023) == set(TABLE_5_1)
    for grade, (fck, fcm, fctm, fctk05, fctk95) in TABLE_5_1.items():
        g = d2023[grade]
        assert (g["fck"], g["fcm"], g["fctm"], g["fctk05"]) == (float(fck), float(fcm), fctm, fctk05), grade
        assert g["fcm"] == g["fck"] + 8.0                                   # fcm = fck + 8 MPa
        assert g["Ecm"] == round(9500.0 * g["fcm"] ** (1 / 3), 1), grade    # Eq. (5.1)
        c = Concrete(grade.replace("_", "/"), edition="2023")
        assert c.fctk_95 == pytest.approx(fctk95), grade                    # 1,3·fctm
        # the governing formulae of the table: fctm = 0,3·fck^(2/3) (≤ C50) / 1,1·fck^(1/3)
        formula = 0.3 * fck ** (2 / 3) if fck <= 50 else 1.1 * fck ** (1 / 3)
        assert g["fctm"] == pytest.approx(formula, abs=0.06), grade
        assert g["fctk05"] == pytest.approx(0.7 * g["fctm"], abs=0.08), grade   # (table rounding)


def test_2023_stress_strain_parameters_are_the_same_for_all_classes():
    from eurocodepy.ec2 import Concrete

    for grade in TABLE_5_1:
        c = Concrete(grade.replace("_", "/"), edition="2023")
        assert (c.eps_c2, c.eps_cu2, c.n) == (2.0, 3.5, 2.0), grade        # 8.1.2(1), Eq. (8.4)
    assert Concrete.from_fck(70, edition="2023").eps_cu2 == 3.5
    assert (Concrete.from_fck(70, edition="2023").eps_c2, Concrete.from_fck(70, edition="2023").n) == (2.0, 2.0)
    # 2004 keeps the reduced values of high-strength concrete
    c04 = Concrete("C70/85")
    assert (c04.eps_cu2, c04.n) == (2.7, 1.45) and c04.eps_c2 > 2.0
    f04 = Concrete.from_fck(70)
    assert f04.eps_cu2 < 3.5 and f04.n < 2.0


def test_2023_grades_added_by_the_edition_and_2004_untouched():
    from eurocodepy.ec2 import Concrete

    assert Concrete("C12/15", edition="2023").fcm == 20.0
    assert Concrete("C16/20", edition="2023").fctm == 1.9
    with pytest.raises(ValueError, match="not found"):
        Concrete("C12/15")                        # 2004 database has no C12/15 here
    assert Concrete("C60/75").fctm == 4.4         # 2004 Table 3.1
    assert Concrete("C60/75", edition="2023").fctm == 4.3


def test_get_concrete_takes_the_edition():
    from eurocodepy.ec2 import Concrete, ConcreteClass, get_concrete

    a = get_concrete("C60/75")
    b = get_concrete("C60/75", edition="2023")
    assert (a.edition, b.edition) == ("2004", "2023")
    assert (a.fctm, b.fctm) == (4.4, 4.3)
    k = get_concrete("C50/60", "2023", loading="other", k_cip=1.1)
    assert (k.k_tc, k.gamma_c) == (0.85, pytest.approx(1.65))
    assert get_concrete(ConcreteClass["C30_37"], edition="2023").edition == "2023"
    assert get_concrete("C12/15", edition="2023").fck == 12.0
    # an object is returned as it is; another edition than the asked one is refused
    c23 = Concrete("C30/37", edition="2023")
    assert get_concrete(c23) is c23 and get_concrete(c23, edition="2023") is c23
    with pytest.raises(ValueError, match="edition '2023', not '2004'"):
        get_concrete(c23, edition="2004")
    with pytest.raises(ValueError, match="edition '2004', not '2023'"):
        get_concrete(Concrete("C30/37"), edition="2023")
    with pytest.raises(TypeError, match="ConcreteClass"):
        get_concrete(30)
