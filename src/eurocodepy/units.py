# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum

# ---------------- Base unit enums (scale to SI) ----------------


class ForceUnit(Enum):
    N = 1.0
    kN = 1000.0  # noqa: N815
    kgf = 9.80665
    tf = 9806.65


class LengthUnit(Enum):
    m = 1.0
    mm = 1e-3
    cm = 1e-2
    km = 1000.0
    inch = 0.0254
    foot = 0.3048
    yard = 0.9144
    mile = 1609.344


class TimeUnit(Enum):
    s = 1.0
    m = 60.0
    h = 3600.0
    ms = 0.001


class MassUnit(Enum):
    kg = 1.0
    t = 1e3
    pound = 0.45359237
    ounce = 0.028349523125


class TemperatureUnit(Enum):
    """Temperature scales. The value is ``(size of one degree in kelvin, name)``.

    The name keeps ``C`` and ``K`` apart (both have a degree of the same size: with the bare
    number ``Enum`` made one an alias of the other). The scales differ by an offset, which
    :meth:`UnitSystem.convert_temperature` applies; differences of temperature need only the scale.
    """

    K = (1.0, "kelvin")
    C = (1.0, "celsius")
    F = (5.0 / 9.0, "fahrenheit")

    @property
    def scale(self) -> float:
        """Size of one degree of this scale in kelvin."""
        return self.value[0]


class UnitType(Enum):
    FORCE = 0
    LENGTH = 1
    TIME = 2
    TEMPERATURE = 3
    MASS = 4
    PRESSURE = 5
    WORK = 6
    ENERGY = 7
    POWER = 8
    AREA = 9
    VOLUME = 10
    VELOCITY = 11
    ACCELERATION = 12
    MOMENT = 13
    DENSITY = 14
    FORCE_LENGTH = 15
    FORCE_VOLUME = 16


def _to_kelvin(value: float, unit: TemperatureUnit) -> float:
    if unit is TemperatureUnit.K:
        return value
    if unit is TemperatureUnit.C:
        return value + 273.15
    return (value - 32.0) * 5.0 / 9.0 + 273.15            # Fahrenheit


def _from_kelvin(value: float, unit: TemperatureUnit) -> float:
    if unit is TemperatureUnit.K:
        return value
    if unit is TemperatureUnit.C:
        return value - 273.15
    return (value - 273.15) * 9.0 / 5.0 + 32.0            # Fahrenheit


# ---------------- Unit system ----------------

