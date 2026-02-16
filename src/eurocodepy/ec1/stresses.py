# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
from eurocodepy.utils.stress import invariants

import math
import operator
from dataclasses import dataclass, fields, replace
from enum import Enum
from typing import Self

import numpy as np

from eurocodepy.units import Default, UnitSystem, UnitType


class FailureCriteria(Enum):
    """Enum for failure criteria."""

    MOHR_COULOMB = "Mohr-Coulomb"
    MOHR_CIRCLE = "Mohr Circle"
    MAX_SHEAR = "Max Shear Stress"
    MAX_PRINCIPAL = "Max Principal Stress"
    MIN_PRINCIPAL = "Min Principal Stress"
    ELLIPTIC = "Elliptic"
    HENCKY = "Hencky"
    RANKINE = "Rankine"
    VON_MISES = "Von Mises"
    TREFFTZ = "Trefftz"
    CONCRETE = "Concrete"


class Invariant(Enum):
    """Enum for stress invariants."""

    I1 = "I1"
    J2 = "J2"
    J3 = "J3"
    MEAN_STRESS = "Mean Stress"
    EQV_STRESS = "Equivalent Stress"
    LODE_R = "Lode R"
    LODE_Z = "Lode Z"
    LODE_THETA = "Lode Theta"
    COS3T = "Cos(3Theta)"
    TRIAXIALITY = "Triaxiality"


