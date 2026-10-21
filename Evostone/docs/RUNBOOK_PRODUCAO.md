# RUNBOOK — Levantar a base do cliente em PRODUÇÃO

> Projeto **Odoo - EVOSTONE** (`project_id` 316). Escrito a 2026-08-28, depois de a
> sequência inteira ter sido executada uma vez em `staging`. Tudo o que está aqui foi
> feito e verificado; nada é teórico.
>
> Estimativa: **meio dia**, se as pré-condições estiverem cumpridas.

---

## Pré-condições — todas obrigatórias

| | Dono | Estado |
|---|---|---|
| Ratificação da decisão de proveniência | Cláudio Pereira | 31/08 |
| Subscrição Odoo activa para o NIF 516617770 | Cláudio / Paula | depende da cotação do Gestor de Conta do cliente |
| **Projeto Odoo.sh activado** com o código de subscrição — deixa de ser trial | Cláudio / Paula | sem isto o projeto é apagado ~25/09 |
| Armazenamento dimensionado: **≥ 8 GB livres** no contentor de produção | Cláudio / Paula | o filestore **descomprimido são 2421 MB** em 20 791 ficheiros; somando o zip, a extracção temporária e o filestore restaurado, o pico anda pelos 5–6 GB |
| Decisão sobre as duas colunas em falta (Passo 6) | gestor de projeto | ver o próprio passo |

**Se a subscrição não estiver activa, não começar.** Importar para um projeto em trial
repete o trabalho quando o projeto for apagado.

---

## Materiais, já preparados