@dataclass(frozen=True)
class UnitSystem:
    # multipliers to convert "your unit" -> SI
    force_unit: ForceUnit = ForceUnit.N
    distance_unit: LengthUnit = LengthUnit.m
    time_unit: TimeUnit = TimeUnit.s
    mass_unit: MassUnit = MassUnit.kg
    temperature_unit: TemperatureUnit = TemperatureUnit.K

    def convert_temperature(self,
            temperature: float,
            temp_to: TemperatureUnit) -> float:
        """Convert a temperature (a point on the scale, not a difference) to another scale.

        ``temperature`` is in this system's ``temperature_unit``; the result is in ``temp_to``.
        For differences of temperature use ``convert_to(..., UnitType.TEMPERATURE)``.
        """
        return _from_kelvin(_to_kelvin(temperature, self.temperature_unit), temp_to)

    # derived factors (your -> SI)
    @property
    def distance(self) -> float: return self.distance_unit.value

    @property
    def time(self) -> float: return self.time_unit.value

    @property
    def force(self) -> float: return self.force_unit.value

    @property
    def mass(self) -> float: return self.mass_unit.value

    @property
    def temperature(self) -> float: return self.temperature_unit.scale

    @property
    def area(self) -> float: return self.distance_unit.value ** 2

    @property
    def volume(self) -> float: return self.distance_unit.value ** 3

    @property
    def pressure(self) -> float: return self.force_unit.value / (self.distance_unit.value ** 2)

    @property
    def moment(self) -> float: return self.force_unit.value * self.distance_unit.value

    @property
    def force_length(self) -> float: return self.force_unit.value / self.distance_unit.value

    @property
    def force_volume(self) -> float: return self.force_unit.value / (self.distance_unit.value ** 3)

    @property
    def work(self) -> float:
        """Work factor: (your force * your length) -> J (N·m)."""
        return self.force_unit.value * self.distance_unit.value

    @property
    def energy(self) -> float:
        """Alias of work (in mechanics, same unit)."""
        return self.work

    @property
    def power(self) -> float:
        """Power factor: (your force * your length / your time) -> W."""
        return self.force_unit.value * self.distance_unit.value / self.time_unit.value

    @property
    def density(self) -> float:
        """Density factor: (your mass / your length^3) -> kg/m³."""
        return self.mass_unit.value / (self.distance_unit.value ** 3)

    @property
    def velocity(self) -> float:
        """Velocity factor: (your length / your time) -> m/s."""
        return self.distance_unit.value / self.time_unit.value

    @property
    def acceleration(self) -> float:
        """Acceleration factor: (your length / your time^2) -> m/s²."""
        return self.distance_unit.value / (self.time_unit.value ** 2)

    def convert_from(self, from_system: "UnitSystem", unit_type: UnitType) -> float:
        # convert to SI
        # convert from SI
        match unit_type:
            case UnitType.FORCE:
                return  from_system.force / self.force
            case UnitType.LENGTH:
                return  from_system.distance / self.distance
            case UnitType.PRESSURE:
                return  from_system.pressure / self.pressure
            case UnitType.MOMENT:
                return  from_system.moment / self.moment
            case UnitType.VELOCITY:
                return  from_system.velocity / self.velocity
            case UnitType.ACCELERATION:
                return  from_system.acceleration / self.acceleration
            case UnitType.AREA:
                return  from_system.area / self.area
            case UnitType.VOLUME:
                return  from_system.volume / self.volume
            case UnitType.TIME:
                return  from_system.time / self.time
            case UnitType.MASS:
                return  from_system.mass / self.mass
            case UnitType.FORCE_LENGTH:
                return  from_system.force_length / self.force_length
            case UnitType.FORCE_VOLUME:
                return  from_system.force_volume / self.force_volume
            case UnitType.WORK | UnitType.ENERGY:
                return  from_system.work / self.work
            case UnitType.POWER:
                return  from_system.power / self.power
            case UnitType.DENSITY:
                return  from_system.density / self.density
            case UnitType.TEMPERATURE:                  # temperature *difference*
                return  from_system.temperature / self.temperature
            case _:
                msg = f"unit type {unit_type!r} is not supported"
                raise ValueError(msg)

    def convert_to(self, to_system: "UnitSystem", unit_type: UnitType) -> float:
        # convert to SI
        # convert from SI
        match unit_type:
            case UnitType.FORCE:
                return self.force / to_system.force
            case UnitType.LENGTH:
                return self.distance / to_system.distance
            case UnitType.PRESSURE:
                return self.pressure / to_system.pressure
            case UnitType.MOMENT:
                return self.moment / to_system.moment
            case UnitType.VELOCITY:
                return self.velocity / to_system.velocity
            case UnitType.ACCELERATION:
                return self.acceleration / to_system.acceleration
            case UnitType.AREA:
                return self.area / to_system.area
            case UnitType.VOLUME:
                return self.volume / to_system.volume
            case UnitType.TIME:
                return self.time / to_system.time
            case UnitType.MASS:
                return self.mass / to_system.mass
            case UnitType.FORCE_LENGTH:
                return self.force_length / to_system.force_length
            case UnitType.FORCE_VOLUME:
                return self.force_volume / to_system.force_volume
            case UnitType.WORK | UnitType.ENERGY:
                return self.work / to_system.work
            case UnitType.POWER:
                return self.power / to_system.power
            case UnitType.DENSITY:
                return self.density / to_system.density
            case UnitType.TEMPERATURE:                  # temperature *difference*
                return self.temperature / to_system.temperature
            case _:
                msg = f"unit type {unit_type!r} is not supported"
                raise ValueError(msg)

    def to_si(self, value: float, factor: float) -> float:
        return value * factor

    def from_si(self, value_si: float, factor: float) -> float:
        return value_si / factor

# default variable (kN, m, s, K, kg)
Default = UnitSystem(force_unit=ForceUnit.kN)
SI = UnitSystem()
kN_mm = UnitSystem(force_unit=ForceUnit.kN, distance_unit=LengthUnit.mm)
kN_m = UnitSystem(force_unit=ForceUnit.kN)
N_mm = UnitSystem(force_unit=ForceUnit.N, distance_unit=LengthUnit.mm)


if __name__ == "__main__":
    original = SI
    converted = UnitSystem(distance_unit=LengthUnit.km, time_unit=TimeUnit.h)
    orig = 30.0 # cm
    conv = orig * converted.convert_from(from_system = original, unit_type = UnitType.VELOCITY)
    print(f"{orig=} {original.distance_unit.name} = {conv=} {converted.distance_unit.name}")