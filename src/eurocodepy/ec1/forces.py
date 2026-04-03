# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import ClassVar, Self

import numpy as np
from numpy.typing import NDArray

from eurocodepy.units import Default, UnitSystem, UnitType


@dataclass
class BaseForce:
    """Generic vectorised structural force container.

    Internal representation:
        forces → (n_components, n_cases)
    """

    forces: NDArray
    u: UnitSystem = Default

    # Must be defined in subclasses
    COMPONENTS: ClassVar[tuple[str, ...]] = ()
    UNIT_TYPES: ClassVar[tuple[UnitType, ...]] = ()

    # --------------------------------------------------------
    # Shared Initializer
    # --------------------------------------------------------
    @classmethod
    def _build(
        cls,
        *components: float | NDArray,
        u: UnitSystem = Default,
    ) -> Self:

        if len(components) != len(cls.COMPONENTS):
            msg = f"{cls.__name__} expects {len(cls.COMPONENTS)} components."
            raise ValueError(
                msg
            )

        arrays = [np.asarray(c, float) for c in components]

        # Scalars → 1D
        arrays = [a.reshape(1) if a.ndim == 0 else a for a in arrays]

        # Strict shape check
        shapes = {a.shape for a in arrays if a.size > 1}

        if len(shapes) > 1:
            msg = f"All components must have identical shape. Got {shapes}"
            raise ValueError(
                msg,
            )

        shape = shapes.pop() if shapes else (1,)

        expanded = [
            np.full(shape, a.item()) if a.size == 1 else a
            for a in arrays
        ]

        forces = np.vstack(expanded)

        return cls(forces=forces, u=u)

    # --------------------------------------------------------
    # Load-case slicing
    # --------------------------------------------------------
    def __getitem__(self, item) -> Self:
        selected = self.forces[:, item]

        if selected.ndim == 1:
            selected = selected[:, None]

        return type(self)(forces=selected, u=self.u)

    # --------------------------------------------------------
    # Envelope utilities
    # --------------------------------------------------------
    def envelope_max(self) -> Self:
        return type(self)(
            forces=np.max(self.forces, axis=1, keepdims=True),
            u=self.u,
        )

    def envelope_min(self) -> Self:
        return type(self)(
            forces=np.min(self.forces, axis=1, keepdims=True),
            u=self.u,
        )

    def merge(self, other: Self) -> Self:
        """Return a new BaseForce merged."""
        if type(self) is not type(other):
            msg = "Cannot combine different force types."
            raise TypeError(msg)

        if self.u != other.u:
            other = other.convert_to(self.u)

        merged = np.concatenate((self.forces, other.forces), axis=1)

        return type(self)(forces=merged, u=self.u)

    @classmethod
    def combine(cls, one: Self, other: Self) -> Self:
        if type(one) is not type(other):
            msg = "Cannot combine different force types."
            raise TypeError(msg)

        if one.u != other.u:
            other = other.convert_to(one.u)

        merged = np.concatenate((one.forces, other.forces), axis=1)

        return type(one)(forces=merged, u=one.u)

    # --------------------------------------------------------
    # Unit conversion (generic)
    # --------------------------------------------------------
    def convert_to(self, unit_system: UnitSystem) -> Self:
        if self.u == unit_system:
            return self

        scale = np.array([
            self.u.convert_to(unit_system, ut)
            for ut in self.UNIT_TYPES
        ])[:, None]

        return type(self)(
            forces=self.forces * scale,
            u=unit_system,
        )

    # --------------------------------------------------------
    # Number of load cases
    # --------------------------------------------------------
    @property
    def n_cases(self) -> int:
        return self.forces.shape[1]

    # --------------------------------------------------------
    # Dynamic component properties
    # --------------------------------------------------------
    def __getattr__(self, name: str):
        if name in self.COMPONENTS:
            idx = self.COMPONENTS.index(name)
            return self.forces[idx]
        raise AttributeError(name)


