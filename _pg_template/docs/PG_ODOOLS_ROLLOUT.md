# PG OdooLS Rollout

## Objetivo

Disponibilizar navegacao Odoo-aware em Python, XML, CSV e manifests sem carregar repositorios inteiros no contexto dos agentes.

## Componentes

- `scripts/pg_setup_odools.ps1`: valida source/versao, descobre addon roots e gera `odools.toml` local.
- `scripts/pg_rollout_odools_orgwide.ps1`: audita por omissao; `-Apply` configura repositorios elegiveis.
- `scripts/pg_odools_query.py`: cliente LSP limitado para consultas deliberadas de simbolos.
- `scripts/pg_test_odools_setup.ps1`: testes deterministas do gerador.
- `templates/.agents/skills/pg-odoo-navigator/`: skill comum, sincronizada para agentes e Claude.

`odools.toml` e `.pg/odools/` sao locais e ignorados pelo Git. O primeiro contem paths absolutos da maquina; nao deve ser versionado.

## Operacao

Instalar a extensao oficial no posto de trabalho:

```powershell
code --install-extension Odoo.odoo
```

Auditar todos os repositorios:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pg_rollout_odools_orgwide.ps1 -RootPath C:\Projetos
```

Configurar os elegiveis:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pg_rollout_odools_orgwide.ps1 -RootPath C:\Projetos -Apply
```

Configurar ou validar um repositorio:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pg_setup_odools.ps1 -RepoPath C:\Projetos\GLC
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pg_setup_odools.ps1 -RepoPath C:\Projetos\GLC -CheckOnly
```

## Resultado do piloto de 2026-08-17

- extensao oficial `Odoo.odoo` 1.2.1 instalada e binario Windows detetado
- 53 de 58 repositorios de cliente configurados
- 5 bloqueados por falta de `vendor/odoo_src`: `domusacropoles`, `Essani`, `hodoosh`, `Private-Label`, `Roliband`
- piloto funcional em `GLC`: OdooLS devolveu classes/modelos Python e XML IDs de Community e Enterprise com `file:line`
- primeira indexacao completa: aproximadamente 278 segundos
- novo processo nao ficou pronto em 120 segundos apesar de `file_cache=true`

Conclusao operacional: usar OdooLS como servidor persistente do IDE. O cliente CLI e valido para uma consulta deliberada, mas nao deve ser arrancado repetidamente numa tarefa. A bridge persistente para agentes permanece uma fase posterior e a reducao de tokens ainda exige A/B medido.

## Medicao A/B

Os hooks passam a gravar `navigation_mode=odools` quando o transcript usa `pg_odools_query`, `odoo_ls_server` ou OdooLS; caso contrario gravam `native`. O relatorio agrega um unico close cumulativo por sessao, em vez de contar `SessionStart` e `session_close` como modos separados.

Executar pelo menos dez tarefas comparaveis por modo e comparar tokens por sessao, tempo total e correcao. A baseline historica continua fraca: depois da correcao do parser, apenas cerca de 0,3% dos tokens existentes estao marcados como medidos; a maioria Claude e estimada a partir do transcript. Usar o dashboard do fornecedor como fonte autoritativa de custo.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pg_report_token_consumption.ps1 -RootPath C:\Projetos
```

## Gates

- Nunca gerar configuracao sem source e versao resolvidos.
- Nunca substituir um `odools.toml` manual sem `-Force`.
- Nunca aquecer todos os repositorios em paralelo.
- Tratar resultados como navegacao; ler o source final antes de decidir ou editar.
- Manter fallback `rg` limitado quando o cold start for desproporcionado.
