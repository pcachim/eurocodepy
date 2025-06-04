import numpy as np


def rankine_coefficient(phi, betha):
    """Calculate Rankine coefficients for earth pressures.

    Args:
        phi (float): Friction angle of the soil (radians).
        betha (float): slope angle of the backfill (radians).

    Returns:
        list: Active/Passive earth pressure coefficients at rest (Ka, Kp).
    """
    a1 = (np.cos(betha)-np.sqrt((np.cos(betha))**2-(np.cos(phi))**2)) #*np.cos(betha)
    a2 = (np.cos(betha)+np.sqrt((np.cos(betha))**2-(np.cos(phi))**2))
    return [a1/a2, a2/a1]


def coulomb_coefficient(phi, delta, theta, betha):
    """Calculate Coulomb coefficients for earth pressures.

    Args:
        phi (float): friction angle of the soil (radians).
        delta (float): friction angle of the wall (radians).
        theta (float): slope angle of the backfill (radians).
        betha (float): slope angle of the wall (radians).

    Returns:
        list: Active/passive earth pressure coefficients (Ka, Kp).
    """
    a1 = np.cos(phi-theta)**2/(np.cos(theta)**2*np.cos(delta+theta)*
            (1+np.sqrt((np.sin(phi+delta)*np.sin(phi-betha))/(np.cos(betha-theta*np.cos(delta+theta)))))**2)
    a2 = np.cos(phi+theta)**2/(np.cos(theta)**2*np.cos(delta-theta)*
            (1-np.sqrt((np.sin(phi+delta)*np.sin(phi+betha))/(np.cos(betha-theta*np.cos(delta-theta)))))**2)
    return [a1, a2]


def ec7_coefficient(phi, delta, theta, betha):
    """Calculate EC7 coefficients for earth pressures.

    Args:
        phi (float): friction angle of the soil (radians).
        delta (float): friction angle of the wall (radians).
        theta (float): slope angle of the backfill (radians).
        betha (float): slope angle of the wall (radians).

    Returns:
        list: Active/passive earth pressure coefficients (Ka, Kp, Kaq, Kpq, Kac, Kpc).
    """
    amt = np.arccos(np.sin(betha)/np.sin(phi))+phi-betha
    amw = np.arccos(np.sin(delta)/np.sin(phi))+phi+delta
    av = amt/2+betha-amw/2-theta
    akn = ((1-np.sin(phi)*np.sin(amw-phi))/(1+np.sin(phi)*np.sin(amt-phi)))*np.exp(-2*av*np.tan(phi))
    pmt = np.arccos(-np.sin(betha)/np.sin(phi))-phi-betha
    pmw = np.arccos(np.sin(delta)/np.sin(phi))-phi-delta
    pv = pmt/2+betha-pmw/2-theta
    pkn = ((1+np.sin(phi)*np.sin(pmw+phi))/(1-np.sin(phi)*np.sin(pmt+phi)))*np.exp(2*pv*np.tan(phi))
    aux = np.cos(betha)*np.cos(betha-theta)
    kag = akn*aux
    kpg = pkn*aux
    aux = np.cos(betha)**2
    kaq = akn*aux
    kpq = pkn*aux
    kac = (akn-1.0)/np.tan(-phi)
    kpc = (pkn-1.0)/np.tan(phi)
    return [kag, kpg, kaq, kpq, kac, kpc]


def inrest_coefficient(phi, betha, OCR=1.0):
    """Calculate coefficients for earth pressures at rest.

    Args:
        phi (float): friction angle of the soil (radians).
        betha (floast): slope angle of the backfill (radians).
        OCR (float, optional): OCR for clays. Defaults to 1.0.

    Returns:
        list: In rest earth pressure coefficients at rest (Ka, Kp).
    """
    a = (1-np.sin(phi))*np.sqrt(OCR)*(1+np.sin(betha))
    return [a, a]


