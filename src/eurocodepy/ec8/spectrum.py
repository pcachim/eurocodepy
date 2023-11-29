import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .. import db


def get_spec_params(locale:str, code: str, class_imp: str, soil: str, zone: str) -> list:
    """Get the spectrum parameters

    Args:
        locale (str): country code (EU, PT)
        code (str): 
                CEN-1, CEN-2: standard Eurocode spectrums (EU)
                PT-1, PT-2, PT-A: Portuguese National Annex spectrums (PT)
                (PT-1 and PT-2, for continent and Madeira, PT-A for Azores)
        class_imp (str): importance class  (i, ii, iii, iv)
        soil (str): soil type (A, B, C, D, E)
        zone (str): (1.1, 1.2, 1.3, 1.4, 1.5, 1.6) for "PT-1"
                    (2.1, 2.2, 2.3, 2.4, 2.5) for "PT-2" and "PT-A"
                    (.1g, .2g, .3g, .4g, .5g, .6g, .7g, .8g, .9g, 1.0g) for "CEN-1" and "CEN-2"
    Raises:
        ValueError: if locale is not available
        ValueError: if code is not available
        ValueError: if class_imp is not available

    Returns:
        list: soil amplification factor, acceleration, T_B, T_C, T_D
    """
    local = db.SeismicLoads["Locale"][locale]

    if code not in local["Types"]:
        raise ValueError(f"Code {code} not available for locale {locale}")

    class_imp = str.lower(class_imp)
    if class_imp not in local["ImportanceClass"].keys():
        raise ValueError(f"Class {class_imp} not available for locale {locale}")

    if zone not in local["a_gR"][code].keys():
        raise ValueError(f"Zone {zone} not available for locale {locale}")
    
    soil = str.upper(soil)
    if soil not in local["SoilType"].keys():
        raise ValueError(f"Soil {soil} not available for code {code}")

    importance_coef = local["ImportanceCoef"][code][class_imp]
    a_gR = local["a_gR"][code][zone]
    a_g = a_gR * importance_coef

    TB = local["Spectrum"][code][soil]["T_B"]
    TC = local["Spectrum"][code][soil]["T_C"]
    TD = local["Spectrum"][code][soil]["T_D"]
    Smax = local["Spectrum"][code][soil]["S_max"]
    Smin = local["Spectrum"][code][soil]["S_min"]
    ag1 = local["Spectrum"][code][soil]["a_g1"]
    ag2 = local["Spectrum"][code][soil]["a_g2"]
    if a_g <= ag1:
        S = Smax
    elif a_g >= ag2:
        S = Smin
    else:
        S = Smax - (Smax - Smin) * (a_g - ag1) / (ag2 - ag1)
    return S, a_g, TB, TC, TD


