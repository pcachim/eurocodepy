"""Eurocode 7 - Geotechnical design module
This module provides functions and classes for geotechnical design according to Eurocode 7 (EN 1997-1:2004).
It includes calculations for bearing capacity, earth pressures, and other geotechnical parameters.
"""

from .. import db
from .. import utils

from . import bearing_capacity
from .bearing_capacity import bearing_resistance
from .bearing_capacity import seismic_bearing_resistance

from . import earth_pressures
from .earth_pressures import rankine_coefficient
from .earth_pressures import coulomb_coefficient
from .earth_pressures import inrest_coefficient
from .earth_pressures import ec7_coefficient
from .earth_pressures import pressure_coefficients
from .earth_pressures import earthquake_coefficient
