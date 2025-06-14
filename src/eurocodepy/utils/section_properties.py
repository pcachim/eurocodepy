import numpy as np
from dataclasses import dataclass


@dataclass
class CrossSectionProperties:
    """Represents the geometric and mechanical properties of a cross-section.

    Attributes:
        Area (float): Cross-sectional area.
        Inertia (float): Moment of inertia.
        G_inf (float): Some property at the bottom fiber (description needed).
        G_sup (float): Some property at the top fiber (description needed).
        NeutralAxis (float): Position of the neutral axis.
        W_inf (float): Section modulus at the bottom fiber.
        W_sup (float): Section modulus at the top fiber.

    """

    Area: float
    Inertia: float
    G_inf: float
    G_sup: float
    NeutralAxis: float
    W_inf: float
    W_sup: float


# Resolver a equação cúbica
def calc_section_T(h, bw, bf, hf, A_s, A_sc, A_p, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display=False, label="SECÇÃO EM T") -> tuple:
    """Calculate the area, center of gravity, bending modulus and moment of inertia of a T-section.

    Args:
        h (float): Total height of the section.
        bw (float): Web width of the section.
        bf (float): Flange width of the section.
        hf (float): Flange height of the section.
        A_s (float[]): Area of the tensioned reinforcement.
        A_sc (float[]): Area of the compressed reinforcement.
        A_p (float[]): Area of the prestressing tendon.
        ds (float[]): Distance to the tensioned reinforcement from the top.
        dsc (float[]): Distance to the compressed reinforcement from the top.
        dp (float[]): Distance to the prestressing tendon from the top.
        alpha_Es (float): Equivalence factor of the passive steel.
        alpha_Ep (float): Equivalence factor of the prestressed steel.
        M (float): Bending moment.
        P (float): Prestressing normal force.
        display (bool, optional): If True, displays the calculated results. Defaults to False.

    Returns:
        tuple: A tuple containing two dictionaries, representing the properties of the uncracked
            and cracked sections respectively. Each dictionary contains the area, center of
            gravity, and moment of inertia.
            (prop_un, prop_cr)

    """
    if display:
        print(f"\n{label}")
        print(f"   Altura total: {h:.3f}")
        print(f"   Largura da alma: {bw:.3f}")
        print(f"   Largura do banzo: {bf:.3f}")
        print(f"   Altura do banzo: {hf:.3f}")
        print(f"   Área da armadura tracionada: {np.sum(A_s):.6f}")
        print(f"   Área da armadura comprimida: {np.sum(A_sc):.6f}")
        print(f"   Área do cabo de pré-esforço: {np.sum(A_p):.6f}")
        print(f"   Distância da armadura tracionada: {np.sum(ds):.3f}")
        print(f"   Distância da armadura comprimida: {np.sum(dsc):.3f}")
        print(f"   Distância do cabo de pré-esforço: {np.sum(dp):.3f}")
        print(f"   Fator de equivalência do aço: {alpha_Es:.1f}")
        print(f"   Fator de equivalência do pré-esforço: {alpha_Ep:.1f}")
        print(f"   Momento fletor: {M:.1f}")
        print(f"   Força normal de pré-esforço: {P:.1f}")
    prop_un = calc_section_T_uncrack(h, bw, bf, hf, A_s, A_sc, A_p, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display=display)
    prop_cr = calc_section_T_crack(h, bw, bf, hf, A_s, A_sc, A_p, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display=display)
    return prop_un, prop_cr


