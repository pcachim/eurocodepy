# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Reinforced-concrete column design -- **prEN 1992-1-1:2023** (override of
:mod:`eurocodepy.ec2.uls.column`).

Mirrors :mod:`eurocodepy.ec2.uls.column` by ``import *`` and overrides only
what actually changes in this edition. Relative to EN 1992-1-1:2004+A1:2014,
this module currently overrides:

  * (nothing yet)

Every symbol not listed above -- ``ColumnInput``, ``ColumnResult``,
``RebarLayout``, ``slenderness_limit``, ``biaxial_interaction_exponent``,
``nominal_curvature_e2``, ``nominal_stiffness_moment``,
``uniaxial_moment_resistance``, ``eurocode2_column_check`` -- is **inherited
unchanged** from the 2004 module: corrections made there propagate here
automatically as long as this list stays empty for them.

**Why nothing is overridden yet**: the second-generation Eurocode 2
(prEN 1992-1-1:2023) revises, among other things, the simplified slenderness
criterion of EC2:2004 §5.8.3.1 (Eq. 5.13N) and the ``alpha_cc``/``kcc``
long-term-effects coefficient -- see ``dev/RC_COLUMN_DESIGN.md`` §1.2 in the
xdfem2d repository for the analysis. At the time this module was written the
exact coefficients of the approved prEN text had not been confirmed against a
reliable primary source, so guessing plausible-looking numbers here would be
worse than shipping the (conservative, EC2:2004) values under the ``2023``
name. **Do not add an override below without a specific clause reference to
the confirmed, approved prEN 1992-1-1:2023 text** -- update the list above
in the same change, so the next reader knows exactly what changed and why,
following the documentation convention proposed in
``dev/GRILLAGE_DESIGN.md`` §3.4 for ``uls2023/punch.py``.
"""

from eurocodepy.ec2.uls.column import *  # noqa: F401, F403
from eurocodepy.ec2.uls.column import __all__ as _column_all

__all__ = list(_column_all)
