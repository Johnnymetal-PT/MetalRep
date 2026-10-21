param(
  [string]$ReposRoot,
  [string[]]$RepoNames,
  [switch]$SkipSync
)

$ErrorActionPreference = "Stop"

function Test-Path-PgSameDirectory {
  # O proprio _pg_template tem um .pg_framework que aponta para si mesmo, pelo que
  # a deteccao por presenca do symlink tambem o apanha. Sincroniza-lo seria copiar
  # os ficheiros por cima deles proprios ("Cannot overwrite the item ... with itself")
  # e fazia a auditoria da frota terminar sempre em erro.
  param(
    [string]$Left,
    [string]$Right
  )

  if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) {
    return $false
  }

  $normalize = {
    param([string]$p)
    return ([System.IO.Path]::GetFullPath($p)).TrimEnd([char]92, [char]47)
  }

  return ((& $normalize $Left) -ieq (& $normalize $Right))
}

function Resolve-TemplateRoot {
  return (Split-Path -Parent $PSScriptRoot)
}

function Resolve-ReposRoot {
  param(
    [string]$ExplicitReposRoot,
    [string]$TemplateRoot
  )

  if (-not [string]::IsNullOrWhiteSpace($ExplicitReposRoot)) {
    return [System.IO.Path]::GetFullPath($ExplicitReposRoot)
  }

  return (Split-Path -Parent $TemplateRoot)
}

$templateRoot = Resolve-TemplateRoot
$reposRootPath = Resolve-ReposRoot -ExplicitReposRoot $ReposRoot -TemplateRoot $templateRoot
$syncScript = Join-Path $PSScriptRoot "pg_sync_shared_assets.ps1"
$smokeScript = Join-Path $PSScriptRoot "pg_smoke_test_repo.ps1"

if (-not (Test-Path $syncScript)) {
  throw "Script em falta: $syncScript"
}
if (-not (Test-Path $smokeScript)) {
  throw "Script em falta: $smokeScript"
}
if (-not (Test-Path $reposRootPath)) {
  throw "ReposRoot nao encontrado: $reposRootPath"
}

$repos = @()
if ($RepoNames -and $RepoNames.Count -gt 0) {
  foreach ($name in $RepoNames) {
    $repoPath = Join-Path $reposRootPath $name
    if (-not (Test-Path $repoPath)) {
      Write-Host "WARN: repo ignorado (nao encontrado): $repoPath"
      continue
    }

    if (Test-Path-PgSameDirectory -Left $repoPath -Right $templateRoot) {
      Write-Host "WARN: repo ignorado (e o proprio _pg_template): $repoPath"
      continue
    }

    if (Test-Path (Join-Path $repoPath ".pg_framework")) {
      $repos += [pscustomobject]@{
        Name = $name
        Path = $repoPath
      }
    }
    else {
      Write-Host "WARN: repo ignorado (sem .pg_framework): $repoPath"
    }
  }
}
else {
  $repos = @(Get-ChildItem -Path $reposRootPath -Directory | Where-Object {
      (Test-Path (Join-Path $_.FullName ".pg_framework")) -and
      (-not (Test-Path-PgSameDirectory -Left $_.FullName -Right $templateRoot))
    } | ForEach-Object {
      [pscustomobject]@{
        Name = $_.Name
        Path = $_.FullName
      }
    })
}

if ($repos.Count -eq 0) {
  Write-Host "WARN: nenhum repo bootstrapado encontrado em $reposRootPath"
  exit 0
}

$results = @()

foreach ($repo in $repos) {
  Write-Host ""
  Write-Host "=== Repo: $($repo.Name) ==="

  $syncOk = $true
  $smokeOk = $true
  $syncError = $null
  $smokeError = $null

  if (-not $SkipSync) {
    try {
      & $syncScript -RepoName $repo.Name -RepoPath $repo.Path
    }
    catch {
      $syncOk = $false
      $syncError = $_.Exception.Message
    }
  }

  try {
    & $smokeScript -RepoPath $repo.Path
  }
  catch {
    $smokeOk = $false
    $smokeError = $_.Exception.Message
  }

  $results += [pscustomobject]@{
    repo = $repo.Name
    sync_ok = $syncOk
    smoke_ok = $smokeOk
    sync_error = $syncError
    smoke_error = $smokeError
  }
}

Write-Host ""
Write-Host "=== Resumo ==="

$failed = 0
foreach ($row in $results) {
  $syncState = if ($row.sync_ok) { "OK" } else { "FAIL" }
  $smokeState = if ($row.smoke_ok) { "OK" } else { "FAIL" }
  Write-Host ("- {0}: sync={1}; smoke={2}" -f $row.repo, $syncState, $smokeState)

  if (-not $row.sync_ok -or -not $row.smoke_ok) {
    $failed += 1
    if ($row.sync_error) {
      Write-Host ("  sync_error: {0}" -f $row.sync_error)
    }
    if ($row.smoke_error) {
      Write-Host ("  smoke_error: {0}" -f $row.smoke_error)
    }
  }
}

if ($failed -gt 0) {
  throw "Auditoria concluida com falhas em $failed repo(s)."
}

Write-Host "OK: auditoria concluida sem falhas."
