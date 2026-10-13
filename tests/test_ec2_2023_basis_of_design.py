"""EN 1992-1-1:2023 Clause 4 (basis of design) and Eqs. (5.3)-(5.5) in ec2.materials.

Values: Table 4.1 (r_sup/r_inf), Table 4.2 (prestress partial factors),
Table 4.3 (gamma_S, gamma_C, gamma_CE, gamma_V), 4.3.1 (gamma_SH), 4.3.3(4)
(k_cip) and 5.1.6 (eta_cc, k_tc, k_tt). The 2004 default must not change.
"""
import pytest

from eurocodepy import dbase
from eurocodepy.ec2 import (
    Concrete,
    Prestress,
    Reinforcement,
    material_partial_factors,
    prestress_partial_factors,
)


def test_table_4_3_values():
    p = material_partial_factors("2023", "persistent")
    assert (p["gamma_s"], p["gamma_c"], p["gamma_ce"], p["gamma_ce_tested"],
            p["gamma_v"]) == (1.15, 1.5, 1.5, 1.3, 1.4)
    f = material_partial_factors("2023", "fatigue")
    assert (f["gamma_s"], f["gamma_c"], f["gamma_v"]) == (1.15, 1.5, 1.4)
    a = material_partial_factors("2023", "accidental")
    assert (a["gamma_s"], a["gamma_c"], a["gamma_ce"], a["gamma_v"]) == (1.0, 1.15, 1.15, 1.15)
    s = material_partial_factors("2023", "serviceability")
    assert (s["gamma_s"], s["gamma_c"], s["gamma_v"]) == (1.0, 1.0, None)


def test_2004_factors_unchanged_and_only_persistent():
    p = material_partial_factors()
    assert (p["gamma_s"], p["gamma_c"]) == (1.15, 1.5)
    with pytest.raises(ValueError, match="persistent"):
        material_partial_factors("2004", "accidental")
    with pytest.raises(ValueError, match="situation"):
        material_partial_factors("2023", "seismic")


def test_prestress_tables_4_1_and_4_2():
    t = prestress_partial_factors("2023")
    assert t["action"]["gamma_P_fav"] == 1.0
    assert t["action"]["gamma_P_unfav"] == 1.2
    assert t["action"]["gamma_dP_sup"] == 0.8
    assert t["action"]["gamma_dP_inf"] == 1.2
    assert t["action"]["gamma_dP_linear_uncracked"] == 1.0
    assert t["characteristic"]["pre_tensioning"] == {"r_sup": 1.05, "r_inf": 0.95}
    assert t["characteristic"]["post_tensioning_unbonded"] == {"r_sup": 1.05, "r_inf": 0.95}
    assert t["characteristic"]["post_tensioning_bonded"] == {"r_sup": 1.10, "r_inf": 0.90}
    assert prestress_partial_factors("2004") == {"action": {}, "characteristic": {}}


def test_gamma_sh_and_k_cip():
    pf = dbase.get_edition_params("ec2", "partial_factors", "2023")
    assert pf["gamma_SH"] == 1.0
    assert pf["k_cip"]["general"] == 1.1
    assert pf["k_cip"]["en_1536_1538_14199"] == 1.0


def test_concrete_2023_defaults_to_late_loading_k_tc_1():
    c = Concrete("C30/37", edition="2023")
    assert c.edition == "2023"
    assert (c.k_tc, c.k_tt, c.eta_cc, c.gamma_c) == (1.0, 0.8, 1.0, 1.5)
    assert c.fcd == pytest.approx(30.0 / 1.5)
    assert c.fctd == pytest.approx(0.8 * c.fctk_05 / 1.5)
    assert c.Ecm == 31938.8  # Eq. (5.1), from the 2023 grade override


def test_concrete_2023_other_loading_and_eta_cc():
    c = Concrete("C50/60", edition="2023", loading="other")
    eta = (40.0 / 50.0) ** (1 / 3)
    assert c.eta_cc == pytest.approx(eta)
    assert c.k_tc == 0.85
    assert c.fcd == pytest.approx(eta * 0.85 * 50.0 / 1.5)
    assert c.fctd == pytest.approx(0.7 * c.fctk_05 / 1.5)
    assert Concrete("C40/50", edition="2023").eta_cc == 1.0   # fck <= fck_ref
    assert Concrete("C20/25", edition="2023").eta_cc == 1.0   # capped at 1


