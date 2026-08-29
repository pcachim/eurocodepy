# Validação do eurocodepy — índice

Suite de validação do pacote `eurocodepy`: cada `validation_*.py` chama
diretamente as funções de baixo nível do pacote (não um adaptador de outro
projeto) e compara o resultado com a mesma fórmula do Eurocódigo, escrita à
mão, dentro do próprio script — número a número, não copiado de outro
documento. Onde os dois caminhos batem certo há confirmação cruzada por dois
caminhos independentes; onde uma função cobre um procedimento com mais
passos do que uma fórmula fechada consegue reproduzir à mão (encurvadura de
colunas, diagramas de interação N-M completos, etc.), isso fica assinalado
no próprio documento — não escondido nem forçado a bater certo.

Cada `validation_*.py` gera o `.md` correspondente ao correr. Os `.md` são
Markdown simples (tabelas, sem HTML) para poderem ser exportados para Word
(por exemplo com Pandoc) sem reformatação.

## Como correr

Requer o `eurocodepy` instalado a partir do código-fonte real do
repositório (não a versão publicada no PyPI — ver nota nos scripts
individuais quando a API diverge).

```
cd eurocodepy
python validation/validation_actions.py
python validation/validation_rc_concrete.py
python validation/validation_steel.py
python validation/validation_timber.py
python validation/validation_geotechnical.py
python validation/validation_seismic.py
```

## Lista de ficheiros

| Eurocódigo | Script | Documento | Casos | Estado |
|---|---|---|---|---|
| EN 1990 / EN 1991 (ações) | `validation_actions.py` | `validation_actions.md` | 11 | 11/11 ✓ |
| EN 1992-1-1 (betão armado) | `validation_rc_concrete.py` | `validation_rc_concrete.md` | 15 | 15/15 ✓ |
| EN 1993-1-1 (aço) | `validation_steel.py` | `validation_steel.md` | 13 | 13/13 ✓ |
| EN 1995-1-1 (madeira) | `validation_timber.py` | `validation_timber.md` | 19 | 19/19 ✓ |
| EN 1997-1 (geotecnia) | `validation_geotechnical.py` | `validation_geotechnical.md` | 10 | 10/10 ✓ |
| EN 1998-1 (ação sísmica) | `validation_seismic.py` | `validation_seismic.md` | 11 | 11/11 ✓ |
| **Total** | | | **79** | **79/79 ✓** |

## O que cada ficheiro cobre

**EC1 — ações** (`validation_actions.py`): pressão dinâmica de pico do vento
q_p(z) (EN 1991-1-4 §4, terreno plano, categoria II), tensões principais 3D
(decomposição espectral, usada nas verificações de placas/cascas), uma
combinação ULS simples (EN 1990 Eq. 6.10: 1.35G+1.5Q). O módulo
`eurocodepy.ec1.snow` está vazio no código atual — confirmado por
introspeção, não por suposição — e fica registado como sem cobertura, não
omitido.

**EC2 — betão armado** (`validation_rc_concrete.py`): flexão simples (método
K / bloco retangular, `calc_asl`), esforço transverso sem armadura
(`calc_vrdc`, mínimo v_min e V_Rd,c), esforço transverso com armadura
(modelo de treliça §6.2.3, `calc_asws`/`calc_vrdmax`), torção pura (analogia
de parede fina fechada §6.3, `calc_torsion` — reutiliza e reproduz à mão o
caso já testado em `tests/test_torsion.py` do próprio repositório). Fora do
âmbito desta ronda (verificações simples): punçoamento, colunas com
diagrama N-M completo, interação corte+torção combinada — ficam para uma
extensão futura com casos combinados.

**EC3 — aço** (`validation_steel.py`): fator de material ε, resistência
axial N_pl,Rd, resistência à flexão M_pl,Rd (Classe 1/2), resistência ao
esforço transverso V_pl,Rd, resistência à torção pura T_Rd, carga crítica de
Euler N_cr e fator de redução χ (encurvadura por compressão centrada,
perfil IPE300/S275 — mesmas propriedades de secção usadas em
`xdfem2d/validation/design_cases_manual.md`). O procedimento completo
`eurocode3_member_check` (§6.3.3, com interação biaxial N-M-buckling) fica
fora do âmbito — só os seus blocos isolados (`calc_Ncr`, `reduction_chi`)
são validados aqui.

**EC5 — madeira** (`validation_timber.py`): valores de cálculo
(k_mod, γ_M, f_t0d/f_c0d/f_md/f_vd), tração axial pura, compressão axial
pura (sem encurvadura), flexão pura, esforço transverso puro
(τ=1.5V/(b·h)), torção pura — reutiliza a secção C24 0.10×0.20 m de
`xdfem2d/validation/design_cases_manual.md` (A7.1-A7.4). O caso de torção
(A7.5 nesse documento) tinha ficado sinalizado como não verificável por
fórmula simples de manual — aqui reproduz-se com sucesso porque a fórmula à
mão usa exatamente o α(h/b) e o k_shape que `check_shear_with_torsion` usa
internamente, lidos do código-fonte, não da norma pura (a norma remete o
coeficiente de forma de torção retangular para teoria da elasticidade,
Saint-Venant, não uma fórmula do texto do Eurocódigo em si).

**EC7 — geotecnia** (`validation_geotechnical.py`): coeficientes de impulso
de Rankine (K_a, K_p — muro vertical, terrapleno horizontal), coeficiente de
impulso em repouso (fórmula de Jáky, K0=(1−sinφ)·√OCR), capacidade de carga
de fundação superficial (EN 1997-1 Anexo D — N_q, N_c, N_γ e a fórmula
completa para uma sapata corrida sem coesão nem sobrecarga). O caso sísmico
pseudo-estático (`seismic_bearing_resistance`) e os coeficientes de Coulomb
/ EC7 completos (com atrito de muro e inclinação de terrapleno) ficam fora
do âmbito desta ronda de verificações simples.

**EC8 — ação sísmica** (`validation_seismic.py`): fator de correção de
amortecimento η, espetro elástico Se(T) e espetro de cálculo Sd(T), nas
quatro ramificações cada (T<T_B, T_B≤T<T_C, T_C≤T<T_D, T≥T_D) — mesma
estrutura de referência independente já usada em `tests/test_elastic_
spectrum.py` do próprio repositório do eurocodepy.

## O que fica assinalado, não escondido

Sempre que uma função testada envolve mais passos do que uma fórmula
fechada consegue reproduzir à mão dentro do próprio script de validação
(colunas com encurvadura completa em EC2/EC3, diagramas de interação N-M
biaxiais, punçoamento com geometria de perímetro variável, o modelo
combinado corte+torção em madeira antes de se ler o código-fonte), isso é
dito explicitamente no `.md` correspondente, com a razão — nunca omitido em
silêncio nem forçado a um número que não foi de facto verificado por dois
caminhos independentes.

## Extensões possíveis (fora do âmbito desta ronda)

- EC2: punçoamento, colunas (método da curvatura nominal), interação
  corte+torção combinada, secções em T/circulares.
- EC3: verificação completa de barra (`eurocode3_member_check`, §6.3.3),
  classificação de secção completa (Classe 1-4), encurvadura lateral (LTB).
- EC5: verificação combinada N+M+encurvadura (`eurocode5_section_check`
  completo), CLT/LVL/Glulam.
- EC7: capacidade de carga sísmica pseudo-estática, coeficientes de Coulomb
  e EC7 completos com atrito de muro δ≠0 e terrapleno inclinado.
- EC8: espetro vertical, deslocamento entre pisos (drift), fatores de
  comportamento q por sistema estrutural.
