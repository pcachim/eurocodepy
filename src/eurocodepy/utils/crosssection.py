# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

import numpy as np


class CrossSection:
    """Base class for cross-sectional properties."""

    def area(self) -> float:
        """Calculate the cross-sectional area."""
        raise NotImplementedError("Subclasses must implement this method.")

    def inertia_z(self) -> float:
        """Calculate the second moment of inertia about the z-axis."""
        raise NotImplementedError("Subclasses must implement this method.")

    def inertia_y(self) -> float:
        """Calculate the second moment of inertia about the y-axis."""
        raise NotImplementedError("Subclasses must implement this method.")

    def bend_mod_z(self) -> float:
        """Calculate the bending modulus about the z-axis."""
        raise NotImplementedError("Subclasses must implement this method.")

    def bend_mod_y(self) -> float:
        """Calculate the bending modulus about the y-axis."""
        raise NotImplementedError("Subclasses must implement this method.")

    def radius_z(self) -> float:
        """Calculate the radius of gyration about the z-axis."""
        raise NotImplementedError("Subclasses must implement this method.")

    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis."""
        raise NotImplementedError("Subclasses must implement this method.")

    def polar_inertia(self) -> float:
        """Calculate the polar moment of inertia."""
        raise NotImplementedError("Subclasses must implement this method.")


class RectangularCrossSection(CrossSection):
    """Initialize a rectangular cross-section.

    Args:
        width: Width of the rectangle (horizontal dimension)
        height: Height of the rectangle (vertical dimension)

    """

    def __init__(self, width: float, height: float) -> None:  # noqa: D107
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
    def radius_z(self) -> float:
        """Calculate the radius of gyration about the z-axis (horizontal)."""
        return self.height / np.sqrt(12)

    @property
    def radius_y(self) -> float:
        """Calculate the radius of gyration about the y-axis (vertical)."""
        return self.width / np.sqrt(12)

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