def calc_section_rectangular(h, b, A_s, A_sc, A_p, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display = False, label="SECÇÃO RETANGULAR"):
    """Calculate the area, center of gravity, and moment of inertia of a rectangular section.

    Args:
        h (float): Section height.
        b (float): Section width.
        A_s (float): Area of tensioned reinforcement.
        A_sc (float): Area of compressed reinforcement.
        A_p (float): Area of prestressing tendon.
        ds (float): Distance to tensioned reinforcement.
        dsc (float): Distance to compressed reinforcement.
        dp (float): Distance to prestressing tendon.
        alpha_Es (float): Equivalence factor of passive steel.
        alpha_Ep (float): Equivalence factor of prestressed steel.
        M (float): Bending moment.
        P (float): Prestressing normal force.
        display (bool, optional): If True, displays the results. Defaults to False.

    Returns:
        tuple: A tuple containing two dictionaries, representing the properties of the uncracked
            and cracked sections respectively. Each dictionary contains the area, center of
            gravity, and moment of inertia.
            (prop_un, prop_cr)

    """
    if display:
        print(f"\n{label}")
        print(f"   Altura: {h:.3f}")
        print(f"   Largura: {b:.3f}")
        print(f"   Área da armadura tracionada: {np.sum(A_s):.6f}")
        print(f"   Área da armadura comprimida: {np.sum(A_sc):.6f}")
        print(f"   Área do cabo de pré-esforço: {np.sum(A_p):.6f}")
        print(f"   Distância da armadura tracionada: {np.sum(ds):.3f}")
        print(f"   Distância da armadura comprimida: {np.sum(dsc):.3f}")
        print(f"   Distância do cabo de pré-esforço: {np.sum(dp):.3f}")
        print(f"   Fator de equivalência do aço: {alpha_Es:.1f}")
        print(f"   Fator de equivalência do pré-esforço: {alpha_Ep:.1f}")
        print(f"   Momento fletor: {M:.1f}")
        print(f"   Força normal de pré-esforço: {P:.1f}")
    prop_un = calc_section_T_uncrack(h, b, b, 0, A_s, A_sc, A_p, ds, dsc, dp,
                            alpha_Es, alpha_Ep, M, P, display=display)
    prop_cr = calc_section_T_crack(h, b, b, 0, A_s, A_sc, A_p, ds, dsc, dp,
                            alpha_Es, alpha_Ep, M, P, display=display)
    return prop_un, prop_cr


def calc_section_T_crack(h, bw, bf, hf, A_s, A_sc, A_p, ds, dsc, dp,
                alpha_Es, alpha_Ep, M, P, display = False):
    """Calculate the area, center of gravity, bending modulus and moment of inertia of a cracked T-section.

    Args:
        h (float): Total height of the section.
        bw (float): Web width of the section.
        bf (float): Flange width of the section.
        hf (float): Flange height of the section.
        A_s (float[]): Area of the tensioned reinforcement.
        A_sc (float[]): Area of the compressed reinforcement.
        A_p (float[]): Area of the prestressing tendon.
        ds (float[]): Distance to the tensioned reinforcement from the top.
        dsc (float[]): Distance to the compressed reinforcement from the top.
        dp (float[]): Distance to the prestressing tendon from the top.
        alpha_Es (float): Equivalence factor of the passive steel.
        alpha_Ep (float): Equivalence factor of the prestressed steel.
        M (float): Bending moment.
        P (float): Prestressing normal force.
        display (bool, optional): If True, displays the calculated results. Defaults to False.

    Returns:
        dict: the properties of the cracked section. The dictionary contains the area, center of
            gravity, and moment of inertia.

    """
    xi = calc_neutral_axis_cracked_T(h, bf, bw, hf, A_s, A_sc, A_p, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display=display)

    # Cálculo da área da secção fendilhada
    Aun = xi * bw + hf * (bf - bw) + (alpha_Es - 1) * np.sum(A_sc) + alpha_Es * np.sum(A_s) + alpha_Ep * np.sum(A_p)

    # Cálculo do centro de gravidade
    zgs = (0.5 * xi*xi * bw + 0.5 * hf**2 * (bf - bw) + (alpha_Es - 1) * np.sum(dsc * A_sc) +
              alpha_Es * np.sum(ds * A_s) + alpha_Ep * np.sum(dp * A_p)) / Aun
    zg = h - zgs

    if zgs < hf:
        # Se o centro de gravidade estiver dentro da banzo, a secção é como retangular com bw = bf
        return calc_section_T_crack(h, bw, bw, 0.0, A_s, A_sc, A_p, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display=display)

    # Cálculo do momento de inércia da secção fendilhada
    Iun = np.float64( 
           ((bf - bw) * hf**3) / 12 + (bf - bw) * hf * (zgs - hf / 2)**2 + 
           (bw * xi**3) / 12 + (bw * xi) * (zgs - xi / 2)**2 + 
           (alpha_Es - 1)  * np.sum(A_sc * (dsc - zgs)**2) + 
           alpha_Es * np.sum(A_s * (ds - zgs)**2) + 
           alpha_Ep * np.sum(A_p * (dp - zgs)**2))

    e_p = np.round(dp - zgs, 4)
    Ws = Iun/zgs
    Wi = Iun/zg
    sigma_cs = np.round(-P/Aun - (M - P * e_p) / Ws, 1)
    sigma_p = np.round(alpha_Ep * (-P / Aun + (M - P * e_p) / Iun * e_p), 1)
    sigma_sc = np.round(alpha_Es * (-P / Aun + (M - P * e_p) / Iun * (dsc - zgs)), 1)
    sigma_st = np.round(alpha_Es * (-P / Aun + (M - P * e_p) / Iun * (ds - zgs)), 1)

    if display:
        print("Propriedades da secção fendilhada")
        print(f"   Área: {Aun:.4f}")
        print(f"   Momento de inércia: {Iun:.6f}")
        print(f"   Centro de gravidade (inf): {zg:.4f}")
        print(f"   Centro de gravidade (sup): {zgs:.4f}")
        print(f"   Módulo de flexão (sup): {Ws:.6f}")
        print(f"   Módulo de flexão (inf): {Wi:.6f}")
        print(f"   Profundidade do eixo neutro: {xi:.4f}")
        print(f"   Excentricidade (P): {e_p}")
        print(f"   Sigma_cs: {sigma_cs}")
        print(f"   Sigma_sc: {sigma_sc}")
        print(f"   Sigma_st: {sigma_st}")
        print(f"   Sigma_p: {sigma_p}")

    return {"Area": Aun, "Inertia": Iun, "zGi": zg, "zGs": zgs, "Wi": Wi, "Ws": Ws, "NeutralAxis": xi, "e_p": e_p}


