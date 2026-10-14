"""EN 1995-1-1: design values of a timber grade."""
import pytest

from eurocodepy.ec5.materials import LoadDuration, ServiceClass, SolidTimber


def test_design_values_report_kmod_and_the_design_strengths():
    t = SolidTimber("C24")
    d = t.design_values(ServiceClass.SC1, LoadDuration.MediumDuration)
    assert d["kmod"] == pytest.approx(0.8)              # Table 3.1, service class 1, medium term
    assert d["fmd"] == pytest.approx(0.8 * 24.0 / 1.3)  # Eq. 2.14
    assert d["safety"] == pytest.approx(1.3)


def test_combination_design_values_follow_the_shortest_action():
    from eurocodepy.ec1 import Load, LoadCombination, LoadType, Loads
    from eurocodepy.ec5.materials import GetTimberDesignValues

    loads = Loads()
    loads.add(Load("G", LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
    loads.add(Load("Q", LoadType.LIVE, 0.0, 1.5, 0.7, 0.5, 0.3))
    loads.add(Load("W", LoadType.WIND, 0.0, 1.5, 0.6, 0.2, 0.0))
    combos = list(loads.get_ULS_combos().values()) + list(loads.get_SLS_combos().values())
    values = GetTimberDesignValues(SolidTimber("C24"), combos)
    uls = {name: v for name, v in values.items() if v["design"]}
    assert len(uls) == len(loads.get_ULS_combos()) and len(values) > len(uls)
    for name, v in uls.items():
        expected = (LoadDuration.ShortDuration if "_W" in name else LoadDuration.MediumDuration)
        assert v["loadduration"] == expected
        assert v["kmod"] == pytest.approx(SolidTimber("C24").k_mod(ServiceClass.SC1, expected))
    sc3 = GetTimberDesignValues(SolidTimber("C24"), combos, ServiceClass.SC3)
    assert all(sc3[n]["kmod"] < uls[n]["kmod"] for n in uls)        # wetter: lower kmod

    only_g = LoadCombination("G", {"G": (Load("G", LoadType.PERMANENT, 1.0, 1.35, 0, 0, 0), 1.35)})
    assert GetTimberDesignValues(SolidTimber("C24"), [only_g])["G"]["loadduration"] == LoadDuration.Permanent
    manual = LoadCombination("m", {"G": 1.35}, loadduration=LoadDuration.LongDuration)
    assert GetTimberDesignValues(SolidTimber("C24"), [manual])["m"]["loadduration"] == LoadDuration.LongDuration
    with pytest.raises(ValueError, match="load duration"):
        GetTimberDesignValues(SolidTimber("C24"), [LoadCombination("x", {"G": 1.35})])
