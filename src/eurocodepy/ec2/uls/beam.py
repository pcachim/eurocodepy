import math
from typing import Tuple, Dict, List
import eurocodepy as ec


def calc_vrd(bw: float, d: float, fck: float, g_c: float, fyk: float, g_s: float, cott: float, asw_s: float, alpha: float) -> float:
    """Calculates the design shear strength Vrds and Vrd.max

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        fyk (float): steel strength
        g_s (float): steel partial safety coefficient
        cott (float): truss inclination (cot)
        asw_s (float): steel transverse area (Asw/s)
        alpha (float): coefficient

    Returns:
        float: (shear reinforcement max(Asw/s), Vrd.max)
    """
    z = 0.9 * d
    vrd_s = asw_s * z * fyk / g_s * cott * 1000.0
    niu = 0.6*(1.0-fck/250)
    vrd_max = bw * z * niu * fck / g_c * 100.0 / (cott + 1.0/cott)
    return max(vrd_s, vrd_max)


def calc_asws(bw: float, d: float, fck: float, g_c: float, fyk: float, g_s: float, cott: float, ved: float, alpha: float) -> Tuple[float, float]:
    """Calculates the design shear reinforcement

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        fyk (float): steel strength
        g_s (float): steel partial safety coefficient
        cott (float): truss inclination (cot)
        ved (float): design shear force
        alpha (float): coefficient

    Returns:
        Tuple[float, float]: (shear reinforcement (Asw/s), maximum shear force Vrd.max)
    """
    z = 0.9 * d
    niu = 0.6*(1.0-fck/250)
    vrd_max = bw * z * niu * fck / g_c * 1000.0 / (cott + 1.0/cott)

    asw_s = ved / z / fyk * g_s / cott / 1000.0 if vrd_max >= ved else math.nan
    return asw_s, vrd_max


def calc_vrdc(bw: float, d: float, fck: float, g_c: float, rho_l: float) -> Tuple[float, float, float]:
    """Shear strength without shear reinforcement

    Args:
        bw (float): beam width
        d (float): beam depth
        fck (float): concrete compressive strength
        g_c (float): concrete partial safety coefficient
        rho_l (float): longitudinal reinforcement ratio (As/bd)

    Returns:
        Tuple[float, float, float]: (vrd.min, vrd.c, vrd [min(vrd.mmin, vrd.c])
    """
    k = min(2.0, 1.0+math.sqrt(0.2/d))
    vrd_min = 35.0 * math.pow(k, 1.5) * math.sqrt(fck) * bw * d
    vrd_c = 180.0 / g_c * k * (100.0*rho_l*fck)**(1.0/3.0) * bw * d
    vrd = max (vrd_min, vrd_c)
    return vrd_min, vrd_c, vrd


def calc_asl(b: float, d: float, med: float, fcd: float=13.7, fyd: float=348.0, iprint: bool=False) -> Tuple[float, float, float]:
    """Calculates the reinforcement in a rectangular concrete beam.

    Args:
        b (float): bredth of the beam in m.
        d (float): depth of the reinforced in beam in m.
        med (float): bending moment in kNm.
        fcd (float, optional): concrete strength in MPa. Defaults to 20.0.
        fyd (float, optional): reinforcement strength in MPa. Defaults to 400.0.
        iprint (bool, optional): print results. Defaults to False.

    Returns:
        Tuple[float, float, float, float]: reinforcement area in cm2, strain in reinforcement, neutral axis depth, omega.
    """
    mmed = med
    bb = b
    dd = d
    miu = mmed/bb/d**2/fcd/1000.0
    try:
        omega = 1.0-math.sqrt(1-2*miu)
    except:
        omega = math.nan
    alpha = 1.25*omega
    ast = omega*b*d*fcd/fyd * 10000.0
    epss = (1.0-alpha)*3.5/alpha
    if iprint: 
        print("miu={:.3f} omega={:.3f} x/d={:.3f} eps-s={:.3f} As={:.2f} cm2".format(miu, round(omega,3), alpha, epss, ast))
    return ast, epss, alpha


def calc_mrd(b: float, d: float, ast: float, fcd: float=20.0, fyd: float=400.0, iprint: bool=False) -> Tuple[float, float, float]:
    """Calculates the bending moment in a rectangular concrete beam.

    Args:
        b (float): bredth of the beam in m.
        d (float): depth of the reinforced in beam in m.
        ast (float): reinforcement area in cm2.
        fcd (float, optional): concrete strength in MPa. Defaults to 20.0.
        fyd (float, optional): reinforcement strength in MPa. Defaults to 400.0.
        iprint (bool, optional): print results. Defaults to False.

    Returns:
        Tuple[float, float, float]: bending moment in kNm, strain in reinforcement, neutral axis depth.
    """
    omega = ast*fyd/b/d/fcd/10000.0
    miu = omega*(1-0.5*omega)
    alpha = 1.25*omega
    epss = (1.0-alpha)*3.5/alpha
    mrd = miu*b*d*d*fcd*1000
    if iprint: 
        print("med={:.1f} kNm; miu={:.3f}; omega={:.3f}".format(mrd, round(miu,3), round(omega,3)))
    return mrd, epss, alpha


