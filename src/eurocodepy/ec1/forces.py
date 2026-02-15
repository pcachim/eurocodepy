# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
from dataclasses import dataclass, fields, replace
from enum import Enum
from typing import Self

import numpy as np

from eurocodepy.units import UnitSystem, SI, Default, UnitType


class BaseForce:
    """
    Provides +, -, *, / operators for dataclasses
    that contain numeric fields and a 'u' UnitSystem.
    """

    def convert_to(self, unit_system: UnitSystem) -> "BaseForce":
        return self

    # --------------------
    # Internal helpers
    # --------------------
    def _numeric_field_names(self):
        return [
            f.name for f in fields(self)
            if f.name != "u"
        ]

    def _check_units(self, other: Self):
        if self.u != other.u:
            raise ValueError("Unit systems must match before operations.")

    def _match_units(self, other):
        if self.u != other.u:
            other.convert_to(self.u)
        return other

    def _operate(self, other, op):
        data = {}
        for name in self._numeric_field_names():
            data[name] = op(getattr(self, name), getattr(other, name))
        data["u"] = self.u
        return replace(self, **data)

    def _scale(self, scalar, op):
        data = {}
        for name in self._numeric_field_names():
            data[name] = op(getattr(self, name), scalar)
        data["u"] = self.u
        return replace(self, **data)

    # --------------------
    # Operators
    # --------------------
    def __add__(self, other: Self) -> Self:
        self._match_units(other)
        return self._operate(other, lambda a, b: a + b)

    def __sub__(self, other: Self) -> Self:
        self._match_units(other)
        return self._operate(other, lambda a, b: a - b)

    def __mul__(self, scalar: float) -> Self:
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return self._scale(scalar, lambda a, b: a * b)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Self:
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return self._scale(scalar, lambda a, b: a / b)


@dataclass
class BarForce(BaseForce):
    n_x: float | np.ndarray = 0.0
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "BarForce":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)
        self.n_x *= ffactor
        self.u = unit_system
        return self


@dataclass
class FrameForce(BaseForce):
    n_x: float | np.ndarray = 0.0
    m_y: float | np.ndarray = 0.0
    m_z: float | np.ndarray = 0.0
    v_y: float | np.ndarray = 0.0
    v_z: float | np.ndarray = 0.0
    t_x: float | np.ndarray = 0.0
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "FrameForce":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)
        mfactor = self.u.convert_to(unit_system, unit_type=UnitType.MOMENT)
        self.n_x *= ffactor
        self.v_y *= ffactor
        self.v_z *= ffactor
        self.m_y *= mfactor
        self.m_z *= mfactor
        self.t_x *= mfactor
        self.u = unit_system
        return self


@dataclass
class SlabForce(BaseForce):
    m_xx: float | np.ndarray
    m_yy: float | np.ndarray
    m_xy: float | np.ndarray
    v_xz: float | np.ndarray
    v_yz: float | np.ndarray
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "SlabForce":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        mfactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)
        self.m_xx *= mfactor
        self.m_yy *= mfactor
        self.m_xy *= mfactor
        self.v_xz *= ffactor
        self.v_yz *= ffactor
        self.u = unit_system
        return self


@dataclass
class PlaneForce(BaseForce):
    n_xx: float | np.ndarray
    n_yy: float | np.ndarray
    n_xy: float | np.ndarray
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "PlaneForce":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        self.n_xx *= ffactor
        self.n_yy *= ffactor
        self.n_xy *= ffactor
        self.u = unit_system
        return self


@dataclass
class ShellForce(BaseForce):
    n_xx: float | np.ndarray
    n_yy: float | np.ndarray
    n_xy: float | np.ndarray
    m_xx: float | np.ndarray
    m_yy: float | np.ndarray
    m_xy: float | np.ndarray
    v_xz: float | np.ndarray
    v_yz: float | np.ndarray
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "ShellForce":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        mfactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)
        self.m_xx *= mfactor
        self.m_yy *= mfactor
        self.m_xy *= mfactor        
        self.n_xx *= ffactor
        self.n_yy *= ffactor
        self.n_xy *= ffactor
        self.v_xz *= ffactor
        self.v_yz *= ffactor
        self.u = unit_system
        return self
