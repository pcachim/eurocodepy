"""Default EN 1990 factors per action: values, locale/category lookup, errors."""
import pytest

from eurocodepy.ec1 import ActionFactors, LoadType, action_factors


def test_permanent_and_variable_defaults():
    assert action_factors(LoadType.PERMANENT) == ActionFactors(1.0, 1.35, 1.0, 1.0, 1.0)
    assert action_factors("wind") == ActionFactors(0.0, 1.5, 0.6, 0.2, 0.0)
    assert action_factors(LoadType.TEMPERATURE).psi1 == 0.5


@pytest.mark.parametrize("cat,psi", [
    ("A", (0.7, 0.5, 0.3)), ("C", (0.7, 0.7, 0.6)), ("E", (1.0, 0.9, 0.8)),
    ("H", (0.0, 0.0, 0.0)), ("B2", (0.7, 0.5, 0.3)),
])
def test_live_categories_follow_the_database(cat, psi):
    f = action_factors(LoadType.LIVE, cat)
    assert (f.psi0, f.psi1, f.psi2) == psi
    assert f.gamma_unf == 1.5 and f.gamma_fav == 0.0
    assert action_factors("live", cat, locale="PT") == f


def test_live_without_category_is_generic():
    assert action_factors("live").psi0 == 0.7


def test_snow_altitude_variants():
    assert action_factors(LoadType.SNOW) == action_factors("snow", "<=1000")
    assert action_factors("snow", "<=1000")[2:] == (0.5, 0.2, 0.0)
    assert action_factors("snow", ">1000")[2:] == (0.7, 0.5, 0.2)


def test_construction_and_accidental():
    assert action_factors("construction")[2:] == (1.0, 0.9, 0.0)
    for k in (LoadType.EARTHQUAKE, LoadType.ACCIDENTAL, LoadType.FIRE):
        assert action_factors(k) == ActionFactors(0.0, 1.0, 0.0, 0.0, 0.0)


def test_every_loadtype_resolves():
    for lt in LoadType:
        action_factors(lt)


def test_errors():
    with pytest.raises(KeyError):
        action_factors("nope")
    with pytest.raises(KeyError):
        action_factors("live", "Z")
    with pytest.raises(KeyError):
        action_factors("snow", "500")


from eurocodepy.ec1 import live_load_values


@pytest.mark.parametrize("usage,qk,Qk", [
    ("A1", 2.0, 2.0), ("C2", 4.0, 4.0), ("D2", 5.0, 7.0), ("E1", 7.5, 7.0),
    ("F", 2.5, 20.0), ("G", 5.0, 90.0), ("H", 0.4, 1.0),
])
def test_live_load_values(usage, qk, Qk):
    v = live_load_values(usage)
    assert (v.q_k, v.Q_k) == (qk, Qk)
    assert v.q_k_min <= v.q_k <= v.q_k_max


def test_national_annex_values_differ_from_the_recommended():
    assert (live_load_values("B", "PT").q_k, live_load_values("B", "PT").Q_k) == (3.0, 4.0)
    assert live_load_values("F", "PT").Q_k == 15.0
    assert live_load_values("G", "PT").Q_k == 75.0
    assert live_load_values("E1", "PT") == live_load_values("E1", "EU")


def test_live_load_values_errors():
    with pytest.raises(KeyError):
        live_load_values("C")      # divided into C1..C5
    with pytest.raises(KeyError):
        live_load_values("I")      # no values of its own
    with pytest.raises(KeyError):
        live_load_values("Z")