def get_bend_params(conc:str='C20/25')->Tuple[float, float, float]:
    n = ec.ConcreteClasses[conc]['n']
    epsc2 = ec.ConcreteClasses[conc]['epsc2']
    epscu2 = ec.ConcreteClasses[conc]['epscu2']
    epsc12 = epsc2/epscu2
    chi1 = 1.0-epsc12/(n+1)
    chi2 = 1.0-((n+1)*(n+2)*0.5-epsc12**2)/((n+1)*(n+2)*chi1)
    chi = 0.5*chi1/chi2
    return chi1, chi2, chi


class RCBeam:
    def __init__(self, b: float, h: float, at: float = 0.05, ac: float = 0.05,
                conc: str="C25/30", gammac = None, reinf: str="B500B", gammas = None) -> None:
        """_summary_

        Args:
            b (float): bredth of the beam in m.
            h (float): height of the beam in m.
            conc (str, optional): concrete class. Defaults to "C25/30".
            reinf (str, optional): reinforcement lass. Defaults to "B500B".
            at (float, optional): tensile reinforcement mechanical cover. Defaults to 0.05 m.
            ac (float, optional): compressive reinforcement mechanical cover. Defaults to 0.05 m.
        """
        self.b = b
        self.h = h
        self.conc = conc
        self.reinf = reinf
        self.at = at
        self.ac = ac
        self.d = self.h - self.at
        self.fck = ec.ConcreteClasses[self.conc]['fck']
        self.fyk = ec.ReinforcementClasses[self.reinf]['fyk']
        self.gammac = gammac if gammac is not None else 1.5
        self.gammas = gammas if gammas is not None else 1.15
        self.fcd = self.fck/self.gammac
        self.fyd = self.fyk/self.gammas
        return
    
    def calcShear(self, med: float, ved: float, cott: float = 2.5, iprint: bool=False) -> Tuple[float, float, float]:
        aslt = 0.0
        aslc = 0.0
        alpha = 0.0
        epsst = 0.0
        epssc = 0.0
        asws = 0.0
        vrdmax = 0.0

        asws = calc_asws(self.b, self.d, self.fck, self.gammac, self.fyk,self.gammas, ved)
        return aslt, aslc, alpha, epsst, epssc, asws, vrdmax
    
    def calcBending(self, med: float, delta: float = 1.0, iprint: bool=False) -> Tuple[float, float, float, float, float]:
        """Calculates the reinforcement area in a rectangular concrete beam.

        Args:
            med (float): design bending moment in kNm.
            delta (float, optional): redistribution ratio (0.7 to 1.0). Defaults to 1.0 (no redistribution).
            iprint (bool, optional): prints results to stdout. Defaults to False.

        Returns:
            Tuple[float, float, float, float, float]: reinforcement area in cm2, strain in reinforcement, neutral axis depth.
        """

        # Calculate med_max
        alpha_c = self.ac/self.d
        epscu2 = ec.ConcreteClasses[self.conc]['epscu2']

        alpha_lim = 0.45 if self.fck <= 50 else 0.35 # correct this values for fck > 50
        omega_max = alpha_lim/1.25
        miu_max = omega_max*(1-0.5*omega_max)
        med_max = miu_max*self.b*self.d*self.d*self.fck/self.gammac*1000.0
        
        # Check if miu is less than miu-max and calculate reinforcement accordingly
        if med <= med_max:
            # Calculate reinforcement for miu < miu-max
            aslt, epsst, alpha = calc_asl(self.b, self.d, med, self.fcd, self.fyd, iprint)
            aslc = None
            epssc = None
        else:
            # Calculate reinforcement for miu = miu-max
            epsyd = self.fyd/ec.ReinforcementClasses[self.reinf]['Es']*1000
            # epssc = (alpha_lim-alpha_c)/alpha_lim*epscu2
            # if epssc < epsyd:
            #     alpha_lim = epscu2/(epscu2-epsyd)*alpha_c
            #     omega_max = alpha_lim/1.25
            #     miu_max = omega_max*(1-0.5*omega_max)
            #     med_max = miu_max*self.b*self.d*self.d*self.fck/self.gammac*1000.0
            
            aslt, epsst, alpha = calc_asl(self.b, self.d, med_max, self.fcd, self.fyd, iprint)
            aslc = (med-med_max)/(self.d-self.ac)/self.fyd*10.0
            aslt += aslc
            epssc = (alpha-alpha_c)/alpha*epscu2

        
        return aslt, aslc, alpha, epsst, epssc

if __name__ == "__main__":
    # test RCBeam class
    print("\nTest RCBeam:\n")
    beam = RCBeam(0.3, 0.5, at=0.05, ac=0.05, conc="C70/85", reinf="A500NR")
    asl, asc, a, epst, epsc = beam.calcBending(100.0)
    print (f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}\n")
    asl, asc, a, epst, epsc = beam.calcBending(500.0)
    print (f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}\n")
    asl, asc, a, epst, epsc = beam.calcBending(900.0)
    print (f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}\n")

