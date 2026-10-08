"""EN 1995-1-1:2025 timber parameters in the database (Editions.ec5["2025"]):
service classes (Table 4.2), k_mod (Table 5.4), k_def (Table 5.5), k_h
(Table 5.6), partial factors (Tables 4.3-4.5) and the edition-aware ``Timber``.
The 2004 edition (the default) must be unchanged."""
import copy

import pytest

from eurocodepy import dbase
from eurocodepy.ec5 import uls2025
from eurocodepy.ec5.materials import (LoadDuration, ServiceClass, Timber,
                                      TimberClass, TimberForcesType)

P = LoadDuration.Permanent
L = LoadDuration.LongDuration
M = LoadDuration.MediumDuration
S = LoadDuration.ShortDuration
I = LoadDuration.Instantaneous       # noqa: E741
A = [0.60, 0.70, 0.80, 0.90, 1.10]
B = [0.55, 0.60, 0.70, 0.80, 1.00]


def _p25():
    return dbase.get_edition_data("ec5", "2025")["Timber"]["Parameters"]


# ── the 2004 edition is untouched ───────────────────────────────────────────

def test_2004_is_still_the_default_and_unchanged():
    assert dbase.TimberMaterial["ServiceClasses"] == ["SC1", "SC2", "SC3"]
    t = TimberClass("GL24h")
    assert t.edition is None
    assert t.kmods["SC3"] == [0.5, 0.55, 0.65, 0.7, 0.9]       # 2004 SC3
    assert "SC4" not in t.kmods
    assert dbase.TimberParams["safety"]["glulam"] == 1.25
    assert "clt" not in dbase.TimberParams["kmod"]               # new keys: 2025 only


def test_edition_data_is_a_copy_and_never_mutates_the_base():
    d = dbase.get_edition_data("ec5", "2025")
    d["Timber"]["Parameters"]["kmod"]["timber"]["SC1"][0] = -1.0
    assert dbase.TimberParams["kmod"]["timber"]["SC1"][0] == 0.6
    assert _p25()["kmod"]["timber"]["SC1"][0] == 0.6


def test_service_class_enum_has_sc4_but_2004_has_no_data_for_it():
    assert [s.name for s in ServiceClass] == ["SC1", "SC2", "SC3", "SC4"]
    with pytest.raises(KeyError, match="SC4"):
        TimberClass("C24").k_mod(ServiceClass.SC4, M)


# ── Table 4.2 ───────────────────────────────────────────────────────────────

def test_service_classes_of_2025():
    tm = dbase.get_edition_data("ec5", "2025")["Timber"]
    assert tm["ServiceClasses"] == ["SC1", "SC2", "SC3", "SC4"]
    d = _p25()["ServiceClassData"]
    assert (d["SC1"]["rh_upper"], d["SC2"]["rh_upper"], d["SC3"]["rh_upper"]) == (65, 85, 95)
    assert (d["SC1"]["mc_upper"], d["SC2"]["mc_upper"], d["SC3"]["mc_upper"]) == (12, 20, 24)
    assert (d["SC1"]["rh_mean"], d["SC2"]["mc_mean"], d["SC3"]["mc_mean"]) == (50, 16, 20)
    assert d["SC4"]["saturated"]


