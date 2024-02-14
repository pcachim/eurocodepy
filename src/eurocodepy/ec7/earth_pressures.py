import numpy as np


def rankine_coefficient(phi, betha):
    a1 = (np.cos(betha)-np.sqrt((np.cos(betha))**2-(np.cos(phi))**2)) #*np.cos(betha)
    a2 = (np.cos(betha)+np.sqrt((np.cos(betha))**2-(np.cos(phi))**2))
    return [a1/a2, a2/a1]


def coulomb_coefficient(phi, delta, theta, betha):
    a1 = np.cos(phi-theta)**2/(np.cos(theta)**2*np.cos(delta+theta)*
            (1+np.sqrt((np.sin(phi+delta)*np.sin(phi-betha))/(np.cos(betha-theta*np.cos(delta+theta)))))**2)
    a2 = np.cos(phi+theta)**2/(np.cos(theta)**2*np.cos(delta-theta)*
            (1-np.sqrt((np.sin(phi+delta)*np.sin(phi+betha))/(np.cos(betha-theta*np.cos(delta-theta)))))**2)
    return [a1, a2]


def ec7_coefficient(phi, delta, theta, betha):
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
    a = (1-np.sin(phi))*np.sqrt(OCR)*(1+np.sin(betha))
    return [a, a]


def earthquake_coefficient(phi, delta, theta, betha, kh, kv):
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