def test_concrete_2023_situations_and_k_cip():
    assert Concrete("C30/37", edition="2023", situation="accidental").fcd == pytest.approx(30 / 1.15)
    assert Concrete("C30/37", edition="2023", situation="serviceability").fcd == pytest.approx(30.0)
    c = Concrete("C30/37", edition="2023", k_cip=1.1)
    assert c.gamma_c == pytest.approx(1.65)
    assert c.fcd == pytest.approx(30 / 1.65)


def test_concrete_2023_has_c100_115():
    c = Concrete("C100/115", edition="2023")
    assert c.fck == 100.0
    assert c.eta_cc == pytest.approx(0.4 ** (1 / 3))
    with pytest.raises(ValueError, match="not found"):
        Concrete("C100/115")


def test_concrete_invalid_loading():
    with pytest.raises(ValueError, match="loading"):
        Concrete("C30/37", edition="2023", loading="short")


def test_concrete_default_is_unchanged_2004():
    c = Concrete("C30/37")
    assert (c.edition, c.gamma_c, c.fcd, c.fctd) == ("2004", 1.5, 20.0, 1.3)
    assert (c.eta_cc, c.k_tc, c.k_tt) == (1.0, 1.0, 1.0)
    assert Concrete("C30/37", edition="2004").fcd == 20.0


def test_from_fck_2023():
    c = Concrete.from_fck(30, edition="2023", loading="other")
    assert c.fcm == 38.0
    assert c.Ecm == round(9500 * 38.0 ** (1 / 3), 1)
    assert c.fcd == pytest.approx(0.85 * 30 / 1.5)
    hi = Concrete.from_fck(60, edition="2023")
    assert hi.fctm == round(1.1 * 60 ** (1 / 3), 1)
    assert Concrete.from_fck(30).fcd == 20.0


def test_reinforcement_and_prestress_gamma_s():
    assert Reinforcement("B500B").fyd == 434.8
    assert Reinforcement("B500B", edition="2023").gamma_s == 1.15
    r = Reinforcement("B500B", edition="2023", situation="accidental")
    assert (r.gamma_s, r.fyd) == (1.0, 500.0)
    p = Prestress("Y1860S7 12.5")
    assert p.gamma_P == 1.15
    assert Prestress("Y1860S7 12.5", edition="2023", situation="accidental").gamma_P == 1.0


def test_fctk_05_is_the_table_value_not_multiplied_by_fctm():
    c = Concrete("C30/37")
    assert c.fctk_05 == 2.0
    assert c.fctk_95 == pytest.approx(3.8)


def test_from_partial_factors_on_check_inputs():
    from eurocodepy.ec2.uls.punch_check import PunchInput
    from eurocodepy.ec2.uls.shear_check import ShearInput

    p = PunchInput.from_partial_factors("2023", "accidental",
                                        d=0.25, bx=0.4, by=0.4, fck=30.0, fyk=500.0)
    assert (p.gamma_v, p.gamma_c, p.gamma_s, p.edition) == (1.15, 1.15, 1.0, "2023")
    # explicit fields win; the default edition is 2004 and keeps gamma_v's default
    q = PunchInput.from_partial_factors(d=0.25, bx=0.4, fck=30.0, fyk=500.0, gamma_v=1.3)
    assert (q.gamma_v, q.gamma_c, q.edition) == (1.3, 1.5, "2004")
    # serviceability has no gamma_v: the field default stays
    assert PunchInput.from_partial_factors("2023", "serviceability", d=0.25, bx=0.4,
                                           fck=30.0, fyk=500.0).gamma_v == 1.4
    # classes without gamma_v / edition just get gamma_c and gamma_s
    s = ShearInput.from_partial_factors("2023", "fatigue", b=0.3, d=0.5, fck=30.0, fyk=500.0)
    assert (s.gamma_c, s.gamma_s) == (1.5, 1.15)