# ── Table 5.4 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key,sc,expected", [
    ("timber", "SC1", A), ("timber", "SC2", A), ("timber", "SC3", B),
    ("timber", "SC4", [0.50, 0.55, 0.65, 0.70, 0.90]),
    ("fst", "SC2", A), ("glulam", "SC1", A), ("glulam", "SC3", B),
    ("bgl", "SC2", A), ("gst", "SC1", A), ("clt", "SC2", A),
    ("lvl", "SC2", A), ("lvl", "SC3", B), ("glvl", "SC2", A),
    ("swp_1s", "SC1", A), ("swp_2s", "SC2", A),
    ("plywood_1", "SC1", A), ("plywood_2", "SC2", A),
    ("plywood_3", "SC3", B),
    ("osb_2", "SC1", [0.30, 0.45, 0.65, 0.85, 1.10]),
    ("osb_3_4", "SC1", [0.40, 0.50, 0.70, 0.90, 1.10]),
    ("osb_3_4", "SC2", [0.30, 0.40, 0.55, 0.70, 0.90]),
    ("hb_la", "SC1", [0.30, 0.45, 0.65, 0.85, 1.10]),
    ("hb_hla", "SC2", [0.20, 0.30, 0.45, 0.60, 0.80]),
    ("mb_la", "SC1", [0.20, 0.40, 0.60, 0.80, 1.10]),
    ("mb_hls", "SC2", [None, None, None, 0.45, 0.80]),
    ("mdf_hls", "SC2", [None, None, None, 0.45, 0.80]),
    ("sb_ls", "SC1", [0.20, 0.40, 0.50, 0.65, 1.00]),
    ("sb_hls", "SC2", [0.10, 0.20, 0.30, 0.40, 0.60]),
    ("cpb", "SC1", [0.30, 0.45, 0.65, 0.85, 1.10]),
    ("cpb", "SC2", [0.20, 0.30, 0.45, 0.60, 0.80]),
    ("rpb_p4", "SC1", [0.30, 0.45, 0.65, 0.85, 1.10]),
    ("rpb_p5", "SC2", [0.20, 0.30, 0.45, 0.60, 0.80]),
    ("rpb_p6", "SC1", [0.40, 0.50, 0.70, 0.90, 1.10]),
    ("rpb_p7", "SC2", [0.30, 0.40, 0.55, 0.70, 0.90]),
    ("gypsum", "SC1", [0.20, 0.40, 0.60, 0.80, 1.10]),
    ("gypsum", "SC2", [0.15, 0.30, 0.45, 0.60, 0.80]),
    ("bonded_in_rods", "SC1", A),
    ("bonded_in_rods", "SC2", [0.50, 0.55, 0.65, 0.70, 0.90]),
])
def test_kmod_table_5_4(key, sc, expected):
    assert _p25()["kmod"][key][sc] == expected


def test_kmod_is_not_defined_where_the_table_has_no_entry():
    km = _p25()["kmod"]
    assert "SC4" not in km["glulam"] and "SC3" not in km["clt"]
    assert "SC3" not in km["glvl"] and "SC2" not in km["swp_1s"]


def test_timber_k_mod_follows_the_edition():
    gl04, gl25 = TimberClass("GL24h"), TimberClass("GL24h", edition="2025")
    assert gl04.k_mod(ServiceClass.SC3, P) == 0.5
    assert gl25.k_mod(ServiceClass.SC3, P) == 0.55
    assert gl25.k_mod(ServiceClass.SC3, I) == 1.00
    c25 = TimberClass("C24", edition="2025")
    assert [c25.k_mod(ServiceClass.SC4, ld) for ld in (P, L, M, S, I)] == \
        [0.50, 0.55, 0.65, 0.70, 0.90]
    assert c25.k_mod(ServiceClass.SC1, M) == 0.8
    assert c25.k_mod("SC2", S) == 0.9


def test_glulam_has_no_k_mod_in_sc4_in_2025():
    with pytest.raises(KeyError, match="SC4"):
        TimberClass("GL24h", edition="2025").k_mod(ServiceClass.SC4, M)


def test_design_strength_changes_with_the_edition():
    gl04, gl25 = TimberClass("GL24h"), TimberClass("GL24h", edition="2025")
    d04 = gl04.design_values(ServiceClass.SC3, P)
    d25 = gl25.design_values(ServiceClass.SC3, P)
    assert d25["fmd"] / d04["fmd"] == pytest.approx(0.55 / 0.5)
    # SC1/SC2 unchanged
    assert gl25.design_values(ServiceClass.SC1, M)["fmd"] == pytest.approx(
        gl04.design_values(ServiceClass.SC1, M)["fmd"])


