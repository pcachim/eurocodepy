# Validação EC3 (EN 1993-1-1) — aço

Cálculo independente: as expressões do Eurocódigo 3 são escritas aqui
diretamente a partir do texto da norma e comparadas com o resultado real das
funções do `eurocodepy.ec3`. **13/13** comparações numéricas OK.

Perfil-tipo: IPE300 / S275, γM0=1.0. A=5188.06 mm², W_pl,y=602098.0 mm³,
Av,z=2054.03 mm², W_t=14555.0 mm³ — mesmas propriedades usadas em
`xdfem2d/validation/design_cases_manual.md` (A6.1-A6.6), para comparação
direta.

### Fator de material ε — EN 1993-1-1 Tabela 5.2

```
ε = √(235/f_y)                              = 0.92442   (f_y=275.0 MPa)
```

`eurocodepy.ec3.classification.epsilon(275.0)` → ε=0.92442.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `epsilon` | ✓ PASS |
| ε(S275) ≈ 0.9245 | ✓ PASS |

### Resistência axial N_pl,Rd — EN 1993-1-1 §6.2.4

```
N_pl,Rd = A·f_y/γM0  (mm²·MPa → kN)         = 1426.716 kN
```

**Nota:** o `eurocodepy.ec3` não expõe uma função dedicada só para N_pl,Rd —
é uma multiplicação direta que o utilizador faz. Este caso confirma apenas a
fórmula em si (perfil IPE300/S275, A=5188.06 mm²), sem chamar nenhuma função.

| Verificação | Resultado |
|---|---|
| N_pl,Rd ≈ 1426.72 kN | ✓ PASS |

### Resistência à flexão M_pl,Rd (Classe 1/2) — EN 1993-1-1 §6.2.5

```
M_pl,Rd = W_pl,y·f_y  (mm³·MPa → kNm, /1e6) = 165.577 kNm
```

`eurocodepy.ec3.uls.bending.calculate_moment_capacity_class1_2(275.0, 602.098)`
(W_pl em cm³) → M_pl,Rd=165.577 kNm.

**Nota:** `eurocodepy.ec3.uls.bending` está marcado como *deprecated* (avisa
para usar `member_buckling`/`cross_section`), mas continua funcional e é o
único sítio com uma função isolada para M_pl,Rd — a alternativa,
`eurocode3_section_check` em `cross_section.py`, é o procedimento completo
§6.2 com N/M/V/T combinados, não uma função de M_pl,Rd sozinha.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == função | ✓ PASS |
| M_pl,Rd ≈ 165.58 kNm | ✓ PASS |

### Resistência ao esforço transverso V_pl,Rd — EN 1993-1-1 §6.2.6

```
V_pl,Rd = Av·(f_y/√3)/γM0  (mm²·MPa → kN)   = 326.121 kN
```

`eurocodepy.ec3.uls.cross_section.shear_resistance(2054.03, 275.0, 1.0)`
→ V_pl,Rd=326.121 kN.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `shear_resistance` | ✓ PASS |
| V_pl,Rd ≈ 326.12 kN | ✓ PASS |

### Resistência à torção pura T_Rd — EN 1993-1-1 §6.2.7

```
τ_t,Rd = f_y/√3                             = 158.771 MPa
T_Rd = W_t·τ_t,Rd  (mm³·MPa → kNm, /1e6)    = 2.311 kNm
T_Ed = 2.0 kNm → τ_t,Ed = T_Ed/W_t         = 137.410 MPa
utilização = τ_t,Ed/τ_t,Rd                  = 0.86546
```

`eurocodepy.ec3.uls.cross_section.torsion_resistance(14555.0, 275.0, 1.0)`
→ T_Rd=2.311 kNm.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `torsion_resistance` | ✓ PASS |
| τ_t,Rd ≈ 158.77 MPa | ✓ PASS |
| Utilização ≈ 0.86544 (T_Ed=2 kNm) | ✓ PASS |

### Carga crítica de Euler N_cr e fator χ — EN 1993-1-1 §6.3.1

Coluna IPE300/S275, L=8 m, K=1.0 (biencastrada-livre lateralmente, para
efeito de exemplo), encurvadura em torno de y-y (curva de encurvadura 'a'
para perfis I laminados, h/b>1.2, t_f≤40mm).

```
N_cr = π²·E·I_y/(K·L)²                      = 2706.060 kN
N_pl,Rd = A·f_y/γM0                         = 1426.716 kN
λ̄ = √(N_pl,Rd/N_cr)                         = 0.72611
Φ = 0.5·[1+α(λ̄−0.2)+λ̄²]  (α=0.21, curva a)  = 0.81886
χ = 1/(Φ+√(Φ²−λ̄²)) ≤ 1.0                    = 0.83514
N_b,Rd = χ·N_pl,Rd                          = 1191.512 kN
```

`eurocodepy.ec3.uls.member_buckling.calc_Ncr(E, 83560000.0, 8000.0, 1.0)` →
N_cr=2706.060 kN. `reduction_chi(0.72611, curve="a")` →
χ=0.83514.

**Nota:** isto valida os blocos isolados (`calc_Ncr`, `reduction_chi`), não o
procedimento completo `eurocode3_member_check` (que soma N_pl, M, interação
biaxial e outras verificações do §6.3.3 num único resultado) — esse fica
fora do âmbito desta suite de verificações simples.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `calc_Ncr` | ✓ PASS |
| Fórmula à mão == `reduction_chi` | ✓ PASS |
| N_b,Rd < N_pl,Rd | ✓ PASS |


## Resumo

13/13 verificações OK.
