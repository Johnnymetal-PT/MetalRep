# PG_007_ODOO_ENV_COLLECTION_CONTRACT

## Metadados

| Campo | Valor |
|---|---|
| Item de backlog | `PG-007` (a registar em `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`) |
| Tipo de documento | Contrato arquitetural (discovery; sem implementação) |
| Estado | `D3 FECHADA E F1 IMPLEMENTADO EM 2026-08-11; D1 E D2 EM ABERTO (BLOQUEIAM F2)` |
| Autor | Claude Code (Opus 5) — sessão de diagnóstico 2026-08-10 |
| Origem | Incidente observado no Odoo da Parâmetro Global em 2026-08-10 (filtro "Employees" incompleto), que expôs o defeito do espelho M1 |
| Dependências | Nenhuma bloqueante; independente de `PG-005` (namespacing), mas o schema respeita os paths namespaced já em produção |
| Próximo passo | Deploy do addon no Odoo PG → republicar os 13 espelhos → fechar D1 e D2 para abrir F2 |

---

## 1. Objetivo e enquadramento

O `odoo_env.json` (marco M1 do espelho) é a **fonte de verdade nº 6** do `templates/AGENTS_SHARED.md` e o árbitro explícito do passo 1 (standard **já instalado** no projeto) contra o passo 2 (standard adicional) da ordem obrigatória de decisão.

Verificou-se em 2026-08-10 que o ficheiro publicado nos repositórios de projeto **não contém o inventário do Odoo do cliente**: contém o inventário do Odoo da Parâmetro Global, etiquetado com os dados do projeto do cliente.

O objetivo deste contrato é fixar como é que o inventário do ambiente do cliente passa a ser recolhido, persistido, publicado e validado, de forma a que:
- o artefacto diga sempre **qual base** inventariou e **quando**;
- a ausência de inventário seja um estado explícito e não silenciosamente confundida com "nada instalado";
- exista um único caminho de escrita para o repositório, sem escritas concorrentes ao mesmo ficheiro.

**Restrições do contrato:**
- Não implementar código nesta fase.
- Não quebrar os consumidores actuais do espelho (agentes, `pg_preflight_context.ps1`).
- Preservar a estabilidade do `payload_hash` (regressão AUD-04): builds sucessivos sem alteração de conteúdo não podem gerar commits repetidos.

---

## 2. Análise do estado actual

### 2.1 Factos observados

`FACTO OBSERVADO`: o inventário é lido da base onde o addon corre. `pg_brodoo/services/project_mirror_payload_builder.py:697-700` — `_installed_modules()` faz `self.env['ir.module.module'].sudo().search([('state', '=', 'installed')])`. `self.env` é o Odoo da Parâmetro Global, onde o `pg_brodoo` está instalado.

`FACTO OBSERVADO`: o `build_odoo_env_payload()` (mesmo ficheiro, linha 712) combina esse inventário local com `project.pg_odoo_version`, `project.pg_odoo_edition` e `project.pg_odoo_environment`, que são campos declarados à mão no projeto. O ficheiro resultante mistura, sem o distinguir, dados do cliente (versão/edição/ambiente) com dados da base da Parâmetro Global (módulos).

`FACTO OBSERVADO`: o comportamento está consagrado em teste. `pg_brodoo/tests/test_m1m3_env_deliverables.py:27` afirma `self.assertIn('pg_brodoo', names)` — o teste exige que o inventário contenha o módulo do próprio Brodoo, isto é, que seja o inventário da base local. A suite passa.

`FACTO OBSERVADO`: não existe caminho para consultar o Odoo do cliente dentro do addon. O modelo `pg.odoo.connection` (`pg_brodoo/models/pg_odoo_connection.py`) guarda `base_url`, `database`, `login` e `api_key`, mas nenhum serviço do addon as usa; o único `requests` é o do GitHub (`pg_brodoo/services/github_service.py:8`). Os campos `last_check_at` e `last_check_status` existem no modelo e na vista e **nunca são escritos** — não há teste de ligação.

