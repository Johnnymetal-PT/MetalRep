<#
.SYNOPSIS
  Garante que a framework partilhada esta atualizada e que o projeto esta sincronizado
  com a versao ATUAL do framework. Auto-atualiza no arranque (deteta drift e corrige).

.DESCRIPTION
  Encapsula os passos 2-4 do ritual num unico script robusto e a prova de falhas:
    1. Se a arvore de trabalho do framework (.pg_framework) estiver LIMPA, faz
       `git pull --ff-only` (atualiza ao origin sem merge/clobber). Se estiver suja ou
       nao for fast-forward, NAO forca: avisa e continua.
    2. Compara a versao do framework (HEAD) com a registada no projeto
       (.pg/PG_TEMPLATE_SYNC_STATE.json -> template_git_head). Se houver DRIFT, re-sincroniza
       o projeto com pg_sync_shared_assets.ps1 (idempotente; so ficheiros geridos pelo framework).

  A prova de falhas: erros (ex.: offline) sao avisos, nunca quebram a sessao (exit 0).
  Nao faz nada se .pg_framework nao estiver ligado (o preflight ja o marca como bloqueante).

.PARAMETER RepoPath   Repositorio do projeto (default: cwd).
.PARAMETER SkipPull   Nao faz git pull do framework (util offline / CI).
.PARAMETER WhatIf     Mostra as acoes sem as executar.
#>
param(
  [string]$RepoPath = (Get-Location).Path,
  [switch]$SkipPull,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Write-Info { param([string]$m) Write-Host "  $m" }

try {
  $repo = [System.IO.Path]::GetFullPath($RepoPath)
  $frameworkLink = Join-Path $repo ".pg_framework"
  if (-not (Test-Path $frameworkLink)) {
    Write-Host "AVISO: .pg_framework nao ligado; nada a atualizar (correr pg_link_framework.ps1)."
    exit 0
  }

  Write-Host "=== pg_ensure_framework_current ($repo) ==="

  # 1) git pull --ff-only do framework, se a arvore estiver limpa
  if (-not $SkipPull) {
    $isRepo = $false
    try {
      $inside = (& git -C $frameworkLink rev-parse --is-inside-work-tree 2>$null)
      if ($LASTEXITCODE -eq 0 -and (($inside -join '').Trim() -eq 'true')) { $isRepo = $true }
    }
    catch { $isRepo = $false }

    if (-not $isRepo) {
      Write-Info "WARN: .pg_framework nao e um repositorio git; pull ignorado."
    }
    else {
      $dirty = (& git -C $frameworkLink status --porcelain 2>$null)
      if (-not [string]::IsNullOrWhiteSpace(($dirty -join '').Trim())) {
        Write-Info "WARN: framework com alteracoes locais nao commitadas; pull ignorado (resolver manualmente)."
      }
      elseif ($WhatIf) {
        Write-Info "WHATIF: git -C .pg_framework pull --ff-only"
      }
      else {
        $before = (& git -C $frameworkLink rev-parse HEAD 2>$null)
        & git -C $frameworkLink pull --ff-only 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
          Write-Info "WARN: 'git pull --ff-only' falhou (offline ou nao fast-forward); a continuar com a versao local."
        }
        else {
          $after = (& git -C $frameworkLink rev-parse HEAD 2>$null)
          if ((($before -join '').Trim()) -ne (($after -join '').Trim())) { Write-Info "OK: framework atualizado ao origin." }
          else { Write-Info "OK: framework ja estava atualizado." }
        }
      }
    }
  }
  else {
    Write-Info "INFO: -SkipPull; git pull ignorado."
  }

  # 2) drift projeto vs framework -> re-sincronizar
  $frameworkHead = $null
  try {
    $h = (& git -C $frameworkLink rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0) { $frameworkHead = (($h -join '').Trim()) }
  }
  catch { $frameworkHead = $null }

  $syncStatePath = Join-Path $repo ".pg\PG_TEMPLATE_SYNC_STATE.json"
  $projectHead = $null
  if (Test-Path $syncStatePath) {
    try { $projectHead = ([string]((Get-Content -Path $syncStatePath -Raw | ConvertFrom-Json).template_git_head)).Trim() }
    catch { $projectHead = $null }
  }

  $drift = ($null -eq $projectHead) -or ($frameworkHead -and ($frameworkHead -ne $projectHead))
  if (-not $drift) {
    Write-Info "OK: projeto sincronizado com o framework ($frameworkHead)."
    exit 0
  }

  Write-Info "DRIFT: projeto=$projectHead framework=$frameworkHead -> re-sincronizar."
  $syncScript = Join-Path $frameworkLink "scripts\pg_sync_shared_assets.ps1"
  if (-not (Test-Path $syncScript)) { $syncScript = Join-Path $PSScriptRoot "pg_sync_shared_assets.ps1" }
  if (-not (Test-Path $syncScript)) {
    Write-Info "WARN: pg_sync_shared_assets.ps1 nao encontrado; correr bootstrap manualmente."
    exit 0
  }
  if ($WhatIf) {
    Write-Info "WHATIF: & pg_sync_shared_assets.ps1 -RepoName $(Split-Path -Leaf $repo) -RepoPath $repo"
    exit 0
  }
  & $syncScript -RepoName (Split-Path -Leaf $repo) -RepoPath $repo | Out-Null
  Write-Info "OK: projeto re-sincronizado com o framework atual."
  exit 0
}
catch {
  Write-Host "AVISO: pg_ensure_framework_current nao concluiu ($($_.Exception.Message)); a sessao continua."
  exit 0
}
