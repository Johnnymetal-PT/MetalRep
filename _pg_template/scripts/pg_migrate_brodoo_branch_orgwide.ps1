<#
.SYNOPSIS
  Migra projetos para a branch Brodoo padrao 'brodoo' e tira o framework da 'main'
  (producao do cliente). Por repo (deduplicado): cria 'brodoo', reconfigura o Odoo
  (pg_repo_branch='brodoo'), limpa o framework da 'main' e re-sincroniza o mirror.

.DESCRIPTION
  Le um mapa JSON [{project_id, owner, repo, current_branch}, ...]. Agrupa por owner/repo
  (varios projetos podem apontar ao mesmo repo). Idempotente. -WhatIf so LE e reporta.

  Passos por repo (modo real):
    1. criar refs/heads/brodoo a partir de current_branch (se nao existir);
    2. Odoo: pg_repo_branch='brodoo' para cada project_id do repo;
    3. limpar framework da 'main' (se la existir) via clone isolado + git rm + push;
    4. Odoo: action_sync_project_mirror_now para cada project_id.

  A parte odoo.sh (despromover antiga->Development, promover brodoo->Staging) e MANUAL,
  por conta, e NAO e feita por este script.

.PARAMETER MappingPath  JSON com os alvos.
.PARAMETER WhatIf        Dry-run: nao escreve nada; so reporta o plano.
.PARAMETER WorkDir       Pasta base para clones temporarios (limpeza da main).
.PARAMETER OnlyOwner     Processar so repos deste owner (ex.: parametroglobaladmin).
#>
param(
  [Parameter(Mandatory = $true)][string]$MappingPath,
  [switch]$WhatIf,
  [string]$WorkDir,
  [string]$OnlyOwner
)

$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$queryScript = Join-Path $here 'pg_odoo_query.ps1'
if ([string]::IsNullOrWhiteSpace($WorkDir)) { $WorkDir = Join-Path $env:TEMP 'pg_migrate_brodoo' }

# Ficheiros de framework a remover da 'main' (nunca o codigo Odoo)
$fwPaths = @('.pg', '.claude', '.codex', '.agents', 'AGENTS.md', 'CLAUDE.md', 'PG_CONTEXT.md',
  'PG_SCOPE_INTAKE.yaml', 'config.toml', 'doc_templates', 'projects',
  '.github/workflows/pg_refresh_pg_context.yml', '.github/workflows/pg_doc_templates_drift_check.yml')

function Test-GhPath { param($Slug, $Path, $Ref)
  gh api "repos/$Slug/contents/$Path`?ref=$Ref" --silent 2>$null; return ($LASTEXITCODE -eq 0)
}
function Test-GhBranch { param($Slug, $Branch)
  gh api "repos/$Slug/git/refs/heads/$Branch" --silent 2>$null; return ($LASTEXITCODE -eq 0)
}

$mapping = Get-Content -Path $MappingPath -Raw | ConvertFrom-Json
# agrupar por owner/repo
$groups = @{}
foreach ($e in $mapping) {
  if ($OnlyOwner -and $e.owner -ne $OnlyOwner) { continue }
  $key = "$($e.owner)/$($e.repo)"
  if (-not $groups.ContainsKey($key)) { $groups[$key] = [ordered]@{ owner = $e.owner; repo = $e.repo; branch = $e.current_branch; projects = @() } }
  $groups[$key].projects += $e.project_id
}

Write-Host ("=== Migracao brodoo {0} | {1} repos unicos ===" -f $(if ($WhatIf) { '[DRY-RUN]' } else { '[EXECUCAO]' }), $groups.Count)
$report = New-Object System.Collections.Generic.List[object]