def get_spectrum_parameters(code: str, coef_imp: str, soil: str, zone: str) -> list:
    """Get the spectrum parameters

    Args:
        code (str): code to be used (CEN-1, CEN-2, PT-1, PT-2, PT-A)
                CEN-1, CEN-2: standard Eurocode spectrums
                PT-1, PT-2, PT-A: Portuguese National Annex spectrums
                    (PT-1 and PT-2, for continent and Madeira, PT-A for Azores)
        coef_imp (str): importance coefficient (i, ii, iii, iv)
        soil (str): soil type (A, B, C, D, E)
        zone (str): zone (1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, .1g, .2g, .3g, .4g, .5g, .6g, .7g, .8g, .9g, 1.0g)

    Returns:
        list: soil amplification factor, acceleration, T_B, T_C, T_D
    """
    # accelarations
    a_gR = {'1.1': 2.5, '1.2': 2.0, '1.3': 1.5, '1.4': 1.0, '1.5': 0.6, '1.6': 0.35, 
            '2.1': 2.5, '2.2': 2.0, '2.3': 1.7, '2.4': 1.1, '2.5': 0.8,
            '.1g': 0.980665, '.2g': 1.96133, '.3g':  2.941995, '.4g': 3.92266, '.5g': 4.903325, 
            '.6g': 5.88399, '.7g': 6.864655, '.8g': 7.84532, '.9g': 8.825985, '1.0g': 9.80665}
    
    index1 = ['i', 'ii', 'iii', 'iv']
    gama_f = {'CEN-1': [0.8, 1.0, 1.2, 1.4], 
            'CEN-2': [0.8, 1.0, 1.2, 1.4], 
            'PT-1': [0.65, 1.0, 1.45, 1.95], 
            'PT-2': [0.75, 1.0, 1.25, 1.5], 
            'PT-A': [0.85, 1.0, 1.15, 1.35]}
    coefs = pd.DataFrame(gama_f, index=index1)
    
    coef_imp = str.lower(coef_imp)
    a_g = a_gR[zone] * coefs.at[coef_imp, code]
    
    soil = str.upper(soil)
    index = ['A', 'B', 'C', 'D', 'E']
    code = str.upper(code)
    if code == 'CEN-1':
        data = {'S_max': [1.0 , 1.2, 1.15, 1.35, 1.4],
                'T_B': [0.15, 0.15, 0.2, 0.3, 0.15],
                'T_C': [0.4, 0.5, 0.6, 0.8, 0.5],
                'T_D': [2.0, 2.0, 2.0, 2.0, 2.0]
                }
    elif code == 'CEN-2':
        data = {'S_max': [1.0 , 1.35, 1.5, 1.88, 1.6],
                'T_B': [0.05, 0.05, 0.1, 0.1, 0.05],
                'T_C': [0.25, 0.25, 0.25, 0.3, 0.25],
                'T_D': [1.2, 1.2, 1.2, 1.2, 1.2]
                }
    elif code == 'PT-1':
        data = {'S_max': [1.0 , 1.35, 1.60, 2.0, 1.8],
                'T_B': [0.1, 0.1, 0.1, 0.1, 0.1],
                'T_C': [0.25, 0.25, 0.25, 0.3, 0.25],
                'T_D': [2.0, 2.0, 2.0, 2.0, 2.0]
                }
    elif code == 'PT-2' or code == 'PT-A':
        data = {'S_max': [1.0 , 1.35, 1.60, 2.0, 1.8],
                'T_B': [0.1, 0.1, 0.1, 0.1, 0.1],
                'T_C': [0.6, 0.6, 0.6, 0.8, 0.6],
                'T_D': [2.0, 2.0, 2.0, 2.0, 2.0]
                }
    values = pd.DataFrame(data, index=index)
    
    Smax = values.at[soil, 'S_max']

    if code == 'CEN-1' or code == 'CEN-2':
        S = Smax
    else: 
        if a_g <= 1.0:
            S = Smax 
        elif a_g >= 4.0:
            S = 1.0
        else:
            S = Smax-(Smax-1.0)*(a_g-1.0)/3.0

    TB = values.at[soil, 'T_B']
    TC = values.at[soil, 'T_C']
    TD = values.at[soil,'T_D']

    return S, a_g, TB, TC, TD


def get_spectrum(T: float, a_g: float, S: float, q: float, TB: float, TC: float, TD: float, beta: float=0.2) -> float:
    """Calculates the spectrum value for a given period, T

    Args:
        T (float): period (s)
        a_g (float): acceleration (m/s2)
        S (float): soil amplification factor
        q (float): behaviour factor
        TB (float): spectrum parameter
        TC (float): spectrum parameter
        TD (float): spectrum parameter
        beta (float, optional): the limiting value of the spectrum. Defaults to 0.2.

    Returns:
        float: the spectrum value
    """
    ag_S = a_g * S
    
    if T < TB:
        spec = ag_S * (2.0/3.0 + T / TB * (2.5 / q - 2.0/3.0))
    elif T < TC:
        spec = ag_S * 2.5 / q
    elif T < TD:
        spec = max(ag_S * 2.5 / q * (TC)/T, beta * ag_S)
    else:
        spec = max(ag_S * 2.5 / q * (TC*TD)/T**2, beta * ag_S)

    return spec


