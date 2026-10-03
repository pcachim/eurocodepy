# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Combined shear + torsion design -- **EN 1992-1-1:2023** (override of
:mod:`eurocodepy.ec2.uls.shear_torsion`).

Mirrors :mod:`eurocodepy.ec2.uls.shear_torsion` by ``import *`` and overrides
only what actually changes in this edition. Relative to EN 1992-1-1:2004+A1:2014,
this module currently overrides:

  * (nothing yet)

Every symbol not listed above -- ``ShearTorsionInput``, ``ShearTorsionResult``,
``eurocode2_shear_torsion_check``, ``distribute_torsion_longitudinal`` -- is
**inherited unchanged** from the 2004 module: corrections made there
propagate here automatically as long as this list stays empty for them.

**Why nothing is overridden yet**: the second-generation Eurocode 2
(EN 1992-1-1:2023) is known to revise, for shear and torsion, the strut
crushing coefficients (a ``nu1``-equivalent reduction factor for cracked
struts) and possibly the permitted ``cotg_theta`` range -- see
``dev/GRILLAGE_DESIGN.md`` §2.6 in the xdfem2d repository for the analysis.
At the time this module was written the exact coefficients of the approved
EN text had not been confirmed against a reliable primary source, so
guessing plausible-looking numbers here would be worse than shipping the
(conservative, EC2:2004) values under the ``2023`` name -- same reliability
caveat already documented in ``eurocodepy.ec2.uls2023.column`` for the
slenderness/``alpha_cc`` coefficients. The linear shear+torsion interaction
form itself (EC2 eq. 6.29 equivalent) is **not** expected to change
structurally between editions (see §2.6), so no override is anticipated
there even once the strut coefficients are confirmed.

**Do not add an override below without a specific clause reference to the
confirmed, approved EN 1992-1-1:2023 text** -- update the list above in
the same change, so the next reader knows exactly what changed and why.
"""

from eurocodepy.ec2.uls.shear_torsion import *  # noqa: F401, F403
from eurocodepy.ec2.uls.shear_torsion import __all__ as _shear_torsion_all

__all__ = list(_shear_torsion_all)
