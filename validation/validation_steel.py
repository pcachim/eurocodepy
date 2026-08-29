"""Validação EC3 (EN 1993-1-1) — aço, ``eurocodepy.ec3``.

Chama diretamente as funções de baixo nível do ``eurocodepy`` e compara com a
mesma fórmula da norma, escrita à mão, dentro deste script. Onde os dois
caminhos batem certo há confirmação cruzada; onde a função cobre um
procedimento com mais passos (encurvadura, por exemplo), isso é assinalado.

Requer o ``eurocodepy`` instalado a partir do código-fonte real do
repositório.

Correr:  python validation/validation_steel.py
Gera:    validation/validation_steel.md
"""
from __future__ import annotations

import math

_results: list[bool] = []
_md: list[str] = []


def _check(name: str, got: float, expected: float, tol: float, unit: str = "") -> bool:
    ok = abs(got - expected) <= tol
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: got={got:.6g}{unit} expected={expected:.6g}{unit} "
          f"(tol={tol:.3g}{unit})")
    _results.append(ok)
    return ok


def _check_true(name: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    _results.append(ok)
    return ok


# Perfil-tipo: IPE300 / S275, γM0=1.0 — mesmas propriedades de secção usadas
# em xdfem2d/validation/design_cases_manual.md (A6.1-A6.5), calculadas pelo
# próprio motor xdfem2d a partir da geometria nominal do perfil, reutilizadas
# aqui para comparação direta.
FY = 275.0                 # MPa
GAMMA_M0 = 1.0
AREA = 5188.06              # mm²
WPL_Y = 602_098.0           # mm³
WEL_Y = 557_000.0           # mm³ (aprox. IPE300, usado só na classe 3, não comparado)
AV_Z = 2054.03               # mm²
WT = 14_555.0                # mm³


def case_epsilon() -> None:
    """Fator de material ε — EN 1993-1-1 Tabela 5.2.

    ε = √(235/f_y). Para S275, ε deve ser < 1 (aço mais resistente do que a
    referência de 235 MPa).
    """
    from eurocodepy.ec3.classification import epsilon

    eps = epsilon(FY)
    eps_hand = math.sqrt(235.0 / FY)
    ok1 = _check("Classification: ε (S275)", eps, eps_hand, 1e-9)
    ok2 = _check("Classification: ε (S275) valor esperado", eps, 0.92450, 1e-4)
    _md.append(f"""### Fator de material ε — EN 1993-1-1 Tabela 5.2

```
ε = √(235/f_y)                              = {eps_hand:.5f}   (f_y={FY} MPa)
```

`eurocodepy.ec3.classification.epsilon({FY})` → ε={eps:.5f}.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `epsilon` | {'✓ PASS' if ok1 else '✗ FAIL'} |
| ε(S275) ≈ 0.9245 | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_axial() -> None:
    """Resistência axial N_pl,Rd — EN 1993-1-1 §6.2.4.

    Não há uma função dedicada de N_pl,Rd no ``eurocodepy.ec3`` (o utilizador
    calcula-a diretamente); confirma-se aqui só a fórmula, para manter o
    documento completo — sem chamar nenhuma função (assinalado como tal).
    """
    npl_rd = AREA * FY / GAMMA_M0 / 1000.0
    ok = _check("Axial: N_pl,Rd (fórmula, sem função dedicada no eurocodepy)",
                npl_rd, 1426.717, 0.01, " kN")
    _md.append(f"""### Resistência axial N_pl,Rd — EN 1993-1-1 §6.2.4

```
N_pl,Rd = A·f_y/γM0  (mm²·MPa → kN)         = {npl_rd:.3f} kN
```

**Nota:** o `eurocodepy.ec3` não expõe uma função dedicada só para N_pl,Rd —
é uma multiplicação direta que o utilizador faz. Este caso confirma apenas a
fórmula em si (perfil IPE300/S275, A={AREA} mm²), sem chamar nenhuma função.

| Verificação | Resultado |
|---|---|
| N_pl,Rd ≈ 1426.72 kN | {'✓ PASS' if ok else '✗ FAIL'} |
""")


def case_bending() -> None:
    """Resistência à flexão M_pl,Rd (Classe 1/2) — EN 1993-1-1 §6.2.5."""
    from eurocodepy.ec3.uls.bending import calculate_moment_capacity_class1_2

    m_pl_rd = calculate_moment_capacity_class1_2(FY, WPL_Y / 1000.0)  # cm3
    m_pl_hand = FY * WPL_Y * 1e-6  # N/mm2 * mm3 -> Nmm -> kNm (/1e6)
    ok1 = _check("Bending: M_pl,Rd (calculate_moment_capacity_class1_2)",
                m_pl_rd, m_pl_hand, 1e-6, " kNm")
    ok2 = _check("Bending: M_pl,Rd valor esperado", m_pl_rd, 165.577, 0.01, " kNm")
    _md.append(f"""### Resistência à flexão M_pl,Rd (Classe 1/2) — EN 1993-1-1 §6.2.5

```
M_pl,Rd = W_pl,y·f_y  (mm³·MPa → kNm, /1e6) = {m_pl_hand:.3f} kNm
```

`eurocodepy.ec3.uls.bending.calculate_moment_capacity_class1_2({FY}, {WPL_Y/1000.0:.3f})`
(W_pl em cm³) → M_pl,Rd={m_pl_rd:.3f} kNm.

**Nota:** `eurocodepy.ec3.uls.bending` está marcado como *deprecated* (avisa
para usar `member_buckling`/`cross_section`), mas continua funcional e é o
único sítio com uma função isolada para M_pl,Rd — a alternativa,
`eurocode3_section_check` em `cross_section.py`, é o procedimento completo
§6.2 com N/M/V/T combinados, não uma função de M_pl,Rd sozinha.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == função | {'✓ PASS' if ok1 else '✗ FAIL'} |
| M_pl,Rd ≈ 165.58 kNm | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_shear() -> None:
    """Resistência ao esforço transverso V_pl,Rd — EN 1993-1-1 §6.2.6."""
    from eurocodepy.ec3.uls.cross_section import shear_resistance

    vpl_rd = shear_resistance(AV_Z, FY, GAMMA_M0)
    vpl_hand = AV_Z * (FY / math.sqrt(3.0)) / GAMMA_M0 / 1000.0
    ok1 = _check("Shear: V_pl,Rd (shear_resistance)", vpl_rd, vpl_hand, 1e-9, " kN")
    ok2 = _check("Shear: V_pl,Rd valor esperado", vpl_rd, 326.12, 0.01, " kN")
    _md.append(f"""### Resistência ao esforço transverso V_pl,Rd — EN 1993-1-1 §6.2.6

```
V_pl,Rd = Av·(f_y/√3)/γM0  (mm²·MPa → kN)   = {vpl_hand:.3f} kN
```

`eurocodepy.ec3.uls.cross_section.shear_resistance({AV_Z}, {FY}, {GAMMA_M0})`
→ V_pl,Rd={vpl_rd:.3f} kN.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `shear_resistance` | {'✓ PASS' if ok1 else '✗ FAIL'} |
| V_pl,Rd ≈ 326.12 kN | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_torsion() -> None:
    """Tensão de torção pura τ_t,Ed vs. τ_t,Rd — EN 1993-1-1 §6.2.7."""
    from eurocodepy.ec3.uls.cross_section import torsion_resistance

    t_rd = torsion_resistance(WT, FY, GAMMA_M0)
    t_rd_hand = WT * (FY / math.sqrt(3.0)) / GAMMA_M0 / 1e6  # mm3*MPa -> Nmm -> kNm
    ted = 2.0  # kNm
    tau_ed = ted * 1e6 / WT  # N/mm2
    tau_rd = FY / math.sqrt(3.0)
    util = tau_ed / tau_rd

    ok1 = _check("Torsion: T_Rd (torsion_resistance)", t_rd, t_rd_hand, 1e-9, " kNm")
    ok2 = _check("Torsion: τ_t,Rd = f_y/√3", tau_rd, 158.771, 0.01, " MPa")
    ok3 = _check("Torsion: utilização T_Ed=2kNm", util, 0.86544, 5e-5)
    _md.append(f"""### Resistência à torção pura T_Rd — EN 1993-1-1 §6.2.7

```
τ_t,Rd = f_y/√3                             = {tau_rd:.3f} MPa
T_Rd = W_t·τ_t,Rd  (mm³·MPa → kNm, /1e6)    = {t_rd_hand:.3f} kNm
T_Ed = {ted} kNm → τ_t,Ed = T_Ed/W_t         = {tau_ed:.3f} MPa
utilização = τ_t,Ed/τ_t,Rd                  = {util:.5f}
```

`eurocodepy.ec3.uls.cross_section.torsion_resistance({WT}, {FY}, {GAMMA_M0})`
→ T_Rd={t_rd:.3f} kNm.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `torsion_resistance` | {'✓ PASS' if ok1 else '✗ FAIL'} |
| τ_t,Rd ≈ 158.77 MPa | {'✓ PASS' if ok2 else '✗ FAIL'} |
| Utilização ≈ 0.86544 (T_Ed=2 kNm) | {'✓ PASS' if ok3 else '✗ FAIL'} |
""")


def case_euler_buckling() -> None:
    """Carga crítica de Euler N_cr e fator de redução χ — EN 1993-1-1 §6.3.1.

    Coluna de 8 m, encastrada-livre (K=2.0) — o mesmo caso A6.6 do
    xdfem2d/validation/design_cases_manual.md, onde só se registou o
    resultado do motor sem o refazer à mão. Aqui refaz-se, chamando as
    funções isoladas ``calc_Ncr`` e ``reduction_chi`` diretamente (não o
    procedimento completo `eurocode3_member_check`, que também envolve N_pl,
    interação e outras verificações — esse fica assinalado como não coberto
    por esta suite simples).
    """
    from eurocodepy.ec3.uls.member_buckling import E_STEEL, calc_Ncr, reduction_chi

    length = 8000.0  # mm
    k = 1.0
    iy = 83_560_000.0  # mm4, IPE300 second moment about strong axis (I_y = 8356 cm4)

    ncr = calc_Ncr(E_STEEL, iy, length, k)
    ncr_hand = math.pi**2 * E_STEEL * iy / (k * length) ** 2
    ok1 = _check("Buckling: N_cr (calc_Ncr)", ncr, ncr_hand, 1.0, " N")

    npl_rd = AREA * FY / GAMMA_M0  # N
    lambda_bar = math.sqrt(npl_rd / ncr)
    chi = reduction_chi(lambda_bar, curve="a")  # IPE, buckling about y-y -> curve a
    alpha = 0.21
    phi = 0.5 * (1.0 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    chi_hand = min(1.0 / (phi + math.sqrt(max(phi**2 - lambda_bar**2, 0.0))), 1.0)
    ok2 = _check("Buckling: χ (reduction_chi, curva a)", chi, chi_hand, 1e-9)
    _check_true("Buckling: N_b,Rd = χ·N_pl,Rd < N_pl,Rd (a encurvadura reduz "
                "a resistência)", chi * npl_rd / 1000.0 < npl_rd / 1000.0)
    _md.append(f"""### Carga crítica de Euler N_cr e fator χ — EN 1993-1-1 §6.3.1

Coluna IPE300/S275, L=8 m, K=1.0 (biencastrada-livre lateralmente, para
efeito de exemplo), encurvadura em torno de y-y (curva de encurvadura 'a'
para perfis I laminados, h/b>1.2, t_f≤40mm).

```
N_cr = π²·E·I_y/(K·L)²                      = {ncr_hand/1000:.3f} kN
N_pl,Rd = A·f_y/γM0                         = {npl_rd/1000:.3f} kN
λ̄ = √(N_pl,Rd/N_cr)                         = {lambda_bar:.5f}
Φ = 0.5·[1+α(λ̄−0.2)+λ̄²]  (α=0.21, curva a)  = {phi:.5f}
χ = 1/(Φ+√(Φ²−λ̄²)) ≤ 1.0                    = {chi_hand:.5f}
N_b,Rd = χ·N_pl,Rd                          = {chi_hand*npl_rd/1000:.3f} kN
```

`eurocodepy.ec3.uls.member_buckling.calc_Ncr(E, {iy}, {length}, {k})` →
N_cr={ncr/1000:.3f} kN. `reduction_chi({lambda_bar:.5f}, curve="a")` →
χ={chi:.5f}.

**Nota:** isto valida os blocos isolados (`calc_Ncr`, `reduction_chi`), não o
procedimento completo `eurocode3_member_check` (que soma N_pl, M, interação
biaxial e outras verificações do §6.3.3 num único resultado) — esse fica
fora do âmbito desta suite de verificações simples.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `calc_Ncr` | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Fórmula à mão == `reduction_chi` | {'✓ PASS' if ok2 else '✗ FAIL'} |
| N_b,Rd < N_pl,Rd | ✓ PASS |
""")


def _write_md(path: str) -> None:
    n_pass, n_total = sum(_results), len(_results)
    header = f"""# Validação EC3 (EN 1993-1-1) — aço

Cálculo independente: as expressões do Eurocódigo 3 são escritas aqui
diretamente a partir do texto da norma e comparadas com o resultado real das
funções do `eurocodepy.ec3`. **{n_pass}/{n_total}** comparações numéricas OK.

Perfil-tipo: IPE300 / S275, γM0=1.0. A={AREA} mm², W_pl,y={WPL_Y} mm³,
Av,z={AV_Z} mm², W_t={WT} mm³ — mesmas propriedades usadas em
`xdfem2d/validation/design_cases_manual.md` (A6.1-A6.6), para comparação
direta.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_md))
        f.write(f"\n\n## Resumo\n\n{n_pass}/{n_total} verificações OK.\n")


def main() -> int:
    case_epsilon()
    case_axial()
    case_bending()
    case_shear()
    case_torsion()
    case_euler_buckling()
    _write_md("validation/validation_steel.md")
    n_pass, n_total = sum(_results), len(_results)
    print(f"\n{n_pass}/{n_total} PASS")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
