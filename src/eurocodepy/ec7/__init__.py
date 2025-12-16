# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 7 - Geotechnical design module.

This module provides functions and classes for geotechnical design according to
Eurocode 7 (EN 1997-1:2004).
It includes calculations for bearing capacity, earth pressures,
and other geotechnical parameters.
"""

from .bearing_capacity import (
    bearing_resistance,  # noqa: F401
    seismic_bearing_resistance,  # noqa: F401
    soil_gamma_rd,  # noqa: F401
)
from .earth_pressures import (
    EarthPressureModels,  # noqa: F401
    pressure_coefficients,  # noqa: F401
)
from .materials import (
    Soil,  # noqa: F401
    SoilEnum,  # noqa: F401
    SoilSafetyFactors,  # noqa: F401
    SoilSafetyFactorsEnum,  # noqa: F401
    SoilSeismicParameters,  # noqa: F401
    SoilSurcharge,  # noqa: F401
    get_soil_seismic_parameters,  # noqa: F401
    
)
