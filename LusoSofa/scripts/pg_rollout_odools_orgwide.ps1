<#
.SYNOPSIS
  Audita ou configura OdooLS nos repositorios Git imediatamente abaixo de uma raiz.
#>
param(
  [string]$RootPath = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [switch]$Apply,
  [switch]$InstallVsCodeExtension,
  [string[]]$RepoName,
  [string]$OutputFile
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath($RootPath)
if (-not (Test-Path $root)) { throw "RootPath nao encontrado: $root" }
$setupScript = Join-Path $PSScriptRoot 'pg_setup_odools.ps1'
if (-not (Test-Path $setupScript)) { throw "Script de setup em falta: $setupScript" }

if ($InstallVsCodeExtension) {
  $code = Get-Command code -ErrorAction SilentlyContinue
  if (-not $code) { throw 'VS Code CLI nao encontrado' }
  & $code.Source --install-extension Odoo.odoo | Out-Host
  if ($LASTEXITCODE -ne 0) { throw 'Falhou a instalacao da extensao Odoo.odoo' }
}

$repos = Get-ChildItem -Path $root -Directory | Where-Object {
  (Test-Path (Join-Path $_.FullName '.git')) -and
  ($_.Name -ne '_pg_template') -and
  ((-not $RepoName) -or ($RepoName -contains $_.Name))
}

$results = foreach ($repo in $repos) {
  try {
    $json = & $setupScript -RepoPath $repo.FullName -CheckOnly:(-not $Apply) -AsJson
    $data = $json | ConvertFrom-Json
    [pscustomobject]@{
      repo = $repo.Name; status = if ($Apply) { 'configured' } else { 'ready' }
      version = $data.version; binary = $data.binary_available; detail = ''
    }
  }
  catch {
    [pscustomobject]@{ repo = $repo.Name; status = 'blocked'; version = ''; binary = $false; detail = $_.Exception.Message }
  }
}

$summary = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  root_path = $root
  apply = [bool]$Apply
  total = @($results).Count
  ready_or_configured = @($results | Where-Object { $_.status -ne 'blocked' }).Count
  blocked = @($results | Where-Object status -eq 'blocked').Count
  repositories = @($results)
}

if ($OutputFile) {
  $path = [System.IO.Path]::GetFullPath($OutputFile)
  $parent = Split-Path -Parent $path
  if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, (($summary | ConvertTo-Json -Depth 6) + "`n"), $utf8)
}

Write-Host ("OdooLS rollout: {0}/{1} {2}; bloqueados={3}" -f $summary.ready_or_configured, $summary.total, $(if ($Apply) { 'configurados' } else { 'prontos' }), $summary.blocked)
$results | Format-Table -AutoSize
if ($summary.blocked -gt 0) { exit 2 }

