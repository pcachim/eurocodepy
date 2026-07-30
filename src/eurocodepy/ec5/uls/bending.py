# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Bending + axial checks — **EN 1995-1-1:2004** (§6).

Baseline (first-generation) Eurocode 5 member verification:

* biaxial bending factor ``k_m`` — 0.7 for rectangular solid timber / glulam /
  LVL, 1.0 otherwise (§6.1.6, Eqs. 6.11/6.12); exposed as ``calc_k_red`` to keep
  the function name shared with the :2025 edition;
* column instability factor ``k_c`` (§6.3.2, Eqs. 6.25-6.29) with
  ``β_c = 0.2`` (solid timber) / ``0.1`` (glulam, LVL);
* lateral-torsional factor ``k_crit`` (§6.3.3, Eqs. 6.30-6.34) — exposed as
  ``calc_k_m`` to keep the shared name — from the critical bending moment
  ``M_y,crit`` (Eq. 6.31);
* the combined bending + axial-tension (Eqs. 6.17/6.18), bending +
  axial-compression (Eqs. 6.19/6.20), the buckling interactions (Eqs. 6.23/6.24)
  and the lateral-torsional interaction (Eqs. 6.33/6.35).

The EN 1995-1-1:2025 (§8) versions live in
:mod:`eurocodepy.ec5.uls2025.bending`; the function names match so the two
editions are drop-in swappable.

