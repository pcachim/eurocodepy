# eurocodepy

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

import pandas as pd 
import os

__version__ = "2025.5.8"
print_version = "This is 'eurocodepy' version " + __version__

from . import ec1
from . import ec2
from . import ec3
from . import ec5
from . import ec7
from . import ec8
from . import utils

# National parameters
local_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
local_name = os.path.join(local_name, 'eurocode_data_portugal.csv')
locale = {}
locale["PT"] = pd.read_csv(local_name)

def get_national_params(local: str = "PT", concelho: str = "Lisboa") -> dict:
    """

    Args:
        locale (str, optional): _description_. Defaults to "PT".
        concelho (str, optional): _description_. Defaults to "Lisboa".

    Returns:
        dict: _description_
    """
    pt_data = locale[str.upper(local)]
    row = pt_data[pt_data['Concelho'] == concelho]
    # Convert to dict if found
    if not row.empty:
        result = row.iloc[0].to_dict()
        print(result)
    else:
        result = None
        print("Concelho not found.")
    return result



# Database imports
from .db import db
from .db import dbobj
from .db import Materials

from .db import Bolts
from .db import BoltGrades
from .db import BoltDiameters

from .db import Concrete
from .db import ConcreteGrades
from .db import ConcreteParams

from .db import Prestress
from .db import PrestressGrades
from .db import PrestressParams

from .db import Reinforcement
from .db import ReinforcementBars
from .db import ReinforcementGrades
from .db import ReinforcementParams

from .db import Steel
from .db import SteelGrades
from .db import SteelParams

from .db import SteelProfiles

from .db import Loads
from .db import WindLoads
from .db import DeadLoads
from .db import SeismicLoads

from .params import wind_get_params
from .params import seismic_get_params

from .ec8 import get_spec_params

from .ec1 import wind

from .utils import stress

RECTANGULAR = 0
CIRCULAR = 1
TSECTION = 2
LSECTION = 3
INVTSECTION = 4
POLYGONAL = 5
