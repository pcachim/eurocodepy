"""Unit systems: factors, conversions between systems, temperatures, forces and stresses."""
import pytest

from eurocodepy.ec1 import FrameForce, PlaneForce, ShellForce, SlabForce
from eurocodepy.ec1.stresses import Stresses2d, Stresses3d
from eurocodepy.units import (
    SI, ForceUnit, LengthUnit, N_mm, TemperatureUnit, TimeUnit, UnitSystem, UnitType, kN_m, kN_mm,
)

ALL_TYPES = list(UnitType)


def test_si_values_of_each_system():
    assert (kN_mm.force, kN_mm.distance, kN_mm.pressure) == pytest.approx((1000.0, 1e-3, 1e9))      # kN/mm² = GPa
    assert (N_mm.force, N_mm.distance, N_mm.pressure) == pytest.approx((1.0, 1e-3, 1e6))             # N/mm² = MPa
    assert kN_m.pressure == pytest.approx(1000.0)                                                    # kPa
    assert kN_m.force_length == pytest.approx(1000.0) and kN_m.moment == pytest.approx(1000.0)


@pytest.mark.parametrize(("unit_type", "expected"), [
    (UnitType.FORCE, 1e-3), (UnitType.LENGTH, 1e3), (UnitType.MOMENT, 1.0), (UnitType.PRESSURE, 1e-9),
    (UnitType.FORCE_LENGTH, 1e-6), (UnitType.AREA, 1e6), (UnitType.VOLUME, 1e9),
    (UnitType.WORK, 1.0), (UnitType.ENERGY, 1.0), (UnitType.FORCE_VOLUME, 1e-12),
])
def test_si_to_kn_mm(unit_type, expected):
    assert SI.convert_to(kN_mm, unit_type) == pytest.approx(expected)


@pytest.mark.parametrize("unit_type", ALL_TYPES)
def test_convert_to_and_convert_from_are_inverse_and_consistent(unit_type):
    a, b = UnitSystem(ForceUnit.kN, LengthUnit.m, TimeUnit.s), UnitSystem(ForceUnit.N, LengthUnit.mm, TimeUnit.h)
    to = a.convert_to(b, unit_type)
    assert to * b.convert_to(a, unit_type) == pytest.approx(1.0)
    assert b.convert_from(a, unit_type) == pytest.approx(to)        # "a -> b" read from either side


def test_new_unit_types_are_not_silently_zero():
    from eurocodepy.units import MassUnit

    km_h = UnitSystem(distance_unit=LengthUnit.km, time_unit=TimeUnit.h)
    tonne = UnitSystem(mass_unit=MassUnit.t)
    assert SI.convert_to(km_h, UnitType.VELOCITY) == pytest.approx(3.6)
    assert SI.convert_to(tonne, UnitType.DENSITY) == pytest.approx(1e-3)               # kg/m³ -> t/m³
    assert SI.convert_to(UnitSystem(ForceUnit.kN, LengthUnit.m, TimeUnit.s), UnitType.POWER) == pytest.approx(1e-3)
    for t in ALL_TYPES:
        assert SI.convert_to(kN_mm, t) != 0.0


def test_celsius_and_kelvin_are_different_scales():
    assert TemperatureUnit.C is not TemperatureUnit.K and len(list(TemperatureUnit)) == 3


def test_temperature_scales():
    k = UnitSystem(temperature_unit=TemperatureUnit.K)
    c = UnitSystem(temperature_unit=TemperatureUnit.C)
    f = UnitSystem(temperature_unit=TemperatureUnit.F)
    assert k.convert_temperature(300.0, TemperatureUnit.C) == pytest.approx(26.85)
    assert k.convert_temperature(273.15, TemperatureUnit.F) == pytest.approx(32.0)
    assert c.convert_temperature(20.0, TemperatureUnit.F) == pytest.approx(68.0)
    assert c.convert_temperature(0.0, TemperatureUnit.K) == pytest.approx(273.15)
    assert f.convert_temperature(212.0, TemperatureUnit.C) == pytest.approx(100.0)
    assert f.convert_temperature(32.0, TemperatureUnit.K) == pytest.approx(273.15)
    assert c.convert_temperature(25.0, TemperatureUnit.C) == pytest.approx(25.0)
    # a temperature difference has no offset: 1 K = 1 °C = 1.8 °F
    assert c.convert_to(f, UnitType.TEMPERATURE) == pytest.approx(1.0 / (5.0 / 9.0))


def test_frame_force_conversion():
    f = FrameForce(n_x=10.0, m_y=5.0, u=kN_m).convert_to(N_mm)
    assert f.forces.ravel().tolist() == pytest.approx([1e4, 0, 0, 5e6, 0, 0])      # N, N·mm


def test_forces_per_unit_width_convert_as_forces():
    # 100 kN/m = 100 N/mm; 20 kNm/m = 20 kN = 20 000 N·mm/mm
    plane = PlaneForce(n_xx=100.0, u=kN_m).convert_to(N_mm)
    assert plane.forces[0, 0] == pytest.approx(100.0)
    slab = SlabForce(m_xx=20.0, v_xz=5.0, u=kN_m).convert_to(N_mm)
    assert slab.forces[0, 0] == pytest.approx(20000.0) and slab.forces[3, 0] == pytest.approx(5.0)
    shell = ShellForce(n_xx=100.0, m_xx=20.0, v_xz=5.0, u=kN_m).convert_to(N_mm)
    assert shell.forces.ravel()[[0, 3, 6]].tolist() == pytest.approx([100.0, 20000.0, 5.0])
    back = shell.convert_to(kN_m)
    assert back.forces.ravel()[[0, 3, 6]].tolist() == pytest.approx([100.0, 20.0, 5.0])


def test_merge_of_forces_in_different_systems():
    a = ShellForce(m_xx=20.0, u=kN_m)
    b = ShellForce(m_xx=20000.0, u=N_mm)                     # the same moment per metre
    merged = a.merge(b)
    assert merged.forces[3].tolist() == pytest.approx([20.0, 20.0])


def test_stresses_convert_and_add_across_systems():
    a = Stresses3d(sig_xx=10.0, tau_xy=2.0, u=kN_m)           # kN/m²
    b = a.convert_to(N_mm)
    assert (b.sig_xx, b.tau_xy) == pytest.approx((0.01, 0.002)) and b.u == N_mm
    assert a.sig_xx == 10.0                                    # the original is untouched
    c = Stresses3d(sig_xx=5.0, u=N_mm)                         # 5 N/mm² = 5000 kN/m²
    assert (a + c).sig_xx == pytest.approx(5010.0) and (c + a).sig_xx == pytest.approx(5.01)
    assert (c - a).sig_xx == pytest.approx(4.99)
    assert Stresses2d(sig_xx=3.0, u=kN_m).convert_to(SI).sig_xx == pytest.approx(3000.0)
