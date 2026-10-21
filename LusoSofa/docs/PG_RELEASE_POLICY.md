# PG_RELEASE_POLICY

## Objetivo
Este documento define quando e como o `_pg_template` passa de alterações em curso para uma release utilizável como baseline.

Não e um documento conceptual.
E a regra operacional mínima para publicar versões estáveis da framework.

## Principios

- o `_pg_template` e a source of truth
- nenhuma alteração transversal fica apenas em repositórios piloto
- uma release só existe quando houver commit, changelog, tag e critério de fecho explicito
- `main` pode continuar a evoluir, mas a baseline recomendada para adoção deve ser sempre identificável por tag

## Tipos de versão

- `v2.x.y`:
  - `x` muda quando ha mudança estrutural relevante na framework
  - `y` muda quando ha melhoria incremental compatível
- exemplos:
  - `v2.4.4` = baseline validada de piloto
  - `v2.4.6` = endurecimento compatível sem quebra estrutural
  - `v2.5.0` = nova iteração fechada com objetivo próprio

## Quando promover uma release

Uma release do `_pg_template` deve ser promovida quando:

- o objetivo da iteração esta implementado
- os documentos centrais estão coerentes
- o working tree esta limpo
- existe evidência mínima de validação
- o `CHANGELOG.md` foi atualizado
- a tag da versão vai ser publicada no remoto

## Gate mínimo por tipo de alteração

### Documentação apenas

Mínimo exigido:
- revisão dos documentos alterados
- `CHANGELOG.md` atualizado
- versão revista se a alteração tiver impacto real de uso

### Scripts ou template de ficheiros

Mínimo exigido:
- validação local do script ou fluxo alterado
- `scripts\pg_test_python_suites.ps1` (corre as suites Python todas de uma vez) e os `pg_test_*.ps1` afetados
- quando aplicável, `pg_smoke_test_repo.ps1`
- `CHANGELOG.md` e docs operacionais atualizados

Um teste que ninguém corre é documentação, não é rede. Até 2026-09-10 as suites Python existiam e não eram invocadas por nada — foi por isso que o guard de migração pôde ser alterado à vontade sem nada acusar.

### Addon `pg_brodoo`

Mínimo exigido:
- `scripts/pg_run_odoo_addon_tests.ps1` a passar
- instalação e upgrade do módulo validados no runner
- docs relevantes atualizadas se o comportamento mudou

### Mudança estrutural da framework

Mínimo exigido:
- validação em projeto piloto real ou repositório de reprodutibilidade
- smoke test estrutural
- testes automatizados do addon, se o addon foi tocado
- critério de fecho da iteração revisto

## Sequência obrigatória de release

1. concluir implementação
2. validar localmente o que mudou
3. atualizar docs afetadas
4. atualizar `CHANGELOG.md`
5. atualizar referência de versão, quando aplicável
6. confirmar `git status` limpo ou apenas com os ficheiros esperados
7. criar commit final da iteração
8. fazer `push` para `origin/main`
9. criar tag anotada da release
10. fazer `push` da tag
11. **propagar à frota** e registar a cobertura alcançada (ver abaixo)

## Propagação à frota (passo 11)

Uma release publicada não é uma release adotada. O publisher do espelho **nunca** escreve ficheiros de framework: a cada release os repositórios da frota ficam para trás e só se atualizam quando alguém abre uma sessão em cada um.

`FACTO OBSERVADO` (2026-09-10): os únicos 5 repositórios de 34 na versão corrente eram exactamente aqueles onde tinha havido sessão nos dias anteriores. Os restantes estavam na versão do último alinhamento manual, de 24/08.

Por isso a release fecha com:

```powershell
# 1. quanto da frota está na versão corrente, e o que bloqueia o resto
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_align_fleet_framework.ps1 -ReportPath .pg\tmp\frota.json

# 2. alinhar e publicar o que for alinhável
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_align_fleet_framework.ps1 -Apply
```

O relatório traz `repos_na_versao` de `repos_total` e, para cada repositório não alinhado, a razão. **Nenhuma razão é silenciada** — é isso que impede um relatório de cobertura parcial de se ler como cobertura total.

Três classes de bloqueio não se resolvem pelo alinhador, e a release deve registá-las em vez de as dar por resolvidas:

- **branch Brodoo declarada `main`** — `main` é a produção do cliente e ficheiros de framework não vão para lá. A correção é no Odoo (`repository_branch`), com `scripts\pg_migrate_brodoo_branch_orgwide.ps1`, seguida de republicação do espelho.
- **commits locais não publicados fora do âmbito da framework** — trabalho de outra pessoa. Publicar ou rever antes; um `push` do alinhador levá-lo-ia atrás.
- **elegível sem `.pg_framework`** (`sem_framework`) — o repositório está fora do perímetro da auditoria, do smoke test e do alinhador ao mesmo tempo. Ligar com `pg_link_framework.ps1`, ou tirar a pasta da raiz da frota se for um clone duplicado.

## Comandos de referência

### Publicar `main`

```powershell
cd C:\Users\Utilizador\Desktop\Repos\_pg_template
git push origin main
```

### Criar e publicar tag

```powershell
cd C:\Users\Utilizador\Desktop\Repos\_pg_template
git tag -a vX.Y.Z -m "release: vX.Y.Z"
git push origin vX.Y.Z
```

## O que entra no `CHANGELOG.md`

Cada release deve registar:

- número da versão
- data
- tipo de mudança
- resumo curto do que mudou
- se houve impacto em bootstrap, sync, addon, testes ou docs

## O que não conta como release

Os seguintes casos não devem ser tratados como release estável por si só:

- alterações locais não publicadas no remoto
- mudanças testadas apenas num piloto sem consolidação no `_pg_template`
- ajustes ainda sem changelog
- commits experimentais sem critério de fecho

## Regra de adoção por projetos

- projetos novos devem preferir bootstrap a partir de tag estável
- `main` pode ser usada quando o objetivo for testar iteração em curso
- repositórios piloto não definem baseline; apenas a validam

## Regra para ronda de validação piloto

Quando uma baseline já estiver fechada no repo canónico, mas a ronda seguinte for de validação operacional e adoção controlada:

- o objetivo imediato deixa de ser abrir nova frente estrutural
- a baseline deve ser testada com runbook próprio e relatório factual
- o resultado da ronda deve terminar numa classificação explicita:
  - `READY`
  - `READY WITH GUARDRAILS`
  - `NOT READY`
- a próxima frente estrutural só deve abrir depois dessa classificação ficar registada no repo canónico
- o piloto valida a baseline existente; não cria sozinho uma baseline nova

## Responsabilidade de fecho

Antes de declarar uma release como baseline utilizável, deve ser possível responder `sim` a estas perguntas:

- a alteração esta consolidada no `_pg_template`?
- existe evidência mínima de validação?
- o changelog explica a release?
- a tag identifica de forma única a baseline?
- um projeto novo consegue reproduzir a baseline sem depender de contexto informal?
- se a baseline entrou em ronda de piloto, o resultado `READY / READY WITH GUARDRAILS / NOT READY` ficou registado?
