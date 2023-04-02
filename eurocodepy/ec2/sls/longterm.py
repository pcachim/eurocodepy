import math as m


cemprops = {
    'Type S': [3, 0.13],
    'Type N': [4, 0.12],
    'Type R': [6, 0.11],
}


def calc_creep_coef(t=28, h0=100,rh=65, t0=10, fck=20.0, cem=0.0)->float:
    """Calculates the creep coeficient.

    Args:
        t (int, optional): _description_. Defaults to 28.
        h0 (int, optional): _description_. Defaults to 100.
        rh (int, optional): _description_. Defaults to 65.
        t0 (int, optional): _description_. Defaults to 10.
        fck (float, optional): _description_. Defaults to 20.0.
        cem (float, optional): _description_. Defaults to 0.0.

    Returns:
        float: _description_
    """
    fcm = fck+8
    alpha1 = (35/fcm)**0.7
    alpha2 = (35/fcm)**0.2
    alpha3 = min(1.0, (35/fcm)**0.5)
    tt0 = t0*((1.0+9.0/(2.0+t0**1.2))**cem)
    phi_RH = (1.0-rh/100)/(0.1*(h0**0.33333333))
    phi_RH = 1.0+phi_RH if fcm <= 35 else (1.0+phi_RH*alpha1)*alpha2
    beta_fcm = 16.8/m.sqrt(fcm)
    beta_t0 = 1.0/(0.1+tt0**0.2)
    phi_0 = beta_fcm*beta_t0*phi_RH

    try:        
        betah = min(1500*alpha3, 1.5*(1.0+m.pow(0.012*rh,18))*h0+250*alpha3)
        beta_cc = m.pow((t-t0)/(betah+t-t0), 0.3)
        phi = beta_cc*phi_0    
    except:
        beta_cc = 0.0
        phi = 0.0

    return phi


def calc_shrink_strain(t=28, h0=100, ts=3, rh=65, fck=20.0, cem='Type N')->float:
    """_summary_

    Args:
        t (int, optional): _description_. Defaults to 28.
        h0 (int, optional): _description_. Defaults to 100.
        ts (int, optional): _description_. Defaults to 3.
        rh (int, optional): _description_. Defaults to 65.
        fck (float, optional): _description_. Defaults to 20.0.
        cem (str, optional): _description_. Defaults to 'Type N'.

    Returns:
        float: the total shrinkage strain
    """
    fcm = fck+8
    alpha1 = cemprops[cem][0]
    alpha2 = cemprops[cem][1]

    eps_ca = 25.0e-7*(fck-10)
    beta_as = 1.0-m.exp(-0.2*(t**0.5))

    beta_rh = 1.55*(1.0-(rh/100)**3)
    eps_cd = beta_rh*0.85e-6*((220+110*alpha1)*m.exp(-alpha2*fcm/10.0))
    beta_ds = (t-ts)/((t-ts)+0.4*h0**1.5)
    
    return beta_as*eps_ca + beta_ds*eps_cd