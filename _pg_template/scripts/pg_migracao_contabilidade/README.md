# pg_migracao_contabilidade

Motor do método **TPL_MIGRACAO_CONTABILIDADE_MEIO_ANO** (`doc_templates`): passar a contabilidade
de um cliente para o Odoo a meio do ano, importando o SAF-T de contabilidade com a Exo PT+,
consolidando o plano de contas e verificando tudo contra o SAF-T.

Extraído da migração da Reckon.AI (Odoo 19, Exo PT+, janeiro a julho de 2026, passagem a
produção a 06/10/2026). A configuração desse caso está no repositório `reckon.ai`, em
`docs/plano_contas/migracao_contabilidade.json`, e serve de exemplo.

| Ficheiro | Para quê |
|---|---|
| `motor.py` | cada passo do método, um subcomando; escreve só com `--confirm` (e `--allow-prod` em produção) |
| `verificar.py` | verificação contra o SAF-T (só leitura) |
| `correr.py` | a sequência completa, no ensaio e no dia da passagem; pára ao primeiro erro |

```
python .pg_framework\scripts\pg_migracao_contabilidade\correr.py <config.json> <ligação>               # ensaio
python .pg_framework\scripts\pg_migracao_contabilidade\correr.py <config.json> producao --producao     # passagem
python .pg_framework\scripts\pg_migracao_contabilidade\motor.py <config.json> <ligação> <passo> [--confirm]
python .pg_framework\scripts\pg_migracao_contabilidade\verificar.py <config.json> <ligação>
```

`<ligação>` é um ficheiro de ligação local (bases de ensaio; fora do repositório) ou `producao`
(canal do projeto, sem chave em disco). O diário de cada execução fica na pasta de dados do
projeto: `diario_ensaio.md` nos ensaios, `diario_producao.md` em produção.

## Configuração do projeto (JSON)

| Chave | Obrigatória | O quê |
|---|---|---|
| `project_key` | sim | projeto no Brodoo (canal de produção) |
| `empresa` | sim | id da empresa do cliente no Odoo |
| `nome_importacao` | sim | nome da importação SAF-T da Exo |
| `saft` | sim | ficheiro SAF-T original (nunca uma versão convertida) |
| `pasta` | sim | pasta dos dados do cliente (fora do git, ver `.git/info/exclude`) |
| `data_abertura`, `data_corte` | sim | data do lançamento de abertura (31/12 do ano anterior) e último dia do histórico |
| `ref_abertura` | sim | referência do lançamento de abertura |
| `periodos_resumo` | sim | períodos do resumo das grelhas: `[["T1", "início", "fim"], …]` |
| `diarios_apuramento` | não | códigos dos diários de apuramento do SAF-T (ficam fora das grelhas e dos impostos) |
| `prefixo_outros_devedores_credores` | não | defeito `278` |
| `contas_diferimentos_por_cliente` | não | prefixos (ex.: `282`, `2721`) para a contagem de linhas sem cliente |
| `ficheiros` | sim | tabelas do projeto, relativas a `pasta` (abaixo) |
| `nomes_finais_excel` | não | `{ficheiro, folha, coluna}`: designações finais numa coluna "`<código> <nome> [(nova\|renomear)]`"; em alternativa, a tabela `nomes_finais` |
| `nomes_contas_novas` | não | designação de contas criadas pela reclassificação, por código |
| `impostos_por_conta` | não | imposto escolhido pela contabilidade para a base de certas contas |
| `natureza` | sim | `{padrao, abertura_e_resultado, conta_resultado}`: natureza da alteração no capital próprio (ex.: `d5`, `a7`, `818`) |
| `retencoes` | não | `{prefixo, contas_modelo10}`: só as retenções a crédito destas contas levam parceiro |
| `config_fiscal` | não | `{iva_a_pagar, iva_a_recuperar, retencoes_por_rendimento}` |
| `esperado` | não | `{retencoes_modelo10}`: número que o `correr.py` exige |
| `preparar` | não | comandos do projeto que geram as tabelas (`script.py\|arg\|arg`), corridos antes de importar |

## Tabelas do projeto (`ficheiros`)

Os preparadores de cada projeto leem os ficheiros do cliente (o Excel do plano, a taxonomia em
PDF) e produzem estas tabelas, que são o contrato com o motor. CSV com `;` e UTF-8.

| Chave | Obrigatória | Conteúdo |
|---|---|---|
| `plano` | sim | Excel com as folhas `Tabela` (conta SAF-T, …, conta final), `Esperado` (conta final, saldo à data de corte), `Recodificar` (de, para, nome), `Juntar` (final, fonte) e `Reclassificar` (conta certificada, para, nome) |
| `grelhas` | sim | `subconta;…;grelhas` (grelhas da Exo separadas por `\|`) |
| `abertura` | sim | `conta;conta_saft;parceiro_nif;parceiro_nome;debito;credito` |
| `contas_certificadas` | sim | JSON com as contas do plano certificado (`[{"code": …}]`), lido de produção antes da importação |
| `parceiros_por_subconta` | não | `subconta;…;movimentos;…;parceiro_confirmado_nif`: cliente das subcontas de diferimentos |
| `parceiros_em_falta` | não | `nome;nif;subconta_saft`: entidades que o SAF-T não identifica |
| `correcoes_nif` | não | `nome;nif_atual;nif_novo`: NIF errados em fichas que já existiam |
| `nomes_finais` | não | `codigo;nome;renomear` |
| `config_extra` | não | JSON `{impostos, posicoes_fiscais}` criados pelo cliente numa base de testes |
| `linhas_base_testes` | não | JSON das linhas da base de testes do cliente, para aproveitar parceiros atribuídos à mão |
| `fichas_contabilidade` | não | Excel da contabilidade com fichas duplicadas e saldo total esperado (folha `Fichas duplicadas`) |

## Regras que o motor garante

- Toda a escrita em linhas com impostos passa `skip_invoice_sync`: sem isso o Odoo recalcula o IVA.
- O bloqueio desce para a véspera da abertura para lançar e fica na data de corte no fim.
- Fusão de fichas: fica a ficha com faturas de cliente, senão a que já existia, senão a que tem mais movimentos.
- A verificação compara com o SAF-T, não com o Odoo.

O que fica fora da sequência (módulos da Exo, utilizador da contabilidade, código da Exo, séries,
bancos) está no template, no Passo 8 e no Passo 9.