`FACTO OBSERVADO`: quem consulta o Odoo do cliente é o lado do operador, por `scripts/pg_odoo_client_query.ps1`, com resolução do nome da base por `scripts/pg_odoo_resolve_db.ps1` (HTTP e, em fallback, SSH com a conta do operador).

`FACTO OBSERVADO`: o publisher é o único escritor do ficheiro e sobrescreve sempre. `pg_brodoo/services/github_service.py:360-390` — `upsert_repository_file()` faz `PUT` na API do GitHub com o `sha` **refrescado a cada tentativa**, desenhado para vencer escritas concorrentes ao mesmo artefacto. Qualquer conteúdo escrito localmente no repositório é substituído no sync seguinte, sem conflito e sem aviso.

`FACTO OBSERVADO`: a validação actual só verifica presença. `scripts/pg_preflight_context.ps1:179` procura um ficheiro chamado `odoo_env.json` e o aviso da linha 212 dispara apenas quando ele **falta**. Não há verificação de conteúdo, de origem nem de idade — um espelho com o inventário da base errada passa o preflight como válido.

`FACTO OBSERVADO`: a documentação da framework contradiz-se. `docs/PG_ODOO_CLIENT_CHANNELS_TEMPLATE_MAP.md:29,38-40` estabelece que os módulos instalados para a ordem de decisão vêm de `ir.module.module [state=installed]` **pelo canal `production`**; o `templates/AGENTS_SHARED.md` declara o `odoo_env.json` como fonte primária dos módulos realmente instalados.

`FACTO OBSERVADO`: dimensão do problema à data (12 repositórios com espelho publicado, snapshots entre 2026-07-10 e 2026-08-10): os 13 ficheiros `odoo_env.json` declaram 483–488 módulos e **100% dos nomes coincidem** com os módulos instalados no Odoo da Parâmetro Global, incluindo `pg_brodoo`, `pg_doc_templates` e `pg_project_budget_import`.

`FACTO OBSERVADO`: cobertura das ligações `production` (24 activas) contra os repositórios com espelho:
- com ligação: `GBUK`, `givachoice`, `HMD`, `jmmgroup`, `odoosh`, `SmartEnergy`, `Sofmovel`, `sofmovelsh` — 8;
- sem ligação: `besimple`, `ENIGMAF`, `Mercado-Abastecedor`, `Private-Label` — 4;
- ligações a redes privadas, inalcançáveis a partir do Odoo.sh: `http://192.168.10.4:8069` (GBUK), `http://192.168.1.12:8069` (HPRD);
- ligações com `database` vazio: Cartonagem São Tiago, FPV Vela (staging), HPRD.

`FACTO OBSERVADO`: `pg.odoo.connection` tem restrição de unicidade `unique(repository_id, purpose)` (`pg_brodoo/models/pg_odoo_connection.py:43-49`) — a ligação pertence ao **repositório**, não ao projeto. Existem repositórios com mais de um projeto: o `Sofmovel` tem dois espelhos (`odoo-sofmovel` e `odoo-sofmovel-migracao-para-odoo-sh-v19`) para a mesma base de produção.

### 2.2 Inferências

`INFERÊNCIA`: o M1 foi desenhado sob a premissa implícita de que o Odoo onde o `pg_brodoo` corre é o Odoo do projeto. A premissa seria verdadeira se o addon fosse instalado na base do cliente; corre na base da Parâmetro Global, e a premissa quebra sem produzir erro — apenas dados errados.

`INFERÊNCIA`: os canais `pg.odoo.connection` surgiram depois do M1 e do lado do operador (PowerShell), e o M1 nunca foi reconciliado com eles. Daí a contradição entre os dois documentos de contrato.

`INFERÊNCIA`: enquanto o `AGENTS_SHARED.md` mandar ler o espelho como fonte primária, qualquer análise consultiva na frota pode classificar como "standard já instalado" aquilo que exige instalar um módulo — exactamente o erro que a ordem obrigatória de decisão existe para evitar.

`INFERÊNCIA`: um publisher que corre no Odoo.sh da Parâmetro Global não alcança bases de cliente em rede privada. Não foi testado, mas os dois endereços `192.168.x.x` registados como `production` não são encaminháveis a partir da internet.

### 2.3 Pontos por validar

