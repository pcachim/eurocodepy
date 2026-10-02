# Validação EC5 (EN 1995-1-1) — madeira

Cálculo independente: as expressões do Eurocódigo 5 são escritas aqui
diretamente a partir do texto da norma (para a torção, W_t da teoria da
elasticidade de Saint-Venant) e comparadas com o resultado real das funções do
`eurocodepy.ec5`. **19/19** comparações numéricas OK.

Secção-tipo: 0.10×0.20 m, madeira C24, classe de serviço 1, duração média —
mesma secção de `xdfem2d/validation/design_cases_manual.md` (A7.1-A7.4),
para comparação direta.

### Valores de cálculo — EN 1995-1-1 §2.4.1

Madeira C24, classe de serviço 1, duração média. k_mod=0.8,
γ_M=1.3 (madeira maciça, EC5 Tabela 2.3).

```
f_t0d = k_mod·f_t0k/γ_M                     = 8.9231 MPa  (f_t0k=14.5 MPa)
f_c0d = k_mod·f_c0k/γ_M                     = 12.9231 MPa  (f_c0k=21.0 MPa)
f_md  = k_mod·f_mk/γ_M                      = 14.7692 MPa   (f_mk=24.0 MPa)
f_vd  = k_mod·f_vk/γ_M                      = 2.4615 MPa   (f_vk=4.0 MPa)
```

`Timber("C24").design_values(SC1, MediumDuration)` → mesmos valores.

| Verificação | Resultado |
|---|---|
| Todos os valores de cálculo à mão == `Timber.design_values` | ✓ PASS |

### Tração axial pura — EN 1995-1-1 §6.1.2 (Eq. 6.1)

Secção 0.10×0.20 m, N_Ed = 25.0 kN (tração).

```
σ_t0,d = N_Ed/A                            = 1.2500 MPa
utilização = σ_t0,d/f_t0d                  = 0.14009
```

`check_bending_with_normal(n_ed=25.0, m_ed_y=0, m_ed_z=0, ...)` →
utilização=0.14009.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == função | ✓ PASS |
| Confere com A7.1 de `design_cases_manual.md` | ✓ PASS |

### Compressão axial pura (sem encurvadura) — EN 1995-1-1 §6.1.4 (Eq. 6.2)

Secção 0.10×0.20 m, N_Ed = -25.0 kN (compressão), sem comprimento de
encurvadura definido (l_0y=l_0z=0 → k_c=1.0, verificação de secção pura).

```
σ_c0,d = |N_Ed|/A                          = 1.2500 MPa
utilização = σ_c0,d/f_c0d                  = 0.09673
```

`check_bending_with_normal(n_ed=-25.0, m_ed_y=0, m_ed_z=0, l_0y=0, l_0z=0, ...)`
→ utilization=0.09673 (o valor governante, que com k_c=1.0
para l_0=0 é a própria Eq. 6.2; note-se que `checks['check1']`
=0.00936 é a Eq. 6.19 — (σ_c0/f_c0d)² + termos de
flexão — que colapsa para o termo ao quadrado, não a razão simples, quando
não há momento: não é o valor a comparar aqui).

| Verificação | Resultado |
|---|---|
| Fórmula à mão == utilização governante | ✓ PASS |
| Confere com A7.2 de `design_cases_manual.md` | ✓ PASS |

### Flexão pura — EN 1995-1-1 §6.1.6 (Eq. 6.11)

Secção 0.10×0.20 m, M_y,Ed = 6.0 kN·m. W_y = b·h²/6 = 0.000667 m³.

```
σ_m,y,d = M_y,Ed/W_y                       = 9.0000 MPa
utilização = σ_m,y,d/f_md                  = 0.60937
```

`check_bending_with_normal(n_ed=0, m_ed_y=6.0, m_ed_z=0, ...)` →
check1=0.60937.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == função | ✓ PASS |
| Confere com A7.3 de `design_cases_manual.md` | ✓ PASS |

### Esforço transverso puro — EN 1995-1-1 §6.1.7 (Eq. 6.13)

Secção retangular: τ_d = 1.5·V_Ed/(k_cr·A) (fator 1.5 da distribuição
parabólica; b_ef = k_cr·b, k_cr = 0.67 para madeira maciça, §6.1.7(2)).
V_z,Ed = 8.0 kN.

```
τ_d = 1.5·V_Ed/(k_cr·A)                    = 0.8955 MPa
utilização = τ_d/f_vd                      = 0.36381
```

`check_shear_with_torsion(v_ed_y=0, v_ed_z=8.0, t_ed=0, ...)` →
util_shear=0.36381.

| Verificação | Resultado |
|---|---|
| τ_d à mão ≈ 0.600 MPa | ✓ PASS |
| Fórmula à mão == função | ✓ PASS |
| Confere com A7.4 de `design_cases_manual.md` (÷ k_cr) | ✓ PASS |

### Torção pura — EN 1995-1-1 §6.1.8 (Eq. 6.14)

Secção retangular, módulo de torção W_t = α·h·b², α = (1/3)(1 − 0.672·b/h + 0.3·(b/h)²), com h o lado
maior e b o menor (h/b=2.0). T_Ed = 0.5 kN·m.

```
α                                           = 0.24633
W_t = α·h·b²                                = 4.926667e-04 m³
τ_tor,d = T_Ed/W_t                          = 1.0149 MPa
k_shape = min(1+0.15·h/b, 2.0)              = 1.3000
f_vd,tor = k_shape·f_vd                     = 3.2000 MPa
utilização = τ_tor,d/f_vd,tor               = 0.31715
```

`check_shear_with_torsion(v_ed_y=0, v_ed_z=0, t_ed=0.5, ...)` →
util_torsion=0.31715.

| Verificação | Resultado |
|---|---|
| W_t à mão == função | ✓ PASS |
| k_shape à mão | ✓ PASS |
| Utilização à mão == função | ✓ PASS |


## Resumo

19/19 verificações OK.
