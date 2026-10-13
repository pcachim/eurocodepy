# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""EN 1992-1-1:2023 Annex G.4 shell element design by the sandwich model — composite.

The 2023 counterpart of :mod:`eurocodepy.ec2.uls.shell_check`, with the same input
fields (plus ``k_tc``, ``annex``, ``nu_mode``, ``lam``, ``e_s``) and result object. It is
:func:`eurocodepy.ec2.uls2023.slab_design.eurocode2_slab_check` with ``method="sandwich"``
for the shell's forces and moments: layers of thickness ``t = 2·c``, Table G.1 per layer,
``fcd = ηcc·ktc·fck/γc`` and the strut check ``σcd ≤ ν·fcd`` with ``ν = 0,4`` (Eq. G.8,
``nu_mode="simple"``) or Eq. (G.9) (``"strain"``).

Units and signs as :mod:`eurocodepy.ec2.uls.shell_check`.
"""

from __future__ import annotations

from dataclasses import dataclass

from eurocodepy.ec2.materials import PartialFactorsMixin
from eurocodepy.ec2.uls.shell_check import ShellResult, layer_stresses
from eurocodepy.ec2.uls2023 import slab_design as _slab

__all__ = ["ShellInput", "ShellResult", "eurocode2_shell_check", "layer_stresses"]


@dataclass
class ShellInput(PartialFactorsMixin):
    """Shell element data for the sandwich-model design (EN 1992-1-1:2023)."""

    n_xx: float               # membrane force, x [kN/m]
    n_yy: float
    n_xy: float
    m_xx: float               # bending moment, x [kNm/m] (sagging +)
    m_yy: float
    m_xy: float               # torsional moment [kNm/m]
    fck: float
    fyk: float
    thickness: float          # shell thickness h [m]
    cover: float              # distance from the surface to the bar centres [m]
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float | None = None   # η_cc·k_tc of fcd; None = from fck and k_tc
    k_tc: float = 1.0
    annex: str | None = None
    nu_mode: str = "simple"   # 'simple' (ν = 0,4, G.8) or 'strain' (G.9-G.11)
    lam: float = 1.0
    e_s: float = 200000.0


def eurocode2_shell_check(inp: ShellInput, trace=None) -> ShellResult:
    """Design the four orthogonal reinforcements of a shell element (Annex G.4(1)-(3)).

    Returns a :class:`ShellResult` (``crushing``: a layer's strut exceeds ``ν·fcd``;
    ``details`` as :func:`eurocodepy.ec2.uls2023.slab_design.eurocode2_slab_check`).
    """
    slab = _slab.SlabInput(
        m_x=inp.m_xx, m_y=inp.m_yy, m_xy=inp.m_xy, fck=inp.fck, fyk=inp.fyk,
        thickness=inp.thickness, cover_bot_x=inp.cover, cover_bot_y=inp.cover,
        cover_top_x=inp.cover, cover_top_y=inp.cover, gamma_c=inp.gamma_c,
        gamma_s=inp.gamma_s, alpha_cc=inp.alpha_cc, k_tc=inp.k_tc, annex=inp.annex,
        n_x=inp.n_xx, n_y=inp.n_yy, n_xy=inp.n_xy, method="sandwich",
        nu_mode=inp.nu_mode, lam=inp.lam, e_s=inp.e_s)
    r = _slab.eurocode2_slab_check(slab, trace=trace)
    return ShellResult(asx_bot=r.asx_bot, asy_bot=r.asy_bot, asx_top=r.asx_top,
                       asy_top=r.asy_top, crushing=bool(r.details["crushing"]),
                       details=r.details)
