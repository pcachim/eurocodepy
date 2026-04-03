# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, fields
from typing import Self

import numpy as np

from eurocodepy.units import Default, UnitSystem, UnitType

# ============================================================
# Base Class
# ============================================================


class BaseForce:
    """Base class providing arithmetic operators for dataclasses containing numeric fields and a unit system `u`.

    Designed to be immutable and safe for structural load workflows.
    """

    u: UnitSystem = Default

    # --------------------------------------------------------
    # Unit Conversion (must be implemented in subclasses)
    # --------------------------------------------------------
    def convert_to(self, unit_system: UnitSystem) -> Self:
        raise NotImplementedError

    # --------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------
    def _numeric_fields(self):
        return [
            f for f in fields(self)
            if f.name != "u"
        ]

    def _match_units(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            msg = (
                f"Cannot operate between {type(self).__name__} "
                f"and {type(other).__name__}"
            )
            raise TypeError(
                msg
            )

        if self.u != other.u:
            other = other.convert_to(self.u)

        return other

    def _operate(self, other: Self, op) -> Self:
        data = {}
        for f in self._numeric_fields():
            data[f.name] = op(
                getattr(self, f.name),
                getattr(other, f.name)
            )
        data["u"] = self.u
        return type(self)(**data)

    def _scale(self, scalar: float, op) -> Self:
        data = {}
        for f in self._numeric_fields():
            data[f.name] = op(getattr(self, f.name), scalar)
        data["u"] = self.u
        return type(self)(**data)

    # --------------------------------------------------------
    # Operators
    # --------------------------------------------------------
    def __add__(self, other: Self) -> Self:
        other = self._match_units(other)
        return self._operate(other, lambda a, b: a + b)

    def __sub__(self, other: Self) -> Self:
        other = self._match_units(other)
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


# ============================================================
# 1D Bar Forces
# ============================================================

@dataclass
class BarForce(BaseForce):
    n_x: float | np.ndarray = 0.0
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "BarForce":
        if self.u == unit_system:
            return self

        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)

        return BarForce(
            n_x=self.n_x * ffactor,
            u=unit_system,
        )


# ============================================================
# Frame (Beam/3D) Forces
# ============================================================

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
        if self.u == unit_system:
            return self

        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)
        mfactor = self.u.convert_to(unit_system, unit_type=UnitType.MOMENT)

        return FrameForce(
            n_x=self.n_x * ffactor,
            v_y=self.v_y * ffactor,
            v_z=self.v_z * ffactor,
            m_y=self.m_y * mfactor,
            m_z=self.m_z * mfactor,
            t_x=self.t_x * mfactor,
            u=unit_system,
        )


# ============================================================
# Slab Forces (Plate Resultants)
# ============================================================

@dataclass
class SlabForce(BaseForce):
    m_xx: float | np.ndarray
    m_yy: float | np.ndarray
    m_xy: float | np.ndarray
    v_xz: float | np.ndarray
    v_yz: float | np.ndarray
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "SlabForce":
        if self.u == unit_system:
            return self

        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        mfactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)

        return SlabForce(
            m_xx=self.m_xx * mfactor,
            m_yy=self.m_yy * mfactor,
            m_xy=self.m_xy * mfactor,
            v_xz=self.v_xz * ffactor,
            v_yz=self.v_yz * ffactor,
            u=unit_system,
        )


# ============================================================
# Plane Forces (Membrane)
# ============================================================

@dataclass
class PlaneForce(BaseForce):
    n_xx: float | np.ndarray
    n_yy: float | np.ndarray
    n_xy: float | np.ndarray
    u: UnitSystem = Default

    def convert_to(self, unit_system: UnitSystem) -> "PlaneForce":
        if self.u == unit_system:
            return self

        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)

        return PlaneForce(
            n_xx=self.n_xx * ffactor,
            n_yy=self.n_yy * ffactor,
            n_xy=self.n_xy * ffactor,
            u=unit_system,
        )


# ============================================================
# Shell Forces (Membrane + Bending)
# ============================================================

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
        if self.u == unit_system:
            return self

        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        mfactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE)

        return ShellForce(
            n_xx=self.n_xx * ffactor,
            n_yy=self.n_yy * ffactor,
            n_xy=self.n_xy * ffactor,
            m_xx=self.m_xx * mfactor,
            m_yy=self.m_yy * mfactor,
            m_xy=self.m_xy * mfactor,
            v_xz=self.v_xz * ffactor,
            v_yz=self.v_yz * ffactor,
            u=unit_system,
        )