class BaseStress:
    """Provide +, -, *, / operators for dataclasses.

    that contain numeric fields and a 'u' UnitSystem.

    """

    def convert_to(self, unit_system: UnitSystem) -> "BaseStress":
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
        return self._operate(other, operator.add)

    def __sub__(self, other: Self) -> Self:
        self._match_units(other)
        return self._operate(other, operator.sub)

    def __mul__(self, scalar: float) -> Self:
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return self._scale(scalar, operator.mul)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Self:
        """Divide by a scalar."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if scalar == 0:
            msg = "Cannot divide by zero."
            raise ZeroDivisionError(msg)
        return self._scale(scalar, operator.truediv)


@dataclass
class Stresses3d(BaseStress):
    sig_xx: float | np.ndarray = 0.0
    sig_yy: float | np.ndarray = 0.0
    sig_zz: float | np.ndarray = 0.0
    tau_xy: float | np.ndarray = 0.0
    tau_yz: float | np.ndarray = 0.0
    tau_zx: float | np.ndarray = 0.0
    u: UnitSystem = Default

    def __post_init__(self) -> None:
        self.invariants: None | dict = None
        self.n: int = 3

    def convert_to(self, unit_system: UnitSystem) -> "Stresses3d":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        self.n_xx *= ffactor
        self.n_yy *= ffactor
        self.n_xy *= ffactor
        self.u = unit_system
        return self

    def to_numpy(self) -> np.ndarray:
        return np.array([
                    [self.sig_xx, self.tau_xy, self.tau_zx],
                    [self.tau_xy, self.sig_yy, self.tau_yz],
                    [self.tau_zx, self.tau_yz, self.sig_zz]])

    def principals(self) -> tuple[np.ndarray, np.ndarray]:
        """Calculate the principal stresses and the normalized principal directions.

        Returns:
            tuple of ndarray: (principal stresses, normalized principal directions)

        """
        return np.linalg.eigh(self.to_numpy())

    def principal_vectors(self) -> np.ndarray:
        """Calculate the princcipal vectors (size proportional to principal stresses).

        Returns:
        ndarray: an array of the principal vectors

        """
        values, vectors = np.linalg.eigh(self.to_numpy())

        return vectors * np.array([values[0] * vectors[0],
                values[1] * vectors[1],
                values[2] * vectors[2]])

    def calc_invariants(self) -> dict:
        """Calculate the stress invariants.

        Returns:
            stress invariants (list): I1, J2, J3, mean_stress, eqv_stress,
                            lode_r, lode_z, lode_theta, cos3t, triaxiality

        """
        # load the stresses into our matrix and compute the
        # deviatoric and isotropic stress matricies
        sigma = self.to_numpy()
        sigma_iso = (np.trace(sigma) * np.eye(3)) / 3.0
        sigma_dev = sigma - sigma_iso

        # # compute max shear stress
        # maxshear = (max(eigvals)-min(eigvals))/2.0  # noqa: ERA001

        # compute the stress invariants
        I1 = np.trace(sigma)
        J2 = 0.5 * np.trace(np.dot(sigma_dev, sigma_dev))
        J3 = 0.33333333333333333 * np.trace(np.dot(sigma_dev, np.dot(sigma_dev, sigma_dev)))

        # compute other common stress measures
        mean_stress = I1 / self.n
        eqv_stress = math.sqrt(3.0 * J2)

        # compute lode coordinates
        lode_r = math.sqrt(2.0 * J2)
        lode_z = I1 / math.sqrt(3.0)

        stresses = 3.0 * math.sqrt(6.0) * np.linalg.det(sigma_dev / lode_r)
        stresses = max(stresses, -1)
        stresses = min(stresses, 1)
        lode_theta = 1.0 / 3.0 * math.asin(stresses)
        cos3t = 2.5980762114 * J3 / (J2**1.5)

        # compute the stress triaxiality
        triaxiality = mean_stress / eqv_stress

        self.invariants =   {
            Invariant.I1: I1,
            Invariant.J2: J2,
            Invariant.J3: J3,
            Invariant.MEAN_STRESS: mean_stress,
            Invariant.EQV_STRESS: eqv_stress,
            Invariant.MEAN_STRESS: mean_stress,
            Invariant.LODE_R: lode_r,
            Invariant.LODE_Z: lode_z,
            Invariant.LODE_THETA: lode_theta,
            Invariant.COS3T: cos3t,
            Invariant.TRIAXIALITY: triaxiality,
        }

        return self.invariants

    def __str__(self) -> str:
        s = "\nStresses:\n"
        s += (
            f"   sig_xx = {self.sig_xx:.5f}\n"
            f"   sig_yy = {self.sig_yy:.5f}\n"
            f"   sig_zz = {self.sig_zz:.5f}\n"
            f"   tau_xy = {self.tau_xy:.5f}\n"
            f"   tau_yz = {self.tau_yz:.5f}\n"
            f"   tau_zx = {self.tau_zx:.5f}\n"
        )
        if self.invariants is not None:
            s += "\nInvariants:\n"
            for k, v in self.invariants.items():
                s += f"   {k.value} = {v:.5f}\n"

        return s

@dataclass
class Stresses2d(Stresses3d):

    def __post_init__(self) -> None:
        self.n: int = 2
        self.sig_zz = 0.0
        self.tau_yz = 0.0
        self.tau_zx = 0.0

    def convert_to(self, unit_system: UnitSystem) -> "Stresses2d":
        ffactor = self.u.convert_to(unit_system, unit_type=UnitType.FORCE_LENGTH)
        self.sig_xx *= ffactor
        self.sig_yy *= ffactor
        self.sig_xy *= ffactor
        self.u = unit_system
        return self


def principals(sigxx: float, sigyy: float, sigzz: float,  # noqa: PLR0913, PLR0917
            sigxy: float, sigyz: float, sigzx: float) -> tuple[np.ndarray, np.ndarray]:
    """Calculate the principal stresses and the normalized principal directions.

    Author. Paulo Cachim (2022).

    Args:
        sigxx (float): stress xx
        sigyy (float): stress yy
        sigzz (float): stress zz
        sigxy (float): stress xy
        sigyz (float): stress yz
        sigzx (float): stress zx

    Returns:
        tuple of ndarray: (principal stresses, normalized principal directions)

    """
    eigvals, eigvecs = np.linalg.eigh(np.array([[sigxx, sigxy, sigzx],
                    [sigxy, sigyy, sigyz],
                    [sigzx, sigyz, sigzz]]))
    return eigvals, eigvecs


def principal_vectors(sigxx: float, sigyy: float, sigzz: float,  # noqa: PLR0913
    sigxy: float, sigyz: float, sigzx: float) -> np.ndarray:
    """Calculate the princcipal vectors (size proportional to principal stresses).

    Author. Paulo Cachim (2022)

    Args:
    sigxx (float): stress xx
    sigyy (float): stress yy
    sigzz (float): stress zz
    sigxy (float): stress xy
    sigyz (float): stress yz
    sigzx (float): stress zx

    Returns:
    ndarray: an array of the principal vectors

    """
    values, vectors = np.linalg.eigh(np.array([
                    [sigxx, sigxy, sigzx],
                    [sigxy, sigyy, sigyz],
                    [sigzx, sigyz, sigzz]]))

    return vectors * np.array([values[0] * vectors[0],
            values[1] * vectors[1],
            values[2] * vectors[2]])


def invariants(sigxx: float, sigyy: float, sigzz: float,
                        sigxy: float, sigyz: float, sigzx: float) -> tuple:
    """Calculate the stress invariants.

    Author. Paulo Cachim (2022)

    Args:
        sigxx (float): stress xx
        sigyy (float): stress yy
        sigzz (float): stress zz
        sigxy (float): stress xy
        sigyz (float): stress yz
        sigzx (float): stress zx

    Returns:
        stress invariants (list): I1, J2, J3, mean_stress, eqv_stress,
                        lode_r, lode_z, lode_theta, cos3t, triaxiality

    """
    # load the stresses into our matrix and compute the
    # deviatoric and isotropic stress matricies
    sigma = np.array([
                            [sigxx, sigxy, sigzx],
                            [sigxy, sigyy, sigyz],
                            [sigzx, sigyz, sigzz]])
    sigma_iso = (np.trace(sigma) * np.eye(3)) / 3.0
    sigma_dev = sigma - sigma_iso

    # # compute max shear stress
    # maxshear = (max(eigvals)-min(eigvals))/2.0

    # compute the stress invariants
    I1 = np.trace(sigma)
    J2 = 0.5 * np.trace(np.dot(sigma_dev, sigma_dev))
    J3 = 0.33333333333333333 * np.trace(np.dot(sigma_dev, np.dot(sigma_dev, sigma_dev)))

    # compute other common stress measures
    mean_stress = I1 / 3.0
    eqv_stress = math.sqrt(3.0 * J2)

    # compute lode coordinates
    lode_r = math.sqrt(2.0 * J2)
    lode_z = I1 / math.sqrt(3.0)

    stresses = 3.0 * math.sqrt(6.0) * np.linalg.det(sigma_dev / lode_r)
    stresses = max(stresses, -1)
    stresses = min(stresses, 1)
    lode_theta = 1.0 / 3.0 * math.asin(stresses)
    cos3t = 2.5980762114 * J3 / (J2**1.5)

    # compute the stress triaxiality
    triaxiality = mean_stress / eqv_stress

    return (
        I1, J2, J3, mean_stress, eqv_stress,
        lode_r, lode_z, lode_theta, cos3t, triaxiality,
    )


if __name__ == "__main__":

    print("\nTest stress module: principals:")
    eval1, evec = principals(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
    print(eval1)
    print(evec)
    print("\nTest stress module: principal_vectors:")
    evec = principal_vectors(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
    print(evec)

    print("\nTest stress module: stress invariants:")
    u = invariants(3.0, 2.0, -1.0, 0.3, -0.4, 0.5)
    print(u)

    sig = Stresses2d(2.0, 2.0, 0.0)
    inv = sig.calc_invariants()
    print(f"{sig}")
