"""CLT and LVL strength categories of EN 1995-1-1:2025 Annex N (Tables N.1-N.3)."""

import pytest

from eurocodepy import dbase
from eurocodepy.ec5 import materials as m

EDITIONS = [None, "2025"]


def _grades(edition):
    return dbase.get_edition_data("ec5", edition)["Timber"]["Grade"]


@pytest.mark.parametrize("edition", EDITIONS)
def test_grades_present_in_both_editions(edition):
    g = _grades(edition)
    for label in ("CL24", "LVL32P", "LVL35P", "LVL48P", "LVL50P", "LVL80P",
                  "LVL22C", "LVL25C", "LVL32C", "LVL36C", "LVL70C", "LVL75C"):
        assert label in g
    assert g["C24"]["Type"] == "timber"  # existing grades untouched


def test_cl24_table_n1():
    g = dbase.TimberGrades["CL24"]
    assert (g["fmk"], g["fm_edge_k"], g["ft0k"], g["ft90k"]) == (24, 20.5, 14, 0.12)
    assert (g["fc0k"], g["fc90k"], g["fvk"], g["frk"], g["fvxyk"]) == (21, 2.5, 3.5, 0.7, 5.5)
    assert (g["E0mean"], g["E90mean"], g["Gmean"], g["Grmean"], g["Gvxymean"]) == (
        11000, 370, 650, 50, 250)
    assert g["rhok"] == 385
    # not in the table: derived with the 2025 clt parameters (0.83, 1.1)
    assert g["E0k"] == pytest.approx(0.83 * 11000)
    assert g["Gk"] == pytest.approx(0.83 * 650)
    assert g["rhom"] == pytest.approx(1.1 * 385)


# label: (fm_edge, fm_flat, ft0, ft90, fc0, fc90, fv_edge, fv_flat, E0mean, E0k, rhom, rhok)
LVL = {
    "LVL32P": (27, 32, 22, 0.5, 26, 4, 3.2, 2.0, 9600, 8000, 440, 410),
    "LVL35P": (30, 35, 22, 0.5, 30, 6, 3.2, 2.3, 12000, 10000, 510, 480),
    "LVL48P": (44, 48, 35, 0.8, 35, 6, 4.2, 2.3, 13800, 11600, 510, 480),
    "LVL50P": (46, 50, 36, 0.9, 42, 8.5, 4.8, 3.2, 15200, 12600, 580, 550),
    "LVL80P": (75, 80, 60, 1.5, 69, 14, 8, 8, 16800, 14900, 800, 730),
    "LVL22C": (19, 22, 14, 4, 18, 8, 3.6, 1.1, 6700, 5500, 440, 410),
    "LVL25C": (20, 25, 15, 4, 18, 8, 3.6, 1.1, 7200, 6000, 440, 410),
    "LVL32C": (28, 32, 18, 5, 18, 9, 4.5, 1.3, 10000, 8300, 510, 480),
    "LVL36C": (32, 36, 22, 5, 26, 9, 4.5, 1.3, 10500, 8800, 510, 480),
    "LVL70C": (54, 70, 45, 16, 54, 45, 7.8, 3.8, 11800, 10900, 800, 730),
    "LVL75C": (60, 75, 51, 8, 64, 53, 7.8, 3.8, 13200, 12200, 800, 730),
}


@pytest.mark.parametrize("label", LVL)
def test_lvl_tables_n2_n3(label):
    g = dbase.TimberGrades[label]
    keys = ("fm_edge_k", "fmk", "ft0k", "ft90k", "fc0k", "fc90k", "fvk", "fv_flat_k",
            "E0mean", "E0k", "rhom", "rhok")
    assert tuple(g[k] for k in keys) == LVL[label]
    assert g["Product"] == ("LVL-P" if label.endswith("P") else "LVL-C")
    assert g["s_size"] == 0.15


def test_lvl_shear_moduli_and_mdv():
    p48 = dbase.TimberGrades["LVL48P"]
    assert (p48["Gmean"], p48["Gk"], p48["G_flat_mean"], p48["G_flat_k"]) == (600, 400, 380, 270)
    assert (p48["E90mean"], p48["E90k"]) == (430, 350)
    c32 = dbase.TimberGrades["LVL32C"]
    assert (c32["fm90_flat_k"], c32["fv90_flat_k"], c32["E90mean"], c32["Em90_flat_k"]) == (
        7, 0.6, 2400, 1000)
    assert (c32["G90_flat_mean"], c32["G90_flat_k"]) == (22, 16)
    # manufacturer's declared values / not produced from pine are null
    assert dbase.TimberGrades["LVL32P"]["E90mean"] is None
    assert dbase.TimberGrades["LVL22C"]["fm90_flat_k"] is None
    assert dbase.TimberGrades["LVL80P"]["fc90_flat_pine_k"] is None
    assert dbase.TimberGrades["LVL75C"]["fv90_flat_k"] is None


@pytest.mark.parametrize("edition", EDITIONS)
def test_timber_class_dispatch_and_design_values(edition):
    clt = m.TimberClass("CL24", edition)
    assert isinstance(clt, m.CLT) and clt.material == m.TimberType.CLT
    assert clt.safety == 1.25 and clt.frk == 0.7 and clt.fm_edge_k == 20.5
    p = m.TimberClass("LVL48P", edition)
    c = m.TimberClass("LVL32C", edition)
    assert isinstance(p, m.LVL) and p.timber_product == m.TimberProduct.LVL_P
    assert isinstance(c, m.LVL) and c.timber_product == m.TimberProduct.LVL_C
    assert p.safety == 1.2 and p.fm_edge_k == 44 and c.props["fv90_flat_k"] == 0.6
    # existing dispatch is not hijacked by the new labels
    assert isinstance(m.TimberClass("C24", edition), m.SolidTimber)
    assert isinstance(m.TimberClass("GL24h", edition), m.Glulam)
    d = p.design_values(m.ServiceClass.SC1, m.LoadDuration.MediumDuration)
    assert d["fmd"] == pytest.approx(48 * 0.8 / 1.2)


def test_clt_kmod_only_in_2025():
    assert m.TimberClass("CL24", "2025").k_mod(
        m.ServiceClass.SC1, m.LoadDuration.MediumDuration) == 0.8
    with pytest.raises(KeyError, match="No k_mod"):
        m.TimberClass("CL24").k_mod(m.ServiceClass.SC1, m.LoadDuration.MediumDuration)


def test_wrong_class_for_label_is_rejected():
    with pytest.raises(ValueError, match="CLT type"):
        m.CLT("LVL32P")
    with pytest.raises(ValueError, match="LVL type"):
        m.LVL("CL24")
    with pytest.raises(ValueError, match="Softwood"):
        m.SolidTimber("CL24")
