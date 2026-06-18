"""Module that provides functions and classes for Eurocode 8 calculations.

It includes functions for generating design response spectra, retrieving national annex parameters,
and writing design response spectra to a file. It also includes classes for representing
soil amplification, reference acceleration, and spectrum shape parameters.
"""

from eurocodepy import (
    dbase as dbase,
    utils as utils,
)
from eurocodepy.ec8 import spectrum as spectrum
from eurocodepy.ec8.spectrum import (
    calc_elastic_spectrum as calc_elastic_spectrum,
    calc_spectrum as calc_spectrum,
    damping_correction as damping_correction,
    draw_spectrum_ec8 as draw_spectrum_ec8,
    get_elastic_spectrum_user as get_elastic_spectrum_user,
    get_spec_params as get_spec_params,
    get_spectrum_ec8 as get_spectrum_ec8,
    get_spectrum_parameters as get_spectrum_parameters,
    get_spectrum_user as get_spectrum_user,
    write_spectrum_ec8 as write_spectrum_ec8,
)

__all__ = [
    "dbase",
    "utils",
    "spectrum",
    "calc_elastic_spectrum",
    "calc_spectrum",
    "damping_correction",
    "draw_spectrum_ec8",
    "get_elastic_spectrum_user",
    "get_spec_params",
    "get_spectrum_ec8",
    "get_spectrum_parameters",
    "get_spectrum_user",
    "write_spectrum_ec8",
]
