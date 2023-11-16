from .. import db
from .. import utils
from . import pressure
from .pressure import *

wind_pars = db["Loads"]["Wind"]["Locale"]

# z_0 = pressure.z0
# z_min = pressure.zmin