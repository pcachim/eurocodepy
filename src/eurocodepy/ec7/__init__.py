# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 7 - Geotechnical design module.

This module provides functions and classes for geotechnical design according to
Eurocode 7 (EN 1997-1:2004).
It includes calculations for bearing capacity, earth pressures,
and other geotechnical parameters.
"""

from eurocodepy.ec7.materials import (
    Soil,
    SoilEnum,
    SoilSafetyFactors,
    SoilSafetyFactorsEnum,
    SoilSeismicParameters,
    SoilSurcharge,
    get_soil_seismic_parameters,
)
from eurocodepy.ec7.bearing_capacity import (
    bearing_resistance,
    seismic_bearing_resistance,
    soil_gamma_rd,
)
from eurocodepy.ec7.earth_pressures import (
    EarthPressureModels,
    pressure_coefficients,
)
