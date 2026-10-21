param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,

  [string]$EffortPath
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_effort_sync_common.ps1")

$repo = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

$resolvedEffortPath = Resolve-EffortSyncPath -RepositoryPath $repo -ExplicitEffortPath $EffortPath
if (-not (Test-Path $resolvedEffortPath)) {
  throw "PG_EFFORT_SYNC.json nao encontrado em $resolvedEffortPath"
}

$effort = Get-EffortSyncData -Path $resolvedEffortPath
[void](Assert-EffortSyncContract -Data $effort)

Write-Host "OK: PG_EFFORT_SYNC.json validado com sucesso"
