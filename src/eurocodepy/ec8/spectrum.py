# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
"""Module for Eurocode 8 Seismic Design Response Spectrum calculations.

It includes functions for generating design response spectra,
retrieving national annex parameters, and writing design response spectra to a file.
It also includes classes for representing soil amplification, reference acceleration,
and spectrum shape parameters.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eurocodepy import dbase


def get_spec_params(locale: str, code: str, class_imp: str,  # noqa: PLR0914
                    soil: str, zone: str) -> tuple:
    """Get the spectrum parameters.

    Args:
        locale (str): country code (EU, PT)
        code (str):
                CEN-1, CEN-2: standard Eurocode spectrums (EU)
                PT1, PT2, PTA: Portuguese National Annex spectrums (PT)
                (PT1 and PT2, for continent and Madeira, PTA for Azores)
        class_imp (str): importance class  (i, ii, iii, iv)
        soil (str): soil type (A, B, C, D, E)
        zone (str): (1_1, 1_2, 1_3, 1_4, 1_5, 1_6) for "PT-1"
                    (2.1, 2.2, 2.3, 2.4, 2.5) for "PT-2" and "PT-A"
                    (.1g, .2g, .3g, ..., .8g, .9g, 1_0g) for "CEN-1" and "CEN-2"

    Raises:
        ValueError: if locale is not available
        ValueError: if code is not available
        ValueError: if class_imp is not available

    Returns:
        list: soil amplification factor, acceleration, T_B, T_C, T_D

    """
    local = dbase.SeismicLoads["Locale"][locale]

    if code not in local["Types"]:
        msg = f"Code {code} not available for locale {locale}"
        raise ValueError(msg)

    class_imp = str.lower(class_imp)
    if class_imp not in local["ImportanceClass"]:
        msg = f"Class {class_imp} not available for locale {locale}"
        raise ValueError(msg)

    zone = zone.replace(".", "_")
    if zone not in local["a_gR"][code]:
        msg = f"Zone {zone} not available for locale {locale}"
        raise ValueError(msg)

    soil = str.upper(soil)
    if soil not in local["SoilType"]:
        msg = f"Soil {soil} not available for code {code}"
        raise ValueError(msg)

    importance_coef = local["ImportanceCoef"][code][class_imp]
    a_gr = local["a_gR"][code][zone]
    a_g = a_gr * importance_coef

    t_b = local["Spectrum"][code][soil]["T_B"]
    t_c = local["Spectrum"][code][soil]["T_C"]
    t_d = local["Spectrum"][code][soil]["T_D"]
    s_max = local["Spectrum"][code][soil]["S_max"]
    s_min = local["Spectrum"][code][soil]["S_min"]
    ag1 = local["Spectrum"][code][soil]["a_g1"]
    ag2 = local["Spectrum"][code][soil]["a_g2"]
    if a_g <= ag1:
        s_val = s_max
    elif a_g >= ag2:
        s_val = s_min
    else:
        s_val = s_max - (s_max - s_min) * (a_g - ag1) / (ag2 - ag1)
    return s_val, a_g, t_b, t_c, t_d


def get_spectrum_parameters(code: str, coef_imp: str, soil: str, zone: str) -> tuple:  # noqa: PLR0914
    """Get the spectrum parameters.

    Args:
        code (str): code to be used (CEN-1, CEN-2, PT-1, PT-2, PT-A)
                CEN-1, CEN-2: standard Eurocode spectrums
                PT-1, PT-2, PT-A: Portuguese National Annex spectrums
                    (PT-1 and PT-2, for continent and Madeira, PT-A for Azores)
        coef_imp (str): importance coefficient (i, ii, iii, iv)
        soil (str): soil type (A, B, C, D, E)
        zone (str): zone (1_1, 1_2, 1_3, 1_4, 1_5, 1_6, 2.1, 2.2, 2.3, 2.4, 2.5, .1g,
        .2g, .3g, .4g, .5g, .6g, .7g, .8g, .9g, 1_0g)

    Returns:
        list: soil amplification factor, acceleration, T_B, T_C, T_D

    """
    # accelarations
    a_gr = {"1_1": 2.5, "1_2": 2.0, "1_3": 1_5, "1_4": 1_0, "1_5": 0.6, "1_6": 0.35,
            "2.1": 2.5, "2.2": 2.0, "2.3": 1.7, "2.4": 1.1, "2.5": 0.8,
            ".1g": 0.980665, ".2g": 1.96133, ".3g":  2.941995, ".4g": 3.92266,
            ".5g": 4.903325, ".6g": 5.88399, ".7g": 6.864655, ".8g": 7.84532,
            ".9g": 8.825985, "1_0g": 9.80665}

    index1 = ["i", "ii", "iii", "iv"]
    gama_f = {"CEN-1": [0.8, 1.0, 1.2, 1.4],
            "CEN-2": [0.8, 1.0, 1.2, 1.4],
            "PT-1": [0.65, 1.0, 1.45, 1.95],
            "PT-2": [0.75, 1.0, 1.25, 1.5],
            "PT-A": [0.85, 1.0, 1.15, 1.35]}
    coefs = pd.DataFrame(gama_f, index=index1)

    coef_imp = str.lower(coef_imp)
    a_g = a_gr[zone] * coefs.at[coef_imp, code]  # noqa: PD008

    soil = str.upper(soil)
    index = ["A", "B", "C", "D", "E"]
    code = str.upper(code)
    if code == "CEN-1":
        data = {"S_max": [1.0, 1.2, 1.15, 1.35, 1.4],
                "T_B": [0.15, 0.15, 0.2, 0.2, 0.15],
                "T_C": [0.4, 0.5, 0.6, 0.8, 0.5],
                "T_D": [2.0, 2.0, 2.0, 2.0, 2.0],
                }
    elif code == "CEN-2":
        data = {"S_max": [1.0, 1.35, 1.5, 1.8, 1.6],
                "T_B": [0.05, 0.05, 0.1, 0.1, 0.05],
                "T_C": [0.25, 0.25, 0.25, 0.3, 0.25],
                "T_D": [1.2, 1.2, 1.2, 1.2, 1.2],
                }
    elif code in {"PT-2", "PT-A"}:
        data = {"S_max": [1.0, 1.35, 1.60, 2.0, 1.8],
                "T_B": [0.1, 0.1, 0.1, 0.1, 0.1],
                "T_C": [0.25, 0.25, 0.25, 0.3, 0.25],
                "T_D": [2.0, 2.0, 2.0, 2.0, 2.0],
                }
    elif code == "PT-1":
        data = {"S_max": [1.0, 1.35, 1.60, 2.0, 1.8],
                "T_B": [0.1, 0.1, 0.1, 0.1, 0.1],
                "T_C": [0.6, 0.6, 0.6, 0.8, 0.6],
                "T_D": [2.0, 2.0, 2.0, 2.0, 2.0],
                }
    values = pd.DataFrame(data, index=index)

    s_max = values.at[soil, "S_max"]  # noqa: PD008

    if code in {"CEN-1", "CEN-2"} or a_g <= 1.0:
        s_val = s_max
    elif a_g >= 4.0:
        s_val = 1.0
    else:
        s_val = s_max - (s_max - 1.0) * (a_g - 1.0) / 3.0

    t_b = values.at[soil, "T_B"]  # noqa: PD008
    t_c = values.at[soil, "T_C"]  # noqa: PD008
    t_d = values.at[soil, "T_D"]  # noqa: PD008

    return s_val, a_g, t_b, t_c, t_d


def calc_spectrum(period: float, a_g: float, s_val: float, q: float,  # noqa: PLR0913, PLR0917
            t_b: float, t_c: float, t_d: float, beta: float = 0.2) -> float:
    """Calculate the spectrum value for a given period, T.

    Args:
        period (float): period (s)
        a_g (float): acceleration (m/s2)
        s_val (float): soil amplification factor
        q (float): behaviour factor
        t_b (float): spectrum parameter
        t_c (float): spectrum parameter
        t_d (float): spectrum parameter
        beta (float, optional): the limiting value of the spectrum. Defaults to 0.2.

    Returns:
        float: the spectrum value

    """
    ag_s = a_g * s_val

    if t_b > period:
        spec = ag_s * (2.0 / 3.0 + period / t_b * (2.5 / q - 2.0 / 3.0))
    elif t_c > period:
        spec = ag_s * 2.5 / q
    elif t_d > period:
        spec = max(ag_s * 2.5 / q * (t_c) / period, beta * ag_s)
    else:
        spec = max(ag_s * 2.5 / q * (t_c * t_d) / period**2, beta * ag_s)

    return spec


def get_spectrum_ec8(locale: str, code: str, imp_class: str, soil: str, zone: str,  # noqa: PLR0913, PLR0917
                behaviour: float) -> pd.DataFrame:
    """Generate the spectrum DataFrame for the given parameters.

    Args:
        locale (str): country code (EU, PT)
        code (str): the code of the spectrum (CEN-1, CEN-2, PT-1, PT-2, PT-A)
        imp_class (str): importance class (I, II, III, IV)
        soil (str): type of soil (A, B, C, D, E)
        zone (str): seismic zone
        behaviour (float): behaviour factor

    Returns:
        pd.DataFrame: the spectrum DataFrame

    """
    txt = (
        code + "_" + imp_class + "_" + soil + "_"
        + str.replace(zone, "_", ".") + "_" + str(behaviour)
    )

    s_val, a_g, t_b, t_c, t_d = get_spec_params(locale, code, imp_class, soil, zone)

    perds = np.linspace(0.0, t_b, 10, endpoint=False)
    perds = np.append(perds, np.linspace(t_b, t_c, 10, endpoint=False))
    perds = np.append(perds, np.linspace(t_c, t_d, 10, endpoint=False))
    perds = np.append(perds, np.linspace(t_d, 10, 30))

    value = [calc_spectrum(T, a_g, s_val, behaviour, t_b, t_c, t_d, 0.2) for T in perds]
    data = {"period": perds,
            "value": value}

    spec = pd.DataFrame(data)
    spec.attrs["name"] = txt
    spec.attrs["S"] = s_val
    spec.attrs["a_g"] = a_g
    spec.attrs["q"] = str(behaviour)

    return spec


def get_spectrum_user(  # noqa: PLR0913, PLR0917
    a_g: float,
    s_val: float,
    q: float,
    t_b: float,
    t_c: float,
    t_d: float,
    beta: float = 0.2,
) -> pd.DataFrame:
    """Generate the spectrum DataFrame for the given parameters.

    Args:
        a_g (float): acceleration (m/s2)
        s_val (float): soil amplification factor
        q (float): behaviour factor
        t_b (float): spectrum parameter
        t_c (float): spectrum parameter
        t_d (float): spectrum parameter
        beta (float, optional): the limiting value of the spectrum. Defaults to 0.2.

    Returns:
        pd.DataFrame: _description_

    """
    txt = (
        "t_b_" + str(t_b) + "_t_c_" + str(t_c) +
        "_t_d_" + str(t_d) + "_b_" + str(beta)
        )

    periods = np.linspace(0.0, t_b, 10, endpoint=False)
    periods = np.append(periods, np.linspace(t_b, t_c, 10, endpoint=False))
    periods = np.append(periods, np.linspace(t_c, t_d, 10, endpoint=False))
    periods = np.append(periods, np.linspace(t_d, 10, 30))

    value = [calc_spectrum(T, a_g, s_val, q, t_b, t_c, t_d, beta) for T in periods]
    data = {"period": periods,
            "value": value}

    spec = pd.DataFrame(data)
    spec.attrs["name"] = txt
    spec.attrs["S"] = s_val
    spec.attrs["a_g"] = round(a_g, 5)
    spec.attrs["q"] = q

    return spec


def write_spectrum_ec8(spectrum: pd.DataFrame, filename: str | None = None,
                        separator: str = ",") -> None:
    """Generate a text file with the spectrum data.

    Args:
        spectrum (pd.DataFrame): a pandas DataFrame with the
        spectrum data (columns: period, value)
        filename (str | None): the filename to use when saving the spectrum data
            (if None, a default is used)
        separator (str): a string with the separator to be used in the text file

    """
    # separator was defined as " " (space) for SAP2000 compatibility.
    # any other can be used
    if filename is None:
        filename = "spectrum_" + spectrum.attrs["name"] + ".csv"

    spectrum.to_csv(filename, index=False, sep=separator)


def draw_spectrum_ec8(spectrum: pd.DataFrame, save: bool = False,  # noqa: FBT001, FBT002
            filename: str | None = None, show: bool = True) -> None:  # noqa: FBT001, FBT002
    """Draw the spectrum using matplotlib.

    Args:
        spectrum (pd.DataFrame): a pandas DataFrame with the
            spectrum data (columns: period, value)
        save (bool): whether to save the plot as an image file
        filename (str | None): the filename to use when saving the plot
            (if None, a default is used)
        show (bool): whether to display the plot window

    """
    # plot the spectrum
    plt.plot(spectrum["period"].to_numpy(), spectrum["value"].to_numpy())
    s = (
        spectrum.attrs["name"]
        + ":    S=" + str(round(spectrum.attrs["S"], 3))
        + " a_g=" + str(round(spectrum.attrs["a_g"], 3))
        + " q=" + str(spectrum.attrs["q"])
    )
    plt.title(s)
    plt.xlabel("Period (s)")
    plt.ylabel("Spectrum value (m/s2)")
    if save:
        if filename is None:
            filename = s + ".png"
        plt.savefig(filename, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
