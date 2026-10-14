# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Time-dependent behaviour of concrete and prestressing steel — **EN 1992-1-1:2023 Annex B**.

Strength and stiffness development (B.4), creep (B.5, B.8), shrinkage (B.6), the
calibration with tests (B.7) and the relaxation of prestressing steel (B.9), plus the
simplified values after 50 years of Tables 5.2 and 5.3 (``Editions.ec2["2023"].creep_shrinkage``;
Table 5.3 is an NDP, ``annex=`` applies a national annex).

The 2004 counterparts (EN 1992-1-1:2004 3.1.4, 3.1.2 and Annex B) are
:func:`eurocodepy.ec2.materials.calc_creep_coef` and ``calc_shrink_strain``; the models are
different (this one has basic and drying components, the strength classes CS/CN/CR and
``fcm,28``). ``eurocodepy.ec2.sls.creep_coef`` and ``shrink_strain`` are the same Annex B model
in a bare, array-friendly form (no validation, no class check); they give the same numbers
as :func:`creep_coefficient` and :func:`shrinkage_total` where both apply. These functions are
scalar and validated (RH, ``fcm,28``, ages, strength class) and add the strength and stiffness
development, the non-linear creep, the creep function, the test calibration, the tables of
50 years and the relaxation of prestressing steel.