`PONTO POR VALIDAR`: existe alguma base de cliente com `pg_brodoo` instalado? Nesse subconjunto o M1 actual estaria correcto. Nada do observado sugere que exista.

`PONTO POR VALIDAR`: qual é a periodicidade útil do inventário do cliente? Determina o TTL de frescura (D5) e se vale a pena automatizar a recolha.

`PONTO POR VALIDAR`: os 4 repositórios sem ligação `production` vão passar a ter uma, ou o seu espelho fica permanentemente em estado `unavailable`?

---

## 3. Proposta recomendada — recolha do lado do operador, persistência no Odoo, publicação pelo publisher

### 3.1 Princípio

Três responsabilidades separadas, cada uma no lado que consegue cumpri-la:

| Responsabilidade | Onde | Porquê |
|---|---|---|
| **Recolher** o inventário da base do cliente | lado do operador/agente (`scripts/`) | é quem tem o canal `production` a funcionar, quem resolve o nome da base após rebuild e quem está dentro da rede quando o cliente é on-premise |
| **Persistir** o inventário recolhido | Odoo da Parâmetro Global (modelo novo) | o publisher tem de o poder ler no momento do sync, que é assíncrono em relação à recolha |
| **Publicar** no repositório | `pg_brodoo` (publisher actual) | é o único escritor do ficheiro; qualquer outro escritor é sobrescrito |

O `_installed_modules()` deixa de consultar `self.env` e passa a ler o inventário persistido. O publisher continua o único caminho de escrita para o repositório.

### 3.2 Fluxo alvo

```
operador/agente                    Odoo PG (pg_brodoo)                repositório do projeto
──────────────────                 ───────────────────                ──────────────────────
pg_collect_odoo_env.ps1
  -ProjectKey <key>
  -Purpose production
       │
       ├─ resolve a ligação (canal Brodoo)
       ├─ resolve a BD se necessário (pg_odoo_resolve_db.ps1)
       ├─ ir.module.module [state=installed]  ──► base do cliente
       │
       └─ write ──────────────────► pg.odoo.env.snapshot
                                     (por ligação, com collected_at)
                                            │
                                   sync do projeto (trigger/cron)
                                            │
                                   build_odoo_env_payload()
                                     lê o snapshot da ligação
                                     production do repositório
                                            │
                                            └─ upsert ──────────────► .pg/projects/<key>/project/odoo_env.json
                                                                        (schema 1.1, com collection block)
```

### 3.3 Modelo de persistência (`pg.odoo.env.snapshot`)

Um registo por **ligação** (não por projeto), porque a ligação é a base física e há repositórios com vários projetos sobre a mesma base:

| Campo | Tipo | Notas |
|---|---|---|
| `connection_id` | `many2one pg.odoo.connection` | obrigatório; `ondelete='cascade'` |
| `collected_at` | `datetime` | momento da recolha na base do cliente |
| `collected_by` | `many2one res.users` | quem comandou a recolha |
| `base_url` | `char` | copiado da ligação no momento da recolha (a ligação pode mudar depois) |
| `database` | `char` | idem; é o que identifica a build no Odoo.sh |
| `module_ids` | `one2many` | `name`, `shortdesc`, `installed_version`, `application`, `author` |
| `module_count` | `integer` | desnormalizado para leitura rápida |

Unicidade: um snapshot **corrente** por ligação. Histórico é opcional (ver D6).

### 3.4 Schema `odoo_env.json` — versão `1.1`

`ODOO_ENV_SCHEMA_VERSION` sobe de `1.0` para `1.1`. Bloco novo `collection`, que torna a origem e o estado legíveis por quem consome:

```json
{
  "schema_version": "1.1",
  "project": { "...": "inalterado" },
  "odoo_env": {
    "odoo_version": "19.0",
    "odoo_edition": "enterprise",
    "odoo_environment": "odoo_sh",
    "collection": {
      "status": "collected",
      "purpose": "production",
      "base_url": "https://cliente.odoo.com",
      "database": "cliente-main-12345678",
      "collected_at": "2026-08-10 09:00:00",
      "collected_by": "Bruno Pinheiro",
      "unavailable_reason": null
    },
    "installed_module_count": 118,
    "installed_modules": [ { "name": "sale", "...": "..." } ]
  },
  "source_metadata": { "...": "inalterado" }
}
```

