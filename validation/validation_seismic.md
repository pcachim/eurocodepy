# Validação EC8 (EN 1998-1) — ação sísmica

Cálculo independente: as expressões do Eurocódigo 8 são escritas aqui
diretamente a partir do texto da norma (§3.2.2.2 e §3.2.2.5) e comparadas
com o resultado real das funções do `eurocodepy.ec8`, nas quatro
ramificações do espetro (T<T_B, T_B≤T<T_C, T_C≤T<T_D, T≥T_D).
**11/11** comparações numéricas OK.

Parâmetros: a_g=1.5 m/s², S=1.2, T_B=0.15 s, T_C=0.5 s, T_D=2.0 s,
q=1.5 (espetro de cálculo), β=0.2.

### Fator de correção de amortecimento η — EN 1998-1 Eq. 3.6

```
η = √(10/(5+ξ)) ≥ 0.55                     η(5%)=1.00000, η(10%)=0.81650
```

`eurocodepy.ec8.spectrum.damping_correction(5.0)` → η=1.00000.
`damping_correction(10.0)` → η=0.81650.

| Verificação | Resultado |
|---|---|
| η(5%) = 1.0 | ✓ PASS |
| η(5%) à mão == função | ✓ PASS |
| η(10%) à mão == função | ✓ PASS |

### Espetro elástico Se(T) — EN 1998-1 §3.2.2.2 (Eq. 3.2-3.5)

a_g=1.5 m/s², S=1.2, T_B=0.15 s, T_C=0.5 s, T_D=2.0 s, η=1.0 (5% amort.).

```
T < T_B:        Se = ag·S·[1 + T/T_B·(η·2.5−1)]
T_B ≤ T < T_C:  Se = ag·S·η·2.5
T_C ≤ T < T_D:  Se = ag·S·η·2.5·(T_C/T)
T ≥ T_D:        Se = ag·S·η·2.5·(T_C·T_D/T²)
```

| Ramo | T [s] | Se à mão [m/s²] | Se `calc_elastic_spectrum` [m/s²] | Resultado |
|---|---|---|---|---|
| T < T_B (0.05 s) | 0.05 | 2.7000 | 2.7000 | ✓ PASS |
| T_B ≤ T < T_C (0.30 s) | 0.30 | 4.5000 | 4.5000 | ✓ PASS |
| T_C ≤ T < T_D (1.00 s) | 1.00 | 2.2500 | 2.2500 | ✓ PASS |
| T ≥ T_D (3.00 s) | 3.00 | 0.5000 | 0.5000 | ✓ PASS |

| Verificação | Resultado |
|---|---|
| As 4 ramificações batem certo | ✓ PASS |

### Espetro de cálculo Sd(T) — EN 1998-1 §3.2.2.5 (Eq. 3.13-3.16)

a_g=1.5 m/s², S=1.2, q=1.5, T_B=0.15 s, T_C=0.5 s, T_D=2.0 s, β=0.2.

```
T < T_B:        Sd = ag·S·[2/3 + T/T_B·(2.5/q−2/3)]
T_B ≤ T < T_C:  Sd = ag·S·2.5/q
T_C ≤ T < T_D:  Sd = max(ag·S·2.5/q·(T_C/T), β·ag)
T ≥ T_D:        Sd = max(ag·S·2.5/q·(T_C·T_D/T²), β·ag)
```

| Ramo | T [s] | Sd à mão [m/s²] | Sd `calc_spectrum` [m/s²] | Resultado |
|---|---|---|---|---|
| T < T_B (0.05 s) | 0.05 | 1.8000 | 1.8000 | ✓ PASS |
| T_B ≤ T < T_C (0.30 s) | 0.30 | 3.0000 | 3.0000 | ✓ PASS |
| T_C ≤ T < T_D (1.00 s) | 1.00 | 1.5000 | 1.5000 | ✓ PASS |
| T ≥ T_D (3.00 s) | 3.00 | 0.3333 | 0.3333 | ✓ PASS |

| Verificação | Resultado |
|---|---|
| As 4 ramificações batem certo | ✓ PASS |


## Resumo

11/11 verificações OK.