def earthquake_coefficient(phi, delta, theta, betha, kh, kv):
    """Calculate earthquake coefficients for earth pressures.

    Args:
        phi (float): friction angle of the soil (radians).
        delta (float): friction angle of the wall (radians).
        theta (float): slope angle of the backfill (radians).
        betha (float): slope angle of the wall (radians).
        kh (float): horizontal seismic coefficient.
        kv (float): vertical seismic coefficient.

    Returns:
        list: Active/passive earthquake coefficients (kas1, kps1, kas2, kps2).
    """
    psi = np.pi/2 - theta

    eps = np.arctan(kh/(1+kv))
    a1 = np.sin(psi+phi-eps)**2
    a2 = np.cos(eps)*np.sin(psi)**2*np.sin(psi-eps-delta)
    a3 = 1.0 if betha > phi-eps else (1+np.sqrt((np.sin(phi+delta)*np.sin(phi-betha-eps))/(np.sin(psi-eps-delta)*np.sin(psi+betha))))**2
    kas1 = a1/(a2*a3)
    a1 = np.sin(psi+phi-eps)**2
    a2 = np.cos(eps)*np.sin(psi)**2*np.sin(psi+eps)
    a3 = 1.0 if betha > phi-eps else (1+np.sqrt((np.sin(phi+delta)*np.sin(phi-betha-eps))/(np.sin(psi+eps)*np.sin(psi+betha))))**2
    kps1 = a1/(a2*a3) 
    
    eps = np.arctan(kh/(1-kv))
    a1 = np.sin(psi+phi-eps)**2
    a2 = np.cos(eps)*np.sin(psi)**2*np.sin(psi-eps-delta)
    a3 = 1.0 if betha > phi-eps else (1+np.sqrt((np.sin(phi+delta)*np.sin(phi-betha-eps))/(np.sin(psi-eps-delta)*np.sin(psi+betha))))**2
    kas2 = a1/(a2*a3)
    a1 = np.sin(psi+phi-eps)**2
    a2 = np.cos(eps)*np.sin(psi)**2*np.sin(psi+eps)
    a3 = 1.0 if betha > phi-eps else (1+np.sqrt((np.sin(phi+delta)*np.sin(phi-betha-eps))/(np.sin(psi+eps)*np.sin(psi+betha))))**2
    kps2 = a1/(a2*a3) 
    
    return [kas1, kps1, kas2, kps2]


def pressure_coefficients(phi, delta, theta, beta, method="ec7", seismic=None):
    """Calculate earth pressure coefficients based on the specified method.

    Args:
        phi (float): friction angle of the soil (radians).
        delta (float): friction angle of the wall (radians).
        theta (float): slope angle of the backfill (radians).
        betha (float): slope angle of the wall (radians).
        method (str, optional): calculation method for earth pressures. Defaults to "ec7".
        seismic (_type_, optional): Seismic horizontal/vertical seismic coefficients. Defaults to None.

    Raises:
        ValueError: Method not found.

    Returns:
        tuple: pressure coefficients (Ka, Kp, Kaq, Kpq, dkas1, dkps1, dkas2, dkps2).
        - Ka: Active earth pressure coefficient.
        - Kp: Passive earth pressure coefficient.
        - Kaq: Active earth pressure coefficient at rest.
        - Kpq: Passive earth pressure coefficient at rest.
        - dkas1: Difference in active earth pressure coefficient for seismic case 1.
        - dkps1: Difference in passive earth pressure coefficient for seismic case 1.
        - dkas2: Difference in active earth pressure coefficient for seismic case 2.
        - dkps2: Difference in passive earth pressure coefficient for seismic case 2.
    """
    method = method.lower()
    if method == "ec7":
        Ka, Kp, Kaq, Kpq, Kac, Kpc = ec7_coefficient(phi, delta, theta, beta)
    elif method == "rankine":
        Ka, Kp = rankine_coefficient(phi, beta)
        Kaq = Ka
        Kpq = Kp
    elif method == "coulomb":
        Ka, Kp = coulomb_coefficient(phi, delta, theta, beta)
        Kaq = Ka
        Kpq = Kp
    elif method == "inrest":
        Ka, Kp = inrest_coefficient(phi, beta)
        Kaq = Ka
        Kpq = Kp
    else:
        raise ValueError("Method not found")

    kas1 = 0.0
    kas2 = 0.0
    kps1 = 0.0
    kps2 = 0.0
    dkas1 = 0.0
    dkas2 = 0.0
    dkps1 = 0.0
    dkps2 = 0.0
    if seismic is not None:
        kas1, kps1, kas2, kps2 = earthquake_coefficient(phi, delta, theta, beta, seismic.kh, seismic.kv)
        dkas1 = (1.0 + seismic.kv) * kas1 - Ka
        dkas2 = (1.0 - seismic.kv) * kas2 - Ka
        dkps1 = Kp - (1.0 + seismic.kv) * kps1
        dkps2 = Kp - (1.0 - seismic.kv) * kps2
    
    return Ka, Kp, Kaq, Kpq, dkas1, dkps1, dkas2, dkps2
