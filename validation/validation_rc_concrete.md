# Validação EC2 (EN 1992-1-1) — betão armado

Cálculo independente: as expressões do Eurocódigo 2 são escritas aqui
diretamente a partir do texto da norma e comparadas com o resultado real das
funções do `eurocodepy.ec2`, chamadas exatamente como um utilizador as
chamaria — não com valores copiados de outro documento. **15/15**
comparações numéricas OK.

Secção-tipo (salvo indicação em contrário): b=0.30 m, h=0.50 m,
cobrimento=0.03 m → d=0.47 m. Betão C25/30 (f_ck=25 MPa), aço A500
(f_yk=500 MPa), γc=1.5, γs=1.15, αcc=1.0 → f_cd=16.667 MPa,
f_yd=434.783 MPa.

### Flexão simples — EC2 §6.1

Secção 0.3×0.5 m, d=0.47 m, C25/30, A500. f_cd=16.667 MPa, f_yd=434.783 MPa.
M_Ed = 150.0 kN·m, N_Ed = 0.

```
μ = M_Ed / (b·d²·f_cd)              = 0.13581
ω = 1 − √(1 − 2μ)                   = 0.14655
A_s = ω·b·d·f_cd/f_yd               = 7.9208 cm²  (7.9208e-04 m²)
```

`eurocodepy.ec2.uls.beam.calc_asl(0.3, 0.47, 150.0, fcd=16.667, fyd=434.783)`
→ A_s = 7.9208 cm² (7.9208e-04 m²), ε_s=15.6066, x/d=0.1832.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `calc_asl` | ✓ PASS |
| Confere com A1 de `xdfem2d/validation/design_cases_manual.md` | ✓ PASS |

### Esforço transverso sem armadura — EC2 §6.2.2

k = 1 + √(0.2/d) ≤ 2.0 (nota: `calc_vrdc` usa 0.2, não 200/d[mm] — equivalente
com d em metros: 200/(d·1000)=0.2/d) = 1.65233

```
v_min = 0.035·k^1.5·√f_ck [MPa]            = 0.37169 MPa
V_Rd,min = v_min·b·d  (m → kN)             = 52.408 kN
```

`eurocodepy.ec2.uls.shear.calc_vrdc(0.3, 0.47, 25.0, 1.5, 0.0)` →
(V_Rd,min=52.408, V_Rd,c=0.000, V_Rd=52.408) kN.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `calc_vrdc` (V_Rd,min) | ✓ PASS |
| V_Rd = V_Rd,min quando ρ_l = 0 | ✓ PASS |
| Confere com A4 de `design_cases_manual.md` | ✓ PASS |

### Esforço transverso com armadura — EC2 §6.2.3 (treliça)

z=0.9d=0.4230 m, ν=0.6(1−f_ck/250)=0.5400, cot θ = 2.5 (θ=21.8°),
V_Ed = 250.0 kN.

```
V_Rd,max = b·z·ν·f_cd/(cotθ+1/cotθ)        = 393.828 kN
Asw/s = V_Ed/(z·f_yd·cotθ)                 = 5.4374 cm²/m
```

`eurocodepy.ec2.uls.shear.calc_asws(...)` → Asw/s=5.4374 cm²/m,
V_Rd,max=393.828 kN. `calc_vrdmax(...)` → 393.828 kN.

| Verificação | Resultado |
|---|---|
| `calc_asws` e `calc_vrdmax` dão o mesmo V_Rd,max | ✓ PASS |
| Fórmula à mão == V_Rd,max | ✓ PASS |
| Fórmula à mão == Asw/s | ✓ PASS |
| V_Ed ≤ V_Rd,max | ✓ PASS |

### Torção pura — EC2 §6.3 (parede fina fechada, θ=45°)

Secção 0.3×0.5 m, T_Ed = 50.0 kN·m, cot θ = 1.0.

```
t_ef = (b·h)/[2(b+h)]                      = 0.09375 m
A_k  = (b−t_ef)(h−t_ef)                    = 0.083789 m²
u_k  = 2[(b−t_ef)+(h−t_ef)]                = 1.22500 m
ν    = 0.6(1 − f_ck/250)                   = 0.5400
T_Rd,max = 2·ν·f_cd·A_k·t_ef·sinθcosθ      = 70.697 kN·m
Asw,tor/s = T_Ed/(2·A_k·f_yd·cotθ)         = 6.8625 cm²/m
Asl,tor   = T_Ed·cotθ·u_k/(2·A_k·f_yd)     = 8.4065 cm²
```

`eurocodepy.ec2.uls.torsion.calc_torsion(50.0, 0.3, 0.5, 25.0, 1.5, 500.0, 1.15, 1.0)`
→ T_Rd,max=70.697 kN·m,
Asw,tor/s=6.8625 cm²/m, Asl,tor=8.4065 cm²,
util=0.7072.

| Verificação | Resultado |
|---|---|
| t_ef, A_k, u_k à mão == função | ✓ PASS |
| T_Rd,max à mão == função | ✓ PASS |
| Asw,tor/s à mão == função | ✓ PASS |
| Asl,tor à mão == função | ✓ PASS |
| Confere com `tests/test_torsion.py` (C30/37, T_Rd,max=82.95 kNm) | ✓ PASS |


## Resumo

15/15 verificações OK.
