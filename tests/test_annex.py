"""National annexes: registry, validation, patches on editions, loads, no mutation of the database."""
import copy
import json

import pytest

import eurocodepy as ec
from eurocodepy import annex as annex_mod
from eurocodepy import dbase
from eurocodepy.ec2 import Concrete, Prestress, Reinforcement, material_partial_factors, uls2023
from eurocodepy.ec2.uls2023 import detailing as dt
from eurocodepy.ec2.uls2023 import shear as sh
from eurocodepy.national_parameters import seismic_get_params, wind_get_params

XX = {
    "country": "xx",
    "name": "Testland",
    "source": "synthetic, for tests",
    "loads": {"wind": {
        "base_velocity": {"ZonaT": {"vb0": 31.0}},
        "terrain": {"II": {"z0": 0.05, "zmin": 2.0}},
        "cprob": 1.0, "k_I": 1.0}},
    "editions": {"ec2": {"2023": {
        "overrides": {
            "Concrete.Parameters": {"fck_ref": 50.0, "k_tc": {"late_loading": 0.9}},
        },
        "partial_factors": {
            "materials": {"persistent": {"gamma_c": 1.4, "gamma_s": 1.1, "gamma_v": 1.3}},
            "gamma_SH": 0.9,
        },
        "detailing": {"beams": {"s_l_max": 0.7}, "columns": {"k_confinement": 0.03}},
        "shear_interface": {"rough": {"c_v1": 0.2}},
        "punch_params": {"dmax": 16.0},
    }}},
}


@pytest.fixture
def xx():
    code = ec.register_annex(XX)
    yield code
    ec.unregister_annex(code)


def test_builtin_pt_and_unknown_annex():
    assert "PT" in ec.available_annexes()
    a = ec.get_annex("pt")
    assert a["country"] == "PT"
    assert set(a["loads"]) == {"wind", "seismic", "live"}
    a["loads"]["wind"].clear()                                   # a copy
    assert ec.get_annex("PT")["loads"]["wind"]
    with pytest.raises(ValueError, match="Unknown national annex 'ZZ'.*PT"):
        ec.get_annex("ZZ")
    with pytest.raises(ValueError, match="Unknown national annex"):
        dbase.get_edition_data("ec2", "2023", annex="ZZ")
    with pytest.raises(ValueError, match="Unknown national annex"):
        Concrete("C30/37", edition="2023", annex="ZZ")


def test_pt_loads_are_in_the_annex_file_and_in_the_database():
    pt = ec.get_annex("PT")["loads"]
    assert dbase.WindLoads["locale"]["PT"] == pt["wind"]
    assert dbase.SeismicLoads["Locale"]["PT"] == pt["seismic"]
    assert dbase.Loads["Live"]["Locale"]["PT"] == pt["live"]
    raw = json.loads((annex_mod._DIR.parent / "eurocodes.json").read_text(encoding="utf-8"))
    loads = raw["Eurocodes"]["Loads"]
    assert "PT" not in loads["Wind"]["locale"]
    assert "PT" not in loads["Seismic"]["Locale"]
    assert "PT" not in loads["Live"]["Locale"]
    assert "EU" in loads["Wind"]["locale"]


def test_register_validates_and_refuses_duplicates():
    with pytest.raises(ValueError, match="'country'"):
        ec.register_annex({"name": "x"})
    with pytest.raises(ValueError, match="unknown keys"):
        ec.register_annex({"country": "YY", "values": {}})
    with pytest.raises(ValueError, match="loads"):
        ec.register_annex({"country": "YY", "loads": {"snow": {}}})
    with pytest.raises(TypeError, match="overrides"):
        ec.register_annex({"country": "YY",
                           "editions": {"ec2": {"2023": {"overrides": []}}}})
    with pytest.raises(ValueError, match="already registered"):
        ec.register_annex({"country": "pt"})
    assert "YY" not in ec.available_annexes()


def test_register_from_a_file(tmp_path):
    f = tmp_path / "ZZ.json"
    f.write_text(json.dumps({"country": "ZZ", "editions": {}}), encoding="utf-8")
    assert ec.register_annex(f) == "ZZ"
    try:
        assert "ZZ" in ec.available_annexes()
        assert ec.register_annex(f, replace=True) == "ZZ"
    finally:
        ec.unregister_annex("ZZ")
    assert "ZZ" not in ec.available_annexes()


def test_edition_data_patch_and_database_untouched(xx):
    before = copy.deepcopy(dbase.db["Editions"])
    p = dbase.get_edition_data("ec2", "2023", annex=xx)["Concrete"]["Parameters"]
    assert p["fck_ref"] == 50.0
    assert p["k_tc"]["late_loading"] == 0.9                       # patched one key only
    assert p["k_tc"]["other"] == 0.85
    assert p["gamma_cc"] == 1.5                                  # the rest as recommended
    assert dbase.get_edition_data("ec2", "2023")["Concrete"]["Parameters"]["fck_ref"] == 40.0
    assert dbase.db["Editions"] == before
    assert ec.get_annex(xx)["editions"]["ec2"]["2023"]["overrides"]["Concrete.Parameters"][
        "fck_ref"] == 50.0                                       # the registry is not edited either


