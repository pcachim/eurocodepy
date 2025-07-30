"""Module that provides functions and classes for Eurocode 8 calculations.

It includes functions for generating design response spectra, retrieving national annex parameters,
and writing design response spectra to a file. It also includes classes for representing
soil amplification, reference acceleration, and spectrum shape parameters.
"""
from eurocodepy import dbase, utils
from eurocodepy.ec8 import spectrum
from eurocodepy.ec8.spectrum import (
    calc_spectrum,
    draw_spectrum_ec8,
    get_spec_params,
    get_spectrum_ec8,
    get_spectrum_parameters,
    get_spectrum_user,
    write_spectrum_ec8,
)