Units: ages and durations in **days**, strengths and moduli in **MPa**, the notional
size ``hn = 2·Ac/u`` in **mm**, relative humidity ``RH`` in **%**, temperatures in **°C**,
shrinkage strains dimensionless (not per mille). The functions of ages, durations,
humidity and strength accept numpy arrays (broadcasting) as well as scalars, e.g. a whole
time history; the tables and the relaxation classes are scalar. ``fcm28`` is the mean compressive
strength at 28 days, ``fck + 8`` for a class of Table 5.1. The relations are valid for
12 ≤ fck ≤ 100 MPa, ``σc ≤ 0,40·fcm(t0)``, 20 % ≤ RH ≤ 100 %, 5 °C ≤ T ≤ 30 °C and a loading age of
at least 1 day (B.3(3)).
"""

import math

import numpy as np

from eurocodepy import dbase

STRENGTH_CLASSES = ("CS", "CN", "CR")       # Table B.1 (NDP): slow, normal, rapid
_S_C = {                                    # Table B.2, by fck: ≤ 35, < 60, ≥ 60
    "CS": (0.6, 0.5, 0.4), "CN": (0.5, 0.4, 0.3), "CR": (0.3, 0.2, 0.1)}
_ALPHA_SC = {"CS": -1.0, "CN": 0.0, "CR": 1.0}       # B.5(4)
_ALPHA_BS_DS = {"CS": (800.0, 3.0), "CN": (700.0, 4.0), "CR": (600.0, 6.0)}   # Table B.3
_FCK_MIN, _FCK_MAX = 12.0, 100.0
_RH_MIN = 20.0
_FCM_OFFSET = 8.0
_FRACTILES = {"0.05": 0.5, "0.10": 0.6, "0.90": 1.4, "0.95": 1.5}   # B.5(8), B.6(4)


def _check_class(cls: str) -> str:
    c = str(cls).upper()
    if c not in STRENGTH_CLASSES:
        msg = f"strength development class must be one of {STRENGTH_CLASSES}, got '{cls}'"
        raise ValueError(msg)
    return c


def _check_fcm(fcm28: float) -> None:
    f = np.asarray(fcm28, dtype=float)
    if np.any((f < _FCK_MIN + _FCM_OFFSET) | (f > _FCK_MAX + _FCM_OFFSET)):
        msg = (f"fcm,28 = {np.min(f):g}..{np.max(f):g} MPa is outside the validity of Annex B "
               f"(12 ≤ fck ≤ 100 MPa, B.3(3))")
        raise ValueError(msg)


def _check_rh(rh: float) -> None:
    r = np.asarray(rh, dtype=float)
    if np.any((r < _RH_MIN) | (r > 100.0)):
        msg = f"RH = {np.min(r):g}..{np.max(r):g} % is outside 20 % ≤ RH ≤ 100 % (B.3(3))"
        raise ValueError(msg)


# ── B.4 Strength and stiffness with time ────────────────────────────────────

def calc_s_c(fck: float, cls: str = "CN") -> float:
    """Return the coefficient ``sC`` of Table B.2 (``fck`` ≤ 35, 35-60, ≥ 60 MPa)."""
    row = _S_C[_check_class(cls)]
    if fck <= 35.0:  # noqa: PLR2004
        return row[0]
    return row[1] if fck < 60.0 else row[2]  # noqa: PLR2004


def calc_beta_cc(t: float, fck: float, cls: str = "CN", t_ref: float = 28.0) -> float:
    """Return ``βcc(t) = exp[sC·(1 − √(tref/t))·√(28/tref)]`` for ``t ≤ tref``, Eq. (B.2); 1 after.

    ``t`` in days (temperature-adjusted age where relevant), ``t_ref`` 28 days in general
    (28 to 91 days when specified, 5.1.3(2)).
    """
    t = np.asarray(t, dtype=float)
    if np.any(t <= 0.0):
        msg = "the age t must be positive"
        raise ValueError(msg)
    early = np.exp(calc_s_c(fck, cls) * (1.0 - np.sqrt(t_ref / t)) * math.sqrt(28.0 / t_ref))
    return np.where(t >= t_ref, 1.0, early)[()]


def fcm_t(t: float, fcm: float, fck: float, cls: str = "CN", t_ref: float = 28.0) -> float:
    """Return ``fcm(t) = βcc(t)·fcm`` [MPa], Eq. (B.1)."""
    return calc_beta_cc(t, fck, cls, t_ref) * fcm


def fctm_t(t: float, fctm: float, fck: float, cls: str = "CN", t_ref: float = 28.0) -> float:
    """Return ``fctm(t) = βcc(t)^0,6·fctm`` [MPa], Eq. (B.3)."""
    return calc_beta_cc(t, fck, cls, t_ref) ** 0.6 * fctm


def ecm_t(t: float, ecm: float, fck: float, cls: str = "CN", t_ref: float = 28.0) -> float:
    """Return ``Ecm(t) = βcc(t)^(1/3)·Ecm`` [MPa], Eq. (B.4)."""
    return calc_beta_cc(t, fck, cls, t_ref) ** (1.0 / 3.0) * ecm


def temperature_adjusted_age(durations: list[float], temperatures: list[float]) -> float:
    """Return the temperature-adjusted age ``tT = Σ Δti·exp(13,65 − 4000/(273 + T(Δti)))`` [days], Eq. (B.18).

    Valid for 0 °C ≤ T ≤ 80 °C; 20 °C gives the age itself.
    """
    if len(durations) != len(temperatures):
        msg = "durations and temperatures must have the same length"
        raise ValueError(msg)
    for temp in temperatures:
        if not 0.0 <= temp <= 80.0:  # noqa: PLR2004
            msg = f"T = {temp:g} °C is outside 0 °C ≤ T ≤ 80 °C (B.5(5))"
            raise ValueError(msg)
    return float(sum(d * math.exp(13.65 - 4000.0 / (273.0 + temp))
                     for d, temp in zip(durations, temperatures)))


# ── B.5 Creep ───────────────────────────────────────────────────────────────

def calc_alpha_c(fcm28: float) -> float:
    """Return ``αc = 1/(0,8 + 0,2·fcm,28/88) ≥ 1,0``, Eq. (B.22) (``Ec = αc·Ecm,28``, B.21)."""
    return np.maximum(1.0 / (0.8 + 0.2 * np.asarray(fcm28, dtype=float) / 88.0), 1.0)[()]


def adjusted_loading_age(t0: float, cls: str = "CN") -> float:
    """Return ``t0,adj = t0,T·[9/(2 + t0,T^1,2) + 1]^αSC ≥ 0,5`` [days], Eq. (B.17).

    ``t0`` is the age at loading adjusted for temperature (Eq. B.18); ``αSC`` is −1, 0 and 1
    for the classes CS, CN and CR.
    """
    a = _ALPHA_SC[_check_class(cls)]
    t0 = np.asarray(t0, dtype=float)
    return np.maximum(t0 * (9.0 / (2.0 + t0**1.2) + 1.0) ** a, 0.5)[()]


def _check_times(t: float, t0: float) -> None:
    if np.any(np.asarray(t0, dtype=float) < 1.0):
        msg = "the age at loading must be at least 1 day (B.3(3))"
        raise ValueError(msg)
    if np.any(np.asarray(t, dtype=float) < np.asarray(t0, dtype=float)):
        msg = "t must not be less than t0"
        raise ValueError(msg)


def creep_basic(t: float, t0: float, fcm28: float, cls: str = "CN",
                xi_bc1: float = 1.0, xi_bc2: float = 1.0, t0_T: float | None = None) -> float:
    """Return the basic creep coefficient ``φbc(t,t0) = βbc,fcm·βbc,t−t0``, Eqs. (B.6)-(B.8).

    ``βbc,fcm = 1,8/fcm,28^0,7``; ``βbc,t−t0 = ln[(30/t0,adj + 0,035)²·(t − t0)/ξbc2 + 1]``. ``xi_bc1``
    and ``xi_bc2`` are the factors calibrated with tests (B.7, Eqs. B.34-B.35). ``t0`` is the real
    age at loading (the duration is ``t − t0``); ``t0_T`` its temperature-adjusted value of Eq. (B.18)
    that goes into ``t0,adj`` (B.17): ``None`` for 20 °C.
    """
    _check_times(t, t0)
    _check_fcm(fcm28)
    t0a = adjusted_loading_age(t0 if t0_T is None else t0_T, cls)
    fcm28 = np.asarray(fcm28, dtype=float)
    b_fcm = 1.8 / fcm28**0.7
    b_t = np.log((30.0 / t0a + 0.035) ** 2 * (np.asarray(t, dtype=float) - t0) / xi_bc2 + 1.0)
    return (xi_bc1 * b_fcm * b_t)[()]


def creep_drying(t: float, t0: float, fcm28: float, rh: float, hn: float, cls: str = "CN",
                 xi_dc1: float = 1.0, xi_dc2: float = 1.0, t0_T: float | None = None) -> float:
    """Return the drying creep coefficient ``φdc = βdc,fcm·βdc,RH·βdc,t0·βdc,t−t0``, Eqs. (B.9)-(B.16).

    ``βdc,fcm = 412/fcm,28^1,4``; ``βdc,RH = (1 − RH/100)/(0,1·hn/100)^(1/3)``;
    ``βdc,t0 = 1/(0,1 + t0,adj^0,2)``; ``βdc,t−t0 = [(t − t0)/(βh·ξdc2 + (t − t0))]^γ`` with
    ``γ = 1/(2,3 + 3,5/√t0,adj)``, ``βh = min(1,5·hn + 250·αfcm, 1500·αfcm)`` and
    ``αfcm = (35/fcm,28)^0,5``. ``hn`` in mm; ``xi_dc1``, ``xi_dc2`` as B.7 (Eq. B.36); ``t0_T`` as in :func:`creep_basic`.
    """
    _check_times(t, t0)
    _check_fcm(fcm28)
    _check_rh(rh)
    t0a = adjusted_loading_age(t0 if t0_T is None else t0_T, cls)
    fcm28, rh, hn = (np.asarray(v, dtype=float) for v in (fcm28, rh, hn))
    b_fcm = 412.0 / fcm28**1.4
    b_rh = (1.0 - rh / 100.0) / (0.1 * hn / 100.0) ** (1.0 / 3.0)
    b_t0 = 1.0 / (0.1 + t0a**0.2)
    gamma = 1.0 / (2.3 + 3.5 / np.sqrt(t0a))
    alpha_fcm = (35.0 / fcm28) ** 0.5
    beta_h = np.minimum(1.5 * hn + 250.0 * alpha_fcm, 1500.0 * alpha_fcm)
    dt = np.asarray(t, dtype=float) - t0
    b_t = (dt / (beta_h * xi_dc2 + dt)) ** gamma
    return (xi_dc1 * b_fcm * b_rh * b_t0 * b_t)[()]


def creep_coefficient(t: float, t0: float, fcm28: float, rh: float, hn: float,
                      cls: str = "CN", t0_T: float | None = None, **xi: float) -> float:
    """Return the total mean creep coefficient ``φ(t,t0) = φbc + φdc``, Eq. (B.5).

    ``t0_T``: temperature-adjusted age at loading (B.18, ``None`` for 20 °C). ``**xi`` passes ``xi_bc1``,
    ``xi_bc2``, ``xi_dc1``, ``xi_dc2`` (B.7). Example: C30/37,
    CN cement, RH = 50 %, ``hn`` = 200 mm, loaded at 28 days, after 50 years: about 2,2.
    """
    bc = {k: v for k, v in xi.items() if k.startswith("xi_bc")}
    dc = {k: v for k, v in xi.items() if k.startswith("xi_dc")}
    unknown = set(xi) - set(bc) - set(dc)
    if unknown:
        msg = f"unknown factors {sorted(unknown)}; use xi_bc1, xi_bc2, xi_dc1, xi_dc2"
        raise TypeError(msg)
    return (creep_basic(t, t0, fcm28, cls, t0_T=t0_T, **bc)
            + creep_drying(t, t0, fcm28, rh, hn, cls, t0_T=t0_T, **dc))


def creep_nonlinear(phi: float, k_sigma: float) -> float:
    """Return ``φσ = φ·exp[1,5·(kσ − 0,4)]`` for ``0,4 < kσ ≤ 0,6`` (``kσ = σc/fcm(t0)``), Eq. (B.19).

    Below 0,4 the creep is linear and ``φ`` is returned; above 0,6 is outside the model.
    """
    k = np.asarray(k_sigma, dtype=float)
    if np.any(k > 0.6):  # noqa: PLR2004
        msg = "kσ > 0,6: outside the creep model (B.5(6))"
        raise ValueError(msg)
    return np.where(k <= 0.4, phi, phi * np.exp(1.5 * (k - 0.4)))[()]  # noqa: PLR2004


def characteristic_value(value: float, fractile: str) -> float:
    """Return a characteristic value of the creep coefficient or the shrinkage strain, B.5(8), B.6(4).

    ``fractile``: ``"0.05"`` (0,5·), ``"0.10"`` (0,6·), ``"0.90"`` (1,4·) or ``"0.95"`` (1,5·).
    """
    if fractile not in _FRACTILES:
        msg = f"fractile must be one of {tuple(_FRACTILES)}, got '{fractile}'"
        raise ValueError(msg)
    return _FRACTILES[fractile] * value


def creep_strain(phi: float, sigma_c: float, e_c28: float) -> float:
    """Return the creep strain ``εcc = φ·σc/Ec,28``, Eq. (B.20); ``σc`` [MPa] compression positive."""
    return phi * sigma_c / e_c28


def creep_compliance(t: float, t0: float, fcm28: float, ecm28: float, rh: float, hn: float,
                     cls: str = "CN", fck: float | None = None, t_ref: float = 28.0) -> float:
    """Return the creep function ``J(t,t0) = 1/Ec(t0) + φ(t,t0)/Ec(28)`` [1/MPa], Eq. (B.40).

    ``Ec = αc·Ecm`` (Eqs. B.21-B.22); ``Ec(t0)`` uses ``Ecm(t0)`` of Eq. (B.4) (``fck`` defaults to
    ``fcm28 − 8``). ``ecm28`` is the secant modulus at 28 days.
    """
    ck = fcm28 - _FCM_OFFSET if fck is None else fck
    ac = calc_alpha_c(fcm28)
    ec_t0 = ac * ecm_t(t0, ecm28, ck, cls, t_ref)
    ec28 = ac * ecm28
    return 1.0 / ec_t0 + creep_coefficient(t, t0, fcm28, rh, hn, cls) / ec28


def strain_history(t: float, increments: list[tuple[float, float]], fcm28: float, ecm28: float,
                   rh: float, hn: float, cls: str = "CN", fck: float | None = None) -> float:
    """Return the stress-dependent strain ``εcσ(t) = Σ Δσc(τi)·J(t,τi)`` by superposition, Eq. (B.41).

    ``increments`` is ``[(τ0, σc(t0)), (τ1, Δσc1), ...]`` (age [days], stress [MPa]; the first is the
    stress at first loading). Linear creep only (``σc ≤ 0,40·fcm``).
    """
    return sum(ds * creep_compliance(t, tau, fcm28, ecm28, rh, hn, cls, fck) for tau, ds in increments)


# ── B.6 Shrinkage ───────────────────────────────────────────────────────────

def shrinkage_basic(t: float, fcm28: float, cls: str = "CN", alpha_ndp_b: float = 1.0,
                    xi_bs1: float = 1.0, xi_bs2: float = 1.0) -> float:
    """Return the basic shrinkage strain ``εcbs(t) = εcbs,fcm·βbs,t·αNDP,b``, Eqs. (B.24), (B.26), (B.27).

    ``εcbs,fcm = αbs·(fcm,28/(60 + fcm,28))^2,5·10⁻⁶`` (Table B.3), ``βbs,t = 1 − exp(−0,2·ξbs2·√t)``;
    ``t`` is the concrete age [days]. ``xi_bs1`` and ``xi_bs2``: B.7 (Eqs. B.37-B.38).
    """
    _check_fcm(fcm28)
    alpha_bs = _ALPHA_BS_DS[_check_class(cls)][0]
    fcm28 = np.asarray(fcm28, dtype=float)
    e_fcm = alpha_bs * (fcm28 / (60.0 + fcm28)) ** 2.5 * 1.0e-6
    return (xi_bs1 * e_fcm * (1.0 - np.exp(-0.2 * xi_bs2 * np.sqrt(np.asarray(t, dtype=float))))
            * alpha_ndp_b)[()]


def rh_eq(fcm28: float) -> float:
    """Return ``RHeq = 99·(35/fcm,28)^0,1 ≤ 99`` [%], Eq. (B.32)."""
    return np.minimum(99.0 * (35.0 / np.asarray(fcm28, dtype=float)) ** 0.1, 99.0)[()]


def calc_beta_rh(rh: float, fcm28: float) -> float:
    """Return ``βRH`` of Eqs. (B.29)-(B.31): 1,55·[1 − (RH/RHeq)³] up to ``RHeq``, 1,55·[1 − (RH/RHeq)²] above,
    and −0,25 more at RH = 100 % (water available)."""
    _check_rh(rh)
    rh = np.asarray(rh, dtype=float)
    eq = rh_eq(fcm28)
    r = rh / eq
    return np.where(rh <= eq, 1.55 * (1.0 - r**3),
                    np.where(rh < 100.0, 1.55 * (1.0 - r**2), 1.55 * (1.0 - r**2) - 0.25))[()]  # noqa: PLR2004


def shrinkage_drying(t: float, ts: float, fcm28: float, rh: float, hn: float, cls: str = "CN",
                     alpha_ndp_d: float = 1.0, xi_ds1: float = 1.0, xi_ds2: float = 1.0) -> float:
    """Return the drying shrinkage strain ``εcds(t − ts) = εcds,fcm·βRH·βds,t−ts·αNDP,d``, Eqs. (B.25), (B.28)-(B.33).

    ``εcds,fcm = (220 + 110·αds)·exp(−0,012·fcm,28)·10⁻⁶`` (Table B.3);
    ``βds,t−ts = √[(t − ts)/(0,035·ξds2·hn² + (t − ts))]``. ``ts`` is the age at the start of drying [days],
    ``hn`` in mm; ``xi_ds1``, ``xi_ds2``: B.7 (Eqs. B.37, B.39).
    """
    if np.any(np.asarray(t, dtype=float) < np.asarray(ts, dtype=float)):
        msg = "t must not be less than ts"
        raise ValueError(msg)
    _check_fcm(fcm28)
    alpha_ds = _ALPHA_BS_DS[_check_class(cls)][1]
    fcm28 = np.asarray(fcm28, dtype=float)
    e_fcm = (220.0 + 110.0 * alpha_ds) * np.exp(-0.012 * fcm28) * 1.0e-6
    d = np.asarray(t, dtype=float) - ts
    hn = np.asarray(hn, dtype=float)
    b_ds = np.sqrt(d / (0.035 * xi_ds2 * hn**2 + d))
    return (xi_ds1 * e_fcm * calc_beta_rh(rh, fcm28) * b_ds * alpha_ndp_d)[()]


def shrinkage_total(t: float, ts: float, fcm28: float, rh: float, hn: float, cls: str = "CN",
                    alpha_ndp_b: float = 1.0, alpha_ndp_d: float = 1.0, **xi: float) -> float:
    """Return the total shrinkage strain ``εcs(t,ts) = εcbs(t) + εcds(t − ts)``, Eq. (B.23).

    ``t`` is the concrete age [days], ``ts`` the age at the start of drying; ``αNDP`` are 1,0 unless the
    National Annex says otherwise; ``**xi``: ``xi_bs1``, ``xi_bs2``, ``xi_ds1``, ``xi_ds2`` (B.7).
    Shrinkage is positive (shortening).
    """
    bs = {k: v for k, v in xi.items() if k.startswith("xi_bs")}
    ds = {k: v for k, v in xi.items() if k.startswith("xi_ds")}
    unknown = set(xi) - set(bs) - set(ds)
    if unknown:
        msg = f"unknown factors {sorted(unknown)}; use xi_bs1, xi_bs2, xi_ds1, xi_ds2"
        raise TypeError(msg)
    return (shrinkage_basic(t, fcm28, cls, alpha_ndp_b, **bs)
            + shrinkage_drying(t, ts, fcm28, rh, hn, cls, alpha_ndp_d, **ds))


# ── Tables 5.2 and 5.3: values after 50 years ───────────────────────────────

def _interp(x: float, xs: list[float], ys: list[float], name: str, *, log: bool = False) -> float:
    if not xs[0] - 1e-9 <= x <= xs[-1] + 1e-9:
        msg = f"{name} = {x:g} is outside the range {xs[0]:g}-{xs[-1]:g} of the table: use Annex B"
        raise ValueError(msg)
    for i in range(len(xs) - 1):
        if x <= xs[i + 1] + 1e-9:
            a, b = (math.log(xs[i]), math.log(xs[i + 1])) if log else (xs[i], xs[i + 1])
            xv = math.log(x) if log else x
            w = (xv - a) / (b - a)
            return ys[i] + w * (ys[i + 1] - ys[i])
    return ys[-1]


def _column(rh: float) -> str:
    if rh not in (50, 80):
        msg = "Tables 5.2 and 5.3 give RH = 50 % (dry) and RH = 80 % (humid) only: use Annex B"
        raise ValueError(msg)
    return "dry" if rh == 50 else "humid"  # noqa: PLR2004


def creep_coefficient_50y(t0: float, cls: str, rh: float, hn: float, fck: float,
                          annex: str | None = None) -> float:
    """Return ``φ(50y, t0)`` of Table 5.2, interpolated (``t0`` logarithmically, ``hn`` linearly).

    ``rh`` is 50 or 80; the table is for ``fck,28 = 35`` MPa and 12 ≤ fck ≤ 100 MPa is handled with the
    factor ``(35/fck)^A`` (``A`` of the table, interpolated in ``hn``). Used where
    ``σc ≤ 0,40·fcm(t0)`` and great accuracy is not required (5.1.5(2)).
    """
    cls = _check_class(cls)
    if not _FCK_MIN <= fck <= _FCK_MAX:
        msg = "12 MPa ≤ fck ≤ 100 MPa (Table 5.2)"
        raise ValueError(msg)
    tab = dbase.get_edition_params("ec2", "creep_shrinkage", "2023", annex)
    col = _column(rh)
    hns = tab["hn"]
    c = tab["creep_50y"]
    per_age = [_interp(hn, hns, row, "hn") for row in c[col]]
    phi35 = _interp(t0, c["t0"][cls], per_age, "t0", log=True)
    a = _interp(hn, hns, c["A_" + col], "hn")
    return phi35 * (35.0 / fck) ** a


def shrinkage_50y(cls: str, rh: float, hn: float, fck: float, annex: str | None = None) -> float:
    """Return the nominal total shrinkage ``εcs`` after 50 years of drying of Table 5.3 (NDP), dimensionless.

    Interpolated linearly in ``hn`` and ``fck``; ``rh`` is 50 or 80. The classes have different ranges
    of ``fck`` (CS 20-50, CN 20-80, CR 35-80 MPa).
    """
    cls = _check_class(cls)
    tab = dbase.get_edition_params("ec2", "creep_shrinkage", "2023", annex)
    col = _column(rh)
    s = tab["shrinkage_50y"][cls]
    per_fck = [_interp(hn, tab["hn"], row, "hn") for row in s[col]]
    return _interp(fck, s["fck"], per_fck, "fck") * 1.0e-3


# ── B.9 Relaxation of prestressing steel ────────────────────────────────────

_RHO_1000 = {                  # Table B.4: initial stress / fp -> (wires and strands, bars φ ≤ 15, bars φ > 15) [%]
    0.5: (0.0, 0.0, 0.0),
    0.7: (2.5, 6.0, 4.0),
    0.8: (4.5, None, None),
}
_REL_KINDS = ("wire", "bar")


def relaxation_rho1000(sigma_pi_over_fp: float, kind: str = "wire", phi: float = 0.0) -> float:
    """Return ``ρ1000`` [%], the relaxation loss at 1 000 h, Table B.4 (linear interpolation, Note 2).

    ``kind``: ``"wire"`` (wires and strands) or ``"bar"`` (then ``phi`` [mm] ≤ 15 or > 15). Initial stress
    between 50 % and 80 % of ``fp`` for wires and strands, 50 % to 70 % for bars.
    """
    if kind not in _REL_KINDS:
        msg = f"kind must be one of {_REL_KINDS}, got '{kind}'"
        raise ValueError(msg)
    idx = 0 if kind == "wire" else (1 if phi <= 15.0 else 2)  # noqa: PLR2004
    pts = [(k, v[idx]) for k, v in sorted(_RHO_1000.items()) if v[idx] is not None]
    if not pts[0][0] - 1e-9 <= sigma_pi_over_fp <= pts[-1][0] + 1e-9:
        msg = (f"σpi/fp = {sigma_pi_over_fp:g} is outside {pts[0][0]:g}-{pts[-1][0]:g} "
               "for this prestressing steel (Table B.4): use test results")
        raise ValueError(msg)
    return _interp(sigma_pi_over_fp, [p[0] for p in pts], [p[1] for p in pts], "σpi/fp")


def relaxation_loss(t: float, sigma_pi: float, rho_1000: float, k_rho: float = 0.16) -> float:
    """Return the relaxation loss ``Δσpr = σpi·ρ1000/100·(24·t/1000)^kρ``, Eq. (B.43).

    ``t`` in days (24·t hours), ``rho_1000`` in %, ``kρ`` = 0,16 unless there is more accurate data;
    in the unit of ``sigma_pi``.
    """
    return sigma_pi * rho_1000 / 100.0 * (24.0 * np.asarray(t, dtype=float) / 1000.0) ** k_rho


def relaxation_loss_fit(t: float, sigma_pi: float, a: float, b: float) -> float:
    """Return ``Δσpr = σpi·b·t^a`` of the best-fit curve of relaxation tests, Eq. (B.44)."""
    return sigma_pi * b * np.asarray(t, dtype=float) ** a