Units: forces in kN, moments in kNm, section dimensions / moduli in m, and the
effective lengths ``l_0y`` / ``l_0z`` / ``l_0m`` in **mm**.
"""
import numpy as np

import eurocodepy as ec
from eurocodepy.ec5.materials import LoadDuration, ServiceClass, Timber, TimberForcesType
from eurocodepy.utils import CrossSection

LAMBDA_REL_C_LIM = 0.3      # §6.3.2(3): below this k_c = 1.0
LAMBDA_REL_M_LOW = 0.75     # §6.3.3(4): below this k_crit = 1.0
LAMBDA_REL_M_HIGH = 1.4     # §6.3.3(4): above this k_crit = 1/λ²
BETA_C_TIMBER = 0.2         # §6.3.2(3): solid timber
BETA_C_GLULAM = 0.1         # §6.3.2(3): glulam and LVL


def get_safety_factor(timber_type: str) -> float:
    """Partial factor γM for a timber type (EN 1995-1-1 Table 2.3).

    Args:
        timber_type (str): 'timber', 'glulam', 'lvl', …

    Returns:
        float: γM.

    """
    return ec.TimberParams["safety"][timber_type]


def calc_k_red(section: CrossSection) -> float:
    """Biaxial-bending redistribution factor ``k_m`` (EN 1995-1-1:2004 §6.1.6).

    ``k_m = 0.7`` for a rectangular section of solid timber, glulam or LVL and
    ``1.0`` for any other shape. Named ``calc_k_red`` so the function is shared
    with the :2025 edition.

    Args:
        section (CrossSection): Cross-section object.

    Returns:
        float: k_m.

    """
    return 0.7 if section.shape == "rectangular" else 1.0


def _beta_c(timber: Timber) -> float:
    """Straightness factor β_c — 0.2 solid timber, 0.1 glulam/LVL (§6.3.2(3))."""
    return BETA_C_TIMBER if timber.type == "timber" else BETA_C_GLULAM


def calc_k_c(l_0y: float, l_0z: float, section: CrossSection,
             timber: Timber) -> tuple[float, float]:
    """Column instability factors ``k_c,y`` / ``k_c,z`` (EN 1995-1-1:2004 §6.3.2).

    ``λ_rel = (l_ef / i) / π · √(f_c,0,k / E_0,05)`` (Eq. 6.21/6.22) with the
    radius of gyration ``i``; then (Eqs. 6.27-6.29)::

        k = 0.5·[1 + β_c·(λ_rel − 0.3) + λ_rel²]
        k_c = 1 / (k + √(k² − λ_rel²))          for λ_rel > 0.3, else 1.0

    Args:
        l_0y, l_0z (float): Effective (buckling) lengths about y / z [mm].
        section (CrossSection): Cross-section object (radius of gyration in m).
        timber (Timber): Timber object (f_c,0,k and E_0,05 = ``E0k``).

    Returns:
        (k_c_y, k_c_z).

    """
    e005 = timber.E0k
    fc0k = timber.fc0k
    beta_c = _beta_c(timber)

    def _kc(l0_mm: float, i_gyr: float) -> float:
        if l0_mm <= 0.0 or i_gyr <= 0.0:
            return 1.0                                # no buckling data → k_c = 1
        lam = (l0_mm / 1e3) / i_gyr                   # slenderness λ (Eq. 6.21)
        lam_rel = lam / np.pi * np.sqrt(fc0k / e005)  # Eq. 6.22
        if lam_rel <= LAMBDA_REL_C_LIM:
            return 1.0
        k = 0.5 * (1.0 + beta_c * (lam_rel - LAMBDA_REL_C_LIM) + lam_rel**2)
        return float(1.0 / (k + np.sqrt(k**2 - lam_rel**2)))

    return (_kc(l_0y, section.radius_y), _kc(l_0z, section.radius_z))


def calc_mcr(l_0m: float, section: CrossSection, timber: Timber) -> float:
    """Critical bending moment ``M_y,crit`` (EN 1995-1-1:2004 §6.3.3, Eq. 6.31).

    ``M_y,crit = (π / l_ef)·√(E_0,05·I_z·G_0,05·I_tor)`` — the elastic
    lateral-torsional buckling moment of the beam.

    Args:
        l_0m (float): Effective length for lateral-torsional buckling [mm].
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object (``E0k`` = E_0,05, ``Gk`` = G_0,05).

    Returns:
        float: M_y,crit [kNm] (∞ when ``l_0m`` ≤ 0 → no LTB).

    """
    lef = l_0m / 1e3                                  # mm → m
    if lef <= 0.0:
        return float("inf")
    e005 = timber.E0k
    g005 = timber.Gk
    iz = section.inertia_z
    itor = section.torsional_inertia
    return float(np.pi / lef * np.sqrt(e005 * g005 * iz * itor))


def calc_k_m(l_0m: float, section: CrossSection, timber: Timber) -> float:
    """Lateral-torsional stability factor ``k_crit`` (EN 1995-1-1:2004 §6.3.3).

    ``λ_rel,m = √(f_m,k / σ_m,crit)`` with ``σ_m,crit = M_y,crit / W_y``
    (Eq. 6.30), then (Eq. 6.34)::

        k_crit = 1.0                       λ_rel,m ≤ 0.75
        k_crit = 1.56 − 0.75·λ_rel,m       0.75 < λ_rel,m ≤ 1.4
        k_crit = 1 / λ_rel,m²              λ_rel,m > 1.4

    Named ``calc_k_m`` so the function is shared with the :2025 edition.

    Args:
        l_0m (float): Effective length for lateral-torsional buckling [mm].
        section (CrossSection): Cross-section object.
        timber (Timber): Timber object.

    Returns:
        float: k_crit.

    """
    m_cr = calc_mcr(l_0m, section, timber)
    wy = section.bend_mod_y
    if not np.isfinite(m_cr) or m_cr <= 0.0 or wy <= 0.0:
        return 1.0
    sig_crit = m_cr / wy                              # σ_m,crit (Eq. 6.30)
    lam_rel_m = np.sqrt(timber.fmk / sig_crit)
    if lam_rel_m <= LAMBDA_REL_M_LOW:
        return 1.0
    if lam_rel_m <= LAMBDA_REL_M_HIGH:
        return float(1.56 - 0.75 * lam_rel_m)
    return float(1.0 / lam_rel_m**2)


def check_bending_with_normal(n_ed: float, m_ed_y: float, m_ed_z: float,  # noqa: PLR0913, PLR0914, PLR0917
                    section: CrossSection, timber: Timber,
                    l_0y: float, l_0z: float, l_0m: float,
                    service_class: ServiceClass, load_duration: LoadDuration) -> dict:
    """Combined bending + axial check (EN 1995-1-1:2004 §6.2 / §6.3).

    Compression (``n_ed`` < 0):
      * ``check1`` / ``check2`` — cross-section, Eqs. 6.19 / 6.20;
      * ``check3`` — column buckling, max of Eqs. 6.23 / 6.24 (with ``k_c``);
      * ``check4`` — lateral-torsional + compression, Eq. 6.35 (with ``k_crit``).

    Tension (``n_ed`` ≥ 0):
      * ``check1`` / ``check2`` — cross-section, Eqs. 6.17 / 6.18;
      * ``check3`` — not applicable (sentinel);
      * ``check4`` — lateral-torsional, Eq. 6.33 (bending only, with ``k_crit``).

    Args:
        n_ed (float): Axial force [kN] (negative = compression).
        m_ed_y, m_ed_z (float): Bending moments about y / z [kNm].
        section, timber: Cross-section / material objects.
        l_0y, l_0z, l_0m (float): Effective lengths [mm].
        service_class, load_duration: EN 1995-1-1 design conditions.

    Returns:
        dict with ``report``, ``is_ok``, ``utilization``, ``checks``, ``k_c``,
        ``k_m`` (= k_crit).

    """
    timber.design_values(service_class=service_class, load_duration=load_duration)
    km = calc_k_red(section)                          # §6.1.6 biaxial factor
    fc0d = timber.fc0d
    ft0d = timber.ft0d
    k_hy = timber.k_h(section.height, TimberForcesType.Bending)
    fmdy = timber.fmd * k_hy
    k_hz = timber.k_h(section.width, TimberForcesType.Bending)
    fmdz = timber.fmd * k_hz

    # Stresses [MPa] (kN, kNm with section in m → /1e3 gives MPa).
    sig_ax = abs(n_ed) / section.area / 1e3
    sig_my = abs(m_ed_y) / section.bend_mod_y / 1e3
    sig_mz = abs(m_ed_z) / section.bend_mod_z / 1e3

    k_c = calc_k_c(l_0y=l_0y, l_0z=l_0z, section=section, timber=timber)
    k_crit = calc_k_m(l_0m=l_0m, section=section, timber=timber)

    if n_ed < 0.0:                                    # compression
        rc = sig_ax / fc0d
        check1 = rc**2 + (sig_my / fmdy) + km * (sig_mz / fmdz)          # 6.19
        check2 = rc**2 + km * (sig_my / fmdy) + (sig_mz / fmdz)          # 6.20
        # Column buckling (governing of the two axes), Eqs. 6.23 / 6.24.
        c23 = sig_ax / (k_c[0] * fc0d) + (sig_my / fmdy) + km * (sig_mz / fmdz)
        c24 = sig_ax / (k_c[1] * fc0d) + km * (sig_my / fmdy) + (sig_mz / fmdz)
        check3 = max(c23, c24)
        # Lateral-torsional buckling + compression, Eq. 6.35.
        check4 = (sig_my / (k_crit * fmdy))**2 + sig_ax / (k_c[1] * fc0d)
    else:                                             # tension
        rt = sig_ax / ft0d
        check1 = rt + (sig_my / fmdy) + km * (sig_mz / fmdz)             # 6.17
        check2 = rt + km * (sig_my / fmdy) + (sig_mz / fmdz)             # 6.18
        check3 = True                                 # no column buckling in tension
        check4 = sig_my / (k_crit * fmdy) + km * (sig_mz / fmdz)         # 6.33

    check = (check1 <= 1.0 and check2 <= 1.0
             and (check3 is True or check3 <= 1.0) and check4 <= 1.0)
    _c3 = 0.0 if check3 is True else float(check3)
    utilization = max(float(check1), float(check2), _c3, float(check4))

    s = (
        f"EC5:2004 bending + axial check\n"
        f"  A = {section.area:.4f} m²  W_y = {section.bend_mod_y:.6f} m³\n"
        f"  N_ed = {n_ed:.2f} kN  M_y = {m_ed_y:.2f} kNm  M_z = {m_ed_z:.2f} kNm\n"
        f"  fc0d = {fc0d:.2f}  ft0d = {ft0d:.2f}  fmdy = {fmdy:.2f}  "
        f"fmdz = {fmdz:.2f} MPa  km = {km:.2f}\n"
        f"  k_cy = {k_c[0]:.3f}  k_cz = {k_c[1]:.3f}  k_crit = {k_crit:.3f}\n"
        f"  checks: {float(check1):.3f} / {float(check2):.3f} / {_c3:.3f} / "
        f"{float(check4):.3f}  → util {utilization:.3f} "
        f"({'OK' if check else 'NOT OK'})\n"
    )

    return {
        "report": s,
        "is_ok": check,
        "utilization": utilization,
        "checks": {"check1": float(check1), "check2": float(check2),
                   "check3": _c3, "check4": float(check4)},
        "k_c": (float(k_c[0]), float(k_c[1])),
        "k_m": float(k_crit),
    }