def calc_section_T_uncrack(h, bw, bf, hf, As, Asc, Ap, ds, dsc, dp, alpha_Es, alpha_Ep, M, P, display=False):
    """Calculate the area, center of gravity, bending modulus and moment of inertia of a cracked T-section.

    Args:
        h (float): Total height of the section.
        bw (float): Web width of the section.
        bf (float): Flange width of the section.
        hf (float): Flange height of the section.
        A_s (float[]): Area of the tensioned reinforcement.
        A_sc (float[]): Area of the compressed reinforcement.
        A_p (float[]): Area of the prestressing tendon.
        ds (float[]): Distance to the tensioned reinforcement from the top.
        dsc (float[]): Distance to the compressed reinforcement from the top.
        dp (float[]): Distance to the prestressing tendon from the top.
        alpha_Es (float): Equivalence factor of the passive steel.
        alpha_Ep (float): Equivalence factor of the prestressed steel.
        M (float): Bending moment.
        P (float): Prestressing normal force.
        display (bool, optional): If True, displays the calculated results. Defaults to False.

    Returns:
        dict: the properties of the uncracked section. The dictionary contains the area, center of
            gravity, and moment of inertia.

    """
    # Cálculo da área equivalente em betão
    Aun = h * bw + hf * (bf - bw) + (alpha_Es - 1) * (np.sum(As) + np.sum(Asc)) + (alpha_Ep - 1) * np.sum(Ap)

    # Cálculo do centro de gravidade
    zgs = (0.5 * h**2 * bw + 0.5 * hf**2 * (bf - bw) + 
           (alpha_Es - 1) * (np.sum(ds * As) + np.sum(dsc * Asc)) + 
           (alpha_Ep - 1) * np.sum(dp * Ap)) / Aun
    zg = h - zgs

    # Cálculo da inércia não fendilhada
    Iun = np.float64(
        (bw * h**3)/12 + (bw * h * (0.5 * h - zgs)**2) + 
        ((bf - bw) * hf**3)/12 + (hf * (bf - bw) * (0.5 * hf - zgs)**2) + 
        (alpha_Es - 1) * (np.sum(Asc * (dsc - zgs)**2) + np.sum(As * (ds - zgs)**2)) + 
        (alpha_Ep - 1) * (np.sum(Ap * (dp - zgs)**2)))

    root_un = zgs + P / Aun / (M - P * np.sum(dp - zgs)) * Iun 

    e_p = np.round(dp - zgs, 4)
    Ws = Iun/zgs
    Wi = Iun/zg
    sigma_cs = np.round(-P/Aun - (M - P * e_p) / Ws, 1)
    sigma_ci = np.round(-P/Aun + (M - P * e_p) / Wi, 1)
    sigma_p = np.round(alpha_Ep * (-P / Aun + (M - P * e_p) / Iun * e_p), 1)
    sigma_sc = np.round(alpha_Es * (-P / Aun + (M - P * e_p) / Iun * (dsc - zgs)), 1)
    sigma_st = np.round(alpha_Es * (-P / Aun + (M - P * e_p) / Iun * (ds - zgs)), 1)

    if display:
        print("Propriedades da secção não fendilhada")
        print(f"   Área: {Aun:.4f}")
        print(f"   Momento de inércia: {Iun:.6f}")
        print(f"   Centro de gravidade (inf): {zg:.4f}")
        print(f"   Centro de gravidade (sup): {zgs:.4f}")
        print(f"   Módulo de flexão (sup): {Ws:.6f}")
        print(f"   Módulo de flexão (inf): {Wi:.6f}")
        print(f"   Profundidade do eixo neutro: {root_un:.4f}")
        print(f"   Excentricidade (P): {e_p}")
        print(f"   Sigma_cs: {sigma_cs}")
        print(f"   Sigma_ci: {sigma_ci}")
        print(f"   Sigma_sc: {sigma_sc}")
        print(f"   Sigma_st: {sigma_st}")
        print(f"   Sigma_p: {sigma_p}")

    return {"Area": Aun, "Inertia": Iun, "zGi": zg, "zGs": zgs, "Wi": Wi, "Ws": Ws, "NeutralAxis": root_un, "e_p": e_p}