**Valores de `collection.status`:**

| Estado | Significado | `installed_modules` |
|---|---|---|
| `collected` | inventário recolhido na base do cliente identificada em `collection` | lista real |
| `unavailable` | não foi possível recolher; `unavailable_reason` explica (`no_connection`, `unreachable`, `auth_failed`, `never_collected`) | `[]` |
| `stale` | recolhido mas fora do TTL (ver D5) | lista da última recolha, com `collected_at` no passado |

**Regra de leitura obrigatória (a acrescentar ao `AGENTS_SHARED.md`):** `status != collected` significa **`PONTO POR VALIDAR`** e nunca "nada instalado". Com `unavailable`, a ordem de decisão não pode ser fechada a partir do espelho; usar o canal `production` ou declarar a incerteza.

### 3.5 Alterações no `templates/AGENTS_SHARED.md`

A fonte de verdade nº 6 passa a ler-se: o `odoo_env.json` é o inventário do **Odoo do cliente**, válido apenas quando `collection.status = collected`; caso contrário, a fonte é o canal `production` (`pg_odoo_client_query.ps1`), como já estabelece o `PG_ODOO_CLIENT_CHANNELS_TEMPLATE_MAP.md`. Elimina-se a contradição entre os dois documentos.

### 3.6 Alterações no `scripts/pg_preflight_context.ps1`

O teste de presença passa a teste de **estado**: ler o `collection.status` e o `collected_at`, e emitir aviso quando `unavailable`, `stale` ou schema `1.0` (espelho antigo, origem desconhecida). Mantém-se aviso e não erro bloqueante, coerente com o tratamento dos restantes avisos.

---

## 4. Alternativas rejeitadas

### 4.1 O publisher consulta o cliente por RPC no momento do sync

**Descrição**: `_installed_modules()` recebe a ligação `production` e consulta a base do cliente por RPC durante o sync.

**Razões de rejeição:**
- `INCOMPATIBILIDADE ESTRUTURAL`: não alcança bases on-premise em rede privada — 2 das ligações `production` registadas são endereços `192.168.x.x`.
- `RISCO OPERACIONAL`: mete dependência de rede externa num serviço de publicação hoje puramente local, disparado por trigger/cron; uma base em rebuild ou offline passa a fazer falhar (ou degradar) o sync do projeto.
- `CUSTO`: obriga a duplicar dentro do addon a resolução do nome da base (hoje em `pg_odoo_resolve_db.ps1`, com fallback SSH que usa a conta do operador e não existe no servidor).
- Continua a não cobrir os 4 repositórios sem ligação `production`.

**Nota**: pode ser adoptada mais tarde como **optimização oportunista** para bases públicas alcançáveis, alimentando o mesmo `pg.odoo.env.snapshot`. Não é alternativa ao fluxo comandado; é um atalho para um subconjunto.

### 4.2 O operador escreve o ficheiro directamente no repositório

**Razão de rejeição:** `FACTO OBSERVADO` — o `upsert_repository_file()` sobrescreve sempre, com `sha` refrescado. O conteúdo escrito à mão desaparece no sync seguinte, silenciosamente. Dois escritores para o mesmo artefacto é o defeito, não a solução.

### 4.3 Manter o comportamento e documentá-lo

**Descrição**: aceitar que o M1 inventaria a base da Parâmetro Global e limitar-se a dizê-lo no contrato.

**Razão de rejeição:** o inventário da base da Parâmetro Global não tem nenhum uso consultivo — não informa nada sobre o cliente. O artefacto passaria a ocupar espaço no espelho e na janela de contexto dos agentes sem valor. Se não for para ser o inventário do cliente, o campo deve ser **removido** do M1, não documentado.

---

## 5. Tabela de trade-offs

