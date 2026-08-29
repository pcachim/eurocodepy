"""Validação EC8 (EN 1998-1) — ação sísmica, ``eurocodepy.ec8``.

Chama diretamente as funções de baixo nível do ``eurocodepy`` e compara com
a mesma fórmula da norma, escrita à mão, dentro deste script — as quatro
ramificações do espetro (T<TB, TB≤T<TC, TC≤T<TD, T≥TD), tanto para o espetro
elástico Se(T) como para o de cálculo Sd(T).

Requer o ``eurocodepy`` instalado a partir do código-fonte real do
repositório.

Correr:  python validation/validation_seismic.py
Gera:    validation/validation_seismic.md
"""
from __future__ import annotations

_results: list[bool] = []
_md: list[str] = []

# Parâmetros-tipo: terreno tipo B (TB=0.15, TC=0.5, TD=2.0, S=1.2 — Anexo
# Nacional Português, zona genérica), ag=1.5 m/s², q=1.5 (espetro de
# cálculo), amortecimento 5% (η=1.0).
AG, S_VAL, T_B, T_C, T_D = 1.5, 1.2, 0.15, 0.5, 2.0
Q, BETA = 1.5, 0.2


def _check(name: str, got: float, expected: float, tol: float, unit: str = "") -> bool:
    ok = abs(got - expected) <= tol
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: got={got:.6g}{unit} expected={expected:.6g}{unit} "
          f"(tol={tol:.3g}{unit})")
    _results.append(ok)
    return ok


def _se_hand(period: float, eta: float = 1.0) -> float:
    """Espetro elástico Se(T) — EN 1998-1 Eq. 3.2-3.5, escrito à mão."""
    ag_s = AG * S_VAL
    if period < T_B:
        return ag_s * (1.0 + period / T_B * (eta * 2.5 - 1.0))
    if period < T_C:
        return ag_s * eta * 2.5
    if period < T_D:
        return ag_s * eta * 2.5 * (T_C / period)
    return ag_s * eta * 2.5 * (T_C * T_D / period**2)


def _sd_hand(period: float) -> float:
    """Espetro de cálculo Sd(T) — EN 1998-1 Eq. 3.13-3.16, escrito à mão."""
    ag_s = AG * S_VAL
    if period < T_B:
        return ag_s * (2.0 / 3.0 + period / T_B * (2.5 / Q - 2.0 / 3.0))
    if period < T_C:
        return ag_s * 2.5 / Q
    if period < T_D:
        return max(ag_s * 2.5 / Q * (T_C / period), BETA * AG)
    return max(ag_s * 2.5 / Q * (T_C * T_D / period**2), BETA * AG)


def case_damping_correction() -> None:
    """Fator de correção de amortecimento η — EN 1998-1 Eq. 3.6."""
    from eurocodepy.ec8.spectrum import damping_correction

    eta5 = damping_correction(5.0)
    eta5_hand = max((10.0 / (5.0 + 5.0)) ** 0.5, 0.55)
    eta10 = damping_correction(10.0)
    eta10_hand = max((10.0 / (5.0 + 10.0)) ** 0.5, 0.55)

    ok1 = _check("η(5%) == 1.0 (amortecimento de referência)", eta5, 1.0, 1e-9)
    ok2 = _check("η(5%) à mão == damping_correction", eta5, eta5_hand, 1e-9)
    ok3 = _check("η(10%) à mão == damping_correction", eta10, eta10_hand, 1e-9)
    _md.append(f"""### Fator de correção de amortecimento η — EN 1998-1 Eq. 3.6

```
η = √(10/(5+ξ)) ≥ 0.55                     η(5%)={eta5_hand:.5f}, η(10%)={eta10_hand:.5f}
```

`eurocodepy.ec8.spectrum.damping_correction(5.0)` → η={eta5:.5f}.
`damping_correction(10.0)` → η={eta10:.5f}.

| Verificação | Resultado |
|---|---|
| η(5%) = 1.0 | {'✓ PASS' if ok1 else '✗ FAIL'} |
| η(5%) à mão == função | {'✓ PASS' if ok2 else '✗ FAIL'} |
| η(10%) à mão == função | {'✓ PASS' if ok3 else '✗ FAIL'} |
""")


