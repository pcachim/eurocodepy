# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

# EurocodePy
"""Provide several functions to help designers working with Eurocodes.

The package provides modules for different Eurocodes and utilities, such as:

* `dbase`: access to the database of materials, loads, sections, etc.
* `utils`: utility functions for calculations, stress, and section properties.
* `ec1`: utility functions for ec1 calculations.<br>
* `ec2`: utility functions for ec2 calculations.<br>
* `ec3`: utility functions for ec3 calculations.<br>
* `ec5`: utility functions for ec5 calculations.<br>
* `ec7`: utility functions for ec7 calculations.<br>
* `ec8`: utility functions for ec8 calculations.
"""

__version__ = "2026.1.1"
"""Version of EurocodePy package."""
print_version = "This is 'EurocodePy' version " + __version__
"""Prints the version of EurocodePy package."""
from dataclasses import dataclass  # noqa: E402
from enum import Enum  # noqa: E402
from pathlib import Path  # noqa: E402

import pandas as pd  # noqa: E402

from eurocodepy import dbase, ec1, ec2, ec3, ec5, ec7, ec8, utils

# National parameters
local_name = Path(__file__).parent / "data" / "eurocode_data_portugal.csv"
locale = Enum("locale", ["EU", "PT"])
locales = {}
locales["PT"] = pd.read_csv(local_name)


@dataclass
class NationalParams:
    """Class to hold national parameters."""

    local: locale = locale.PT
    """Locale for national parameters."""
    concelho: str = "Lisboa"
    """Municipality name, default is 'Lisboa'."""

    def __post_init__(self):
        """Post-initialization to load data."""
        self.data = get_national_params(self.local, self.concelho)


class LocaleData:
    """Class to hold locale data."""

    PT: pd.DataFrame = pd.read_csv(local_name)


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
        print(result)  # noqa: T201
    else:
        result = None
        print("Concelho not found.")  # noqa: T201
    return result


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
    SteelCHSProfiles,
    SteelGrades,
    SteelIProfiles,
    SteelParams,
    SteelRHSProfiles,
    SteelSHSProfiles,
    Timber,
    TimberGrades,
    TimberLoadDuration,
    TimberParams,
    TimberServiceClasses,
    WindLoads,
    db,
    dbobj,
)
from eurocodepy.ec1 import wind
from eurocodepy.ec8 import get_spec_params, spectrum
from eurocodepy.national_parameters import seismic_get_params, wind_get_params
from eurocodepy.utils import crosssection, section_properties, stress

RECTANGULAR = 0
CIRCULAR = 1
TSECTION = 2
LSECTION = 3
INVTSECTION = 4
POLYGONAL = 5
