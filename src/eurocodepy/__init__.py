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

__version__ = "2026.2.1"
version = "This is 'EurocodePy' version " + __version__  # noqa: RUF067
"""Version of EurocodePy package."""


from eurocodepy import (  # noqa: E402, I001
    dbase as dbase,
    ec1 as ec1,
    ec2 as ec2,
    ec3 as ec3,
    ec5 as ec5,
    ec7 as ec7,
    ec8 as ec8,
    utils as utils,
)

# Database imports
from eurocodepy.dbase import (  # noqa: E402
    BoltDiameters as BoltDiameters,
    BoltGrades as BoltGrades,
    Bolts as Bolts,
    ConcreteMaterial as ConcreteMaterial,
    ConcreteGrades as ConcreteGrades,
    ConcreteParams as ConcreteParams,
    DeadLoads as DeadLoads,
    Loads as Loads,
    Materials as Materials,
    PrestressMaterial as PrestressMaterial,
    PrestressGrades as PrestressGrades,
    PrestressParams as PrestressParams,
    ReinforcementMaterial as ReinforcementMaterial,
    ReinforcementBars as ReinforcementBars,
    ReinforcementGrades as ReinforcementGrades,
    ReinforcementParams as ReinforcementParams,
    SeismicLoads as SeismicLoads,
    SteelMaterial as SteelMaterial,
    SteelCHSProfiles as SteelCHSProfiles,
    SteelGrades as SteelGrades,
    SteelIProfiles as SteelIProfiles,
    SteelParams as SteelParams,
    SteelRHSProfiles as SteelRHSProfiles,
    SteelSHSProfiles as SteelSHSProfiles,
    TimberMaterial as TimberMaterial,
    TimberGrades as TimberGrades,
    TimberLoadDuration as TimberLoadDuration,
    TimberParams as TimberParams,
    TimberServiceClasses as TimberServiceClasses,
    WindLoads as WindLoads,
    db as db,
    dbobj as dbobj,
)

# General function imports
from eurocodepy.ec1 import wind as wind  # noqa: E402
from eurocodepy.ec8 import get_spec_params as get_spec_params, spectrum as spectrum  # noqa: E402
from eurocodepy.national_parameters import (  # noqa: E402
    local_name as local_name,
    locale as locale,
    locales as locales,
    seismic_get_params as seismic_get_params,
    wind_get_params as wind_get_params,
    NationalParams as NationalParams,
    LocaleData as LocaleData,
)
from eurocodepy.utils import (  # noqa: E402
    crosssection as crosssection,
    section_properties as section_properties,
    stress as stress
)

# Materials imports
from eurocodepy.ec2.materials import Concrete as Concrete  # noqa: E402
from eurocodepy.ec2.materials import Reinforcement as Reinforcement  # noqa: E402
from eurocodepy.ec2.materials import Prestress as Prestress  # noqa: E402
from eurocodepy.ec3.materials import Steel as Steel  # noqa: E402
from eurocodepy.ec3.materials import Weld as Weld  # noqa: E402
from eurocodepy.ec5.materials import Timber as Timber  # noqa: E402
