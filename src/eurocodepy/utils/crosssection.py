# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
from enum import StrEnum

import numpy as np


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
        """Calculate the polar moment of inertia."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    @property
    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)


class RectangularCrossSection(CrossSection):
    """Initialize a rectangular cross-section.

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
        """Calculate the second moment of inertia about the z-axis (horizontal)."""
        return (self.width * self.height**3) / 12

    @property
    def inertia_y(self) -> float:
        """Calculate the second moment of inertia about the y-axis (vertical)."""
        return (self.height * self.width**3) / 12

    @property
    def bend_mod_y(self) -> float:
        """Calculate the bending modulus about the z-axis (horizontal)."""
        return (self.width * self.height**2) / 6

    @property
    def bend_mod_z(self) -> float:
        """Calculate the bending modulus about the y-axis (vertical)."""
        return (self.height * self.width**2) / 6

    @property
    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis (vertical)."""
        return self.height / np.sqrt(12)

    @property
    def radius_z(self) -> float:
        """Calculate the radius of gyration about the z-axis (horizontal)."""
        return self.width / np.sqrt(12)

    @property
    def torsional_inertia(self) -> float:
        """Calculate the torsional inertia."""
        b: float = self.width
        h: float = self.height
        return (b * h**3) * (1.0 / 3.0) * (1.0 - 0.672 * (h / b) + 0.3 * (h / b)**2)

    @property
    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        return self.inertia_z + self.inertia_y

    def __repr__(self) -> str:  # noqa: D105
        return f"RectangularSection(width={self.width}, height={self.height})"


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
        return self.radius / np.sqrt(2)

    @property
    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis."""
        return self.radius / np.sqrt(2)

    @property
    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        return (np.pi * (self.radius ** 4)) / 2

    def __repr__(self) -> str:  # noqa: D105
        return f"CircularSection(diameter={self.diameter})"
