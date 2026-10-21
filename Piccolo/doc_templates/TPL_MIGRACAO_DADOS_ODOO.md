# TPL_MIGRACAO_DADOS_ODOO.md

> Template executável: **mover dados entre bases de dados Odoo** com segurança e de forma
> reproduzível — promoção de `brodoo_dev` para `client_test`, migração Studio → standard,
> correcção de campos em massa, reposição a partir de uma fonte.
> Fonte de verdade deste template: artigo Odoo do workspace `pg_doc_templates`.
> Se for editado localmente, **republicar no Odoo** para não perder no próximo pull.

## Finalidade

Uma migração de dados falha de duas maneiras: perde registos, ou escreve no sítio errado.
Este template existe para que nenhuma das duas aconteça por falta de método.

O que aqui está foi extraído de uma migração real e validada — o WP1 do SmartEnergy
(Studio → standard, 379 empresas, 299 condomínios, 714 pessoas, 448 anexos, reconciliação
a 100%, 0 divergências de NIF). Não é teoria.

## Quando usar

Disparar quando o utilizador pedir, por exemplo: "migrar os dados para a base de testes",
"promover o desenvolvimento para validação", "passar isto para a base do cliente",
"replicar a configuração na base de validação", "migrar os campos Studio para standard".

**Qualquer escrita de dados no Odoo de um cliente cai neste template**, mesmo quando é
apresentada como pequena ("é só corrigir um campo em massa").

---

## Passo 0 — Classificar a migração [GATE]

Antes de tocar em nada, responder a esta pergunta, porque decide o esforço:

> **O modelo de destino é o mesmo do de origem?**

| Resposta | Tipo | Exige ledger campo-a-campo? |
|---|---|---|
| Sim — mesma estrutura nas duas pontas | **Promoção** (ex.: `brodoo_dev` → `client_test`) | Não |
| Não — o destino tem estrutura diferente | **Remodelação** (ex.: Studio `x_*` → `res.partner`) | **Sim, obrigatório** |

A **reconciliação de contagens é obrigatória nos dois casos**. O que varia é o ledger: só
faz sentido quando há decisões de destino a tomar campo a campo. Numa promoção, onde o
modelo é igual nas duas pontas, não há decisões — há verificação.

Se a classificação não for evidente, **parar e perguntar ao utilizador**. Classificar mal
para baixo é o erro caro: começa-se a escrever sem ter decidido onde é que cada dado vai.

## Passo 1 — Pré-condições (verificar, não assumir)

1. **Código no destino primeiro.** Se a migração depende de campos `pg_*` de um módulo do
   projeto, esse módulo tem de estar **deployado por git na branch do destino e instalado**,
   na versão que traz esses campos. Registar a versão mínima exigida e **verificá-la em
   execução** — não confiar em que "já deve estar".
   Uma migração não faz deploy de código. Só migra dados.
2. **Fonte intacta e legível.** Confirmar que a origem continua acessível e que nada foi
   apagado. A origem é a rede de segurança: se a migração correr mal, é de lá que se repõe.
3. **Ambiente confirmado** — versão e edição do Odoo, e a série do `vendor/odoo_src` a
   corresponder, para o comportamento do standard ser o que se lê no código.

Se alguma pré-condição falhar, **parar e reportar**. Não migrar "à sorte" para ver se dá.

## Passo 2 — Ligação e guarda (obrigatório)

Toda a comunicação com o Odoo passa por `.pg_framework/scripts/pg_odoo_migration_guard.py`.
Nenhum script fala com o Odoo directamente — é o ponto único de passagem, e é isso que faz
com que o que ele proíbe fique proibido para todos.

As credenciais do Odoo-alvo vêm de `pg.odoo.connection`, pelo canal Brodoo, **em memória**.
Nada é escrito para disco:

```python
import sys; sys.path.insert(0, r".pg_framework\scripts")
from pg_odoo_migration_guard import resolver_alvo_por_projeto, Guard

alvo = resolver_alvo_por_projeto("<project_key>", "client_test")
o = Guard(alvo, confirmed=args.confirm, allow_prod=args.allow_prod)

o.kw("res.partner", "search_read", [[["is_company", "=", True]]], {"fields": ["name"]})
o.kw("res.partner", "write", [ids, valores], allow_write=True)   # escrita: consentimento por chamada
```

Verificar a ligação antes de começar (não escreve nada):

```
python .pg_framework\scripts\pg_odoo_migration_guard.py --project-key <chave> --purpose client_test
```

**Não criar ficheiros de ligação com a API key.** A política de credenciais do
`AGENTS_SHARED.md` é explícita: as credenciais do cliente ficam centralizadas no Odoo PG,
nunca em ficheiros nos repositórios de projeto. Se a ligação ainda não existir, criá-la em
**Brodoo > Repositório > Ligações Odoo do cliente** — não contornar com um ficheiro local.

Só quando a ligação não estiver registada e não puder ser criada é que existe o caminho
alternativo `resolver_alvo("conn_alvo.json")`, com a finalidade declarada dentro do
ficheiro. Nunca versionar esse ficheiro.

| Finalidade | Escrita |
|---|---|
| `brodoo_dev` | permitida com `--confirm` |
| `client_test` | permitida com `--confirm` |
| `production` | bloqueada; exige `--confirm` **e** `--allow-prod` |

**Não recriar guardas locais.** Se faltar um método na lista branca, acrescentá-lo ao guard
partilhado — nunca contornar. Um método não classificado é bloqueado de propósito: pode
escrever sem que se saiba.

## Passo 3 — Ledger campo-a-campo *(só em remodelação)*

Quando o modelo de destino difere do de origem, produzir `docs/<WP>_LEDGER_MIGRACAO.md`
**antes de escrever dados**. É o registo autoritário do destino de cada dado, e serve três
fins: garantir que nada essencial se perde, tornar visíveis as decisões, e permitir
perceber a migração meses depois.

Uma linha por campo de origem:

| Campo origem | % preenchido | Disposição | Destino |
|---|---:|---|---|

Taxonomia de disposição (usar exactamente estes termos):

- `standard` — campo nativo do Odoo (preferir sempre; reutilizar `ref`, `company_name`… antes de criar `pg_`)
- `pg_` — campo do módulo do projeto, quando o standard não tem equivalente
- `sub-objeto` — vira registo próprio (endereço-filho, conta bancária)
- `tag` — vira `category_id` ou etiqueta
- `relação` — vira `parent_id` / m2o / o2m
- `anexo` / `chatter` — `ir.attachment` / `mail.message`
- `diferido` — migra num work package posterior; **fica preservado na origem** (não é perda, é faseamento)
- `derivado` — calculável a partir de outros dados; não migra
- `técnico` — ruído de implementação; não migra
- `descartar` — baixo valor; **exige validação do cliente antes de assumir**

Regras do ledger:
- a **percentagem de preenchimento na origem** é obrigatória — é o que distingue um campo
  relevante de um campo que ninguém usou;
- `descartar` nunca é decisão só do agente: lista-se e **valida-se com o cliente**;
- achados de comportamento do Odoo citam o **source** (`vendor/odoo_src/...`, ficheiro e
  linha). Inferência apresentada como facto é o que faz perder dados;
- o ledger tem **histórico de versões** no fim: cada revisão diz o que mudou e porquê.

## Passo 4 — Sequência idempotente

A migração tem de poder correr **várias vezes com o mesmo resultado**. Sem isto, um erro a
meio deixa a base num estado que ninguém sabe descrever.

Como se consegue: marcar tudo o que a migração cria com um **namespace próprio** (ex.:
`ir.model.data` com `module='x_mig'`, ou `description` nos anexos) e começar a sequência
por um `reset` que remove o que a passagem anterior criou.

Ordem típica, a adaptar:

```
reset → dados estruturais → campos derivados → relações → correcções a partir da fonte
      → chatter → anexos → camada de apresentação → reconciliação
```

Duas regras que não se negociam:

- **Nunca apagar a camada anterior.** Vistas e menus Studio, campos `x_*`: **desactivar**
  (`active=False`), que é reversível. A eliminação definitiva é uma fase posterior de
  decomissionamento, depois de tudo validado e estável.
- **Desactivar por nome, nunca por id.** Os ids não são portáveis entre bases de dados; o
  script tem de funcionar igual em qualquer alvo.

## Passo 5 — Reconciliação (obrigatória, sempre)

Uma migração sem reconciliação **não está terminada**. No fim, e por entidade:

1. **contagem origem = contagem destino** — reportar os dois números, não "OK";
2. **verificação de integridade** dos campos sensíveis, comparando com a fonte. Contar
   divergências e reportar o número, que deve ser zero;
3. **inspecção de um caso real ponta a ponta** — escolher um registo e seguir a cadeia de
   relações até ao fim. As contagens não apanham relações trocadas.

Reportar num quadro, não em prosa:

| Entidade | Origem | Destino | Divergências |
|---|---:|---:|---:|

Se houver divergências, **não declarar a migração feita**. Documentar, decidir e repetir —
a sequência é idempotente precisamente para isto.

Cuidado com um efeito que já morde: campos que o Odoo **sincroniza** entre registos ligados
(o `vat` propaga-se por `parent_id` em três direcções — ver
`vendor/odoo_src/community/odoo/addons/base/models/res_partner.py`, `_fields_sync`). Migrar
o campo certo não garante que ele fique com o valor certo. Verificar contra a fonte.

## Passo 6 — Promoção: dry-run, validação, produção

```
python cutover.py conn_<alvo>.json --dry-run                 # verifica pré-condições, não escreve
python cutover.py conn_<alvo>.json --confirm                 # executa (brodoo_dev / client_test)
python cutover.py conn_<alvo>.json --confirm --allow-prod    # produção, explícito
```

- **dry-run primeiro, sempre.** Nada é escrito sem `--confirm`.
- **produção não é mais uma flag.** Antes de `--allow-prod`: dry-run revisto, reconciliação
  aceita em `client_test`, e **decisão registada** — quem aprovou, quando, sobre que
  contagens. Registar no `PG_CONTEXT.md`.
- O log de todas as chamadas fica em `.pg/migration/api_calls.log.jsonl`. É o que permite
  reconstruir o que aconteceu quando alguém perguntar.

## Regras invioláveis

- `vendor/odoo_src` é `read-only`.
- A origem **nunca** é apagada enquanto o destino não estiver validado.
- Camadas anteriores desactivam-se, não se eliminam.
- Nenhuma escrita fora do guard.
- Credenciais só no ficheiro de ligação, fora do controlo de versões.
- Contagens reportadas como números. "Correu bem" não é reconciliação.

## Checklist antes de declarar a migração feita (falha = não está feita)

- [ ] Migração classificada (promoção ou remodelação) e o ledger produzido quando exigido.
- [ ] Módulo do projeto deployado e instalado no destino, na versão mínima, **verificada**.
- [ ] Todas as escritas passaram pelo guard; `purpose` correcto no ficheiro de ligação.
- [ ] Dry-run corrido e revisto antes da execução.
- [ ] Sequência idempotente (corrida duas vezes, mesmo resultado).
- [ ] Camada anterior desactivada, não apagada.
- [ ] Reconciliação: contagens origem = destino, por entidade, reportadas como números.
- [ ] Integridade dos campos sensíveis verificada contra a fonte, com divergências a zero.
- [ ] Um caso real seguido ponta a ponta.
- [ ] Decisões de `descartar` validadas com o cliente.
- [ ] `PG_CONTEXT.md` actualizado com o resultado e as decisões.

## Resposta final ao utilizador

- Indicar o alvo (finalidade e base de dados) e o que foi migrado.
- Apresentar o quadro de reconciliação com os números.
- Listar o que ficou `PONTO POR VALIDAR` e as decisões pendentes do cliente.
- Indicar o caminho do log e do ledger, quando exista.
- Perguntar se deve seguir para o alvo seguinte (`client_test` → produção).
