"""wind_get_params / seismic_get_params: values, errors, and no mutation of the database."""
import copy

import pytest

from eurocodepy import dbase
from eurocodepy.national_parameters import seismic_get_params, wind_get_params


def test_seismic_returns_a_copy_and_leaves_the_database_untouched():
    before = copy.deepcopy(dbase.SeismicLoads)
    a = seismic_get_params("PT", "PT1", "A", "ii")
    assert a["ImportanceCoef"] == 1.0
    assert a["a_g1"] == 1.0
    assert dbase.SeismicLoads == before
    assert "ImportanceCoef" not in dbase.SeismicLoads["Locale"]["PT"]["Spectrum"]["PT1"]["A"]
    # editing the result does not edit the database
    a["S_max"] = 99.0
    assert dbase.SeismicLoads["Locale"]["PT"]["Spectrum"]["PT1"]["A"]["S_max"] == 1.0


def test_seismic_importance_coefficient_follows_each_call():
    assert seismic_get_params("pt", "pt1", "a", "I")["ImportanceCoef"] == 0.65
    assert seismic_get_params("PT", "PT1", "A", "iv")["ImportanceCoef"] == 1.95
    assert seismic_get_params("PT", "PT1", "A", "ii")["ImportanceCoef"] == 1.0


@pytest.mark.parametrize(("args", "match", "valid"), [
    (("XX", "PT1", "A", "ii"), "Invalid code", "PT"),
    (("PT", "PT9", "A", "ii"), "Invalid seismic type", "PT2"),
    (("PT", "PT1", "Z", "ii"), "Invalid soil type", "'E'"),
    (("PT", "PT1", "A", "x"), "Invalid importance class", "'iv'"),
])
def test_seismic_errors_list_the_valid_values(args, match, valid):
    with pytest.raises(ValueError, match=match) as exc:
        seismic_get_params(*args)
    assert valid in str(exc.value)


def test_wind_values():
    vb0, zmin, z0, z0ii = wind_get_params("PT", "ZonaA", "II")
    assert (zmin, z0, z0ii) == (
        dbase.WindLoads["locale"]["PT"]["terrain"]["II"]["zmin"],
        dbase.WindLoads["locale"]["PT"]["terrain"]["II"]["z0"],
        dbase.WindLoads["locale"]["PT"]["terrain"]["II"]["z0"])
    assert vb0 == dbase.WindLoads["locale"]["PT"]["base_velocity"]["ZonaA"]["vb0"]
    assert wind_get_params("pt", "ZonaA", "ii") == (vb0, zmin, z0, z0ii)


@pytest.mark.parametrize(("args", "match", "valid"), [
    (("XX", "ZonaA", "II"), "Invalid code", "EU"),
    (("PT", "ZonaX", "II"), "Invalid wind zone", "ZonaB"),
    (("PT", "ZonaA", "V"), "Invalid terrain", "'IV'"),
])
def test_wind_errors_list_the_valid_values(args, match, valid):
    with pytest.raises(ValueError, match=match) as exc:
        wind_get_params(*args)
    assert valid in str(exc.value)
