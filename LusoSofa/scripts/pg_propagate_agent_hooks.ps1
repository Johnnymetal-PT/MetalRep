<#
.SYNOPSIS
  AUD-03: propaga os ficheiros de hook de registo de tokens (.claude/settings.json e
  .codex/hooks.json) para projetos JA existentes, de forma segura e idempotente.

.DESCRIPTION
  Os projetos criados antes destes ficheiros nao os tem (o bootstrap so copia para
  projetos novos). Este script copia SO esses dois ficheiros (nao corre o sync completo
  de assets, que e mais pesado).

  Seguranca:
  - por defeito copia apenas se o destino NAO existir; se existir, avisa e nao sobrescreve
    (para nao destruir configuracao propria do projeto). Usar -Force para atualizar.
  - -WhatIf mostra o que faria sem escrever.
  - so atua em repos elegiveis (com .pg/ ou PG_CONTEXT.md) e nunca no proprio _pg_template.

.PARAMETER RepoPath
  Caminho de um repositorio (modo piloto: um so projeto).

.PARAMETER RootPath
  Pasta que contem varios repositorios; processa cada subpasta elegivel (modo "todos").

.EXAMPLE
  .\pg_propagate_agent_hooks.ps1 -RepoPath C:\Users\U\Desktop\Repos\SmartEnergy -WhatIf
.EXAMPLE
  .\pg_propagate_agent_hooks.ps1 -RootPath C:\Users\U\Desktop\Repos
#>
param(
  [string]$RepoPath,
  [string]$RootPath,
  [switch]$Force,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$templateRoot = Split-Path -Parent $PSScriptRoot
$templatesDir = Join-Path $templateRoot "templates"

$assets = @(
  @{ Source = Join-Path $templatesDir ".claude\settings.json"; Rel = ".claude\settings.json" },
  @{ Source = Join-Path $templatesDir ".codex\hooks.json"; Rel = ".codex\hooks.json" }
)

function Test-EligibleRepo {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path)) { return $false }
  $full = [System.IO.Path]::GetFullPath($Path)
  if ($full -eq [System.IO.Path]::GetFullPath($templateRoot)) { return $false }  # nunca o proprio framework
  return ((Test-Path (Join-Path $full ".pg")) -or (Test-Path (Join-Path $full "PG_CONTEXT.md")))
}

function Invoke-PropagateRepo {
  param([string]$Path)
  $repo = [System.IO.Path]::GetFullPath($Path)
  Write-Host ("--- {0}" -f $repo)
  foreach ($asset in $assets) {
    if (-not (Test-Path $asset.Source)) { Write-Host ("  WARN: fonte em falta: {0}" -f $asset.Source); continue }
    $dest = Join-Path $repo $asset.Rel
    $exists = Test-Path $dest
    if ($exists -and -not $Force) {
      Write-Host ("  SKIP: {0} ja existe (usar -Force para atualizar)" -f $asset.Rel)
      continue
    }
    $action = if ($exists) { "ATUALIZAR" } else { "CRIAR" }
    if ($WhatIf) {
      Write-Host ("  WHATIF: {0} {1}" -f $action, $asset.Rel)
      continue
    }
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -Path $asset.Source -Destination $dest -Force
    Write-Host ("  OK ({0}): {1}" -f $action, $asset.Rel)
  }
  # garantir .pg/tokens/consumption.jsonl (destino do registo)
  $tokensDir = Join-Path $repo ".pg\tokens"
  $consumption = Join-Path $tokensDir "consumption.jsonl"
  if (-not (Test-Path $consumption)) {
    if ($WhatIf) { Write-Host "  WHATIF: criar .pg/tokens/consumption.jsonl" }
    else {
      if (-not (Test-Path $tokensDir)) { New-Item -ItemType Directory -Path $tokensDir -Force | Out-Null }
      $encoding = New-Object System.Text.UTF8Encoding($false)
      [System.IO.File]::WriteAllText($consumption, "", $encoding)
      Write-Host "  OK: criado .pg/tokens/consumption.jsonl"
    }
  }
}

$targets = @()
if (-not [string]::IsNullOrWhiteSpace($RepoPath)) {
  if (Test-EligibleRepo -Path $RepoPath) { $targets += (Resolve-Path $RepoPath).Path }
  else { throw "RepoPath nao e um repositorio elegivel (precisa de .pg/ ou PG_CONTEXT.md): $RepoPath" }
}
elseif (-not [string]::IsNullOrWhiteSpace($RootPath)) {
  if (-not (Test-Path $RootPath)) { throw "RootPath nao encontrado: $RootPath" }
  Get-ChildItem -Path $RootPath -Directory | ForEach-Object {
    if (Test-EligibleRepo -Path $_.FullName) { $targets += $_.FullName }
  }
}
else {
  throw "Indicar -RepoPath (um projeto) ou -RootPath (pasta com varios projetos)."
}

if ($targets.Count -eq 0) { Write-Host "Nenhum repositorio elegivel encontrado."; return }

Write-Host ("Propagacao de hooks de tokens para {0} repo(s){1}:" -f $targets.Count, $(if ($WhatIf) { " [WHATIF]" } elseif ($Force) { " [FORCE]" } else { "" }))
foreach ($t in $targets) { Invoke-PropagateRepo -Path $t }
Write-Host "OK: propagacao concluida."
