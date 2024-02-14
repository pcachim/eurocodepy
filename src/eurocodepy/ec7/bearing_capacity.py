import numpy as np


def bearing_resistance(phi, gamma, q, Bx, By, Hx, Hy, V, c=0, drained=True):
    """calculates the bearing capacity of a shallow foundation according with Eurocode 7 (EN 1997-1:2004)

    Args:
        phi (float or numpy.array): effective soil friction angle
        gamma (float or numpy.array): unit weight of the soil
        Bx (float or numpy.array): effective width of the foundation
        By (float or numpy.array): effective length of the foundation
        Hx (float or numpy.array): horizontal load in X direction on the foundation
        Hy (float or numpy.array): horizontal load in Y direction on the foundation
        V (float or numpy.array): vertical load on the foundation
        c (int or numpy.array, optional): effective cohesion. Defaults to 0.
        drained (bool, optional): drained or undrained conditions. if undrained c = cu. Defaults to True.

    Returns:
        float or numpy.array: the bearing capacity of the foundation 
    """
    bearing = 0.0
    area = Bx*By
    
    B = np.where(Bx <= By, Bx, By)
    L = np.where(Bx <= By, By, Bx)
    theta = np.where(Bx <= By, np.arctan2(Hx, Hy), np.arctan2(Hy, Hx))

    if drained:
        mb = (2+B/L)/(1+B/L)
        ml = (2+L/B)/(1+L/B)
        m = ml*np.cos(theta)**2 + mb*np.sin(theta)**2
        H = np.sqrt(Hx**2 + Hy**2)

        tanphi = np.tan(phi)
        sinphi = np.sin(phi)

        Nq = np.exp(np.pi*tanphi)*np.tan(np.pi/4 + phi/2)**2
        Nc = (Nq-1.0)/tanphi
        Ng = 2.0*(Nq-1.0)*tanphi
        
        sq = 1.0 + (B/L)*sinphi
        sg = 1.0 - 0.3*(B/L)
        sc = (sq*Nq-1.0)/(Nq-1.0)
        
        aux = (1.0 - H / (V + area*c/tanphi))
        iq = aux**m
        ig = aux**(m+1)
        ic = iq-(1.0-iq)/(Nc*tanphi)
        
        bearing = c * Nc * sc * ic + q * Nq * sq * iq + 0.5 * gamma * B * Ng * sg * ig
    
    else:
        sc = 1.0 + 0.2*(B/L)
        aux = H / (area*c)
        aux = aux if aux < 1.0 else 1.0
        ic = 0.5 * (1.0 + np.sqrt(1.0 - aux))
        bearing = (np.pi+2.0) * c * sc * ic + q 

    return bearing


if __name__ == "__main__":
    fhi = np.radians(np.array([32.5, 27, 32.5]))
    B = np.array([2.05, 2.63, 3.06])
    d = 0.8
    gamma = 19
    q = d*gamma
    H = np.array([274.6, 274.7, 202.0])
    V = np.array([716.4, 557.0, 530.5])
    bearing = bearing_capacity(fhi, gamma, q, B, B, H, H, V, 0, True)
    print(f"Bearing capacity: {np.round(bearing, 1)} kN/m²")
    print(f"Bearing capacity: {np.round(bearing*B, 1)} kN")