| Dimensão | Recomendada (recolha comandada) | 4.1 (RPC no publisher) | 4.3 (manter e documentar) |
|---|---|---|---|
| **Cobertura da frota** | Total, incluindo on-premise | Parcial — falha rede privada e falta de ligação | N/A |
| **Fiabilidade do sync** | Inalterada (sem rede externa no publisher) | Degradada — nova dependência externa | Inalterada |
| **Custo de implementação** | Médio — modelo novo + script + schema | Alto — RPC, resolução de BD, tratamento de falhas | Nulo |
| **Automatismo** | Baixo — depende de comando humano | Alto quando funciona | N/A |
| **Frescura do dado** | Explícita, com TTL e estado | Sempre fresca quando alcança | N/A |
| **Risco de decisão errada** | Eliminado pelo estado explícito | Eliminado quando recolhe; reaparece se falhar em silêncio | Mantém-se se o contrato não for lido |
| **Valor consultivo** | Inventário real do cliente | Inventário real do cliente | Nenhum |

---

## 6. Plano faseado

### F0 — Discovery ✅ concluído em 2026-08-10

- [x] Causa-raiz identificada e provada no código (`_installed_modules()` + teste que a consagra)
- [x] Dimensão medida na frota (13 espelhos, 100% coincidentes com a base da Parâmetro Global)
- [x] Cobertura das ligações `production` levantada
- [x] Produção deste contrato
- [x] **GATE**: D3 fechada em 2026-08-11 (D1 e D2 seguem em aberto; bloqueiam apenas F2)

### F1 — Contrato e estado explícito ✅ implementado em 2026-08-11

Entregou o valor de protecção sem esperar pelo desenvolvimento do modelo:

- [x] `ODOO_ENV_SCHEMA_VERSION` → `1.1` com o bloco `collection`
- [x] `_installed_modules()` removido; enquanto não houver recolha o publisher emite `status: unavailable`, `unavailable_reason: never_collected` e `installed_modules: []` — deixa de publicar o inventário da base da Parâmetro Global
- [x] `validate_odoo_env_payload()` valida o `status` e exige a identificação da base em `collected`/`stale`
- [x] `collected_at` fora do `payload_hash` (D7)
- [x] `templates/AGENTS_SHARED.md`: fonte de verdade nº 6 reescrita, com tabela de leitura do `status` (secção 3.5)
- [x] `scripts/pg_preflight_context.ps1`: aviso por estado, não por presença — cobre `unavailable`, `stale`, JSON ilegível e schema `1.0` (secção 3.6)
- [x] testes: o que exigia `pg_brodoo` na lista passa a proibi-lo; mais três testes novos (estado `unavailable`, identificação da base recolhida, hash imune ao `collected_at`)
- [ ] **deploy do addon no Odoo PG** — sem isto o publisher em produção continua a emitir o payload antigo
- [ ] **republicar os 13 espelhos** para limpar o inventário errado já commitado nos repositórios

**Critérios de aceitação F1:**
- [x] a suite do `pg_brodoo` passa, com o teste invertido — validado contra baseline em worktree isolado: as mesmas 2 falhas e 10 erros pré-existentes antes e depois, sem regressão
- [x] `payload_hash` estável entre dois builds consecutivos sem recolha nova
- [x] o preflight avisa em projeto sem inventário recolhido — validado no `jmmgroup`, que reporta `unknown_origin` no espelho actual
- [ ] nenhum `odoo_env.json` da frota contém módulos da base da Parâmetro Global — depende do deploy e da republicação

> **Nota de sequência**: o aviso do preflight já protege a frota hoje, porque reconhece o schema `1.0` como origem desconhecida. A republicação corrige os ficheiros; o preflight impede que sejam usados enquanto isso não acontece.

### F2 — Recolha e persistência

- modelo `pg.odoo.env.snapshot` (secção 3.3) + segurança/vistas
- `scripts/pg_collect_odoo_env.ps1` — recolhe pelo canal `production` e persiste no Odoo pelo canal Brodoo
- `_installed_modules()` passa a ler o snapshot da ligação `production` do repositório do projeto
- TTL de frescura e cálculo de `stale` (D5)

