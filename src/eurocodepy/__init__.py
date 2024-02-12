# eurocodepy

"""Provide several functions to help designers working with Eurocodes.

This module allows the user to make mathematical calculations.

The module contains the following functions:

- `db`: Returns the database of the Eurocodes.
- `ec1`: Returns the difference of two numbers.
- `ec2` - Returns the product of two numbers.
- `ec5` - Returns the quotient of two numbers.
- `ec8` - Returns the quotient of two numbers.
"""

# print ("This is eurocodepy v0.1.20")

from . import ec1
from . import ec2
from . import ec5
from . import ec8
from . import utils

from .db import db
from .db import dbase
from .db import Materials

from .db import Bolts
from .db import BoltClasses
from .db import BoltDiameters

from .db import Concrete
from .db import ConcreteClasses
from .db import ConcreteParams

from .db import Prestress
from .db import PrestressClasses
from .db import PrestressParams

from .db import Reinforcement
from .db import ReinforcementBars
from .db import ReinforcementClasses
from .db import ReinforcementParams

from .db import Steel
from .db import SteelClasses
from .db import SteelParams

from .db import SteelProfiles

from .db import Loads
from .db import WindLoads
from .db import DeadLoads
from .db import SeismicLoads

from .utils import stress

RECTANGULAR = 0
CIRCULAR = 1
TSECTION = 2
LSECTION = 3
INVTSECTION = 4
POLYGONAL = 5