def test_edition_params_deep_merge(xx):
    d = dbase.get_edition_params("ec2", "detailing", "2023", annex=xx)
    assert d["beams"]["s_l_max"] == 0.7
    assert d["beams"]["s_bu_max"] == 0.6                          # untouched sibling
    assert d["columns"]["k_confinement"] == 0.03
    assert dbase.get_edition_params("ec2", "detailing", "2023")["beams"]["s_l_max"] == 0.75
    assert dbase.get_edition_params("ec2", "partial_factors", "2023", xx)["gamma_SH"] == 0.9
    # other editions / sections are not affected by a patch for 2023
    assert dbase.get_edition_params("ec2", "detailing", "2004", annex=xx) == {}
    em = dbase.EurocodeMaterials("ec2", "2023", annex=xx)
    assert em.Concrete["Parameters"]["fck_ref"] == 50.0
    assert "annex='XX'" in repr(em)


def test_partial_factors_and_concrete_with_annex(xx):
    f = material_partial_factors("2023", "persistent", xx)
    assert (f["gamma_c"], f["gamma_s"], f["gamma_v"]) == (1.4, 1.1, 1.3)
    assert f["gamma_ce"] == 1.5                                  # merged, not replaced
    assert material_partial_factors("2023", "persistent")["gamma_c"] == 1.5
    assert material_partial_factors("2023", "accidental", xx)["gamma_c"] == 1.15

    c = Concrete("C50/60", edition="2023", annex=xx)
    assert (c.gamma_c, c.k_tc, c.eta_cc) == (1.4, 0.9, 1.0)      # fck_ref = 50
    assert c.fcd == pytest.approx(0.9 * 50.0 / 1.4)
    ref = Concrete("C50/60", edition="2023")
    assert ref.eta_cc == pytest.approx((40 / 50) ** (1 / 3)) and ref.gamma_c == 1.5
    assert Concrete.from_fck(30, edition="2023", annex=xx).gamma_c == 1.4
    assert Reinforcement("B500B", edition="2023", annex=xx).gamma_s == 1.1
    assert Prestress("Y1860S7 12.5", edition="2023", annex=xx).gamma_P == 1.1


def test_check_inputs_take_the_annex(xx):
    inp = uls2023.ShearInput.from_partial_factors(
        "2023", "persistent", annex=xx, b=0.3, d=0.5, fck=60.0, fyk=500.0, as_long=0.0015)
    assert (inp.gamma_c, inp.gamma_s, inp.gamma_v) == (1.4, 1.1, 1.3)
    assert inp.annex == "XX"
    r = uls2023.eurocode2_shear_check(inp, 150.0)
    assert r.details["f_cd"] == pytest.approx((50 / 60) ** (1 / 3) * 60.0 / 1.4)  # fck_ref = 50


def test_shear_check_eta_cc_follows_the_annex(xx):
    kw = {"b": 0.3, "d": 0.5, "fck": 60.0, "fyk": 500.0, "as_long": 0.0015}
    rec = uls2023.eurocode2_shear_check(uls2023.ShearInput(**kw), 150.0)
    pat = uls2023.eurocode2_shear_check(uls2023.ShearInput(annex=xx, **kw), 150.0)
    assert rec.details["f_cd"] == pytest.approx((40 / 60) ** (1 / 3) * 60 / 1.5)
    assert pat.details["f_cd"] == pytest.approx((50 / 60) ** (1 / 3) * 60 / 1.5)


def test_punch_input_and_interface_and_detailing_with_annex(xx):
    from eurocodepy.ec2.uls.punch_check import PunchInput
    p = PunchInput(d=0.25, bx=0.4, fck=30.0, fyk=500.0, edition="2023", annex=xx)
    assert p.dmax == 16.0
    assert PunchInput(d=0.25, bx=0.4, fck=30.0, fyk=500.0, edition="2023").dmax == 20.0
    assert sh.interface_coefficients("rough", annex=xx)["c_v1"] == 0.2
    assert sh.interface_coefficients("rough")["c_v1"] == 0.15
    assert sh.calc_tau_rdi(30.0, 1.5, 20.0, "rough", annex=xx) > sh.calc_tau_rdi(
        30.0, 1.5, 20.0, "rough")
    assert dt.beam_max_spacings(0.5, annex=xx)["s_l_max"] == pytest.approx(0.35)
    assert dt.beam_max_spacings(0.5)["s_l_max"] == pytest.approx(0.375)
    assert dt.column_min_confinement_stress(30.0, annex=xx) == pytest.approx(0.9)
    assert dt.column_min_confinement_stress(30.0) == pytest.approx(0.6)
    assert dt.column_min_confinement_stress(30.0, k=0.05, annex=xx) == pytest.approx(1.5)


def test_registered_loads_reach_wind_and_the_database(xx):
    vb0, zmin, z0, _ = wind_get_params("xx", "ZonaT", "II")
    assert (vb0, zmin, z0) == (31.0, 2.0, 0.05)
    assert dbase.WindLoads["locale"]["XX"]["base_velocity"]["ZonaT"]["vb0"] == 31.0
    ec.unregister_annex("XX")
    assert "XX" not in dbase.WindLoads["locale"]
    with pytest.raises(ValueError, match="Invalid code"):
        wind_get_params("XX", "ZonaT", "II")
    ec.register_annex(XX)                                        # the fixture unregisters it


def test_pt_wind_and_seismic_still_work_through_the_annex():
    assert wind_get_params("PT", "ZonaA", "II")[0] == ec.get_annex("PT")["loads"]["wind"][
        "base_velocity"]["ZonaA"]["vb0"]
    assert seismic_get_params("PT", "PT1", "A", "ii")["ImportanceCoef"] == 1.0
