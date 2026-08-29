# Validação EC7 (EN 1997-1) — geotecnia

Cálculo independente: as expressões do Eurocódigo 7 são escritas aqui
diretamente a partir do texto da norma (Anexos C e D) e comparadas com o
resultado real das funções do `eurocodepy.ec7`. **10/10**
comparações numéricas OK.

### Coeficientes de impulso de Rankine — EN 1997-1 (Anexo C)

Muro vertical, terrapleno horizontal (θ=β=0), φ=30.0°.

```
K_a = (1 − sinφ)/(1 + sinφ)                = 0.33333
K_p = 1/K_a                                = 3.00000
```

`eurocodepy.ec7.earth_pressures.pressure_coefficients(0.52360, 0, 0, 0, method="rankine")`
→ K_a=0.33333, K_p=3.00000.

| Verificação | Resultado |
|---|---|
| K_a à mão == função | ✓ PASS |
| K_p à mão == função | ✓ PASS |
| K_a(30°) ≈ 1/3 | ✓ PASS |
| K_p(30°) = 3.0 | ✓ PASS |

### Coeficiente de impulso em repouso K0 — fórmula de Jáky

φ=30°, OCR=1 (solo normalmente consolidado), terrapleno horizontal.

```
K0 = (1 − sinφ)·√OCR                       = 0.50000
```

`pressure_coefficients(0.52360, 0, 0, 0, method="inrest")` → K0=0.50000.

| Verificação | Resultado |
|---|---|
| K0 à mão == função | ✓ PASS |
| K0(φ=30°) = 0.5 | ✓ PASS |

### Capacidade de carga de fundação superficial — EN 1997-1 Anexo D

Sapata corrida (aproximada por B=2.0 m, L→∞), φ=30.0°, γ=18.0 kN/m³,
c=0, q=0 (sem sobrecarga), carga centrada (H=0, sem inclinação).

```
N_q = e^(π·tanφ)·tan²(45°+φ/2)             = 18.4011
N_c = (N_q−1)/tanφ                         = 30.1396
N_γ = 2·(N_q−1)·tanφ                       = 20.0931
R/A' = 0.5·γ·B·N_γ  (s_γ≈1, i_γ=1, c=q=0)   = 361.676 kN/m²
```

`eurocodepy.ec7.bearing_capacity.bearing_resistance(Bx=2.0, By=1e6, Hx=0, Hy=0, N=1, phi=0.52360, gamma=18.0, q=0, c=0)`
→ R/A'=361.675 kN/m².

| Verificação | Resultado |
|---|---|
| N_q à mão | ✓ PASS |
| N_c à mão | ✓ PASS |
| N_γ à mão | ✓ PASS |
| Fórmula completa à mão == função | ✓ PASS |


## Resumo

10/10 verificações OK.