def case_elastic_spectrum() -> None:
    """Espetro elástico Se(T) nas quatro ramificações — EN 1998-1 §3.2.2.2."""
    from eurocodepy.ec8.spectrum import calc_elastic_spectrum

    periods = {
        "T < T_B (0.05 s)": 0.05,
        "T_B ≤ T < T_C (0.30 s)": 0.30,
        "T_C ≤ T < T_D (1.00 s)": 1.00,
        "T ≥ T_D (3.00 s)": 3.00,
    }
    rows = []
    all_ok = True
    for label, t in periods.items():
        got = calc_elastic_spectrum(t, AG, S_VAL, T_B, T_C, T_D, damping=5.0)
        hand = _se_hand(t, eta=1.0)
        ok = _check(f"Elastic spectrum Se({label})", got, hand, 1e-9, " m/s²")
        all_ok = all_ok and ok
        rows.append((label, t, hand, got, ok))

    table = "\n".join(
        f"| {lbl} | {t:.2f} | {hand:.4f} | {got:.4f} | {'✓ PASS' if ok else '✗ FAIL'} |"
        for lbl, t, hand, got, ok in rows)
    _md.append(f"""### Espetro elástico Se(T) — EN 1998-1 §3.2.2.2 (Eq. 3.2-3.5)

a_g={AG} m/s², S={S_VAL}, T_B={T_B} s, T_C={T_C} s, T_D={T_D} s, η=1.0 (5% amort.).

```
T < T_B:        Se = ag·S·[1 + T/T_B·(η·2.5−1)]
T_B ≤ T < T_C:  Se = ag·S·η·2.5
T_C ≤ T < T_D:  Se = ag·S·η·2.5·(T_C/T)
T ≥ T_D:        Se = ag·S·η·2.5·(T_C·T_D/T²)
```

| Ramo | T [s] | Se à mão [m/s²] | Se `calc_elastic_spectrum` [m/s²] | Resultado |
|---|---|---|---|---|
{table}

| Verificação | Resultado |
|---|---|
| As 4 ramificações batem certo | {'✓ PASS' if all_ok else '✗ FAIL'} |
""")


def case_design_spectrum() -> None:
    """Espetro de cálculo Sd(T) nas quatro ramificações — EN 1998-1 §3.2.2.5."""
    from eurocodepy.ec8.spectrum import calc_spectrum

    periods = {
        "T < T_B (0.05 s)": 0.05,
        "T_B ≤ T < T_C (0.30 s)": 0.30,
        "T_C ≤ T < T_D (1.00 s)": 1.00,
        "T ≥ T_D (3.00 s)": 3.00,
    }
    rows = []
    all_ok = True
    for label, t in periods.items():
        got = calc_spectrum(t, AG, S_VAL, Q, T_B, T_C, T_D, beta=BETA)
        hand = _sd_hand(t)
        ok = _check(f"Design spectrum Sd({label})", got, hand, 1e-9, " m/s²")
        all_ok = all_ok and ok
        rows.append((label, t, hand, got, ok))

    table = "\n".join(
        f"| {lbl} | {t:.2f} | {hand:.4f} | {got:.4f} | {'✓ PASS' if ok else '✗ FAIL'} |"
        for lbl, t, hand, got, ok in rows)
    _md.append(f"""### Espetro de cálculo Sd(T) — EN 1998-1 §3.2.2.5 (Eq. 3.13-3.16)

a_g={AG} m/s², S={S_VAL}, q={Q}, T_B={T_B} s, T_C={T_C} s, T_D={T_D} s, β={BETA}.

```
T < T_B:        Sd = ag·S·[2/3 + T/T_B·(2.5/q−2/3)]
T_B ≤ T < T_C:  Sd = ag·S·2.5/q
T_C ≤ T < T_D:  Sd = max(ag·S·2.5/q·(T_C/T), β·ag)
T ≥ T_D:        Sd = max(ag·S·2.5/q·(T_C·T_D/T²), β·ag)
```

| Ramo | T [s] | Sd à mão [m/s²] | Sd `calc_spectrum` [m/s²] | Resultado |
|---|---|---|---|---|
{table}

| Verificação | Resultado |
|---|---|
| As 4 ramificações batem certo | {'✓ PASS' if all_ok else '✗ FAIL'} |
""")


def _write_md(path: str) -> None:
    n_pass, n_total = sum(_results), len(_results)
    header = f"""# Validação EC8 (EN 1998-1) — ação sísmica

Cálculo independente: as expressões do Eurocódigo 8 são escritas aqui
diretamente a partir do texto da norma (§3.2.2.2 e §3.2.2.5) e comparadas
com o resultado real das funções do `eurocodepy.ec8`, nas quatro
ramificações do espetro (T<T_B, T_B≤T<T_C, T_C≤T<T_D, T≥T_D).
**{n_pass}/{n_total}** comparações numéricas OK.

Parâmetros: a_g={AG} m/s², S={S_VAL}, T_B={T_B} s, T_C={T_C} s, T_D={T_D} s,
q={Q} (espetro de cálculo), β={BETA}.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_md))
        f.write(f"\n\n## Resumo\n\n{n_pass}/{n_total} verificações OK.\n")


def main() -> int:
    case_damping_correction()
    case_elastic_spectrum()
    case_design_spectrum()
    _write_md("validation/validation_seismic.md")
    n_pass, n_total = sum(_results), len(_results)
    print(f"\n{n_pass}/{n_total} PASS")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