# ── Table 5.5 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key,expected", [
    ("timber", {"SC1": 0.6, "SC2": 0.8, "SC3": 2.0, "SC4": 2.0}),
    ("fst", {"SC1": 0.6, "SC2": 0.8}), ("glulam", {"SC1": 0.6, "SC2": 0.8, "SC3": 2.0}),
    ("bgl", {"SC1": 0.6, "SC2": 0.8}), ("gst", {"SC1": 0.6, "SC2": 0.8}),
    ("clt", {"SC1": 0.8, "SC2": 1.0}), ("lvl", {"SC1": 0.6, "SC2": 0.8, "SC3": 2.0}),
    ("lvl_c_flatwise", {"SC1": 0.8, "SC2": 1.0, "SC3": 2.5}),
    ("glvl", {"SC1": 0.6, "SC2": 0.8}), ("glvl_c_flatwise", {"SC1": 0.8, "SC2": 1.0}),
    ("swp_p_1s", {"SC1": 0.6}), ("swp_c_2s", {"SC1": 0.8, "SC2": 1.0}),
    ("plywood_1", {"SC1": 0.8}), ("plywood_3", {"SC1": 0.8, "SC2": 1.0, "SC3": 2.5}),
    ("osb_2", {"SC1": 2.25}), ("osb_3_4", {"SC1": 1.5, "SC2": 2.25}),
    ("rpb_p5", {"SC1": 2.25, "SC2": 3.0}), ("rpb_p6", {"SC1": 1.5}),
    ("rpb_p7", {"SC1": 1.5, "SC2": 2.25}), ("hb_hla", {"SC1": 2.25, "SC2": 3.0}),
    ("mb_hls", {"SC1": 3.0, "SC2": 4.0}), ("sb", {"SC1": 3.0}),
    ("mdf_hls", {"SC1": 2.25, "SC2": 3.0}), ("cpb", {"SC1": 2.25, "SC2": 3.0}),
    ("gypsum", {"SC1": 3.0, "SC2": 4.0}),
])
def test_kdef_table_5_5(key, expected):
    kd = dict(_p25()["kdef"][key])
    kd.pop("_clause", None)
    assert kd == expected


def test_k_def_follows_the_edition():
    assert TimberClass("GL24h").k_def(ServiceClass.SC3) == 2.0
    c = TimberClass("C24", edition="2025")
    assert c.k_def(ServiceClass.SC4) == 2.0 and c.k_def(ServiceClass.SC2) == 0.8


# ── Table 5.6 ───────────────────────────────────────────────────────────────

def test_kh_table_5_6_solid_timber():
    c = TimberClass("C24", edition="2025")
    assert c.k_h(0.075, TimberForcesType.Bending) == pytest.approx(
        min((0.15 / 0.075) ** 0.2, 1.3))
    assert c.k_h(0.4, TimberForcesType.Bending) == 1.0                  # k_h,min
    assert c.k_h(0.02, TimberForcesType.Shear) == 1.3                   # k_h,max
    assert c.k_h(0.05, TimberForcesType.Tension) == pytest.approx(
        min((0.15 / 0.05) ** 0.2, 1.3))


def test_kh_table_5_6_glulam():
    g = TimberClass("GL24h", edition="2025")
    assert g.k_h(0.3, TimberForcesType.Bending) == pytest.approx((0.6 / 0.3) ** 0.04)
    assert g.k_h(0.3, TimberForcesType.Shear) == pytest.approx(
        min((0.6 / 0.3) ** 0.1, 1.1))
    assert g.k_h(1.4, TimberForcesType.Shear) == 0.9 or g.k_h(1.4, TimberForcesType.Shear) == pytest.approx(
        max((0.6 / 1.4) ** 0.1, 0.9))
    assert g.k_h(0.3, TimberForcesType.Tension) == 1.0                  # none


def test_kh_table_5_6_lvl_parameters():
    kh = _p25()["kh"]["lvl"]
    assert (kh["sm"], kh["aref"], kh["khmmax"]) == (0.15, 0.3, 1.2)
    assert (kh["st"], kh["atref"], kh["khtmax"]) == (0.075, 3.0, 1.1)   # s = half
    assert (kh["sv"], kh["khvmin"], kh["khvmax"]) == (0.0, 1.0, 1.0)   # no effect


# ── partial factors ─────────────────────────────────────────────────────────

