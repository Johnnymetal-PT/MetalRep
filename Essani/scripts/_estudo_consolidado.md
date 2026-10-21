# Estudo de dados — Backup (10/05 18:07) vs Plataforma (main atual)

> Read-only. Nenhuma alteração feita às bases de dados.
> Backup = BD de origem restaurada a 2026-05-10 18:07 (`essani-test-32696464`).
> Plataforma = produção main (`parametroglobaladmin-essani-main-24829872`).
> Gerado em 2026-05-27.

## 1. Catálogo e dados visíveis — ALINHADOS
| Métrica (produtos ativos) | Backup | Plataforma | Veredicto |
|---|---|---|---|
| Templates sale_ok | 575 | 575 | idêntico |
| Nomes únicos / em falta / a mais | 548 / – / – | 548 / 0 / 0 | idêntico |
| Publicados | 378 | 378 | ≈ (4 diferem) |
| hide_on_website=True (variantes) | 349 | 349 | idêntico, 0 diffs |
| Imagens nível template (ativos) | 805 | 805 | idêntico |
| Imagens nível variante (ativos) | 775 | 775 | idêntico |
| Documentos nível template (ativos) | 455 | 453 | ≈ (−2) |

O "quase dobro" de imagens/documentos no total da Plataforma é **resíduo de produtos arquivados**
(574 templates + 4801 variantes arquivados das promoções anteriores), invisível no website.
Documentos ao nível da variante não medidos (API recusa leitura de ir.attachment, Fault 4).

## 2. Referências — Plataforma está MELHOR (a manter)
| | Backup | Plataforma | Δ |
|---|---|---|---|
| Templates com referência | 254 | 333 | +79 |
| Variantes com referência | 951 | 1449 | +498 |

Reflete o trabalho da Ana + a recuperação de deltas, posterior ao backup.
Uma reposição cega do backup apagaria estas referências.

## 3. Variantes — divergência de combinações (decisão de negócio)
Variantes ativas: backup 4794 → Plataforma 5068 (+274).

### 505 só na Plataforma (extra)
- 33 (6%) com referência; 472 (94%) **sem referência = ruído de geração automática**.
- Top: LED Aureola 84, LED ProLine BX60 84, Tomada CLICK 71, Relé 35, Tomada DESKA 33.

### 112 só no backup (em falta na Plataforma)
- 26 (23%) com referência; todas visíveis no backup (0 escondidas).
- Top: Fita LED eFlex CX120 60, LED ProLine BX120 24, BX60 8.

### Padrão (FACTO): combinações DIFERENTES, não perda aleatória
~15 templates têm conjuntos de variantes divergentes (mesma família, valores de atributo
diferentes). Exemplos:
- LED Spot30: Plataforma V2 (2700/3000/4000/6000) vs backup V3 (idem)
- LED Évora LV: Plataforma 12V V1 vs backup 24V MW2
- Sensor Toque S3: Plataforma V1/V2/V6 vs backup V4
- Interruptor S11: Plataforma 60-F1/F3 vs backup 120-V1-F1

### 33 extra COM referência (na Plataforma, ausentes do backup)
Conector Distribuidor ProLineM3HV3P: EAFT15.3.V3.F1
Fita LED eFlex CX120: EFE6.12202.2100-50, EFE6.12202.6000-50
Interruptor S11: ES11.60-F1, ES11.60-F3
LED Aureola: ELD15-09-F1-V1-30, -V2-30, -V3-30, -V4-30, -V5-30, -X1-30, F8-V5-30, F8-X1-30
LED La Belle: EF30.V1-F1-4000, -F2-4000, -F3-4000
LED Mira: EF17.V1-F8-3000, -F8-4000
LED Spot30: EF8.V2-2700, -3000, -4000, -6000
LED T Spot UNO S: TR2B1TC92740-F1
LED Évora LV: EF1.12-V1-2100, -2700, -3000, -4000, -6000
Sensor Toque S15: ES15.36-F2
Sensor Toque S3: ES3.60-V1-F2, ES3.60-V2-F2, ES3.V6.F2
Sensor Toque S3 DUO: ES3.60-V3-F2

### 26 em falta COM referência (no backup, ausentes da Plataforma)
Interruptor S11: ES11.120-V1-F1
LED Aureola: ELD15-09-F1-X6-30, ELD15-09-F8-X6-30
LED La Belle: EF30.V2.F1.40
LED Mira: EF17.V1-F1-3000
LED ProLine BX60: EFP1.12651.2700-05/-25, .3000-05/-25, .4000-05/-25, .6000-05/-25 (8)
LED ProLine DX120 X2 MW2: EFP6.12651.MW2-05, -25
LED Spot30: EF8.V3-2700, -3000, -4000, -6000
LED T Spot UNO S: TX2W2DL94024-F1
LED Évora LV: EF1.24-V1-MW2
Sensor Toque S15: ES15.1G24
Sensor Toque S3: ES3.60-V4-F2, ES3.60-V4-F4
Sensor Toque S3 DUO: ES3.60-V5-F2, ES3.60-V5-F4

## 4. Categorias de website
Backup 65 vs Plataforma 117. 10 grupos de nome duplicado na Plataforma
(ex.: 'ACESSÓRIOS' 4x, 'Acessórios' 4x, '12 V DC' 2x). O backup também tem 11
grupos repetidos — parte da duplicação vem da origem.

## 5. Conclusões
- Catálogo, imagens e visibilidade ALINHADOS nos produtos ativos.
- Plataforma tem MAIS referências (trabalho posterior) — manter.
- Diferença de variantes = combinações de atributos divergentes em ~15 templates
  (provável: Plataforma reposta de origem ~13/05 vs backup de 10/05). Decisão de
  qual gama é a correta = negócio (Ana).
- Limpezas candidatas: 472 variantes sem referência (ruído), categorias duplicadas,
  produtos arquivados residuais.

## Causa provável (INFERÊNCIA, a validar)
A Plataforma foi reposta a partir do estado da origem por volta de 13/05;
o backup é de 10/05 18:07. As divergências de variantes/atributos refletem
edições entre 10/05 e 13/05, mais eventuais edições diretas na Plataforma.