**Critérios de aceitação F2:**
- um projeto com ligação `production` publica o inventário real do cliente, com `base_url` e `database` corretos no bloco `collection`
- um projeto sem ligação continua a publicar `unavailable` sem erro
- recolha idempotente: duas recolhas seguidas sem alteração na base do cliente não geram commit novo
- funciona num cliente on-premise em rede privada, com o operador dentro da rede

---

## 7. Decisões a fechar

### D1 — Propriedade do ficheiro `ABERTA` (bloqueante)

**Pergunta:** quem escreve o `odoo_env.json` no repositório?

**Recomendação:** o publisher continua o único escritor; o inventário recolhido é persistido no Odoo e lido no momento do sync. Fundamento factual: `upsert_repository_file()` sobrescreve sempre com `sha` refrescado, pelo que qualquer segundo escritor perde silenciosamente.

Condiciona: existência do modelo de persistência (D2) e todo o F2.

---

### D2 — Granularidade do inventário `ABERTA` (bloqueante)

**Pergunta:** o inventário pertence à ligação (`pg.odoo.connection`) ou ao projeto (`project.project`)?

**Recomendação:** à **ligação**. Fundamento factual: a ligação é única por `(repository_id, purpose)` e é a base física; o `Sofmovel` tem dois projetos sobre a mesma base de produção, e um snapshot por projeto duplicaria a recolha e divergiria assim que uma fosse mais recente.

Condiciona: a chave do modelo novo e a forma como o payload do projeto o referencia.

---

### D3 — Declaração de ausência e de origem `FECHADA` em 2026-08-11

**Pergunta:** como é que o artefacto distingue "não recolhido" de "nada instalado", e como declara qual base inventariou?

**Recomendação:** bloco `collection` com `status` (`collected` / `unavailable` / `stale`), `purpose`, `base_url`, `database`, `collected_at`, `collected_by` e `unavailable_reason`, com subida de schema para `1.1` (secção 3.4). Fundamento factual: hoje `installed_modules` é sempre uma lista preenchida, não há forma de expressar ausência, e o preflight só verifica presença do ficheiro — foi por isso que 13 espelhos errados passaram por válidos.

É a decisão com maior valor de protecção e é implementável **sem** D1 e D2 (é o F1).

**Decisão aprovada em 2026-08-11**: bloco `collection` com os três estados, conforme a recomendação. Implementada em F1 — ver `pg_brodoo/services/project_mirror_payload_builder.py` (`_odoo_env_collection`, `validate_odoo_env_payload`) e a secção "Regra de leitura do `odoo_env.json`" no `templates/AGENTS_SHARED.md`.

Nota de implementação: `D4` (lista vazia com `unavailable`, em vez de omitir o campo) e `D7` (`collected_at` fora do hash) ficaram resolvidas por arrasto, porque F1 não podia ser escrito sem as decidir. As restantes — `D5` TTL, `D6` histórico, `D8` autorização — continuam em aberto e só ganham efeito prático em F2.

---

### D4 — Destino do inventário local `ABERTA`

**Pergunta:** enquanto não houver recolha, o payload publica lista vazia com `unavailable`, ou o campo `installed_modules` é omitido?

**Recomendação:** lista vazia com `status: unavailable`. Omitir o campo obrigaria os consumidores a distinguir ausência de chave de ausência de dados, e o validador `validate_odoo_env_payload()` já exige `installed_modules` como lista (`project_mirror_payload_builder.py:886`).

---

### D5 — TTL de frescura `ABERTA`

**Pergunta:** a partir de quantos dias um inventário recolhido passa a `stale`, e o preflight avisa ou bloqueia?

**Recomendação:** 30 dias, **aviso** e nunca bloqueio, coerente com os restantes avisos do preflight. Depende de `PONTO POR VALIDAR`: periodicidade útil do inventário.

---

### D6 — Histórico de snapshots `ABERTA`

**Pergunta:** guardar apenas o snapshot corrente por ligação, ou o histórico das recolhas?

**Recomendação:** apenas o corrente em F2. O histórico da adoção do cliente (evolução de módulos instalados) é um caso de uso legítimo, mas separado, e não deve condicionar este contrato.

---

### D7 — Campos que entram no `payload_hash` `ABERTA`

**Pergunta:** `collected_at` entra no hash?

