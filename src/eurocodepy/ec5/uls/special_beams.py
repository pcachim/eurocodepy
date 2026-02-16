# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
"""Check beams with special geometry.

EN 1995-1-1:2025+prA1:2026
Implementation of Equations (8.53)–(8.76)
GL / BGL beams – single tapered, double tapered, curved,
pitched cambered beams (apex zone checks)

Units:
- Forces: kN
- Moments: kNm
- Stresses: MPa (N/mm²)
- Dimensions: m
- Angles: radians
"""

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

import eurocodepy as ec
from eurocodepy.ec5 import LoadDuration, ServiceClass, Timber, Glulam
from eurocodepy.ec5.materials import TimberForcesType
from eurocodepy.utils import CrossSection

# ==========================================================
# ENUMS
# ==========================================================


class BeamType(Enum):
    SINGLE_TAPPERED = "single_tapered"
    DOUBLE_TAPERED = "double_tapered"
    CURVED = "curved"
    PITCHED = "pitched_cambered"


# ==========================================================
# GEOMETRY
# ==========================================================

@dataclass
class SpecialBeamGeometry:
    beam_type: BeamType  # type of special beam
    b: float             # width (mm)
    h_s: float           # initial height (mm)
    h_ap: float          # height at apex (mm)
    r_in: float          # inner radius (mm)
    alpha_ap: float      # taper angle at apex (radians)
    t_l: float = 0.045   # lamination thickness (mm)
    beta: float = 0.0    # initial angle at origin (radians)

    @classmethod
    def single_tapered(cls,
                    b: float,
                    h_s: float,
                    h_ap: float,
                    alpha_ap: float,
                    t_l = 0.045,
                    ) -> "SpecialBeamGeometry":
        return SpecialBeamGeometry(
            b, h_s, h_ap, r_in=0.0, t_l=t_l,
            alpha_ap=alpha_ap, beam_type=BeamType.SINGLE_TAPPERED)


# ==========================================================
# MAIN CLASS
# ==========================================================

