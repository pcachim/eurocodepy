# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
import numpy as np

from eurocodepy._compat import StrEnum


class CrossSectionShape(StrEnum):
    """Enumeration of cross-section shapes.
 
    Attributes
    ----------
    RECTANGULAR : str
        Rectangular cross-section shape.
    CIRCULAR : str
        Circular cross-section shape.
    GENERIC : str
        Generic cross-section shape.

    """

    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    GENERIC = "generic"


class CrossSection:
    """Base class for cross-sectional properties."""

    shape: CrossSectionShape = CrossSectionShape("generic")

    width = 0.0
    height = 0.0
    diameter = 0.0
    radius = 0.0

    @property
    def area(self) -> float:
        """Calculate the cross-sectional area."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def inertia_z(self) -> float:
        """Calculate the second moment of inertia about the z-axis."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def inertia_y(self) -> float:
        """Calculate the second moment of inertia about the y-axis."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def bend_mod_z(self) -> float:
        """Calculate the bending modulus about the z-axis."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def bend_mod_y(self) -> float:
        """Calculate the bending modulus about the y-axis."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def radius_z(self) -> float:
        """Calculate the radius of gyration about the z-axis."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def torsional_inertia(self) -> float:
        """Calculate the St-Venant torsional constant ``I_t``."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def torsion_modulus(self) -> float:
        """Calculate the torsional section modulus (``τ_tor,max = T/W_t``)."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)


class RectangularCrossSection(CrossSection):
    """Initialize a rectangular cross-section.

    Axes follow EN 1995-1-1: ``y`` is the strong axis (``I_y = b·h³/12``) and
    ``z`` the weak axis (``I_z = h·b³/12``).

    Args:
        width: Width of the rectangle (horizontal dimension)
        height: Height of the rectangle (vertical dimension)

    """

    def __init__(self, width: float, height: float) -> None:  # noqa: D107
        self.shape = CrossSectionShape.RECTANGULAR
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        """Calculate the cross-sectional area."""
        return self.width * self.height

    @property
    def inertia_z(self) -> float:
        """Calculate the second moment of inertia about the z-axis (weak axis)."""
        return (self.height * self.width**3) / 12

    @property
    def inertia_y(self) -> float:
        """Calculate the second moment of inertia about the y-axis (strong axis)."""
        return (self.width * self.height**3) / 12

    @property
    def bend_mod_y(self) -> float:
        """Calculate the bending modulus about the y-axis (strong axis)."""
        return (self.width * self.height**2) / 6

    @property
    def bend_mod_z(self) -> float:
        """Calculate the bending modulus about the z-axis (weak axis)."""
        return (self.height * self.width**2) / 6

    @property
    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis (strong axis)."""
        return self.height / np.sqrt(12)

    @property
    def radius_z(self) -> float:
        """Calculate the radius of gyration about the z-axis (weak axis)."""
        return self.width / np.sqrt(12)

    @property
    def torsional_inertia(self) -> float:
        """Calculate the St-Venant torsional constant ``I_t``.

        ``I_t = h·b³/3 · (1 − 0.63·b/h + 0.052·(b/h)⁵)`` with ``h`` the larger
        and ``b`` the smaller side (the sides are ordered, so the result does
        not depend on which one is called width).
        """
        b, h = sorted((self.width, self.height))
        r = b / h
        return h * b**3 / 3.0 * (1.0 - 0.63 * r + 0.052 * r**5)

    @property
    def torsion_modulus(self) -> float:
        """Calculate the torsional section modulus ``W_t`` (isotropic rectangle).

        ``W_t = α·h·b²`` with ``h`` the larger and ``b`` the smaller side and
        ``α ≈ (1/3)·(1 − 0.672·b/h + 0.3·(b/h)²)``. The maximum St-Venant shear
        stress, at the middle of the long side, is ``τ_tor = T/W_t`` (α = 0.208
        for a square, → 1/3 for a thin rectangle; within ±1.5 % of the exact
        series for any ``b/h``).
        """
        b, h = sorted((self.width, self.height))
        r = b / h
        alpha = (1.0 / 3.0) * (1.0 - 0.672 * r + 0.3 * r**2)
        return alpha * h * b**2

    @property
    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        return self.inertia_z + self.inertia_y

    def __repr__(self) -> str:  # noqa: D105
        return f"RectangularCrossSection(width={self.width}, height={self.height})"


class CircularCrossSection(CrossSection):
    """Initialize a circular cross-section.

    Args:
        diameter: Diameter of the circle

    """

    def __init__(self, diameter: float) -> None:  # noqa: D107
        self.shape = CrossSectionShape.CIRCULAR
        self.diameter = diameter
        self.radius = diameter / 2

    @property
    def area(self) -> float:
        """Calculate the cross-sectional area."""
        return np.pi * (self.radius ** 2)

    @property
    def inertia_z(self) -> float:
        """Calculate the second moment of inertia about the z-axis."""
        return (np.pi * (self.radius ** 4)) / 4

    @property
    def inertia_y(self) -> float:
        """Calculate the second moment of inertia about the y-axis."""
        return (np.pi * (self.radius ** 4)) / 4

    @property
    def bend_mod_z(self) -> float:
        """Calculate the bending modulus about the z-axis."""
        return (np.pi * (self.radius ** 3)) / 4

    @property
    def bend_mod_y(self) -> float:
        """Calculate the bending modulus about the y-axis."""
        return (np.pi * (self.radius ** 3)) / 4

    @property
    def radius_z(self) -> float:
        """Calculate the radius of gyration about the z-axis."""
        return self.radius / 2

    @property
    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis."""
        return self.radius / 2

    @property
    def torsional_inertia(self) -> float:
        """Calculate the torsional constant (= polar moment of inertia)."""
        return (np.pi * (self.radius ** 4)) / 2

    @property
    def torsion_modulus(self) -> float:
        """Calculate the torsional section modulus ``W_t = π·d³/16``."""
        return (np.pi * (self.radius ** 3)) / 2

    @property
    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        return (np.pi * (self.radius ** 4)) / 2

    def __repr__(self) -> str:  # noqa: D105
        return f"CircularCrossSection(diameter={self.diameter})"