**Recomendação:** **não**. Só o conteúdo (lista de módulos e identificação da base) entra. Fundamento: o teste de estabilidade do hash (`test_odoo_env_hash_is_stable_across_builds`, regressão AUD-04) existe para impedir commits repetidos; um timestamp de recolha no hash produziria um commit por recolha mesmo sem alteração de conteúdo.

---

### D8 — Autorização da recolha `ABERTA`

**Pergunta:** a recolha em `production` é leitura livre para o agente, ou exige comando humano explícito?

**Recomendação:** manter o que o `AGENTS_SHARED.md` já impõe para os canais do cliente — acesso comandado por um elemento da equipa. A recolha é só leitura (`ir.module.module`), mas atravessa a fronteira para o Odoo do cliente e deve continuar a exigir intenção explícita.

---

## 8. Riscos e impactos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Espelhos errados permanecem em circulação após a correcção do código | Alta | Alto | F1 inclui republicação dos 13 espelhos; sem isso o defeito persiste no repositório |
| Agente lê espelho `schema_version 1.0` (sem bloco `collection`) e assume que é inventário do cliente | Média | Alto | Preflight avisa em schema `1.0`; `AGENTS_SHARED.md` instrui a tratar `1.0` como origem desconhecida |
| Recolha nunca é corrida e a frota fica em `unavailable` permanente | Média | Médio | Estado explícito é preferível a dado errado; o aviso do preflight cria pressão visível |
| Inventário recolhido envelhece e induz decisão desactualizada | Média | Médio | TTL e `status: stale` (D5) |
| Commits repetidos por instabilidade do hash | Baixa | Médio | D7 mantém o timestamp fora do hash; teste de estabilidade já existente cobre a regressão |
| Módulos de cliente com nomes iguais a módulos internos da Parâmetro Global dificultam a detecção do defeito | Baixa | Baixo | O bloco `collection` identifica a base; deixa de ser necessário inferir pela lista |

---

## 9. Referências consultadas

### Código analisado (`pg_brodoo`)
- `services/project_mirror_payload_builder.py:697-710` — `_installed_modules()` sobre `self.env`
- `services/project_mirror_payload_builder.py:712-734` — `build_odoo_env_payload()`
- `services/project_mirror_payload_builder.py:194-208` — `_source_metadata()` (origem fixa `odoo_parametro_global`)
- `services/project_mirror_payload_builder.py:882-888` — `validate_odoo_env_payload()`
- `services/github_repository_publisher.py:13,30` — paths `mirror_odoo_env` (legacy e namespaced)
- `services/github_service.py:360-390` — `upsert_repository_file()` com `sha` refrescado
- `models/pg_odoo_connection.py` — credenciais por `(repository_id, purpose)`; `last_check_*` nunca escritos
- `tests/test_m1m3_env_deliverables.py:19-36` — teste que consagra o inventário local e teste de estabilidade do hash

### Scripts analisados
- `scripts/pg_preflight_context.ps1:173-180,212,247` — validação por presença de ficheiro
- `scripts/pg_odoo_client_query.ps1` — canal `production` do cliente (2 saltos, via Brodoo)
- `scripts/pg_odoo_resolve_db.ps1` — resolução do nome da base (HTTP e fallback SSH)

### Contratos e documentação
- `templates/AGENTS_SHARED.md` — fonte de verdade nº 6 e canais do cliente
- `docs/PG_ODOO_CLIENT_CHANNELS_TEMPLATE_MAP.md:29,38-40` — módulos instalados pelo canal `production`
- `docs/PG_005_ARCHITECTURE_CONTRACT.md` — formato deste contrato e padrão de decisões fechadas
- `docs/PG_PROJECT_LEARNINGS.md` — `LEARNING 007` (o incidente que originou este contrato)

### Evidência de runtime (canal Brodoo, 2026-08-10)
- `ir.module.module [state=installed]` no Odoo da Parâmetro Global: 488 módulos
- 13 ficheiros `odoo_env.json` em repositórios locais: 483–488 módulos, 100% coincidentes
- `pg.odoo.connection [purpose=production]`: 24 ligações activas, mapeadas por repositório
