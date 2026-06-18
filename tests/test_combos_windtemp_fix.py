"""Regression test for the wind/temperature empty-group bug in ec1.combos.

Before the fix, get_ULS_combos / get_SLS_combos generated NO combinations when
there were neither wind nor temperature loads, because `wind_temp` collapsed to
an empty list and the variable-load loop never ran. A plain G+Q model therefore
produced zero ULS combinations.

Run on a Python >= 3.11 environment with eurocodepy importable:
    python test_combos_windtemp_fix.py
or under pytest:
    pytest test_combos_windtemp_fix.py
"""
from eurocodepy.ec1.combos import Loads, Load, LoadType, CombinationType


def _loads_GQ():
    loads = Loads()
    # name, load_type, gamma_fav, gamma_unf, psi0, psi1, psi2
    loads.add(Load("G", LoadType.PERMANENT, 1.0, 1.35, 1.0, 1.0, 1.0))
    loads.add(Load("Q", LoadType.LIVE,      0.0, 1.5,  0.7, 0.5, 0.3))
    return loads


def test_uls_with_no_wind_or_temperature():
    """G + Q (no wind, no temperature) must still produce a ULS combination."""
    uls = _loads_GQ().get_ULS_combos()
    assert uls, "expected at least one ULS combination for G+Q"
    # Expect 1.35 G + 1.5 Q among the generated combos.
    found = False
    for combo in uls.values():
        factors = {k: round(v, 3) for k, (_, v) in combo.factors.items()}
        if factors == {"G": 1.35, "Q": 1.5}:
            found = True
    assert found, f"1.35G + 1.5Q not generated; got {[c.factors for c in uls.values()]}"


def test_sls_with_no_wind_or_temperature():
    """SLS combinations must also be generated for G + Q."""
    sls = _loads_GQ().get_SLS_combos()
    assert sls, "expected at least one SLS combination for G+Q"


def test_wind_still_included_when_present():
    """A wind load must still appear in the combinations when present."""
    loads = _loads_GQ()
    loads.add(Load("W", LoadType.WIND, 0.0, 1.5, 0.6, 0.2, 0.0))
    uls = loads.get_ULS_combos()
    assert any("W" in combo.factors for combo in uls.values()), \
        "wind load missing from ULS combinations"


def _loads_GQW():
    loads = _loads_GQ()
    loads.add(Load("W", LoadType.WIND, 0.0, 1.5, 0.6, 0.2, 0.0))
    return loads


def _leading(combos, name):
    """True if some combo has *name* acting as the leading variable (factor 1.0)."""
    return any(
        round(combo.factors.get(name, (None, 0.0))[1], 3) == 1.0
        for combo in combos.values()
    )


def test_sls_k_alternates_leading_variable():
    """SLS-K must produce a combo for EACH leading variable (Q and W at 1.0).

    Regression guard for the mis-indented `if combo.name not in combinations`
    that previously kept only the last leading-variable combo.
    """
    sls = _loads_GQW().get_SLS_combos()
    sls_k = {n: c for n, c in sls.items() if str(c.type) == "SLS-K"}
    assert _leading(sls_k, "Q"), "no SLS-K combo with Q leading (factor 1.0)"
    assert _leading(sls_k, "W"), "no SLS-K combo with W leading (factor 1.0)"


def test_sls_fr_alternates_leading_variable():
    """SLS-FR must produce a combo for each leading variable (psi1)."""
    sls = _loads_GQW().get_SLS_combos()
    sls_fr = {n: c for n, c in sls.items() if str(c.type) == "SLS-FR"}
    # Q leading → factor psi1,Q = 0.5; W leading → psi1,W = 0.2.
    assert any(round(c.factors.get("Q", (None, 0))[1], 3) == 0.5 for c in sls_fr.values()), \
        "no SLS-FR combo with Q leading (psi1 = 0.5)"
    assert any(round(c.factors.get("W", (None, 0))[1], 3) == 0.2 for c in sls_fr.values()), \
        "no SLS-FR combo with W leading (psi1 = 0.2)"


if __name__ == "__main__":
    test_uls_with_no_wind_or_temperature()
    test_sls_with_no_wind_or_temperature()
    test_wind_still_included_when_present()
    test_sls_k_alternates_leading_variable()
    test_sls_fr_alternates_leading_variable()
    print("OK — all combo-fix checks passed")
