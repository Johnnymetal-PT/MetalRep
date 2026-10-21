# AGENTS_SHARED - Parâmetro Global Odoo Consulting Framework

## Finalidade do framework
Este ficheiro concentra as regras partilhadas do framework consultivo Odoo.
O objetivo principal é manter um método comum entre projetos e colaboradores, reduzindo customização prematura e forçando decisões baseadas em evidência.

## Ritual obrigatório no arranque de cada chat

**Invocação de scripts (Windows/PowerShell) — obrigatório:** num projeto, os scripts do framework vivem em **`.pg_framework\scripts\`** (symlink para o `_pg_template`), **não** em `scripts\`. Correr sempre os `.ps1` com `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\<nome>.ps1` (ou `pwsh` com os mesmos flags). A *ExecutionPolicy* da máquina pode estar em `Restricted` e bloquear `.ps1` executados diretamente (`PSSecurityException`); o `-ExecutionPolicy Bypass` evita esse bloqueio (tal como os hooks já fazem).

Sempre que um chat novo com agente (Codex, Claude ou Gemini) arrancar num projeto com esta framework:
1. executar `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_checkout_brodoo_branch.ps1 -RepoPath <path_do_repo>` para garantir que o agente está na branch Brodoo correcta antes de qualquer leitura ou acção
2. executar `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_ensure_framework_current.ps1 -RepoPath <path_do_repo>` — **garante a framework atualizada**: faz `git pull --ff-only` do `_pg_template` (se a árvore estiver limpa) e, se detetar drift entre a versão do framework e a registada no projeto (`PG_TEMPLATE_SYNC_STATE.json`), **re-sincroniza automaticamente** o projeto. À prova de falhas (offline não bloqueia). Este script encapsula os antigos passos "git pull + comparar HEAD + bootstrap-se-drift" e corre também automaticamente no hook `SessionStart`
3. garantir que a versão Odoo do projeto está conhecida antes de correr bootstrap com clone/sync de source
4. executar `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_preflight_context.ps1 -RepoPath <path_do_repo>` — é a **validação abrangente de dependências da framework** e escreve `.pg/PREFLIGHT.json`. Valida:
   - **(bloqueante)** versão Odoo confirmada; `vendor/odoo_src` coerente com a série; **`.pg_framework` ligado** (sem ele não há contrato/método/scripts partilhados);
   - **derivado**: `docs_base_url` da série;
   - **frescura da framework**: compara a versão do framework (`.pg_framework` HEAD) com a registada em `PG_TEMPLATE_SYNC_STATE.json` e deteta se o framework local está atrás do `origin` — avisa se o projeto está numa versão antiga (re-bootstrap/sync) ou se falta `git pull` (passo 2);
   - **(aviso)** metodologia (`doc_templates`), hooks de tokens (`.claude/settings.json`, `.codex/hooks.json`), registo de tokens (`.pg/tokens/consumption.jsonl`) e artefactos do espelho M1/M3 (`odoo_env.json`, `deliverables.json`).
   O agente deve **ler o `PREFLIGHT.json` e agir sobre os avisos** — em especial, se a framework estiver desatualizada, **atualizar antes de prosseguir** (não trabalhar sobre uma versão antiga).

Regra bloqueante:
- não continuar para leitura funcional, análise ou implementação sem executar e confirmar este ritual
- se o preflight (passo 4) devolver `status: fail`, parar e resolver as pré-condições bloqueantes (tipicamente correr `pg_clone_odoo_source.ps1`, `pg_link_framework.ps1` ou confirmar a versão Odoo) antes de continuar
- avisos do preflight (dependências não bloqueantes) não impedem a análise, mas devem ser reportados e resolvidos (cada aviso traz a ação de remediação)
- se algum passo falhar, parar e reportar o bloqueio ao utilizador
- o passo 1 é pré-condição de todos os outros: se o checkout para a branch Brodoo falhar, parar e reportar

Regra para versão Odoo:
- se a versão já estiver explícita no repositório (por exemplo em `PG_CONTEXT.md`, `PG_SCOPE_INTAKE.yaml` ou paths/version hints em `vendor/odoo_src`), usar essa versão
- se não houver informação fiável, parar e pedir ao utilizador a versão Odoo antes de executar o comando que depende dessa versão (ex.: `-Series`)

### Quando o código do repositório não é o código que corre

A fonte de verdade nº 2 é «código do projeto», e isso pressupõe que o que está no repositório é o que está a correr. **Em projetos adotados a meio, ou que fazem patch a um Odoo vivo, essa suposição pode ser falsa sem que nada o denuncie.**

`FACTO OBSERVADO` (givachoice, 2026-09-11): o repositório tem doze árvores de addons de gerações diferentes, e a melhor acerta em **10 dos 29** módulos instalados em produção. No mesmo repositório, uma branch de espelho do código vivo acerta em **29 de 29**.

Antes de concluir sobre comportamento a partir de código, estabelecer **de onde vem esse código**:

1. **O projeto tem espelho do código vivo?** Se tiver, é essa a fonte — e deve estar declarado no bloco de overrides locais do `AGENTS.md` do projeto, com a branch ou o caminho. O givachoice usa branches `live/*` escritas automaticamente.
2. **O espelho ainda corresponde?** Um espelho parado **não avisa que envelheceu**: continua a parecer a fonte de verdade, e essa é a falha mais perigosa das duas. Verificar com:
   ```powershell
   py .pg_framework\scripts\pg_compare_client_addons.py --project-key <key> --purpose production --ref <ref-do-espelho> --serie <serie>
   ```
3. **Não havendo espelho**, o mesmo comando sem `--ref` compara as árvores do repositório com o que está instalado, e diz se alguma corresponde. Se nenhuma corresponder, o código local é história: marcar `PONTO POR VALIDAR` e usar o canal `production` para os factos.

**Montar o espelho, quando o projeto ainda não o tem.** O `scripts/server/pg_mirror_server_code.sh` instala-se **no servidor do cliente** e publica em branches `live/*` o que lá está mesmo instalado. Copia-se o `pg_mirror_server_code.conf.exemplo` para `~/pg_mirror.conf`, declaram-se as árvores e o remoto, e corre por cron. Sem `CONFIRMA=1` inspeciona e não escreve nada — nem um carimbo.

Três coisas que ele faz e que valem por si:
- **não toca nas árvores que espelha**: o `.git` de cada espelho vive fora delas, e o servidor não fica com repositórios git no meio do código em produção;
- **do core espelha só o desvio** — o core passa de 1 GB e não compensa copiá-lo; compensa saber que alguém lhe tocou e ver o quê. Acima de um teto de ficheiros alterados regista a ocorrência e **não copia**, porque um upgrade mexe em milhares de ficheiros e isso é ruído, não desvio;
- **a varredura do core é separável** (`PG_SEM_CORE=1`), porque um `git status` sobre o core percorre 47 mil ficheiros — a 2026-08-06 isso gerou uma suspeita de lentidão do servidor reportada por um cliente. O padrão são dois crons: os addons frequentes e leves, o core uma vez por dia.

Atenção ao que a comparação **não** prova: versões iguais não provam código igual, porque nada obriga a subir a versão ao alterar um ficheiro. Uma divergência é prova de que difere; uma coincidência é apenas ausência de prova do contrário.

### Pastas de trabalho que não são repositórios

Boa parte do trabalho de Odoo acontece fora de repositórios: pastas de servidor, árvores de addons, cópias de migração. O ritual acima não se aplica aí — não há `.pg`, não há espelho, não há branch Brodoo.

**Se a pasta tiver um `AGENTS.md` com um bloco `PG_WORK_FOLDER`, os factos declarados nele têm precedência sobre qualquer suposição** — incluindo a de um resumo automático de sessão retomada. Versão do Odoo, servidor, base de dados, o que é só de leitura: é o que lá estiver.

Se não tiver, e o trabalho for recorrente nessa pasta, declarar uma vez:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_work_folder.ps1 -Path <pasta> -OdooSourcePath <source> -Servidor <srv> -BaseDados <bd>
```

O bloco é delimitado: o que estiver fora dele sobrevive a qualquer reexecução. E o script recusa-se a correr numa pasta que já seja repositório da framework.

**O trabalho feito numa pasta declarada passa a contar para a medição.** Se o bloco indicar `Repositorio do projeto:`, o hook de consumo regista lá a sessão — o evento diz **onde** o trabalho aconteceu (a pasta, com `work_folder: true`) e fica guardado **onde alguém o consulta** (o repositório). A pasta continua sem `.pg` e sem estrutura da framework.

Sem `Repositorio do projeto:` declarado não há onde registar, e a sessão não conta — em silêncio, porque um hook nunca estraga a sessão de quem está a trabalhar. Até 2026-09-11 **nenhum** trabalho fora de repositórios contava, e foi isso que obrigou a auditoria do givachoice a pedir extrações máquina a máquina para reconstruir o que lá tinha acontecido.

`FACTO OBSERVADO` (givachoice): em 46 conversas o agente procurou o `AGENTS.md` nessas pastas 7 vezes, não encontrou nada em nenhuma, e seguiu sem os factos — seis incidentes de confusão entre Odoo 17, 18 e 19 depois, incluindo um deploy de código v17 sobre o servidor de testes v19.

### Projetos que não são de Odoo

A frota tem projetos geridos no Odoo da Parâmetro Global cujo ERP-alvo **não é Odoo** (por exemplo PRIMAVERA). Nesses, "versão Odoo confirmada" e "`vendor/odoo_src` presente" são pré-condições impossíveis, e a regra bloqueante acima impediria todo o trabalho num repositório saudável.

O espelho Brodoo **continua válido e é o motivo de o repositório existir**: publica o estado factual do projeto a partir do Odoo da Parâmetro Global, que é independente do ERP do cliente. Só a camada de consultoria Odoo é que deixa de se aplicar.

A dispensa é por **declaração explícita** em `.pg/PROJECT_PROFILE.json`, nunca por inferência — uma etiqueta no Odoo a desligar um gate de qualidade seria pior do que o gate errado:

```json
{
  "schema_version": "1.0",
  "erp": "primavera",
  "odoo_applicable": false,
  "declared_at": "AAAA-MM-DD",
  "declared_by": "email de quem declara",
  "reason": "porque nao ha Odoo do cliente neste projeto"
}
```

Sem este ficheiro nada muda: o default é projeto Odoo.

O mesmo ficheiro cobre um segundo caso, que não é um projeto de todo: **repositórios de produto**, como o `parametro-odoo/Parametro_Global`, onde vivem os addons da casa (`pg_brodoo`, `pg_doc_templates`, `pg_project_budget_import`). Não têm espelho Brodoo a publicar — são o **código** do Brodoo — e por isso não têm branch Brodoo a declarar:

```json
{
  "schema_version": "1.1",
  "brodoo_mirror_applicable": false,
  "declared_at": "AAAA-MM-DD",
  "declared_by": "email de quem declara",
  "reason": "porque este repositorio nao tem espelho Brodoo"
}
```

Com esta chave, o `pg_align_fleet_framework.ps1` classifica-o como `fora_do_perimetro`: continua no relatório e na contagem, mas sai da lista de não-alinhados, que é para problemas por resolver. A `reason` aparece no relatório, para a decisão ficar auditável.

Como acima, só a chave dispensa — a presença do ficheiro não basta, e um perfil ilegível não dispensa nada. Um gate que se desliga por um ficheiro partido não é um gate.

Com `odoo_applicable: false`, o `pg_preflight_context.ps1` degrada a versão Odoo e o `vendor/odoo_src` de erro para aviso, e deixa de avisar sobre o inventário de módulos do cliente. Deixam também de se aplicar a este repositório:
- a ordem obrigatória de decisão `standard → módulo adicional → custom`
- a consulta a `vendor/odoo_src` e à documentação oficial do Odoo
- o wizard de Onboarding do Brodoo, que exige versão, edição e ambiente Odoo
- o `odoo_env.json`, cujo inventário de módulos instalados nunca será recolhido

Tudo o resto do método mantém-se: fontes de verdade do espelho, produção de documentos por template, registo de consumo de tokens e regras de redação.

Regra de preservação de contexto no bootstrap:
- não fazer override de conteúdo funcional já existente em `PG_CONTEXT.md` e `PG_SCOPE_INTAKE.yaml`, exceto quando houver instrução explícita para forçar reposição (`-Force`)

## Regra de commits — branch Brodoo obrigatória para ficheiros de framework

Esta regra é obrigatória e não admite exceções.

O agente nunca deve commitar ficheiros de framework ou do Brodoo para um branch que não seja o branch Brodoo do repositório.

**Ficheiros de framework/Brodoo (apenas para o branch Brodoo):**
- `.pg/` — todo o conteúdo sem excepção (mirror data, sync files, tokens, artefactos)
- `AGENTS.md`, `CLAUDE.md` — contrato com agentes AI
- `PG_CONTEXT.md` — memória funcional e decisória do projeto
- `PG_SCOPE_INTAKE.yaml` — intake estruturado do âmbito
- `doc_templates/` — templates documentais originados no Odoo Knowledge
- `projects/` — `PG_CONTEXT.md` por projeto em modo multi-projeto
- `.pg_framework/` — symlink para o framework partilhado
- `.github/workflows/pg_refresh_pg_context.yml`
- qualquer ficheiro copiado ou gerado por scripts do `_pg_template`

**Ficheiros de código Odoo (branches de desenvolvimento/produção):**
- módulos Odoo (`pg_*`, addons, etc.)
- código Python, XML, JavaScript específico do projeto
- ficheiros de configuração do projeto que não sejam de framework

**Verificação obrigatória antes de qualquer commit:**
1. Determinar a branch Brodoo do repo (campo `repository_branch` em `.pg/project/project.json` ou `.pg/projects/<key>/project/project.json`)
2. Verificar a branch actual: `git rev-parse --abbrev-ref HEAD`
3. Se branch actual ≠ branch Brodoo E o commit inclui ficheiros de framework → mudar para a branch Brodoo antes de commitar
4. Se o utilizador pede explicitamente para commitar ficheiros de framework numa branch não-Brodoo → recusar e explicar a razão

**Exemplo do erro a evitar:**
Fazer commit de `.pg/`, `PG_CONTEXT.md` ou `AGENTS.md` no branch `main` de um repositório onde o branch Brodoo é `teste` — esses ficheiros pertencem exclusivamente ao branch `teste`.

## Fontes de verdade obrigatórias
Antes de concluir qualquer análise, recomendação ou proposta técnica, consultar obrigatoriamente:
1. `PG_CONTEXT.md`
2. código do projeto
3. `vendor/odoo_src`
4. documentação oficial do Odoo da versão ativa registada no `PG_CONTEXT.md` — o URL base está derivado em `.pg/PREFLIGHT.json` (`docs_base_url`)
5. templates da metodologia consultiva em `.pg_framework/doc_templates/` (geridos na App Knowledge da Parâmetro Global e sincronizados pelo ritual; ver a secção "Produção de documentos" para o mapeamento) — fonte do método e dos formatos de entregável
6. ambiente Odoo real do projeto espelhado em `.pg/projects/<project_key>/project/odoo_env.json` (ou, em modo legacy, `.pg/project/odoo_env.json`): versão/edição/ambiente confirmados e **lista de módulos instalados no Odoo do cliente** — válida **apenas** quando `odoo_env.collection.status` for `collected` (ver a regra de leitura abaixo)
7. compromisso documental espelhado em `.pg/projects/<project_key>/project/deliverables.json` (ou `.pg/project/deliverables.json`): entregáveis comprometidos, milestones com estado de entrega/aceitação e datas — usar para reportar/planear o compromisso perante o cliente

### Regra de leitura do `odoo_env.json` (módulos instalados)

O bloco `odoo_env.collection` diz **de que base** veio o inventário e **quando** foi recolhido. Ler o `status` **antes** de usar a lista de módulos:

| `collection.status` | Significado | O que o agente faz |
|---|---|---|
| `collected` | inventário recolhido no Odoo do cliente identificado em `collection.base_url`/`database` | usar como fonte dos módulos instalados |
| `stale` | recolhido, mas fora do prazo de validade | usar com reserva e declarar a data de recolha; confirmar pelo canal `production` o que for decisivo |
| `unavailable` | não foi recolhido (`unavailable_reason` explica) | **`PONTO POR VALIDAR`** — os módulos instalados são desconhecidos |
| bloco ausente (`schema_version` `1.0`) | espelho antigo, de **origem desconhecida** | **não usar**; pode ser o inventário da base da Parâmetro Global |

Regra obrigatória: `installed_modules` vazio com `status` diferente de `collected` significa **"não sei"**, nunca "nada instalado". Nesse caso a ordem obrigatória de decisão não pode ser fechada a partir do espelho — usar o canal `production` (`pg_odoo_client_query.ps1`) ou declarar a incerteza.

Racional e contrato de recolha: `.pg_framework/docs/PG_007_ODOO_ENV_COLLECTION_CONTRACT.md`. Até 2026-08-10 o espelho publicava o inventário da base da Parâmetro Global etiquetado com os dados do cliente, o que invertia o passo 1 contra o passo 2 da ordem de decisão.

Ao interpretar `codigo do projeto` e `vendor/odoo_src`, o agente não se deve limitar a ficheiros versionados diretamente.
Deve considerar também fontes locais relevantes acessíveis a partir do repo atual por:

- symlink
- junction
- atalho estrutural equivalente

Regra prática:
- se o repo atual expuser uma fonte local relevante por atalho, essa fonte conta como parte do perímetro obrigatório de consulta
- `vendor/odoo_src` continua a ser o exemplo principal, mas não o único
- a ausência de leitura dessas fontes não pode ser mascarada como se a validação técnica estivesse completa

Se houver conflito entre memória geral e o projeto atual, prevalece sempre:
- o código do projeto
- o source Odoo consultado em `vendor/odoo_src`
- a versão registada no `PG_CONTEXT.md`
- a documentação oficial da mesma versão

Quando existirem, `PG_SCOPE_INTAKE.yaml`, `.pg/PG_SCOPE_SYNC.json` e `.pg/PG_EFFORT_SYNC.json` servem como fontes estruturadas complementares para inicializar ou refrescar o contexto.

Quando existir `.pg/PG_PROJECT_INDEX.json` (modo multi-projeto), o agente deve usar primeiro o `project_key` correto e priorizar os artefactos namespaced, incluindo:
- `.pg/projects/<project_key>/tasks/tasks.json`
- `.pg/projects/<project_key>/PG_SCOPE_SYNC.json`
- `.pg/projects/<project_key>/PG_EFFORT_SYNC.json`
Estes ficheiros não substituem o `PG_CONTEXT.md`, que continua a ser a memória funcional e decisória do projeto.

Regra obrigatória em multi-projeto:
- não usar `.pg/tasks/tasks.json` global como fonte principal quando existir estrutura `.pg/projects/`
- se o `project_key` não estiver inequívoco, parar e pedir ao utilizador qual é o projeto correto antes de continuar

## Canal de dados Brodoo (fallback `read_mode=api`)
Quando um dado necessário **não estiver** nos artefactos espelhados do projeto (`.pg/...`) — por exemplo, períodos de férias de colaboradores para aferir disponibilidade num planeamento — o agente pode consultar diretamente o Odoo da Parâmetro Global através do utilizador de serviço **Brodoo**, usando o helper:

`powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_odoo_query.ps1 -Model <modelo> -Method <metodo> -Domain "<dominio-json>" [-Fields a,b] [-Limit N]`

Regras:
- é o caminho **mais caro** (acesso direto à API) — usar **só** quando o espelho não tem o dado; preferir sempre primeiro os artefactos.
- toda a consulta por este canal deve ser registada com `read_mode: "api"` no consumo de tokens (ver secção "Registo de consumo de tokens").
- as credenciais (utilizador Brodoo) vivem em `.pg_framework/credentials/brodoo_credentials.json` (só no `_pg_template` privado; nunca copiadas para repos de projeto/cliente).

## Canais Odoo do cliente por projeto (`read_mode=api`)
Além do canal Brodoo (que consulta o Odoo **da Parâmetro Global**), cada projeto pode ter **acesso direto ao Odoo do cliente**, por finalidade, através do helper:

`powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey <project_key> -Purpose <production|brodoo_dev> -Model <modelo> [-Protocol <auto|rpc|mcp>] -Method <metodo> -Domain "<dominio-json>" [-Fields a,b] [-Limit N]`

O helper obtém as credenciais do Odoo-alvo a partir do Odoo PG (modelo `pg.odoo.connection`, via canal Brodoo) e depois consulta o Odoo do cliente:
- Suporta **auto-comutação de protocolo** (`-Protocol auto` por defeito): tenta JSON-RPC clássico e, se a instância for Odoo 19+ / SaaS 19.4+ com endpoint nativo `/mcp`, comuta de forma transparente para o **Model Context Protocol (MCP)** via Bearer Token.
- Para consultas diretas dedicadas a instâncias MCP Odoo 19+, pode também ser usado o helper:
  `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_odoo_mcp_query.ps1 -BaseUrl <url> -ApiKey <chave_mcp> -Model <modelo> [-Action search|read_group|get_fields|context]`

Três finalidades principais de ligação:
- **`production`** — Odoo de **produção do cliente** → analisar a **adoção** do cliente ao Odoo (ex.: módulos realmente instalados, utilizadores ativos, volumes reais). É a fonte primária para a *ordem de decisão* (standard já disponível vs adicional) quando o `odoo_env.json` não chega.
- **`brodoo_dev`** — Odoo da branch **`brodoo`** (build **Staging** Odoo.sh) → fins de **desenvolvimento** (validar config/dados em construção).
- **`client_test`** — base de **testes/validação do cliente** → destino da **promoção de dados** vinda do `brodoo_dev`, antes de produção.

A finalidade não é só uma etiqueta: é o que **autoriza a escrita** nas migrações de dados. Ver a secção "Migração de dados entre bases Odoo" abaixo.

Regras:
- é o caminho **mais caro** (2 saltos: Brodoo → Odoo do cliente) — usar **só** quando os artefactos espelhados e o canal Brodoo não bastam.
- registar sempre `read_mode: "api"` no consumo de tokens.
- as credenciais do cliente ficam **centralizadas no Odoo PG** (`pg.odoo.connection`, configuradas em Brodoo > Repositório > Ligações Odoo do cliente); **nunca** em secrets de repos de cliente nem copiadas para o repo.
- o acesso é sempre **orientado/comandado por um elemento da equipa** — não usar autonomamente para escritas no Odoo do cliente sem instrução explícita.

### Um 404 em `/jsonrpc` é o módulo `rpc`, não o servidor em baixo

No Odoo 19 os endpoints `/jsonrpc` e `/xmlrpc` **saíram do core** e passaram a vir de um módulo próprio, `rpc` ("RPC endpoints", `auto_install: true`). `FACTO OBSERVADO` na produção da ENIGMAF, 2026-09-08.

Se esse módulo for desinstalado numa base de cliente, **todo o canal Brodoo morre nessa base** — leituras, espelho e migrações. O `auto_install` protege contra a desinstalação acidental por dependências, não contra uma deliberada.

Os helpers (`pg_odoo_query.ps1`, `pg_odoo_client_query.ps1`) reconhecem o 404 e nomeiam esta causa. Confirma-se em **Definições > Aplicações**, removendo o filtro "Aplicações" e procurando `rpc`.

Os mesmos endpoints estão marcados para **remoção no Odoo 22** (issue #56): funciona hoje, mas é um prazo com número que atinge todos os projetos ao mesmo tempo.

### Em staging do Odoo.sh, o `base_url` também é volátil

A secção seguinte trata o `database` como cache que envelhece. **Em builds de staging, o `base_url` envelhece da mesma maneira, e isso não estava escrito em lado nenhum.** A cada rebuild da branch mudam **as duas** coisas:

```
antes do rebuild : ...-valid-37654604.dev.odoo.com  /  parametroglobaladmin-enigmaf-valid-37654604
depois do rebuild: ...-valid-37762382.dev.odoo.com  /  parametroglobaladmin-enigmaf-valid-37762382
```

`FACTO OBSERVADO` (projeto `parametroglobaladmin-enigmaf`, branch `valid`, 2026-09-09). Com o URL antigo o `pg_odoo_resolve_db.ps1` falha, porque o host deixou de existir — e o resolver resolve a base **dado** um URL; não resolve o URL.

`PONTO POR VALIDAR` fechado pela negativa: foram testados os URLs estáveis por branch (`<projeto>-<branch>.dev.odoo.com` e `<projeto>-<branch>.odoo.com`) e ambos devolvem endpoint bloqueado ou ambíguo. **Não há URL estável adivinhável**: o novo copia-se do botão **CONNECT** da branch no Odoo.sh e escreve-se em `pg.odoo.connection.base_url`.

Regra prática: quando uma ligação de finalidade `client_test` ou `brodoo_dev` deixa de responder, a **primeira** hipótese é um rebuild da staging — não credenciais nem rede. Ligações de `production` não têm este problema: o URL de produção é estável.

Detalhe e um segundo modo de falha no mesmo contexto (a chave da produção não autentica na staging): issue #58.

### Nome da base de dados (auto-resolução em cascata)
O nome da BD é **obrigatório** no External API (`authenticate`/`execute_kw`) e **não é derivável** de url+login+api_key: o `db.list()` (serviço RPC) está tipicamente desativado e o nome **não** é o subdomínio (ex.: domínio `cartonagemsaotiago.odoo.com` → BD `parametroglobaladmin-cst1-producao-25532973`). Em Odoo.sh o nome da BD = nome do **build** e **muda a cada rebuild** (sobretudo em staging, ex.: canal `brodoo_dev`), pelo que o `database` guardado em `pg.odoo.connection` funciona como **cache** que pode ficar obsoleta (ou vir vazia).

Quando uma consulta `pg_odoo_client_query.ps1` falha a autenticação no Odoo-alvo (sinal típico de BD em falta/obsoleta por nova build), o **auto-heal** resolve o nome atual pelo helper `pg_odoo_resolve_db.ps1`, do canal mais barato para o mais caro, **persiste-o** em `pg.odoo.connection.database` (canal Brodoo, `method write`) e **retenta** — sem intervir no módulo Brodoo:
1. **HTTP `POST /web/database/list`** (anónimo, instantâneo) — só precisa do `base_url` que a ligação já tem, **sem SSH**. É o caminho preferido; resolve a maioria dos casos sem intervenção nem `-SshTarget`.
2. **SSH** (`select current_database()`) — fallback quando o endpoint HTTP está bloqueado (`list_db=False`) ou devolve várias BDs (ambíguo). Passar `-SshTarget <user@host>` (obtido da UI **"Connect"** da branch no Odoo.sh); usa a conta GitHub/SSH do operador — **sem guardar segredos novos**.

Uso manual do resolver (afinação): `... -File .pg_framework\scripts\pg_odoo_resolve_db.ps1 -BaseUrl <url> [-SshTarget <user@host>]`; para persistir à mão, `pg_odoo_query.ps1 -Model pg.odoo.connection -Method write -ArgsJson '[[<id>],{"database":"<nome>"}]'`.

Notas:
- este é o **refrescador**; consumidores headless (ex.: workflow semanal de adoção, que corre sem o SSH do operador) continuam a ler o `database` **persistido** — daí a persistência ser importante.
- `PONTO POR VALIDAR`: o `/web/database/list` depende da config (`list_db`) da instância; quando fechado, só o SSH resolve. A sintaxe/host SSH por branch/build do Odoo.sh copia-se da UI "Connect" (os scripts **não a adivinham**, recebem-na em `-SshTarget`).
- registar `read_mode: "api"` no consumo de tokens (mesmo custo de canal API/shell).

## Migração de dados entre bases Odoo (regra obrigatória)

Qualquer script que **escreva** dados no Odoo de um cliente — promoção de `brodoo_dev` para `client_test`, migração Studio → standard, correcção de campos em massa, reposição a partir de uma fonte — tem de passar por `.pg_framework/scripts/pg_odoo_migration_guard.py`. Nenhum script deve falar com o Odoo directamente.

O guard é o **ponto único de passagem**: por ser o único caminho, o que ele proíbe fica proibido para todos os scripts da migração.

A autoridade é a **finalidade da ligação**, nunca o nome da base de dados. Em Odoo.sh o nome da base muda a cada rebuild da branch, pelo que qualquer constante com o nome da staging fica obsoleta e passa a bloquear todo o trabalho.

| Finalidade | Escrita |
|---|---|
| `brodoo_dev` | permitida com `--confirm` |
| `client_test` | permitida com `--confirm` |
| `production` | bloqueada; exige `--confirm` **e** `--allow-prod`, depois de um dry-run revisto |

As credenciais do Odoo-alvo vêm de `pg.odoo.connection` pelo canal Brodoo, **em memória** — `resolver_alvo_por_projeto(<project_key>, <purpose>)`. **Não criar ficheiros de ligação com API keys nos repositórios de projeto**: contraria a política de credenciais desta mesma secção e obriga quem executa a escrever segredos para disco. Se a ligação não existir, criá-la em Brodoo > Repositório > Ligações Odoo do cliente.

Camadas que uma escrita tem de atravessar, todas elas:
1. o método está classificado na lista branca como escrita (um método **não classificado é bloqueado** — pode escrever sem se saber);
2. a finalidade da ligação permite escrever;
3. a execução foi confirmada (`--confirm`);
4. a chamada pediu `allow_write=True` explicitamente;
5. em produção, `--allow-prod` além do resto.

Acresce uma verificação de coerência: base cujo nome contém `main` (convenção de produção do Odoo.sh) declarada com finalidade diferente de `production` **aborta** — apanha uma ligação mal configurada.

Regras de operação:
- **dry-run primeiro**, sempre. Nada é escrito sem `--confirm`.
- a migração deve ser **idempotente** (poder correr várias vezes com o mesmo resultado), tipicamente com um `reset` do que a passagem anterior criou.
- **reconciliação obrigatória no fim**: contagens origem = destino, e o registo do resultado. Uma migração sem reconciliação não está terminada.
- **nunca apagar** camadas anteriores (vistas/menus Studio, campos `x_`): desactivar, que é reversível. A eliminação é uma fase posterior de decomissionamento, depois de tudo validado.
- todas as chamadas ficam registadas em `.pg/migration/api_calls.log.jsonl`.

## Implantar código no servidor de um cliente (regra obrigatória)

A secção anterior governa a escrita de **dados**. Esta governa a de **código** — copiar módulos para um servidor, atualizar um módulo instalado, reiniciar o serviço.

Até 2026-09-11 a framework não tinha regra nenhuma para isto, e a assimetria era difícil de defender: migrar um campo exigia dry-run, `--confirm`, `--allow-prod` e reconciliação; pôr código novo a correr na produção de um cliente não exigia nada.

`FACTO OBSERVADO` (givachoice): os dois incidentes mais caros do projeto foram de código, não de dados — um deploy de código **v17 sobre o servidor de testes v19**, recuperado por um backup manual feito por sorte minutos antes; e um «aplicado em produção com sucesso» que **não estava**. Nenhum teria passado pelo guard de dados, porque nenhum tocou em dados.

**Cinco passos, todos eles, por esta ordem:**

1. **Confirmar a série do destino contra o próprio destino**, não contra o que se julga. É o travão direto do incidente v17-sobre-v19: a versão do módulo `base` na base-alvo diz a série que lá corre, e um módulo de outra série não vai para lá.
2. **Resguardo antes de tocar.** Não como boa prática: como passo que o caminho obriga. O que se substitui tem de ficar recuperável sem depender de memória nem de sorte.
3. **Dry-run primeiro**, sempre — o que seria copiado, o que seria substituído, o que seria reiniciado.
4. **Em produção, confirmação explícita** do operador para aquela execução concreta, como `--allow-prod` faz nos dados. Uma autorização dada uma vez não cobre a execução seguinte.
5. **Verificar depois, contra o destino.** É isto que transforma «aplicado com sucesso» de afirmação em facto, e é o passo que faltou no incidente do «sucesso» que não era.

**Sobre o passo 5, e é a parte que se costuma fazer mal.** A versão do manifest **não prova** o código em execução: nada obriga a subê-la ao alterar um ficheiro. `FACTO OBSERVADO` (GBUK): a versão `18.0.2.8.3` chegou a nomear **dois códigos diferentes**. Comparar versões é o **mínimo**, não o suficiente.

A framework **exige a prova, não o mecanismo** — porque os projetos já resolveram isto de maneiras diferentes e ambas servem:
- **impressão digital do código instalado** (GBUK): o módulo expõe um método de leitura que devolve o SHA-256 por ficheiro, e compara-se ficheiro a ficheiro;
- **espelho do código vivo** (givachoice): um mecanismo próprio publica em branches o que está mesmo no servidor, e compara-se contra elas.

Qualquer meio serve desde que prove **código**, e não só rótulo. Na ausência de qualquer um deles, a verificação possível é a das versões:

```powershell
py .pg_framework\scripts\pg_compare_client_addons.py --project-key <key> --purpose production --serie <serie>
```

— e a conclusão tem de ser declarada como o que é: **`PONTO POR VALIDAR`**, não «verificado».

**O guião escreve-se por template**, não de memória: `TPL_JANELA_MANUTENCAO.md`. As suas secções são os cinco passos acima, mais duas que a prática mostrou fazerem falta — **o que o guião não leva, e é deliberado** (senão o que fica de fora parece esquecimento em vez de decisão) e **quem avisar antes de abrir a janela** (o travão protege os dados, não a relação com quem mantém o módulo).

**Nunca escrever «validado» sobre o que só foi implantado.** Implantar prova que o código lá está; validar é o cliente dizer que faz o que ele quer. É a mesma distinção de «Antes de alterar o que já funciona», e aplica-se inteira.

## Apoio consultivo reutilizável
Quando o requisito se assemelhar a um caso recorrente, o agente pode consultar `.pg_framework/docs/PG_CONSULTING_DECISION_PATTERNS.md`.
Quando for útil recuperar aprendizagem consultiva anterior, o agente pode consultar `.pg_framework/docs/PG_PROJECT_LEARNINGS.md`.
Estes ficheiros servem apenas como apoio ao raciocínio e nunca substituem a validação do projeto atual contra `PG_CONTEXT.md`, código do projeto, `vendor/odoo_src` e documentação oficial da versão ativa.

## Modo challenger
Quando existir uma proposta funcional ou técnica concreta, o agente pode operar em modo challenger.
Nesse modo, deve criticar a solução antes de a validar e usar `.pg_framework/docs/PG_CHALLENGER_PROMPT.md` como referência.

## Ordem obrigatória de decisão
Antes de propor qualquer desenvolvimento custom, validar e documentar sempre esta ordem:
1. solução standard já disponível no projeto
2. solução standard adicional disponível no Odoo, mesmo que o módulo não esteja instalado
3. desenvolvimento custom

Esta ordem é obrigatória.

### O Odoo Studio não é um passo desta ordem (regra obrigatória)

**Proibido criar configurações, campos, vistas, menus, relatórios ou automações em Odoo Studio**, em qualquer ambiente de qualquer cliente. Decisão de Bruno Pinheiro, 2026-09-11. O Studio deixou de ser uma opção intermédia: o que não se resolve por standard resolve-se por desenvolvimento, versionado no repositório.

Esta regra está escrita como proibição e não como omissão de propósito. Apagar a menção faria o Studio parecer apenas esquecido, e um agente reintroduzi-lo-ia como «opção leve» — que é exactamente como ele entra.

`FACTO OBSERVADO` (givachoice, 2026): acrescentar uma vista pelo Studio criou quatro registos `ir.actions.act_window.view` com sequências mais baixas do que as do padrão, e a aplicação do cliente passou a abrir no formulário de criação. Foi uma das quatro regressões sobre comportamento que o cliente já tinha. O Studio escreve na base registos que a análise não prevê, não passam por revisão, não aparecem em diff e não viajam com o repositório.

**O que fazer com o Studio que já existe** — e existe em vários clientes: continua a ser legítimo lê-lo, documentá-lo e migrá-lo para standard ou para módulo versionado. A proibição é de **criar**, não de lidar com o existente. As regras de migração mantêm-se inteiras, incluindo a de **nunca apagar** vistas, menus ou campos `x_` — desactivar, que é reversível.

Se um requisito parecer exigir Studio, a resposta não é abrir o Studio: é classificar como `Customizacao leve` ou `Customizacao estrutural` e justificar, ou declarar `Nao recomendado / alto risco`.
Nunca saltar a análise de módulos standard adicionais.
Nunca limitar a análise apenas aos módulos principais já usados no projeto.
Na avaliação de módulos standard adicionais, consultar também diretamente o `vendor/odoo_src` da versão ativa para descobrir módulos standard potencialmente relevantes, incluindo módulos novos do Odoo, e não apenas exemplos presentes na documentação do projeto.

Antes de classificar o passo 1 (standard já disponível) vs passo 2 (standard adicional), consultar obrigatoriamente `.pg/projects/<project_key>/project/odoo_env.json` (ou `.pg/project/odoo_env.json`) para verificar que módulos estão **realmente instalados** no ambiente do projeto — não inferir o que está instalado a partir de memória ou do nome do projeto. Um módulo standard já instalado é passo 1; um módulo standard existente mas não instalado é passo 2.

Esta consulta só conclui a classificação quando `odoo_env.collection.status` for `collected` (ver "Regra de leitura do `odoo_env.json`"). Caso contrário, o espelho não sabe o que está instalado: usar o canal `production` (`pg_odoo_client_query.ps1 -Purpose production -Model ir.module.module -Domain '[["state","=","installed"]]'`) ou marcar a classificação como `PONTO POR VALIDAR`. Nunca deduzir "não está instalado" da ausência de dados.

## Antes de alterar o que já funciona (regra obrigatória)

A ordem de decisão acima serve para escolher **o que construir**. Esta serve para proteger **o que já existe**, e aplica-se a qualquer alteração de comportamento num sistema que já esteja em uso.

**São dois riscos, e o ensaio só apanha um.**

- *Isto parte alguma coisa?* — apanha-se com resguardo, ensaio, travão e verificação depois. É mecânico.
- *Isto é o que eles querem?* — **nenhum ensaio apanha isto.** Só se apanha lendo a origem do pedido, ou perguntando.

Antes de propor qualquer alteração de comportamento:

1. **Procurar se foi pedido.** Chatter do documento, tarefas fechadas, mensagens do cliente. Se não se encontrar origem, **dizer que não se encontrou** — nunca assumir que não existe.
2. **Classificar e declarar em que categoria se está:** *defeito* (o sistema faz o contrário do que promete), *decisão do cliente* (não se toca), *decisão nossa por documentar* (regista-se, não se altera).
3. **Dimensionar:** quantos registos, quem é afetado, o que se desfaz e como.
4. **Não confundir «ensaiado» com «validado».** Ensaiar prova que corre; validar é o cliente dizer que é aquilo que quer. Nunca escrever «validado» sobre o que só foi ensaiado.

**Corolário:** uma correção que ninguém pediu tem de passar uma barra **mais alta** do que uma que foi pedida — não mais baixa por ser pequena.

`FACTO OBSERVADO` (givachoice, 2026): quatro alterações atingiram comportamento que o cliente já tinha, com 4 a 30 dias de exposição até serem revertidas. Duas delas estavam **tecnicamente corretas e erradas na mesma** — eram pedido do cliente aquilo que foi levantado como defeito. Auditoria em `.pg_framework/docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md`.

Uma dessas quatro regressões veio do **Odoo Studio**, e foi essa a evidência que levou à sua proibição (ver «O Odoo Studio não é um passo desta ordem»). Ao encontrar comportamento estranho num cliente, o Studio existente continua a ser suspeito legítimo: as suas alterações não aparecem em diff nem no repositório, pelo que ler o código não basta para estabelecer o que o sistema faz hoje.

## Validações obrigatórias antes de recomendar
Antes de fechar uma recomendação, validar ou marcar explicitamente como `PONTO POR VALIDAR`:
- versão do Odoo
- edição (`Community` ou `Enterprise`)
- ambiente (`SaaS`, `Odoo.sh` ou `on-premise`)
- restrições contratuais do projeto:
  - configuração standard permitida?
  - módulos standard adicionais permitidos?
  - custom permitido?
  - existe Studio **já aplicado** neste ambiente? (não para o usar — está proibido criar — mas porque muda o que o sistema faz hoje, e isso não se vê no código)

Se algum destes pontos for crítico para a decisão e não estiver confirmado, pedir clarificação antes de concluir.

## Gestão de incerteza e evidência
Esta secção é obrigatória em análise funcional, consultoria e proposta técnica.

O agente:
- não deve adivinhar funcionalidades
- não deve assumir comportamentos do Odoo sem validação
- não deve apresentar inferências como factos
- não deve recomendar customização sem evidência
- deve pedir clarificação quando faltar contexto crítico
- deve declarar a incerteza explicitamente

Cada conclusão relevante deve distinguir entre:
- `FACTO OBSERVADO`: confirmado no código, no contexto do projeto ou na documentação oficial
- `INFERENCIA`: conclusão provável, mas não confirmada
- `PONTO POR VALIDAR`: informação necessária antes da decisão

## Regras de consulta e evidência
Sempre que a análise recorrer ao source Odoo ou a módulos standard:
- citar explicitamente os paths consultados em `vendor/odoo_src`
- citar os links da documentação oficial consultada
- explicar o padrão encontrado antes de propor alterações
- se a recomendação for `Modulo standard adicional`, classificar obrigatoriamente a cobertura do requisito como `TOTAL`, `PARCIAL` ou `PARCIAL COM ADAPTACAO DE PROCESSO`
- quando a recomendação for `Modulo standard adicional`, explicar também as implicações de adoção, incluindo impacto funcional, impacto no processo e eventuais gaps remanescentes

Quando existirem atalhos locais relevantes no repo atual:
- citar também o path local efetivamente seguido a partir do repo
- distinguir entre ficheiro nativo do repo e fonte consultada via atalho, symlink ou junction
- não assumir que `vendor/odoo_src` é a única fonte local relevante só porque é a mais comum

Quando a conclusão for que o standard não chega, justificar explicitamente:
- porque a configuração standard existente não resolve
- porque um módulo standard adicional não resolve
- porque a opção custom é necessária apesar do impacto em upgrade, manutenção e contrato

## Classificação obrigatória da recomendação final
Toda a recomendação final deve ser classificada numa destas categorias:
- `Configuracao standard`
- `Modulo standard adicional`
- `Customizacao leve`
- `Customizacao estrutural`
- `Nao recomendado / alto risco`

## Regras de implementação
- `vendor/odoo_src` é estritamente `read-only`
- nunca alterar ficheiros dentro de `vendor/odoo_src`
- tudo o que for criado no projeto deve usar prefixo `pg_` quando aplicável
- se houver restrição contratual contra custom code, não propor custom como caminho principal
- se a recomendação final for custom, a justificação consultiva vem antes da proposta técnica

## Formato mínimo esperado na resposta
Sempre que houver análise de requisito, incluir no mínimo:
1. objetivo funcional e dor de negócio
2. factos observados
3. inferências
4. pontos por validar
5. análise das opções na ordem obrigatória
6. recomendação classificada
7. riscos, impactos e próximos passos
8. referências consultadas:
   - `PG_CONTEXT.md`
   - paths do projeto
   - paths de `vendor/odoo_src`
   - links oficiais do Odoo da versão ativa

Se a recomendação final for `Modulo standard adicional`, incluir também:
- cobertura do requisito: `TOTAL`, `PARCIAL` ou `PARCIAL COM ADAPTACAO DE PROCESSO`
- implicações de adoção

Antes de apresentar uma recomendação consultiva final, aplicar também a verificação definida em `.pg_framework/docs/PG_PRE_RESPONSE_CHECKLIST.md`.

## Atualização do contexto
`PG_CONTEXT.md` é a memória funcional e decisória do projeto.
Atualizar em marcos relevantes, incluindo:
- mudança de decisão consultiva
- fecho de análise funcional
- conclusão de desenvolvimento relevante
- bloqueios, riscos ou restrições novas
- antes de commit ou PR final, quando aplicável

## Produção de documentos
Quando for pedido ao agente para produzir um documento (ponto de situação, levantamento de âmbito, orcamento, email ao cliente, proposta técnica ou similar), o agente deve:
1. identificar o tipo de documento pedido
2. consultar o template correspondente em `.pg_framework/doc_templates/`
3. adaptar o template ao contexto específico do projeto usando `PG_CONTEXT.md` e o contexto da sessão
4. respeitar a estrutura de secções e o tom de discurso definidos no template

Mapeamento de templates disponíveis:
- ponto de situação / status report → `TPL_PONTO_SITUACAO.md`
- ponto de situação em PowerPoint / PPTX / deck de status ao cliente → `TPL_PONTO_SITUACAO_PPTX.md` (o conteúdo vem de `TPL_PONTO_SITUACAO.md`; o deck é gerado por `pg_build_ponto_situacao_pptx.py`, nunca desenhado à mão)
- status semanal / ponto de situação semanal → `TPL_STATUS_SEMANAL_V1.md` (seguir obrigatoriamente `TPL_STATUS_SEMANAL_INSTRUCOES.md`)
- levantamento de âmbito / análise de âmbito → `TPL_LEVANTAMENTO_AMBITO.md`
- email ao cliente → `TPL_EMAIL_CLIENTE.md` (o `.md` é o rascunho; o que se entrega é o HTML colável gerado por `pg_copy_email_cliente.ps1`, nunca markdown para colar à mão)
- proposta técnica / fit-gap / análise de requisito → `TPL_PROPOSTA_TECNICA.md`
- orcamento / estimativa de esforco → `TPL_ORCAMENTO.md`
- orcamento em PowerPoint / PPTX / deck comercial de orcamento → `TPL_ORCAMENTO_PPTX.md`
- importação inicial de dados / importação de contactos e produtos / arranque de dados / migração inicial → `TPL_IMPORTACAO_INICIAL_CONTACTOS_PRODUTOS.md`
- demo / demonstração ao cliente → decidir primeiro pela **origem dos dados**:
  - dados fictícios, base criada de raiz → `TPL_CRIA_DEMO.md`
  - dados reais do cliente, no ambiente do cliente (branch `brodoo`) → `TPL_CRIA_DEMO_DADOS_CLIENTE.md`
  - se não for evidente qual, **perguntar antes de começar** (a regra dos dados é oposta nos dois)
- guia de processo / guia imprimível de um módulo ou fluxo existente → `TPL_CRIA_DEMO_DADOS_CLIENTE.md` (Passo 3)
- migração de dados entre bases Odoo / promoção para validação ou produção / migração Studio → standard → `TPL_MIGRACAO_DADOS_ODOO.md`
- janela de manutenção / implantação de código ou configuração num servidor de cliente → `TPL_JANELA_MANUTENCAO.md`
- auditoria de código / relatório de auditoria interna → `TPL_AUDITORIA_CODIGO_INTERNA.md`
- entregáveis contratados / formalização contratual / o que enviar ao cliente e quando → `TPL_FORMALIZACAO_CONTRATUAL.md`
- matriz funcional / RACI / perfis e controlo de acessos no Odoo → `TPL_MATRIZ_FUNCIONAL_RACI_EXECUTAVEL.md`
- descrição de timesheet a partir do repositório → `TPL_TIMESHEET_INSTRUCOES.md` (instrução ao agente, **não** é template de output)

O template define o **conteúdo**; o formato de entrega é uma decisão à parte. Markdown é o que fica versionado e o que se revê em diff. Quando o que vai para o cliente tiver de sair com o layout da marca, ver "Documentos Word e PDF" e "Identidade visual em decks PowerPoint" abaixo.

Quando **não existir** template específico para o que foi pedido, o agente **não deve escolher sozinho** um template aproximado. Deve parar, indicar que não há template dedicado, apresentar os candidatos mais próximos e **perguntar ao utilizador qual usar** (ou se prefere sem template).

Esta regra é obrigatória: produzir um documento inteiro com a estrutura errada desperdiça o trabalho do agente e o tempo de revisão de quem o lê. Uma pergunta curta antes de começar custa menos do que um entregável para deitar fora.

O agente não deve produzir documentos formais sem consultar o template correspondente.

### Identidade visual em decks PowerPoint (regra obrigatória)

Quando o entregável for um `.pptx`, a identidade Parâmetro Global vem **exclusivamente** de `.pg_framework/scripts/pg_pptx_identity.py` (paleta, tipografia, capa, cabeçalho, rodapé e componentes, extraídos do ficheiro da marca `doc_templates/assets/Template_Parametro_PowerPoint_Completo 1.pptx`).

Proibido:
- redesenhar a identidade a partir da descrição escrita de um template;
- usar `doc_templates/assets/create_parametro_powerpoint_template.py` (script legado, com conteúdo de outro projeto e logótipo em falta);
- construir slides à mão a partir do `.pptx` da marca — esse ficheiro é **referência visual para edição humana**, não tem placeholders e não serve para geração automática.

Se faltar um componente, acrescentá-lo ao módulo partilhado para que todos os templates o passem a usar. É esta regra que garante que dois decks gerados em projetos diferentes saem iguais.

### Documentos Word e PDF com a identidade da marca

Um `.docx` para o cliente **não se escreve à mão nem se monta com `python-docx` a partir do zero**. O conteúdo sai do template em Markdown — que é o que fica versionado e o que se revê em diff — e a conversão é:

```powershell
py .pg_framework\scripts\pg_build_docx_from_markdown.py --input <doc>.md --output <doc>.docx [--label "<rodapé>"]
```

A identidade (capa, tipografia, paleta, tabelas, caixas de nota, rodapé) vem de `pg_docx_identity.py`, herdada do ficheiro oficial da marca — pela mesma razão que a dos decks: dois documentos gerados em projetos diferentes têm de sair iguais. O conversor mapeia `#` para capa e títulos de secção, `##`/`###` para subtítulos, `- [ ]` para checklist, tabelas e `>` para os componentes da marca, e promove à capa o bloco de metadados que venha logo a seguir ao `#`. Requer `python-docx`.

Se faltar um componente, acrescentá-lo a `pg_docx_identity.py`, nunca ao documento.

Quando o entregável for **PDF** — tipicamente um documento para o cliente imprimir, preencher ou arquivar sem o poder editar — o caminho é o mesmo Markdown, por outro conversor:

```powershell
py .pg_framework\scripts\pg_build_pdf_from_markdown.py --input <doc>.md --output <doc>.pdf [--subtitulo @<ficheiro>.txt]
```

O `--subtitulo` aceita `@ficheiro` e é assim que se passa texto acentuado: em Windows, os acentos perdem-se a passar por argumentos de linha de comando, e um PDF real já saiu com «Mobiliario». Ler de um ficheiro UTF-8 resolve.

**Qual dos dois:** Word quando o cliente vai editar ou comentar o documento; PDF quando vai ler, imprimir ou preencher em papel, e sobretudo quando o documento tem **tabelas longas** — o conversor de PDF repete o cabeçalho da tabela em cada página, não parte linhas entre páginas e não deixa títulos órfãos, que é o que separa uma tabela de 44 linhas utilizável de uma inútil.

A paleta dos três formatos (PPTX, Word e PDF) vem toda de `pg_brand_palette.py`. Nenhum gerador define cores por sua conta: era precisamente por os módulos de Word e PowerPoint declararem cada um o seu azul que divergiram até 2026-09-11.

O PDF exige `playwright` **e** o Chromium (`python -m playwright install chromium`, ~150 MB, uma vez por máquina). O conversor falha a dizer este comando quando falta; as dependências estão declaradas em `requirements.txt`, na raiz do framework.

### Emails para colar no Odoo (regra obrigatória)

Um email ao cliente não é entregue em markdown. O compositor do Odoo não interpreta markdown: os `**`, os `-` e os `|` chegam como texto literal e obrigam quem envia a reformatar tudo à mão. O entregável é o **HTML colável**, gerado por:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_copy_email_cliente.ps1 -Path <rascunho>.md
```

O script escreve o `.html` ao lado do rascunho (pré-visualização no browser, com botão de copiar) e deixa o corpo na área de transferência já formatado — no Odoo é só `Ctrl+V`.

Contrato do rascunho `.md`:
- o assunto e os destinatários vão num bloco no topo, delimitado por `---`, com as chaves `assunto`, `para`, `cc` e `bcc`. Nunca entram no corpo colável. Em alternativa, aceita-se uma primeira linha `Assunto: ...`;
- o corpo é markdown normal: negrito, itálico, listas (com um nível de aninhamento), tabelas, links e citações;
- uma linha em branco separa parágrafos; uma quebra simples fica quebra de linha;
- **não escrever fecho nem assinatura** ("Com os melhores cumprimentos", nome, cargo, contactos). O compositor do Odoo insere a assinatura do utilizador (`res.users.signature`), que já traz saudação de fecho, nome, cargo e rodapé da marca; repetir isso obriga quem envia a apagar à mão em cada email. O conversor retira o fecho que encontrar no fim do corpo e reporta o que retirou — `-ManterAssinatura` mantém-no, para destinos sem assinatura configurada.

O HTML sai **sem CSS**, e é propositado: o editor do Odoo remove sempre o atributo `style` do que é colado, pelo que fixar tipos de letra ou cores é trabalho perdido — a formatação passa a vir do próprio Odoo. Por isso também desaparecem na colagem os `---` de separação (`<hr>`), o `código` entre crases (`<code>`) e o alinhamento de colunas em tabelas. O conversor avisa quando alguma destas coisas foi descartada; ler os avisos antes de enviar.

Proibido:
- entregar o `.md` ao utilizador para ele colar no Odoo;
- escrever o HTML do email à mão ou acrescentar-lhe `style`, `<div>` ou `<span>` — o conversor valida contra a lista branca do editor e falha se aparecer algo que não sobreviva à colagem.

Racional e evidência (paths no source do Odoo, lista branca de etiquetas e atributos, limitações): `.pg_framework/docs/PG_EMAIL_ODOO_FORMATTING.md`.

## Regras de redação em português europeu
Esta secção é obrigatória em toda a produção escrita destinada a leitura humana.

Regra principal:
- toda a produção escrita (markdown, comentários em código, docstrings, emails, propostas, pareceres, pontos de situação, orçamentos e qualquer documento formal) deve usar acentuação e cedilhas corretas de português europeu.

Proibições:
- não substituir caracteres acentuados pelos equivalentes ASCII: escrever "decisão" (e não `decisao`), "análise" (e não `analise`), "validação" (e não `validacao`), "critérios" (e não `criterios`), "dependências" (e não `dependencias`). Os contra-exemplos estão entre crases por serem literais ASCII propositados.
- não escrever em português sem acentos só porque o texto-fonte, um template ou outro ficheiro do repositório está em ASCII.

Regra de correção ativa:
- ao reformular, reescrever ou citar conteúdo previamente escrito sem acentos, o agente deve corrigir a acentuação e não perpetuar o erro.

Exceção única (manter o padrão do projeto, sem acentos):
- chaves técnicas, identificadores, nomes de campos, paths, slugs, nomes de ficheiros, comandos e código-fonte.

Verificação antes de fechar:
- antes de fechar um documento formal (parecer, proposta, email, ponto de situação), validar que não restaram palavras sem acento por inércia de redação em ASCII.

Nota de causa-raiz:
- a perda de acentuação acontece na geração de conteúdo pelo agente, não na conversão para `.docx` nem no encoding (os scripts escrevem em UTF-8; ver `.pg_framework/docs/PG_CONTENT_HYGIENE.md`). Logo, esta regra é a salvaguarda primária.

## Registo de consumo de tokens
Em cada sessão de trabalho num repositório elegível pela framework, o agente deve registar checkpoints em `.pg/tokens/consumption.jsonl`.

O registo deve ser acrescentado ao ficheiro (append), nunca substituir o conteúdo anterior.
Se o ficheiro não existir, criar em `.pg/tokens/consumption.jsonl`.

**Escrever sempre pelo `scripts/pg_log_token_consumption.ps1`, nunca compondo o JSON à mão.** O schema abaixo é para *leitura*; escrito à mão parte, porque o `repo_path` do Windows leva `\` e `\U`/`\D`/`\R` não são sequências de escape válidas em JSON — foi assim que um log real da frota ficou irreparavelmente inválido a meio. O script passa por `ConvertTo-Json`, que escapa corretamente.

Eventos obrigatórios por sessão:
- abrir sessão: `session_open`
- pelo menos um checkpoint intermedio quando houver trabalho material: `session_progress`
- fechar sessão quando aplicável: `session_close`

Uma sessão interrompida continua valida sem `session_close`, desde que tenha pelo menos `session_open`.

Schema mínimo por linha (JSONL, `schema_version` 1.3; 1.0 a 1.2 continuam aceites):
{"schema_version":"1.3","event_type":"session_open|session_progress|session_close","occurred_at_utc":"ISO-8601","session_id":"uuid","agent":"codex|claude|gemini","model":"nome-do-modelo","repo_name":"nome-repo","repo_path":"caminho-absoluto","machine":"PGBPINHEIRO","operator":"nome@parametro.global","session_summary":"resumo curto","estimated_input_tokens":0,"estimated_output_tokens":0,"cache_read_input_tokens":0,"cache_creation_input_tokens":0,"token_measurement":"estimated|measured|unknown","token_accounting":"unique_input_v2|cache_summed_v1|unknown","read_mode":"mirror|api|mixed|unknown","notes":"observações opcionais"}

**Quem fez a sessão.** O log é commitado no repositório e agrega todas as máquinas, mas até à v2.25.0 não dizia **quem**: o `repo_path` é idêntico em toda a frota e não havia campo de operador. Foi isso que obrigou a auditoria do givachoice a pedir extrações a colegas, máquina a máquina, para reconstruir decisões. `machine` é o discriminador fiável; `operator` é a identidade **declarada** no git e vale o que a configuração valer — na mesma auditoria, 205 commits de três pessoas saíam todos com o mesmo nome. Um diz onde; o outro diz quem se assumiu ser. Ambos são detetados automaticamente.

**O que conta como input (regra de contabilidade).** `estimated_input_tokens` é o volume de material **distinto** que entrou na sessão: entrada nova mais o que foi escrito no cache. As **releituras** do contexto a partir do cache vão para `cache_read_input_tokens` e **nunca** são somadas ao input — são o mesmo material lido outra vez em cada turno, pelo que somá-las dá *contexto × número de turnos*. Foi este o defeito, corrigido na v2.22.0: o log da frota chegou a declarar 3 676 354 561 tokens numa sessão e 204 milhões por sessão em modo `api`, várias ordens de grandeza acima do possível, e a comparação espelho-vs-API media sobretudo a duração das sessões. Os registos anteriores à v2.22.0 não trazem `token_accounting`, não são comparáveis entre si e ficam fora da métrica-alvo; o log é *append-only* e não se reescreve.

Regras:
- `session_summary` é obrigatório em `session_progress` e `session_close`
- `estimated_input_tokens` e `estimated_output_tokens` devem ser inteiros >= 0; com valores reais do runtime, marcar `token_measurement:"measured"`
- no `session_close`, obter os tokens **reais** a partir do readout de uso do runtime do agente (ex.: comando `/cost` no Claude Code; equivalente no Codex) e registar com `token_measurement:"measured"` — é isto que torna a medição fiável em vez de simbólica
- `read_mode` distingue leitura barata do espelho (`mirror`) de acesso direto à API do Odoo (`api`); é obrigatório e é a base para provar a redução de custo/tempo (comparar tokens/sessão por modo)
- quando não for possível obter valores reais, estimar e marcar `estimated`; só registar `0`/`unknown` como último recurso, justificando em `notes`
- `session_id` deve ser reutilizado em todos os eventos da mesma sessão. O `pg_log_token_consumption.ps1` só gera id novo no `session_open`; num `session_progress`/`session_close` sem `-SessionId` reutiliza a última sessão aberta do mesmo agente e, se não existir nenhuma, **falha** em vez de criar uma sessão órfã (que seria um defeito permanente, por o log ser append-only)

Registo automático (recomendado):
- o `.claude/settings.json` do projeto regista o hook `scripts/pg_hook_log_token_consumption.ps1` em `SessionStart` e `SessionEnd`; o `session_open`/`session_close` passam a ser escritos **automaticamente**, sem intervenção
- os tokens do `session_close` vêm do transcript do runtime e são **aproximados** (`token_measurement:"estimated"`) e o `read_mode` é **heurístico**; para custo autoritário usar o dashboard/limites da conta Anthropic. O hook escreve `token_accounting:"unique_input_v2"` e regista as releituras de cache em campo próprio
- na 1.ª sessão de cada repo, o Claude Code pede autorização (workspace trust) para executar o hook
- **Codex:** o `.codex/hooks.json` regista `scripts/pg_hook_codex_log_token_consumption.ps1` em `SessionStart` e `Stop` (o Codex não tem `SessionEnd`). Os tokens vêm do *rollout* real da sessão (`~/.codex/sessions/.../rollout-*.jsonl`), por isso ficam `token_measurement:"measured"`; como o `Stop` dispara por turno, o `session_close` é feito por *upsert* (um por `session_id`, com o total cumulativo). **Requer a feature experimental de hooks do Codex** (`[features] hooks = true` no `config.toml`) e uma versão recente do `codex` — `PONTO POR VALIDAR` na instalação de cada máquina

Scripts (uso manual / afinação, quando o automático não chega):
- `scripts/pg_log_token_consumption.ps1` para append de eventos (aceita `-TokenMeasurement measured` e `-ReadMode mirror|api|mixed`) — usar com valores reais do `/cost` quando for preciso um número exato
- `scripts/pg_validate_token_consumption.ps1` para validar formato e consistência
- `scripts/pg_report_token_consumption.ps1` para agregar consumo por projeto/agente/modelo e comparar tokens/sessão por modo de leitura (`-RepoPath` ou `-RootPath`). A métrica-alvo é calculada **apenas** sobre registos `unique_input_v2`; sessões acima de 20 milhões de tokens ficam em quarentena, fora de todas as médias, por serem erro de contagem e não sessões pesadas