def spectrum_ec8(code: str, coef_imp: str, soil: str, zone:str, behaviour: float) -> pd.DataFrame:
    """Generate the spectrum DataFrame for the given parameters

    Args:
        code (str): the code of the spectrum (CEN-1, CEN-2, PT-1, PT-2, PT-A)
        coef_imp (str): importance coefficient (I, II, III, IV)
        soil (str): type of soil (A, B, C, D, E)
        zone (str): seismic zone 
        behaviour (float): behaviour factor

    Returns:
        pd.DataFrame: the spectrum DataFrame
    """
    txt = code + '_' + coef_imp + '_' + soil + '_' + zone + '_' + str(behaviour)

    S, a_g, TB, TC, TD = get_spectrum_parameters(code, coef_imp, soil, zone)

    periods = np.linspace(0.0, TB, 10, endpoint=False)
    periods = np.append(periods, np.linspace(TB, TC, 10, endpoint=False))
    periods = np.append(periods, np.linspace(TC, TD, 10, endpoint=False))
    periods = np.append(periods, np.linspace(TD, 10, 30))

    value = [get_spectrum(T, a_g, S, behaviour, TB, TC, TD, 0.2) for T in periods]
    data = {'period': periods,
            'value': value}
    
    spec = pd.DataFrame(data)
    spec.attrs['name'] = txt
    spec.attrs['S'] = S
    spec.attrs['a_g'] = a_g
    spec.attrs['q'] = str(behaviour)
    
    return spec


def spectrum_user(a_g: float, S: float, q: float, TB: float, TC: float, TD: float, beta: float=0.2) -> pd.DataFrame:
    """generate the spectrum DataFrame for the given parameters

    Args:
        a_g (float): acceleration (m/s2)
        S (float): soil amplification factor
        q (float): behaviour factor
        TB (float): spectrum parameter
        TC (float): spectrum parameter
        TD (float): spectrum parameter
        beta (float, optional): the limiting value of the spectrum. Defaults to 0.2.

    Returns:
        pd.DataFrame: _description_
    """
    txt = 'TB_' + str(TB) + '_TC_' + str(TC) + '_TD_' + str(TD) + '_b_' + str(beta)

    periods = np.linspace(0.0, TB, 10, endpoint=False)
    periods = np.append(periods, np.linspace(TB, TC, 10, endpoint=False))
    periods = np.append(periods, np.linspace(TC, TD, 10, endpoint=False))
    periods = np.append(periods, np.linspace(TD, 10, 30))

    value = [get_spectrum(T, a_g, S, q, TB, TC, TD, beta) for T in periods]
    data = {'period': periods,
            'value': value}

    spec = pd.DataFrame(data)
    spec.attrs['name'] = txt
    spec.attrs['S'] = S
    spec.attrs['a_g'] = round(a_g, 5)
    spec.attrs['q'] = q

    return spec


def write_spectrum_ec8(spectrum: pd.DataFrame, separator: str):
    """Generate a text file with the spectrum data

    Args:
        spectrum (pd.DataFrame): a pandas DataFrame with the spectrum data (columns: period, value)
        separator (str): a string with the separator to be used in the text file
    """
    # separator was defined as ' ' (space) for SAP2000 compatibility. any other can be used
    spectrum.to_csv('spectrum_' + spectrum.attrs['name'] + '.txt', index=False, sep=separator)


def draw_spectrum_ec8(spectrum: pd.DataFrame):
    """Draw the spectrum using matplotlib

    Args:
        spectrum (pd.DataFrame): a pandas DataFrame with the spectrum data (columns: period, value)
    """
    # plot the spectrum
    plt.plot(spectrum['period'].to_numpy(), spectrum['value'].to_numpy())
    s = spectrum.attrs['name'] + ':    S=' + str(spectrum.attrs['S']) + ' a_g=' + str(spectrum.attrs['a_g']) + ' q=' + str(spectrum.attrs['q'])
    plt.title(s)
    plt.xlabel('Period (s)')
    plt.ylabel('Spectrum value (m/s2)')