foreach ($key in ($groups.Keys | Sort-Object)) {
  $g = $groups[$key]; $slug = "$($g.owner)/$($g.repo)"
  $noAccess = ($g.owner -ne 'parametroglobaladmin')
  $brodooExists = Test-GhBranch -Slug $slug -Branch 'brodoo'
  $mainHasFw = (Test-GhPath -Slug $slug -Path '.pg' -Ref 'main') -or (Test-GhPath -Slug $slug -Path 'AGENTS.md' -Ref 'main')

  $plan = @()
  if (-not $brodooExists) { $plan += "criar brodoo(<-$($g.branch))" } else { $plan += "brodoo existe" }
  $plan += "Odoo pg_repo_branch=brodoo (proj: $($g.projects -join ','))"
  if ($mainHasFw) { $plan += "LIMPAR framework da main" } else { $plan += "main ja limpa" }
  $plan += "re-sync mirror"
  $flag = if ($noAccess) { " [!! owner=$($g.owner) - sem acesso gh]" } else { "" }

  Write-Host ("--- {0}{1}" -f $slug, $flag)
  Write-Host ("    " + ($plan -join ' | '))
  $report.Add([ordered]@{ repo = $slug; brodoo = $brodooExists; mainHasFw = $mainHasFw; projects = ($g.projects -join ','); noAccess = $noAccess })

  if (-not $WhatIf) {
    if ($noAccess) { Write-Host "    SKIP (sem acesso gh)"; continue }
    try {
      # 0) confirmar acesso gh ao repo (senao nao da para criar branch nem limpar main)
      gh api "repos/$slug" --silent 2>$null
      if ($LASTEXITCODE -ne 0) { throw "sem acesso gh a $slug (404) - conceder colaborador ao bruno-pinheiro-pg" }

      # 1) criar brodoo (a partir da branch atual) se nao existir, VERIFICANDO a criacao
      if (-not $brodooExists) {
        $sha = (gh api "repos/$slug/git/refs/heads/$($g.branch)" --jq '.object.sha' 2>$null)
        if ([string]::IsNullOrWhiteSpace($sha)) { throw "sha de $($g.branch) nao obtido" }
        gh api --method POST "repos/$slug/git/refs" -f ref="refs/heads/brodoo" -f sha="$sha" 2>&1 | Out-Null
        gh api "repos/$slug/git/refs/heads/brodoo" --silent 2>$null
        if ($LASTEXITCODE -ne 0) { throw "criacao da branch brodoo falhou (POST nao persistiu)" }
        Write-Host "    OK: brodoo criada (<-$($g.branch))"
      }
      # 2) Odoo: pg_repo_branch='brodoo' por projeto
      foreach ($projId in $g.projects) {
        & $queryScript -Model project.project -Method write -ArgsJson "[[$projId],{`"pg_repo_branch`":`"brodoo`"}]" 2>&1 | Out-Null
        Write-Host "    OK: Odoo pg_repo_branch=brodoo (proj $projId)"
      }
      # 3) limpar framework da main (clone isolado + git rm + push)
      if ($mainHasFw) {
        $dest = Join-Path $WorkDir ("{0}__main" -f $g.repo)
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        gh repo clone $slug $dest -- --depth 1 --branch main --single-branch 2>&1 | Out-Null
        $rmArgs = @('-C', $dest, 'rm', '-r', '--quiet', '--ignore-unmatch') + $fwPaths
        git @rmArgs 2>&1 | Out-Null
        $staged = (git -C $dest diff --cached --name-only 2>$null | Measure-Object -Line).Lines
        if ($staged -gt 0) {
          git -C $dest -c user.name='Brodoo Framework' -c user.email='it.odoo@parametro.global' commit -q -m "chore(brodoo): remover framework/mirror da main (branch Brodoo = brodoo)" 2>&1 | Out-Null
          git -C $dest push origin HEAD:main 2>&1 | Out-Null
          Write-Host "    OK: main limpa ($staged ficheiros removidos)"
        }
        Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
      }
      # 4) re-sync do mirror para brodoo, por projeto (com retry por conflito de SHA transitorio)
      foreach ($projId in $g.projects) {
        $synced = $false
        for ($try = 1; $try -le 3 -and -not $synced; $try++) {
          try {
            & $queryScript -Model project.project -Method action_sync_project_mirror_now -ArgsJson "[[$projId]]" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) { $synced = $true }
          }
          catch { $synced = $false }
        }
        if ($synced) { Write-Host "    OK: re-sync mirror (proj $projId)" }
        else { Write-Host "    AVISO: re-sync falhou apos 3 tentativas (proj $projId) - re-correr o script depois" }
      }
      ($report[$report.Count - 1]).status = 'ok'
    }
    catch {
      Write-Host "    ERRO: $($_.Exception.Message)"
      ($report[$report.Count - 1]).status = 'erro'
    }
  }
}

Write-Host ""
Write-Host "===== RESUMO ====="
$needBrodoo = @($report | Where-Object { -not $_.brodoo }).Count
$needClean = @($report | Where-Object { $_.mainHasFw }).Count
$noAcc = @($report | Where-Object { $_.noAccess }).Count
Write-Host ("repos={0} | criar brodoo={1} | limpar main={2} | sem acesso gh={3}" -f $report.Count, $needBrodoo, $needClean, $noAcc)
if ($noAcc -gt 0) { Write-Host "Sem acesso gh (tratar a parte):"; $report | Where-Object { $_.noAccess } | ForEach-Object { Write-Host "  $($_.repo)" } }