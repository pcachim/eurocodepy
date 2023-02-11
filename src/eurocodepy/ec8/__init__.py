from .. import db
db = db.db

from .. import utils
stress = utils.stress

from .. import ec1
from .. import ec2
from .. import ec5
from .. import ec8

from . import spectrum
from .spectrum import get_spectrum_parameters
from .spectrum import get_spectrum
from .spectrum import spectrum_ec8
from .spectrum import spectrum_user
from .spectrum import write_spectrum_ec8
from .spectrum import draw_spectrum_ec8
