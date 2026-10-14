"""Bolt areas: a numeric diameter must not use the gross area for the thread."""
import pytest

from eurocodepy.ec3 import Bolt, BoltedConnection, SteelPlate, Steel


def _conn(bolt):
    return BoltedConnection(bolt, SteelPlate(10.0, Steel("S355"), 200.0))


def test_numeric_diameter_takes_the_standard_stress_area():
    assert Bolt(20, "8.8").Athread == pytest.approx(Bolt("M20", "8.8").Athread) == pytest.approx(2.45)
    assert _conn(Bolt(20, "8.8")).Ft_Rd() == pytest.approx(_conn(Bolt("M20", "8.8")).Ft_Rd())
    assert _conn(Bolt(20.0, "8.8")).Fv_Rd() == pytest.approx(94.08)


def test_non_standard_diameter_and_explicit_area():
    b = Bolt(19.0, "8.8")
    assert b.Athread == pytest.approx(0.78 * b.A) and b.Athread < b.A
    assert Bolt(19.0, "8.8", athread=2.0).Athread == 2.0


def test_weld_group_inertia_has_the_parallel_axis_terms():
    import numpy as np

    from eurocodepy.ec3 import Weld, WeldConnection

    # two vertical welds a = 5 mm, L = 100 mm, 100 mm apart
    g = WeldConnection()
    for x in (-50.0, 50.0):
        g.add(Weld(5.0, 100.0, "S355", x=x, orientation=np.pi / 2))
    assert g.area == pytest.approx(1000.0)
    assert (g.xg, g.yg) == pytest.approx((0.0, 0.0), abs=1e-9)
    assert g.inertia_xx == pytest.approx(2 * 5.0 * 100.0**3 / 12.0)               # along the welds
    assert g.inertia_yy == pytest.approx(2 * (500.0 * 50.0**2 + 100.0 * 5.0**3 / 12.0))
    assert g.w_el_xx_sup == pytest.approx(g.inertia_xx / 50.0)
    assert g.w_el_yy_inf == pytest.approx(g.inertia_yy / 50.0)


def test_weld_group_centroid_and_constructor_list():
    from eurocodepy.ec3 import Weld, WeldConnection

    a, b = Weld(4.0, 100.0, "S355", x=0.0, y=0.0), Weld(4.0, 100.0, "S355", x=0.0, y=60.0)
    g = WeldConnection([a, b])                              # the welds passed to the constructor count
    assert g.area == pytest.approx(800.0) and g.yg == pytest.approx(30.0)
    assert g.inertia_xx == pytest.approx(2 * (4.0**3 * 100.0 / 12.0 + 400.0 * 30.0**2))
    assert WeldConnection().inertia_xx == 0.0
