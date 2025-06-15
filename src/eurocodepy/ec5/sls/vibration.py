import numpy as np

# useful functions
aval = [0.5, 1, 2, 4]
bval = [150, 120, 80, 50]


def floor_freq(l: float, EI: float, m: float) -> float:
    """Calculate the floor fundamental frequency.

    Parameters
    ----------
    l : float
        Span length.
    EI : float
        Flexural rigidity.
    m : float
        Mass per unit length.

    Returns
    -------
    float
        The fundamental frequency of the floor.
    """
    return (np.pi / 2 / l**2) * np.sqrt(EI / m)


def vel(f1: float, b: float, l: float, m: float, EIl: float, EIt: float):
    """Calculate the velocity response factor for a floor subjected to vibration, based on Eurocode 5 SLS criteria.

    Parameters
    ----------
        f1 (float): Fundamental frequency of the floor (Hz).
        b (float): Width of the floor (m).
        l (float): Span length of the floor (m).
        m (float): Mass per unit area of the floor (kg/m^2).
        EIl (float): Bending stiffness of the floor in the longitudinal direction (Nm^2).
        EIt (float): Bending stiffness of the floor in the transverse direction (Nm^2).

    Returns
    -------
        float: Velocity response factor (m/(Ns)), representing the floor's vibration response.

    Notes
    -----
        The formula is based on the simplified method for vibration assessment in Eurocode 5.

    """
    n40 = np.pow(((40 / f1)**2 - 1.0) * ((b / l)**4) * (EIl / EIt), 0.25)
    return 4 * (0.4 + 0.6 * n40) / (m * b * l + 200)


def b_from_a(a: float) -> float:
    """Interpolates and returns the corresponding 'b' value for a given 'a' using predefined arrays.

    Parameters
    ----------
    a : float
        The input value for which to interpolate the corresponding 'b'.

    Returns
    -------
    float
        The interpolated 'b' value.

    """
    return np.interp(a, aval, bval)


def a_from_b(b: float) -> float:
    """Interpolates and returns the corresponding 'a' value for a given 'b' using predefined arrays.

    Parameters
    ----------
    b : float
        The input value for which to interpolate the corresponding 'a'.

    Returns
    -------
    float
        The interpolated 'a' value.

    """
    return np.interp(b, np.flip(bval), aval)


def vlim(f1: float, b: float, damp: float) -> float:
    """Calculate the vibration limit value based on frequency, width, and damping.

    Parameters
    ----------
    f1 : float
        The fundamental frequency.
    b : float
        The width parameter.
    damp : float
        The damping factor.

    Returns
    -------
    float
        The calculated vibration limit value.

    """
    return np.pow(b, f1 * damp - 1.0)
