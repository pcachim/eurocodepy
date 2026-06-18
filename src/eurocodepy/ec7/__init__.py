# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 7 - Geotechnical design module.

This module provides functions and classes for geotechnical design according to
Eurocode 7 (EN 1997-1:2004).
It includes calculations for bearing capacity, earth pressures,
and other geotechnical parameters.
"""

from .bearing_capacity import (
    bearing_resistance as bearing_resistance,
    seismic_bearing_resistance as seismic_bearing_resistance,
    soil_gamma_rd as soil_gamma_rd,
)
from .earth_pressures import (
    EarthPressureModels as EarthPressureModels,
    pressure_coefficients as pressure_coefficients,
)
from .materials import (
    Soil as Soil,
    SoilEnum as SoilEnum,
    SoilSafetyFactors as SoilSafetyFactors,
    SoilSafetyFactorsEnum as SoilSafetyFactorsEnum,
    SoilSeismicParameters as SoilSeismicParameters,
    SoilSurcharge as SoilSurcharge,
    get_soil_seismic_parameters as get_soil_seismic_parameters,
)

__all__ = [
    "bearing_resistance",
    "seismic_bearing_resistance",
    "soil_gamma_rd",
    "EarthPressureModels",
    "pressure_coefficients",
    "Soil",
    "SoilEnum",
    "SoilSafetyFactors",
    "SoilSafetyFactorsEnum",
    "SoilSeismicParameters",
    "SoilSurcharge",
    "get_soil_seismic_parameters",
]