| Ficheiro | Onde | O quê |
|---|---|---|
| `odoosh_import_dump_producao.zip` | `C:\tmp\evo_backup\` | `dump.sql` (396 909 047 B) + `filestore/` (20 791 ficheiros) + `manifest.json` com os 322 módulos, já no formato que o importador exige |
| `evo_verificacao.sql` | idem | 7 consultas de verificação pós-restauro |
| `evo_relatorios_sweep.py` + `evo_sweep_run.sh` | idem | varrimento dos 49 relatórios |
| `evo_vistas_sweep.py` | idem | validação das vistas |
| `evo_smoke_test.py` | idem | teste funcional sobre registos reais |
| `evo_cleanup_orphans.py` | idem | limpeza dos 3 módulos sem código |

Os guiões lêem `PGDATABASE` do ambiente, por isso são portáveis de staging para
produção sem alteração.

---

## Passo 1 — Fusão `staging` → `main`

Verificado: `main` é ancestral de `staging`, logo é *fast-forward* e não há conflitos
possíveis.

```powershell
cd C:\tmp\Evostone-staging
git fetch origin
git push origin origin/staging:main
```

Confirmar que `main` passou a ter os módulos e não só o `README.md`.

## Passo 2 — Enviar o zip para o contentor de produção

O host SSH de produção é **diferente** do de staging — tem outro número de build.
Obtê-lo no botão **SSH** da branch `main` no painel.

```powershell
$K = "$env:USERPROFILE\.ssh\id_odoosh"
$H = "<build_id>@<host-de-producao>"      # do botão SSH da branch main
scp -O -i $K C:\tmp\evo_backup\odoosh_import_dump_producao.zip "${H}:/home/odoo/odoosh_import_dump.zip"
```

⚠️ O `-O` é obrigatório: o contentor não expõe subsistema SFTP, e sem ele o `scp`
falha com `subsystem request failed on channel 0`.

⚠️ **A via do browser não serve aqui.** O diálogo de importação limita-a a 2 GB e este
zip passa disso. O SSH deixa de ser preferência e passa a ser o único caminho — o que
torna a chave SSH registada no perfil uma pré-condição, não uma conveniência.

Guardar uma cópia antes de importar, porque o importador consome o ficheiro:

```powershell
ssh -o BatchMode=yes -i $K $H "cp /home/odoo/odoosh_import_dump.zip /home/odoo/odoosh_import_dump.zip.bak; df -h /home/odoo | tail -1"
```

## Passo 3 — Importar

Painel: `Branches` → **`main`** → `BACKUPS` → `Import Database` → `Next` →
`Through SSH` → **`Import`**.

## Passo 4 — Verificar a importação

**Não confiar na cor do resultado no painel.** Ler o log:

```powershell
ssh -o BatchMode=yes -i $K $H "cat ~/logs/odoosh-import-database.log"
ssh -o BatchMode=yes -i $K $H "psql -c 'select state, count(*) as n from ir_module_module group by state order by n desc'"
ssh -o BatchMode=yes -i $K $H "psql -c 'select c.id, c.name, cur.name as moeda from res_company c join res_currency cur on cur.id = c.currency_id'"
```

Critérios: **322 módulos `installed`**, empresa `STONE TRADING`, moeda `MZN`.

Erros esperados e benignos no log: duas mensagens sobre a extensão `dblink`, que o
Odoo.sh não permite criar sem superutilizador.

## Passo 5 — Limpeza dos órfãos

Três módulos estão `installed` na base sem código no repositório. Desinstalar pela via
nativa (`ir.model.data._module_data_uninstall`), **nesta ordem**, que é imposta por
dependência:

1. `mh_licenses`
2. `mh_subscription`
3. `auto_database_backup`

⚠️ **Não apagar registos por SQL.** O `mh_licenses` estende `res.users` e o
`mh_subscription` estende `ir.http` e `res.config.settings`; a via nativa preserva o
que ainda pertence a outros módulos e remove tabelas, colunas e restrições do módulo
desinstalado. Usar `evo_cleanup_orphans.py`.

⚠️ **`studio_customization` fica de fora.** Tem 1.667 registos de metadados e é a
camada Studio instalada, não um órfão descartável.

Depois desta limpeza a base fica com **319** módulos.

## Passo 6 — As duas colunas em falta

O dump é o mesmo, portanto produção reproduz o defeito de staging: dois campos
declarados como armazenados no código sem coluna na base.

| Campo | Tabela |
|---|---|
| `mh_show_in_dashboard` | `account_journal` |
| `manual_currency_rate_label` | `account_payment` |

**Opção A — DDL directo** (o que se fez em staging; rápido):

```sql
ALTER TABLE account_journal ADD COLUMN IF NOT EXISTS mh_show_in_dashboard boolean;
ALTER TABLE account_payment ADD COLUMN IF NOT EXISTS manual_currency_rate_label varchar;
```

Verificado que nenhum dos dois campos tem `index` nem constraint, pelo que isto é
equivalente ao que o `_auto_init` faria. As colunas nascem `NULL` e nenhuma linha é
alterada.

Deixa o `ir_model_fields` desalinhado (continua a marcar os campos `store=f`) e o
`mh_account` continua não actualizável.

**Opção B — corrigir e actualizar o módulo** (resolve de vez):

Requer primeiro remover o botão morto de
`mh_account/wizard/resequence_assistant_views.xml:29`, que chama `action_run` num
modelo que não tem métodos. Sem isso, `odoo-update mh_account` falha com `ParseError`
e a registry não carrega — a transacção reverte, mas o módulo não actualiza.

Feito isso, subir a versão no manifesto e deixar o Odoo.sh actualizar.

⚠️ Uma actualização do `mh_account` faz mais do que criar colunas: executa os
`<delete>` de `data/cleanup_advance_views.xml` (remove vistas, acções e menus de
adiantamentos) e recarrega `data/mail_template_data.xml`, que tem `noupdate="0"` e dois
templates de email — quaisquer edições feitas pelo interface são revertidas.

## Passo 7 — Verificação final

```powershell
scp -O -i $K C:\tmp\evo_backup\evo_verificacao.sql "${H}:/home/odoo/"
ssh -o BatchMode=yes -i $K $H "psql -f /home/odoo/evo_verificacao.sql > /home/odoo/verif.txt 2>&1"
scp -O -i $K "${H}:/home/odoo/verif.txt" C:\tmp\evo_backup\
```

E os varrimentos, que precisam do `addons_path` explícito porque o `odoo.conf` do
Odoo.sh **não o declara** — a plataforma injecta-o em execução, e sem ele o
`odoo-bin shell` não vê o enterprise nem os módulos do cliente:

```
/home/odoo/src/user,/home/odoo/src/enterprise,/home/odoo/src/themes,/home/odoo/src/odoo/addons,/home/odoo/src/odoo/odoo/addons
```

Referência medida em staging, para comparar:

| Verificação | Esperado |
|---|---|
| Relatórios | 32 de 49 OK (34 se a Opção B do Passo 6 for feita) |
| Vistas não-QWeb | 169 de 169 |
| Acções órfãs | 0 |
| Smoke test | PASS, com 3 PDF gerados sobre registos reais |

Com o filestore presente — ao contrário de staging — os PDF passam a sair **com
logótipo e imagens**, e os 2400 PDF de faturas emitidas passam a abrir.

## Passo 8 — Utilizadores

Criar os utilizadores do cliente. Pendência registada: **8 utilizadores na cotação
contra 5 confirmados** à Parâmetro. Reconciliar antes de criar.

---

## Armadilhas conhecidas

Tudo isto custou tempo a descobrir. Não voltar a descobrir.

| Armadilha | O que fazer |
|---|---|
| **`Rebuild` numa branch de Staging destrói a base** — um build novo nasce com cópia da produção | Nunca clicar `Rebuild` depois de importar |
| *Behavior upon new commits* = `New build` recria a base a cada commit | Manter em **`Update previous build`** |
| `scp` falha com `subsystem request failed on channel 0` | Usar **`-O`** maiúsculo |
| Comandos remotos com `$`, `\"` ou ciclos `for` são estragados pelo PowerShell | Mandar um script por `scp` e executá-lo |
| `"$H:/path"` em PowerShell é lido como variável `H:` | Escrever **`"${H}:/path"`** |
| `~` não é expandido pelo OpenSSH do Windows | Usar `"$env:USERPROFILE\.ssh\..."` |
| **`/tmp` do contentor é efémero** — apagou-nos o dump num reinício | Trabalhar sempre em `/home/odoo` |
| `pg_restore` 16 não escreve para stdout por omissão | Usar **`-f -`** explícito |
| O importador exige `filestore/` no zip, mesmo vazio | O zip de produção já o traz com conteúdo |
| `returncode 3` diz *"Finished with error(s)"* **depois** de dizer *"Import completed successfully"* | Ler o log, não a cor |
| Mensagens de erro trocadas no importador: *"Missing filestore"* quer dizer falta o `.sql.gz` | Ler o código em `/opt/odoo.sh/odoosh/bin/odoosh-import-database` |
| `odoosh-restart` sem argumento imprime a ajuda e não faz nada; recusa se nenhum trabalhador estiver vivo | `odoosh-restart http` |
| Ícones e imagens vivem no filestore, e o `load_menus` embute-os num payload em cache | Depois de mexer no filestore, `odoosh-restart http` |

---

## Depois de produção estar de pé

Não é parte deste runbook, mas fica registado para não se perder:

- **`pg_evostone_multicompany`** — módulo já no repositório, **não instalado**. 19 regras
  de registo multiempresa. Instalar **antes** de criar a `EVOSTONE Portugal`, senão a
  valorização da empresa portuguesa pode ler lotes moçambicanos sem produzir erro.
- **Três relatórios continuam com falha**, todos caracterizados: o de pendentes de conta
  corrente do `account_MZ` (quebrado na origem, liga-se à tarefa #7244), a folha de
  salários `_copy2` (template Studio a referenciar campo removido no Odoo 17), e as
  etiquetas (exigem IoT Box).
- **O cron de imposição de licença da Make It Happen** vem no dump. Em staging não corre
  porque a importação neutraliza; **em produção corre.** Localizar com a Q7 do
  `evo_verificacao.sql` e desactivar.
