# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Grouped cross-section / member verification — **EN 1995-1-1:2025** (§8).

Same grouped API as :mod:`eurocodepy.ec5.uls.cross_section` (the dataclasses are
re-used unchanged), but the underlying bending-with-axial and shear-with-torsion
checks are the second-generation §8 versions from :mod:`eurocodepy.ec5.uls2025`.
"""

from __future__ import annotations

# The force / input / result dataclasses are edition-independent — re-use them.
from eurocodepy.ec5.uls.cross_section import (
    TimberForces as TimberForces,
    TimberSectionInput as TimberSectionInput,
    TimberSectionResult as TimberSectionResult,
)
from eurocodepy.ec5.uls2025.bending import check_bending_with_normal
from eurocodepy.ec5.uls2025.shear import check_shear_with_torsion


def eurocode5_section_check(inp: TimberSectionInput,
                            f: TimberForces) -> TimberSectionResult:
    """Verify a timber member under N + My + Mz + Vy + Vz + T (EN 1995-1-1:2025).

    Identical grouping to :func:`eurocodepy.ec5.uls.eurocode5_section_check`, but
    calling the §8 (2025) bending / shear checks.
    """
    bend = check_bending_with_normal(
        n_ed=f.n_ed, m_ed_y=f.my_ed, m_ed_z=f.mz_ed,
        section=inp.section, timber=inp.timber,
        l_0y=inp.l_0y, l_0z=inp.l_0z, l_0m=inp.l_0m,
        service_class=inp.service_class, load_duration=inp.load_duration)
    shear = check_shear_with_torsion(
        v_ed_y=f.vy_ed, v_ed_z=f.vz_ed, t_ed=f.t_ed,
        section=inp.section, timber=inp.timber,
        service_class=inp.service_class, load_duration=inp.load_duration)

    u_nm = float(bend["utilization"])
    u_v = float(shear["util_shear"])
    u_t = float(shear["util_torsion"])
    utilization = max(u_nm, u_v, u_t)

    return TimberSectionResult(
        util_bending_axial=u_nm, util_shear=u_v, util_torsion=u_t,
        utilization=utilization, passed=utilization <= 1.0,
        k_c=tuple(bend.get("k_c", (1.0, 1.0))),
        k_m=float(bend.get("k_m", 1.0)),
        details={"bending": bend, "shear": shear})