def cubic_equation(x: float, a1: float, a2: float, a3: float) -> float:
    """Evaluate the cubic equation x^3 + a1*x^2 + a2*x + a3.

    Args:
        x (float): The variable.
        a1 (float): Coefficient of x^2.
        a2 (float): Coefficient of x.
        a3 (float): Constant term.

    Returns:
        float: The result of the cubic equation.

    """
    return x**3 + a1 * x**2 + a2 * x + a3


def solve_cubic(a1: float, a2: float, a3: float, h: float) -> float:
    """Solves the cubic equation x^3 + a1*x^2 + a2*x + a3 = 0 and returns the real root within the interval (0, h).

    Args:
        a1 (float): Coefficient of x^2.
        a2 (float): Coefficient of x.
        a3 (float): Constant term.
        h (float): Upper bound for the root interval.

    Returns:
        float: The real root within (0, h), or np.nan if no such root exists.

    """
    # Resolver a equação cúbica
    roots = np.roots([1, a1, a2, a3])  # np.roots resolve equações polinomiais

    # Filtrar apenas raízes reais e dentro do intervalo (0, h)
    real_roots = [x.real for x in roots if np.isreal(x) and 0 < x.real < h]

    # Retorna a raiz válida ou None se não houver solução dentro do intervalo
    return real_roots[0] if real_roots else np.nan


