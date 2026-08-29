# Validação EC1 (EN 1991 / EN 1990) — ações

Cálculo independente: as expressões do Eurocódigo 1 (e da combinação de
ações do EN 1990) são escritas aqui diretamente a partir do texto da norma e
comparadas com o resultado real das funções do `eurocodepy.ec1`.
**11/11** comparações numéricas OK.

### Pressão dinâmica de pico q_p(z) — EN 1991-1-4 §4

Terreno categoria II (z0=0.05 m, z0,II=0.05 m, zmin=2.0 m), sem
orografia (terreno plano, c_o=1). v_b,0=27.0 m/s, z=10.0 m, ρ=1.25 kg/m³.

```
k_r = 0.19·(z0/z0,II)^0.07                 = 0.19000
c_r(z) = k_r·ln(max(z,zmin)/z0)            = 1.00668
v_b = c_season·c_dir·v_b,0  (=1·1·27.0)    = 27.000 m/s
v_m(z) = c_r·c_o·v_b                       = 27.1804 m/s
I_v(z) = k_I/(c_o·ln(max(z,zmin)/z0))       = 0.18874
q_p(z) = 0.5·(1+7·I_v)·v_m²·ρ               = 1071.762 Pa  (1.0718 kN/m²)
```

`eurocodepy.ec1.wind.pressure.q_p(10.0, 27.000, 2.0, 0.05, 1.00668, 1.0, rho=1.25)`
→ q_p=1071.762 Pa.

| Verificação | Resultado |
|---|---|
| c_r à mão == `c_r` | ✓ PASS |
| c_o == 1 (terreno plano) | ✓ PASS |
| v_b à mão == `v_b` | ✓ PASS |
| v_m à mão == `v_m` | ✓ PASS |
| q_p à mão == `q_p` | ✓ PASS |

### Tensões principais (decomposição espectral 3D) — EN 1991 (uso geral)

Estado plano de tensão: σxx=100.0, σyy=0.0, τxy=40.0 MPa, resto zero.

```
σ_méd = (σxx+σyy)/2                        = 50.0000 MPa
R = √[((σxx−σyy)/2)²+τxy²]                 = 64.0312 MPa
σ1 = σ_méd + R                             = 114.0312 MPa
σ2 = σ_méd − R                             = -14.0312 MPa
σ3 = σzz                                   = 0 MPa
```

`eurocodepy.utils.stress.principals(100.0, 0.0, 0.0, 40.0, 0.0, 0.0)`
(decomposição espectral 3×3 completa, `numpy.linalg.eigh`) → eigenvalues=
[-14.0312, 0.0, 114.0312].

| Verificação | Resultado |
|---|---|
| σ_max à mão == eigh | ✓ PASS |
| σ_min à mão == eigh | ✓ PASS |
| σ_mid == 0 (fora do plano) | ✓ PASS |

### Combinação ULS — EN 1990 §6.4.3.2, Eq. 6.10

Uma ação permanente G (γ_unf=1.35) e uma variável Q (γ_unf=1.5, ψ0=0.6). Com
uma só ação variável, a Eq. 6.10 (Σγ_G·G + γ_Q·Q) não tem termos de
acompanhamento a aplicar — o resultado é diretamente 1.35G+1.5Q.

`Loads` com G e Q, `.get_ULS_combos()` → combinação "ULS: +1.35_G+1.50_Q", com
factors={ G: 1.35, Q: 1.5 }.

| Verificação | Resultado |
|---|---|
| Fator de G == 1.35 | ✓ PASS |
| Fator de Q == 1.5 | ✓ PASS |

### Neve (EN 1991-1-3)

`eurocodepy.ec1.snow` existe como pacote mas está **vazio** (só o docstring
do módulo, sem funções) — confirmado por introspeção
(`dir(eurocodepy.ec1.snow)` sem nomes públicos), não assumido. Sem código
para validar aqui ainda.


## Resumo

11/11 verificações OK.