def test_material_partial_factors_table_4_3():
    ms = dbase.get_edition_params("ec5", "material_safety", "2025")
    assert (ms["ST"], ms["FST"]) == (1.30, 1.30)
    assert (ms["GL"], ms["BGL"], ms["GST"], ms["CLT"], ms["SWP-C"]) == (1.25,) * 5
    assert (ms["LVL-P"], ms["GLVL-C"], ms["PW"], ms["OSB"]) == (1.20,) * 4
    assert (ms["HB"], ms["MB"], ms["SB"], ms["MDF"], ms["RPB"], ms["CPB"],
            ms["GPB"], ms["GFB"]) == (1.30,) * 8


def test_material_factors_used_by_timber_equal_table_4_3():
    ms = dbase.get_edition_params("ec5", "material_safety", "2025")
    assert TimberClass("C24", edition="2025").safety == ms["ST"]
    assert TimberClass("GL24h", edition="2025").safety == ms["GL"]


def test_connection_partial_factors_tables_4_4_and_4_5():
    cs = dbase.get_edition_params("ec5", "connection_safety", "2025")
    assert cs["gamma_R_dowel_type"] == 1.30 and cs["gamma_R_carpentry"] == 1.30
    assert cs["gamma_M_bond_line"] == 1.30
    assert cs["gamma_M1_steel_ductile"] == 1.10
    assert cs["gamma_M2_steel_tension_fracture"] == 1.25
    assert cs["accidental"] == 1.00
    assert dbase.get_edition_params("ec5", "connection_safety", "2004") == {}


# ── other parameters ────────────────────────────────────────────────────────

def test_other_2025_parameters():
    p = _p25()
    assert p["G005_over_Gmean"] == {"_clause": p["G005_over_Gmean"]["_clause"],
                                    "softwood": 0.67, "hardwood": 0.83}
    assert p["clt"]["fv_xy_k_max"] == 5.5 and p["clt"]["f_tor_node_k"] == 2.5
    assert p["clt"]["rho_mean_over_k"] == 1.1
    sh = p["Shrinkage"]
    assert sh["SL_PL_softwood"] == {"perpendicular_to_grain": 0.25,
                                    "parallel_to_grain": 0.01}
    assert sh["OSB_4"]["in_plane"] == 0.015 and sh["CPB"]["perpendicular_to_plane"] == 0.05
    assert p["LoadDurationInfo"]["Permanent"] == "more than 10 years"


def test_fc0k_factor_is_optional_and_not_applied_to_design_values():
    gl = TimberClass("GL24h", edition="2025")
    assert gl.fc0k_factor(ServiceClass.SC1) == 1.0                  # "may": optional
    assert gl.fc0k_factor(ServiceClass.SC1, optional=True) == 1.2
    assert gl.fc0k_factor(ServiceClass.SC2, optional=True) == 1.0
    before = gl.design_values(ServiceClass.SC1, M)["fc0d"]
    assert before == pytest.approx(gl.fc0k * 0.8 / 1.25)
    assert TimberClass("GL24h").fc0k_factor(ServiceClass.SC1, optional=True) == 1.0


# ── the 2025 checks run on a 2025 timber ────────────────────────────────────

def test_2025_section_check_with_sc3_and_sc4():
    from eurocodepy.utils import RectangularCrossSection
    inp_cls = uls2025.TimberSectionInput
    f = uls2025.TimberForces(my_ed=50.0, vz_ed=20.0)
    for grade, sc in (("GL24h", ServiceClass.SC3), ("C24", ServiceClass.SC4)):
        t = TimberClass(grade, edition="2025")
        r = uls2025.eurocode5_section_check(inp_cls(
            section=RectangularCrossSection(0.14, 0.6), timber=t,
            service_class=sc, load_duration=M, l_0y=3000, l_0z=3000, l_0m=3000), f)
        assert r.utilization > 0


def test_json_is_valid_and_has_the_ec5_editions():
    ed = dbase.db["Editions"]["ec5"]
    assert ed["2004"] == {"default": True}
    assert ed["2025"]["default"] is False
    assert copy.deepcopy(ed)["2025"]["source"].startswith("EN 1995-1-1:2025")
