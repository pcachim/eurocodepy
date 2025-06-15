# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

# EurocodePy
"""Provide several functions to help designers working with Eurocodes.

This module allows the user to make mathematical calculations.
The module contains the following functions:

`db`: Returns the database of the Eurocodes.
`ec1`: Returns functions for ec1 calculations.
`ec2`: Returns functions for ec2 calculations.
`ec3`: Returns functions for ec3 calculations.
`ec5`: Returns functions for ec5 calculations.
`ec7`: Returns functions for ec7 calculations.
`ec8`: Returns functions for ec8 calculations.
"""

from enum import Enum
from pathlib import Path

import pandas as pd

__version__ = "2025.6.8"
print_version = "This is 'EurocodePy' version " + __version__

from eurocodepy import ec1, ec2, ec3, ec5, ec7, ec8, utils, dbase

# National parameters
local_name = Path(__file__).parent / "data" / "eurocode_data_portugal.csv"
locale = Enum("locale", ["EU", "PT"])
locales = {}
locales["PT"] = pd.read_csv(local_name)

def get_national_params(local: locale = locale.PT, concelho: str = "Lisboa") -> object:
    """Get Portuguese data for municipalities.

    Args:
        local (locale, optional): Locale to use for national parameters.
        Defaults to locale.PT.
        concelho (str, optional): Municipality name. Defaults to "Lisboa".

    Returns:
        dict: the data

    """
    pt_data = locale[local.name]
    row = pt_data[pt_data["Concelho"] == concelho]
    # Convert to dict if found
    if not row.empty:
        result = row.iloc[0].to_dict()
        print(result)
    else:
        result = None
        print("Concelho not found.")
    return result


from eurocodepy import dbase
# Database imports
from eurocodepy.dbase import (
    BoltDiameters,
    BoltGrades,
    Bolts,
    Concrete,
    ConcreteGrades,
    ConcreteParams,
    DeadLoads,
    Loads,
    Materials,
    Prestress,
    PrestressGrades,
    PrestressParams,
    Reinforcement,
    ReinforcementBars,
    ReinforcementGrades,
    ReinforcementParams,
    SeismicLoads,
    Steel,
    SteelGrades,
    SteelParams,
    SteelProfiles,
    WindLoads,
    db,
    dbobj,
)
from eurocodepy.ec1 import wind
from eurocodepy.ec8 import spectrum, get_spec_params
from eurocodepy.params import seismic_get_params, wind_get_params
from eurocodepy.utils import stress, section_properties

RECTANGULAR = 0
CIRCULAR = 1
TSECTION = 2
LSECTION = 3
INVTSECTION = 4
POLYGONAL = 5