def calc_neutral_axis_cracked_T(h, b, bw, hf, A_s, A_sc, A_p, ds, dsc, dp,
                alpha_E_s, alpha_E_p, M, P, display=False) -> float:
    """Calculate the neutral axis of a cracked T-section.

    Args:
        h (float): Total height of the section.
        bw (float): Web width of the section.
        bf (float): Flange width of the section.
        hf (float): Flange height of the section.
        A_s (float[]): Area of the tensioned reinforcement.
        A_sc (float[]): Area of the compressed reinforcement.
        A_p (float[]): Area of the prestressing tendon.
        ds (float[]): Distance to the tensioned reinforcement from the top.
        dsc (float[]): Distance to the compressed reinforcement from the top.
        dp (float[]): Distance to the prestressing tendon from the top.
        alpha_Es (float): Equivalence factor of the passive steel.
        alpha_Ep (float): Equivalence factor of the prestressed steel.
        M (float): Bending moment.
        P (float): Prestressing normal force.
        display (bool, optional): If True, displays the calculated results. Defaults to False.

    Returns:
        float: the neutral axis depth of a cracked T section.

    """
    ds_ref = np.max(ds)
    dp_ref = np.sum(dp * A_p) / np.sum(A_p) if np.abs(np.sum(A_p)) > 0 else dp[0]
    es = -M / P - (ds_ref - dp_ref)  # Excentricidade

    # Calcular os coeficientes da equação cúbica
    a1 = -3 * np.sum(ds + es)
    a2 = (-6 / bw) * (hf * (b - bw) * np.sum(ds + es - 0.5 * hf) + (alpha_E_s - 1) * np.sum(A_sc * (ds + es - dsc)) +
                    alpha_E_p * np.sum(A_p * (ds + es - dp)) + alpha_E_s * np.sum(A_s * es))
    a3 = (6 / bw) * (0.5 * hf**2 * (b - bw) * np.sum(ds + es - 2/3 * hf) +
                    (alpha_E_s - 1) * A_sc * np.sum(dsc * (ds + es - dsc)) +
                    alpha_E_p * np.sum(A_p * dp * (ds + es - dp)) + alpha_E_s * np.sum(A_s * ds * es))

    a1 = np.sum(a1)
    a2 = np.sum(a2)
    a3 = np.sum(a3)
    # Encontrar as raízes
    roots = np.roots([1, a1, a2, a3])  # np.roots resolve equações polinomiais

    if display:
        pass

    # Filtrar apenas raízes reais e dentro do intervalo (0, h)
    real_roots = [x.real for x in roots if np.isreal(x) and 0 < x.real < h]

    # Retorna a raiz válida ou None se não houver solução dentro do intervalo
    return real_roots[0] if real_roots else np.nan


if __name__ == "__main__":
    # Definir os parâmetros conhecidos (substituir com valores reais)
    h = 0.8 # Altura da secção
    bf = 0.3    # Largura total
    bw = 0.3 # 0.3   # Largura da alma
    hf = 0.15 # 0.15   # Altura da mesa

    A_s = 0.0008  # Área da armadura tracionada
    A_sc = 0.0004  # Área da armadura comprimida
    A_p = 0.0014  # Área do cabo de pré-esforço
    ds = 0.74   # Altura útil
    dsc = 0.06   # Distância da armadura comprimida
    dp = 0.6    # Distância do cabo de pré-esforço

    # A_s = np.array([8.0e-4])
    # ds = np.array([0.74])
    # A_sc = np.array([4.0e-4])
    # dsc = np.array([0.06])
    # A_p = np.array([14.0e-4])
    # dp = np.array([0.6])

    alpha_E_s = 6.0606  # Fator de equivalência do aço
    alpha_E_p = 6.0606  # Fator de equivalência do pré-esforço

    M = 800 # Momento fletor
    P = 1400 # Força normal de pré-esforço
    fctm = 3.6 # Resistência à tração do betão

    root = calc_neutral_axis_cracked_T(h, bf, bw, hf, A_s, A_sc, A_p, ds, dsc, dp,
                                alpha_E_s, alpha_E_p, M, P, display=True)

    # Calcular valores
    prop_un = calc_section_T_uncrack(h, bw, bf, hf, A_s, A_sc, A_p, ds, dsc, dp,
                                alpha_E_s, alpha_E_p, M, P, display=True)
    root_un = prop_un["NeutralAxis"]
    Aun = prop_un["Area"]
    Iun = prop_un["Inertia"]
    zgun = prop_un["zGi"]
    zgsun = prop_un["zGs"]

    Mcr = (fctm + P/Aun) * prop_un["Wi"] + P * np.sum(prop_un["e_p"])

    # Calcular valores
    prop_cr = calc_section_T_crack(h, bw, bf, hf, A_s, A_sc, A_p, ds, dsc, dp, alpha_E_s, alpha_E_p, M, P, display=True)