@dataclass
class FrameForce(BaseForce):

    COMPONENTS = ("n_x", "v_y", "v_z", "m_y", "m_z", "t_x")

    UNIT_TYPES = (
        UnitType.FORCE,
        UnitType.FORCE,
        UnitType.FORCE,
        UnitType.MOMENT,
        UnitType.MOMENT,
        UnitType.MOMENT,
    )

    def __init__(
        self,
        n_x=0.0,
        v_y=0.0,
        v_z=0.0,
        m_y=0.0,
        m_z=0.0,
        t_x=0.0,
        u: UnitSystem = Default,
        forces=None,
    ):
        if forces is not None:
            super().__init__(forces=forces, u=u)
        else:
            obj = self._build(n_x, v_y, v_z, m_y, m_z, t_x, u=u)
            self.forces = obj.forces
            self.u = obj.u


@dataclass
class SlabForce(BaseForce):

    COMPONENTS = ("m_xx", "m_yy", "m_xy", "v_xz", "v_yz")

    UNIT_TYPES = (
        UnitType.MOMENT,
        UnitType.MOMENT,
        UnitType.MOMENT,
        UnitType.FORCE_LENGTH,
        UnitType.FORCE_LENGTH,
    )

    def __init__(self, m_xx=0.0, m_yy=0.0, m_xy=0.0,
                 v_xz=0.0, v_yz=0.0,
                 u: UnitSystem = Default, forces=None):

        if forces is not None:
            super().__init__(forces=forces, u=u)
        else:
            obj = self._build(m_xx, m_yy, m_xy, v_xz, v_yz, u=u)
            self.forces = obj.forces
            self.u = obj.u


@dataclass
class PlaneForce(BaseForce):

    COMPONENTS = ("n_xx", "n_yy", "n_xy")

    UNIT_TYPES = (
        UnitType.FORCE_LENGTH,
        UnitType.FORCE_LENGTH,
        UnitType.FORCE_LENGTH,
    )

    def __init__(self, n_xx=0.0, n_yy=0.0, n_xy=0.0,
                 u: UnitSystem = Default, forces=None):

        if forces is not None:
            super().__init__(forces=forces, u=u)
        else:
            obj = self._build(n_xx, n_yy, n_xy, u=u)
            self.forces = obj.forces
            self.u = obj.u


@dataclass
class ShellForce(BaseForce):

    COMPONENTS = (
        "n_xx", "n_yy", "n_xy",
        "m_xx", "m_yy", "m_xy",
        "v_xz", "v_yz",
    )

    UNIT_TYPES = (
        UnitType.FORCE_LENGTH,
        UnitType.FORCE_LENGTH,
        UnitType.FORCE_LENGTH,
        UnitType.MOMENT,
        UnitType.MOMENT,
        UnitType.MOMENT,
        UnitType.FORCE_LENGTH,
        UnitType.FORCE_LENGTH,
    )

    def __init__(
        self,
        n_xx=0.0, n_yy=0.0, n_xy=0.0,
        m_xx=0.0, m_yy=0.0, m_xy=0.0,
        v_xz=0.0, v_yz=0.0,
        u: UnitSystem = Default,
        forces=None,
    ):
        if forces is not None:
            super().__init__(forces=forces, u=u)
        else:
            obj = self._build(
                n_xx, n_yy, n_xy,
                m_xx, m_yy, m_xy,
                v_xz, v_yz,
                u=u,
            )
            self.forces = obj.forces
            self.u = obj.u


def combine(f1: BaseForce, f2: BaseForce) -> BaseForce:
    """Safely merge load cases from two force objects.

    - Must be same class
    - Units are matched automatically
    - Concatenates load cases along axis=1

    """  # noqa: DOC201, DOC501
    if type(f1) is not type(f2):
        msg = (
            f"Cannot combine {type(f1).__name__} "
            f"with {type(f2).__name__}"
        )
        raise TypeError(
            msg
        )

    # Match units
    if f1.u != f2.u:
        f2 = f2.convert_to(f1.u)

    # Safety check: same number of components
    if f1.forces.shape[0] != f2.forces.shape[0]:
        msg = "Force component mismatch."
        raise ValueError(
            msg,
        )

    merged = np.concatenate(
        (f1.forces, f2.forces),
        axis=1,
    )

    return type(f1)(forces=merged, u=f1.u)
