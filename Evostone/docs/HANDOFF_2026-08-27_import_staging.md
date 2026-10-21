# HANDOFF — 2026-08-27 — Importacao da base do cliente no Odoo.sh (staging)

> Documento de passagem de sessao. Escrito por Claude Code no fim de uma sessao
> longa, para o agente seguinte continuar sem repetir investigacao.
> Projeto: **Odoo - EVOSTONE**, `project_id` 316, `project_key`
> **`odoo-padrao-magistral`** (imutavel; e' este projeto — ver PG_CONTEXT).

---

## 1. Onde parou — o passo imediato

O zip de importacao **esta pronto e correcto** no contentor de staging:

```
/home/odoo/odoosh_import_dump.zip        40,5 MB
  dump.sql        396 909 047 B   (378,5 MB de SQL simples)
  filestore/      0 B             (directorio VAZIO — obrigatorio, ver 5.2)
  manifest.json    13 304 B       (322 modulos installed listados)
```

**Accao seguinte, do utilizador no painel:**
`Branches` → `staging` → `BACKUPS` → `Import Database` → `Next` → `Through SSH` → `Import`

**Logo depois, verificar (nao confiar na cor do resultado no painel):**

```powershell
ssh -i $K $H "cat ~/logs/odoosh-import-database.log"
ssh -i $K $H "psql -c 'select count(*) from ir_module_module where state = ''installed'';'"
```

**Se der 322, a importacao correu.** Depois disso, correr a verificacao completa
(secao 4).

---

## 2. Ambiente

### Odoo.sh — projeto `parametroglobaladmin-evostone`, serie 18.0

| Ramo | Estagio | Estado |
|---|---|---|
| `main` | Production | so `README.md`. **INTOCADO. Nao fazer merge nem importar para aqui** (ver 6.1) |
| `staging` | Staging | commit `cc7fcbb`, 47 modulos do cliente. E' aqui que se trabalha |
| `brodoo` | Development | framework/espelho, 0 modulos. *Behavior upon new commits* = **Do nothing** |

- `staging` → *Behavior upon new commits* = **Update previous build** (preserva a
  base entre commits; **nao mudar para "New build"**, que a recria da producao vazia).
- **Trial com codigo de parceiro: o projeto e' APAGADO, nao rebaixado.** Aviso do
  painel a 27/08: 29 dias → destruicao por volta de **2026-09-25/26**.
- Build de staging tem validade ate **26/09/2026**.

### Restricao de espaco — medida, nao estimada

```
/                1.2T  638G livres   <- do HOST, NAO utilizavel
/home/odoo       994M  ~830M livres  <- quota real
/tmp             994M  ~830M livres  <- MESMA quota
```

Todas as vias gravaveis partilham **uma quota de ~993 MB**. E **`/tmp` e' efemero**:
um reinicio de contentor apagou de la o `.dump` a meio desta sessao. **Usar sempre
`/home/odoo`.**

### Acesso SSH

- Chave: `~/.ssh/id_odoosh` (ed25519, com passphrase, carregada em `ssh-agent`).
  Fingerprint MD5 `af:69:be:65:40:e2:90:ea:dc:87:b5:a4:46:81:a7:c1`.
  Registada em *Change My Profile* → *SSH Keys* do Odoo.sh (nao no GitHub).
- Host: `37070347@parametroglobaladmin-evostone-staging-37070347.dev.odoo.com`

```powershell
$K = "$env:USERPROFILE\.ssh\id_odoosh"
$H = "37070347@parametroglobaladmin-evostone-staging-37070347.dev.odoo.com"
```

**Tres regras aprendidas a custa de erros:**

1. **`scp` exige `-O`** (maiusculo). Sem ele: `subsystem request failed on channel 0`
   — o contentor nao expoe o subsistema SFTP, que e' o que o OpenSSH >= 9.0 usa por
   omissao.
2. **Comandos remotos:** `ssh -i $K $H "<comando linux>"`, aspas exteriores duplas e
   interiores simples. **Sem `$`, sem `\"`, sem ciclos `for`** — o PowerShell
   estraga-os. Se precisar de mais, mandar um script por `scp` e executa-lo.
3. **PowerShell:** `"${H}:/path"` com chaves obrigatorias. `"$H:/path"` e' lido como
   variavel `H:` e parte. E o `~` nao e' expandido pelo OpenSSH do Windows — usar
   `"$env:USERPROFILE\.ssh\..."`.

---

## 3. Ficheiros de trabalho

### Na maquina local — `C:\tmp\evo_backup\`

| Ficheiro | O que e' |
|---|---|
| `stone-main-2026-08-24.dump` | 49,85 MB. Dump PostgreSQL **custom**, magic `PGDMP`, formato 1.14.0, servidor 15.6 Debian, base `stone-trading-mhc-main-090126` |
| `stone-filestore-2026-08-24.tar.gz` | 1735 MB. **Nao importado** (ver 6.2). Conteudo sob `stone-trading-mhc-main-090126/` |
| `stone-backup-2026-08-24.tar` | 1785 MB. O pacote nativo, com os dois acima |
| `evo_import_prep.sh` | Guiao que constroi o zip **no contentor**. Validado |
| `evo_verificacao.sql` | 7 consultas de verificacao pos-restauro. Validado contra o schema 18.0 |
| `odoosh-import-database` | Copia do importador da plataforma (251 linhas, Python). Fonte das conclusoes da secao 5 |

Origem de tudo: `C:\Users\Utilizador\Downloads\Stone Trading.zip` (1,87 GB), entrega
de Cleve Chambule, tarefa Odoo **#7239**, backup de 2026-08-24.

### Worktree de codigo — `C:\tmp\Evostone-staging`

Branch `staging`. Existe para o `Repos\Evostone` continuar em `brodoo`, como o ritual
exige. Os 47 modulos do cliente estao aqui e no ramo remoto.

### No contentor — `/home/odoo/`

`evo_import_prep.sh`, `stone-main-2026-08-24.dump`, `odoosh_import_dump.zip`,
`odoosh_import_dump.zip.bak` (versao antiga **sem** `filestore/` — inutil, apagar).

---

## 4. Verificacao a correr depois da importacao

```powershell
Set-Location C:\tmp\evo_backup
scp -O -i $K evo_verificacao.sql "${H}:/home/odoo/"
ssh -i $K $H "psql -f /home/odoo/evo_verificacao.sql > /home/odoo/evo_resultado.txt 2>&1; wc -l /home/odoo/evo_resultado.txt"
scp -O -i $K "${H}:/home/odoo/evo_resultado.txt" .
```

| Consulta | O que responde | Criterio |
|---|---|---|
| **Q6** | empresa, moeda, pais fiscal | tem de dar `STONE TRADING` / `MZN` / `MZ`. Se nao, parar |
| **Q1 / Q1b** | estado dos 47 modulos entregues | `installed` = replica; `to upgrade`/`uninstalled` = ha trabalho |
| **Q4 / Q4b** | os 4 modulos sem codigo no repo | esperado: `installed` sem codigo em disco |
| **Q5** | dimensao dos orfaos em `ir_model_data` | dimensiona a limpeza |
| **Q2** | **colisao de `key`** em `studio_customization` | e' aqui que se espera problema (ver 5.5) |
| **Q3** | os 8 templates que o `mh_stone_reports` invoca | devem existir **agora** que ha dump |
| **Q7** | cron de imposicao de licenca da Make It Happen | ver 6.3 |

Depois: limpeza de orfaos. O pacote `Repos\odoo-migration` tem `triage_orfaos.py`
em `1_migracao_bd/config/` e `2_migracao_modulos/ferramentas/`.

---

## 5. Achados desta sessao — nao repetir a investigacao

### 5.1 `pg_restore` 16 exige `-f -` para escrever em stdout
O contentor tem `pg_restore 16.15`. Nessa serie ja **nao** escreve para stdout por
omissao: `error: one of -d/--dbname and -f/--file must be specified`. O guiao usa
`-f -` explicito.

### 5.2 O importador do Odoo.sh EXIGE `filestore/`, mas aceita-o VAZIO
Lido em `/opt/odoo.sh/odoosh/bin/odoosh-import-database` (copia local em
`C:\tmp\evo_backup\odoosh-import-database`):

- **linha 58**: espera `<temp>/filestore` (formato do `/web/database/manager`)
- **linha 60**: se `dump.sql` **ou** `filestore` faltarem, cai no ramo
  «Odoo.sh plain backup format», onde exige `<nome>.sql.gz` — que nao temos
- **linha 216**: com `filestore/` presente e **vazio** → registra
  *«Imported filestore is empty, leaving current one»* e **prossegue**
- Descomprime com **`unzip` do shell**, que materializa entradas de directorio
  vazias. Testado localmente com o `unzip` real, funciona.

Como se cria a entrada (esta no guiao):
```python
zi = zipfile.ZipInfo('filestore/')
zi.external_attr = (0o40755 << 16) | 0x10
z.writestr(zi, b'')
```

### 5.3 Duas armadilhas de leitura no script da plataforma
- **Mensagens trocadas** (linhas 76/78): `if not os.path.exists(sql_gz_dump): raise
  InvalidDumpError("Missing filestore ...")`. O erro *«Missing filestore»* que
  recebemos significava de facto **falta do `.sql.gz`**.
- **`returncode = 3`**: se o `psql` escrever para `stderr` fora da lista branca, o log
  diz *«Import completed successfully, but the following issues were encountered»* **e**
  a linha final escreve *«Finished with error(s)»*. **Um `Failed` no painel pode ser
  base restaurada com avisos benignos.** A lista branca cobre propriedade das
  extensoes `pg_trgm`, `unaccent`, `vector` e `permission denied for database`.
- O importador **apaga a base antes de restaurar** (`DROP TABLE` a tudo em `public`).

### 5.4 Campos que nao tem coluna — verificar sempre a definicao
- **`res_company.country_id`** e' `compute` **sem** `store` → **nao existe coluna**.
  Usar `res_company.partner_id` → `res_partner.country_id`. O pais **fiscal** e'
  `res_company.account_fiscal_country_id` (compute **com** store, tem coluna).
- `res_company.name` e' `related` **com** `store=True` → tem coluna.
- `res_company.vat` e' `related` **sem** store → nao tem.
- **`ir_module_module.imported`** vem de `base_import_module`, nao do `base`.
- **`ir.cron`** delega em `ir.actions.server`: o campo `code` vive em **`ir_act_server`**,
  nao em `ir_cron`. Precisa de `JOIN ... ON s.id = c.ir_actions_server_id`.

### 5.5 `mh_stone_reports` depende de dados que so existem na base
- Faz **8 `t-call` para templates no namespace `studio_customization`**
  (`studio_report_docume_<uuid>_document` e variantes `_copy_N`). **Nenhum esta
  definido no pacote** — existem so como `ir_ui_view` na base.
- **Cria 9 `ir_ui_view` com `key` nesse mesmo namespace.** Restaurado o dump, essas
  chaves **ja existem** → risco de **chave duplicada**, que o QWeb resolve por `key`.
  **E' o candidato mais provavel a primeira falha real.** Q2 e Q3 medem isto.

### 5.6 Defeito latente corrigido — `mh_stock_at_date` (commit `cc7fcbb`)
Build falhou com `AssertionError: The ID "stock_account.menu_valuation" refers to an
uninstalled module` em `views/stock_menus.xml:17`. O modulo escreve em registos de
`stock_account` e `stock_enterprise` pela forma `<record id="modulo.xid">` sem os
declarar em `depends`. Escrever assim exige que o modulo esteja `installed` no momento
da leitura (`odoo/tools/convert.py:237`). Corrigido: `depends` passa a
`['stock', 'stock_account', 'stock_enterprise']`. **Verificados os 47 modulos: zero
outras escritas cruzadas sem dependencia.**

> Ressalva: o `Test: Success` do build de `cc7fcbb` **nao prova** a correccao — em
> Staging os builds partem da producao vazia e nao exercitam a instalacao a partir do
> grafo. A prova vem de um `-u` sobre a base restaurada.

### 5.7 Conjunto real de instalacao: 196 modulos, nao 110
O fecho das `depends` dos 47 da 110. Com os `auto_install` cujas dependencias ficam
satisfeitas, sobe. O nucleo filtra os `auto_install` especificos de pais
(`ir_module.py:419-429`: `not module.country_ids or module.country_ids & company_countries`).

| Cenario | Total |
|---|---|
| base sem pais | **196** (110 declarados + 86 auto_install) |
| com a empresa MZ do dump | 198 (`l10n_mz`, `l10n_mz_reports`) |
| MZ + PT | 201 (`l10n_pt`, `l10n_pt_reports`) |

**Consequencia de ambito:** o entregavel da fase 1 diz «sem transformacao fiscal, sem
PT+ no dia 1». O PT+ fica fora, mas **`l10n_pt` e `l10n_pt_reports` auto-instalam-se
no momento em que existir uma empresa portuguesa.**

### 5.8 Riscos que CAEM de ambito com o alvo em 18.0
Verificado no source 18.0 local. Eram itens da migracao para 19:
- `res.users.groups_id` **existe** em 18.0 (`res_users.py:386`). O sweep das 12 regras
  de registo e 14 ocorrencias de codigo **nao se aplica**.
- `stock.valuation.layer` e `procurement.group` **mantem os nomes**.
- `account_auto_transfer` **existe** no enterprise 18.0; a dependencia do `mh_account`
  resolve.
- O dump e' da **propria serie 18** → **restauro, nao upgrade de serie**.

### 5.9 `account_invoice_constraint_chronology` — msgid traduzidas no codigo
Modulo OCA (AGPL-3, 18.0.1.0.1). As *msgid* foram **reescritas em portugues
directamente no codigo** (`model/account_move.py`, quatro `raise UserError`), com os
testes do OCA intactos em ingles. **2 falhas em 11 testes, em todos os builds.**
Nao bloqueia (testes dao *Warning*), mas mascara falhas futuras.
`PONTO POR VALIDAR` — alinhar os testes com o portugues (rapido, consolida a pratica
errada) ou restaurar as msgid inglesas e por o portugues em `i18n/pt_PT.po` (correcto).

### 5.10 `remove_odoo_enterprise` e' legitimo
Modulo OCA (`OCA/server-brand`, AGPL-3, Eska/Onestein). Apenas filtra os modulos
`to_buy` da lista de Apps. **Nao contorna licenciamento**, nada a ver com os portoes
da Make It Happen. Nota menor: num Enterprise com subscricao pode esconder apps
legitimas — reavaliar utilidade mais tarde.

---

## 6. Dividas e bloqueios abertos

### 6.1 Ratificacao — trava o merge para producao
A decisao de **assumir a proveniencia do software** (Bruno Pinheiro, 2026-08-27) esta
**por ratificar por Claudio Pereira a 2026-08-31**. Ate la: nada irreversivel nem
virado para o exterior sobre esta base. **O merge `staging` → `main` e a importacao
para producao nao devem acontecer antes disso.**

### 6.2 O filestore nao foi importado — precisa de aumento de quota
1735 MB nunca cabem na quota de 993 MB, e depois da importacao passaria a viver em
`/home/odoo/data/filestore/<base>`. **Consequencia concreta:** anexos, logotipos,
imagens de artigos e PDFs vao dar erro ao abrir; os registos `ir_attachment` estao la,
falta o conteudo binario.

Irrelevante para a validacao da base. **Incontornavel antes de qualquer demonstracao
ou UAT.** Orcamento para o pedido (`Settings` do projeto): zip com filestore ~1,8 GB +
descompressao temporaria ~2,1 GB + filestore restaurado ~1,7 GB = **pico ~5,6 GB**.
**Pedir 15 GB.**

### 6.3 Cron de imposicao de licenca da Make It Happen
Cron diario (id 138) que executa `action_sync_and_enforce()`, com assinatura a expirar
em 2027-01-09. O codigo (`mh_licenses`, `mh_subscription`) esta **deliberadamente
excluido** do repositorio, mas **o registo do cron vem no dump**. Em staging **nao
corre** — a importacao neutraliza (*«mail servers and scheduled actions are disabled by
default»*, confirmado no dialogo do Odoo.sh). **Mas em producao corre.** Q7 localiza-o;
desactivar antes de qualquer ida a producao.

### 6.4 `brodoo` a saturar o limite de builds — problema de FRAMEWORK
O primeiro push da `staging` teve o **webhook recusado**: *«the number of simultaneous
builds exceeded the limit allowed for this trial subscription»*. Webhooks recusados
**nao sao reprocessados** — foi preciso `Rebuild` manual.

Causa: o `brodoo` estava em Development e **nao tem um unico `__manifest__.py`** (155
ficheiros, 0 modulos). O Odoo.sh construia um container Odoo completo para ele, e o
**bot de sincronizacao do espelho faz-lhe push varias vezes por dia** (12 commits
`chore(pg-sync)`/`chore(pg-mirror)` numa unica sessao). Mitigado com *Behavior upon
new commits* = **Do nothing**.

**⚠️ NAO usar `Delete` no `brodoo`:** no Odoo.sh apagar uma branch apaga-a tambem do
GitHub, e o `brodoo` leva a historia da framework e do espelho (718+ commits).

`PONTO POR VALIDAR` — **isto afecta a frota, nao so este projeto.** Qualquer
repositorio com `brodoo` vigiado pelo Odoo.sh tem a mesma situacao (`sofmovelsh`,
`odoosh`). O modelo «um repositorio por projeto, `brodoo` ao lado do `main`» precisa de
regra explicita para o Odoo.sh.

### 6.5 Higiene
- **`Repos\PadraoMagistral` local ainda existe** e corre o ritual sem nada assinalar
  que e' o repositorio errado (checkout passa, preflight passa). A mitigacao efectiva
  e' apagar a pasta.
- **`_pg_template` tem alteracoes locais nao commitadas**, pelo que o
  `git pull --ff-only` da framework e' ignorado a cada arranque.
- **`Revision: Latest`** na `staging`: o nucleo do Odoo actualiza sozinho toda a semana.
  Correcto nesta fase (patches de seguranca). **Decidir se se fixa a revisao antes de
  UAT e go-live** — um comportamento que muda entre semanas e' dificil de atribuir.
- **PG_CONTEXT precisa da entrada deste ciclo** (importacao, achados 5.1 a 5.5, divida
  6.2). As entradas anteriores de 2026-08-27 estao la.

---

## 7. Contexto de fundo, em tres linhas

O entregavel da fase 1 e' **replica, nao transformacao**: criar o projeto Odoo.sh 18.0,
restaurar o dump tal e qual, instalar os modulos entregues, limpar orfaos, subscricao
activa. Sem transformacao fiscal, sem troca de plano de contas, sem PT+ no dia 1.
A `STONE TRADING` mocambicana fica intacta; a `EVOSTONE Portugal` nascera como empresa
**nova na mesma base**, mais tarde. O detalhe completo esta no `PG_CONTEXT.md`, secao
«Historico de marcos de decisao», entradas de 2026-08-25 a 2026-08-27.
