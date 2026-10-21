<#
.SYNOPSIS
  Propaga os ficheiros de framework do agente (hooks de tokens + wrappers do ritual)
  para os repos de PROJETO no GitHub, na branch Brodoo de cada um, via clones
  temporarios ISOLADOS (nao toca nas copias de trabalho locais do utilizador).

.DESCRIPTION
  Para cada entrada do mapa (owner/repo -> branch(es)):
    1. clona shallow (--depth 1) e single-branch a branch Brodoo para uma pasta temporaria;
    2. copia os ficheiros de framework do agente (.claude/settings.json, .codex/hooks.json,
       AGENTS.md, CLAUDE.md) a partir de templates/;
    3. faz stage SO desses ficheiros; se nao houver diff, salta (sem commit vazio);
    4. commit + push origin HEAD:<branch> (a nao ser -WhatIf);
    5. remove a pasta temporaria.

  Isola-se em pastas temporarias para nao perturbar o WIP do utilizador nas copias locais.
  So mexe nos 4 ficheiros de framework do agente (cumpre a regra "framework -> branch Brodoo").
  NUNCA inclui producao nem credenciais.

.PARAMETER MappingPath
  Caminho para um JSON com o mapa de alvos:
    [ { "owner": "parametroglobaladmin", "repo": "SmartEnergy", "branches": ["Teste"] }, ... ]

.PARAMETER WorkDir
  Pasta base para os clones temporarios (default: %TEMP%\pg_rollout).

.PARAMETER WhatIf
  Mostra o que faria (clona e calcula o diff) mas NAO faz commit nem push.

.EXAMPLE
  .\pg_rollout_agent_hooks_orgwide.ps1 -MappingPath .\mapa.json -WhatIf
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$MappingPath,

  [string]$WorkDir,

  # Restringe o rollout a parte dos ficheiros (caminhos relativos, ex.: '.agents\hooks.json').
  # Por omissao, todos os de $assetRels.
  [string[]]$Assets,

  [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

$templateRoot = Split-Path -Parent $PSScriptRoot
$templatesDir = Join-Path $templateRoot 'templates'

# Ficheiros de framework do agente a propagar (relativos a raiz do repo)
$assetRels = @('.claude\settings.json', '.codex\hooks.json', '.agents\hooks.json', 'AGENTS.md', 'CLAUDE.md')
if ($Assets) {
  $desconhecidos = @($Assets | Where-Object { $assetRels -notcontains $_ })
  if ($desconhecidos.Count -gt 0) { throw "Assets fora da lista do rollout: $($desconhecidos -join ', '). Permitidos: $($assetRels -join ', ')" }
  $assetRels = @($Assets)
}

# AGENTS.md e CLAUDE.md tem um bloco de overrides locais do projeto. Ate 2026-10-08 este
# rollout copiava-os por cima, inteiros, e apagava esse bloco -- no givachoice e la que
# esta declarado o espelho do codigo vivo. O sync (pg_sync_shared_assets.ps1) ja os
# preservava; aqui usa-se a mesma funcao, para os dois caminhos nao divergirem.
. (Join-Path $PSScriptRoot 'pg_file_io_common.ps1')
$comOverrides = @('AGENTS.md', 'CLAUDE.md')

if (-not (Test-Path $MappingPath)) { throw "Mapa nao encontrado: $MappingPath" }
$mapping = Get-Content -Path $MappingPath -Raw | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($WorkDir)) { $WorkDir = Join-Path $env:TEMP 'pg_rollout' }
if (-not (Test-Path $WorkDir)) { New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null }

$commitMsg = @'
chore(framework): propagar hooks de tokens + wrappers atualizados

Ficheiros de framework dos agentes (Claude, Codex, Antigravity) alinhados com o
_pg_template: hooks de arranque e de registo de tokens, e wrappers do ritual.
Os overrides locais do AGENTS.md e do CLAUDE.md sao preservados.

Propagado por pg_rollout_agent_hooks_orgwide.ps1 (framework -> branch Brodoo).
'@

$results = New-Object System.Collections.Generic.List[object]