class GLBeamChecker:
    """Glulam beam checker.

    Check according to EN 1995-1-1:2025+prA1:2026 (8.53–8.76)
    """

    def __init__(  # noqa: D107
        self,
        material: Timber,
        geometry: SpecialBeamGeometry,
        beam_type: BeamType,
        k_v: float = 1.0,      # shear modification factor
    ) -> None:

        self.material = material
        self.geometry = geometry
        self.beam_type = beam_type
        self.k_v = k_v

    def check_bending_tapered_edge(sigma_m_alpha_d, k_m_alpha, f_m_d):
        """
        EN 1995-1-1 Eq. (8.53)
        σ_m,α,d ≤ k_m,α * f_m,d
        """
        return sigma_m_alpha_d <= k_m_alpha * f_m_d

    def k_m_alpha_tension(alpha,
                        sigma_m_alpha_d,
                        tau_d,
                        sigma_t90_d,
                        f_v_d,
                        f_t90_d,
                        k_tau_t):
        """
        EN 1995-1-1 Eq. (8.54)
        Tensile stresses parallel to tapered edge
        """

        term1 = sigma_m_alpha_d
        term2 = k_tau_t * tau_d
        term3 = sigma_t90_d

        denom = (term1 / f_v_d) + (term2 / f_v_d) + (term3 / f_t90_d)

        return 1.0 / denom

    def k_m_alpha_compression(alpha,
                        sigma_m_alpha_d,
                        tau_d,
                        sigma_c90_d,
                        f_v_d,
                        f_c90_d,
                        k_tau_c):
        """
        EN 1995-1-1 Eq. (8.56)
        Compressive stresses parallel to tapered edge
        """

        term1 = sigma_m_alpha_d
        term2 = k_tau_c * tau_d
        term3 = sigma_c90_d

        denom = (term1 / f_v_d) + (term2 / f_v_d) + (term3 / f_c90_d)

        return 1.0 / denom

    # ======================================================
    # 8.58 – Bending stress for α ≤ 15°
    # ======================================================

    def sigma_m_linear(self, M: float) -> float:
        """
        σ_m = 6 M / (b h²)
        """
        b = self.geometry.b
        h = self.geometry.h_ap
        return 6.0 * M / (b * h**2)

    # ======================================================
    # 8.60 – kr factor (lamination curvature effect)
    # ======================================================

    def k_r(self) -> float:
        ratio = self.geometry.r_in / self.geometry.t_l
        if ratio >= 240:
            return 1.0
        return 0.76 + 0.001 * ratio

    # ======================================================
    # 8.63–8.66 – kl,ap components
    # ======================================================

    def _k1(self) -> float:
        a = self.geometry.alpha_ap
        return 1 + 1.4 * math.tan(a) + 5.4 * math.tan(a)**2

    def _k2(self) -> float:
        a = self.geometry.alpha_ap
        return 0.35 - 8 * math.tan(a)

    def _k3(self) -> float:
        a = self.geometry.alpha_ap
        return 0.6 + 8.3 * math.tan(a) - 7.8 * math.tan(a)**2

    def _k4(self) -> float:
        a = self.geometry.alpha_ap
        return 6 * math.tan(a)**2

    # ======================================================
    # 8.62 – kl,ap
    # ======================================================

    def k_l_ap(self) -> float:
        h = self.geometry.h_ap
        r = self.geometry.r_in + 0.5 * h
        eta = h / r

        return (
            self._k1()
            + self._k2() * eta
            + self._k3() * eta**2
            + self._k4() * eta**3
        )

    # ======================================================
    # 8.61 – Apex bending stress
    # ======================================================

    def sigma_m_apex(self, M_ap: float) -> float:
        b = self.geometry.b
        h = self.geometry.h_ap
        return self.k_l_ap() * (6.0 * M_ap) / (b * h**2)

    # ======================================================
    # 8.59 – Apex bending verification
    # ======================================================

    def check_apex_bending(self, M_ap: float) -> bool:
        sigma = self.sigma_m_apex(M_ap)
        return sigma <= self.k_r() * self.material.fmd

    # ======================================================
    # 8.69 – k_dis
    # ======================================================

    def k_dis(self) -> float:
        if self.beam_type in {BeamType.DOUBLE_TAPERED, BeamType.PITCHED}:
            return 1.3
        return 1.15

    # ======================================================
    # 8.70 – k_vol
    # ======================================================

    def k_vol(self, h_ref: float = 600.0) -> float:
        return (h_ref / self.geometry.h_ap) ** 0.2

    # ======================================================
    # 8.68 – Tension ⟂ grain verification
    # ======================================================

    def check_sigma_t90(self, sigma_t90: float) -> bool:
        return sigma_t90 <= (
            self.k_dis() * self.k_vol() * self.material.ft90d
        )

    # ======================================================
    # 8.71 – Combined shear + tension
    # ======================================================

    def check_combined(
        self,
        sigma_t90: float,
        tau: float,
    ) -> bool:

        term1 = sigma_t90 / (
            self.k_dis() * self.k_vol() * self.material.ft90d
        )
        term2 = tau / (self.k_v * self.material.fvd)

        return term1 + term2 <= 1.0

    # ======================================================
    # 8.74–8.76 – kp factors
    # ======================================================

    def _k5(self) -> float:
        return 0.2 * math.tan(self.geometry.alpha_ap)

    def _k6(self) -> float:
        a = self.geometry.alpha_ap
        return 0.25 - 1.5 * math.tan(a) + 2.6 * math.tan(a)**2

    def _k7(self) -> float:
        a = self.geometry.alpha_ap
        return 2.1 * math.tan(a) - 4.0 * math.tan(a)**2

    # ======================================================
    # 8.73 – kp,ap
    # ======================================================

    def k_p_ap(self) -> float:
        h = self.geometry.h_ap
        r = self.geometry.r_in + 0.5 * h
        eta = h / r

        return (
            self._k5()
            + self._k6() * eta
            + self._k7() * eta**2
        )

    # ======================================================
    # 8.72 – Maximum σt,90 from bending deviation
    # ======================================================

    def sigma_t90_apex(self, M_ap: float) -> float:
        b = self.geometry.b
        h = self.geometry.h_ap
        return self.k_p_ap() * (6.0 * M_ap) / (b * h**2)


# ==========================================================
# EXAMPLE USAGE
# ==========================================================

if __name__ == "__main__":

    material = Glulam("GL24h")

    geometry = SpecialBeamGeometry(
        b=160.0,
        h_s=200.0,
        h_ap=600.0,
        r_in=12000.0,
        t_l=40.0,
        alpha_ap=math.radians(6),
        beam_type=BeamType.DOUBLE_TAPERED
    )

    checker = GLBeamChecker(
        material=material,
        geometry=geometry,
        beam_type=BeamType.CURVED,
    )

    M_ap = 250e6  # Nmm

    print("σm,apex =", checker.sigma_m_apex(M_ap))
    print("Bending OK:", checker.check_apex_bending(M_ap))
    print("σt,90,max =", checker.sigma_t90_apex(M_ap))