function Invoke-One {
  param([string]$Owner, [string]$Repo, [string]$Branch)

  # git/gh escrevem mensagens informativas no stderr; com EAP=Stop isso rebentaria como
  # NativeCommandError. Usar Continue e confiar no $LASTEXITCODE (padrao do pg_checkout).
  $ErrorActionPreference = 'Continue'

  $slug = "$Owner/$Repo"
  $dest = Join-Path $WorkDir ("{0}__{1}" -f $Repo, ($Branch -replace '[\\/:*?""<>|]', '_'))
  if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }

  Write-Host ("--- {0} @ {1}" -f $slug, $Branch)

  # 1) clone shallow + single-branch (auth via gh)
  $clone = & gh repo clone $slug $dest -- --depth 1 --branch $Branch --single-branch 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("  ERRO clone: {0}" -f ($clone -join ' '))
    $results.Add([ordered]@{ repo = $slug; branch = $Branch; status = 'erro_clone' })
    return
  }

  # 2) copiar assets
  foreach ($rel in $assetRels) {
    $src = Join-Path $templatesDir $rel
    if (-not (Test-Path $src)) { continue }
    $dst = Join-Path $dest $rel
    $parent = Split-Path -Parent $dst
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    if ($comOverrides -contains (Split-Path -Leaf $rel)) {
      $existente = if (Test-Path $dst) { Read-Utf8TextFile -Path $dst } else { $null }
      $merged = Merge-PgLocalOverrides -ExistingContent $existente -FrameworkContent (Read-Utf8TextFile -Path $src)
      Write-Utf8NoBomFile -Path $dst -Content $merged
    }
    else {
      Copy-Item -Path $src -Destination $dst -Force
    }
  }

  # 3) stage so dos assets + ver diff
  $existingRels = @()
  foreach ($rel in $assetRels) { if (Test-Path (Join-Path $dest $rel)) { $existingRels += ($rel -replace '\\', '/') } }
  & git -C $dest add -- $existingRels 2>&1 | Out-Null
  & git -C $dest diff --cached --quiet 2>$null
  $hasChange = ($LASTEXITCODE -ne 0)

  $changed = @()
  if ($hasChange) {
    $changed = (& git -C $dest diff --cached --name-only 2>$null) | Where-Object { $_ }
  }

  if (-not $hasChange) {
    Write-Host "  sem alteracoes (ja atualizado)"
    $results.Add([ordered]@{ repo = $slug; branch = $Branch; status = 'sem_alteracoes' })
    Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
    return
  }

  Write-Host ("  alteracoes: {0}" -f ($changed -join ', '))

  if ($WhatIf) {
    Write-Host "  WHATIF: commit + push omitidos"
    $results.Add([ordered]@{ repo = $slug; branch = $Branch; status = 'whatif'; changed = $changed })
    Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
    return
  }

  # 4) commit + push
  & git -C $dest -c user.name='Brodoo Framework' -c user.email='it.odoo@parametro.global' commit -m $commitMsg 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO commit"
    $results.Add([ordered]@{ repo = $slug; branch = $Branch; status = 'erro_commit' })
    Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
    return
  }
  $push = & git -C $dest push origin ("HEAD:{0}" -f $Branch) 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("  ERRO push: {0}" -f ($push -join ' '))
    $results.Add([ordered]@{ repo = $slug; branch = $Branch; status = 'erro_push' })
    Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
    return
  }
  Write-Host "  OK: commit + push"
  $results.Add([ordered]@{ repo = $slug; branch = $Branch; status = 'push_ok'; changed = $changed })
  Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ("Rollout de hooks/wrappers para {0} entrada(s){1}" -f $mapping.Count, $(if ($WhatIf) { ' [WHATIF]' } else { '' }))
foreach ($m in $mapping) {
  foreach ($b in $m.branches) {
    Invoke-One -Owner $m.owner -Repo $m.repo -Branch $b
  }
}

Write-Host ""
Write-Host "===== RESUMO ====="
$results | ForEach-Object { Write-Host ("  {0,-14} {1} @ {2}" -f $_.status, $_.repo, $_.branch) }
$grp = $results | Group-Object status | ForEach-Object { "{0}={1}" -f $_.Name, $_.Count }
Write-Host ("Totais: {0}" -f ($grp -join '  '))
